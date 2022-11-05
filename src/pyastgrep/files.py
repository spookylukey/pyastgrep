from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Generator, Sequence

ENCODING_RE = re.compile(b"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")


@dataclass
class MissingPath:
    path: str


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
