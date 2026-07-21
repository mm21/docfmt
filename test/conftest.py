import pytest

from docfmt import Config

KNOWN_GOOD = dict(
    black=True,
    make_summary_multi_line=True,
    non_strict=True,
    pre_summary_newline=True,
)


@pytest.fixture
def config() -> Config:
    """
    The known-good profile used across mm21 projects.
    """
    return Config(**KNOWN_GOOD).resolve()


@pytest.fixture
def pep257() -> Config:
    """
    Default (non-black) configuration.
    """
    return Config().resolve()
