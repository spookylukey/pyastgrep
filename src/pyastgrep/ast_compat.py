"""
Compatibility module for different ast stdlib versions
"""

import ast

# See https://docs.python.org/3/library/ast.html

"""
For changes between versions, try this one liner in bash/zsh:

diff -u <(python3.10 -c 'import ast; print("\n".join(sorted(dir(ast))))') \
        <(python3.11 -c 'import ast; print("\n".join(sorted(dir(ast))))')
"""


BLOCK_AST = tuple(
    i
    for i in [
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Module,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.If,
        ast.With,
        ast.Try,
        getattr(ast, "TryStar", None),
        getattr(ast, "match_case", None),
    ]
    if i
)

STATEMENT_AST = BLOCK_AST + tuple(
    i
    for i in [
        ast.Return,
        ast.Delete,
        ast.Assign,
        ast.AugAssign,
        ast.AnnAssign,
        ast.AsyncWith,
        getattr(ast, "Match", None),
        ast.Raise,
        ast.Assert,
        ast.Import,
        ast.ImportFrom,
        ast.Global,
        ast.Nonlocal,
        ast.Pass,
        ast.Break,
        ast.Continue,
        # Specifically excluding ast.Expr, as that matches everything.
    ]
    if i
)
