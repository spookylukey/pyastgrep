import contextlib
import os
import os.path

import pytest

from pyastgrep.cli import main

if hasattr(contextlib, "chdir"):
    chdir = contextlib.chdir
else:
    # Python < 3.11
    class chdir(contextlib.AbstractContextManager):
        """Non thread-safe context manager to change the current working directory."""

        def __init__(self, path):
            self.path = path
            self._old_cwd = []

        def __enter__(self):
            self._old_cwd.append(os.getcwd())
            os.chdir(self.path)

        def __exit__(self, *excinfo):
            os.chdir(self._old_cwd.pop())


def assert_stdout_contains(capsys, args, text):
    assert_stdout(capsys, args, lambda output: text in output)


def assert_stdout_does_not_contain(capsys, args, text):
    assert_stdout(capsys, args, lambda output: text not in output)


def assert_stdout(capsys, args, func):
    try:
        with chdir(os.path.dirname(__file__) + "/examples/test_cli"):
            main(args)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    with capsys.disabled():
        assert func(output)


@pytest.mark.parametrize("arg", ["-h", "--help"])
def test_help(capsys, arg):
    assert_stdout_contains(capsys, [arg], "Grep Python files")


def test_search(capsys):
    # Negative test to ensure we aren't accidentally grepping this test code,
    # which could happen if CWD is wrong.
    assert_stdout_does_not_contain(capsys, [".//*"], "Not real code")

    assert_stdout_contains(capsys, [".//Name"], "./misc.py:3:12:    return an_arg")
