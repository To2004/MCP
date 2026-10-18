#!/usr/bin/env python3
"""Replay a recorded org-traffic corpus through the gateway, as the agents that made it.

The corpus (``reports/experiments/dynamic_layer/v3/github_helios_org.csv``) was recorded
against the 26-tool npx GitHub server. The remote GitHub MCP merged several of those tools
into one tool with a ``method`` argument and renamed some arguments, so each call is
translated before it is sent. Each persona gets its own MCP session, so the gateway sees
several agents interleaved in the corpus order.

Writes are not sent by default: they would change real repositories. ``--writes scratch``
sends only the writes aimed at the scratch repository the corpus run created.

    uv run python scripts/gateway_replay_corpus.py --limit 50
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from collections import Counter
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.exceptions import McpError

from mcp_security.gateway.github_remote import translate_call

DEFAULT_CORPUS = Path("reports/experiments/dynamic_layer/v3/github_helios_org.csv")
DEFAULT_GATEWAY = "http://127.0.0.1:8765"
DEFAULT_ROUTE = "github"
SCRATCH_REPO = "mcp-traffic-scratch"
WRITE_CATEGORY = "write"


def should_send(row: dict, writes: str) -> bool:
    """Reads always; writes only to the scratch repository, and only when asked."""
    if row["category"] != WRITE_CATEGORY:
        return True
    return writes == "scratch" and json.loads(row["args"]).get("repo") == SCRATCH_REPO


def load_corpus(path: Path, limit: int | None) -> list[dict]:
    """The corpus rows in recorded order, optionally only the first ``limit``."""
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows[:limit] if limit else rows


async def replay(url: str, headers: dict[str, str], rows: list[dict], writes: str) -> Counter:
    """Send every row through its persona's session; count outcomes."""
    outcomes: Counter = Counter()
    async with AsyncExitStack() as stack:
        sessions: dict[str, ClientSession] = {}
        for row in rows:
            if not should_send(row, writes):
                outcomes["not_sent_write"] += 1
                continue
            persona = row["persona"]
            if persona not in sessions:
                read, write, _ = await stack.enter_async_context(
                    streamablehttp_client(url, headers=headers)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                sessions[persona] = session
            tool, args = translate_call(row["tool"], json.loads(row["args"]))
            try:
                result = await sessions[persona].call_tool(tool, args)
            except McpError:  # the server refused the request; the gateway logged it
                outcomes["rpc_error"] += 1
                continue
            outcomes["tool_error" if result.isError else "ok"] += 1
            if sum(outcomes.values()) % 100 == 0:
                print(f"  {sum(outcomes.values())} rows, {dict(outcomes)}", flush=True)
    return outcomes


def main() -> None:
    """Replay ``--corpus`` through ``--gateway``/``--route``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--gateway", default=DEFAULT_GATEWAY)
    parser.add_argument("--route", default=DEFAULT_ROUTE)
    parser.add_argument("--limit", type=int, help="replay only the first N rows")
    parser.add_argument("--writes", choices=["skip", "scratch"], default="skip")
    args = parser.parse_args()

    token = os.environ.get("GATEWAY_AGENT_TOKEN")  # an access token from the identity provider
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{args.gateway.rstrip('/')}/{args.route}"
    rows = load_corpus(args.corpus, args.limit)
    print(f"replaying {len(rows)} rows from {args.corpus} via {url} (writes: {args.writes})")
    outcomes = asyncio.run(replay(url, headers, rows, args.writes))
    print(f"done: {dict(outcomes)}")


if __name__ == "__main__":
    main()
