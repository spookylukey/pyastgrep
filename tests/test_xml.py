import sys
from pathlib import Path

from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_xml"


def test_literals():
    # We need a way to distinguish between different literals
    if sys.version_info < (3, 8):
        expr_int = ".//Num"
        expr_string = ".//Str"
    else:
        expr_int = './/Constant[@type="int"]'
        expr_string = './/Constant[@type="str"]'

    output_int = run_print(DIR, expr_int, print_xml=True).stdout
    output_string = run_print(DIR, expr_string, print_xml=True).stdout
    assert "assigned_int" in output_int
    assert "assigned_string" not in output_int

    assert "assigned_int" not in output_string
    assert "assigned_string" in output_string


def test_re_match():
    output = run_print(DIR, './/Name[re:match("assigned_.*", @id)]').stdout
    assert "assigned_int" in output
    assert "assigned_str" in output

    output2 = run_print(DIR, './/Name[re:match("sign", @id)]').stdout
    assert "assigned_int" not in output2


def test_re_search():
    output = run_print(DIR, './/Name[re:search("_.nt", @id)]').stdout
    assert "assigned_int" in output
    assert "assigned_str" not in output


def test_lower_case():
    output = run_print(DIR, './/ClassDef[lower-case(@name) = "myclass"]', xpath2=True).stdout
    assert "MyClass" in output


def test_attribute():
    """
    XPath expressions resolving to attributes don't return anything
    """
    output = run_print(DIR, ".//Name/@id")
    assert output.stdout == ""
    assert "XPath expression returned a value that is not an AST node: assigned_string" in output.stderr
    assert output.retval[0] == 0
    assert output.retval[1] > 0
