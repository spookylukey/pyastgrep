from __future__ import annotations

import contextlib
import io
import os
from dataclasses import dataclass

from pyastgrep.printer import print_results
from pyastgrep.search import search_python_files

if hasattr(contextlib, "chdir"):
    chdir = contextlib.chdir  # type: ignore[attr-defined]
else:
    # Python < 3.11
    class chdir(contextlib.AbstractContextManager):  # type: ignore[no-redef]
        """Non thread-safe context manager to change the current working directory."""

        def __init__(self, path: str):
            self.path = path
            self._old_cwd: list[str] = []

        def __enter__(self):
            self._old_cwd.append(os.getcwd())
            os.chdir(self.path)

        def __exit__(self, *excinfo):
            os.chdir(self._old_cwd.pop())


@dataclass
class Output:
    stdout: str
    stderr: str
    retval: tuple[int, int]


def run_print(
    cwd: str,
    expr: str,
    paths: list[str] | None = None,
    xpath2: bool = False,
    print_xml: bool = False,
    before_context: int = 0,
    after_context: int = 0,
) -> Output:
    # As much as possible, we're avoiding capsys or other techniques that
    # capture stdin/out, because they interacts badly with trying to do REPL
    # programming and debugging
    # https://lukeplant.me.uk/blog/posts/repl-python-programming-and-debugging-with-ipython/

    stdout = io.StringIO()
    stderr = io.StringIO()
    with chdir(cwd):
        retval = print_results(
            search_python_files(paths or ["."], expr, xpath2=xpath2),
            stdout=stdout,
            stderr=stderr,
            print_xml=print_xml,
            before_context=before_context,
            after_context=after_context,
        )
    return Output(stdout=stdout.getvalue(), stderr=stderr.getvalue(), retval=retval)
