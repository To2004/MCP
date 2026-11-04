"""INF-3: a small synthetic gateway log, written by the gateway itself, and its pinned re-score.

The log is recorded once by the real gateway app (``proxy.create_app``) in front of a fake
upstream, with callers signed in by the test identity provider (``tokens.py``) and a fake
clock, so every line comes from the gateway's own writers. Nothing in it is real: the users,
issuer, tokens and repositories are invented here. Never copy ``runs/gateway/*.jsonl`` into
the golden folder: those logs can hold real identities.

The run goes through the app's lifespan, so the log starts with ``gateway_started`` and ends
with ``gateway_stopped`` (their ``gateway.config_sha256`` is the route's config digest).

The pin is the CSV that ``score.py`` writes when it re-scores that log with the route's v4
behaviour policy. Re-baseline it only for an intended change, and name it (E9, AI-3 or PS7
are the changes allowed to move it). By default only the CSV is rewritten, from the pinned
log, so a diff shows scorer drift alone:

    uv run python -m tests.gateway.golden_log --reason "AI-3: <why the re-score changes>"

A change to the live gateway's lines (E9) also re-records the log and the artifacts first:

    uv run python -m tests.gateway.golden_log --rerecord --reason "E9: <why the lines change>"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import shutil
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp_security.behaviour import BehaviourConfig
from mcp_security.behaviour.policy import config_to_json
from mcp_security.gateway import proxy, score, wire_log
from mcp_security.gateway.config import DEFAULT_HASH_KEY_ENV, GatewayConfig, Upstream
from mcp_security.gateway.wire_log import catalog_digest
from tests.gateway.tokens import OAUTH, mint, verifier

GOLDEN_DIR = Path(__file__).parent / "golden"
CHANGELOG = GOLDEN_DIR / "CHANGELOG.md"
ROUTE = "github"
KIND = "gh"
LOG_NAME = f"{ROUTE}.jsonl"
CSV_NAME = f"{ROUTE}_scored.csv"
SCAN_NAME, BREADTH_NAME, POLICY_NAME = "scan.json", "breadth.json", "behaviour_policy_v4.json"
UPSTREAM_URL = "http://upstream/mcp"
SEED = 20_261_026
START = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()  # a Monday, 00:00 UTC
DAY_S, HOUR_S = 86_400.0, 3_600.0
DAYS = 5
CLOCK_STEP_S = 0.05  # each line the gateway writes is this much later than the one before
PROXY_HOST = "127.0.0.1"
USER_AGENT = "golden-agent/1.0"
INVALID_PARAMS = -32602
ORG = "acme"

#: The synthetic catalog: tool -> impact on the scan's ladder (4 = write).
IMPACT = {
    "get_file_contents": 1,
    "list_commits": 1,
    "pull_request_review": 2,
    "merge_pull_request": 4,
    "create_issue": 4,
}
SENSITIVITY = {"repo-a": 4, "repo-b": 5, "repo-c": 2, "repo-d": 1, "repo-e": 3}
TOOLS = [{"name": tool} for tool in IMPACT]
BAND_EDGES = ((10.0, "low"), (30.0, "medium"), (60.0, "high"))
INPUTS = {
    "get_file_contents": ("owner", "repo", "path"),
    "list_commits": ("owner", "repo", "perPage"),
    "pull_request_review": ("owner", "repo", "pullNumber"),
    "merge_pull_request": ("owner", "repo", "pullNumber"),
    "create_issue": ("owner", "repo", "title", "body"),
}
POLICY = BehaviourConfig(
    design="v4",
    warmup_calls=3,
    burst_per_minute=6,
    request_limit_bytes=1_000,
    request_limit_by_tool={"create_issue": 3_000},
    many_assets_per_hour=3,
    requires_before={"merge_pull_request": frozenset({"pull_request_review"})},
)


def _band(cell: float) -> str:
    return next((band for edge, band in BAND_EDGES if cell < edge), "critical")


def scan_artifact() -> dict:
    """The route's synthetic scan: cells, bands, sensitivities, impacts, blast radii."""
    cells, bands, blast = {}, {}, {}
    for i, (asset, sensitivity) in enumerate(SENSITIVITY.items()):
        cells[asset], bands[asset] = {}, {}
        for j, (tool, impact) in enumerate(IMPACT.items()):
            radius = 1 + (i + j) % 5
            cells[asset][tool] = float(sensitivity * impact * radius)
            bands[asset][tool] = _band(cells[asset][tool])
            blast[f"{tool}|{asset}"] = radius
    return {
        "cells": cells,
        "bands": bands,
        "asset_sensitivity": SENSITIVITY,
        "tool_impact": IMPACT,
        "blast_radius": blast,
        "score_max": 125,
        "catalog": {"sha256": catalog_digest({"tools": TOOLS})},
    }


