from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pytest
from pyastgrep.cli import main

from tests.utils import chdir

DIR = Path(__file__).parent / "examples" / "test_cli"


def assert_output(
    capsys,
    args: list[str],
    stdin: str | None = None,
    contains: str | list[str] | None = None,
    does_not_contain: str | list[str] | None = None,
    equals: str | None = None,
    error_equals: str | None = None,
):
    try:
        with chdir(DIR):
            main(args, stdin=io.BytesIO(stdin.encode("utf-8")) if stdin is not None else None)
    except SystemExit:
        pass
    output = capsys.readouterr()
    stdout = output.out
    stderr = output.err
    with capsys.disabled():
        if contains is not None:
            if not isinstance(contains, list):
                contains = [contains]
            for text in contains:
                assert text in stdout
        if does_not_contain is not None:
            if not isinstance(does_not_contain, list):
                does_not_contain = [does_not_contain]
            for text in does_not_contain:
                assert text not in stdout
        if equals is not None:
            assert stdout == equals
        if error_equals is not None:
            assert stderr == error_equals


@pytest.mark.parametrize("arg", ["-h", "--help"])
def test_help(capsys, arg):
    assert_output(capsys, [arg], contains="Grep Python files")


def test_search(capsys):
    # Negative test to ensure we aren't accidentally grepping this test code,
    # which could happen if CWD is wrong.
    assert_output(capsys, [".//*"], does_not_contain="Not real code")
    assert_output(capsys, [".//Name"], contains="misc.py:3:12:    return an_arg")


def test_search_file(capsys):
    assert_output(
        capsys,
        [".//Name", "misc.py"],
        contains="return an_arg",
        does_not_contain="return another_arg",
    )


def test_search_files(capsys):
    assert_output(
        capsys,
        [".//Name", "misc.py", "other.py"],
        contains=[
            "return an_arg",
            "return another_arg",
        ],
    )


def test_search_subdir(capsys):
    assert_output(
        capsys,
        [".//Name", "subdir"],
        contains="return an_arg",
        does_not_contain="return another_arg",
    )


def test_xml_output(capsys):
    assert_output(
        capsys,
        ["--xml", ".//Name", "misc.py"],
        contains=[
            "misc.py",
            '<Name lineno="3" col_offset="11" type="str" id="an_arg">',
        ],
    )


def test_quiet(capsys):
    assert_output(
        capsys,
        ["--quiet", ".//Name", "misc.py"],
        equals="",
    )
    with chdir(DIR):
        assert main(["--quiet", ".//Name", "misc.py"]) == 0
        assert main(["--quiet", ".//NameXXXX", "misc.py"]) == 1


def test_pipe_stdin(capsys):
    assert_output(
        capsys,
        [".//Import", "-"],
        stdin="import os",
        equals="<stdin>:1:1:import os\n",
    )


def test_print_ast(capsys):
    expected = """<stdin>:1:1:a + b
Expr(
    lineno=1,
    col_offset=0,
    end_lineno=1,
    end_col_offset=5,
    value=BinOp(
        lineno=1,
        col_offset=0,
        end_lineno=1,
        end_col_offset=5,
        left=Name(lineno=1, col_offset=0, end_lineno=1, end_col_offset=1, id='a', ctx=Load()),
        op=Add(),
        right=Name(lineno=1, col_offset=4, end_lineno=1, end_col_offset=5, id='b', ctx=Load()),
    ),
)
"""
    assert_output(
        capsys,
        ["--ast", "./*/*", "-"],
        stdin="a + b",
        equals=expected,
    )


def test_invalid_xpath(capsys):
    assert_output(
        capsys,
        ["some nonsense"],
        error_equals="Invalid XPath expression: some nonsense\n",
    )


def test_stdin_bytes():
    # To really test what is going on with stdin, we go the whole way and use a
    # subprocess on ourselves. This catches the bug where we use stdin in text
    # mode, which causes a TypeError
    process = subprocess.Popen(
        ["pyastgrep", "-q", "./*/*", "-"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(input=b"x = 1\n")
    assert stderr == b""
    assert stdout == b""
    assert process.returncode == 0

    # Another way of testing the same thing, without relying on getting
    # Popen stuff correct
    result = subprocess.run("echo 'x = 1' | pyastgrep --xml './*/*' -", shell=True, capture_output=True)
    assert result.stdout.startswith(b"<stdin>:1:1:x = 1\n<Assign")


def test_css_select(capsys):
    assert_output(
        capsys,
        ["--css", "For > target > Name", "-"],
        stdin="""
for item in items:
    pass
for idx, x in enumerate(items):
    pass
""".strip(),
        equals="<stdin>:1:5:for item in items:\n",
    )


def test_css_select_error(capsys):
    assert_output(
        capsys,
        ["--css", ".//For/Name", "-"],
        stdin="""
for item in items:
    pass
""".strip(),
        error_equals="Invalid CSS selector: .//For/Name\n",
    )


def test_pyastdump_stdin():
    result = subprocess.run("echo 'x = 1' | pyastdump -", shell=True, capture_output=True)
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == (
        b"<Module>\n"
        b"  <body>\n"
        b'    <Assign lineno="1" col_offset="0">\n'
        b"      <targets>\n"
        b'        <Name lineno="1" col_offset="0" type="str" id="x">\n'
        b"          <ctx>\n"
        b"            <Store/>\n"
        b"          </ctx>\n"
        b"        </Name>\n"
        b"      </targets>\n"
        b"      <value>\n"
        b'        <Constant lineno="1" col_offset="4" type="int" value="1"/>\n'
        b"      </value>\n"
        b"    </Assign>\n"
        b"  </body>\n"
        b"  <type_ignores/>\n"
        b"</Module>\n"
    )


def test_pyastdump_syntax_error():
    result = subprocess.run("echo 'x =' | pyastdump -", shell=True, capture_output=True)
    assert result.returncode != 0
    assert b"SyntaxError" in result.stderr


def test_pyastdump_read_error():
    result = subprocess.run("pyastdump missing", shell=True, capture_output=True)
    assert result.returncode != 0
    assert b"missing" in result.stderr


def test_pyastdump_remove_indent():
    result = subprocess.run("echo '    x = 1\n    y = 2' | pyastdump -", shell=True, capture_output=True)
    assert result.returncode == 0
    assert b"indent" not in result.stderr
