"""
Formatting orchestration.

Discovers docstring sites, builds a set of non-overlapping edits, applies them in
one pass, and verifies the result against the safety gates before returning it.
"""

from __future__ import annotations

import ast

from .config import PRESERVE, BlankLines, Config
from .discovery import DocstringKind, DocstringSite, discover
from .errors import InternalError, ParseError
from .gates import assert_ast_equivalent
from .interior import format_literal
from .splice import Edit, LineIndex, apply_edits

__all__ = [
    "format_source",
    "format_source_checked",
]

_AFTER_RULES = {
    DocstringKind.MODULE: "blank_line_after_module_docstring",
    DocstringKind.CLASS: "blank_line_after_class_docstring",
    DocstringKind.FUNCTION: "blank_line_after_function_docstring",
    DocstringKind.ATTRIBUTE: "blank_line_after_attribute_docstring",
}


def _in_line_range(site: DocstringSite, config: Config) -> bool:
    if config.line_range is None:
        return True
    low, high = config.line_range
    return low <= site.stmt_lineno and site.stmt_end_lineno <= high


def _in_length_range(site: DocstringSite, config: Config) -> bool:
    if config.length_range is None:
        return True
    low, high = config.length_range
    length = site.stmt_end_lineno - site.stmt_lineno + 1
    return low <= length <= high


def _blank_run_after(index: LineIndex, lineno: int) -> tuple[int, int]:
    """
    Get the (start_lineno, count) of the blank-line run following a line.
    """
    start = lineno + 1
    count = 0
    while start + count <= index.line_count and not index.line(start + count).strip():
        count += 1
    return start, count


def _blank_run_before(index: LineIndex, lineno: int) -> tuple[int, int]:
    """
    Get the (start_lineno, count) of the blank-line run preceding a line.
    """
    count = 0
    while lineno - count - 1 >= 1 and not index.line(lineno - count - 1).strip():
        count += 1
    return lineno - count, count


def _gap_edit(
    index: LineIndex, start_lineno: int, existing: int, desired: BlankLines
) -> Edit | None:
    """
    Build an edit normalizing a blank-line run to `desired` lines.
    """
    if desired == PRESERVE or not isinstance(desired, int):
        return None
    if existing == desired:
        return None

    start = index.line_start(start_lineno)
    end = index.line_start(start_lineno + existing)
    return Edit(start=start, end=end, replacement="\n" * desired)


def _blank_line_edits(
    site: DocstringSite, index: LineIndex, config: Config
) -> list[Edit]:
    """
    Build blank-line edits for a site.

    All rules default to preserving existing blank lines, so this returns nothing
    unless a rule is explicitly configured.
    """
    edits: list[Edit] = []

    if site.next_lineno is not None:
        rule: BlankLines = getattr(config, _AFTER_RULES[site.kind])
        start, count = _blank_run_after(index, site.stmt_end_lineno)
        if start + count == site.next_lineno:
            edit = _gap_edit(index, start, count, rule)
            if edit is not None:
                edits.append(edit)

    if site.is_own and site.kind is DocstringKind.CLASS:
        start, count = _blank_run_before(index, site.stmt_lineno)
        edit = _gap_edit(index, start, count, config.blank_line_before_class_docstring)
        if edit is not None:
            edits.append(edit)

    return edits


def format_source(source: str, config: Config) -> str:
    """
    Format docstrings in a source string.

    Raises `ParseError` if the source is not valid Python.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ParseError(str(exc)) from exc

    index = LineIndex(source)
    sites = discover(tree, source, index)

    edits: list[Edit] = []

    for site in sites:
        if not _in_line_range(site, config) or not _in_length_range(site, config):
            continue

        replacement = format_literal(site.literal, site.indent, site.kind, config)
        if replacement != source[site.start : site.end]:
            edits.append(Edit(start=site.start, end=site.end, replacement=replacement))

        edits.extend(_blank_line_edits(site, index, config))

    if not edits:
        return source

    return apply_edits(source, edits)


def format_source_checked(source: str, config: Config) -> str:
    """
    Format a source string and verify it against the safety gates.

    Raises `InternalError` if the result changes anything beyond docstring
    contents, or if formatting is not idempotent. Callers must leave the file
    untouched in that case.
    """
    result = format_source(source, config)

    if result == source:
        return result

    try:
        if not assert_ast_equivalent(source, result):
            raise InternalError("formatting changed the AST beyond docstrings")
    except SyntaxError as exc:
        raise InternalError(f"formatting produced invalid Python: {exc}") from exc

    if format_source(result, config) != result:
        raise InternalError("formatting is not idempotent")

    return result
