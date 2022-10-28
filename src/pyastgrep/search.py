"""Functions for searching the XML from file, file contents, or directory."""
from __future__ import annotations

import ast
import glob
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Callable, Generator, Iterable, Sequence

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


class NonElementReturned(ValueError):
    pass


def position_from_xml(element: _Element, node_mappings: dict[_Element, ast.AST] | None = None) -> Position | None:
    if not hasattr(element, "xpath"):
        # Mostly like an _ElementUnicodeResult, the result of a query that terminated in
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
        return xml.elementpath_query
    else:
        return xml.lxml_query


def get_files_to_search(paths: Sequence[str | BinaryIO]) -> Generator[Path | BinaryIO | MissingPath, None, None]:
    for path in paths:
        if isinstance(path, str):
            if not os.path.exists(path):
                yield MissingPath(path)
            elif os.path.isfile(path):
                yield Path(path)
            else:
                for filename in glob.glob(path + "/**/*.py", recursive=True):
                    yield Path(filename)
        else:
            # BinaryIO
            yield path


ENCODING_RE = re.compile(b"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")


def get_encoding(python_file_bytes: bytes) -> str:
    # Search in first two lines. But what does a line break character look like
    # if we don't know the encoding. Have to assume '\n' for now
    first_lb = python_file_bytes.find(b"\n")
    if first_lb < 0:
        first_lb = 0
    second_lb = python_file_bytes.find(b"\n", first_lb + 1)
    if second_lb < 0:
        second_lb = 0
    last_lb = max(first_lb, second_lb)
    first_two_lines = python_file_bytes[0:last_lb]
    coding_match = ENCODING_RE.match(first_two_lines)
    if coding_match:
        return coding_match.groups()[0].decode("ascii")
    else:
        return "utf-8"


def search_python_files(
    paths: Sequence[str | BinaryIO],
    expression: str,
    xpath2: bool = False,
) -> Generator[Match | MissingPath | ReadError | NonElementReturned, None, None]:
    """
    Perform a recursive search through Python files.

    """
    query_func = get_query_func(xpath2=xpath2)

    for path in get_files_to_search(paths):
        node_mappings: dict[_Element, ast.AST] = {}
        source: Pathlike
        if isinstance(path, MissingPath):
            yield path
            continue
        elif isinstance(path, Path):
            source = path
            try:
                with open(path, "rb") as f:
                    contents = f.read()
            except OSError as ex:
                yield ReadError(str(path), ex)
                continue
        else:
            source = "<stdin>"
            contents = path.read()

        try:
            parsed_ast: ast.AST = ast.parse(contents, str(source))
        except SyntaxError as ex:
            yield ReadError(str(source), ex)
            continue

        encoding = get_encoding(contents)
        file_lines = contents.decode(encoding).splitlines()
        xml_ast = convert_to_xml(
            parsed_ast,
            node_mappings,
        )

        matching_elements = query_func(xml_ast, expression)

        for element in matching_elements:
            ast_node = node_mappings.get(element, None)
            try:
                position = position_from_xml(element, node_mappings=node_mappings)
            except NonElementReturned as ex:
                position = None
                yield ex
            if position is not None and ast_node is not None:
                yield Match(source, file_lines, element, position, ast_node)
