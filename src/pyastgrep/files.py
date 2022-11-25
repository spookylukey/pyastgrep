from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Generator, Sequence

from .ignores import DirWalker


@dataclass
class MissingPath:
    path: Path


def get_files_to_search(paths: Sequence[Path | BinaryIO]) -> Generator[Path | BinaryIO | MissingPath, None, None]:
    walker = DirWalker(glob="*.py")
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
    if auto_dedent:
        contents = auto_dedent_code(contents)

    parsed_ast: ast.AST = ast.parse(contents, str(filename))
    # ast.parse does it's own encoding detection, which we have to replicate
    # here since we can't assume utf-8
    encoding = get_encoding(contents)
    str_contents = contents.decode(encoding)
    return str_contents, parsed_ast


def auto_dedent_code(python_code: bytes) -> bytes:
    # Can't use textwrap.dedent, it only works on str,

    # Plus we can have a simpler algo:
    # - optimizing for the case where this is no whitespace prefix
    # - bailing out if the first whitespace prefix is
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
