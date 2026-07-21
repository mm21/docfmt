"""
Property tests over the corpus: formatting must be idempotent, must never change
the AST beyond docstring contents, and must be independent of file position.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from docfmt import Config, assert_ast_equivalent, format_source

CORPUS = sorted((Path(__file__).parent / "corpus").glob("*.py"))
SOURCES = sorted(Path(__file__).parent.parent.joinpath("src").rglob("*.py"))
TESTS = sorted(Path(__file__).parent.glob("test_*.py"))

ALL_FILES = CORPUS + SOURCES + TESTS

PROFILES = {
    "known-good": dict(
        black=True,
        make_summary_multi_line=True,
        non_strict=True,
        pre_summary_newline=True,
    ),
    "pep257": {},
    "aggressive": dict(
        black=True,
        force_reflow=True,
        add_summary_period=True,
        capitalize_summary=True,
        post_description_blank=True,
    ),
    "normalizing": dict(
        black=True,
        pre_summary_newline=True,
        make_summary_multi_line=True,
        blank_line_after_attribute_docstring=1,
        blank_line_after_class_docstring=1,
        blank_line_after_module_docstring=1,
    ),
}


def ids(paths):
    return [path.name for path in paths]


@pytest.fixture(params=sorted(PROFILES), ids=sorted(PROFILES))
def profile(request) -> Config:
    return Config(**PROFILES[request.param]).resolve()


@pytest.mark.parametrize("path", ALL_FILES, ids=ids(ALL_FILES))
def test_idempotent(path: Path, profile: Config):
    source = path.read_text(encoding="utf-8")
    once = format_source(source, profile)
    twice = format_source(once, profile)
    assert twice == once, f"formatting {path.name} is not idempotent"


@pytest.mark.parametrize("path", ALL_FILES, ids=ids(ALL_FILES))
def test_ast_equivalent(path: Path, profile: Config):
    source = path.read_text(encoding="utf-8")
    result = format_source(source, profile)
    assert assert_ast_equivalent(
        source, result
    ), f"formatting {path.name} changed the AST beyond docstrings"


@pytest.mark.parametrize("path", CORPUS, ids=ids(CORPUS))
def test_corpus_is_already_formatted(path: Path, config: Config):
    # the committed corpus is written in the known-good style, so the known-good
    # profile must be a no-op on it
    source = path.read_text(encoding="utf-8")
    assert format_source(source, config) == source


@pytest.mark.parametrize("path", CORPUS, ids=ids(CORPUS))
def test_position_independence_over_corpus(path: Path, config: Config):
    source = path.read_text(encoding="utf-8")
    formatted = format_source(source, config)

    prefix = "\n\n".join(
        f'class Lead{index}:\n    """\n    Lead {index}.\n    """\n\n'
        f"    value: int = {index}\n" + '    """\n    Value.\n    """\n'
        for index in range(4)
    )
    shifted = format_source(prefix + "\n\n" + source, config)

    assert shifted.endswith(
        formatted
    ), f"formatting {path.name} depended on preceding code"


def test_wrap_width_extremes_are_idempotent():
    source = (Path(__file__).parent / "corpus" / "dataclasses_.py").read_text()
    for width in (0, 20, 40, 88, 200):
        config = Config(wrap_summaries=width, wrap_descriptions=width)
        once = format_source(source, config)
        assert format_source(once, config) == once, f"width={width}"


def test_force_reflow_is_idempotent():
    source = (Path(__file__).parent / "corpus" / "myst_.py").read_text()
    config = replace(Config(black=True).resolve(), force_reflow=True)
    once = format_source(source, config)
    assert format_source(once, config) == once
