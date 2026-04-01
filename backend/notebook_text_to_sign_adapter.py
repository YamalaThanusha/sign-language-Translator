from __future__ import annotations

import json
import os
from typing import Any, Callable


_cached_fn: Callable[[str], dict[str, Any]] | None = None
_load_attempted = False


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _notebook_path() -> str:
    return os.path.join(_project_root(), "notebook", "text_to_sign.ipynb")


def _extract_function_cells(cells: list[dict[str, Any]]) -> str:
    code_chunks: list[str] = []
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if "def process_text_to_sign" in source:
            code_chunks.append(source)
    return "\n\n".join(code_chunks).strip()


def _load_notebook_callable() -> Callable[[str], dict[str, Any]] | None:
    global _load_attempted
    global _cached_fn

    if _load_attempted:
        return _cached_fn

    _load_attempted = True
    notebook_file = _notebook_path()

    if not os.path.exists(notebook_file):
        return None

    try:
        with open(notebook_file, "r", encoding="utf-8") as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"Failed to read notebook for text-to-sign integration: {e}")
        return None

    code = _extract_function_cells(notebook.get("cells", []))
    if not code:
        return None

    namespace: dict[str, Any] = {}
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"Failed to execute notebook text-to-sign cells: {e}")
        return None

    fn = namespace.get("process_text_to_sign")
    if callable(fn):
        _cached_fn = fn
        return _cached_fn

    return None


def run_notebook_text_to_sign(text: str) -> dict[str, Any] | None:
    fn = _load_notebook_callable()
    if fn is None:
        return None

    try:
        result = fn(text)
    except Exception as e:
        print(f"Notebook text-to-sign callable failed: {e}")
        return None

    if not isinstance(result, dict):
        return None

    return result
