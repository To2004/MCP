"""Drive a real GitHub MCP server with a realistic org call mix.

The previous live corpus drew its tool uniformly, so all eight tools it touched held an
equal share and none was ever rare. ``org_traffic`` supplies the distribution instead:
roles with different volumes, whose union is heavy-tailed across the full 26-tool catalog.

Writes are real, so they are confined to a scratch repository this script creates and can
delete. Reads go to the account's existing repositories. Failures are recorded in the
``status`` column and kept: the runtime scores the call that was made, not the reply, so a
call the server rejected is still a real observation of what an agent asked for.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import sys
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_real_warmup import CSV_HEADER, _json, _text, server_params  # noqa: E402
from org_traffic import Call, sample_call, write_tools  # noqa: E402

ORGS = {"github": "github_helios", "slack": "slack_vireo", "calendar": "calendar_aurora"}

REPO = Path("/home/ovadyat/MCP")
OUT = REPO / "reports" / "experiments" / "real_benign"
DEFAULT_SEED = 20260814
DEFAULT_CALLS = 1000

#: GitHub's search endpoints allow ~30 requests/minute; everything else is far higher.
_SEARCH_TOOLS = frozenset({"search_code", "search_issues", "search_repositories",
                           "search_users"})
_SEARCH_PACE_SEC = 2.1

#: Repositories probed for real paths and ids. Each costs three calls.
PROBE_REPOS = 8

#: Seeded into the scratch repo so comment/close/review calls have real targets.
_SEED_ISSUES = 4


async def _call(session: ClientSession, tool: str, args: dict) -> str:
    """Invoke one tool, returning a short status rather than raising."""
    try:
        result = await session.call_tool(tool, args)
    except Exception as exc:                      # noqa: BLE001 - status is the datum here
        return f"error:{type(exc).__name__}"
    return "error:tool" if getattr(result, "isError", False) else "ok"


async def probe_slack(session: ClientSession) -> dict:
    """Learn which channels and usergroups exist, so arguments name real ones."""
    state: dict = {"channels": [], "usergroups": [], "thread_ts": "0.0"}
    listing = _json(await session.call_tool(
        "channels_list", {"channel_types": "public_channel", "limit": 100}))
    rows = listing if isinstance(listing, list) else (listing or {}).get("channels") or []
    state["channels"] = [c["id"] for c in rows if isinstance(c, dict) and c.get("id")]
    if not state["channels"]:
        text = _text(await session.call_tool(
            "channels_list", {"channel_types": "public_channel", "limit": 100}))
        state["channels"] = re.findall(r"C[A-Z0-9]{8,}", text)[:60]
    groups = _text(await session.call_tool("usergroups_list", {}))
    state["usergroups"] = re.findall(r"S[A-Z0-9]{8,}", groups)[:20] or ["S0000000000"]
    return state


async def probe_calendar(session: ClientSession) -> dict:
    """Learn which calendars exist and pick real event ids to name."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    state: dict = {
        "calendars": [], "events": [],
        "now": now.isoformat().replace("+00:00", "Z"),
        "horizon": {d: (now + timedelta(days=d)).isoformat().replace("+00:00", "Z")
                    for d in (1, 7, 14, 30, 90, 365)},
    }
    text = _text(await session.call_tool("list-calendars", {}))
    ids = re.findall(r"[\w.+-]+@[\w.-]+|[a-z0-9]{20,}@group\.v\.calendar\.google\.com", text)
    state["calendars"] = list(dict.fromkeys(ids))[:12] or ["primary"]
    events = _text(await session.call_tool(
        "list-events", {"calendarId": [state["calendars"][0]],
                        "timeMin": state["now"], "timeMax": state["horizon"][90]}))
    state["events"] = re.findall(r"\b[a-z0-9_]{10,}\b", events)[:30] or ["evt0"]
    return state


