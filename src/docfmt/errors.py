"""
Exception types raised by docfmt.
"""

from __future__ import annotations

__all__ = [
    "DocfmtError",
    "ParseError",
    "InternalError",
]


class DocfmtError(Exception):
    """
    Base class for all docfmt errors.
    """


class ParseError(DocfmtError):
    """
    Raised when a source file cannot be parsed as Python.

    The file is left untouched.
    """


class InternalError(DocfmtError):
    """
    Raised when a safety gate fails: the formatted result either changed the AST
    beyond docstring constants, or was not idempotent.

    This always indicates a bug in docfmt. The file is left untouched.
    """
