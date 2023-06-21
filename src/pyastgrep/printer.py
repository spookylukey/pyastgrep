from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, Protocol, TextIO

from pyastgrep import ast_compat

from . import xml
from .search import FileFinished, Match, MissingPath, NonElementReturned, Pathlike, ReadError


@dataclass(frozen=True)
class StaticContext:
    before: int = 0
    after: int = 0


class StatementContext:
    pass


class Formatter(Protocol):
    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        pass

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        pass

    def format_match_line(self, result: Match) -> str:
        pass


def print_results(
    results: Iterable[Match | MissingPath | ReadError | NonElementReturned | FileFinished],
    print_xml: bool = False,
    print_ast: bool = False,
    context: StaticContext | StatementContext = StaticContext(before=0, after=0),
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    quiet: bool = False,
    heading: bool = False,
) -> tuple[int, int]:
    if print_ast:
        # Don't import unless needed
        import astpretty

    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr
    matches = 0
    errors = 0

    formatter: Formatter
    if heading:
        formatter = HeadingFormatter()
    else:
        formatter = DefaultFormatter()

    def do_error(message: str) -> None:
        nonlocal errors
        print(message, file=stderr)
        errors += 1

    context_handler = ContextHandler(config=context, stdout=stdout, formatter=formatter)

    for result in results:
        if isinstance(result, MissingPath):
            do_error(f"{result.path}: No such file or directory")
            continue
        elif isinstance(result, ReadError):
            do_error(f"{result.path}: {result.exception}")
            continue
        elif isinstance(result, NonElementReturned):
            do_error(f"Error: XPath expression returned a value that is not an AST node: {result.args[0]}")
            continue
        elif isinstance(result, FileFinished):
            context_handler.flush_context_lines()
            continue

        matches += 1
        if quiet:
            continue

        context_handler.handle_result(result, context)

        if print_ast:
            print(astpretty.pformat(result.ast_node), file=stdout)

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)

    # Last result
    context_handler.flush_context_lines()

    return (matches, errors)


class ContextHandler:
    # Helper class to manage context lines:
    #
    # This is quite complex due to:
    # - handling before and after context,
    # - including overlapping context
    # - handling the fact that a single line may be printed multiple times
    #   if there is a match on multiple parts of the line.
    # - ensuring that we print results as soon as we get them,
    #   rather than waiting (grouping by file would simplify some things)
    # - A match line is formatted differently from a result line, which
    #   means we have to wait to print the 'after' lines of a previous result
    #   to be sure they don't contain a match line.
    # - edge conditions

    def __init__(self, *, config: StaticContext | StatementContext, stdout: TextIO, formatter: Formatter):
        # Configuration from outside:
        self.config = config
        self.stdout = stdout
        self.formatter = formatter

        # Internal state this class manages:
        self.printed_context_lines: set[tuple[Pathlike, int]] = set()
        self.queued_context_lines: list[tuple[Pathlike, int, str]] = []

    def handle_result(self, result: Match, context: StaticContext | StatementContext) -> None:
        if isinstance(context, StaticContext):
            before_context = context.before
            after_context = context.after
        else:
            before_context, after_context = _get_statement_context_lines(result)

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

    def print_match_line(self, result: Match, line_index: int) -> None:
        self.maybe_print_header(result.path, line_index)
        print(self.formatter.format_match_line(result), file=self.stdout)
        self.printed_context_lines.add((result.path, line_index))

    def maybe_print_header(self, path: Pathlike, line_index: int) -> None:
        if (path, line_index - 1) not in self.printed_context_lines:
            header = self.formatter.format_header(path, line_index)
            if header is not None:
                print(header, file=self.stdout)

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
                print(to_print, file=self.stdout)
                self.printed_context_lines.add((path, line_index))
        self.queued_context_lines[:] = []


class DefaultFormatter:
    # Same formatting as ripgrep:
    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        return None

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        return f"{result.path}-{context_line_index + 1}-{context_line}"

    def format_match_line(self, result: Match) -> str:
        return f"{result.path}:{result.position.lineno}:{result.position.col_offset + 1}:{result.matching_line}"


# Formatting for heading mode


class HeadingFormatter:
    def __init__(self) -> None:
        self.first_result_printed = False

    def format_header(self, path: Pathlike, context_line_index: int) -> str | None:
        # Start with hash like a Python comment, for integration with tools that
        # consume Python code

        # Gap between results, for all but very first
        spacer = "\n" if self.first_result_printed else ""
        self.first_result_printed = True
        return spacer + f"# {path}:{context_line_index + 1}:"

    def format_context_line(self, result: Match, context_line: str, context_line_index: int) -> str:
        return context_line

    def format_match_line(self, result: Match) -> str:
        return result.matching_line


# Statement handling
def _get_statement_context_lines(result: Match) -> tuple[int, int]:
    result_node = current_node = result.ast_node
    while True:
        if isinstance(current_node, ast_compat.STATEMENT_AST):
            break
        parent = current_node.parent  # type: ignore

        # If directly in the 'body' of a block statement, this node is
        # 'statement-like' i.e. it is self-contained and could appear at top
        # level in a module in most cases.
        if isinstance(parent, ast_compat.BLOCK_AST) and current_node in parent.body:
            break
        current_node = parent
    before_context = result_node.lineno - current_node.lineno
    if isinstance(current_node.end_lineno, int):
        after_context = current_node.end_lineno - result_node.lineno
    else:
        after_context = 0

    return (before_context, after_context)
