"""Load a server's tools from its own saved ``tools/list`` response.

The scanner understands a server's tools from the **server's own advertised tool
list** — the exact `tools/list` an MCP client receives — not from a hand-authored
catalog. Those lists are captured per server (run the MCP once) and saved to
``reports/tool_lists/<kind>.json`` by ``scripts/save_tool_lists.py``. This loader
turns one into :class:`ToolSpec` objects, carrying each tool's name, description,
self-declared annotations, and full input schema (so the parameter-scoring stage
sees the real parameters).
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_security.static_scoring.registry import ToolSpec

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_LIST_DIR = REPO_ROOT / "reports" / "tool_lists"


def tool_list_path(kind: str) -> Path:
    """Path to the saved tools/list for a server ``kind``."""
    return TOOL_LIST_DIR / f"{kind}.json"


def _spec_from_entry(entry: dict) -> ToolSpec:
    ann = entry.get("annotations") or {}
    return ToolSpec(
        name=entry["name"],
        description=entry.get("description", ""),
        read_only_hint=ann.get("read_only_hint"),
        destructive_hint=ann.get("destructive_hint"),
        idempotent_hint=ann.get("idempotent_hint"),
        input_schema=entry.get("input_schema") or {},
    )


def load_tool_list(kind: str, *, path: Path | None = None) -> list[ToolSpec]:
    """Load the saved tool list for ``kind`` (or an explicit ``path``).

    Raises a clear error if no saved list exists — the scanner does not invent a
    tool set; run ``scripts/save_tool_lists.py`` (which captures each MCP's
    ``tools/list``) first.
    """
    book = path or tool_list_path(kind)
    if not book.exists():
        raise FileNotFoundError(
            f"no saved tool list for kind {kind!r}: {book}. "
            "Run `python scripts/save_tool_lists.py` to capture each MCP's tools/list."
        )
    data = json.loads(book.read_text(encoding="utf-8"))
    tools = [_spec_from_entry(t) for t in data.get("tools", []) if t.get("name")]
    if not tools:
        raise ValueError(f"no tools in {book}")
    return tools
