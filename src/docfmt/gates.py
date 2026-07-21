"""
Safety gates.

Every formatted result is verified before it is written. These checks exist to
make whole classes of formatter bugs unshippable: a result which perturbs
anything other than docstring contents, or which is not a fixed point, is
discarded and the file left untouched.
"""

from __future__ import annotations

import ast

from .discovery import iter_docstring_nodes

__all__ = [
    "structural_signature",
    "assert_ast_equivalent",
]

_SENTINEL = ""


def structural_signature(tree: ast.AST) -> str:
    """
    Get a signature of the tree with docstring contents blanked out.

    Two sources with the same signature differ only in docstring text, so any
    change to code structure — or to a non-docstring string — is detectable.
    """
    for node in iter_docstring_nodes(tree):
        node.value = _SENTINEL

    return ast.dump(tree, include_attributes=False)


def assert_ast_equivalent(before: str, after: str) -> bool:
    """
    Whether two sources are equivalent apart from docstring contents.
    """
    return structural_signature(ast.parse(before)) == structural_signature(
        ast.parse(after)
    )
