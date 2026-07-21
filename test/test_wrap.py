from docfmt import tokenize_atoms, wrap_paragraph


def test_plain_words():
    assert tokenize_atoms("one two three") == ["one", "two", "three"]


def test_inline_code_with_role_attribute_is_one_atom():
    # MyST role attributes must never be split from their code span
    assert tokenize_atoms("`False`{l=python} value") == [
        "`False`{l=python}",
        "value",
    ]


def test_code_span_containing_spaces_is_one_atom():
    assert tokenize_atoms("see `a b c` end") == ["see", "`a b c`", "end"]


def test_rest_role_is_one_atom():
    assert tokenize_atoms("call :py:func:`x` now") == ["call", ":py:func:`x`", "now"]


def test_markdown_link_is_one_atom():
    assert tokenize_atoms("see [the docs](http://x/y) now") == [
        "see",
        "[the docs](http://x/y)",
        "now",
    ]


def test_autolink_is_one_atom():
    assert tokenize_atoms("see <http://x/y> now") == ["see", "<http://x/y>", "now"]


def test_punctuation_attaches_to_atom():
    assert tokenize_atoms("`False`{l=python}: get") == ["`False`{l=python}:", "get"]


def test_wrap_respects_width():
    lines = wrap_paragraph("aaa bbb ccc ddd", width=7, indent_len=0)
    assert lines == ["aaa bbb", "ccc ddd"]


def test_wrap_accounts_for_indent():
    lines = wrap_paragraph("aaa bbb ccc", width=8, indent_len=4)
    assert lines == ["aaa", "bbb", "ccc"]


def test_wrap_never_splits_a_long_atom():
    text = "x `a very long code span here` y"
    lines = wrap_paragraph(text, width=10, indent_len=0)
    assert "`a very long code span here`" in lines


def test_wrap_never_splits_role_attribute_at_narrow_width():
    lines = wrap_paragraph("get `False`{l=python} now", width=12, indent_len=0)
    assert "`False`{l=python}" in lines


def test_zero_width_disables_wrapping():
    assert wrap_paragraph("a b c", width=0, indent_len=0) == ["a b c"]


def test_empty_text():
    assert wrap_paragraph("", width=10, indent_len=0) == []
