from docfmt import BlockKind, format_source, parse_blocks


def block_kinds(lines: list[str]) -> list[str]:
    return [block.kind.value for block in parse_blocks(lines)]


def test_simple_directive_is_one_verbatim_block():
    lines = ["```{note}", "Test note", "```"]
    blocks = parse_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].kind is BlockKind.VERBATIM
    assert blocks[0].lines == lines


def test_nested_directive_closes_only_on_wider_fence():
    # the inner 3-backtick fence must not terminate the 4-backtick block
    lines = [
        "````{note}",
        "```{warning}",
        "Test warning",
        "```",
        "````",
    ]
    blocks = parse_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].lines == lines


def test_colon_fence():
    lines = [":::{note}", "Test note", ":::"]
    blocks = parse_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].kind is BlockKind.VERBATIM


def test_tilde_fence():
    lines = ["~~~{note}", "Test note", "~~~"]
    assert block_kinds(lines) == ["verbatim"]


def test_fence_char_must_match_to_close():
    lines = ["```{note}", "~~~", "text", "```"]
    blocks = parse_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].lines == lines


def test_fence_with_info_string_is_never_a_closer():
    # per CommonMark a closing fence carries no info string, so same-width
    # nesting is not possible: the outer block ends at the first bare fence.
    # This is exactly why MyST requires widening the outer fence.
    lines = ["```{note}", "```python", "code", "```", "```"]
    blocks = parse_blocks(lines)
    assert blocks[0].lines == ["```{note}", "```python", "code", "```"]
    assert len(blocks) == 2


def test_unterminated_fence_consumes_remainder():
    lines = ["```{note}", "text", "more text"]
    blocks = parse_blocks(lines)
    assert len(blocks) == 1
    assert blocks[0].kind is BlockKind.VERBATIM
    assert blocks[0].lines == lines


def test_prose_before_and_after_fence():
    lines = ["Summary.", "", "```{note}", "n", "```", "", "After."]
    assert block_kinds(lines) == [
        "prose",
        "blank",
        "verbatim",
        "blank",
        "prose",
    ]


def test_nested_fence_preserved_end_to_end(config):
    source = '''class Content:
    """
    Get or set content as follows:

    ```
    note.content = "<p>Hello</p>"
    ```

    ````{todo}
    Helper `Note.file` to set content from file, automatically
    setting `mime` and `#originalFilename`.

    Example:

    ```
    note.file = "assets/my_content.html"
    ```
    ````
    """
'''
    assert format_source(source, config) == source


def test_indented_directive_indentation_preserved(config):
    source = '''class Thing:
    def method(self):
        """
        Summary.

        ```{note}
        Indented note.
        ```
        """
'''
    assert format_source(source, config) == source


def test_long_line_inside_fence_is_not_wrapped(config):
    long_line = "x = " + "a" * 120
    source = f'''def f():
    """
    Summary.

    ```
    {long_line}
    ```
    """
'''
    assert format_source(source, config) == source
