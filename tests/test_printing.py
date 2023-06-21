import io
from pathlib import Path

from pyastgrep.printer import StatementContext, StaticContext
from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_printing"


def test_before_context():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], context=StaticContext(before=1)).stdout
    assert (
        output
        == """
context_example.py-2-def func():
context_example.py:3:5:    a_name = "Peter"
context_example.py-6-    another_var = 1
context_example.py:7:5:    a_name = "Fred"
""".lstrip()
    )


def test_after_context():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], context=StaticContext(after=1)).stdout
    assert (
        output
        == """
context_example.py:3:5:    a_name = "Peter"
context_example.py-4-    # Comment
context_example.py:7:5:    a_name = "Fred"
context_example.py-8-    # Final comment
""".lstrip()
    )


def test_overlapping_context():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], context=StaticContext(before=10)).stdout
    assert (
        output
        == """
context_example.py-1-# flake8: noqa
context_example.py-2-def func():
context_example.py:3:5:    a_name = "Peter"
context_example.py-4-    # Comment
context_example.py-5-    "random_string"
context_example.py-6-    another_var = 1
context_example.py:7:5:    a_name = "Fred"
""".lstrip()
    )


def test_overlapping_context_2():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], context=StaticContext(after=10)).stdout
    assert (
        output
        == """
context_example.py:3:5:    a_name = "Peter"
context_example.py-4-    # Comment
context_example.py-5-    "random_string"
context_example.py-6-    another_var = 1
context_example.py:7:5:    a_name = "Fred"
context_example.py-8-    # Final comment
""".lstrip()
    )


def test_encoding():
    # Use stdin method rather than separate file, because one of our linters
    # (pyupgrade) complains about the encoding and workarounds fail.

    # We should be able to decode it, and then print it in normal UTF-8
    file_data = b'# -*- coding: windows-1252 -*-\n\nX = "\x85"\n'
    output = run_print(DIR, './/Name[@id="X"]', [io.BytesIO(file_data)]).stdout
    assert output == '<stdin>:3:1:X = "…"\n'


def test_heading():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], heading=True).stdout
    assert (
        output
        == """
# context_example.py:3:
    a_name = "Peter"

# context_example.py:7:
    a_name = "Fred"
""".lstrip()
    )


def test_heading_with_context():
    # Test edge conditions for grouping
    output = run_print(
        DIR, './/Name[@id="a_name"]', ["context_example.py"], heading=True, context=StaticContext(before=2, after=1)
    ).stdout
    assert (
        output
        == """
# context_example.py:1:
# flake8: noqa
def func():
    a_name = "Peter"
    # Comment
    "random_string"
    another_var = 1
    a_name = "Fred"
    # Final comment
""".lstrip()
    )

    output2 = run_print(
        DIR, './/Name[@id="a_name"]', ["context_example.py"], heading=True, context=StaticContext(before=2, after=0)
    ).stdout
    assert (
        output2
        == """
# context_example.py:1:
# flake8: noqa
def func():
    a_name = "Peter"

# context_example.py:5:
    "random_string"
    another_var = 1
    a_name = "Fred"
""".lstrip()
    )


def test_statement_context_if_body():
    output = run_print(DIR, './/Name[@id="OTHERNAME"]', ["statements.py"], context=StatementContext()).stdout
    assert (
        output
        == """
statements.py:3:5:    OTHERNAME
""".lstrip()
    )


def test_statement_context_if_condition():
    # MYNAME appears in the condition of an if statement, not the body
    output2 = run_print(DIR, './/Name[@id="MYNAME"]', ["statements.py"], context=StatementContext()).stdout
    assert (
        output2
        == """
statements.py:2:4:if MYNAME:
statements.py-3-    OTHERNAME
""".lstrip()
    )


def test_statement_context_expr():
    output = run_print(
        DIR, './/Constant[@value="123"]', ["statements.py"], heading=True, context=StatementContext()
    ).stdout
    assert (
        output
        == """
# statements.py:7:
function_call(
    123,
)
""".lstrip()
    )


def test_statement_context_with_heading_auto_dedent():
    output = run_print(DIR, ".//FunctionDef", ["indented.py"], heading=True, context=StatementContext()).stdout
    assert (
        output
        == '''
# indented.py:5:
def func(self):
    """Docstring"""
'''.lstrip()
    )

    output2 = run_print(
        DIR, './/Constant[@type="str"]', ["indented.py"], heading=True, context=StatementContext()
    ).stdout
    assert (
        output2
        == '''
# indented.py:6:
"""Docstring"""
'''.lstrip()
    )
