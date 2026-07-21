"""
Dataclass-heavy corpus file.

Mirrors the annotation-only attribute style used across mm21 projects, including
decorated members and multi-paragraph class docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Sequence

__all__ = [
    "DEFAULTS",
    "BaseThing",
    "ProjectLike",
]

DEFAULTS: dict[str, str] = {
    "a": "1",
    "b": "2",
}
"""
Module-level assignment followed by a docstring.

Updated alongside releases; projects can override individual entries.
"""


@dataclass(kw_only=True)
class BaseThing:
    """
    Base class with a ClassVar attribute docstring and an abstract-ish method.

    A second paragraph, to exercise multi-paragraph class docstrings.
    """

    table_path: ClassVar[str]
    """
    Dotted path of the tool's table.
    """

    def to_toml(self) -> dict[str, Any]:
        """
        Get this tool's table contents.
        """
        return {}


@dataclass(kw_only=True)
class ProjectLike(BaseThing):
    """
    Top-level configuration.
    """

    package: str
    """
    Import name of the package, e.g. `"trilium_alchemy"`.
    """

    python: tuple[int, int]
    """
    Supported Python versions.
    """

    packages_dir: str = "src"
    """
    Directory containing packages, relative to the project root.
    """

    format_paths: Sequence[str] = ("src", "test", "doc", "examples")
    """
    Directories to format (those which exist), in addition to `*.py` and `*.toml` files
    at the project root.
    """

    overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    """
    Escape hatch: extra entries merged last into managed tables, keyed by table path.

    A key not otherwise managed creates a new managed table.
    """

    @property
    def package_path(self) -> Path:
        """
        Path to the package directory, relative to the project root.
        """
        return Path(self.packages_dir) / self.package

    @classmethod
    def default(cls) -> ProjectLike:
        """
        Get the default instance.
        """
        return cls(package="x", python=(3, 12))

    def __post_init__(self):
        if not self.package:
            raise ValueError("package is required")
