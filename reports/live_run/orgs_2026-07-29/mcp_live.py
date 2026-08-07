"""Minimal stdio JSON-RPC client for driving a real MCP server from a call plan.

Usage:
    python mcp_live.py <plan.json>

Plan format:
    {
      "server": {"command": "npx", "args": [...], "env": {...}},
      "calls": [{"name": "tool_name", "arguments": {...}}, ...],
      "out": "path/to/captured.json"
    }

Writes {"tools": [...], "results": [...]} to `out`. Never prints credentials.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


class StdioMCP:
    """A single MCP server subprocess spoken to over stdio JSON-RPC."""

    def __init__(self, command: str, args: list[str], env: dict[str, str]) -> None:
        merged = {**os.environ, **env}
        self.proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=merged,
            text=True,
            bufsize=1,
        )
        self._next_id = 0
        self._stderr: list[str] = []
        threading.Thread(target=self._drain_stderr, daemon=True).start()

    def _drain_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self._stderr.append(line.rstrip())

    def _send(self, payload: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """One JSON-RPC request; returns the matching response object."""
        self._next_id += 1
        req_id = self._next_id
        self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == req_id:
                return msg
        raise RuntimeError(f"server closed before answering {method}; stderr: {self._stderr[-8:]}")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def close(self) -> None:
        try:
            self.proc.stdin and self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def run_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Initialize the server, list tools, run every planned call, return the capture."""
    spec = plan["server"]
    client = StdioMCP(spec["command"], spec["args"], spec.get("env", {}))
    try:
        client.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-security-live", "version": "1.0"},
            },
        )
        client.notify("notifications/initialized")
        tools = client.request("tools/list").get("result", {}).get("tools", [])
        results = []
        for call in plan.get("calls", []):
            resp = client.request(
                "tools/call", {"name": call["name"], "arguments": call.get("arguments", {})}
            )
            body = resp.get("result", resp.get("error"))
            results.append({"call": call, "response": body})
            label = call.get("label", call["name"])
            is_error = bool(isinstance(body, dict) and body.get("isError")) or "error" in resp
            print(f"  [{'FAIL' if is_error else 'ok'}] {label}", flush=True)
            if is_error:
                print(f"        {json.dumps(body)[:400]}", flush=True)
        return {"tools": tools, "results": results, "stderr": client._stderr[-20:]}
    finally:
        client.close()


def main() -> int:
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    capture = run_plan(plan)
    out = Path(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(capture, indent=2), encoding="utf-8")
    print(f"tools={len(capture['tools'])} calls={len(capture['results'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
