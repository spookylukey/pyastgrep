from __future__ import annotations

import sys
from typing import Protocol

from pyastgrep.search import Match

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


class UseColor(StrEnum):
    # The choices here are based on ripgrep
    NEVER = "never"
    AUTO = "auto"
    ALWAYS = "always"

    # ANSI - not implemented, we support only ANSI at the moment,
    # we'd need someone to implement and test Windows color escaping


# https://stackoverflow.com/a/33206814/182604
class Colors:
    "ANSI color codes"
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"


class Styles:
    BOLD = "\033[1m"
    END = "\033[0m"


class Colorer(Protocol):
    def color_path(self, path: str) -> str:
        ...

    def color_lineno(self, lineno: int) -> str:
        ...

    def color_match(self, match: Match) -> str:
        ...


class NullColorer:
    def color_path(self, path: str) -> str:
        return path

    def color_lineno(self, lineno: int) -> str:
        return str(lineno)

    def color_match(self, match: Match) -> str:
        return match.matching_line


class AnsiColorer:
    def __init__(self, path_colors: list[str], lineno_colors: list[str], match_colors: list[str]):
        self.path_color = "".join(path_colors)
        self.lineno_color = "".join(lineno_colors)
        self.match_color = "".join(match_colors)

    def color_path(self, path: str) -> str:
        return f"{self.path_color}{path}{Styles.END}"

    def color_lineno(self, lineno: int) -> str:
        return f"{self.lineno_color}{lineno}{Styles.END}"

    def color_match(self, match: Match) -> str:
        # A match could be an AST node as big as a function or class. In this
        # case:
        # 1) it doesn't make much sense to color it
        # 2) it would be much harder to color it, because our current
        #    implementation treats only the first line as the match line,
        #    and later lines are printed as context lines

        # So, we only color matches if they start and end on the same line.
        ast_node = match.ast_node
        if match.position.lineno == ast_node.lineno == ast_node.end_lineno:  # type: ignore [attr-defined]
            raw_line = match.matching_line
            before = raw_line[0 : ast_node.col_offset]  # type: ignore [attr-defined]
            matched = raw_line[ast_node.col_offset : ast_node.end_col_offset]  # type: ignore [attr-defined]
            after = raw_line[ast_node.end_col_offset :]  # type: ignore [attr-defined]
            return f"{before}{self.match_color}{matched}{Styles.END}{after}"

        else:
            return match.matching_line


# Based on ripgrep - https://github.com/BurntSushi/ripgrep/blob/304a60e8e9d4b2a42dc3dfb1ba4cef6d7bf92515/crates/printer/src/color.rs#L14
def make_default_colorer() -> Colorer:
    return AnsiColorer(
        path_colors=[Colors.MAGENTA], lineno_colors=[Colors.GREEN], match_colors=[Colors.RED, Styles.BOLD]
    )
