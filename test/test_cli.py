import pytest

from docfmt.cli import main

PYPROJECT = """
[tool.docfmt]
black = true
make-summary-multi-line = true
non-strict = true
pre-summary-newline = true
"""

UNFORMATTED = '''def f():
    """Summary."""
'''

FORMATTED = '''def f():
    """
    Summary.
    """
'''


@pytest.fixture
def project(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_in_place_writes_and_returns_ok(project):
    path = project / "a.py"
    path.write_text(UNFORMATTED)

    assert main(["--in-place", str(path)]) == 0
    assert path.read_text() == FORMATTED


def test_in_place_on_formatted_file_is_a_noop(project):
    path = project / "a.py"
    path.write_text(FORMATTED)

    assert main(["--in-place", str(path)]) == 0
    assert path.read_text() == FORMATTED


def test_check_returns_one_when_changes_needed(project):
    path = project / "a.py"
    path.write_text(UNFORMATTED)

    assert main(["--check", str(path)]) == 1
    assert path.read_text() == UNFORMATTED, "check mode must not write"


def test_check_returns_zero_when_clean(project):
    path = project / "a.py"
    path.write_text(FORMATTED)

    assert main(["--check", str(path)]) == 0


def test_syntax_error_returns_error_and_leaves_file(project):
    path = project / "bad.py"
    path.write_text("def f(\n")

    assert main(["--in-place", str(path)]) == 2
    assert path.read_text() == "def f(\n"


def test_missing_file_returns_error(project):
    assert main(["--in-place", str(project / "nope.py")]) == 2


def test_recursive_collects_files(project):
    package = project / "pkg"
    package.mkdir()
    (package / "a.py").write_text(UNFORMATTED)
    (package / "b.py").write_text(UNFORMATTED)

    assert main(["--in-place", "--recursive", str(package)]) == 0
    assert (package / "a.py").read_text() == FORMATTED
    assert (package / "b.py").read_text() == FORMATTED


def test_non_recursive_skips_directories(project):
    package = project / "pkg"
    package.mkdir()
    (package / "a.py").write_text(UNFORMATTED)

    assert main(["--in-place", str(package)]) == 0
    assert (package / "a.py").read_text() == UNFORMATTED


def test_exclude_skips_paths(project):
    package = project / "pkg"
    vendor = package / "vendor"
    vendor.mkdir(parents=True)
    (package / "a.py").write_text(UNFORMATTED)
    (vendor / "b.py").write_text(UNFORMATTED)

    # -e takes a variable number of values, so the paths must precede it
    assert main(["--in-place", "-r", str(package), "-e", "vendor"]) == 0
    assert (package / "a.py").read_text() == FORMATTED
    assert (vendor / "b.py").read_text() == UNFORMATTED


def test_diff_is_printed_without_writing(project, capsys):
    path = project / "a.py"
    path.write_text(UNFORMATTED)

    assert main([str(path)]) == 0
    assert path.read_text() == UNFORMATTED

    out = capsys.readouterr().out
    assert "---" in out and "+++" in out


def test_check_lists_file_on_stderr(project, capsys):
    path = project / "a.py"
    path.write_text(UNFORMATTED)

    main(["--check", str(path)])
    assert "a.py" in capsys.readouterr().err


def test_config_is_read_from_pyproject(project):
    # make-summary-multi-line comes from the config file, not the command line
    path = project / "a.py"
    path.write_text(UNFORMATTED)

    main(["--in-place", str(path)])
    assert path.read_text() == FORMATTED


def test_explicit_config_path(project, tmp_path):
    other = tmp_path / "other.toml"
    other.write_text("[tool.docfmt]\nblack = true\n")

    path = project / "a.py"
    path.write_text(UNFORMATTED)

    # the explicit config lacks make-summary-multi-line, so the one-liner stays
    assert main(["--in-place", "--config", str(other), str(path)]) == 0
    assert path.read_text() == UNFORMATTED

    # ...whereas the project config would have expanded it
    assert main(["--in-place", str(path)]) == 0
    assert path.read_text() == FORMATTED
