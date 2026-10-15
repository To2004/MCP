"""A fast stand-in MCP server for load tests: answers at once, so only the gateway is measured.

Speaks the 2025-11-25 Streamable HTTP shape the gateway sees from the remote GitHub MCP:
`initialize` assigns a session, `tools/list` returns the real 49-tool remote catalog (so the
gateway's catalog check matches the scan), `tools/call` returns a small JSON result.

    uv run uvicorn fake_upstream:app --app-dir reports/experiments/gateway/scale --port 19100
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

CATALOG = Path(__file__).resolve().parents[1] / "github_remote" / "github_remote.json"
TOOLS = json.loads(CATALOG.read_text(encoding="utf-8"))["tools"]
RESULT_BYTES = int(os.environ.get("FAKE_RESULT_BYTES", "1024"))
TEXT = "x" * RESULT_BYTES
DELAY_S = float(os.environ.get("FAKE_DELAY_MS", "0")) / 1000  # e.g. 400: the remote GitHub MCP


async def mcp(request: Request) -> Response:
    if request.method != "POST":
        return Response(status_code=405)
    message = json.loads(await request.body())
    method, rpc_id = message.get("method"), message.get("id")
    if rpc_id is None:  # a notification
        return Response(status_code=202)
    if method == "initialize":
        reply = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake", "version": "1"},
            },
        }
        return JSONResponse(reply, headers={"mcp-session-id": uuid.uuid4().hex})
    if method == "tools/list":
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}})
    if DELAY_S:
        await asyncio.sleep(DELAY_S)
    result = {"content": [{"type": "text", "text": TEXT}], "isError": False}
    return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})


app = Starlette(routes=[Route("/mcp", mcp, methods=["POST", "GET", "DELETE"])])
