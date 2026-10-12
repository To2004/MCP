"""The observe-only gateway: transparent to the agent, records every message, scores offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp_security.gateway.proxy import GatewayConfig, Upstream, create_app
from mcp_security.gateway.score import pair_calls, read_log, score_calls

AGENT_TOKEN = "agent-token"
UPSTREAM_KEY = "upstream-secret"
UPSTREAM_URL = "http://upstream/mcp"
SESSION_ID = "sess-1"
INITIALIZE = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
CALL = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "get_file_contents", "arguments": {"repo": "repo-a", "path": "README"}},
}


def _fake_upstream(seen_headers: list[dict[str, str]]) -> Starlette:
    """A minimal Streamable-HTTP MCP endpoint: JSON for initialize, SSE for tools/call."""

    async def mcp(request: Request) -> Response:
        seen_headers.append({k.lower(): v for k, v in request.headers.items()})
        message = json.loads(await request.body())
        if message["method"] == "initialize":
            reply = {"jsonrpc": "2.0", "id": message["id"], "result": {"serverInfo": {}}}
            return JSONResponse(reply, headers={"mcp-session-id": SESSION_ID})
        reply = {"jsonrpc": "2.0", "id": message["id"], "result": {"content": [{"text": "ok"}]}}
        frame = f"event: message\ndata: {json.dumps(reply)}\n\n"
        return Response(frame, media_type="text/event-stream", headers={"x-upstream": "1"})

    return Starlette(routes=[Route("/mcp", mcp, methods=["POST", "GET", "DELETE"])])


@pytest.fixture
def seen_headers() -> list[dict[str, str]]:
    return []


@pytest.fixture
def upstream_client(seen_headers: list[dict[str, str]]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=_fake_upstream(seen_headers)))


@pytest.fixture
def gateway(
    tmp_path: Path, upstream_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> httpx.AsyncClient:
    monkeypatch.setenv("TEST_UPSTREAM_KEY", UPSTREAM_KEY)
    config = GatewayConfig(
        upstreams={
            "github": Upstream(name="github", url=UPSTREAM_URL, key_env="TEST_UPSTREAM_KEY")
        },
        agents={hashlib.sha256(AGENT_TOKEN.encode()).hexdigest(): "alice"},
        log_dir=tmp_path,
    )
    app = create_app(config, client=upstream_client)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw")


def _as_agent(session: str | None = None) -> dict[str, str]:
    headers = {"authorization": f"Bearer {AGENT_TOKEN}", "content-type": "application/json"}
    if session:
        headers["mcp-session-id"] = session
    return headers


def _comparable(headers: httpx.Headers) -> dict[str, str]:
    """Headers minus the framing ones a stream legitimately recomputes."""
    framing = {"content-length", "transfer-encoding"}
    return {k.lower(): v for k, v in headers.items() if k.lower() not in framing}


async def test_reply_is_identical_to_calling_the_upstream_directly(
    gateway: httpx.AsyncClient, upstream_client: httpx.AsyncClient
) -> None:
    direct = await upstream_client.post(UPSTREAM_URL, json=CALL)
    via = await gateway.post("/github", json=CALL, headers=_as_agent())

    assert via.status_code == direct.status_code
    assert via.content == direct.content
    assert _comparable(via.headers) == _comparable(direct.headers)


async def test_upstream_gets_the_gateway_key_never_the_agent_token(
    gateway: httpx.AsyncClient, seen_headers: list[dict[str, str]]
) -> None:
    await gateway.post("/github", json=CALL, headers=_as_agent())

    assert seen_headers[-1]["authorization"] == f"Bearer {UPSTREAM_KEY}"
    assert not any(AGENT_TOKEN in value for value in seen_headers[-1].values())


async def test_log_has_both_directions_with_session_and_no_secrets(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=INITIALIZE, headers=_as_agent())
    await gateway.post("/github", json=CALL, headers=_as_agent(session=SESSION_ID))

    log_path = tmp_path / "github.jsonl"
    records = read_log(log_path)
    directions = [(r["direction"], r["message"].get("id")) for r in records]
    assert directions == [
        ("agent->server", 1),
        ("server->agent", 1),
        ("agent->server", 2),
        ("server->agent", 2),
    ]
    assert {r["agent"] for r in records} == {"alice"}
    assert records[1]["session"] == SESSION_ID  # assigned by the server on initialize
    assert records[2]["session"] == SESSION_ID
    raw = log_path.read_text(encoding="utf-8")
    assert UPSTREAM_KEY not in raw
    assert AGENT_TOKEN not in raw


async def test_unknown_agent_is_refused_and_nothing_reaches_the_upstream(
    gateway: httpx.AsyncClient, seen_headers: list[dict[str, str]]
) -> None:
    reply = await gateway.post("/github", json=CALL, headers={"authorization": "Bearer nope"})

    assert reply.status_code == 401
    assert seen_headers == []


async def test_unknown_route_is_not_found(gateway: httpx.AsyncClient) -> None:
    reply = await gateway.post("/nowhere", json=CALL, headers=_as_agent())

    assert reply.status_code == 404


def _record(direction: str, message: dict, session: str = SESSION_ID) -> dict:
    return {
        "ts": 0.0,
        "route": "github",
        "agent": "alice",
        "session": session,
        "direction": direction,
        "http": "POST",
        "status": None,
        "message": message,
    }


def test_calls_are_paired_with_their_results_and_unanswered_ones_kept() -> None:
    reply = {"jsonrpc": "2.0", "id": 2, "result": {"content": [], "isError": True}}
    unanswered = {**CALL, "id": 3}
    records = [
        _record("agent->server", CALL),
        _record("server->agent", reply),
        _record("agent->server", unanswered),
    ]

    calls = pair_calls(records)

    assert [(c["tool"], c["outcome"]) for c in calls] == [
        ("get_file_contents", "tool_error"),
        ("get_file_contents", "no_response"),
    ]
    assert calls[0]["args"] == {"repo": "repo-a", "path": "README"}


def test_scanned_route_gets_cell_times_runtime_factor() -> None:
    scan = {
        "cells": {"repo-a": {"get_file_contents": 20.0}},
        "bands": {"repo-a": {"get_file_contents": "medium"}},
        "score_max": 125,
    }
    calls = pair_calls([_record("agent->server", CALL)])

    [row] = score_calls(calls, scan=scan, specs={}, route="github", kind="github")

    assert row["cell"] == 20.0
    assert row["asset"] == "repo-a"
    assert row["factor"] == 1.0  # first call: no argument history, no tool history
    assert row["risk"] == 20.0


def test_unscanned_route_is_recorded_without_a_score() -> None:
    calls = pair_calls([_record("agent->server", CALL)])

    [row] = score_calls(calls, scan=None, specs={}, route="deepwiki", kind=None)

    assert row["risk"] is None
    assert row["tool"] == "get_file_contents"
