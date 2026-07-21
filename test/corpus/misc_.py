"""
Miscellaneous corpus file: edge cases which must survive untouched.
"""

from __future__ import annotations

import os

# a bare comment, not a docstring
PATH = os.sep
ANOTHER = "value"

UNDOCUMENTED = 1
OTHER = 2


class NoDocstrings:
    a: int
    b: str = "x"

    def method(self):
        pass


class Mixed:
    """
    Has a docstring, but undocumented fields.
    """

    a: int
    b: str = "x"

    # a comment between members, which must not be read as a docstring
    c: float = 1.0

    def documented(self):
        """
        Documented.
        """

    def undocumented(self):
        return 1


class Structured:
    """
    Summary.

    :param x: a parameter
    :returns: a value

    >>> Structured()
    <Structured>

    .. note::
       A reST directive.

    - a bullet
    - another bullet

    1. numbered
    2. numbered
    """


def concatenated():
    "part one" "part two"


def raw_docstring():
    r"""
    Raw docstring with a \n escape sequence.
    """


def single_quoted_body():
    """
    Contains an apostrophe's quote and "double quotes".
    """


async def async_function():
    """
    An async function.
    """


class Exception_(Exception):
    """
    An exception subclass.
    """
