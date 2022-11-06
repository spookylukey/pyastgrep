from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Generator, Sequence


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
