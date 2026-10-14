"""Offline trial: which extra runtime signals separate planted misuse-shaped sessions from
normal traffic? No network, no repository content: planted sessions are request records
built from ordinary read calls and appended after the 908 real benign calls.

Every signal is computed per call, in time order, from earlier calls only (what a gateway
knows before forwarding). Run from the repo root: `uv run python reports/experiments/gateway/signal_trial/trial_signals.py`.
"""

from __future__ import annotations

import collections
import math
import statistics
from pathlib import Path

from mcp_security.gateway.proxy import load_config
from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.score import pair_calls, score_calls
from mcp_security.gateway.wire_log import read_log

HERE = Path(__file__).parent
ROUTES = Path("src/mcp_security/gateway/routes.example.json")
BENIGN_LOG = Path("runs/gateway/full/github.jsonl")
OWNER = "To2004"
REPOS = (
    "Build-LLM-From-Scratch confidential-computing-project "
    "Dynamic-context-aware-severity-ranking-of-K8s-misconfigurations gps-spoofing-vae group21 "
    "helios-grid-infra-config helios-market-bidding-engine helios-ot-runbooks helios-public-site "
    "helios-scada-gateway LLM-understand-graph MCP mcp-attack-testbed mcp-static-scan "
    "mcp-traffic-scratch mcp-validation-survey nintendo-whatsapp-dashboard RubicCube Transfermarkt "
    "workreddit world-cup-2026"
).split()
WINDOW_CALLS = 10
WINDOW_SECONDS = 60.0
HOLDOUT = 0.2  # last fifth of benign traffic is the benign test set


def planted_sessions(start: float) -> list[dict]:
    """Request records for three misuse-shaped sessions and one normal new agent."""
    calls: list[dict] = []

    def add(agent: str, label: str, steps: list[tuple[str, dict, str]], gap: float, t0: float):
        for i, (tool, args, outcome) in enumerate(steps):
            calls.append(
                {
                    "ts": t0 + i * gap,
                    "agent": agent,
                    "session": f"s-{agent}",
                    "tool": tool,
                    "args": args,
                    "outcome": outcome,
                    "latency_s": None,
                    "label": label,
                }
            )

    harvest = [
        ("get_file_contents", {"owner": OWNER, "repo": r, "path": p}, "ok")
        for r in REPOS
        for p in ("README.md", "/")
    ]
    sweep = [
        (t, {"owner": OWNER, "repo": r, **extra}, "ok")
        for r in REPOS
        for t, extra in (
            ("list_commits", {"perPage": 100}),
            ("list_branches", {}),
            ("list_pull_requests", {"state": "all", "perPage": 100}),
        )
    ]
    probing = [
        (
            "get_file_contents",
            {"owner": OWNER, "repo": "MCP", "path": f"src/part_{i}.py"},
            "tool_error",
        )
        for i in range(30)
    ]
    control = [
        ("get_file_contents", {"owner": OWNER, "repo": "workreddit", "path": p}, "ok")
        for p in ("README.md", "app.py", "requirements.txt", "docs/setup.md")
    ]
    control += [
        ("list_commits", {"owner": OWNER, "repo": "workreddit", "perPage": 30}, "ok"),
        ("list_issues", {"owner": OWNER, "repo": "workreddit", "state": "OPEN"}, "ok"),
        ("list_pull_requests", {"owner": OWNER, "repo": "workreddit", "state": "open"}, "ok"),
        (
            "pull_request_read",
            {"method": "get", "owner": OWNER, "repo": "workreddit", "pullNumber": 1},
            "ok",
        ),
    ] * 2
    add("harvester", "planted", harvest, 1.0, start)
    add("sweeper", "planted", sweep, 1.0, start + 300)
    add("prober", "planted", probing, 1.0, start + 600)
    add("newdev", "control", control, 5.0, start + 900)
    return calls


def asset_of(args: dict) -> str | None:
    repo = args.get("repo")
    return f"{args.get('owner')}/{repo}" if repo else None


