import io
from pathlib import Path

from pyastgrep.printer import StaticContext
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
