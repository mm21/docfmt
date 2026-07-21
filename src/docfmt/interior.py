"""
Docstring interior reformatting.

Operates purely on the text between the quotes. Structured content is copied
verbatim; only plain prose paragraphs are rewrapped. By default docfmt never
mutates author text — adding a trailing period and capitalizing the first word
are opt-in.

The fence scanner is MyST-aware: directives nest by *widening* the fence, so
fence length is significant and a narrower fence inside a wider one is content,
not a terminator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum, auto

from .config import Config
from .discovery import DocstringKind, StringLiteral
from .wrap import wrap_paragraph

__all__ = [
    "BlockKind",
    "Block",
    "parse_blocks",
    "format_literal",
]

_FENCE_RE = re.compile(r"^(?P<marker>`{3,}|~{3,}|:{3,})(?P<info>.*)$")

_DOCTEST_RE = re.compile(r"^>>>\s")
_DIRECTIVE_RE = re.compile(r"^\.\.\s")
_FIELD_RE = re.compile(r"^:[^:\s][^:]*:")
_BULLET_RE = re.compile(r"^([-*+]|\(?\d+[.)])\s")
_TABLE_RE = re.compile(r"^(\||\+[-=+]{2,})")
_ADORNMENT_RE = re.compile(r"^([!-/:-@\[-`{-~])\1{2,}\s*$")

_SPECIAL_RES = (
    _DOCTEST_RE,
    _DIRECTIVE_RE,
    _FIELD_RE,
    _BULLET_RE,
    _TABLE_RE,
    _ADORNMENT_RE,
)

_INDENTED_CODE = 4


class BlockKind(StrEnum):
    """
    Classification of a run of docstring lines.
    """

    BLANK = auto()
    PROSE = auto()
    VERBATIM = auto()


@dataclass
class Block:
    """
    A run of consecutive docstring lines sharing a classification.
    """

    kind: BlockKind
    lines: list[str]


def _is_blank(line: str) -> bool:
    return not line.strip()


def _is_special(line: str) -> bool:
    """
    Whether a line starts a construct which must not be rewrapped.
    """
    stripped = line.lstrip()
    if line.startswith(" " * _INDENTED_CODE):
        return True
    return any(pattern.match(stripped) for pattern in _SPECIAL_RES)


def _scan_fence(lines: list[str], start: int) -> int | None:
    """
    If `lines[start]` opens a fence, get the index just past its closing fence.

    A block closes only on a fence of the same character with at least as many
    markers and no info string; anything narrower, or carrying an info string, is
    content. An unterminated fence consumes the remainder.
    """
    match = _FENCE_RE.match(lines[start].lstrip())
    if match is None:
        return None

    marker = match.group("marker")
    char = marker[0]
    width = len(marker)

    for index in range(start + 1, len(lines)):
        closer = _FENCE_RE.match(lines[index].lstrip())
        if closer is None:
            continue
        candidate = closer.group("marker")
        if candidate[0] != char or len(candidate) < width:
            continue
        if closer.group("info").strip():
            continue
        return index + 1

    return len(lines)


def parse_blocks(lines: list[str]) -> list[Block]:
    """
    Split docstring content lines into classified blocks.

    A paragraph containing any structured line is verbatim in its entirety,
    which keeps wrapping conservative.
    """
    blocks: list[Block] = []
    index = 0

    while index < len(lines):
        if _is_blank(lines[index]):
            run = index
            while run < len(lines) and _is_blank(lines[run]):
                run += 1
            blocks.append(Block(BlockKind.BLANK, lines[index:run]))
            index = run
            continue

        fence_end = _scan_fence(lines, index)
        if fence_end is not None:
            blocks.append(Block(BlockKind.VERBATIM, lines[index:fence_end]))
            index = fence_end
            continue

        run = index
        while run < len(lines) and not _is_blank(lines[run]):
            if run > index and _scan_fence(lines, run) is not None:
                break
            run += 1

        chunk = lines[index:run]
        kind = (
            BlockKind.VERBATIM
            if any(_is_special(line) for line in chunk)
            else BlockKind.PROSE
        )
        blocks.append(Block(kind, chunk))
        index = run

    return blocks


def _dedent(body: str) -> list[str]:
    """
    Split a literal body into content lines with common indentation removed.

    The first line is handled separately since it sits on the opening-quote line
    and therefore carries no indentation.
    """
    raw = body.split("\n")
    first = raw[0].strip()
    tail = raw[1:]

    indents = [len(line) - len(line.lstrip()) for line in tail if line.strip()]
    common = min(indents) if indents else 0

    dedented = [line[common:] if line.strip() else "" for line in tail]
    lines = ([first] if first else []) + dedented

    while lines and _is_blank(lines[0]):
        lines.pop(0)
    while lines and _is_blank(lines[-1]):
        lines.pop()

    return lines


def _fits(lines: list[str], width: int, indent_len: int) -> bool:
    """
    Whether every line already fits within the wrap width.
    """
    if width <= 0:
        return True
    return all(indent_len + len(line.rstrip()) <= width for line in lines)


def _reflow(lines: list[str], width: int, indent_len: int, force: bool) -> list[str]:
    """
    Rewrap a prose block, but only when it does not already fit.

    Preserving author line breaks in paragraphs that are already within the wrap
    width keeps docfmt a drop-in: it does not refill prose that nothing is wrong
    with. `force_reflow` opts into unconditional reflow.
    """
    if not force and _fits(lines, width, indent_len):
        return [line.rstrip() for line in lines]

    text = " ".join(line.strip() for line in lines).strip()
    return wrap_paragraph(text, width, indent_len)


def _normalize_quote(literal: StringLiteral) -> str:
    """
    Get the quote sequence to emit, preferring triple double quotes.

    Conversion is skipped when the body would become ambiguous.
    """
    body = literal.body
    if '"""' in body or body.endswith('"') or body.startswith('"'):
        return literal.quote
    return '"""'


