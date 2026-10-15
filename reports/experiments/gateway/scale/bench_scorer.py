"""Cost of the framework per call, with no network: what each part costs, how cost and
memory grow with the number of callers and with history, and how fast state can be saved,
restored or rebuilt by replay.

Workload: the 100k synthetic GitHub org corpus, translated to the remote server's tool
names, scored with the real remote-GitHub artifacts (scan cells, breadth spec, input rules).
Each experiment runs in a fresh process so memory figures are its own.

    uv run python reports/experiments/gateway/scale/bench_scorer.py all > results_scorer.jsonl
"""

from __future__ import annotations

import csv
import json
import random
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.github_remote import translate_call
from mcp_security.gateway.proxy import load_config

CORPUS = Path("reports/experiments/real_benign/github_helios_org_100k.csv")
ROUTES = Path("src/mcp_security/gateway/routes.example.json")
CALLER_COUNTS = (1, 10, 100, 1_000, 10_000, 100_000)
CALLS_FOR_CALLERS = 300_000  # enough that the larger caller counts see repeat visits
ZIPF_S = 1.1  # a few heavy callers, a long tail of light ones
SEED = 7
ORIGINAL_SNAPSHOT_MAX_CALLERS = 1_000  # 10k took 349 s; 100k would take hours


def calls(n: int) -> list[tuple[str, dict]]:
    """``n`` calls from the corpus, translated to remote names, repeated if n > 100k."""
    with CORPUS.open(encoding="utf-8") as handle:
        rows = [translate_call(r["tool"], json.loads(r["args"])) for r in csv.DictReader(handle)]
    return [rows[i % len(rows)] for i in range(n)]


def scorer(history: str = "route") -> RouteScorer:
    up = load_config(ROUTES).upstreams["github"]
    artifacts = load_artifacts("github", up.scan, up.breadth, up.rules, up.kind)
    return RouteScorer("github", artifacts, history=history)


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def pct(values: list[float], q: float) -> float:
    return sorted(values)[min(len(values) - 1, int(q * len(values)))]


def components(n: int = 100_000) -> dict:
    """Microseconds per call for each part, one shared history."""
    work, s, t0 = calls(n), scorer(), time.time()
    conn = s.connection(None)
    parts = {
        "static_cell_uncached": lambda tool, args, ts: s._matrix.score(tool, args),
        "static_cell_cached": lambda tool, args, ts: s._cell(tool, args),
        "dynamic_BxL": lambda tool, args, ts: s._gate.score(conn, tool, args),
        "input_rules": lambda tool, args, ts: s._input_level(tool, args, ts),
    }
    out = {}
    for name, fn in parts.items():
        started = time.perf_counter()
        for i, (tool, args) in enumerate(work):
            fn(tool, args, t0 + i)
        out[name] = (time.perf_counter() - started) / n * 1e6
    fresh, per_call = scorer(), []
    for i, (tool, args) in enumerate(work):
        a = time.perf_counter()
        fresh.score(tool, args, t0 + i)
        per_call.append((time.perf_counter() - a) * 1e6)
    out |= {
        "full_mean": statistics.mean(per_call),
        "full_p50": pct(per_call, 0.5),
        "full_p99": pct(per_call, 0.99),
        "full_max": max(per_call),
    }
    return {"experiment": "components", "calls": n, "us_per_call": out, "rss_mb": rss_mb()}


def callers(count: int) -> dict:
    """Per-caller history with ``count`` callers sharing 300k calls on a Zipf curve."""
    rng = random.Random(SEED)
    weights = [1 / (rank**ZIPF_S) for rank in range(1, count + 1)]
    owners = rng.choices(range(count), weights=weights, k=CALLS_FOR_CALLERS)
    work, s, t0 = calls(CALLS_FOR_CALLERS), scorer("caller"), time.time()
    base = rss_mb()
    lat = []
    for i, ((tool, args), owner) in enumerate(zip(work, owners)):
        a = time.perf_counter()
        s.score(tool, args, t0 + i, caller=f"agent-{owner}")
        lat.append((time.perf_counter() - a) * 1e6)
    seen = len(set(owners))
    gate = s._gate
    original_s = None
    if count <= ORIGINAL_SNAPSHOT_MAX_CALLERS:  # GateScorer.snapshot is N x keys
        started = time.perf_counter()
        {c: gate.snapshot(conn) for c, conn in s._connections.items()}
        original_s = time.perf_counter() - started
    started = time.perf_counter()
    snaps = s.snapshot_all()
    snap_s = time.perf_counter() - started
    blob = json.dumps(snaps)
    restored = scorer("caller")
    started = time.perf_counter()
    restored.restore_all(json.loads(blob))
    rehydrate_s = time.perf_counter() - started
    return {
        "experiment": "callers",
        "callers": count,
        "callers_seen": seen,
        "calls": CALLS_FOR_CALLERS,
        "us_p50": pct(lat, 0.5),
        "us_p99": pct(lat, 0.99),
        "us_mean": statistics.mean(lat),
        "rss_mb_growth": rss_mb() - base,
        "history_keys": len(gate.history),
        "snapshot_original_s": original_s,
        "snapshot_s": snap_s,
        "snapshot_mb": len(blob) / 1e6,
        "rehydrate_s": rehydrate_s,
    }


def saturation(n: int = 1_000_000, window: int = 50_000) -> dict:
    """One caller, a million calls: does cost grow as each history fills to its cap?"""
    work, s, t0 = calls(n), scorer(), time.time()
    marks, started = [], time.perf_counter()
    for i, (tool, args) in enumerate(work):
        s.score(tool, args, t0 + i)
        if (i + 1) % window == 0:
            now = time.perf_counter()
            marks.append(round((now - started) / window * 1e6, 1))
            started = now
    return {
        "experiment": "saturation",
        "calls": n,
        "us_per_call_by_50k": marks,
        "rss_mb": rss_mb(),
        "history_keys": len(s._gate.history),
    }


EXPERIMENTS = {"components": components, "saturation": saturation}


def main() -> None:
    which = sys.argv[1]
    if which == "all":
        for name in ("components", *[f"callers:{c}" for c in CALLER_COUNTS], "saturation"):
            out = subprocess.run([sys.executable, __file__, name], capture_output=True, text=True)
            print(
                out.stdout.strip() or json.dumps({"experiment": name, "error": out.stderr[-500:]}),
                flush=True,
            )
        return
    if which.startswith("callers:"):
        print(json.dumps(callers(int(which.split(":")[1]))))
    else:
        print(json.dumps(EXPERIMENTS[which]()))


if __name__ == "__main__":
    main()
