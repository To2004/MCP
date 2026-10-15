"""Make the example log: one gateway run on the remote GitHub MCP with every kind of line.

Starts the real gateway (``python -m mcp_security.gateway.proxy``) on a local port with this
folder's ``routes.json``, drives one agent session with the real ``mcp`` client (read-only
calls on a public repository, one tool error, one unknown tool), then three requests that
should be noticed: a second agent reusing the first one's ended session, a guessed token
and an unknown route. Writes ``github.jsonl`` and ``_gateway.jsonl`` here, replacing them,
and ``github_view.txt`` / ``github_grouped.txt``: the same log rendered for reading
(``log_view.py``: one line per event, and grouped by session).

    uv run python reports/experiments/gateway/log_example/make_example.py   # needs `gh` login
"""

from __future__ import annotations

import asyncio
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.exceptions import McpError

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "routes.json"
LOG_FILES = ("github.jsonl", "_gateway.jsonl")
#: The same log rendered for reading (log_view.py): one line per event, and by session.
VIEWS = {"github_view.txt": [], "github_grouped.txt": ["--grouped"]}
PORT = 18781
URL = f"http://127.0.0.1:{PORT}"
#: Throwaway tokens for this example only; routes.json holds their SHA-256.
TOKENS = {"alice": "example-alice-token", "bob": "example-bob-token"}
LOG_KEY = "example-key"  # GATEWAY_LOG_KEY for the run: pseudonyms are keyed HMACs
PROTOCOL = "2025-11-25"
START_TRIES, START_WAIT_S, STOP_WAIT_S, HTTP_TIMEOUT_S = 100, 0.1, 20, 30
REPO = {"owner": "modelcontextprotocol", "repo": "python-sdk"}
PLAN = [
    ("search_repositories", {"query": "repo:modelcontextprotocol/python-sdk"}),
    ("get_file_contents", {**REPO, "path": "README.md"}),
    (
        "list_commits",
        {**REPO, "perPage": 3, "since": "2026-09-01T00:00:00Z", "until": "2026-10-01T00:00:00Z"},
    ),
    ("get_file_contents", {**REPO, "path": "no-such-file.md"}),  # the tool reports an error
    ("no_such_tool", {}),  # JSON-RPC -32602: the caller's mistake
]


def main() -> None:
    """Run the gateway, the session and the three side requests; stop the gateway cleanly."""
    for name in LOG_FILES:
        (HERE / name).unlink(missing_ok=True)
    github_token = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True
    ).stdout.strip()
    env = os.environ | {"GATEWAY_LOG_KEY": LOG_KEY, "GITHUB_TOKEN": github_token}
    command = [sys.executable, "-m", "mcp_security.gateway.proxy", "--config", str(CONFIG)]
    gateway = subprocess.Popen(
        [*command, "--port", str(PORT)], env=env, stdout=subprocess.PIPE, text=True
    )
    try:
        _wait_for_port()
        session_id = asyncio.run(agent_session())
        asyncio.run(side_requests(session_id))
    finally:
        gateway.send_signal(signal.SIGINT)  # uvicorn shuts down: lifespan logs gateway_stopped
        gateway.communicate(timeout=STOP_WAIT_S)
    log = os.path.relpath(HERE / LOG_FILES[0])  # the views name the log as the reader runs them
    view = [sys.executable, "-m", "mcp_security.gateway.log_view", log]
    for name, flags in VIEWS.items():
        subprocess.run([*view, *flags, "--out", str(HERE / name)], check=True)


def _wait_for_port() -> None:
    for _ in range(START_TRIES):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=START_WAIT_S).close()
            return
        except OSError:
            time.sleep(START_WAIT_S)
    raise RuntimeError(f"gateway did not open port {PORT}")


async def agent_session() -> str:
    """Alice: initialize, list tools, run the plan. Returns the session id the server gave."""
    headers = {"Authorization": f"Bearer {TOKENS['alice']}"}
    async with streamablehttp_client(f"{URL}/github", headers=headers) as (read, write, sid):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"alice: {len((await session.list_tools()).tools)} tools")
            for tool, args in PLAN:
                try:
                    result = await session.call_tool(tool, args)
                    print(f"alice: {tool:<20} isError={result.isError}")
                except McpError as exc:
                    print(f"alice: {tool:<20} JSON-RPC error {exc.error.code}")
            return sid()


async def side_requests(session_id: str) -> None:
    """Bob on Alice's ended session, a guessed token, an unknown route."""
    call = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "tools/call",
        "params": {"name": "list_commits", "arguments": {**REPO, "perPage": 1}},
    }
    base = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
        "mcp-protocol-version": PROTOCOL,
    }
    bob = base | {"authorization": f"Bearer {TOKENS['bob']}", "mcp-session-id": session_id}
    async with httpx.AsyncClient(base_url=URL, timeout=HTTP_TIMEOUT_S) as http:
        reply = await http.post("/github", json=call, headers=bob)
        print(f"bob on alice's ended session: {reply.status_code}")
        reply = await http.post("/github", json=call, headers=base | {"authorization": "Bearer x"})
        print(f"guessed token: {reply.status_code}")
        alice = base | {"authorization": f"Bearer {TOKENS['alice']}"}
        print(
            f"unknown route: {(await http.post('/gitlab', json=call, headers=alice)).status_code}"
        )


if __name__ == "__main__":
    main()
