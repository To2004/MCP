"""The whole framework through the gateway: scored before forwarding, the same live and offline."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.proxy import GatewayConfig, Upstream, create_app
from mcp_security.gateway.score import pair_calls, score_calls
from mcp_security.gateway.log_file import read_log
from mcp_security.gateway.wire_log import FROM_GATEWAY, catalog_digest

SESSION_ID = "sess-1"
UPSTREAM_URL = "http://upstream/mcp"
SCANNED_TOOLS = [{"name": "get_file_contents"}]
SCAN = {
    "cells": {"repo-a": {"get_file_contents": 20.0}, "repo-b": {"get_file_contents": 60.0}},
    "bands": {"repo-a": {"get_file_contents": "medium"}, "repo-b": {"get_file_contents": "high"}},
    "asset_sensitivity": {"repo-a": 4, "repo-b": 5},
    "tool_impact": {"get_file_contents": 1},
    "blast_radius": {"get_file_contents|repo-a": 5, "get_file_contents|repo-b": 12},
    "score_max": 125,
    "catalog": {"sha256": catalog_digest({"tools": SCANNED_TOOLS})},
}
BREADTH = {
    "tools": {
        "get_file_contents": {
            "inputs": [
                {"name": "repo", "kind": "none", "breadth": 5, "ceiling": None, "default": None},
                {"name": "path", "kind": "none", "breadth": 5, "ceiling": None, "default": "/"},
            ]
        }
    }
}


def _rpc(rpc_id: int, method: str, params: dict | None = None) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params or {}}


def _call(rpc_id: int, repo: str) -> dict:
    args = {"repo": repo, "path": "README.md"}
    return _rpc(rpc_id, "tools/call", {"name": "get_file_contents", "arguments": args})


class Upstream_:
    """A fake MCP server that also records whether each call was scored before it arrived."""

    def __init__(self, log_path: Path, tools: list[dict]) -> None:
        self.log_path = log_path
        self.tools = tools
        self.scored_before_arrival: list[bool] = []

    def app(self) -> Starlette:
        async def mcp(request: Request) -> Response:
            message = json.loads(await request.body())
            if message["method"] == "initialize":
                reply = {"jsonrpc": "2.0", "id": message["id"], "result": {}}
                return JSONResponse(reply, headers={"mcp-session-id": SESSION_ID})
            if message["method"] == "tools/list":
                result = {"tools": self.tools}
                return JSONResponse({"jsonrpc": "2.0", "id": message["id"], "result": result})
            lines = read_log(self.log_path) if self.log_path.exists() else []
            self.scored_before_arrival.append(
                any(
                    "gateway.decision" in r and r.get("jsonrpc.request.id") == str(message["id"])
                    for r in lines
                )
            )
            result = {"content": [{"type": "text", "text": "ok"}]}
            return JSONResponse({"jsonrpc": "2.0", "id": message["id"], "result": result})

        return Starlette(routes=[Route("/mcp", mcp, methods=["POST"])])


def _route_files(tmp_path: Path) -> Upstream:
    scan, breadth = tmp_path / "scan.json", tmp_path / "breadth.json"
    scan.write_text(json.dumps(SCAN))
    breadth.write_text(json.dumps(BREADTH))
    return Upstream(
        name="github", url=UPSTREAM_URL, scan=str(scan), breadth=str(breadth), kind="gh"
    )


def _gateway(
    tmp_path: Path, tools: list[dict]
) -> tuple[httpx.AsyncClient, Upstream_, GatewayConfig]:
    upstream = Upstream_(tmp_path / "logs" / "github.jsonl", tools)
    config = GatewayConfig(upstreams={"github": _route_files(tmp_path)}, log_dir=tmp_path / "logs")
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream.app()))
    app = create_app(config, client=client)
    return (
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw"),
        upstream,
        config,
    )


async def _session(gateway: httpx.AsyncClient, calls: list[dict]) -> None:
    headers = {"content-type": "application/json"}
    await gateway.post("/github", json=_rpc(0, "initialize"), headers=headers)
    headers["mcp-session-id"] = SESSION_ID
    await gateway.post("/github", json=_rpc(1, "tools/list"), headers=headers)
    for call in calls:
        assert (await gateway.post("/github", json=call, headers=headers)).status_code == 200


def _decisions(config: GatewayConfig) -> list[dict]:
    return [r for r in read_log(config.log_dir / "github.jsonl") if "gateway.decision" in r]


async def test_a_call_is_scored_before_it_is_forwarded(tmp_path: Path) -> None:
    gateway, upstream, config = _gateway(tmp_path, SCANNED_TOOLS)
    await _session(gateway, [_call(2, "repo-a")])

    assert upstream.scored_before_arrival == [True]
    [record] = _decisions(config)
    decision = record["gateway.decision"]
    assert record["gateway.direction"] == FROM_GATEWAY
    assert (decision["cell"], decision["band"], decision["risk"]) == (20.0, "medium", 20.0)
    assert (decision["sensitivity"], decision["impact"], decision["blast"]) == (4, 1, 5)
    assert set(decision["artifacts"]) == {"scan", "breadth"}
    assert record["gateway.catalog_match"] is True  # the session saw the scanned tool list


async def test_live_decisions_equal_an_offline_rescore_of_the_same_log(tmp_path: Path) -> None:
    gateway, _, config = _gateway(tmp_path, SCANNED_TOOLS)
    calls = [_call(i, "repo-a" if i % 3 else "repo-b") for i in range(2, 40)]
    await _session(gateway, calls)

    live = [r["gateway.decision"] for r in _decisions(config)]
    route = config.upstreams["github"]
    fresh = RouteScorer("github", load_artifacts("github", route.scan, route.breadth, None, "gh"))
    offline = score_calls(pair_calls(read_log(config.log_dir / "github.jsonl")), fresh)

    keys = ("asset", "cell", "factor", "risk", "input_level")
    assert [tuple(d.get(k) for k in keys) for d in live] == [
        tuple(r.get(k) for k in keys) for r in offline
    ]


async def test_a_tool_list_the_scan_never_saw_is_saved_once(tmp_path: Path) -> None:
    changed = [*SCANNED_TOOLS, {"name": "delete_everything"}]
    gateway, _, config = _gateway(tmp_path, changed)
    await _session(gateway, [_call(2, "repo-a")])
    headers = {"content-type": "application/json", "mcp-session-id": SESSION_ID}
    await gateway.post("/github", json=_rpc(9, "tools/list"), headers=headers)  # listed again

    lines = read_log(config.log_dir / "github.jsonl")
    notices = [r for r in lines if r.get("gateway.notice") == "catalog_not_scanned"]
    assert len(notices) == 1
    saved = json.loads(Path(notices[0]["gateway.catalog_file"]).read_text())
    assert [t["name"] for t in saved["tools"]] == ["get_file_contents", "delete_everything"]
    assert _decisions(config)[0]["gateway.catalog_match"] is False


async def test_a_scoring_failure_is_logged_and_the_call_still_goes_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: object, **_kwargs: object) -> dict:
        raise ValueError("scan is corrupt")

    monkeypatch.setattr(RouteScorer, "score", broken)
    gateway, upstream, config = _gateway(tmp_path, SCANNED_TOOLS)
    await _session(gateway, [_call(2, "repo-a")])  # asserts the reply was 200

    assert upstream.scored_before_arrival == [True]
    assert _decisions(config)[0]["gateway.decision"]["error"] == "ValueError: scan is corrupt"


def _remote_scorer(history: str) -> RouteScorer:
    scan, breadth, rules = (
        "reports/experiments/gateway/github_remote/github_remote.cells.json",
        "reports/experiments/breadth_spec/github_remote_scan.json",
        "reports/experiments/gateway/github_remote/rules/github_remote.json",
    )
    artifacts = load_artifacts("github", scan, breadth, rules, "github_remote")
    return RouteScorer("github", artifacts, history=history)


def _traffic(n: int) -> list[tuple[str, dict, str]]:
    repos = ["MCP", "workreddit", "helios-ot-runbooks", "RubicCube"]
    return [
        (
            "list_commits",
            {"owner": "To2004", "repo": repos[i % 4], "perPage": 10 + i % 90},
            f"a{i % 3}",
        )
        for i in range(n)
    ]


def test_per_caller_history_keeps_callers_apart() -> None:
    shared, per_caller = _remote_scorer("route"), _remote_scorer("caller")
    for i, (tool, args, caller) in enumerate(_traffic(300)):
        shared.score(tool, args, float(i), caller=caller)
        per_caller.score(tool, args, float(i), caller=caller)
    assert set(per_caller.snapshot_all()) == {"a0", "a1", "a2"}
    assert set(shared.snapshot_all()) == {"gateway"}


def test_a_restored_scorer_continues_exactly_where_the_saved_one_stopped() -> None:
    first, traffic = _remote_scorer("caller"), _traffic(400)
    for i, (tool, args, caller) in enumerate(traffic[:300]):
        first.score(tool, args, float(i), caller=caller)
    restored = _remote_scorer("caller")
    restored.restore_all(json.loads(json.dumps(first.snapshot_all())))  # through JSON, as on disk
    for i, (tool, args, caller) in enumerate(traffic[300:], start=300):
        assert (
            restored.score(tool, args, float(i), caller=caller)["factor"]
            == first.score(tool, args, float(i), caller=caller)["factor"]
        )


async def test_a_restarted_gateway_continues_the_dynamic_history(tmp_path: Path) -> None:
    calls = [_call(i, "repo-a" if i % 3 else "repo-b") for i in range(2, 42)]

    def gateway(where: Path, state: Path | None) -> tuple[httpx.AsyncClient, Starlette]:
        where.mkdir(parents=True, exist_ok=True)
        upstream = Upstream_(where / "logs" / "github.jsonl", SCANNED_TOOLS)
        route = replace(_route_files(where), state_file=str(state) if state else None)
        config = GatewayConfig(upstreams={"github": route}, log_dir=where / "logs")
        app = create_app(
            config, client=httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream.app()))
        )
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw"), app

    def factors(where: Path) -> list[float]:
        lines = read_log(where / "logs" / "github.jsonl")
        return [r["gateway.decision"]["factor"] for r in lines if "gateway.decision" in r]

    straight, _ = gateway(tmp_path / "straight", None)
    await _session(straight, calls)

    state = tmp_path / "state.json"
    first, first_app = gateway(tmp_path / "first", state)
    await _session(first, calls[:20])
    first_app.state.gateway.save_state()  # what shutdown does
    second, _ = gateway(tmp_path / "second", state)  # a new process would restore the same way
    await _session(second, calls[20:])

    assert factors(tmp_path / "first") + factors(tmp_path / "second") == factors(
        tmp_path / "straight"
    )
