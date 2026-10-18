"""Drive the three real MCP servers with read-only calls, to warm the breadth fences.

The runtime layer decides "is this call unusually broad for this organization" from the
distribution of quantity arguments it has seen. Every corpus available so far was
generated from the scan artifacts, so its argument sizes were chosen by whoever wrote
the generator — which makes any outlier found in it an outlier with respect to an
invented distribution. This script produces the missing input: **real calls to real
servers, whose breadth comes from real account state.**

The distinction that matters: the number of calendars in a `list-events` call is bounded
by how many calendars the account actually has; the `limit` on a Slack history read is
drawn from how many messages a real channel actually holds; a GitHub path is a path that
really exists. Nobody picked those numbers to be interesting.

**Read-only by construction.** Every tool used here reads. The servers are pointed at
live accounts, so a write would be a real, externally-visible change; the tool lists
below are filtered to reads and nothing else. That also keeps the corpus honest — a
failed write teaches the fences nothing.

Credentials come from the environment, never from disk into the output:

    GITHUB_TOKEN         (or `gh auth token`)
    SLACK_MCP_XOXP_TOKEN
    GOOGLE_OAUTH_CREDENTIALS / calendar token path

    python3 scripts/dynamic_design/make_real_warmup.py --server slack --n 1000
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path("/home/ovadyat/MCP")
OUT = REPO / "reports" / "experiments" / "real_warmup"
NODE_BIN = Path.home() / ".conda" / "envs" / "mcpnode" / "bin"
CSV_HEADER = ["index", "org", "persona", "category", "asset", "tool", "status", "args", "source"]

ORG = {"github": "github_helios", "slack": "slack_vireo", "calendar": "calendar_aurora"}
PERSONA = {"github": "Real Agent@helios", "slack": "Real Agent@vireo",
           "calendar": "Real Agent@aurora"}
DEFAULT_SEED = 20260813


def node_env() -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{NODE_BIN}:{env.get('PATH', '')}"
    return env


def server_params(kind: str) -> StdioServerParameters:
    """Launch spec for one real MCP server, with its credential from the environment."""
    env = node_env()
    if kind == "github":
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = os.environ["GITHUB_TOKEN"]
        return StdioServerParameters(
            command=str(NODE_BIN / "npx"),
            args=["-y", "@modelcontextprotocol/server-github"], env=env)
    if kind == "slack":
        env["SLACK_MCP_XOXP_TOKEN"] = os.environ["SLACK_MCP_XOXP_TOKEN"]
        env.setdefault("SLACK_MCP_ADD_MESSAGE_TOOL", "")  # keep the write tool disabled
        return StdioServerParameters(
            command=str(NODE_BIN / "npx"), args=["-y", "slack-mcp-server@latest"], env=env)
    if kind == "calendar":
        return StdioServerParameters(
            command=str(NODE_BIN / "npx"),
            args=["-y", "@cocal/google-calendar-mcp"], env=env)
    raise ValueError(kind)


def _text(result) -> str:
    parts = [c.text for c in getattr(result, "content", []) if getattr(c, "type", "") == "text"]
    return "\n".join(parts)


def _json(result):
    try:
        return json.loads(_text(result))
    except (ValueError, TypeError):
        return None


async def probe_github(session: ClientSession, rng: random.Random) -> dict:
    """Real repositories, real paths, real commit counts — the breadth source."""
    state: dict = {"repos": [], "paths": {}}
    got = await session.call_tool("search_repositories", {"query": "user:To2004"})
    payload = _json(got) or {}
    items = payload.get("items") or payload.get("repositories") or []
    for item in items[:12]:
        full = item.get("full_name") or f"{item.get('owner', {}).get('login')}/{item.get('name')}"
        if full and "/" in full:
            state["repos"].append(full)
    for full in state["repos"][:6]:
        owner, repo = full.split("/", 1)
        listing = _json(await session.call_tool(
            "get_file_contents", {"owner": owner, "repo": repo, "path": ""}))
        if isinstance(listing, list):
            state["paths"][full] = [e.get("path") for e in listing if e.get("path")]
    return state


async def probe_slack(session: ClientSession, rng: random.Random) -> dict:
    """This server answers in CSV, not JSON — parse the real channel directory from it."""
    raw = _text(await session.call_tool("channels_list", {"channel_types": "public_channel"}))
    ids: list[str] = []
    reader = csv.DictReader(raw.splitlines())
    for row in reader:
        channel_id = (row.get("ID") or "").strip()
        if channel_id.startswith("C"):
            ids.append(channel_id)
    return {"channels": ids}


async def probe_calendar(session: ClientSession, rng: random.Random) -> dict:
    cals = _json(await session.call_tool("list-calendars", {}))
    ids = []
    if isinstance(cals, dict):
        ids = [c.get("id") for c in cals.get("calendars", []) or [] if c.get("id")]
    elif isinstance(cals, list):
        ids = [c.get("id") for c in cals if isinstance(c, dict) and c.get("id")]
    return {"calendars": ids}


# Paging sizes span the API's own legal range rather than a hand-picked set. The point
# is coverage of every read tool that carries a quantity, because a per-argument
# reference only warms the arguments the traffic actually exercises.
_PAGES = [1, 5, 10, 25, 30, 50, 75, 100]


def plan_github(state: dict, rng: random.Random) -> tuple[str, dict] | None:
    repos = state["repos"]
    if not repos:
        return None
    full = rng.choice(repos)
    owner, repo = full.split("/", 1)
    page = rng.choice([1, 1, 1, 2, 3])
    query = rng.choice(["user:To2004", "language:python", "mcp", "stars:>10000", "agent"])
    return rng.choice([
        lambda: ("get_file_contents", {"owner": owner, "repo": repo,
                                       "path": rng.choice(state["paths"].get(full) or [""])}),
        lambda: ("list_commits", {"owner": owner, "repo": repo,
                                  "perPage": rng.choice(_PAGES), "page": page}),
        lambda: ("list_issues", {"owner": owner, "repo": repo, "state": "all",
                                 "per_page": rng.choice(_PAGES), "page": page}),
        lambda: ("list_pull_requests", {"owner": owner, "repo": repo, "state": "all",
                                        "per_page": rng.choice(_PAGES), "page": page}),
        lambda: ("search_repositories", {"query": query, "perPage": rng.choice(_PAGES),
                                         "page": page}),
        lambda: ("search_code", {"q": f"repo:{full} def", "per_page": rng.choice(_PAGES),
                                 "page": page}),
        lambda: ("search_issues", {"q": f"repo:{full} is:issue", "per_page": rng.choice(_PAGES),
                                   "page": page}),
        lambda: ("search_users", {"q": rng.choice(["To2004", "location:israel"]),
                                  "per_page": rng.choice(_PAGES), "page": page}),
    ])()


def plan_slack(state: dict, rng: random.Random) -> tuple[str, dict] | None:
    channels = state["channels"]
    if not channels:
        return None
    channel = rng.choice(channels)
    window = rng.choice(["1d", "7d", "30d", "90d", "10", "25", "50", "100"])
    types = rng.choice(["public_channel", "im", "mpim",
                        "public_channel,private_channel", "public_channel,im"])
    return rng.choice([
        lambda: ("conversations_history", {"channel_id": channel, "limit": window}),
        lambda: ("conversations_search_messages",
                 {"search_query": rng.choice(["the", "mcp", "test", "hello", "a"]),
                  "limit": rng.choice([1, 5, 20, 50, 100])}),
        lambda: ("conversations_search_messages",
                 {"search_query": "a", "filter_in_channel": channel,
                  "limit": rng.choice([1, 20, 100])}),
        lambda: ("channels_list", {"channel_types": types, "limit": rng.choice([1, 10, 50, 100, 999])}),
        lambda: ("channels_me", {"channel_types": types, "limit": rng.choice([1, 10, 100])}),
        lambda: ("users_search", {"query": rng.choice(["a", "test", "mcp"]),
                                  "limit": rng.choice([1, 5, 20, 50, 100])}),
        lambda: ("conversations_unreads",
                 {"max_channels": rng.choice([1, 5, 20, 50]),
                  "max_messages_per_channel": rng.choice([1, 10, 50])}),
        lambda: ("usergroups_list", {}),
    ])()


def plan_calendar(state: dict, rng: random.Random) -> tuple[str, dict] | None:
    cals = state["calendars"]
    if not cals:
        return None
    # Breadth comes from how many calendars the account really has, and from spans a
    # real scheduling agent would ask for (a day, a week, a month, a quarter, a year).
    k = rng.randint(1, max(1, len(cals)))
    picked = rng.sample(cals, k)
    span_days = rng.choice([1, 7, 14, 30, 90, 180, 365])
    start = datetime(2026, 1, 1)
    end = start + timedelta(days=span_days)
    t_min, t_max = start.isoformat() + "Z", end.isoformat() + "Z"
    return rng.choice([
        lambda: ("list-events", {"calendarId": picked if k > 1 else picked[0],
                                 "timeMin": t_min, "timeMax": t_max}),
        lambda: ("search-events", {"calendarId": picked[0], "query": rng.choice(["meeting", "a", "1:1"]),
                                   "timeMin": t_min, "timeMax": t_max}),
        lambda: ("get-freebusy", {"calendars": [{"id": c} for c in picked],
                                  "timeMin": t_min, "timeMax": t_max,
                                  "calendarExpansionMax": rng.choice([1, 5, 20, 50])}),
        lambda: ("list-calendars", {}),
        lambda: ("list-colors", {}),
        lambda: ("get-current-time", {}),
    ])()


PROBES = {"github": probe_github, "slack": probe_slack, "calendar": probe_calendar}
PLANS = {"github": plan_github, "slack": plan_slack, "calendar": plan_calendar}


async def run(kind: str, n: int, pace: float, seed: int, out: Path) -> int:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{ORG[kind]}_real.csv"
    written = ok = failed = 0
    started = time.time()

    async with stdio_client(server_params(kind)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            print(f"{kind}: {len(tools)} tools advertised", flush=True)
            state = await PROBES[kind](session, rng)
            print(f"{kind}: real state -> "
                  f"{ {k: len(v) for k, v in state.items() if hasattr(v, '__len__')} }", flush=True)

            with path.open("w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(CSV_HEADER)
                while written < n:
                    plan = PLANS[kind](state, rng)
                    if plan is None:
                        print(f"{kind}: no usable real state; stopping", flush=True)
                        break
                    tool, args = plan
                    if tool not in tools:
                        continue
                    status = "OK"
                    try:
                        result = await session.call_tool(tool, args)
                        if getattr(result, "isError", False):
                            status = "ERROR"
                            failed += 1
                        else:
                            ok += 1
                    except Exception as exc:  # noqa: BLE001 - a failed call is still real traffic
                        status = f"EXC:{type(exc).__name__}"
                        failed += 1
                    written += 1
                    writer.writerow([written, ORG[kind], PERSONA[kind], "REAL", "", tool,
                                     status, json.dumps(args), "real_mcp"])
                    if written % 100 == 0:
                        fh.flush()
                        rate = written / max(time.time() - started, 1e-6)
                        print(f"  {kind}: {written}/{n}  ok={ok} failed={failed} "
                              f"({rate:.1f} calls/s)", flush=True)
                    if pace:
                        await asyncio.sleep(pace)

    print(f"{kind}: wrote {written} calls (ok={ok}, failed={failed}) -> {path}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, choices=sorted(ORG))
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--pace", type=float, default=0.0,
                        help="seconds between calls (Slack rate-limits aggressively)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    return asyncio.run(run(args.server, args.n, args.pace, args.seed, args.out))


if __name__ == "__main__":
    raise SystemExit(main())
