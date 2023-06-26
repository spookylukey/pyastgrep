"""Convert AST to XML objects."""
from __future__ import annotations

import ast
import re
import sys
from functools import partial
from typing import Callable

from lxml import etree
from lxml.etree import _Element

illegal_unichrs = [
    (0x00, 0x08),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x7F, 0x84),
    (0x86, 0x9F),
    (0xFDD0, 0xFDDF),
    (0xFFFE, 0xFFFF),
]
if sys.maxunicode >= 0x10000:  # not narrow build
    illegal_unichrs.extend(
        [
            (0x1FFFE, 0x1FFFF),
            (0x2FFFE, 0x2FFFF),
            (0x3FFFE, 0x3FFFF),
            (0x4FFFE, 0x4FFFF),
            (0x5FFFE, 0x5FFFF),
            (0x6FFFE, 0x6FFFF),
            (0x7FFFE, 0x7FFFF),
            (0x8FFFE, 0x8FFFF),
            (0x9FFFE, 0x9FFFF),
            (0xAFFFE, 0xAFFFF),
            (0xBFFFE, 0xBFFFF),
            (0xCFFFE, 0xCFFFF),
            (0xDFFFE, 0xDFFFF),
            (0xEFFFE, 0xEFFFF),
            (0xFFFFE, 0xFFFFF),
            (0x10FFFE, 0x10FFFF),
        ]
    )

illegal_ranges = [rf"{chr(low)}-{chr(high)}" for (low, high) in illegal_unichrs]
xml_illegal_character_regex = "[" + "".join(illegal_ranges) + "]"
illegal_xml_chars_re = re.compile(xml_illegal_character_regex)


def _set_encoded_literal(set_fn: Callable[[str | bytes], None], literal: bool | int | bytes | str | None) -> None:
    if isinstance(literal, (bool, int, float)):
        literal = str(literal)
    if literal is None:
        literal = ""
    if isinstance(literal, bytes):
        literal = literal.decode("utf-8", errors="replace")

    # NUL characters and control characters are not allowed in XML. It's better
    # to be able to search the rest of the string, so we replace
    set_fn(illegal_xml_chars_re.sub("", literal))


def ast_to_xml(
    ast_node: ast.AST,
    node_mappings: dict[_Element, ast.AST],
    *,
    parent: _Element | None = None,
) -> _Element:
    """Convert supplied AST node to XML.
    Mappings from XML back to AST nodes will be recorded in node_mappings
    """
    if parent is None:
        xml_node = etree.Element(ast_node.__class__.__name__)
    else:
        xml_node = etree.SubElement(parent, ast_node.__class__.__name__)
    for attr in ("lineno", "col_offset"):
        value = getattr(ast_node, attr, None)
        if value is not None:
            _set_encoded_literal(partial(xml_node.set, attr), value)
    node_mappings[xml_node] = ast_node

    node_fields = zip(ast_node._fields, (getattr(ast_node, attr) for attr in ast_node._fields))

    for field_name, field_value in node_fields:
        if isinstance(field_value, ast.AST):
            field = etree.SubElement(xml_node, field_name)
            ast_to_xml(
                field_value,
                node_mappings,
                parent=field,
            )

        elif isinstance(field_value, list):
            field = etree.SubElement(xml_node, field_name)
            for item in field_value:
                if isinstance(item, ast.AST):
                    ast_to_xml(
                        item,
                        node_mappings,
                        parent=field,
                    )
                else:
                    subfield = etree.SubElement(field, "item")
                    _set_encoded_literal(partial(setattr, subfield, "text"), item)

        elif field_value is not None:
            # add type attribute e.g. so we can distinguish strings from numbers etc
            # in older Python (< 3.8) type could be identified by Str vs Num and s vs n etc
            # e.g. <Constant lineno="1" col_offset="6" type="int" value="1"/>
            _set_encoded_literal(partial(xml_node.set, "type"), type(field_value).__name__)
            _set_encoded_literal(partial(xml_node.set, field_name), field_value)

    return xml_node
