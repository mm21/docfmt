"""
Offset-based edit splicing and source geometry.

The central invariant of docfmt: the output is the input with a set of
non-overlapping character-range replacements applied. Everything not covered by
an edit is preserved byte-for-byte. There is no tokenize/untokenize round trip
and no whole-file regeneration, so no edit can perturb an unrelated region.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

__all__ = [
    "Edit",
    "apply_edits",
    "LineIndex",
]


@dataclass(frozen=True)
class Edit:
    """
    Replacement of `source[start:end]` with `replacement`.

    Offsets are character indices into the original source.
    """

    start: int
    end: int
    replacement: str

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"Invalid edit range: {self.start} > {self.end}")


def apply_edits(source: str, edits: Sequence[Edit]) -> str:
    """
    Apply edits to the source, returning the new text.

    Edits must not overlap; they are applied from the end backwards so that
    earlier offsets remain valid throughout.
    """
    ordered = sorted(edits, key=lambda edit: (edit.start, edit.end))

    previous_end = -1
    for edit in ordered:
        if edit.start < previous_end:
            raise ValueError(f"Overlapping edit: {edit}")
        previous_end = edit.end

    result = source
    for edit in reversed(ordered):
        result = result[: edit.start] + edit.replacement + result[edit.end :]
    return result


class LineIndex:
    """
    Maps `ast` positions to character offsets in the source.

    `ast` reports `col_offset` as a UTF-8 byte offset into the line, so columns
    are converted through the encoded line rather than used directly.
    """

    def __init__(self, source: str):
        self._source = source
        self._lines = source.splitlines(keepends=True)

        starts: list[int] = []
        offset = 0
        for line in self._lines:
            starts.append(offset)
            offset += len(line)
        starts.append(offset)
        self._starts = starts

    def offset(self, lineno: int, col_offset: int) -> int:
        """
        Get the character offset of a 1-indexed line and byte column.
        """
        if lineno > len(self._lines):
            return self._starts[-1]
        line = self._lines[lineno - 1]
        prefix = line.encode("utf-8")[:col_offset].decode("utf-8", errors="replace")
        return self._starts[lineno - 1] + len(prefix)

    def line_start(self, lineno: int) -> int:
        """
        Get the character offset of the start of a 1-indexed line.
        """
        if lineno > len(self._lines):
            return self._starts[-1]
        return self._starts[lineno - 1]

    def line_end(self, lineno: int) -> int:
        """
        Get the character offset just past the end of a 1-indexed line, including
        its newline.
        """
        if lineno >= len(self._lines):
            return self._starts[-1]
        return self._starts[lineno]

    def line(self, lineno: int) -> str:
        """
        Get the text of a 1-indexed line, including its newline.
        """
        if lineno > len(self._lines):
            return ""
        return self._lines[lineno - 1]

    @property
    def line_count(self) -> int:
        """
        Number of lines in the source.
        """
        return len(self._lines)
