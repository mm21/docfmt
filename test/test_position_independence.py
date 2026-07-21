"""
Regression tests for the exact docformatter failure mode: formatting that
depends on how much unrelated code precedes the docstring being formatted.
"""

import pytest

from docfmt import format_source

TARGET = '''@dataclass(kw_only=True)
class Target:
    """
    Target class.
    """

    first: str
    """
    First attribute.
    """

    second: int = 3
    """
    Second attribute.
    """

    @property
    def path(self) -> str:
        """
        A property after attributes.
        """
        return ""
'''


def filler(count: int) -> str:
    """
    Build unrelated leading classes, each with its own docstrings.
    """
    blocks = []
    for index in range(count):
        blocks.append(
            f'''@dataclass(kw_only=True)
class Filler{index}:
    """
    Filler {index}.
    """

    value: int = {index}
    """
    A value.
    """
'''
        )
    return "\n\n".join(blocks)


def build(count: int) -> str:
    header = '"""\nModule.\n"""\n\nfrom dataclasses import dataclass\n\n\n'
    lead = filler(count)
    if lead:
        lead += "\n\n"
    return header + lead + TARGET


@pytest.mark.parametrize("count", [0, 1, 2, 5, 12])
def test_target_formatting_is_independent_of_preceding_code(config, count):
    result = format_source(build(count), config)
    assert result.endswith(TARGET), (
        "formatting of the target class changed when unrelated code was "
        f"prepended (count={count})"
    )


@pytest.mark.parametrize("count", [0, 1, 2, 5, 12])
def test_blank_lines_between_attribute_pairs_survive(config, count):
    result = format_source(build(count), config)
    assert '"""\n\n    second: int = 3' in result


def test_last_class_is_not_treated_specially(config):
    # docformatter corrupted only the last class in a file
    source = build(3)
    result = format_source(source, config)
    assert result == source


@pytest.mark.parametrize("count", [0, 3])
def test_no_blank_line_injected_inside_class_docstring(config, count):
    result = format_source(build(count), config)
    assert '"""\n    Target class.\n    """' in result
