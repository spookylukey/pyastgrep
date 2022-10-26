"""Convert AST to XML objects."""
from __future__ import annotations

import ast
import codecs
from functools import partial

from lxml import etree
from lxml.etree import _Element


def _set_encoded_literal(set_fn: partial, literal: bool | int | str | None) -> None:
    if isinstance(literal, (bool, int, float)):
        literal = str(literal)
    if literal is None:
        set_fn("")
    else:
        try:
            set_fn(codecs.encode(literal, "ascii", "xmlcharrefreplace"))
        except Exception:
            set_fn("")  # Null byte - failover to empty string


def _strip_docstring(body: list[ast.AST]) -> list[ast.AST]:
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
        return body[1:]
    return body


def convert_to_xml(
    ast_node: ast.AST,
    node_mappings: dict[_Element, ast.AST],
    *,
    omit_docstrings: bool = False,
) -> _Element:
    """Convert supplied AST node to XML."""
    possible_docstring = isinstance(ast_node, (ast.FunctionDef, ast.ClassDef, ast.Module))

    xml_node = etree.Element(ast_node.__class__.__name__)
    for attr in ("lineno", "col_offset"):
        value = getattr(ast_node, attr, None)
        if value is not None:
            _set_encoded_literal(partial(xml_node.set, attr), value)
    node_mappings[xml_node] = ast_node

    node_fields = zip(ast_node._fields, (getattr(ast_node, attr) for attr in ast_node._fields))

    for field_name, field_value in node_fields:
        if isinstance(field_value, ast.AST):
            field = etree.SubElement(xml_node, field_name)
            field.append(
                convert_to_xml(
                    field_value,
                    node_mappings,
                    omit_docstrings=omit_docstrings,
                )
            )

        elif isinstance(field_value, list):
            field = etree.SubElement(xml_node, field_name)
            if possible_docstring and omit_docstrings and field_name == "body":
                field_value = _strip_docstring(field_value)

            for item in field_value:
                if isinstance(item, ast.AST):
                    field.append(
                        convert_to_xml(
                            item,
                            node_mappings,
                            omit_docstrings=omit_docstrings,
                        )
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
