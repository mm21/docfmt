"""
Configuration model and discovery.

Options stay close to docformatter's so an existing profile ports over directly.
Defaults are conservative: docfmt normalizes docstring *layout* but never mutates
author text, and preserves every blank line around docstrings unless a
blank-line rule is explicitly configured.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Literal

from .errors import DocfmtError

__all__ = [
    "PRESERVE",
    "BlankLines",
    "Config",
    "find_config_file",
    "load_table",
    "config_from_table",
]

PRESERVE = "preserve"
"""
Blank-line rule value meaning "leave existing blank lines alone".
"""

type BlankLines = Literal["preserve"] | int

_BLACK_WRAP = 88
_PEP257_SUMMARY_WRAP = 79
_PEP257_DESCRIPTION_WRAP = 72

_CONFIG_FILES = ("pyproject.toml", "setup.cfg", "tox.ini")


@dataclass(kw_only=True)
class Config:
    """
    Resolved docfmt configuration.

    Field names map to TOML keys via `field(metadata={"toml": ...})` where they
    differ, following the same convention as pyprojkit's tool configs.
    """

    black: bool = False
    """
    Defer line length to black's.

    Matches docformatter's observed `--black` behavior, which changes wrap
    lengths only; `pre_summary_space` remains opt-in.
    """

    wrap_summaries: int = _PEP257_SUMMARY_WRAP
    """
    Wrap summaries at this length; 0 disables wrapping.
    """

    wrap_descriptions: int = _PEP257_DESCRIPTION_WRAP
    """
    Wrap descriptions at this length; 0 disables wrapping.
    """

    line_length_from_black: bool = True
    """
    In black mode, take wrap lengths from `[tool.black] line-length` when set.
    """

    pre_summary_newline: bool = False
    """
    Put the summary on the line after the opening quotes.
    """

    pre_summary_space: bool = False
    """
    Add a space after the opening quotes when the summary follows them.
    """

    make_summary_multi_line: bool = False
    """
    Put a one-line summary on its own line between the quotes.
    """

    post_description_blank: bool = False
    """
    Add a blank line after the description.
    """

    close_quotes_on_newline: bool = False
    """
    Place closing quotes on their own line when a docstring wraps.
    """

    non_strict: bool = False
    """
    Don't strictly follow reST syntax when identifying lists.
    """

    force_reflow: bool = False
    """
    Reflow descriptions even when they already fit within the wrap width.
    """

    tab_width: int = 1
    """
    Width of a tab when measuring indentation.
    """

    non_cap: tuple[str, ...] = ()
    """
    Words never capitalized when they lead a summary.
    """

    add_summary_period: bool = False
    """
    Append a period to summaries which lack terminal punctuation; opt-in because
    it mutates author text.
    """

    capitalize_summary: bool = False
    """
    Capitalize the first word of summaries; opt-in because it mutates author text.
    """

    blank_line_before_class_docstring: BlankLines = PRESERVE
    blank_line_after_module_docstring: BlankLines = PRESERVE
    blank_line_after_class_docstring: BlankLines = PRESERVE
    blank_line_after_function_docstring: BlankLines = PRESERVE
    blank_line_after_attribute_docstring: BlankLines = PRESERVE

    line_range: tuple[int, int] | None = None
    """
    Only format docstrings within this 1-indexed line range.
    """

    length_range: tuple[int, int] | None = None
    """
    Only format docstrings whose line count falls in this range.
    """

    exclude: tuple[str, ...] = ()
    """
    Path name fragments to skip when recursing.
    """

    def resolve(self, *, black_line_length: int | None = None) -> Config:
        """
        Apply black-mode defaults, returning a new config.

        Wrap lengths explicitly set by the user are left alone.
        """
        if not self.black:
            return self

        width = _BLACK_WRAP
        if self.line_length_from_black and black_line_length is not None:
            width = black_line_length

        updates: dict[str, Any] = {}
        if self.wrap_summaries == _PEP257_SUMMARY_WRAP:
            updates["wrap_summaries"] = width
        if self.wrap_descriptions == _PEP257_DESCRIPTION_WRAP:
            updates["wrap_descriptions"] = width

        if not updates:
            return self

        from dataclasses import replace

        return replace(self, **updates)


def _toml_key(name: str) -> str:
    return name.replace("_", "-")


def find_config_file(start: Path) -> Path | None:
    """
    Find the nearest configuration file, walking upwards from `start`.
    """
    for directory in [start, *start.parents]:
        for name in _CONFIG_FILES:
            candidate = directory / name
            if candidate.is_file():
                if name != "pyproject.toml":
                    return candidate
                with candidate.open("rb") as handle:
                    data = tomllib.load(handle)
                if "docfmt" in data.get("tool", {}):
                    return candidate
    return None


def load_table(path: Path) -> tuple[dict[str, Any], int | None]:
    """
    Read the `[tool.docfmt]` table and black's line length from a config file.
    """
    if path.suffix != ".toml":
        raise DocfmtError(f"Unsupported config file: {path}")

    with path.open("rb") as handle:
        data = tomllib.load(handle)

    tools = data.get("tool", {})
    table = tools.get("docfmt", {})
    black_line_length = tools.get("black", {}).get("line-length")

    return table, black_line_length


def config_from_table(table: dict[str, Any]) -> Config:
    """
    Build a config from a `[tool.docfmt]` table, ignoring unknown keys.
    """
    known = {_toml_key(f.name): f for f in fields(Config)}
    values: dict[str, Any] = {}

    for key, value in table.items():
        info = known.get(key)
        if info is None:
            continue
        if info.type in ("tuple[str, ...]",):
            value = tuple(value)
        elif info.name in ("line_range", "length_range") and value is not None:
            value = tuple(value)
        values[info.name] = value

    return Config(**values)
