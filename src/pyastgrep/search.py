"""Functions for searching the XML from file, file contents, or directory."""
import ast
import glob
import os
from itertools import islice, repeat

from . import xml
from .asts import convert_to_xml

PYTHON_EXTENSION = f"{os.path.extsep}py"


def positions_from_xml(elements, node_mappings=None):
    """Given a list of elements, return a list of (line, col) numbers."""
    positions = []
    for element in elements:
        try:
            linenos = xml.lxml_query(element, "./ancestor-or-self::*[@lineno][1]/@lineno")
            col_offsets = xml.lxml_query(element, "./ancestor-or-self::*[@col_offset][1]/@col_offset")
        except AttributeError:
            raise AttributeError("Element has no ancestor with line number/col offset")

        if linenos and col_offsets:
            positions.append((int(linenos[0]), int(col_offsets[0])))
    return positions


def file_contents_to_xml_ast(contents, omit_docstrings=False, node_mappings=None, filename="<unknown>"):
    """Convert Python file contents (as a string) to an XML AST, for use with find_in_ast."""
    parsed_ast = ast.parse(contents, filename)
    return convert_to_xml(
        parsed_ast,
        omit_docstrings=omit_docstrings,
        node_mappings=node_mappings,
    )


def file_to_xml_ast(filename, omit_docstrings=False, node_mappings=None):
    """Convert a file to an XML AST, for use with find_in_ast."""
    with open(filename) as f:
        contents = f.read()
    return file_contents_to_xml_ast(
        contents,
        omit_docstrings=omit_docstrings,
        node_mappings=node_mappings,
        filename=filename,
    )


def get_query_func(*, xpath2: bool):
    if xpath2:
        return xml.elementpath_query
    else:
        return xml.lxml_query


def get_files_to_search(paths):
    for path in paths:
        # TODO handle missing files by yielding some kind of error object
        if os.path.isfile(path):
            yield path
        else:
            yield from glob.glob(path + "/**/*.py", recursive=True)


def search(
    paths,
    expression,
    print_matches=False,
    print_xml=False,
    verbose=False,
    abspaths=False,
    before_context=0,
    after_context=0,
    extension=PYTHON_EXTENSION,
    xpath2=False,
):
    """
    Perform a recursive search through Python files.

    Only for files in the given directory for items matching the specified
    expression.
    """
    query_func = get_query_func(xpath2=xpath2)

    global_matches = []
    for filename in get_files_to_search(paths):
        print(filename)
        node_mappings = {}
        try:
            with open(filename) as f:
                contents = f.read()
            file_lines = contents.splitlines()
            xml_ast = file_contents_to_xml_ast(
                contents,
                node_mappings=node_mappings,
            )
        except Exception:
            if verbose:
                print(f"WARNING: Unable to parse or read {os.path.abspath(filename) if abspaths else filename}")
            continue  # unparseable

        matching_elements = query_func(xml_ast, expression)

        if print_xml:
            for element in matching_elements:
                print(xml.tostring(element, pretty_print=True).decode("utf-8"))

        matching_positions = positions_from_xml(matching_elements, node_mappings=node_mappings)
        global_matches.extend(zip(repeat(filename), matching_positions))

        if print_matches:
            for (matched_lineno, col_offset) in matching_positions:
                matching_lines = list(
                    context(
                        file_lines,
                        matched_lineno - 1,
                        before_context,
                        after_context,
                    )
                )
                for lineno, line in matching_lines:
                    print(
                        "{path}:{lineno}:{colno}:{line}".format(
                            path=os.path.abspath(filename) if abspaths else filename,
                            lineno=lineno + 1,
                            colno=col_offset + 1,
                            line=line,
                        )
                    )
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
