import os.path

from tests.utils import run_print

DIR = os.path.dirname(__file__) + "/examples/test_printing"


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
