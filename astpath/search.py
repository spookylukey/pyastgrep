"""Functions for searching the XML from file, file contents, or directory."""


from __future__ import print_function

import ast
import os
from itertools import islice, repeat

from . import xml

from .asts import convert_to_xml


PYTHON_EXTENSION = '{}py'.format(os.path.extsep)


def find_in_ast(xml_ast, expr, node_mappings=None):
    """Find items matching expression expr in an XML AST."""
    results = xml.lxml_query(xml_ast, expr)
    return positions_from_xml(results, node_mappings=node_mappings)


def positions_from_xml(elements, node_mappings=None):
    """Given a list of elements, return a list of (line, col) numbers."""
    positions = []
    for element in elements:
        try:
            linenos = xml.lxml_query(element, './ancestor-or-self::*[@lineno][1]/@lineno')
            col_offsets = xml.lxml_query(element, './ancestor-or-self::*[@col_offset][1]/@col_offset')
        except AttributeError:
            raise AttributeError("Element has no ancestor with line number/col offset")

        if linenos and col_offsets:
            positions.append((int(linenos[0]), int(col_offsets[0])))
    return positions


def file_contents_to_xml_ast(contents, omit_docstrings=False, node_mappings=None, filename='<unknown>'):
    """Convert Python file contents (as a string) to an XML AST, for use with find_in_ast."""
    parsed_ast = ast.parse(contents, filename)
    return convert_to_xml(
        parsed_ast,
        omit_docstrings=omit_docstrings,
        node_mappings=node_mappings,
    )


def file_to_xml_ast(filename, omit_docstrings=False, node_mappings=None):
    """Convert a file to an XML AST, for use with find_in_ast."""
    with open(filename, 'r') as f:
        contents = f.read()
    return file_contents_to_xml_ast(
        contents,
        omit_docstrings=omit_docstrings,
        node_mappings=node_mappings,
        filename=filename,
    )


def search(
        directory, expression, print_matches=False, print_xml=False,
        verbose=False, abspaths=False, recurse=True,
        before_context=0, after_context=0, extension=PYTHON_EXTENSION
):
    """
    Perform a recursive search through Python files.

    Only for files in the given directory for items matching the specified
    expression.
    """

    if os.path.isfile(directory):
        if recurse:
            raise ValueError("Cannot recurse when only a single file is specified.")
        files = (('', None, [directory]),)
    elif recurse:
        files = os.walk(directory)
    else:
        files = ((directory, None, [
            item
            for item in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, item))
        ]),)
    global_matches = []
    for root, __, filenames in files:
        python_filenames = (
            os.path.join(root, filename)
            for filename in filenames
            if filename.endswith(extension)
        )
        for filename in python_filenames:
            node_mappings = {}
            try:
                with open(filename, 'r') as f:
                    contents = f.read()
                file_lines = contents.splitlines()
                xml_ast = file_contents_to_xml_ast(
                    contents,
                    node_mappings=node_mappings,
                )
            except Exception:
                if verbose:
                    print("WARNING: Unable to parse or read {}".format(
                        os.path.abspath(filename) if abspaths else filename
                    ))
                continue  # unparseable

            matching_elements = xml.lxml_query(xml_ast, expression)

            if print_xml:
                for element in matching_elements:
                    print(xml.tostring(xml_ast, pretty_print=True))

            matching_positions = positions_from_xml(matching_elements, node_mappings=node_mappings)
            global_matches.extend(zip(repeat(filename), matching_positions))

            if print_matches:
                for (matched_lineno, col_offset) in matching_positions:
                    matching_lines = list(context(
                        file_lines, matched_lineno - 1, before_context, after_context
                    ))
                    for lineno, line in matching_lines:
                        print('{path}:{lineno}:{colno}:{line}'.format(
                            path=os.path.abspath(filename) if abspaths else filename,
                            lineno=lineno + 1,
                            colno=col_offset + 1,
                            sep='>' if lineno == matched_lineno - 1 else ' ',
                            line=line,
                        ))
                    if before_context or after_context:
                        print()

    return global_matches


def context(lines, index, before=0, after=0, both=0):
    """
    Yield of 2-tuples from lines around the index. Like grep -A, -B, -C.

    before and after are ignored if a value for both is set. Example usage::

        >>>list(context('abcdefghij', 5, before=1, after=2))
        [(4, 'e'), (5, 'f'), (6, 'g'), (7, 'h')]

    :arg iterable lines: Iterable to select from.
    :arg int index: The item of interest.
    :arg int before: Number of lines of context before index.
    :arg int after: Number of lines of context after index.
    :arg int both: Number of lines of context either side of index.
    """
    before, after = (both, both) if both else (before, after)
    start = max(0, index - before)
    end = index + 1 + after
    return islice(enumerate(lines), start, end)
