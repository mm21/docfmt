import pytest

from docfmt import Config


@pytest.fixture
def config() -> Config:
    """
    The known-good profile used across mm21 projects.
    """
    return Config(summary_on_own_line=True)
