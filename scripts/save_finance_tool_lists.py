"""Extract each finance MCP server's ``tools/list`` from its MITM capture.

Companion to ``scripts/save_tool_lists.py``, but sourced from the live finance
sessions recorded by ``logs/proxy/scripts/run_mitm_finance.py`` (mitmdump →
``logs/proxy/sessions/<session>/captured.jsonl``). For each captured session we
pull the largest ``tools/list`` response, normalise it to the scanner's tool-list
shape, and write ``reports/scan_finance/tool_lists/<kind>.json``.

This is the "connect + inventory" step: the tool list is exactly what an MCP
client received from the real server over the wire, not a hand-authored catalog.

Run:  uv run python scripts/save_finance_tool_lists.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSIONS = REPO_ROOT / "logs" / "proxy" / "sessions"
OUT_DIR = REPO_ROOT / "reports" / "scan_finance" / "tool_lists"

# kind -> (captured session dir, human server name). Only no-credential servers
# that were actually driven through the MITM proxy appear here.
KIND_SOURCES: dict[str, tuple[str, str]] = {
    "yahoo_finance": ("finance_yahoo", "yfinance"),
    "finance_tools": ("finance_tools", "finance-tools-mcp"),
    "maverick": ("finance_maverick", "maverick-mcp"),
    "sec_edgar": ("finance_sec_edgar", "sec-edgar-mcp"),
    "openbb": ("finance_openbb", "openbb-platform"),
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
    """Return the tools array from the largest ``tools/list`` response captured."""
    best: list[dict] = []
    for raw in captured.open(errors="replace"):
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rc = 0
    for kind, (session, server) in KIND_SOURCES.items():
        captured = SESSIONS / session / "captured.jsonl"
        if not captured.exists():
            print(f"{kind}: no capture at {captured} — run run_mitm_finance.py first")
            rc = 1
            continue
        tools = [_normalise(t) for t in extract_tool_list(captured) if t.get("name")]
        if not tools:
            print(f"{kind}: no tools/list found in {session} — skipped")
            rc = 1
            continue
        payload = {
            "server": server,
            "kind": kind,
            "source": f"live MITM capture logs/proxy/sessions/{session}/captured.jsonl",
            "tools": tools,
        }
        out = OUT_DIR / f"{kind}.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        n_schema = sum(1 for t in tools if t["input_schema"].get("properties"))
        print(f"{kind}: saved {len(tools)} tools ({n_schema} with input schema) -> "
              f"{out.relative_to(REPO_ROOT)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
