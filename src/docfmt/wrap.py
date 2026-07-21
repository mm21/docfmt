"""
Prose wrapping over unbreakable atoms.

Docstrings in these projects use MyST inline constructs such as
``\\`False\\`{l=python}`` — an inline code span immediately followed by a role
attribute. A naive whitespace wrapper may break between the closing backtick and the
`{...}`, silently corrupting rendering. Wrapping therefore happens over *atoms*: runs of
text that are never split, even if a single atom exceeds the wrap width.
"""

from __future__ import annotations

import re

__all__ = [
    "tokenize_atoms",
    "wrap_paragraph",
]

_ATOM_RE = re.compile(
    r"""
      (?P<role> : [\w.+-]+ : `[^`]*` (?: \{[^{}]*\} )? )
    | (?P<code> (?P<ticks>`+) .*? (?P=ticks) (?: \{[^{}]*\} )? )
    | (?P<link> \[ [^\]]* \] \( [^()\s]* \) )
    | (?P<auto> < [^<>\s]+ > )
    | (?P<word> \S+? (?= ` | \s | $ ) )
    | (?P<other> \S )
    """,
    re.VERBOSE,
)


def tokenize_atoms(text: str) -> list[str]:
    """
    Split text into unbreakable atoms.

    Adjacent tokens with no whitespace between them are merged, so a construct
    like ``\\`False\\`{l=python}`` — or a code span containing spaces — survives as a
    single atom.
    """
    atoms: list[str] = []
    previous_end: int | None = None

    for match in _ATOM_RE.finditer(text):
        if atoms and match.start() == previous_end:
            atoms[-1] += match.group()
        else:
            atoms.append(match.group())
        previous_end = match.end()

    return atoms


def wrap_paragraph(text: str, width: int, indent_len: int) -> list[str]:
    """
    Greedily wrap a paragraph, returning lines *without* indentation.

    Lines are sized so that `indent_len` plus the line length does not exceed
    `width`. A width of 0 disables wrapping. An atom longer than the available
    width is emitted on its own line rather than being split.
    """
    atoms = tokenize_atoms(text)
    if not atoms:
        return []

    if width <= 0:
        return [" ".join(atoms)]

    available = width - indent_len
    if available <= 0:
        return list(atoms)

    lines: list[str] = []
    current: list[str] = []
    length = 0

    for atom in atoms:
        if not current:
            current = [atom]
            length = len(atom)
            continue
        if length + 1 + len(atom) <= available:
            current.append(atom)
            length += 1 + len(atom)
        else:
            lines.append(" ".join(current))
            current = [atom]
            length = len(atom)

    if current:
        lines.append(" ".join(current))

    return lines
