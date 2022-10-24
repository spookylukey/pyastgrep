import sys
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
    for result in results:
        matches += 1
        position = result.position
        line = result.file_lines[position.lineno - 1]
        if quiet:
            break
        print(f"{result.path}:{position.lineno}:{position.col_offset + 1}:{line}", file=stdout)

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)

    return (matches, errors)
