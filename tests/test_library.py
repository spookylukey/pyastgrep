"""
Tests for the documented library API.
"""
# This may duplicate tests elsewhere, but here we are testing everything that we
# document as being public API. Test failures are breaking changes.

import ast
from pathlib import Path

from pyastgrep.api import Match, Position, search_python_files

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