def breadth_artifact() -> dict:
    """Breadth specs: every input of every tool is a plain, unbounded value."""
    entry = {"kind": "none", "breadth": 5, "ceiling": None, "default": None}
    return {
        "tools": {
            tool: {"inputs": [{"name": name, **entry} for name in inputs]}
            for tool, inputs in INPUTS.items()
        }
    }


def write_artifacts(where: Path) -> None:
    """The scan, breadth and v4 behaviour policy files the route is configured with."""
    (where / SCAN_NAME).write_text(json.dumps(scan_artifact(), indent=1), encoding="utf-8")
    (where / BREADTH_NAME).write_text(json.dumps(breadth_artifact(), indent=1), encoding="utf-8")
    (where / POLICY_NAME).write_text(json.dumps(config_to_json(POLICY), indent=1), encoding="utf-8")


def route(where: Path) -> Upstream:
    """The route as the routes file names it, reading its artifacts from ``where``."""
    return Upstream(
        name=ROUTE,
        url=UPSTREAM_URL,
        scan=str(where / SCAN_NAME),
        breadth=str(where / BREADTH_NAME),
        kind=KIND,
        behaviour_policy=str(where / POLICY_NAME),
    )


@dataclass(frozen=True)
class Step:
    """One request the traffic sends: who, when, from where, and the JSON-RPC body."""

    ts: float
    caller: str
    body: dict
    address: str
    session: str | None = None  # a key into the sessions opened so far, not the server's id


class _FakeUpstream:
    """An MCP server: a new session per initialize, the catalog, and canned call results."""

    def __init__(self) -> None:
        self.sessions = 0

    def app(self) -> Starlette:
        async def mcp(request: Request) -> Response:
            message = json.loads(await request.body())
            rpc_id, method = message.get("id"), message["method"]
            if method == "initialize":
                self.sessions += 1
                reply = {"jsonrpc": "2.0", "id": rpc_id, "result": {"serverInfo": {}}}
                return JSONResponse(reply, headers={"mcp-session-id": f"up-{self.sessions}"})
            if method == "tools/list":
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}})
            args = (message.get("params") or {}).get("arguments") or {}
            if args.get("repo") not in SENSITIVITY:
                error = {"code": INVALID_PARAMS, "message": "no such repository"}
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "error": error})
            failed = args.get("title") == "fail"
            result = {"content": [{"type": "text", "text": "ok"}], "isError": failed}
            return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})

        return Starlette(routes=[Route("/mcp", mcp, methods=["POST"])])


def _call(rpc_id: int, tool: str, repo: str, **extra: object) -> dict:
    args = {"owner": ORG, "repo": repo, **extra}
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }


def _rpc(rpc_id: int, method: str, params: dict | None = None) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params or {}}


