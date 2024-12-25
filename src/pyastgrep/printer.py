from __future__ import annotations

import sys
import textwrap
from typing import Callable, Iterable, Protocol, TextIO

from pyastgrep.ignores import WalkError

from . import xml
from .color import Colorer, NullColorer
from .context import ContextType, StatementContext, StaticContext
from .files import MissingPath, Pathlike, ReadError
from .search import FileFinished, Match, NonElementReturned


class Formatter(Protocol):
    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        ...

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        ...

    def format_match_line(self, result: Match) -> str:
        ...


class ContextHandler(Protocol):
    def handle_result(self, result: Match) -> None:
        pass

    def flush(self) -> None:
        pass


LinePrinter = Callable[[str], None]


def print_results(
    results: Iterable[Match | MissingPath | ReadError | WalkError | NonElementReturned | FileFinished],
    print_xml: bool = False,
    print_ast: bool = False,
    context: ContextType = StaticContext(before=0, after=0),
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    quiet: bool = False,
    heading: bool = False,
    colorer: Colorer | None = None,
) -> tuple[int, int]:
    if print_ast:
        # Don't import unless needed
        import astpretty

    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr
    if colorer is None:
        colorer = NullColorer()
    matches = 0
    errors = 0

    def do_error(message: str) -> None:
        nonlocal errors
        print(message, file=stderr)
        errors += 1

    def line_printer(line: str) -> None:
        print(line, file=stdout)

    context_handler: ContextHandler
    if heading:
        if isinstance(context, StatementContext):
            context_handler = StatementWithHeadingContextHandler(
                line_printer=line_printer, formatter=HeadingFormatter(colorer=colorer)
            )
        else:
            context_handler = DefaultContextHandler(
                context_type=context, line_printer=line_printer, formatter=HeadingFormatter(colorer=colorer)
            )
    else:
        context_handler = DefaultContextHandler(
            context_type=context, line_printer=line_printer, formatter=DefaultFormatter(colorer=colorer)
        )

    for result in results:
        if isinstance(result, MissingPath):
            do_error(f"{result.path}: No such file or directory")
            continue
        elif isinstance(result, ReadError):
            do_error(f"{result.path}: {result.exception}")
            continue
        elif isinstance(result, WalkError):
            do_error(f"{result.path}: {result.exception}")
            continue
        elif isinstance(result, NonElementReturned):
            do_error(f"Error: XPath expression returned a value that is not an AST node: {result.args[0]}")
            continue
        elif isinstance(result, FileFinished):
            context_handler.flush()
            continue

        matches += 1
        if quiet:
            continue

        context_handler.handle_result(result)

        if print_ast:
            line_printer(astpretty.pformat(result.ast_node))  # type: ignore[reportPossiblyUnboundVariable]

        if print_xml:
            line_printer(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"))

    # Last result
    context_handler.flush()

    return (matches, errors)


# Context handlers


class DefaultContextHandler:
    # Helper class to manage context lines:
    #
    # This is quite complex due to:
    # - handling before and after context,
    # - including overlapping context
    # - handling the fact that a single line may be printed multiple times
    #   if there is a match on multiple parts of the line.
    # - ensuring that we print results as soon as we get them,
    #   rather than waiting (grouping by file would simplify some things)
    # - A match line is formatted differently from a context line, which
    #   means we have to wait to print the 'after' lines of a previous result
    #   to be sure they don't contain a match line.
    # - edge conditions

    def __init__(self, *, context_type: ContextType, line_printer: LinePrinter, formatter: Formatter):
        # Configuration from outside:
        self.context_type = context_type
        self.line_printer = line_printer
        self.formatter = formatter

        # Internal state this class manages:
        self.printed_context_lines: set[tuple[Pathlike, int]] = set()
        self.queued_context_lines: list[tuple[Pathlike, int, str]] = []

    def handle_result(self, result: Match) -> None:
        before_context, after_context = self.context_type.get_context_lines_for_result(result)

        line_index = result.position.lineno - 1

        # Previous result's 'after' lines
        self.flush_context_lines(
            before_result_path=result.path,
            before_result_line=result.position.lineno - before_context - 1,
        )

        # This result's 'before' lines
        self.queue_context_lines(result, list(range(max(0, line_index - before_context), line_index)))
        self.flush_context_lines()

        # The actual result
        self.print_match_line(result, line_index)

        # This result's 'after' lines
        self.queue_context_lines(
            result, list(range(line_index + 1, min(len(result.file_lines), line_index + after_context + 1)))
        )

    def flush(self) -> None:
        self.flush_context_lines()

    def print_match_line(self, result: Match, line_index: int) -> None:
        self.maybe_print_header(result.path, line_index)
        self.line_printer(self.formatter.format_match_line(result))
        self.printed_context_lines.add((result.path, line_index))

    def maybe_print_header(self, path: Pathlike, line_index: int) -> None:
        # We print the header only if there is a gap
        if (path, line_index - 1) not in self.printed_context_lines:
            header = self.formatter.format_header(path, line_index)
            if header is not None:
                self.line_printer(header)

    def queue_context_lines(self, result: Match, context_line_indices: list[int]) -> None:
        for context_line_index in context_line_indices:
            if (result.path, context_line_index) not in self.printed_context_lines:
                context_line = result.file_lines[context_line_index]
                self.queued_context_lines.append(
                    (
                        result.path,
                        context_line_index,
                        self.formatter.format_context_line(result, context_line, context_line_index),
                    )
                )

    def flush_context_lines(
        self, *, before_result_path: Pathlike | None = None, before_result_line: int | None = None
    ) -> None:
        """
        Print queued context lines.

        If passed, print only the context lines that come before before_result_path and before_result_line.
        """

        for path, line_index, to_print in self.queued_context_lines:
            if (
                before_result_path is None
                or path != before_result_path
                # from a different file => print
            ) or (
                before_result_line is None
                or line_index < before_result_line
                # Before the context for current result => print
            ):
                self.maybe_print_header(path, line_index)
                self.line_printer(to_print)
                self.printed_context_lines.add((path, line_index))
        self.queued_context_lines[:] = []


class StatementWithHeadingContextHandler:
    # This is a special case for when we have headings and are displaying full
    # statements. In this case, it is much more useful if we auto-dedent the
    # statements, which will make the output valid Python, which can be useful
    # if we are doing things like gathering example input.

    # This requires a different strategy, because we need to dedent the whole
    # statement at once. We don't have the issues with needing to wait for the
    # next result, because context lines are not formatted different to matches.
    # For cases of overlapping or nested matches, we don't print the same lines
    # multiple times.

    def __init__(self, *, line_printer: LinePrinter, formatter: Formatter):
        # Configuration from outside:
        self.line_printer = line_printer
        self.formatter = formatter
        self.context_type = StatementContext()

        # Managed state:
        self.printed_context_lines: set[tuple[Pathlike, int]] = set()

    def handle_result(self, result: Match) -> None:
        line_index = result.position.lineno - 1
        path = result.path

        before_context, after_context = self.context_type.get_context_lines_for_result(result)
        start_line_idx = line_index - before_context
        end_line_idx = line_index + after_context
        stop_line_idx = end_line_idx + 1

        if (path, end_line_idx) in self.printed_context_lines:
            # Already printed
            return

        if (path, start_line_idx - 1) not in self.printed_context_lines:
            header = self.formatter.format_header(path, start_line_idx)
            if header is not None:
                self.line_printer(header)

        code = "\n".join(result.file_lines[start_line_idx:stop_line_idx])
        to_print = textwrap.dedent(code)
        self.line_printer(to_print.rstrip("\n"))
        for idx in range(start_line_idx, stop_line_idx):
            self.printed_context_lines.add((path, idx))

    def flush(self) -> None:
        pass


# Formatters


class DefaultFormatter:
    def __init__(self, colorer: Colorer):
        self.colorer = colorer

    # Same formatting as ripgrep:
    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        return None

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        c = self.colorer
        path_s = c.color_path(str(result.path))
        lineno_s = c.color_lineno(context_line_index + 1)
        return f"{path_s}-{lineno_s}-{context_line}"

    def format_match_line(self, result: Match) -> str:
        c = self.colorer
        path_s = c.color_path(str(result.path))
        lineno_s = c.color_lineno(result.position.lineno)
        match_s = c.color_match(result)
        colum = result.position.col_offset + 1
        return f"{path_s}:{lineno_s}:{colum}:{match_s}"


class HeadingFormatter:
    def __init__(self, colorer: Colorer):
        self.colorer = colorer
        self.first_result_printed = False

    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        # Start with hash like a Python comment, for integration with tools that
        # consume Python code

        # Gap between results, for all but very first
        spacer = "\n" if self.first_result_printed else ""
        self.first_result_printed = True
        c = self.colorer
        path_s = c.color_path(str(path))
        lineno_s = c.color_lineno(context_line_index + 1)
        return spacer + f"# {path_s}:{lineno_s}:"

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        return context_line

    def format_match_line(self, result: Match) -> str:
        return self.colorer.color_match(result)
