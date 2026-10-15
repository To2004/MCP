"""Load generator: many agents, each with its own token, calling tools as fast as replies come.

Each agent opens a session (initialize, tools/list) and then sends `tools/call` requests
drawn from the corpus until the deadline, one at a time (an agent waits for its reply).
Agent ``i`` goes to ``ports[hash(agent) % len(ports)]``, which is how a load balancer that
routes by caller would shard the gateway. Prints one JSON line of results.

    python loadgen.py --base http://127.0.0.1 --ports 8800 --path /github --agents 64 \
        --first 0 --seconds 20 --tokens tokens.json
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import time
from pathlib import Path

import httpx

from mcp_security.gateway.github_remote import translate_call

CORPUS = Path("reports/experiments/real_benign/github_helios_org_100k.csv")
HEADERS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


def load_calls() -> list[tuple[str, dict]]:
    with CORPUS.open(encoding="utf-8") as handle:
        return [translate_call(r["tool"], json.loads(r["args"])) for r in csv.DictReader(handle)]


def shard(agent: str, n: int) -> int:
    return int(hashlib.sha256(agent.encode()).hexdigest(), 16) % n


async def agent_loop(client: httpx.AsyncClient, url: str, token: str | None, offset: int,
                     calls: list, deadline: float, latencies: list, errors: list) -> None:
    headers = dict(HEADERS)
    if token:
        headers["authorization"] = f"Bearer {token}"
    init = {"jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                       "clientInfo": {"name": "loadgen", "version": "1"}}}
    reply = await client.post(url, json=init, headers=headers)
    if session := reply.headers.get("mcp-session-id"):
        headers["mcp-session-id"] = session
    await client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=headers)
    i = offset
    while time.perf_counter() < deadline:
        tool, args = calls[i % len(calls)]
        body = {"jsonrpc": "2.0", "id": i + 2, "method": "tools/call",
                "params": {"name": tool, "arguments": args}}
        started = time.perf_counter()
        try:
            r = await client.post(url, json=body, headers=headers)
            r.raise_for_status()
            latencies.append(time.perf_counter() - started)
        except httpx.HTTPStatusError as exc:
            errors.append(f"HTTP {exc.response.status_code}")
        except httpx.HTTPError as exc:
            errors.append(type(exc).__name__)
        i += 997  # agents walk the corpus at different strides


async def run(args: argparse.Namespace) -> dict:
    calls = load_calls()
    tokens = json.loads(Path(args.tokens).read_text()) if args.tokens else {}
    ports = [int(p) for p in args.ports.split(",")]
    limits = httpx.Limits(max_connections=args.agents * 2, max_keepalive_connections=args.agents)
    latencies: list[float] = []
    errors: list[str] = []
    async with httpx.AsyncClient(limits=limits, timeout=60) as client:
        names = [f"agent-{i}" for i in range(args.first, args.first + args.agents)]
        await asyncio.sleep(0)
        deadline = time.perf_counter() + args.seconds
        started = time.perf_counter()
        await asyncio.gather(*(
            agent_loop(client, f"{args.base}:{ports[shard(n, len(ports))]}{args.path}",
                       tokens.get(n), k * 131, calls, deadline, latencies, errors)
            for k, n in enumerate(names)))
        wall = time.perf_counter() - started
    kinds: dict[str, int] = {}
    for e in errors:
        kinds[e] = kinds.get(e, 0) + 1
    return {"calls": len(latencies), "errors": len(errors), "error_kinds": kinds, "wall_s": wall,
            "latencies_ms": [round(x * 1000, 3) for x in latencies]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1")
    parser.add_argument("--ports", required=True)
    parser.add_argument("--path", default="/github")
    parser.add_argument("--agents", type=int, required=True)
    parser.add_argument("--first", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--tokens")
    print(json.dumps(asyncio.run(run(parser.parse_args()))))


if __name__ == "__main__":
    main()
