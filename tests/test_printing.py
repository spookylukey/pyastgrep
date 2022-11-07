import io
from pathlib import Path

from tests.utils import run_print

DIR = Path(__file__).parent / "examples" / "test_printing"


def test_before_context():
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], before_context=1).stdout
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
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], after_context=1).stdout
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
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], before_context=10).stdout
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
    output = run_print(DIR, './/Name[@id="a_name"]', ["context_example.py"], after_context=10).stdout
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
