"""The observe-only gateway: transparent to the agent, records every message, scores offline."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_security.gateway import proxy
from mcp_security.gateway.proxy import GatewayConfig, Upstream, create_app
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.framework import Artifacts, RouteScorer
from mcp_security.gateway.score import ARGS_NOT_LOGGED, pair_calls, score_calls
from mcp_security.gateway.log_file import read_log, verify_chain

AGENT_TOKEN = "agent-token"
UPSTREAM_KEY = "upstream-secret"
UPSTREAM_URL = "http://upstream/mcp"
SESSION_ID = "sess-1"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"clientInfo": {"name": "demo-agent", "version": "1.0"}},
}
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
        if request.method == "DELETE":  # the client ends its session; no body either way
            return Response(status_code=200)
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
    monkeypatch.delenv("GATEWAY_LOG_KEY", raising=False)  # pseudonyms: plain SHA-256
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
    directions = [(r["gateway.direction"], r["message"].get("id")) for r in records]
    assert directions == [
        ("agent->server", 1),
        ("server->agent", 1),
        ("agent->server", 2),
        ("server->agent", 2),
    ]
    assert {r["gateway.agent"] for r in records} == {"alice"}
    session = Pseudonymizer().of(SESSION_ID)  # logged as a pseudonym, never as sent
    assert records[1]["mcp.session.id"] == session  # assigned by the server on initialize
    assert records[2]["mcp.session.id"] == session
    raw = log_path.read_text(encoding="utf-8")
    assert UPSTREAM_KEY not in raw
    assert AGENT_TOKEN not in raw
    assert SESSION_ID not in raw


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
        "schema": "gateway-log/2",
        "ts": 0.0,
        "gateway.route": "github",
        "gateway.agent": "alice",
        "mcp.session.id": session,
        "gateway.direction": direction,
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


def _scorer(scan: dict, rules: dict | None = None) -> RouteScorer:
    artifacts = Artifacts(scan=scan, specs={}, rules=rules, kind="github", digests={})
    return RouteScorer("github", artifacts)


def test_scanned_route_gets_cell_times_runtime_factor() -> None:
    scan = {
        "cells": {"repo-a": {"get_file_contents": 20.0}},
        "bands": {"repo-a": {"get_file_contents": "medium"}},
        "score_max": 125,
    }
    calls = pair_calls([_record("agent->server", CALL)])

    [row] = score_calls(calls, _scorer(scan))

    assert row["cell"] == 20.0
    assert row["asset"] == "repo-a"
    assert row["factor"] == 1.0  # first call: no argument history, no tool history
    assert row["risk"] == 20.0


def test_unscanned_route_is_recorded_without_a_score() -> None:
    calls = pair_calls([_record("agent->server", CALL)])

    [row] = score_calls(calls, None)

    assert row.get("risk") is None
    assert row["tool"] == "get_file_contents"


def test_row_carries_the_static_levels_and_the_input_level_beside_the_risk() -> None:
    scan = {
        "cells": {"repo-a": {"get_file_contents": 20.0}},
        "bands": {"repo-a": {"get_file_contents": "medium"}},
        "asset_sensitivity": {"repo-a": 4},
        "tool_impact": {"get_file_contents": 1},
        "blast_radius": {"get_file_contents|repo-a": 5},
    }
    path_rule = {
        "path": "path",
        "rule": {
            "kind": "keywords",
            "default": 3,
            "groups": [{"contains": ["readme"], "level": 2}],
        },
    }
    rules = {"get_file_contents": ([path_rule], {"repo-a": 4})}
    calls = pair_calls([_record("agent->server", CALL)])

    [row] = score_calls(calls, _scorer(scan, rules))

    assert (row["sensitivity"], row["impact"], row["blast"]) == (4, 1, 5)
    assert row["input_level"] == 2  # README: below the neutral 3
    assert row["input_set_by"] == "path"
    assert row["risk"] == 20.0  # the input level is reported, not multiplied in
    assert row["score_us"] >= 0


async def test_each_line_says_who_when_where_and_what_from_the_wire_alone(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=INITIALIZE, headers=_as_agent())
    await gateway.post("/github", json=CALL, headers=_as_agent(session=SESSION_ID))

    request, reply = read_log(tmp_path / "github.jsonl")[2:]

    assert request["gateway.client"] == "demo-agent/1.0"  # from initialize, kept per session
    assert request["client.address"]
    assert (request["mcp.method.name"], request["gen_ai.tool.name"]) == (
        "tools/call",
        "get_file_contents",
    )
    assert request["jsonrpc.request.id"] == "2"  # a string, as OpenTelemetry records it
    assert "gateway.tool_listed" not in request  # this session never called tools/list
    assert reply["mcp.method.name"] == "tools/call"  # a reply is labelled by its request
    assert reply["gen_ai.tool.name"] == "get_file_contents"
    assert reply["http.response.status_code"] == 200
    assert reply["gateway.duration_s"] >= 0
    assert reply["gateway.seq"] == request["gateway.seq"] + 1
    assert "error.type" not in reply


def test_v1_lines_are_read_with_v2_names(tmp_path: Path) -> None:
    old = {"ts": 1.0, "route": "github", "agent": "alice", "session": "s", "direction": "x"}
    path = tmp_path / "old.jsonl"
    path.write_text(json.dumps(old) + "\n")

    [record] = read_log(path)

    assert record["gateway.agent"] == "alice"
    assert record["mcp.session.id"] == "s"
    assert record["gateway.direction"] == "x"


# ---- gateway-log/3: refusals, identity, sessions, proxies, run markers, bodies ----

BOB_TOKEN = "bob-token"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _app(tmp_path: Path, upstream_client: httpx.AsyncClient, **fields: Any) -> Starlette:
    route = Upstream(name="github", url=UPSTREAM_URL, **fields.pop("route", {}))
    config = GatewayConfig(upstreams={"github": route}, log_dir=tmp_path, **fields)
    return create_app(config, client=upstream_client)


def _client(app: Starlette) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw")


def _notices(path: Path, notice: str) -> list[dict]:
    return [r for r in read_log(path) if r.get("gateway.notice") == notice]


async def test_refused_requests_are_logged_without_the_token(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=CALL, headers={"authorization": "Bearer stolen-guess"})
    await gateway.post("/github", json=CALL)
    await gateway.post("/nowhere", json=CALL, headers=_as_agent())

    refused = _notices(tmp_path / "github.jsonl", "auth_failed")
    assert [r["gateway.reason"] for r in refused] == ["unknown_token", "no_bearer_token"]
    assert all(r["client.address"] and "gateway.agent" not in r for r in refused)
    assert "stolen-guess" not in (tmp_path / "github.jsonl").read_text()
    [unknown] = _notices(tmp_path / "_gateway.jsonl", "unknown_route")
    assert unknown["gateway.route"] == "nowhere"


async def test_a_session_used_by_another_agent_is_flagged_and_still_forwarded(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    agents = {_hash(AGENT_TOKEN): "alice", _hash(BOB_TOKEN): "bob"}
    gateway = _client(_app(tmp_path, upstream_client, agents=agents))
    await gateway.post("/github", json=INITIALIZE, headers=_as_agent())  # alice opens it
    bob = {"authorization": f"Bearer {BOB_TOKEN}", "mcp-session-id": SESSION_ID}

    reply = await gateway.post("/github", json=CALL, headers=bob)

    assert reply.status_code == 200  # observe-only: logged, never blocked
    [notice] = _notices(tmp_path / "github.jsonl", "session_agent_mismatch")
    assert (notice["gateway.agent"], notice["gateway.session_owner"]) == ("bob", "alice")


async def test_an_agent_entry_with_user_and_app_is_on_every_line(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    agents = {
        _hash(AGENT_TOKEN): {"agent": "ci", "user": "u-0417", "app": "ci-bot"},
        _hash(BOB_TOKEN): {"id": "agt-17", "agent": "bob"},
    }
    gateway = _client(_app(tmp_path, upstream_client, agents=agents))
    await gateway.post("/github", json=CALL, headers=_as_agent())
    await gateway.post("/github", json=CALL, headers={"authorization": f"Bearer {BOB_TOKEN}"})

    lines = read_log(tmp_path / "github.jsonl")
    who = {
        (r["gateway.agent_id"], r["gateway.agent"], r.get("user.id"), r.get("gateway.app"))
        for r in lines
    }
    assert who == {
        (_hash(AGENT_TOKEN)[:12], "ci", "u-0417", "ci-bot"),  # default id: the token hash's start
        ("agt-17", "bob", None, None),  # an id set in the config is kept across token rotations
    }
    assert {r["log.level"] for r in lines} == {"info"}


async def test_security_notices_are_warnings(gateway: httpx.AsyncClient, tmp_path: Path) -> None:
    await gateway.post("/github", json=CALL, headers={"authorization": "Bearer guessed"})

    [refused] = _notices(tmp_path / "github.jsonl", "auth_failed")
    assert refused["log.level"] == "warn"


async def test_the_address_behind_a_trusted_proxy_is_the_client_address(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    trusted = ("127.0.0.1/32", "10.0.0.0/8")  # the test client connects from 127.0.0.1
    gateway = _client(_app(tmp_path, upstream_client, trusted_proxies=trusted))
    await gateway.post("/github", json=CALL, headers={"x-forwarded-for": "203.0.113.9, 10.0.0.1"})

    request = read_log(tmp_path / "github.jsonl")[0]
    assert request["client.address"] == "203.0.113.9"
    assert request["network.peer.address"] == "127.0.0.1"
    assert "client.port" not in request  # the port seen was the proxy's


async def test_start_and_stop_are_marked_in_every_route_log(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    app = _app(tmp_path, upstream_client, route={"log_bodies": "requests"})
    with TestClient(app):
        pass

    started, stopped = (
        _notices(tmp_path / "github.jsonl", notice)[0]
        for notice in ("gateway_started", "gateway_stopped")
    )
    assert started["gateway.config_sha256"] == stopped["gateway.config_sha256"]
    assert started["gateway.log_bodies"] == "requests"
    assert verify_chain(tmp_path / "github.jsonl") == []


async def test_an_unreachable_upstream_is_a_notice_with_the_error_class(tmp_path: Path) -> None:
    def refuse(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    down = httpx.AsyncClient(transport=httpx.MockTransport(refuse))
    reply = await _client(_app(tmp_path, down)).post("/github", json=CALL)

    assert reply.status_code == 502
    [notice] = _notices(tmp_path / "github.jsonl", "upstream_unreachable")
    assert notice["error.type"] == "ConnectError"


async def test_a_log_without_reply_bodies_still_pairs_and_scores(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    gateway = _client(_app(tmp_path, upstream_client, route={"log_bodies": "requests"}))
    await gateway.post("/github", json=CALL)

    [call] = pair_calls(read_log(tmp_path / "github.jsonl"))

    assert (call["outcome"], call["args"]) == ("ok", CALL["params"]["arguments"])
    assert call["latency_s"] is not None


async def test_a_log_without_any_bodies_says_why_it_cannot_be_rescored(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    gateway = _client(_app(tmp_path, upstream_client, route={"log_bodies": "none"}))
    await gateway.post("/github", json=CALL)
    scan = {"cells": {"repo-a": {"get_file_contents": 20.0}}, "bands": {}}

    [row] = score_calls(pair_calls(read_log(tmp_path / "github.jsonl")), _scorer(scan))

    assert row["tool"] == "get_file_contents" and row["args"] is None
    assert row["reasons"] == ARGS_NOT_LOGGED


async def test_a_session_taken_over_after_its_owner_ended_it_is_still_flagged(
    tmp_path: Path, upstream_client: httpx.AsyncClient
) -> None:
    """Found live: GitHub kept accepting a session id after the client's DELETE."""
    agents = {_hash(AGENT_TOKEN): "alice", _hash(BOB_TOKEN): "bob"}
    gateway = _client(_app(tmp_path, upstream_client, agents=agents))
    await gateway.post("/github", json=INITIALIZE, headers=_as_agent())
    await gateway.delete("/github", headers=_as_agent(session=SESSION_ID))
    bob = {"authorization": f"Bearer {BOB_TOKEN}", "mcp-session-id": SESSION_ID}
    await gateway.post("/github", json=CALL, headers=bob)

    [notice] = _notices(tmp_path / "github.jsonl", "session_agent_mismatch")
    assert notice["gateway.session_owner"] == "alice"
    assert notice["gateway.session_ended"] is True


