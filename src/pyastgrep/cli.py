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

from . import __version__
from .color import Colorer, NullColorer, UseColor, make_default_colorer
from .context import StatementContext, StaticContext
from .printer import print_results
from .search import search_python_files

NAME_AND_VERSION = "pyastgrep " + __version__
parser = argparse.ArgumentParser(
    prog=NAME_AND_VERSION,
    description="Grep Python files uses XPath expressions against the AST",
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False,
)


def context_parameter(param: str) -> int | StatementContext:
    if param == "statement":
        return StatementContext()
    return int(param)  # Will raise ValueError if invalid, which is handled by argparse


# Names of arguments:
#
# We try to match names from ripgrep where the behaviour is basically the same
parser.add_argument(
    "-h",
    "--help",
    action="help",
    help="Show this help message and exit\n\n",
)
parser.add_argument(
    "--version",
    action="version",
    version=NAME_AND_VERSION + f", Python {sys.version}",
    help="Show program's version number and exit\n\n",
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Hide output of matches\n\n",
    action="store_true",
)
parser.add_argument(
    "--ast",
    help="Pretty-print the matching AST objects\n\n",
    action="store_true",
)
parser.add_argument(
    "--xml",
    help="Pretty-print the matching XML elements\n\n",
    action="store_true",
)
parser.add_argument(
    "-A",
    "--after-context",
    help="Lines of context to display after matching line\n\n",
    type=int,
    default=0,
)
parser.add_argument(
    "-B",
    "--before-context",
    help="Lines of context to display after matching line\n\n",
    type=int,
    default=0,
)
parser.add_argument(
    "-C",
    "--context",
    help="""Lines of context to display before and after matching
line, as an integer.

You can also use '--context=statement' to print the
complete statement of a match. When combined with
--heading, this has some extra behaviour:
  - code is automatically dedented
  - multiple matches within the same statement won't be
    printed twice.
  - matches are not colored
    """,
    type=context_parameter,
    default=0,
)
parser.add_argument(
    "--color",
    help="""Controls when to use colors. Possible values are:
    never    Colors will never be used.
    auto     Use colors if a terminal is detected as the
             output (default)
    always   Colors will always be used regardless of
             where output is sent.
    """,
    type=UseColor,
    default=UseColor.AUTO,
    choices=list(UseColor),
)
parser.add_argument(
    "--css",
    help="Interpret expression as a CSS selector\n\n",
    action="store_true",
)
parser.add_argument(
    "--xpath2",
    help="""Use XPath 2.0 functions and selectors. This currently
makes matching significantly slower, and re:match and
re:search functions are not supported
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "--heading",
    help="""Print the file path and line number as a heading
(formatted as a Python comment) above the results.
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "-.",
    "--hidden",
    help="""Search hidden files and directories, which are skipped
by default. A file or directory is considered hidden if
its base name starts with a dot character ('.').
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "--no-ignore-global",
    help="""Don't respect ignore files that come from \"global\"
sources such as git's `core.excludesFile` configuration
option, which is typically ~/.config/git/ignore or
~/.gitignore
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "--no-ignore-vcs",
    help="""Don't respect version control ignore files such as
.gitignore
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "--debug",
    help="""Print debugging information, especially for why files
are skipped
    """,
    action="store_true",
    default=False,
)
parser.add_argument(
    "expr",
    help="XPath search expression\n\n",
)
parser.add_argument(
    "path",
    help="""Zero or more files or directory to search. Search
defaults to current directory if omitted.
Use - for stdin
    """,
    nargs="*",
)

MATCH_FOUND = 0
NO_MATCH_FOUND = 1
ERROR = 2


def main(sys_args: list[str] | None = None, stdin: BinaryIO | None = None) -> int:
    """Entrypoint for CLI."""
    args = parser.parse_args(args=sys_args)

    if args.debug:
        import logging

        from pathspec import PathSpec
        from pathspec.patterns.gitwildmatch import GitWildMatchPattern

        # Monkey patch PathSpec to have more useful reprs
        PathSpec.__repr__ = lambda self: f"<PathSpec {self.patterns!r}>"  # type: ignore
        GitWildMatchPattern.__repr__ = lambda self: f"<GitWildMatchPattern {self.regex}"  # type: ignore

        logging.basicConfig(level=logging.DEBUG)

    context: StaticContext | StatementContext
    if isinstance(args.context, StatementContext):
        if args.before_context or args.after_context:
            print("ERROR: -A or -B when using --context=statement.", file=sys.stderr)
        context = args.context
    else:
        before_context = args.before_context or args.context
        after_context = args.after_context or args.context
        if (before_context or after_context) and args.quiet:
            print("ERROR: Context cannot be specified when suppressing output.", file=sys.stderr)
            return ERROR
        context = StaticContext(before=before_context, after=after_context)

    if stdin is None:
        # Need to use .buffer here, to get bytes version, not text
        stdin = sys.stdin.buffer
    assert stdin is not None

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

    colorer: Colorer
    color: UseColor = args.color
    if color == UseColor.AUTO:
        if sys.stdout.isatty():
            colorer = make_default_colorer()
        else:
            colorer = NullColorer()
    elif color == UseColor.NEVER:
        colorer = NullColorer()
    elif color == UseColor.ALWAYS:
        colorer = make_default_colorer()

    try:
        matches, errors = print_results(
            search_python_files(
                paths,
                expr,
                xpath2=args.xpath2,
                include_hidden=args.hidden,
                respect_global_ignores=not args.no_ignore_global,
                respect_vcs_ignores=not args.no_ignore_vcs,
            ),
            print_xml=args.xml,
            print_ast=args.ast,
            quiet=args.quiet,
            context=context,
            heading=args.heading,
            colorer=colorer,
        )
    except XPathEvalError:
        print(f"Invalid XPath expression: {expr}", file=sys.stderr)
        return ERROR
    except KeyboardInterrupt:
        sys.exit(1)
    # Match ripgrep:
    if errors and not args.quiet:
        return ERROR
    elif matches:
        return MATCH_FOUND
    return NO_MATCH_FOUND


if __name__ == "__main__":
    sys.exit(main())
