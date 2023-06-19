from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, TextIO

from . import xml
from .search import Match, MissingPath, NonElementReturned, Pathlike, ReadError


@dataclass(frozen=True)
class StaticContext:
    before: int = 0
    after: int = 0


def print_results(
    results: Iterable[Match | MissingPath | ReadError | NonElementReturned],
    print_xml: bool = False,
    print_ast: bool = False,
    context: StaticContext = StaticContext(before=0, after=0),
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

    # Printing context lines:
    #
    # This function is quite complex due to:
    # - handling before and after context,
    # - including overlapping context
    # - handling the fact that a single line may be printed multiple times
    #   if there is a match on multiple parts of the line.
    # - ensuring that we print results as soon as we get them,
    #   rather than waiting (grouping by file would simplify some things)
    # - edge conditions

    before_context = context.before
    after_context = context.after
    printed_context_lines: set[tuple[Pathlike, int]] = set()
    queued_context_lines: list[tuple[Pathlike, int, str]] = []

    if heading:
        format_context_line = _format_context_line_heading
        format_match_line = _format_match_line_heading
    else:
        format_context_line = _format_context_line_default
        format_match_line = _format_match_line_default

    def queue_context_lines(result: Match, context_line_indices: list[int]) -> None:
        for context_line_index in context_line_indices:
            if (result.path, context_line_index) not in printed_context_lines:
                context_line = result.file_lines[context_line_index]
                queued_context_lines.append(
                    (
                        result.path,
                        context_line_index,
                        format_context_line(result, context_line, context_line_index),
                    )
                )

    def print_header(path: Pathlike, line_index: int) -> None:
        if heading and (path, line_index - 1) not in printed_context_lines:
            # Gap between results, for all but very first
            if matches > 1:
                print("", file=stdout)
            print(_format_header(path, line_index), file=stdout)

    def flush_context_lines(*, before_result: Match | None = None) -> None:
        """
        Print queued context lines, but not if they would be covered by the passed
        in result.
        """

        for path, line_index, to_print in queued_context_lines:
            if (
                before_result is None
                or path != before_result.path  # from a different file => print
                or line_index
                < before_result.position.lineno - before_context - 1  # Before the context for current result => print
            ):
                print_header(path, line_index)
                print(to_print, file=stdout)
                printed_context_lines.add((path, line_index))
        queued_context_lines[:] = []

    def do_error(message: str) -> None:
        nonlocal errors
        print(message, file=stderr)
        errors += 1

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

        matches += 1
        line_index = result.position.lineno - 1
        if quiet:
            break
        # Previous result's 'after' lines
        flush_context_lines(before_result=result)

        # This result's 'before' lines
        queue_context_lines(result, list(range(max(0, line_index - before_context), line_index)))
        flush_context_lines()

        # The actual result
        print_header(result.path, line_index)
        print(format_match_line(result), file=stdout)
        printed_context_lines.add((result.path, line_index))

        if print_ast:
            print(astpretty.pformat(result.ast_node), file=stdout)

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)

        # This result's 'after' lines
        queue_context_lines(
            result, list(range(line_index + 1, min(len(result.file_lines), line_index + after_context + 1)))
        )
    # Last result
    flush_context_lines()

    return (matches, errors)


# Same formatting as ripgrep:


def _format_context_line_default(result: Match, context_line: str, context_line_index: int) -> str:
    return f"{result.path}-{context_line_index + 1}-{context_line}"


def _format_match_line_default(result: Match) -> str:
    return f"{result.path}:{result.position.lineno}:{result.position.col_offset + 1}:{result.matching_line}"


# Formatting for heading mode


def _format_context_line_heading(result: Match, context_line: str, context_line_index: int) -> str:
    return context_line


def _format_match_line_heading(result: Match) -> str:
    return result.matching_line


def _format_header(path: Pathlike, context_line_index: int) -> str:
    # Start with hash like a Python comment, for integration with tools that
    # consume Python code
    return f"# {path}:{context_line_index + 1}:"
