#!/usr/bin/python
"""
The Command Line Interface using argparse.

For more help use::

    pyastgrep -h

"""
from __future__ import annotations

import argparse

from pyastgrep.printer import print_results
from pyastgrep.search import search

parser = argparse.ArgumentParser(description="Grep Python files uses XPath expressions against the AST")
parser.add_argument(
    "-q",
    "--quiet",
    help="hide output of matches",
    action="store_true",
)
parser.add_argument(
    "-v",
    "--verbose",
    help="increase output verbosity",
    action="store_true",
)
parser.add_argument(
    "-x",
    "--xml",
    help="print only the matching XML elements",
    action="store_true",
)
parser.add_argument(
    "-R",
    "--no-recurse",
    help="ignore subdirectories, searching only files in the specified directory",
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
    "--xpath2",
    help="Use XPath 2.0 functions. This currently makes matching significantly slower, "
    "and re: functions are not supported",
    action="store_true",
    default=False,
)
parser.add_argument(
    "expr",
    help="XPath search expression",
)
parser.add_argument(
    "path",
    help="Files or directory to search, defaults to current directory",
    nargs="*",
)


def main(sys_args: list[str] | None = None) -> None:
    """Entrypoint for CLI."""
    args = parser.parse_args(args=sys_args)

    before_context = args.before_context or args.context
    after_context = args.after_context or args.context
    if (before_context or after_context) and args.quiet:
        print("ERROR: Context cannot be specified when suppressing output.")
        exit(1)

    if len(args.path) == 0:
        paths = ["."]
    else:
        paths = args.path
    print_results(
        search(
            paths,
            args.expr,
            xpath2=args.xpath2,
        ),
        print_xml=args.xml,
        before_context=before_context,
        after_context=after_context,
    )


if __name__ == "__main__":
    main()
