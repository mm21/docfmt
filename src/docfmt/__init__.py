"""
Reliable docstring formatter.

Docstrings are located via `ast` structure and rewritten by surgical text
splices, so everything outside a docstring is preserved byte-for-byte. Results
are verified for AST equivalence and idempotency before being written.
"""

__submodules__ = [
    "errors",
    "splice",
    "config",
    "discovery",
    "wrap",
    "interior",
    "gates",
    "formatter",
    "cli",
]

# isort: off
# <AUTOGEN_INIT>
from .errors import (
    DocfmtError,
    ParseError,
    InternalError,
)
from .splice import (
    Edit,
    apply_edits,
    LineIndex,
)
from .config import (
    PRESERVE,
    BlankLines,
    Config,
    find_config_file,
    load_table,
    config_from_table,
)
from .discovery import (
    DocstringKind,
    StringLiteral,
    DocstringSite,
    parse_string_literal,
    iter_docstring_nodes,
    discover,
)
from .wrap import (
    tokenize_atoms,
    wrap_paragraph,
)
from .interior import (
    BlockKind,
    Block,
    parse_blocks,
    format_literal,
)
from .gates import (
    structural_signature,
    assert_ast_equivalent,
)
from .formatter import (
    format_source,
    format_source_checked,
)
from .cli import (
    main,
)

__all__ = [
    "BlankLines",
    "Block",
    "BlockKind",
    "Config",
    "DocfmtError",
    "DocstringKind",
    "DocstringSite",
    "Edit",
    "InternalError",
    "LineIndex",
    "PRESERVE",
    "ParseError",
    "StringLiteral",
    "apply_edits",
    "assert_ast_equivalent",
    "config_from_table",
    "discover",
    "find_config_file",
    "format_literal",
    "format_source",
    "format_source_checked",
    "iter_docstring_nodes",
    "load_table",
    "main",
    "parse_blocks",
    "parse_string_literal",
    "structural_signature",
    "tokenize_atoms",
    "wrap_paragraph",
]
# </AUTOGEN_INIT>
