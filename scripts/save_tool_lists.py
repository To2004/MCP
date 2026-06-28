"""Save each MCP server's own ``tools/list`` (with input schemas) to disk.

The scanner understands a server's tools from the server's **own** advertised tool
list — exactly what an MCP client gets from a ``tools/list`` request — not from a
hand-authored catalog. We captured that response per server when the demos ran
(``logs/proxy/sessions/*/captured.jsonl``, the proxy's HTTP capture); this script
extracts it and writes one canonical tool list per server kind to
``reports/tool_lists/<kind>.json``. Equivalent to running each MCP once and saving
its tool list.

Run:  python scripts/save_tool_lists.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSIONS = REPO_ROOT / "logs" / "proxy" / "sessions"
OUT_DIR = REPO_ROOT / "reports" / "tool_lists"

# Which captured session advertises each server kind's tool list. The filesystem
# demos all front the same secure-filesystem-server tool set; sqlite its own.
KIND_SOURCES = {
    "filesystem": ("filesystem_sim", "secure-filesystem-server"),
    "sqlite": ("cbg_sqlite_sim", "cbg-sqlite-server"),
}


def _parse_body(body: str) -> dict | None:
    """Parse a JSON-RPC body that may be plain JSON or SSE (``data:`` framed)."""
    body = (body or "").strip()
    if not body:
        return None
    if body[0] == "{":
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            chunk = line[len("data:"):].strip()
            if chunk.startswith("{"):
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    continue
    return None


def extract_tool_list(captured: Path) -> list[dict]:
    """Return the tools array from the ``tools/list`` response in a capture file."""
    best: list[dict] = []
    for raw in captured.open(errors="replace"):
        # The JSON-RPC bodies are escaped strings inside each record, so match on
        # the (unescaped) method name that appears in req_body.
        if "tools/list" not in raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        req = _parse_body(rec.get("req_body", "")) or {}
        if req.get("method") != "tools/list":
            continue
        resp = _parse_body(rec.get("resp_body", "")) or {}
        tools = resp.get("result", {}).get("tools")
        if isinstance(tools, list) and len(tools) > len(best):
            best = tools
    return best


def _normalise(tool: dict) -> dict:
    """Keep the fields the scanner needs from a raw tools/list entry."""
    ann = tool.get("annotations") or {}
    return {
        "name": tool.get("name"),
        "description": tool.get("description") or tool.get("title") or "",
        "input_schema": tool.get("inputSchema") or {},
        "annotations": {
            "read_only_hint": ann.get("readOnlyHint"),
            "destructive_hint": ann.get("destructiveHint"),
            "idempotent_hint": ann.get("idempotentHint"),
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for kind, (session, server) in KIND_SOURCES.items():
        captured = SESSIONS / session / "captured.jsonl"
        if not captured.exists():
            print(f"{kind}: no capture at {captured} — skipped")
            continue
        tools = [_normalise(t) for t in extract_tool_list(captured) if t.get("name")]
        if not tools:
            print(f"{kind}: no tools/list found in {session} — skipped")
            continue
        payload = {
            "server": server,
            "kind": kind,
            "source": f"captured tools/list from logs/proxy/sessions/{session}",
            "tools": tools,
        }
        out = OUT_DIR / f"{kind}.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        n_schema = sum(1 for t in tools if t["input_schema"].get("properties"))
        print(f"{kind}: saved {len(tools)} tools ({n_schema} with input schema) -> "
              f"{out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
