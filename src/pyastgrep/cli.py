"""
The Command Line Interface using argparse.

For more help use::

    pyastgrep -h

"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import BinaryIO

from lxml.etree import XPathEvalError

from pyastgrep import __version__
from pyastgrep.printer import print_results
from pyastgrep.search import search_python_files

NAME_AND_VERSION = "pyastgrep " + __version__
parser = argparse.ArgumentParser(
    prog=NAME_AND_VERSION,
    description="Grep Python files uses XPath expressions against the AST",
)
parser.add_argument("--version", action="version", version=NAME_AND_VERSION + f", Python {sys.version}")
parser.add_argument(
    "-q",
    "--quiet",
    help="hide output of matches",
    action="store_true",
)
parser.add_argument(
    "--ast",
    help="pretty-print the matching AST objects",
    action="store_true",
)
parser.add_argument(
    "--xml",
    help="pretty-print the matching XML elements",
    action="store_true",
)
parser.add_argument(
    "-A",
    "--after-context",
    help="lines of context to display after matching line",
    type=int,
    default=0,
)
parser.add_argument(
    "-B",
    "--before-context",
    help="lines of context to display after matching line",
    type=int,
    default=0,
)
parser.add_argument(
    "-C",
    "--context",
    help="lines of context to display before and after matching line",
    type=int,
    default=0,
)
parser.add_argument(
    "--css",
    help="interpret expression as a CSS selector",
    action="store_true",
)
parser.add_argument(
    "--xpath2",
    help="use XPath 2.0 functions and selectors. This currently makes matching significantly slower, "
    "and re:match and re:search functions are not supported",
    action="store_true",
    default=False,
)
parser.add_argument(
    "expr",
    help="XPath search expression",
)
parser.add_argument(
    "path",
    help="Zero or more files or directory to search. Search defaults to current directory if omitted. Use - for stdin",
    nargs="*",
)

MATCH_FOUND = 0
NO_MATCH_FOUND = 1
ERROR = 2


def main(sys_args: list[str] | None = None, stdin: BinaryIO | None = None) -> int:
    """Entrypoint for CLI."""
    args = parser.parse_args(args=sys_args)

    before_context = args.before_context or args.context
    after_context = args.after_context or args.context
    if (before_context or after_context) and args.quiet:
        print("ERROR: Context cannot be specified when suppressing output.", file=sys.stderr)
        return ERROR

    if stdin is None:
        # Need to use .buffer here, to get bytes version, not text
        # mypy thinks type is `typing.BinaryIO`, which is not a runtime thing
        # we can `isinstance` against, so we have to cast.
        stdin = sys.stdin.buffer

    paths: list[Path | BinaryIO]
    if len(args.path) == 0:
        paths = [Path(".")]
    else:
        paths = [stdin if p == "-" else Path(p) for p in args.path]

    expr = args.expr
    if args.css:
        import cssselect

        try:
            expr = cssselect.GenericTranslator().css_to_xpath(expr, prefix=".//")
        except cssselect.SelectorError:
            print(f"Invalid CSS selector: {expr}", file=sys.stderr)
            return ERROR

    try:
        matches, errors = print_results(
            search_python_files(
                paths,
                expr,
                xpath2=args.xpath2,
            ),
            print_xml=args.xml,
            print_ast=args.ast,
            quiet=args.quiet,
            before_context=before_context,
            after_context=after_context,
        )
    except XPathEvalError:
        print(f"Invalid XPath expression: {expr}", file=sys.stderr)
        return ERROR
    # Match ripgrep:
    if errors and not args.quiet:
        return ERROR
    elif matches:
        return MATCH_FOUND
    return NO_MATCH_FOUND


if __name__ == "__main__":
    sys.exit(main())