def traffic(seed: int = SEED) -> list[Step]:
    """Four callers over five days: sessions, sessionless bot calls, a network change, a
    merge with no review, a burst, a sweep, an oversized request and two failed calls."""
    rng = random.Random(seed)
    steps: list[Step] = []
    ids = iter(range(1, 1_000_000))

    def session(caller: str, ts: float, address: str, client: str, calls: list[dict]) -> None:
        key = f"{caller}@{ts:.0f}"
        init = _rpc(
            next(ids),
            "initialize",
            {"protocolVersion": "2025-06-18", "clientInfo": {"name": client, "version": "1.0"}},
        )
        steps.append(Step(ts, caller, init, address))
        steps.append(Step(ts + 1.0, caller, _rpc(next(ids), "tools/list"), address, key))
        for i, call in enumerate(calls):
            steps.append(Step(ts + 2.0 + 90.0 * i + rng.uniform(0, 30), caller, call, address, key))

    def at(day: int, hour: float) -> float:
        return START + day * DAY_S + hour * HOUR_S + rng.uniform(0, 600)

    for day in range(DAYS):
        alice = [
            _call(
                next(ids),
                rng.choice(["get_file_contents", "list_commits"]),
                rng.choice(["repo-a", "repo-c", "repo-d"]),
                path="README.md",
            )
            for _ in range(5)
        ]
        session("alice", at(day, 9.0), f"10.1.0.{rng.randint(2, 250)}", "claude-code", alice)
        bob_net = "172.16.4" if day >= 3 else "10.2.0"  # bob's network changes on day 3
        bob = [
            _call(
                next(ids), "get_file_contents", rng.choice(["repo-c", "repo-e"]), path="src/main.py"
            )
            for _ in range(4)
        ]
        session("bob", at(day, 15.0), f"{bob_net}.{rng.randint(2, 250)}", "cursor", bob)
        pr = rng.randint(1, 90)
        carol = [
            _call(next(ids), "pull_request_review", "repo-a", pullNumber=pr),
            _call(next(ids), "merge_pull_request", "repo-a", pullNumber=pr),
        ]
        if day == 4:
            carol = carol[1:]  # a merge with no review earlier in the session
        session("carol", at(day, 11.0), f"10.3.0.{rng.randint(2, 250)}", "claude-code", carol)
        for hour in (1.0, 7.0, 13.0, 19.0):  # the bot: sessionless, clientInfo in _meta
            call = _call(next(ids), "list_commits", "repo-d", perPage=100)
            call["params"]["_meta"] = {
                wire_log.META_CLIENT: {"name": "ci-runner", "version": "3.2"}
            }
            steps.append(Step(at(day, hour), "ci-bot", call, "10.9.0.5"))
    day4, day5 = START + 3 * DAY_S, START + 4 * DAY_S
    steps += [  # one-off events
        Step(
            day4 + 10 * HOUR_S,
            "alice",
            _call(next(ids), "get_file_contents", "repo-missing", path="x"),
            "10.1.0.7",
        ),
        Step(
            day4 + 10.1 * HOUR_S,
            "alice",
            _call(next(ids), "create_issue", "repo-c", title="fail", body="..."),
            "10.1.0.7",
        ),
        Step(
            day5 + 10 * HOUR_S,
            "alice",
            _call(next(ids), "create_issue", "repo-c", title="long", body="x" * 4_000),
            "10.1.0.7",
        ),
    ]
    steps += [
        Step(
            day5 + 3 * HOUR_S + 2.0 * i,
            "ci-bot",
            _call(next(ids), "list_commits", "repo-d", perPage=100),
            "10.9.0.5",
        )
        for i in range(10)
    ]  # a burst
    steps += [
        Step(
            day5 + 17 * HOUR_S + 300.0 * i,
            "bob",
            _call(next(ids), "get_file_contents", repo, path="a"),
            "172.16.4.9",
        )
        for i, repo in enumerate(SENSITIVITY)
    ]  # a sweep: five repositories in an hour
    return sorted(steps, key=lambda s: s.ts)


TOKEN_SUBJECTS = {  # caller -> (sub, client_id): who the test identity provider signs in
    "alice": ("alice-sub", "claude-code"),
    "bob": ("bob-sub", "cursor"),
    "carol": ("carol-sub", "claude-code"),
    "ci-bot": ("ci-bot", "ci-bot"),  # client credentials: the service is its own subject
}


class _Clock:
    """The time the gateway's writers read: set per request, a step later per line."""

    def __init__(self) -> None:
        self.now = START

    def at(self, ts: float) -> None:
        self.now = max(self.now, ts)

    def time(self) -> float:
        self.now += CLOCK_STEP_S
        return self.now


