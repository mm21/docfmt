import pytest

from docfmt import assert_ast_equivalent, format_source_checked
from docfmt.errors import InternalError, ParseError


def test_ast_equivalent_ignores_docstring_text():
    before = '''def f():
    """
    One.
    """
    return 1
'''
    after = '''def f():
    """Two."""
    return 1
'''
    assert assert_ast_equivalent(before, after)


def test_ast_equivalent_detects_code_change():
    before = "def f():\n    return 1\n"
    after = "def f():\n    return 2\n"
    assert not assert_ast_equivalent(before, after)


def test_ast_equivalent_detects_non_docstring_string_change():
    before = 'x = "a"\n'
    after = 'x = "b"\n'
    assert not assert_ast_equivalent(before, after)


def test_ast_equivalent_detects_removed_statement():
    before = "x = 1\ny = 2\n"
    after = "x = 1\n"
    assert not assert_ast_equivalent(before, after)


def test_checked_format_passes_on_corpus_style(config):
    source = '''class Thing:
    """
    Class.
    """

    a: int
    """
    A.
    """
'''
    assert format_source_checked(source, config) == source


def test_checked_format_raises_on_syntax_error(config):
    with pytest.raises(ParseError):
        format_source_checked("def f(\n", config)


def test_checked_format_reports_internal_error_on_gate_violation(config, monkeypatch):
    # simulate a formatter bug: a result which drops a statement
    import docfmt.formatter as formatter

    def broken(source, config):
        return "x = 1\n"

    monkeypatch.setattr(formatter, "format_source", broken)

    with pytest.raises(InternalError):
        formatter.format_source_checked("x = 1\ny = 2\n", config)


def test_checked_format_detects_non_idempotent_result(config, monkeypatch):
    import docfmt.formatter as formatter

    calls = {"n": 0}
    original = formatter.format_source

    def flapping(source, config):
        calls["n"] += 1
        result = original(source, config)
        # mutate the docstring differently on every call so the result is never a
        # fixed point, while staying AST-equivalent
        return result.replace("A.", f"A.{calls['n']}")

    monkeypatch.setattr(formatter, "format_source", flapping)

    source = '''def f():
    """
    A.
    """
'''
    with pytest.raises(InternalError, match="idempotent"):
        formatter.format_source_checked(source, config)
