"""
MyST corpus file.

Exercises directives, nested fences, inline role attributes, and plain code
fences in module, class, method, and attribute docstrings.

```python
from myst_ import Content

content = Content()
```
"""

from __future__ import annotations

__all__ = [
    "Content",
]


class Content:
    """
    Content accessor.

    Type of content depends on whether the note is text or binary:

    - `True`{l=python}: get/set `str`{l=python}
    - `False`{l=python}: get/set `bytes`{l=python}

    Get or set content as follows:

    ```
    note.content = "<p>Hello, world!</p>"
    assert note.content == "<p>Hello, world!</p>"
    ```

    ````{todo}
    Helper `Note.file` to set content from file, automatically
    setting `mime` and `#originalFilename`.

    Example:

    ```
    note.file = "assets/my_content.html"
    ```
    ````
    """

    blob_id: str
    """
    Blob id.

    ```{note}
    An attribute docstring containing a directive.
    ```
    """

    def refresh(self) -> None:
        """
        Refresh the content.

        ```{warning}
        This discards local changes.
        ```
        """

    def nested(self) -> None:
        """
        Summary.

        ````{note}
        ```{warning}
        Test warning
        ```
        ````
        """

    def colon_fence(self) -> None:
        """
        Summary.

        :::{note}
        A colon-delimited directive.
        :::
        """
