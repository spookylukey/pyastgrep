"""
Compatibility and utility module for different ast stdlib versions

See https://docs.python.org/3/library/ast.html
"""

import ast

"""
For changes between Python versions, try this one liner in bash/zsh:

diff -u <(python3.10 -c 'import ast; print("\n".join(sorted(dir(ast))))') \
        <(python3.11 -c 'import ast; print("\n".join(sorted(dir(ast))))')
"""


# BLOCK_AST and STATEMENT_AST together are based on the 'stmt' rule in the
# Python grammar, plus others that have `body` attributes like Module and
# ExceptHandler. BLOCK_AST are the ones that have a 'body' attribute.
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
        ast.ExceptHandler,
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


def get_ast_statement_node(ast_node: ast.AST) -> ast.AST:
    """
    For a given AST node, return the statement node it belongs to.
    """
    current_node = ast_node
    while True:
        if isinstance(current_node, STATEMENT_AST):
            break
        parent = current_node.parent  # type: ignore

        # If directly in the 'body' of a block statement, this node is
        # 'statement-like' i.e. it is self-contained and could appear at top
        # level in a module in most cases.
        if isinstance(parent, BLOCK_AST) and current_node in parent.body:
            break
        current_node = parent

    return current_node
