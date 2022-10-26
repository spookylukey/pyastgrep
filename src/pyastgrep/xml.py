from __future__ import annotations

import re
from typing import Any

import elementpath  # XPath 2.0 functions
from lxml import etree
from lxml.etree import _Element, _ElementUnicodeResult, tostring

__all__ = ["tostring", "lxml_query"]


def lxml_query(element: _Element, expression: str) -> list[_Element | Any | _ElementUnicodeResult]:
    return element.xpath(expression)


def elementpath_query(element: _Element, expression: str) -> list[_Element | Any]:
    return elementpath.select(element, expression)


regex_ns = etree.FunctionNamespace("https://github.com/spookylukey/pyastgrep")
regex_ns.prefix = "re"


@regex_ns
def match(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.match(pattern, s) is not None for s in strings)


@regex_ns
def search(ctx: None, pattern: str, strings: list[str]) -> bool:
    return any(re.search(pattern, s) is not None for s in strings)
