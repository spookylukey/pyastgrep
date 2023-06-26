"""Convert AST to XML objects."""
from __future__ import annotations

import ast
import codecs
from functools import partial
from typing import Callable

from lxml import etree
from lxml.etree import _Element


def _set_encoded_literal(set_fn: Callable[[str | bytes], None], literal: bool | int | str | None) -> None:
    if isinstance(literal, (bool, int, float)):
        literal = str(literal)
    if literal is None:
        set_fn("")
    else:
        try:
            set_fn(codecs.encode(literal, "ascii", "xmlcharrefreplace"))
        except Exception:
            set_fn("")  # Null byte - failover to empty string


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
