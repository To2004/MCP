"""Generate a large synthetic corpus with the same call mix as the live org run.

Same ``org_traffic`` model, same arguments sampler, same assets — only the network is
missing. The state (which repositories, paths, issue and pull numbers exist) is recovered
from the live corpus rather than invented, so the two runs differ in exactly one respect:
how many calls were drawn. Anything the runtime does differently between them is therefore
a property of sample size, not of two unrelated generators.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_real_warmup import CSV_HEADER  # noqa: E402
from org_traffic import sample_call, write_tools  # noqa: E402

REPO = Path("/home/ovadyat/MCP")
OUT = REPO / "reports" / "experiments" / "real_benign"
ORG = "github_helios"
DEFAULT_SEED = 20260815
DEFAULT_CALLS = 100_000


def _slack_state(rows: list[dict]) -> dict:
    """Recover the channels, usergroups and a thread stamp the live run really used."""
    channels: set[str] = set()
    usergroups: set[str] = set()
    thread_ts = "0.0"
    for row in rows:
        args = json.loads(row["args"])
        if isinstance(args.get("channel_id"), str):
            channels.add(args["channel_id"])
        if isinstance(args.get("filter_in_channel"), str):
            channels.add(args["filter_in_channel"])
        if isinstance(args.get("usergroup_id"), str):
            usergroups.add(args["usergroup_id"])
        if isinstance(args.get("ts"), str) and args["ts"] != "0.0":
            thread_ts = args["ts"]
    if not channels:
        raise ValueError("no channels recoverable")
    return {"channels": sorted(channels), "usergroups": sorted(usergroups) or ["S0000000000"],
            "thread_ts": thread_ts}


def _calendar_state(rows: list[dict]) -> dict:
    """Recover the calendars, event ids and the time origin the live run really used."""
    calendars: set[str] = set()
    events: set[str] = set()
    horizon: dict[int, str] = {}
    now = ""
    for row in rows:
        args = json.loads(row["args"])
        target = args.get("calendarId")
        for value in (target if isinstance(target, list) else [target]):
            if isinstance(value, str) and value:
                calendars.add(value)
        for entry in args.get("calendars") or []:
            if isinstance(entry, dict) and entry.get("id"):
                calendars.add(entry["id"])
        if isinstance(args.get("eventId"), str):
            events.add(args["eventId"])
        if isinstance(args.get("timeMin"), str):
            now = now or args["timeMin"]
        if isinstance(args.get("timeMax"), str):
            horizon[len(horizon)] = args["timeMax"]
    if not calendars:
        raise ValueError("no calendars recoverable")
    # The window ends the live run used, keyed by the day counts the sampler asks for.
    ends = sorted(set(horizon.values()))
    days = (1, 7, 14, 30, 90, 365)
    return {"calendars": sorted(calendars), "events": sorted(events) or ["evt0"],
            "now": now or "2026-08-14T00:00:00Z",
            "horizon": {d: ends[min(i, len(ends) - 1)] for i, d in enumerate(days)}}


def state_from_corpus(path: Path, server: str = "github") -> dict:
    """Rebuild the sampler's world from the calls the live run actually made."""
    if server != "github":
        with path.open() as handle:
            rows = list(csv.DictReader(handle))
        return _slack_state(rows) if server == "slack" else _calendar_state(rows)
    repos: set[str] = set()
    paths: dict[str, set[str]] = collections.defaultdict(set)
    issues: dict[str, set[int]] = collections.defaultdict(set)
    pulls: dict[str, set[int]] = collections.defaultdict(set)
    owner = ""
    write_repo = ""

    with path.open() as handle:
        for row in csv.DictReader(handle):
            args = json.loads(row["args"])
            owner = args.get("owner") or owner
            repo = args.get("repo")
            if not repo:
                continue
            repos.add(repo)
            if row["category"] == "write":
                write_repo = repo
            if isinstance(args.get("path"), str) and args["path"]:
                paths[repo].add(args["path"])
            if isinstance(args.get("issue_number"), int):
                issues[repo].add(args["issue_number"])
            if isinstance(args.get("pull_number"), int):
                pulls[repo].add(args["pull_number"])

    if not repos:
        raise ValueError(f"no repositories recoverable from {path}")
    return {
        "owner": owner,
        "repos": sorted(repos),
        "write_repo": write_repo or sorted(repos)[0],
        "paths": {r: sorted(p) for r, p in paths.items()},
        "issues": {r: sorted(i) for r, i in issues.items()},
        "pulls": {r: sorted(p) for r, p in pulls.items()},
    }


def generate(state: dict, count: int, seed: int, out: Path, server: str) -> None:
    """Draw ``count`` calls and write them in the shared corpus format."""
    rng = random.Random(seed)
    writes = write_tools(server)
    out.parent.mkdir(parents=True, exist_ok=True)
    tools: collections.Counter[str] = collections.Counter()
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        for index in range(1, count + 1):
            call = sample_call(rng, state, server)
            tools[call.tool] += 1
            writer.writerow({
                "index": index, "org": ORG, "persona": call.persona,
                "category": "write" if call.tool in writes else "read",
                "asset": call.args.get("repo", call.args.get("name", "")),
                "tool": call.tool, "status": "synthetic",
                "args": json.dumps(call.args, separators=(",", ":")),
                "source": "synthetic",
            })
    print(f"wrote {count:,} calls to {out}")
    print(f"{len(tools)} distinct tools; "
          f"most common {tools.most_common(1)[0][0]} at {tools.most_common(1)[0][1] / count:.1%}, "
          f"rarest {tools.most_common()[-1][0]} at {tools.most_common()[-1][1] / count:.2%}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-from", type=Path, default=OUT / "github_helios_org.csv",
                        help="live corpus whose repositories and ids to reuse")
    parser.add_argument("--server", default="github")
    parser.add_argument("--calls", type=int, default=DEFAULT_CALLS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=OUT / "github_helios_org_100k.csv")
    args = parser.parse_args(argv)
    generate(state_from_corpus(args.state_from, args.server), args.calls, args.seed,
             args.out, args.server)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
