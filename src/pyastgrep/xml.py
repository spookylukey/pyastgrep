from __future__ import annotations

import re
from typing import Any, Callable, Protocol, TypeVar, cast

from lxml import etree
from lxml.etree import _Element, _ElementUnicodeResult, tostring

__all__ = ["tostring", "lxml_query"]


def lxml_query(element: _Element, expression: str) -> list[_Element | _ElementUnicodeResult]:
    return element.xpath(expression)  # type: ignore[no-any-return]


F = TypeVar("F", bound=Callable[..., Any])


class IdentityProto(Protocol):
    def __call__(self, val: F, /) -> F:
        ...


regex_ns = cast(IdentityProto, etree.FunctionNamespace("https://github.com/spookylukey/pyastgrep"))
regex_ns.prefix = "re"  # type: ignore[attr-defined]


@regex_ns
def match(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.match(pattern, s) is not None for s in strings)


@regex_ns
def search(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.search(pattern, s) is not None for s in strings)
