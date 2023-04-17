from __future__ import annotations

import sys
from typing import Iterable, TextIO

from . import xml
from .search import Match, MissingPath, NonElementReturned, Pathlike, ReadError


def print_results(
    results: Iterable[Match | MissingPath | ReadError | NonElementReturned],
    print_xml: bool = False,
    print_ast: bool = False,
    before_context: int = 0,
    after_context: int = 0,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    quiet: bool = False,
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

    printed_context_lines: set[tuple[Pathlike, int]] = set()
    queued_context_lines: list[tuple[Pathlike, int, str]] = []

    def queue_context_lines(result: Match, context_line_indices: list[int]) -> None:
        for context_line_index in context_line_indices:
            if (result.path, context_line_index) not in printed_context_lines:
                context_line = result.file_lines[context_line_index]
                # Same formatting as ripgrep
                queued_context_lines.append(
                    (result.path, context_line_index, f"{result.path}-{context_line_index + 1}-{context_line}")
                )

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
        position = result.position
        line_index = position.lineno - 1
        line = result.matching_line
        if quiet:
            break
        # Previous result's 'after' lines
        flush_context_lines(before_result=result)

        # This result's 'before' lines
        if before_context:
            queue_context_lines(result, list(range(max(0, line_index - before_context), line_index)))
            flush_context_lines()

        # The actual result
        print(f"{result.path}:{line_index + 1}:{position.col_offset + 1}:{line}", file=stdout)
        printed_context_lines.add((result.path, line_index))

        if print_ast:
            print(astpretty.pformat(result.ast_node), file=stdout)

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)

        # This result's 'after' lines
        if after_context:
            queue_context_lines(
                result, list(range(line_index + 1, min(len(result.file_lines), line_index + after_context + 1)))
            )
    # Last result
    flush_context_lines()

    return (matches, errors)
