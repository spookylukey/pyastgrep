"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Generator, Iterable, Literal, Sequence, Union

from lxml.etree import _Element

from . import xml
from .asts import ast_to_xml
from .files import MissingPath, get_files_to_search, parse_python_file

Pathlike = Union[Path, Literal["<stdin>"]]


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


@dataclass(frozen=True)
class ReadError:
    path: str
    exception: Exception


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


def get_query_func(*, xpath2: bool) -> Callable[[_Element, str], Iterable[_Element]]:
    if xpath2:
        from .xpath2 import elementpath_query

        return elementpath_query
    else:
        return xml.lxml_query


def search_python_files(
    paths: Sequence[Path | BinaryIO],
    expression: str,
    xpath2: bool = False,
    include_hidden: bool = False,
    respect_global_ignores: bool = True,
    respect_vcs_ignores: bool = True,
) -> Generator[Match | MissingPath | ReadError | NonElementReturned | FileFinished, None, None]:
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
        else:
            yield from search_python_file(path, query_func, expression)
            yield FileFinished(path)


def search_python_file(
    path: Path | BinaryIO,
    query_func: Callable[[ast.AST, str], Iterable[_Element]],
    expression: str,
) -> Generator[Match | ReadError | NonElementReturned, None, None]:
    node_mappings: dict[_Element, ast.AST] = {}
    source: Pathlike
    auto_dedent = False
    if isinstance(path, Path):
        source = path
        try:
            contents = path.read_bytes()
        except OSError as ex:
            yield ReadError(str(path), ex)
            return
    else:
        source = "<stdin>"
        contents = path.read()
        auto_dedent = True

    try:
        str_contents, parsed_ast = parse_python_file(contents, source, auto_dedent=auto_dedent)
    except SyntaxError as ex:
        yield ReadError(str(source), ex)
        return

    file_lines = str_contents.splitlines()
    xml_ast = ast_to_xml(
        parsed_ast,
        node_mappings,
    )

    matching_elements = query_func(xml_ast, expression)

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

        ast_node = node_mappings.get(element, None)
        if ast_node is not None:
            position = position_from_node(ast_node)
            if position is not None:
                yield Match(source, file_lines, element, position, ast_node)
