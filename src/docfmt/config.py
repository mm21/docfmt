"""
Configuration model and discovery.

Defaults are conservative: docfmt normalizes docstring *layout* but never mutates author
text, and preserves every blank line around docstrings unless a blank-line rule is
explicitly configured.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Literal

from .errors import DocfmtError

__all__ = [
    "DEFAULT_LINE_LENGTH",
    "PRESERVE",
    "BlankLines",
    "BlankLineRules",
    "Config",
    "find_config_file",
    "load_table",
    "config_from_table",
]

PRESERVE: Literal["preserve"] = "preserve"
"""
Blank-line rule value meaning "leave existing blank lines alone".
"""

DEFAULT_LINE_LENGTH = 88
"""
Line length used when neither docfmt nor black configures one.
"""

type BlankLines = Literal["preserve"] | int

_CONFIG_FILES = ("pyproject.toml", "setup.cfg", "tox.ini")


@dataclass(kw_only=True)
class BlankLineRules:
    """
    Blank lines to enforce around docstrings.

    Each rule is either a count or `PRESERVE`, which leaves whatever the author wrote
    alone.
    """

    before_class: BlankLines = PRESERVE
    after_module: BlankLines = PRESERVE
    after_class: BlankLines = PRESERVE
    after_function: BlankLines = PRESERVE
    after_attribute: BlankLines = PRESERVE


@dataclass(kw_only=True)
class Config:
    """
    Docfmt configuration.

    Field names map to TOML keys by replacing underscores with hyphens.
    """

    line_length: int = DEFAULT_LINE_LENGTH
    """
    Wrap docstrings at this length; 0 disables wrapping.

    When left unset in the config file, black's configured line length is used if there
    is one.
    """

    summary_on_own_line: bool = False
    """
    Put the summary on the line after the opening quotes.
    """

    blank_after_description: bool = False
    """
    Add a blank line after the description, before the closing quotes.
    """

    force_reflow: bool = False
    """
    Reflow descriptions even when they already fit within the wrap width.
    """

    add_summary_period: bool = False
    """
    Append a period to summaries which lack terminal punctuation; opt-in because it
    mutates author text.
    """

    blank_lines: BlankLineRules = field(default_factory=BlankLineRules)
    """
    Blank-line rules to enforce around docstrings.
    """

    exclude: tuple[str, ...] = ()
    """
    Path name fragments to skip when recursing.
    """

    in_place: bool = False
    """
    Write changes to files instead of printing a diff.
    """

    check: bool = False
    """
    Only report files which would change; mutually exclusive with `in_place`.
    """

    diff: bool = False
    """
    Print a unified diff even in in-place or check mode.
    """

    recursive: bool = False
    """
    Recurse into directories given as arguments.
    """


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


def config_from_table(
    table: dict[str, Any], *, black_line_length: int | None = None
) -> Config:
    """
    Build a config from a `[tool.docfmt]` table.

    An unknown key is an error rather than a silent no-op: a typo, or a key docfmt does
    not implement, would otherwise look like it had taken effect.

    An unset `line-length` falls back to black's when one is configured.
    """
    known = {_toml_key(f.name): f for f in fields(Config)}
    _reject_unknown(table, known, "tool.docfmt")

    values: dict[str, Any] = {}

    for key, value in table.items():
        info = known[key]
        if info.name == "blank_lines":
            value = _blank_line_rules(value)
        elif info.type == "tuple[str, ...]":
            value = tuple(value)
        values[info.name] = value

    if "line_length" not in values and black_line_length is not None:
        values["line_length"] = black_line_length

    return Config(**values)


def _toml_key(name: str) -> str:
    return name.replace("_", "-")


def _blank_line_rules(table: dict[str, Any]) -> BlankLineRules:
    """
    Build blank-line rules from a `[tool.docfmt.blank-lines]` table.
    """
    known = {_toml_key(f.name): f.name for f in fields(BlankLineRules)}
    _reject_unknown(table, known, "tool.docfmt.blank-lines")
    return BlankLineRules(**{known[key]: value for key, value in table.items()})


def _reject_unknown(
    table: dict[str, Any], known: dict[str, Any], table_name: str
) -> None:
    """
    Raise if `table` carries any key outside `known`.
    """
    unknown = sorted(set(table) - set(known))
    if not unknown:
        return

    keys = ", ".join(repr(key) for key in unknown)
    plural = "keys" if len(unknown) > 1 else "key"
    raise DocfmtError(
        f"Unknown {plural} in [{table_name}]: {keys} "
        f"(known: {', '.join(sorted(known))})"
    )
