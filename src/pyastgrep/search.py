"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
import glob
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generator

from lxml.etree import _Element

from . import xml
from .asts import convert_to_xml


@dataclass
class Match:
    path: Path
    file_lines: list[str]
    xml_element: _Element
    position: Position


@dataclass
class Position:
    lineno: int  # 1-indexed, as per AST
    col_offset: int  # 0-indexed, as per AST


def position_from_xml(element: _Element, node_mappings: dict[_Element, ast.AST] | None = None) -> Position | None:
    try:
        linenos = xml.lxml_query(element, "./ancestor-or-self::*[@lineno][1]/@lineno")
        col_offsets = xml.lxml_query(element, "./ancestor-or-self::*[@col_offset][1]/@col_offset")
    except AttributeError:
        raise AttributeError("Element has no ancestor with line number/col offset")
    if linenos and col_offsets:
        return Position(int(linenos[0]), int(col_offsets[0]))
    return None


def file_contents_to_xml_ast(
    contents: str,
    omit_docstrings: bool = False,
    node_mappings: dict[_Element, ast.AST] | None = None,
    filename: str = "<unknown>",
) -> _Element:
    """Convert Python file contents (as a string) to an XML AST, for use with find_in_ast."""
    parsed_ast: ast.AST = ast.parse(contents, filename)
    return convert_to_xml(
        parsed_ast,
        omit_docstrings=omit_docstrings,
        node_mappings=node_mappings,
    )


def get_query_func(*, xpath2: bool) -> Callable:
    if xpath2:
        return xml.elementpath_query
    else:
        return xml.lxml_query


def get_files_to_search(paths: list[str]) -> Generator[Path, None, None]:
    for path in paths:
        # TODO handle missing files by yielding some kind of error object
        if os.path.isfile(path):
            yield Path(path)
        else:
            for filename in glob.glob(path + "/**/*.py", recursive=True):
                yield Path(filename)


def search_python_files(
    paths: list[str],
    expression: str,
    xpath2: bool = False,
) -> Generator[Match, None, None]:
    """
    Perform a recursive search through Python files.

    """
    query_func = get_query_func(xpath2=xpath2)

    for path in get_files_to_search(paths):
        node_mappings: dict[_Element, ast.AST] = {}
        try:
            with open(path) as f:
                contents = f.read()
            file_lines = contents.splitlines()
            xml_ast = file_contents_to_xml_ast(
                contents,
                node_mappings=node_mappings,
            )
        except Exception:
            # TODO yield warning
            continue  # unparseable

        matching_elements = query_func(xml_ast, expression)

        for element in matching_elements:
            position = position_from_xml(element, node_mappings=node_mappings)
            if position is not None:
                yield Match(path, file_lines, element, position)
