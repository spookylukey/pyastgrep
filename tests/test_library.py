"""
Tests for the documented library API.
"""
# This may duplicate tests elsewhere, but here we are testing everything that we
# document as being public API. Test failures are breaking changes.

import ast
from pathlib import Path

from lxml import etree
from pyastgrep.api import Match, Position, search_python_files
from pyastgrep.files import ProcessedPython, process_python_file_cached

DIR = Path(__file__).parent / "examples" / "test_library"


def test_search_python_files():
    results = list(search_python_files([DIR], ".//For"))
    filtered_results = [result for result in results if isinstance(result, Match)]
    assert len(filtered_results) == 1
    match = filtered_results[0]
    assert match.path == DIR / "example.py"
    assert match.position == Position(lineno=2, col_offset=4)
    assert isinstance(match.ast_node, ast.For)
    assert match.matching_line == "    for item in [1, 2, 3]:"


def test_search_python_files_with_cached_python_processor():
    results = list(search_python_files([DIR], ".//Name", python_file_processor=process_python_file_cached))
    filtered_results = [result for result in results if isinstance(result, Match)]
    assert len(filtered_results) > 0


def null_python_processor(path):
    # Replacement for process_python_file that treats all files as if they
    # were empty.
    return ProcessedPython(path=path, contents="", ast=ast.parse(""), xml=etree.fromstring("<root/>"), node_mappings={})


def test_search_python_files_with_custom_python_processor():
    results = list(search_python_files([DIR], ".//Name", python_file_processor=null_python_processor))
    filtered_results = [result for result in results if isinstance(result, Match)]
    assert len(filtered_results) == 0
