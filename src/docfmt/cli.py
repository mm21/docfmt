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
    parser.add_argument("--black", action="store_true", help="use black's line length")
    parser.add_argument("--wrap-summaries", type=int, metavar="length")
    parser.add_argument("--wrap-descriptions", type=int, metavar="length")
    parser.add_argument("--pre-summary-newline", action="store_true", default=None)
    parser.add_argument("--pre-summary-space", action="store_true", default=None)
    parser.add_argument("--make-summary-multi-line", action="store_true", default=None)
    parser.add_argument("--close-quotes-on-newline", action="store_true", default=None)
    parser.add_argument(
        "--blank", dest="post_description_blank", action="store_true", default=None
    )
    parser.add_argument("--non-strict", action="store_true", default=None)
    parser.add_argument("--force-wrap", action="store_true", default=None)
    parser.add_argument("--add-summary-period", action="store_true", default=None)
    parser.add_argument("--capitalize-summary", action="store_true", default=None)
    parser.add_argument("--tab-width", type=int, metavar="width")
    parser.add_argument("--non-cap", nargs="*")
    parser.add_argument("--range", dest="line_range", nargs=2, type=int, metavar="line")
    parser.add_argument(
        "--docstring-length", dest="length_range", nargs=2, type=int, metavar="length"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("files", nargs="+", help="files or directories to format")

    return parser


_OVERRIDABLE = (
    "black",
    "wrap_summaries",
    "wrap_descriptions",
    "pre_summary_newline",
    "pre_summary_space",
    "make_summary_multi_line",
    "close_quotes_on_newline",
    "post_description_blank",
    "non_strict",
    "force_wrap",
    "add_summary_period",
    "capitalize_summary",
    "tab_width",
)


def _load_config(args: argparse.Namespace) -> Config:
    """
    Build the effective config from the config file plus CLI overrides.
    """
    path = Path(args.config) if args.config else find_config_file(Path.cwd())

    black_line_length: int | None = None
    config = Config()

    if path is not None:
        table, black_line_length = load_table(path)
        config = config_from_table(table)

    updates = {
        name: getattr(args, name) for name in _OVERRIDABLE if getattr(args, name, None)
    }
    if args.non_cap:
        updates["non_cap"] = tuple(args.non_cap)
    if args.exclude:
        updates["exclude"] = tuple(args.exclude)
    if args.line_range:
        updates["line_range"] = tuple(args.line_range)
    if args.length_range:
        updates["length_range"] = tuple(args.length_range)

    if updates:
        config = replace(config, **updates)

    return config.resolve(black_line_length=black_line_length)


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

    for name in ("line_range", "length_range"):
        value = getattr(config, name)
        if value is not None and (value[0] < 1 or value[0] > value[1]):
            parser.error(f"invalid {name}: {value}")

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


if __name__ == "__main__":
    sys.exit(main())