@contextmanager
def _deterministic(clock: _Clock) -> Iterator[None]:
    """The gateway's clock and exchange ids, made reproducible for the recording."""
    original = proxy._exchange
    counter = iter(range(1, 1_000_000))

    def stamped(*args: object, **kwargs: object) -> wire_log.Exchange:
        exchange = original(*args, **kwargs)
        return replace(exchange, received=clock.now, id=f"{next(counter):032x}")

    with (
        mock.patch.object(wire_log, "time", clock),
        mock.patch.object(proxy, "_exchange", stamped),
        mock.patch.dict(os.environ),
    ):
        os.environ.pop(DEFAULT_HASH_KEY_ENV, None)  # pseudonyms: plain SHA-256
        yield


async def _drive(where: Path, logs: Path) -> None:
    upstream = _FakeUpstream()
    config = GatewayConfig(
        upstreams={ROUTE: route(where)},
        log_dir=logs,
        trusted_proxies=(f"{PROXY_HOST}/32",),
        oauth=OAUTH,
    )
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream.app()))
    app = proxy.create_app(config, client=client, verifier=verifier())
    gateway = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(PROXY_HOST, 50_000)), base_url="http://gw"
    )
    tokens = {c: mint(sub=sub, client_id=app_id) for c, (sub, app_id) in TOKEN_SUBJECTS.items()}
    opened: dict[str, str] = {}
    clock = _Clock()
    # the lifespan writes the start and stop lines and closes the log, as a real run does
    with _deterministic(clock):
        async with app.router.lifespan_context(app):
            for step in traffic():
                clock.at(step.ts)
                headers = {
                    "authorization": f"Bearer {tokens[step.caller]}",
                    "content-type": "application/json",
                    "user-agent": USER_AGENT,
                    "x-forwarded-for": step.address,
                }
                if step.session:
                    headers["mcp-session-id"] = opened[step.session]
                reply = await gateway.post(f"/{ROUTE}", json=step.body, headers=headers)
                if step.body["method"] == "initialize":
                    opened[f"{step.caller}@{step.ts:.0f}"] = reply.headers["mcp-session-id"]


def record_log(where: Path) -> Path:
    """Write the artifacts and the synthetic log into ``where``; the log's path."""
    write_artifacts(where)
    with tempfile.TemporaryDirectory() as scratch:
        logs = Path(scratch) / "logs"
        asyncio.run(_drive(where, logs))
        shutil.copyfile(logs / LOG_NAME, where / LOG_NAME)
    return where / LOG_NAME


def rescore(golden: Path, out_dir: Path) -> Path:
    """Re-score ``golden``'s log through ``score.py``'s CLI, as an operator would; the CSV."""
    logs = out_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(golden / LOG_NAME, logs / LOG_NAME)
    entry = {
        "url": UPSTREAM_URL,
        "scan": str(golden / SCAN_NAME),
        "breadth": str(golden / BREADTH_NAME),
        "kind": KIND,
        "behaviour_policy": str(golden / POLICY_NAME),
    }
    routes = out_dir / "routes.json"
    routes.write_text(
        json.dumps({"log_dir": str(logs), "upstreams": {ROUTE: entry}}), encoding="utf-8"
    )
    argv = ["score", "--config", str(routes), "--route", ROUTE]
    with mock.patch.object(sys, "argv", argv):
        score.main()
    return logs / CSV_NAME


def main() -> None:
    """Re-score the pinned log into the CSV (``--rerecord``: re-record the log and artifacts
    first), and append the reason and the mode to the changelog."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reason", required=True, help="the change that moves the re-score")
    parser.add_argument(
        "--rerecord",
        action="store_true",
        help="also re-record the log and artifacts (a change to the live gateway's lines)",
    )
    args = parser.parse_args()
    GOLDEN_DIR.mkdir(exist_ok=True)
    if args.rerecord:
        record_log(GOLDEN_DIR)
    with tempfile.TemporaryDirectory() as scratch:
        shutil.copyfile(rescore(GOLDEN_DIR, Path(scratch)), GOLDEN_DIR / CSV_NAME)
    done = f"re-recorded {LOG_NAME} and re-scored" if args.rerecord else "re-scored"
    with CHANGELOG.open("a", encoding="utf-8") as log:
        log.write(f"- {date.today().isoformat()}: {done} {CSV_NAME}. {args.reason}\n")


if __name__ == "__main__":
    main()
