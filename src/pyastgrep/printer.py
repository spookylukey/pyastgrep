from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from . import xml
from .search import Match


def print_results(
    results: Iterable[Match],
    print_xml: bool = False,
    before_context: int = 0,
    after_context: int = 0,
    stdout=None,
    quiet=False,
) -> tuple[int, int]:
    if stdout is None:
        stdout = sys.stdout
    matches = 0
    errors = 0  # TODO

    printed_context_lines: set[tuple[Path, int]] = set()
    # This is more complex than just iterating through results due to before and after context,
    # which can result in overlapping matches. We have to know if there is another result
    # from the same file before we can print "after" context lines for the current result.

    queued_context_lines: list[tuple[Path, int, str]] = []

    def queue_context_lines(result, context_line_indices):
        for context_line_index in context_line_indices:
            if (result.path, context_line_index) not in printed_context_lines:
                context_line = result.file_lines[context_line_index]
                # Same formatting as ripgrep
                queued_context_lines.append(
                    (result.path, context_line_index, f"{result.path}-{context_line_index + 1}-{context_line}")
                )

    def flush_context_lines(compare_result: Match | None):
        """
        Print queued context lines, but not if they would be covered by the passed
        in result.
        """

        for path, line_index, to_print in queued_context_lines:
            if (
                compare_result is None
                or path != compare_result.path  # from a different file => print
                or line_index
                < result.position.lineno - before_context - 1  # Before the context for current result => print
            ):
                print(to_print, file=stdout)
                printed_context_lines.add((path, line_index))
        queued_context_lines[:] = []

    for result in results:
        matches += 1
        position = result.position
        line_index = position.lineno - 1
        line = result.file_lines[line_index]
        if quiet:
            break

        # Previous result's 'after' lines
        flush_context_lines(result)

        # This result's 'before' lines
        if before_context:
            queue_context_lines(result, list(range(max(0, line_index - before_context), line_index)))
            flush_context_lines(None)

        # The actual result
        print(f"{result.path}:{line_index + 1}:{position.col_offset + 1}:{line}", file=stdout)
        printed_context_lines.add((result.path, line_index))

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)

        # This result's 'after' lines
        if after_context:
            queue_context_lines(
                result, list(range(line_index + 1, min(len(result.file_lines), line_index + after_context + 1)))
            )
    # Last result
    flush_context_lines(None)

    return (matches, errors)