"""Latency and isolation check for :mod:`gate_runtime`.

Two questions, both answered by measurement rather than argument:

1. **Isolation** — do two tenants on the *same* MCP kind actually stay separate
   now that history is keyed by ``Connection.scope`` instead of kind alone?
2. **Latency** — what does the per-call cost distribution look like (not just
   the mean) for one org juggling several MCP servers at once, and what does
   the async snapshot hand-off cost the caller?

    python3 scripts/dynamic_design/bench_gate_runtime.py <scratch_dir>
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
import time
from pathlib import Path

from gate_runtime import Connection, GateScorer, SnapshotStore, load_gate_specs


def load(path: Path) -> list[tuple[str, dict]]:
    rows = []
    for row in csv.DictReader(path.open()):
        try:
            call_args = json.loads(row.get("args") or "{}")
        except json.JSONDecodeError:
            call_args = {}
        if not isinstance(call_args, dict):
            call_args = {}
        rows.append((row["tool"], call_args))
    return rows


def interleave(*streams: list) -> list:
    out, cursors = [], [0] * len(streams)
    while any(c < len(s) for c, s in zip(cursors, streams)):
        for i, s in enumerate(streams):
            if cursors[i] < len(s):
                out.append(s[cursors[i]])
                cursors[i] += 1
    return out


def percentiles(samples_us: list[float]) -> dict[str, float]:
    ordered = sorted(samples_us)
    n = len(ordered)

    def at(p: float) -> float:
        return ordered[min(n - 1, int(n * p))]

    return {"p50": at(0.50), "p90": at(0.90), "p99": at(0.99),
            "p999": at(0.999), "max": ordered[-1], "mean": statistics.fmean(ordered)}


def check_isolation(specs: dict, scratch: Path) -> None:
    print("=== isolation: two tenants, same kind (github) ===")
    org_a = load(scratch / "github_100k.csv")[:20000]
    org_b_path = scratch / "github_org_b_100k.csv"
    if not org_b_path.exists():
        print(f"  (skipped -- {org_b_path.name} not found; see setup step)")
        return
    org_b = load(org_b_path)[:20000]

    scorer = GateScorer(specs)
    conn_a = Connection(org_id="acme", server_id="github-prod", kind="github")
    conn_b = Connection(org_id="globex", server_id="github-prod", kind="github")

    for tool, args in org_a:
        scorer.score(conn_a, tool, args)
    for tool, args in org_b:
        scorer.score(conn_b, tool, args)

    keys_a = {k for k in scorer.history if k[0] == conn_a.scope}
    keys_b = {k for k in scorer.history if k[0] == conn_b.scope}
    overlap_scope = keys_a & keys_b
    # Same (tool, arg) pairs are expected on both -- same kind. What must NOT
    # happen is the two ever sharing one dict entry (a values list).
    shared_object = any(scorer.history[ka] is scorer.history[kb]
                         for ka in keys_a for kb in keys_b if ka[1:] == kb[1:])
    print(f"  org acme: {len(keys_a)} history keys, org globex: {len(keys_b)} history keys")
    print(f"  keys ever literally shared between tenants: {len(overlap_scope)} (must be 0)")
    print(f"  any underlying list object shared: {shared_object} (must be False)")

    common = {k[1:] for k in keys_a} & {k[1:] for k in keys_b}
    populated = [(tool, arg) for tool, arg in common
                 if scorer.history[(conn_a.scope, tool, arg)]
                 and scorer.history[(conn_b.scope, tool, arg)]]
    if populated:
        tool, arg = populated[0]
        a_vals = scorer.history[(conn_a.scope, tool, arg)]
        b_vals = scorer.history[(conn_b.scope, tool, arg)]
        print(f"  sample arg '{tool}.{arg}': acme n={len(a_vals)} min={min(a_vals):g} "
              f"max={max(a_vals):g}  |  globex n={len(b_vals)} min={min(b_vals):g} "
              f"max={max(b_vals):g}")
    print()


def check_latency(specs: dict, scratch: Path, store_dir: Path) -> None:
    print("=== latency: one org, three MCP servers interleaved ===")
    github = load(scratch / "github_100k.csv")
    slack = load(scratch / "slack_100k.csv")
    calendar = load(scratch / "calendar_100k.csv")
    combined = interleave(
        [("github", t, a) for t, a in github],
        [("slack", t, a) for t, a in slack],
        [("calendar", t, a) for t, a in calendar],
    )

    conns = {
        "github": Connection(org_id="acme", server_id="github-prod", kind="github"),
        "slack": Connection(org_id="acme", server_id="slack-prod", kind="slack"),
        "calendar": Connection(org_id="acme", server_id="cal-prod", kind="calendar"),
    }
    scorer = GateScorer(specs)

    samples_us: list[float] = []
    t_start = time.perf_counter()
    for kind, tool, args in combined:
        t0 = time.perf_counter()
        scorer.score(conns[kind], tool, args)
        samples_us.append((time.perf_counter() - t0) * 1e6)
    elapsed = time.perf_counter() - t_start

    stats = percentiles(samples_us)
    print(f"  {len(combined)} calls, {elapsed:.2f}s wall, "
          f"{len(combined) / elapsed:,.0f} calls/sec")
    print("  per-call latency (us): " + ", ".join(f"{k}={v:.1f}" for k, v in stats.items()))

    print("\n=== snapshot hand-off cost (should never show up above) ===")
    store = SnapshotStore(store_dir)
    enqueue_us = []
    for kind, conn in conns.items():
        cost = store.enqueue(conn, scorer.snapshot(conn))
        enqueue_us.append(cost * 1e6)
    print(f"  caller-side enqueue cost per connection (us): "
          f"{', '.join(f'{v:.1f}' for v in enqueue_us)}")
    t0 = time.perf_counter()
    store.wait_idle()
    print(f"  background drain (serialize + disk write, off hot path): "
          f"{(time.perf_counter() - t0) * 1000:.1f} ms for {store._writes} connections")

    # rehydrate check: a fresh scorer, same org, restored from disk instead of cold
    print("\n=== rehydrate: fresh replica picks up warm state instead of cold-starting ===")
    fresh = GateScorer(specs)
    for kind, conn in conns.items():
        path = store_dir / f"{conn.org_id}__{conn.server_id}.json"
        payload = json.loads(path.read_text())
        t0 = time.perf_counter()
        fresh.rehydrate(conn, payload)
        rehydrate_ms = (time.perf_counter() - t0) * 1000
        ready = sum(1 for k, v in fresh.history.items()
                    if k[0] == conn.scope and len(v) >= 20)
        print(f"  {kind}: rehydrated in {rehydrate_ms:.2f} ms, "
              f"{ready} argument histories immediately judgeable (no cold start)")


def main() -> int:
    scratch = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    store_dir = scratch / "gate_snapshot_store"
    specs = load_gate_specs()
    check_isolation(specs, scratch)
    check_latency(specs, scratch, store_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
