from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import BinaryIO, Callable, Iterable, Literal, Sequence, Union

from lxml.etree import _Element
from typing_extensions import TypeAlias

from .asts import ast_to_xml
from .ignores import DirWalker, WalkError

Pathlike: TypeAlias = Union[Path, Literal["<stdin>"]]


@dataclass(frozen=True)
class MissingPath:
    path: Path


@dataclass(frozen=True)
class ReadError:
    path: str
    exception: Exception


def get_files_to_search(
    paths: Sequence[Path | BinaryIO],
    include_hidden: bool = False,
    respect_global_ignores: bool = True,
    respect_vcs_ignores: bool = True,
) -> Iterable[Path | BinaryIO | MissingPath | WalkError]:
    """
    Entry-point function for finding files to search.

    By default, POSIX hidden files (starting with `.`) will be skipped - pass
    `include_hidden=True` to include them.

    By default, global .gitignore file will be respected - pass
    `respect_global_ignores=False` to ignore it
    """
    walker = DirWalker(
        glob="*.py",
        include_hidden=include_hidden,
        respect_global_ignores=respect_global_ignores,
        respect_vcs_ignores=respect_vcs_ignores,
    )
    working_dir = Path(os.getcwd())
    for path in paths:
        if isinstance(path, Path):
            if not path.exists():
                yield MissingPath(path)
            elif path.is_file():
                yield path
            else:
                yield from walker.for_dir(path, working_dir).walk()
        else:
            # BinaryIO
            yield path


# See https://peps.python.org/pep-0263/
# I couldn't find a stdlib function for this
_ENCODING_RE = re.compile(b"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")


def get_encoding(python_file_bytes: bytes) -> str:
    # Search in first two lines:
    current_idx = 0
    for line_num in (1, 2):
        # what does a line break character look like
        # if we don't know the encoding? Have to assume '\n' for now
        linebreak_idx = python_file_bytes.find(b"\n", current_idx)
        if linebreak_idx < 0:
            line = python_file_bytes[current_idx:]
        else:
            line = python_file_bytes[current_idx:linebreak_idx]
        coding_match = _ENCODING_RE.match(line)
        if coding_match:
            return coding_match.groups()[0].decode("ascii")
        if linebreak_idx < 0:
            break
        else:
            current_idx = linebreak_idx + 1
    return "utf-8"


def parse_python_file(contents: bytes, filename: str | Path, *, auto_dedent: bool) -> tuple[str, ast.AST]:
    """
    Parse Python file and return a tuple of (contents as string, AST of parsed contents)
    """
    if auto_dedent:
        contents = auto_dedent_code(contents)

    parsed_ast: ast.AST = ast.parse(contents, str(filename))
    # Need `parent` backlinks for StatementContext and for position_from_node:
    for node in ast.walk(parsed_ast):
        for child in ast.iter_child_nodes(node):
            child.parent = node  # type: ignore

    # ast.parse does it's own encoding detection, which we have to replicate
    # here since we can't assume utf-8
    encoding = get_encoding(contents)
    str_contents = contents.decode(encoding)
    return str_contents, parsed_ast


def auto_dedent_code(python_code: bytes) -> bytes:
    # Can't use textwrap.dedent, it only works on str.

    # Plus we can have a simpler algo:
    # - optimize for the case where there is no whitespace prefix
    # - bail out if the first whitespace prefix is
    #   longer than others, because this will be invalid Python
    #   code anyway.

    # Find whitespace prefix of first non-empty line
    m = re.match(rb"(^( +)\S|^\s*\n( +)\S)", python_code, re.MULTILINE)
    if not m:
        return python_code

    groups = m.groups()
    # One of the groups will be `None`
    whitespace_prefix = groups[1] or groups[2]
    strip_amount = len(whitespace_prefix)
    new_lines = []
    for line in python_code.split(b"\n"):
        to_strip = line[0:strip_amount]
        # If not all whitespace, we've made a mistake
        # and the first line indent is not a common indent.
        # (this will be invalid Python code anyway)
        if to_strip.strip() != b"":
            return python_code
        new_lines.append(line[strip_amount:])
    return b"\n".join(new_lines)


@dataclass
class ProcessedPython:
    path: Pathlike
    contents: str
    ast: ast.AST
    xml: _Element
    node_mappings: dict[_Element, ast.AST]


def process_python_file(path: Path) -> ProcessedPython | ReadError:
    """
    Reads the Python file at Python, and converts to XML format.
    Returns a `ProcessessPython` object.

    Returns ReadError for cases of OSError when reading or SyntaxError in the file.
    """
    try:
        contents = path.read_bytes()
    except OSError as ex:
        return ReadError(str(path), ex)

    return process_python_source(filename=path, contents=contents, auto_dedent=False)


process_python_file_cached: Callable[[Path], ProcessedPython | ReadError] = cache(process_python_file)


def process_python_source(
    *,
    filename: Pathlike,
    contents: bytes,
    auto_dedent: bool,
) -> ProcessedPython | ReadError:
    node_mappings: dict[_Element, ast.AST] = {}

    try:
        str_contents, parsed_ast = parse_python_file(contents, filename, auto_dedent=auto_dedent)
    except (SyntaxError, ValueError) as ex:
        return ReadError(str(filename), ex)

    xml_ast = ast_to_xml(
        parsed_ast,
        node_mappings,
    )
    return ProcessedPython(
        path=filename,
        contents=str_contents,
        ast=parsed_ast,
        xml=xml_ast,
        node_mappings=node_mappings,
    )
