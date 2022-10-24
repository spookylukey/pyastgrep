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


def assert_stdout(capsys, args, contains=None, does_not_contain=None):
    try:
        with chdir(os.path.dirname(__file__) + "/examples/test_cli"):
            main(args)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    with capsys.disabled():
        if contains is not None:
            assert contains in output
        if does_not_contain is not None:
            assert does_not_contain not in output


@pytest.mark.parametrize("arg", ["-h", "--help"])
def test_help(capsys, arg):
    assert_stdout(capsys, [arg], contains="Grep Python files")


def test_search(capsys):
    # Negative test to ensure we aren't accidentally grepping this test code,
    # which could happen if CWD is wrong.
    assert_stdout(capsys, [".//*"], does_not_contain="Not real code")
    assert_stdout(capsys, [".//Name"], contains="./misc.py:3:12:    return an_arg")
