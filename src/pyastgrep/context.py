from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pyastgrep import ast_utils

from .search import Match

# Context types


class ContextType(Protocol):
    def get_context_lines_for_result(self, result: Match) -> tuple[int, int]:
        """
        Return the number lines to use for context as (before, after) tuple
        """


@dataclass(frozen=True)
class StaticContext:
    before: int = 0
    after: int = 0

    def get_context_lines_for_result(self, result: Match) -> tuple[int, int]:
        return (self.before, self.after)


class StatementContext:
    def get_context_lines_for_result(self, result: Match) -> tuple[int, int]:
        result_node = result.ast_node
        statement_node = ast_utils.get_ast_statement_node(result_node)
        first_line = statement_node.lineno
        if hasattr(statement_node, "decorator_list"):
            first_line = min((first_line, *(n.lineno for n in statement_node.decorator_list)))
        before_context = result_node.lineno - first_line
        if isinstance(statement_node.end_lineno, int):
            after_context = statement_node.end_lineno - result_node.lineno
        else:
            after_context = 0
        return (before_context, after_context)
