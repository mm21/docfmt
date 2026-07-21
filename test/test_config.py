from docfmt import Config, config_from_table, find_config_file, load_table

PYPROJECT = """
[tool.black]
line-length = 100

[tool.docfmt]
black = true
in-place = true
make-summary-multi-line = true
non-strict = true
pre-summary-newline = true
recursive = true
"""


def test_known_good_profile_parses(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT)

    table, black_line_length = load_table(path)
    config = config_from_table(table)

    assert config.black is True
    assert config.make_summary_multi_line is True
    assert config.non_strict is True
    assert config.pre_summary_newline is True
    assert black_line_length == 100


def test_unknown_keys_are_ignored():
    config = config_from_table({"black": True, "style": "sphinx", "nope": 1})
    assert config.black is True


def test_black_mode_defaults():
    config = Config(black=True).resolve()
    assert config.wrap_summaries == 88
    assert config.wrap_descriptions == 88
    # black mode changes wrap lengths only, matching docformatter's behavior
    assert config.pre_summary_space is False


def test_black_line_length_is_used():
    config = Config(black=True).resolve(black_line_length=100)
    assert config.wrap_summaries == 100
    assert config.wrap_descriptions == 100


def test_black_line_length_can_be_disabled():
    config = Config(black=True, line_length_from_black=False).resolve(
        black_line_length=100
    )
    assert config.wrap_summaries == 88


def test_explicit_wrap_lengths_win_over_black():
    config = Config(black=True, wrap_summaries=72).resolve(black_line_length=100)
    assert config.wrap_summaries == 72


def test_pep257_defaults():
    config = Config().resolve()
    assert config.wrap_summaries == 79
    assert config.wrap_descriptions == 72
    assert config.pre_summary_space is False


def test_blank_line_rules_default_to_preserve():
    config = Config()
    assert config.blank_line_after_attribute_docstring == "preserve"
    assert config.blank_line_after_class_docstring == "preserve"
    assert config.blank_line_before_class_docstring == "preserve"


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
