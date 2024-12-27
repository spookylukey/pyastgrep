"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Iterable, Sequence, Union

from lxml.etree import _Element, _ElementUnicodeResult
from typing_extensions import TypeAlias

from pyastgrep.ignores import WalkError

from . import xml
from .files import (
    MissingPath,
    Pathlike,
    ProcessedPython,
    ReadError,
    get_files_to_search,
    process_python_file,
    process_python_source,
)


@dataclass(frozen=True)
class Match:
    path: Pathlike
    file_lines: list[str]
    xml_element: _Element
    position: Position
    ast_node: ast.AST

    @property
    def matching_line(self) -> str:
        return self.file_lines[self.position.lineno - 1]


@dataclass(frozen=True)
class Position:
    lineno: int  # 1-indexed, as per AST
    col_offset: int  # 0-indexed, as per AST


class NonElementReturned(ValueError):
    pass


@dataclass(frozen=True)
class FileFinished:
    """
    Sentinel used for flushing output
    """

    source: Path | BinaryIO


def position_from_node(node: ast.AST) -> Position | None:
    lineno = getattr(node, "lineno", None)
    col_offset = getattr(node, "col_offset", None)
    if lineno is not None and col_offset is not None:
        return Position(int(lineno), int(col_offset))
    if (parent := getattr(node, "parent", None)) is not None:
        return position_from_node(parent)
    return None


XMLQueryFunc: TypeAlias = Callable[[_Element, str], Iterable[Union[_Element, _ElementUnicodeResult]]]


def get_query_func(*, xpath2: bool) -> XMLQueryFunc:
    if xpath2:
        from .xpath2 import elementpath_query

        return elementpath_query
    else:
        return xml.lxml_query


def search_python_files(
    paths: Sequence[Path | BinaryIO],
    expression: str,
    *,
    xpath2: bool = False,
    include_hidden: bool = False,
    respect_global_ignores: bool = True,
    respect_vcs_ignores: bool = True,
    python_file_processor: Callable[[Path], ProcessedPython | ReadError] = process_python_file,
) -> Iterable[Match | MissingPath | ReadError | WalkError | NonElementReturned | FileFinished]:
    """
    Perform a recursive search through Python files.

    Paths may include directories, e.g "." for the current directory.
    .gitignore rules will be applied automatically.

    """
    query_func = get_query_func(xpath2=xpath2)

    for path in get_files_to_search(
        paths,
        include_hidden=include_hidden,
        respect_global_ignores=respect_global_ignores,
        respect_vcs_ignores=respect_vcs_ignores,
    ):
        if isinstance(path, MissingPath):
            yield path
        elif isinstance(path, WalkError):
            yield path
        else:
            yield from search_python_file(path, query_func, expression, python_file_processor=python_file_processor)
            yield FileFinished(path)


def search_python_file(
    path: Path | BinaryIO,
    query_func: XMLQueryFunc,
    expression: str,
    *,
    python_file_processor: Callable[[Path], ProcessedPython | ReadError] = process_python_file,
) -> Iterable[Match | ReadError | NonElementReturned]:
    if isinstance(path, Path):
        processed_python = python_file_processor(path)
    else:
        processed_python = process_python_source(filename="<stdin>", contents=path.read(), auto_dedent=True)

    if isinstance(processed_python, ReadError):
        yield processed_python
        return

    file_lines = processed_python.contents.splitlines()
    matching_elements = query_func(processed_python.xml, expression)

    try:
        iterator = iter(matching_elements)
    except TypeError:
        yield NonElementReturned(matching_elements)
        return

    for element in iterator:
        if not isinstance(element, _Element):
            # Most likely an _ElementUnicodeResult, the result of a query that terminated in
            # an attribute rather than a node. We have no way of getting from here to
            # something representing an AST node.
            yield NonElementReturned(element)
            continue

        ast_node = processed_python.node_mappings.get(element, None)
        if ast_node is not None:
            position = position_from_node(ast_node)
            if position is not None:
                yield Match(
                    path=processed_python.path,
                    file_lines=file_lines,
                    xml_element=element,
                    position=position,
                    ast_node=ast_node,
                )