def _add_period(text: str) -> str:
    """
    Append a period unless the text already ends in terminal punctuation.
    """
    if not text or text[-1] in ".!?:,;":
        return text
    return text + "."


def _summary_lines(lines: list[str], indent: str, config: Config) -> list[str]:
    """
    Build the summary lines, preserving author line breaks when they already fit.
    """
    width = config.line_length

    if config.force_reflow or not _fits(lines, width, len(indent)):
        text = " ".join(line.strip() for line in lines).strip()
        if config.add_summary_period:
            text = _add_period(text)
        return wrap_paragraph(text, width, len(indent))

    out = [line.rstrip() for line in lines]
    if out and config.add_summary_period:
        out[-1] = _add_period(out[-1])
    return out


def format_literal(
    literal: StringLiteral,
    indent: str,
    kind: DocstringKind,
    config: Config,
) -> str:
    """
    Get the replacement text for a docstring literal, including quotes.
    """
    lines = _dedent(literal.body)
    if not lines:
        return literal.prefix + literal.quote + literal.quote

    quote = _normalize_quote(literal)
    blocks = parse_blocks(lines)

    summary_lines: list[str]
    rest: list[Block]

    if blocks and blocks[0].kind is BlockKind.PROSE:
        summary_lines = _summary_lines(blocks[0].lines, indent, config)
        rest = blocks[1:]
    else:
        summary_lines = []
        rest = blocks

    body_lines: list[str] = []
    for block in rest:
        if block.kind is BlockKind.BLANK:
            body_lines.extend("" for _ in block.lines)
        elif block.kind is BlockKind.VERBATIM:
            body_lines.extend(line.rstrip() for line in block.lines)
        else:
            body_lines.extend(
                _reflow(
                    block.lines,
                    config.line_length,
                    len(indent),
                    config.force_reflow,
                )
            )

    while body_lines and not body_lines[-1]:
        body_lines.pop()

    single_line = (
        not body_lines and len(summary_lines) == 1 and not config.summary_on_own_line
    )

    if single_line:
        return f"{literal.prefix}{quote}{summary_lines[0]}{quote}"

    out: list[str] = []

    if config.summary_on_own_line or not summary_lines:
        out.append(f"{literal.prefix}{quote}")
        out.extend(indent + line for line in summary_lines)
    else:
        out.append(f"{literal.prefix}{quote}{summary_lines[0]}")
        out.extend(indent + line for line in summary_lines[1:])

    out.extend(indent + line if line else "" for line in body_lines)

    if config.blank_after_description and body_lines:
        out.append("")

    out.append(indent + quote)
    return "\n".join(out)
