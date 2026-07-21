import pytest

from docfmt import Edit, LineIndex, apply_edits


def test_apply_edits_single():
    assert apply_edits("abcdef", [Edit(start=2, end=4, replacement="XY")]) == "abXYef"


def test_apply_edits_multiple_are_order_independent():
    edits = [
        Edit(start=4, end=5, replacement="E"),
        Edit(start=0, end=1, replacement="A"),
    ]
    assert apply_edits("abcdef", edits) == "AbcdEf"
    assert apply_edits("abcdef", list(reversed(edits))) == "AbcdEf"


def test_apply_edits_empty_is_identity():
    assert apply_edits("abc", []) == "abc"


def test_apply_edits_rejects_overlap():
    edits = [
        Edit(start=0, end=3, replacement="x"),
        Edit(start=2, end=5, replacement="y"),
    ]
    with pytest.raises(ValueError, match="Overlapping"):
        apply_edits("abcdef", edits)


def test_edit_rejects_inverted_range():
    with pytest.raises(ValueError, match="Invalid edit range"):
        Edit(start=5, end=2, replacement="")


def test_line_index_offsets():
    source = "abc\ndef\nghi\n"
    index = LineIndex(source)

    assert index.offset(1, 0) == 0
    assert index.offset(2, 0) == 4
    assert index.offset(2, 2) == 6
    assert index.line(2) == "def\n"
    assert index.line_count == 3


def test_line_index_handles_non_ascii_columns():
    # ast reports col_offset as a utf-8 byte offset, so a multi-byte character
    # must not shift the computed character offset
    source = 'x = "é"\ny = 1\n'
    index = LineIndex(source)

    assert index.offset(2, 0) == len('x = "é"\n')
