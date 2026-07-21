"""
Golden tests for the blank-line rule table.

Every rule defaults to `preserve`, so the default profile must leave all gaps
exactly as written.
"""

from dataclasses import replace

import pytest

from docfmt import format_source

ATTRS = '''class Thing:
    """
    Class.
    """

    a: int
    """
    A.
    """

    b: int
    """
    B.
    """
'''


def test_defaults_preserve_all_gaps(config):
    assert format_source(ATTRS, config) == ATTRS


@pytest.mark.parametrize("blanks", [0, 1, 2, 3])
def test_attribute_gap_preserved_at_any_width(config, blanks):
    source = (
        "class Thing:\n"
        "    a: int\n"
        '    """\n    A.\n    """\n' + "\n" * blanks + "    b: int\n"
        '    """\n    B.\n    """\n'
    )
    assert format_source(source, config) == source


def test_blank_line_after_attribute_docstring_normalizes(config):
    config = replace(config, blank_line_after_attribute_docstring=1)
    source = (
        "class Thing:\n"
        "    a: int\n"
        '    """\n    A.\n    """\n'
        "\n\n\n"
        "    b: int\n"
        '    """\n    B.\n    """\n'
    )
    result = format_source(source, config)
    assert '    """\n\n    b: int' in result


def test_blank_line_after_attribute_docstring_can_insert(config):
    config = replace(config, blank_line_after_attribute_docstring=1)
    source = (
        "class Thing:\n"
        "    a: int\n"
        '    """\n    A.\n    """\n'
        "    b: int\n"
        '    """\n    B.\n    """\n'
    )
    result = format_source(source, config)
    assert '    """\n\n    b: int' in result


def test_blank_line_after_class_docstring_normalizes(config):
    config = replace(config, blank_line_after_class_docstring=1)
    source = 'class Thing:\n    """\n    C.\n    """\n    a: int\n'
    result = format_source(source, config)
    assert '    """\n\n    a: int' in result


def test_blank_line_after_module_docstring_normalizes(config):
    config = replace(config, blank_line_after_module_docstring=2)
    source = '"""\nM.\n"""\nimport os\n'
    result = format_source(source, config)
    assert '"""\n\n\nimport os' in result


def test_blank_line_after_function_docstring_normalizes(config):
    config = replace(config, blank_line_after_function_docstring=0)
    source = 'def f():\n    """\n    F.\n    """\n\n    return 1\n'
    result = format_source(source, config)
    assert '    """\n    return 1' in result


def test_blank_line_before_class_docstring_normalizes(config):
    config = replace(config, blank_line_before_class_docstring=0)
    source = 'class Thing:\n\n    """\n    C.\n    """\n\n    a: int\n'
    result = format_source(source, config)
    assert 'class Thing:\n    """' in result


def test_rules_do_not_affect_other_gaps(config):
    # a rule for one position must not touch a gap it does not govern
    config = replace(config, blank_line_after_module_docstring=2)
    source = '"""\nM.\n"""\n\n\n' + ATTRS
    result = format_source(source, config)
    assert result.endswith(ATTRS)


def test_last_statement_gap_has_no_rule_to_apply(config):
    config = replace(config, blank_line_after_attribute_docstring=1)
    source = 'class Thing:\n    a: int\n    """\n    A.\n    """\n'
    assert format_source(source, config) == source
