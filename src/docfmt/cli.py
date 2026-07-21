"""
Command-line interface.

Exit codes:

- `0`: nothing to do, or changes were written in in-place mode
- `1`: check mode found files which would change
- `2`: an error occurred; no file was modified
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import replace
from pathlib import Path

from .config import Config, config_from_table, find_config_file, load_table
from .errors import DocfmtError, InternalError, ParseError
from .formatter import format_source_checked

__all__ = [
    "main",
]

_EXIT_OK = 0
_EXIT_WOULD_CHANGE = 1
_EXIT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    """
    Run the docfmt command line.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_config(args)
    except (DocfmtError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return _EXIT_ERROR

    if config.line_length < 0:
        parser.error(f"invalid line-length: {config.line_length}")

    paths = _collect(args.files, args.recursive, config.exclude)

    changed = False
    errored = False

    for path in paths:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Error: {path}: {exc}", file=sys.stderr)
            errored = True
            continue

        try:
            result = format_source_checked(source, config)
        except ParseError as exc:
            print(f"Error: {path}: {exc}", file=sys.stderr)
            errored = True
            continue
        except InternalError as exc:
            print(
                f"Internal error: {path}: {exc} (file left unchanged)",
                file=sys.stderr,
            )
            errored = True
            continue

        if result == source:
            continue

        changed = True

        if args.diff or not (args.in_place or args.check):
            diff = difflib.unified_diff(
                source.splitlines(keepends=True),
                result.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
            sys.stdout.writelines(diff)

        if args.in_place:
            try:
                path.write_text(result, encoding="utf-8")
            except OSError as exc:
                print(f"Error: {path}: {exc}", file=sys.stderr)
                errored = True
        elif args.check:
            print(str(path), file=sys.stderr)

    if errored:
        return _EXIT_ERROR
    if args.check and changed:
        return _EXIT_WOULD_CHANGE
    return _EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docfmt", description="Format docstrings in Python source files."
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="write changes to files instead of printing a diff",
    )
    mode.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="only report files which would change",
    )

    parser.add_argument(
        "-d", "--diff", action="store_true", help="print a unified diff"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="recurse into directories"
    )
    parser.add_argument(
        "-e", "--exclude", nargs="*", help="path fragments to skip when recursing"
    )
    parser.add_argument("--config", help="path to a configuration file")
    parser.add_argument(
        "--line-length",
        type=int,
        metavar="length",
        help="wrap docstrings at this length; 0 disables wrapping",
    )
    parser.add_argument("--summary-on-own-line", action="store_true", default=None)
    parser.add_argument("--blank-after-description", action="store_true", default=None)
    parser.add_argument("--force-reflow", action="store_true", default=None)
    parser.add_argument("--add-summary-period", action="store_true", default=None)
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("files", nargs="+", help="files or directories to format")

    return parser


_OVERRIDABLE = (
    "line_length",
    "summary_on_own_line",
    "blank_after_description",
    "force_reflow",
    "add_summary_period",
)


def _load_config(args: argparse.Namespace) -> Config:
    """
    Build the effective config from the config file plus CLI overrides.
    """
    path = Path(args.config) if args.config else find_config_file(Path.cwd())

    config = Config()

    if path is not None:
        table, black_line_length = load_table(path)
        config = config_from_table(table, black_line_length=black_line_length)

    updates = {
        name: getattr(args, name)
        for name in _OVERRIDABLE
        if getattr(args, name, None) is not None
    }
    if args.exclude:
        updates["exclude"] = tuple(args.exclude)

    if updates:
        config = replace(config, **updates)

    return config


def _collect(paths: list[str], recursive: bool, exclude: tuple[str, ...]) -> list[Path]:
    """
    Expand the given paths into a sorted list of Python files.
    """
    found: list[Path] = []

    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            if not recursive:
                continue
            for child in sorted(path.rglob("*.py")):
                if any(part in exclude for part in child.parts):
                    continue
                found.append(child)
        else:
            found.append(path)

    return found


if __name__ == "__main__":
    sys.exit(main())