async def probe(session: ClientSession, owner: str, scratch: str) -> dict:
    """Learn what really exists, so sampled arguments name real things."""
    state: dict = {"owner": owner, "repos": [], "write_repo": scratch,
                   "paths": {}, "issues": {}, "pulls": {}}

    found = _json(await session.call_tool(
        "search_repositories", {"query": f"user:{owner}", "perPage": 30, "page": 1}))
    items = (found or {}).get("items") or []
    state["repos"] = [it["name"] for it in items if it.get("name")] or [scratch]

    for repo in state["repos"][:PROBE_REPOS]:
        listing = _json(await session.call_tool(
            "get_file_contents", {"owner": owner, "repo": repo, "path": ""}))
        if isinstance(listing, list):
            state["paths"][repo] = [e["path"] for e in listing
                                    if e.get("type") == "file"][:8] or ["README.md"]
        issues = _json(await session.call_tool(
            "list_issues", {"owner": owner, "repo": repo, "state": "all", "per_page": 30}))
        if isinstance(issues, list) and issues:
            state["issues"][repo] = [i["number"] for i in issues][:20]
        pulls = _json(await session.call_tool(
            "list_pull_requests", {"owner": owner, "repo": repo, "state": "all",
                                   "per_page": 30}))
        if isinstance(pulls, list) and pulls:
            state["pulls"][repo] = [p["number"] for p in pulls][:20]

    for n in range(_SEED_ISSUES):
        await _call(session, "create_issue", {
            "owner": owner, "repo": scratch, "title": f"Seed issue {n + 1}",
            "body": "Created so comment and close calls have a real target."})
    seeded = _json(await session.call_tool(
        "list_issues", {"owner": owner, "repo": scratch, "state": "all", "per_page": 30}))
    if isinstance(seeded, list) and seeded:
        state["issues"][scratch] = [i["number"] for i in seeded]
    return state


async def run(server: str, owner: str, scratch: str, count: int, seed: int, out: Path,
              skip_writes: bool) -> int:
    """Sample and execute ``count`` calls, writing one CSV row each.

    ``skip_writes`` records a state-changing call with its real arguments but never sends
    it. The runtime scores the call that was made, not the reply, so such a row is worth
    exactly as much to B and L as one the server rejected -- and nothing outward-facing
    happens on a workspace or calendar that is not ours to mutate.
    """
    rng = random.Random(seed)
    writes = write_tools(server)
    rows: list[dict] = []
    async with stdio_client(server_params(server)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if server == "slack":
                state = await probe_slack(session)
                print(f"channels={len(state['channels'])} "
                      f"usergroups={len(state['usergroups'])}", flush=True)
            elif server == "calendar":
                state = await probe_calendar(session)
                print(f"calendars={len(state['calendars'])} "
                      f"events={len(state['events'])}", flush=True)
            else:
                state = await probe(session, owner, scratch)
                print(f"repos={len(state['repos'])} with-issues={len(state['issues'])} "
                      f"with-pulls={len(state['pulls'])} scratch={scratch}", flush=True)

            started = time.time()
            out.parent.mkdir(parents=True, exist_ok=True)
            handle = out.open("w", newline="")
            writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
            writer.writeheader()
            for index in range(1, count + 1):
                call: Call = sample_call(rng, state, server)
                if skip_writes and call.tool in writes:
                    status = "skipped:not-executed"
                else:
                    if call.tool in _SEARCH_TOOLS:
                        await asyncio.sleep(_SEARCH_PACE_SEC)
                    status = await _call(session, call.tool, call.args)
                row = {
                    "index": index, "org": ORGS[server], "persona": call.persona,
                    "category": "write" if call.tool in writes else "read",
                    "asset": str(call.args.get("repo") or call.args.get("channel_id")
                                  or call.args.get("calendarId") or ""),
                    "tool": call.tool, "status": status,
                    "args": json.dumps(call.args, separators=(",", ":")),
                    "source": "live",
                }
                rows.append(row)
                writer.writerow(row)
                handle.flush()
                if index % 25 == 0:
                    ok = sum(r["status"] == "ok" for r in rows)
                    rate = (time.time() - started) / index
                    print(f"  {index}/{count}  ok={ok}  {time.time() - started:.0f}s  "
                          f"{rate:.1f}s/call  eta {rate * (count - index) / 60:.0f}min",
                          flush=True)
            handle.close()
    ok = sum(r["status"] == "ok" for r in rows)
    print(f"\nwrote {len(rows)} calls to {out}  ok={ok} ({ok / len(rows) * 100:.0f}%)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="github", choices=sorted(ORGS))
    parser.add_argument("--skip-writes", action="store_true",
                        help="record state-changing calls without sending them")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "To2004"))
    parser.add_argument("--scratch", default="mcp-traffic-scratch",
                        help="repository that receives every write; must be one we own")
    parser.add_argument("--calls", type=int, default=DEFAULT_CALLS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    out = args.out or OUT / f"{ORGS[args.server]}_org.csv"
    return asyncio.run(run(args.server, args.owner, args.scratch, args.calls, args.seed,
                           out, args.skip_writes))


if __name__ == "__main__":
    raise SystemExit(main())
