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

    def hint(*keys):
        """Annotation lookup tolerant of snake_case and the spec's camelCase."""
        for k in keys:
            if k in ann:
                return ann[k]
        return None

    return ToolSpec(
        name=entry["name"],
        description=entry.get("description", ""),
        read_only_hint=hint("read_only_hint", "readOnlyHint"),
        destructive_hint=hint("destructive_hint", "destructiveHint"),
        idempotent_hint=hint("idempotent_hint", "idempotentHint"),
        open_world_hint=hint("open_world_hint", "openWorldHint"),
        input_schema=entry.get("input_schema") or entry.get("inputSchema") or {},
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
    # Both saved shapes are real: the whole `tools/list` response ({"tools": [...]})
    # and just its `tools` array, which is what a capture that unwrapped the
    # result stores.
    entries = data if isinstance(data, list) else data.get("tools", [])
    tools = [_spec_from_entry(t) for t in entries if isinstance(t, dict) and t.get("name")]
    if not tools:
        raise ValueError(f"no tools in {book}")
    return tools
