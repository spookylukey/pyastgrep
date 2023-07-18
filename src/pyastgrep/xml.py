from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable

from lxml import etree
from lxml.etree import _Element, _ElementUnicodeResult, tostring

__all__ = ["tostring", "lxml_query"]

if TYPE_CHECKING:
    from typing import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


def lxml_query(element: _Element, expression: str) -> list[_Element | _ElementUnicodeResult]:
    return element.xpath(expression)  # type: ignore[no-any-return]


regex_ns: Callable[[Callable[P, R]], Callable[P, R]] = etree.FunctionNamespace(
    "https://github.com/spookylukey/pyastgrep"
)
regex_ns.prefix = "re"  # type: ignore[attr-defined]


@regex_ns
def match(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.match(pattern, s) is not None for s in strings)


@regex_ns
def search(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.search(pattern, s) is not None for s in strings)
