"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Callable, Generator, Iterable, Sequence

from lxml.etree import _Element

from . import xml
from .asts import ast_to_xml
from .files import MissingPath, get_files_to_search, parse_python_file

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

    @property
    def matching_line(self) -> str:
        return self.file_lines[self.position.lineno - 1]


@dataclass
class Position:
    lineno: int  # 1-indexed, as per AST
    col_offset: int  # 0-indexed, as per AST


@dataclass
class ReadError:
    path: str
    exception: Exception


class NonElementReturned(ValueError):
    pass


def position_from_xml(element: _Element, node_mappings: dict[_Element, ast.AST] | None = None) -> Position | None:
    if not hasattr(element, "xpath"):
        # Most likely an _ElementUnicodeResult, the result of a query that terminated in
        # an attribute rather than a node. We have no way of getting from here to
        # something representing an AST node.
        raise NonElementReturned(element)
    try:
        linenos = xml.lxml_query(element, "./ancestor-or-self::*[@lineno][1]/@lineno")
        col_offsets = xml.lxml_query(element, "./ancestor-or-self::*[@col_offset][1]/@col_offset")
    except AttributeError:
        raise AttributeError("Element has no ancestor with line number/col offset")
    if linenos and col_offsets:
        return Position(int(linenos[0]), int(col_offsets[0]))
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
) -> Generator[Match | MissingPath | ReadError | NonElementReturned, None, None]:
    """
    Perform a recursive search through Python files.

    Paths may include directories, e.g "." for the current directory.
    .gitignore rules will be applied automatically.

    """
    query_func = get_query_func(xpath2=xpath2)

    for path in get_files_to_search(paths):
        node_mappings: dict[_Element, ast.AST] = {}
        source: Pathlike
        auto_dedent = False
        if isinstance(path, MissingPath):
            yield path
            continue
        elif isinstance(path, Path):
            source = path
            try:
                contents = path.read_bytes()
            except OSError as ex:
                yield ReadError(str(path), ex)
                continue
        else:
            source = "<stdin>"
            contents = path.read()
            auto_dedent = True

        try:
            str_contents, parsed_ast = parse_python_file(contents, source, auto_dedent=auto_dedent)
        except SyntaxError as ex:
            yield ReadError(str(source), ex)
            continue

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
            continue

        for element in iterator:
            ast_node = node_mappings.get(element, None)
            try:
                position = position_from_xml(element, node_mappings=node_mappings)
            except NonElementReturned as ex:
                position = None
                yield ex
            if position is not None and ast_node is not None:
                yield Match(source, file_lines, element, position, ast_node)
