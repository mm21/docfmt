from docfmt import (
    DEFAULT_LINE_LENGTH,
    Config,
    config_from_table,
    find_config_file,
    load_table,
)

PYPROJECT = """
[tool.black]
line-length = 100

[tool.docfmt]
in-place = true
summary-on-own-line = true
recursive = true

[tool.docfmt.blank-lines]
after-module = 1
before-class = 0
"""


def test_known_good_profile_parses(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT)

    table, black_line_length = load_table(path)
    config = config_from_table(table, black_line_length=black_line_length)

    assert config.summary_on_own_line is True
    assert config.blank_lines.after_module == 1
    assert config.blank_lines.before_class == 0
    assert black_line_length == 100


def test_unknown_keys_are_ignored():
    config = config_from_table({"line-length": 72, "style": "sphinx", "nope": 1})
    assert config.line_length == 72


def test_default_line_length():
    assert Config().line_length == DEFAULT_LINE_LENGTH
    assert config_from_table({}).line_length == DEFAULT_LINE_LENGTH


def test_black_line_length_is_used_when_unset():
    config = config_from_table({}, black_line_length=100)
    assert config.line_length == 100


def test_explicit_line_length_wins_over_black():
    config = config_from_table({"line-length": 72}, black_line_length=100)
    assert config.line_length == 72


def test_blank_line_rules_default_to_preserve():
    config = Config()
    assert config.blank_lines.after_attribute == "preserve"
    assert config.blank_lines.after_class == "preserve"
    assert config.blank_lines.before_class == "preserve"


def test_unknown_blank_line_keys_are_ignored():
    config = config_from_table({"blank-lines": {"after-module": 1, "nope": 2}})
    assert config.blank_lines.after_module == 1


def test_find_config_file_requires_docfmt_table(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    assert find_config_file(tmp_path) is None

    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    assert find_config_file(tmp_path) == tmp_path / "pyproject.toml"


def test_find_config_file_walks_upwards(tmp_path):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_config_file(nested) == tmp_path / "pyproject.toml"
