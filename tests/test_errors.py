from pathlib import Path

from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_errors"


def test_broken_syntax():
    output = run_print(DIR, "./*/*", ["broken.py-broken"])
    assert output.stderr == "broken.py-broken: invalid syntax (broken.py-broken, line 5)\n"


def test_null_byte():
    output = run_print(DIR, "./*/*", ["contains_null.py-broken"])
    assert output.stderr == "contains_null.py-broken: source code string cannot contain null bytes\n"


def test_missing_file():
    output = run_print(DIR, "./*/*", ["missing.py"])
    assert output.stderr == "missing.py: No such file or directory\n"


def test_non_ast_node_xpath():
    output = run_print(DIR, "count(.//FunctionDef)", ["name.py"])
    assert output.stderr == "Error: XPath expression returned a value that is not an AST node: 1.0\n"
