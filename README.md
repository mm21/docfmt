# docfmt

Reliable docstring formatter for Python.

## Why

Docstring formatters that rebuild the file from a token stream are prone to a
particular class of bug: edits computed against one version of the token list get
applied to another, so behavior depends on how much unrelated code precedes the
docstring being formatted. The symptom is formatting that changes when you add or
remove an unrelated class elsewhere in the file.

docfmt is built so that cannot happen:

- **Docstrings are located by AST structure**, never by token heuristics or by
  matching line contents.
- **The file is never regenerated.** Formatting produces a set of non-overlapping
  character-range replacements against the original source; everything outside a
  docstring is preserved byte-for-byte.
- **Results are verified before they are written.** Every formatted file is
  checked for AST equivalence (nothing changed but docstring contents) and for
  idempotency (`format(format(x)) == format(x)`). A failure leaves the file
  untouched and reports an internal error rather than writing a bad result.

## Behavior

docfmt normalizes docstring *layout* and, by default, never mutates author text.
Adding a trailing period and capitalizing the first word are opt-in
(`--add-summary-period`, `--capitalize-summary`).

Blank lines around docstrings are **preserved** by default. Normalization is
opt-in per position, e.g. `blank-line-after-attribute-docstring`.

Structured content is copied verbatim and never rewrapped: fenced code blocks,
MyST directives, doctests, reST directives and field lists, tables, and lists.

### MyST directives

MyST directives nest by widening the fence, so fence *length* is significant:

````
```{note}
Test note
```
````

A block closes only on a fence of the same character with at least as many
markers and no info string, so a narrower inner fence is content:

`````
````{note}
```{warning}
Test warning
```
````
`````

Inline constructs such as `` `False`{l=python} `` are treated as unbreakable
atoms, so wrapping never splits an inline code span from its role attribute.

### Attribute docstrings

A string statement immediately following an assignment at module or class level
is an attribute docstring, including annotation-only attributes:

```python
package: str
"""
Import name of the package.
"""
```

## Usage

```
docfmt --in-place --recursive src test
docfmt --check src        # exit 1 if anything would change
docfmt --diff src
```

Configure via `[tool.docfmt]` in `pyproject.toml`:

```toml
[tool.docfmt]
black = true
in-place = true
make-summary-multi-line = true
non-strict = true
pre-summary-newline = true
recursive = true
```

In `black` mode, wrap lengths come from `[tool.black] line-length` when set,
falling back to 88.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Nothing to do, or changes written in in-place mode |
| 1 | Check mode: files would change |
| 2 | Error; no file was modified |

## License

MIT