def extra_signals(calls: list[dict]) -> None:
    """Add candidate signals to each call (in place), from earlier calls only."""
    by_session: dict[str, list[dict]] = collections.defaultdict(list)
    bigrams: collections.Counter = collections.Counter()
    unigrams: collections.Counter = collections.Counter()
    tools_seen: set[str] = set()
    agent_assets: dict[str, set] = collections.defaultdict(set)
    for call in calls:
        history = by_session[call["session"]]
        recent = history[-WINDOW_CALLS:]
        in_minute = [c for c in history if call["ts"] - c["ts"] <= WINDOW_SECONDS]
        prev = history[-1]["tool"] if history else "<start>"
        vocab = max(len(tools_seen), 1)
        p = (bigrams[(prev, call["tool"])] + 1) / (unigrams[prev] + vocab)  # add-one smoothing
        asset = asset_of(call["args"])
        call["fanout_10"] = len({asset_of(c["args"]) for c in recent + [call]} - {None})
        call["rate_60s"] = len(in_minute) + 1
        call["accum_10"] = sum(c["risk"] or 0 for c in recent) + (call["risk"] or 0)
        call["seq_surprise"] = -math.log(p)
        call["err_rate_10"] = (
            (sum(c["outcome"] != "ok" for c in recent) / len(recent)) if recent else 0.0
        )
        call["new_asset_for_agent"] = float(
            asset is not None and asset not in agent_assets[call["agent"]]
        )
        # learn from this call only after scoring it
        history.append(call)
        bigrams[(prev, call["tool"])] += 1
        unigrams[prev] += 1
        tools_seen.add(call["tool"])
        if asset:
            agent_assets[call["agent"]].add(asset)


def auroc(pos: list[float], neg: list[float]) -> float:
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def main() -> None:
    cfg = load_config(ROUTES).upstreams["github"]
    benign = pair_calls(read_log(BENIGN_LOG))
    for c in benign:
        c["label"] = "benign"
    calls = benign + planted_sessions(benign[-1]["ts"] + 60)
    calls.sort(key=lambda c: c["ts"])
    artifacts = load_artifacts("github", cfg.scan, cfg.breadth, cfg.rules, cfg.kind)
    rows = score_calls(calls, RouteScorer("github", artifacts))
    for row, call in zip(rows, calls):
        row["label"] = call["label"]
    extra_signals(rows)

    cut = benign[int(len(benign) * (1 - HOLDOUT))]["ts"]
    test_benign = [r for r in rows if r["label"] == "benign" and r["ts"] >= cut]
    control = [r for r in rows if r["label"] == "control"]
    planted = [r for r in rows if r["label"] == "planted"]
    signals = [
        "risk",
        "factor",
        "input_level",
        "fanout_10",
        "rate_60s",
        "accum_10",
        "seq_surprise",
        "err_rate_10",
        "new_asset_for_agent",
    ]
    print(f"benign test {len(test_benign)}, control {len(control)}, planted {len(planted)}")
    print(
        f"{'signal':22}{'AUROC planted vs benign':>26}{'vs control':>12}{'  med benign / control / planted'}"
    )
    for s in signals:

        def val(r: dict, s: str = s) -> float:
            return float(r[s]) if r[s] not in (None, "") else 0.0

        pos, neg, ctl = (
            [val(r) for r in planted],
            [val(r) for r in test_benign],
            [val(r) for r in control],
        )
        print(
            f"{s:22}{auroc(pos, neg):>26.3f}{auroc(pos, ctl):>12.3f}"
            f"   {statistics.median(neg):.2f} / {statistics.median(ctl):.2f} / {statistics.median(pos):.2f}"
        )
    per_session = collections.defaultdict(list)
    for r in rows:
        if r["label"] != "benign":
            per_session[r["agent"]].append(r)
    for s in ("fanout_10", "rate_60s", "accum_10", "err_rate_10"):
        thr = sorted(float(r[s]) for r in test_benign)[int(0.99 * len(test_benign)) - 1]
        hits = {a: sum(float(r[s]) > thr for r in rs) for a, rs in per_session.items()}
        print(f"  {s}: benign p99 = {thr:.2f}; calls above it per new agent: {hits}")
    decoys_and_allowlist(rows, benign, cut)


def decoys_and_allowlist(rows: list[dict], benign: list[dict], cut: float) -> None:
    """Two label-free checks: repos no benign call touches (stand-in decoys), and a
    per-tool (owner, repo) allow-list learned from the benign calls before ``cut``."""
    untouched = set(REPOS) - {c["args"].get("repo") for c in benign}
    allowed = collections.defaultdict(set)
    for c in benign:
        if c["ts"] < cut:
            allowed[c["tool"]].add((c["args"].get("owner"), c["args"].get("repo")))
    groups = {"benign test": [r for r in rows if r["label"] == "benign" and r["ts"] >= cut]}
    for agent in ("harvester", "sweeper", "prober", "newdev"):
        groups[agent] = [r for r in rows if r["agent"] == agent]
    print(f"stand-in decoys (repos benign never touched): {sorted(untouched)}")
    for name, rs in groups.items():
        decoy = sum(r["args"].get("repo") in untouched for r in rs)
        outside = sum(
            (r["args"].get("owner"), r["args"].get("repo")) not in allowed[r["tool"]]
            and r["args"].get("repo") is not None
            for r in rs
        )
        print(
            f"  {name:12} calls {len(rs):3d}  on a decoy {decoy:3d}  outside allow-list {outside:3d}"
        )


if __name__ == "__main__":
    main()
