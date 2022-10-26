from __future__ import annotations

import io
import os
import os.path

import pytest

from pyastgrep.cli import main
from tests.utils import chdir

DIR = os.path.dirname(__file__) + "/examples/test_cli"


def assert_stdout(
    capsys,
    args: list[str],
    stdin: str | None = None,
    contains: str | list[str] | None = None,
    does_not_contain: str | list[str] | None = None,
    equals: str | None = None,
):
    try:
        with chdir(DIR):
            main(args, stdin=io.StringIO(stdin) if stdin is not None else None)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    with capsys.disabled():
        if contains is not None:
            if not isinstance(contains, list):
                contains = [contains]
            for text in contains:
                assert text in output
        if does_not_contain is not None:
            if not isinstance(does_not_contain, list):
                does_not_contain = [does_not_contain]
            for text in does_not_contain:
                assert text not in output
        if equals is not None:
            assert output == equals


@pytest.mark.parametrize("arg", ["-h", "--help"])
def test_help(capsys, arg):
    assert_stdout(capsys, [arg], contains="Grep Python files")


def test_search(capsys):
    # Negative test to ensure we aren't accidentally grepping this test code,
    # which could happen if CWD is wrong.
    assert_stdout(capsys, [".//*"], does_not_contain="Not real code")
    assert_stdout(capsys, [".//Name"], contains="misc.py:3:12:    return an_arg")


def test_search_file(capsys):
    assert_stdout(
        capsys,
        [".//Name", "misc.py"],
        contains="return an_arg",
        does_not_contain="return another_arg",
    )


def test_search_files(capsys):
    assert_stdout(
        capsys,
        [".//Name", "misc.py", "other.py"],
        contains=[
            "return an_arg",
            "return another_arg",
        ],
    )


def test_xml_output(capsys):
    assert_stdout(
        capsys,
        ["--xml", ".//Name", "misc.py"],
        contains=[
            "misc.py",
            '<Name lineno="3" col_offset="11" type="str" id="an_arg">',
        ],
    )


def test_quiet(capsys):
    assert_stdout(
        capsys,
        ["--quiet", ".//Name", "misc.py"],
        equals="",
    )
    with chdir(DIR):
        assert main(["--quiet", ".//Name", "misc.py"]) == 0
        assert main(["--quiet", ".//NameXXXX", "misc.py"]) == 1


def test_pipe_stdin(capsys):
    assert_stdout(
        capsys,
        [".//Import", "-"],
        stdin="import os",
        equals="<stdin>:1:1:import os\n",
    )
