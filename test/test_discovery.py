import ast

from docfmt import DocstringKind, LineIndex, discover, parse_string_literal


def sites(source: str):
    return discover(ast.parse(source), source, LineIndex(source))


def kinds(source: str) -> list[str]:
    return [site.kind.value for site in sites(source)]


def test_module_class_function_docstrings():
    source = '''"""
Module.
"""


class Thing:
    """
    Class.
    """

    def method(self):
        """
        Method.
        """
'''
    assert kinds(source) == ["module", "class", "function"]


def test_annotation_only_attribute_docstring():
    source = '''class Thing:
    package: str
    """
    Import name.
    """
'''
    assert kinds(source) == ["attribute"]


def test_assigned_attribute_docstring():
    source = '''class Thing:
    packages_dir: str = "src"
    """
    Directory.
    """
'''
    assert kinds(source) == ["attribute"]


def test_module_level_assign_attribute_docstring():
    source = '''DEFAULTS = {}
"""
Mapping.
"""
'''
    assert kinds(source) == ["attribute"]


def test_decorated_members_are_found():
    source = '''import functools


class Thing:
    @property
    def path(self):
        """
        Path.
        """

    @classmethod
    def make(cls):
        """
        Make.
        """

    @staticmethod
    def helper():
        """
        Helper.
        """
'''
    assert kinds(source) == ["function", "function", "function"]


def test_async_function_docstring():
    source = '''async def go():
    """
    Go.
    """
'''
    assert kinds(source) == ["function"]


def test_string_after_non_assignment_is_not_a_docstring():
    source = """class Thing:
    def method(self):
        pass

    "not a docstring"
"""
    assert kinds(source) == []


def test_string_in_function_body_after_assign_is_not_attribute_docstring():
    # attribute docstrings are only recognized at module or class level
    source = """def f():
    x = 1
    "not a docstring"
"""
    assert kinds(source) == []


def test_implicit_concatenation_is_skipped():
    source = """def f():
    "part one" "part two"
"""
    assert kinds(source) == []


def test_bare_expression_string_only_first_counts_as_own_docstring():
    source = '''class Thing:
    """
    Class.
    """

    x: int
    """
    Attr.
    """
'''
    result = sites(source)
    assert [s.kind for s in result] == [
        DocstringKind.CLASS,
        DocstringKind.ATTRIBUTE,
    ]
    assert result[0].is_own is True
    assert result[1].is_own is False


def test_sites_are_in_source_order():
    source = '''"""
M.
"""


class A:
    """
    A.
    """


class B:
    """
    B.
    """
'''
    offsets = [site.start for site in sites(source)]
    assert offsets == sorted(offsets)


def test_parse_string_literal_variants():
    assert parse_string_literal('"""x"""').quote == '"""'
    assert parse_string_literal("'''x'''").quote == "'''"
    assert parse_string_literal('"x"').body == "x"
    assert parse_string_literal('r"""x"""').is_raw is True
    assert parse_string_literal('"a" "b"') is None
    assert parse_string_literal("not a string") is None
    assert parse_string_literal('"""a""" + x') is None


def test_parse_string_literal_handles_escaped_quote():
    literal = parse_string_literal(r'"a\"b"')
    assert literal is not None
    assert literal.body == r"a\"b"
