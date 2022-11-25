"""
CLI for pyastdump
"""
import argparse
import sys
from pathlib import Path

from . import xml
from .asts import ast_to_xml
from .files import parse_python_file

parser = argparse.ArgumentParser(
    prog="pyastdump",
    description="Dump Python AST as XML, in the format used by pyastgrep.",
)
parser.add_argument(
    "path",
    help="Python file to dump. Use - for stdin",
)


def main() -> int:
    args = parser.parse_args()
    path = args.path
    if path == "-":
        auto_dedent = True
        contents = sys.stdin.buffer.read()
    else:
        auto_dedent = False
        contents = Path(path).read_bytes()
    _, ast = parse_python_file(contents, path, auto_dedent=auto_dedent)
    xml_root = ast_to_xml(ast, {})
    print(xml.tostring(xml_root, pretty_print=True).decode("utf-8"), file=sys.stdout, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
