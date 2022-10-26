"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
import glob
import os
from dataclasses import dataclass
from io import IOBase
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Generator, Sequence

from lxml.etree import _Element

from . import xml
from .asts import convert_to_xml

if TYPE_CHECKING:
    from typing import Literal

    Pathlike = Path | Literal["<stdin>"]
else:
    # `|` not supported on older Python versions we support,
    # and Literal is only available in Python 3.8+
    Pathlike = Path


@dataclass
class Match:
    path: Pathlike
    file_lines: list[str]
    xml_element: _Element
    position: Position
    ast_node: ast.AST


@dataclass
class Position:
    lineno: int  # 1-indexed, as per AST
    col_offset: int  # 0-indexed, as per AST


@dataclass
class MissingPath:
    path: str


@dataclass
class ReadError:
    path: str
    exception: Exception


def position_from_xml(element: _Element, node_mappings: dict[_Element, ast.AST] | None = None) -> Position | None:
    try:
        linenos = xml.lxml_query(element, "./ancestor-or-self::*[@lineno][1]/@lineno")
        col_offsets = xml.lxml_query(element, "./ancestor-or-self::*[@col_offset][1]/@col_offset")
    except AttributeError:
        raise AttributeError("Element has no ancestor with line number/col offset")
    if linenos and col_offsets:
        return Position(int(linenos[0]), int(col_offsets[0]))
    return None


def get_query_func(*, xpath2: bool) -> Callable:
    if xpath2:
        return xml.elementpath_query
    else:
        return xml.lxml_query


def get_files_to_search(paths: Sequence[str | IOBase]) -> Generator[Path | IOBase | MissingPath, None, None]:
    for path in paths:
        # TODO handle missing files by yielding some kind of error object
        if isinstance(path, IOBase):
            yield path
        elif not os.path.lexists(path):
            yield MissingPath(path)
        elif os.path.isfile(path):
            yield Path(path)
        else:
            for filename in glob.glob(path + "/**/*.py", recursive=True):
                yield Path(filename)


def search_python_files(
    paths: Sequence[str | IOBase],
    expression: str,
    xpath2: bool = False,
) -> Generator[Match | MissingPath | ReadError, None, None]:
    """
    Perform a recursive search through Python files.

    """
    query_func = get_query_func(xpath2=xpath2)

    for path in get_files_to_search(paths):
        node_mappings: dict[_Element, ast.AST] = {}
        source: Pathlike
        if isinstance(path, IOBase):
            source = "<stdin>"
            contents = path.read()
        elif isinstance(path, MissingPath):
            yield path
            continue
        else:
            source = path
            try:
                with open(path) as f:
                    contents = f.read()
            except OSError as ex:
                yield ReadError(str(path), ex)
                continue
        file_lines = contents.splitlines()

        try:
            parsed_ast: ast.AST = ast.parse(contents, str(source))
        except SyntaxError as ex:
            yield ReadError(str(source), ex)
            continue

        xml_ast = convert_to_xml(
            parsed_ast,
            node_mappings,
        )

        matching_elements = query_func(xml_ast, expression)

        for element in matching_elements:
            ast_node = node_mappings.get(element, None)
            position = position_from_xml(element, node_mappings=node_mappings)
            if position is not None and ast_node is not None:
                yield Match(source, file_lines, element, position, ast_node)
