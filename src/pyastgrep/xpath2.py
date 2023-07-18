# This is a separate module to avoid importing elementpath if we don't need it
from __future__ import annotations

import elementpath  # XPath 2.0 functions
from lxml.etree import _Element, _ElementUnicodeResult


def elementpath_query(element: _Element, expression: str) -> list[_Element | _ElementUnicodeResult]:
    return elementpath.select(element, expression)  # type: ignore[no-any-return]
