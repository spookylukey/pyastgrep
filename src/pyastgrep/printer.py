from typing import Iterable

from .search import Match


def print_results(
    results: Iterable[Match],
    print_xml: bool = False,
    before_context: int = 0,
    after_context: int = 0,
) -> None:
    for result in results:
        position = result.position
        line = result.file_lines[position.lineno - 1]
        print(f"{result.path}:{position.lineno}:{position.col_offset + 1}:{line}")

        # if print_xml:
        #     for element in matching_elements:
        #         print(xml.tostring(element, pretty_print=True).decode("utf-8"))
