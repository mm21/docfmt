"""
Docstring discovery via AST structure.

Docstrings are located purely from the parsed tree — never from token heuristics
or line-content matching. Four kinds are recognized:

- module / class / function: the first statement of a body being `Expr(Constant(str))`
- attribute: a bare string `Expr` statement immediately following an `AnnAssign` or
  `Assign` at module or class level (this covers annotation-only attributes such as
  `package: str`)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator

from .splice import LineIndex

__all__ = [
    "DocstringKind",
    "StringLiteral",
    "DocstringSite",
    "parse_string_literal",
    "iter_docstring_nodes",
    "discover",
]

_PREFIX_CHARS = "rRuU"
_QUOTES = ('"""', "'''", '"', "'")

_BODY_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
_ATTRIBUTE_PARENTS = (ast.Module, ast.ClassDef)


class DocstringKind(StrEnum):
    """
    Kind of docstring, which selects the applicable blank-line rules.
    """

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ATTRIBUTE = "attribute"


@dataclass(frozen=True)
class StringLiteral:
    """
    A single string literal decomposed into its parts.
    """

    prefix: str
    """
    String prefix, e.g. `"r"`; empty for a plain string.
    """

    quote: str
    """
    Quote sequence, one of `\"\"\"`, `'''`, `"`, `'`.
    """

    body: str
    """
    Raw text between the quotes, exactly as written in the source.
    """

    @property
    def is_raw(self) -> bool:
        """
        Whether this is a raw string.
        """
        return "r" in self.prefix.lower()


@dataclass(frozen=True)
class DocstringSite:
    """
    A located docstring, with everything needed to rewrite it in place.
    """

    kind: DocstringKind
    literal: StringLiteral
    start: int
    """
    Character offset of the start of the string literal (including its prefix).
    """

    end: int
    """
    Character offset just past the end of the string literal.
    """

    indent: str
    """
    Leading whitespace of the line the literal starts on.
    """

    stmt_lineno: int
    """
    1-indexed line of the docstring statement.
    """

    stmt_end_lineno: int
    """
    1-indexed last line of the docstring statement.
    """

    next_lineno: int | None
    """
    1-indexed first line of the following sibling statement, if any.
    """

    is_own: bool
    """
    Whether this is the owner's own docstring (first statement of a body) as
    opposed to an attribute docstring.
    """


def parse_string_literal(segment: str) -> StringLiteral | None:
    """
    Parse a source segment as exactly one string literal.

    Returns `None` if the segment is anything else — most importantly implicit
    string concatenation (`"a" "b"`), which is left untouched rather than
    rewritten into a single literal.
    """
    index = 0
    while index < len(segment) and segment[index] in _PREFIX_CHARS:
        index += 1

    prefix = segment[:index]
    if len(prefix) > 1:
        return None

    rest = segment[index:]

    for quote in _QUOTES:
        if rest.startswith(quote):
            break
    else:
        return None

    body_start = len(quote)
    scan = body_start
    while scan < len(rest):
        if rest[scan] == "\\":
            scan += 2
            continue
        if rest.startswith(quote, scan):
            if scan + len(quote) != len(rest):
                # trailing content: concatenation or something unexpected
                return None
            return StringLiteral(prefix=prefix, quote=quote, body=rest[body_start:scan])
        scan += 1

    return None


def iter_docstring_nodes(tree: ast.AST) -> Iterator[ast.Constant]:
    """
    Yield every `Constant` node which docfmt treats as a docstring.

    Shared by discovery and the AST-equivalence gate so that both agree exactly
    on what counts as a docstring.
    """
    for node in ast.walk(tree):
        if not isinstance(node, _BODY_OWNERS):
            continue

        body = node.body
        if not body:
            continue

        if (constant := _is_string_expr(body[0])) is not None:
            yield constant

        if not isinstance(node, _ATTRIBUTE_PARENTS):
            continue

        for index in range(1, len(body)):
            if not isinstance(body[index - 1], (ast.AnnAssign, ast.Assign)):
                continue
            if (constant := _is_string_expr(body[index])) is not None:
                yield constant


def discover(tree: ast.AST, source: str, index: LineIndex) -> list[DocstringSite]:
    """
    Locate every docstring site in the tree, in source order.

    Sites whose literal cannot be parsed as a single string literal are skipped,
    leaving those docstrings untouched.
    """
    sites: list[DocstringSite] = []

    for node in ast.walk(tree):
        if not isinstance(node, _BODY_OWNERS):
            continue

        body = node.body
        if not body:
            continue

        candidates: list[tuple[DocstringKind, int]] = []

        if _is_string_expr(body[0]) is not None:
            candidates.append((_owner_kind(node), 0))

        if isinstance(node, _ATTRIBUTE_PARENTS):
            for position in range(1, len(body)):
                if not isinstance(body[position - 1], (ast.AnnAssign, ast.Assign)):
                    continue
                if _is_string_expr(body[position]) is not None:
                    candidates.append((DocstringKind.ATTRIBUTE, position))

        for kind, position in candidates:
            stmt = body[position]
            constant = _is_string_expr(stmt)
            assert constant is not None

            start = index.offset(constant.lineno, constant.col_offset)
            assert constant.end_lineno is not None
            assert constant.end_col_offset is not None
            end = index.offset(constant.end_lineno, constant.end_col_offset)

            literal = parse_string_literal(source[start:end])
            if literal is None:
                continue

            line_start = index.line_start(constant.lineno)
            leading = source[line_start:start]
            if leading.strip():
                # literal is not the first thing on its line; leave it alone
                continue

            following = body[position + 1] if position + 1 < len(body) else None

            sites.append(
                DocstringSite(
                    kind=kind,
                    literal=literal,
                    start=start,
                    end=end,
                    indent=leading,
                    stmt_lineno=stmt.lineno,
                    stmt_end_lineno=stmt.end_lineno or stmt.lineno,
                    next_lineno=following.lineno if following else None,
                    is_own=position == 0,
                )
            )

    sites.sort(key=lambda site: site.start)
    return sites


def _is_string_expr(node: ast.stmt) -> ast.Constant | None:
    """
    Get the string `Constant` of a bare-string expression statement, if it is one.
    """
    if not isinstance(node, ast.Expr):
        return None
    value = node.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    return value


def _owner_kind(node: ast.AST) -> DocstringKind:
    if isinstance(node, ast.Module):
        return DocstringKind.MODULE
    if isinstance(node, ast.ClassDef):
        return DocstringKind.CLASS
    return DocstringKind.FUNCTION