async def test_a_reply_without_a_body_still_records_its_status(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=INITIALIZE, headers=_as_agent())
    await gateway.delete("/github", headers=_as_agent(session=SESSION_ID))

    reply = read_log(tmp_path / "github.jsonl")[-1]
    assert (reply["gateway.direction"], reply["http.request.method"]) == ("server->agent", "DELETE")
    assert reply["http.response.status_code"] == 200 and "message" not in reply


def test_pairing_skips_lines_that_name_no_agent() -> None:
    """Found live: start/stop and refused-login lines have no gateway.agent."""
    started = {"schema": "gateway-log/3", "gateway.direction": "gateway", "gateway.notice": "x"}
    records = [
        started,
        _record("agent->server", CALL),
        {**started, "gateway.notice": "auth_failed"},
    ]

    [call] = pair_calls(records)

    assert call["tool"] == "get_file_contents"


def test_the_server_never_takes_x_forwarded_for_on_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Found in the stranger simulation: uvicorn trusts X-Forwarded-For from 127.0.0.1 by
    default, so any local agent could choose the address the log records."""
    routes = tmp_path / "routes.json"
    routes.write_text(
        json.dumps({"log_dir": str(tmp_path), "upstreams": {"g": {"url": "http://x"}}})
    )
    seen: dict = {}
    monkeypatch.setattr(proxy.uvicorn, "run", lambda app, **options: seen.update(options))
    monkeypatch.setattr(sys, "argv", ["proxy", "--config", str(routes)])

    proxy.main()

    assert seen["proxy_headers"] is False
