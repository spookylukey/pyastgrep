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
) -> None:
    if stdout is None:
        stdout = sys.stdout
    for result in results:
        position = result.position
        line = result.file_lines[position.lineno - 1]
        print(f"{result.path}:{position.lineno}:{position.col_offset + 1}:{line}", file=stdout)

        if print_xml:
            print(xml.tostring(result.xml_element, pretty_print=True).decode("utf-8"), file=stdout)
