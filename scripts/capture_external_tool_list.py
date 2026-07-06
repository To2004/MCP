"""Launch an external MCP server over stdio and save its ``tools/list``.

Spawns the server, performs the MCP initialize handshake, requests ``tools/list``,
and writes the response into the scanner's canonical tool-list shape at
``reports/tool_lists/<kind>.json`` (same format as ``scripts/save_tool_lists.py``).

Usage::

    python scripts/capture_external_tool_list.py --kind yahoo_finance \
        --cwd external/yahoo-finance-mcp -- uv run server.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "reports" / "tool_lists"

INIT = {
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "scan-harness", "version": "0.1"},
    },
}
INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}
LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}


def _normalise(tool: dict) -> dict:
    """Keep the fields the scanner needs (mirrors scripts/save_tool_lists.py)."""
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


def _drain_stderr(pipe) -> None:
    for _ in iter(pipe.readline, b""):
        pass


def capture(cmd: list[str], cwd: Path, timeout: float) -> list[dict]:
    """Run the server and return its advertised tools array."""
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, bufsize=0,
    )
    threading.Thread(target=_drain_stderr, args=(proc.stderr,), daemon=True).start()

    def send(msg: dict) -> None:
        proc.stdin.write((json.dumps(msg) + "\n").encode())
        proc.stdin.flush()

    send(INIT)
    send(INITIALIZED)
    send(LIST)

    proc.stdout_deadline = None
    import time  # local: only used for a wall-clock deadline
    deadline = time.monotonic() + timeout
    tools: list[dict] = []
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            msg = json.loads(line.decode(errors="replace"))
        except json.JSONDecodeError:
            continue
        if msg.get("id") == 2 and "result" in msg:
            tools = msg["result"].get("tools", [])
            break
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    return tools


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, help="output name reports/tool_lists/<kind>.json")
    parser.add_argument("--cwd", required=True, type=Path, help="server working directory")
    parser.add_argument("--server", help="server display name (default: kind)")
    parser.add_argument("--timeout", type=float, default=180.0, help="seconds to wait for tools/list")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="-- launch command")
    args = parser.parse_args(argv)

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        parser.error("provide a launch command after --")

    cwd = (REPO_ROOT / args.cwd).resolve() if not args.cwd.is_absolute() else args.cwd
    raw = capture(cmd, cwd, args.timeout)
    tools = [_normalise(t) for t in raw if t.get("name")]
    if not tools:
        print(f"{args.kind}: no tools captured", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "server": args.server or args.kind,
        "kind": args.kind,
        "source": f"live tools/list captured from `{' '.join(cmd)}` in {args.cwd}",
        "tools": tools,
    }
    out = OUT_DIR / f"{args.kind}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    n_schema = sum(1 for t in tools if t["input_schema"].get("properties"))
    print(f"{args.kind}: saved {len(tools)} tools ({n_schema} with input schema) -> "
          f"{out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
