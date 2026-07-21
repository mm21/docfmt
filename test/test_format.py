from dataclasses import replace

from docfmt import Config, format_source


def test_known_good_profile_is_stable_on_corpus_style(config):
    source = '''"""
Module summary.
"""

from dataclasses import dataclass


@dataclass(kw_only=True)
class Thing:
    """
    Class summary.
    """

    package: str
    """
    Import name of the package.
    """

    python: int = 3
    """
    Supported version.
    """

    @property
    def path(self) -> str:
        """
        Path to the package directory.
        """
        return ""
'''
    assert format_source(source, config) == source


def test_make_summary_multi_line(config):
    source = '''def f():
    """Summary."""
'''
    expected = '''def f():
    """
    Summary.
    """
'''
    assert format_source(source, config) == expected


def test_single_quoted_docstring_normalized_to_triple(config):
    source = """def f():
    "Summary."
"""
    expected = '''def f():
    """
    Summary.
    """
'''
    assert format_source(source, config) == expected


def test_one_line_kept_without_multi_line_flags():
    config = Config(black=True).resolve()
    source = '''def f():
    """Summary."""
'''
    assert format_source(source, config) == source


def test_long_summary_is_wrapped(config):
    source = f'''def f():
    """
    {"word " * 30}
    """
'''
    result = format_source(source, config)
    body = [line for line in result.splitlines() if line.strip() not in ('"""',)]
    assert all(len(line) <= 88 for line in body)


def test_short_paragraph_line_breaks_are_preserved(config):
    # docfmt does not refill prose that already fits; this keeps it a drop-in
    source = '''def f():
    """
    Summary.

    A short line.
    Another short line.
    """
'''
    assert format_source(source, config) == source


def test_force_wrap_refills_prose(config):
    config = replace(config, force_wrap=True)
    source = '''def f():
    """
    Summary.

    A short line.
    Another short line.
    """
'''
    result = format_source(source, config)
    assert "A short line. Another short line." in result


def test_no_text_mutation_by_default(config):
    # no trailing period added, no capitalization
    source = '''def f():
    """
    lowercase summary with no period
    """
'''
    assert format_source(source, config) == source


def test_add_summary_period_opt_in(config):
    config = replace(config, add_summary_period=True)
    source = '''def f():
    """
    summary
    """
'''
    assert "summary." in format_source(source, config)


def test_capitalize_summary_opt_in(config):
    config = replace(config, capitalize_summary=True)
    source = '''def f():
    """
    summary
    """
'''
    assert "Summary" in format_source(source, config)


def test_non_cap_respected(config):
    config = replace(config, capitalize_summary=True, non_cap=("docfmt",))
    source = '''def f():
    """
    docfmt does things
    """
'''
    assert "docfmt does things" in format_source(source, config)


def test_doctest_is_verbatim(config):
    source = '''def f():
    """
    Summary.

    >>> f()
    1
    """
'''
    assert format_source(source, config) == source


def test_field_list_is_verbatim(config):
    source = '''def f():
    """
    Summary.

    :param x: some parameter with a fairly long description that keeps going on
    :returns: something
    """
'''
    assert format_source(source, config) == source


def test_bullet_list_is_verbatim(config):
    source = '''def f():
    """
    Summary.

    - first item
    - second item
    """
'''
    assert format_source(source, config) == source


def test_docstring_without_docstrings_untouched(config):
    source = """import os

x = 1
y = 2
"""
    assert format_source(source, config) == source


def test_raw_docstring_prefix_preserved(config):
    source = '''def f():
    r"""
    Summary with \\n escape.
    """
'''
    assert format_source(source, config).startswith('def f():\n    r"""')


def test_docstring_containing_triple_quote_is_not_requoted(config):
    source = """def f():
    '''
    Contains \"\"\" inside.
    '''
"""
    assert "'''" in format_source(source, config)


def test_empty_lines_between_attribute_pairs_preserved(config):
    source = '''class Thing:
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
    assert format_source(source, config) == source


def test_line_range_limits_formatting(config):
    config = replace(config, line_range=(1, 3))
    source = '''def f():
    """Summary one."""


def g():
    """Summary two."""
'''
    result = format_source(source, config)
    assert '"""Summary two."""' in result
    assert '"""Summary one."""' not in result
