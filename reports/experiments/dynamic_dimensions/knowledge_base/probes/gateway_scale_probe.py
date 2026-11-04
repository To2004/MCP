"""Scale probe for the v5 systems review: snapshot size, save time and per-call cost of the
shipped v4 engine, extrapolated to 10^4 identities and 10^5 assets.

Synthetic traffic only (not a development or test world): each caller has a few tools, a
Zipf-weighted set of ~40 assets out of a 10^5 universe, one network, one client, calls spread
over his working hours. A separate "crawler" caller touches many distinct assets to time the
Typical Footprint tail sum (memory.py:89-102), which is O(distinct values he knows).

    python3 -I reports/experiments/dynamic_dimensions/knowledge_base/probes/gateway_scale_probe.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "src"))

from mcp_security.behaviour.engine import (  # noqa: E402
    BehaviourConfig,
    BehaviourEngine,
    Message,
)

CALLERS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
CALLS_PER_DAY = 60
ASSET_UNIVERSE = 100_000
TOOLS = [f"tool_{i}" for i in range(40)]
DAY_S = 86_400.0
TARGET_IDENTITIES = 10_000
CRAWLER_ASSETS = (500, 5_000, 20_000)
SEED = 20261025


def synthetic_stream(rng: np.random.Generator) -> list[Message]:
    """A day-ordered stream of tool calls for CALLERS ordinary callers."""
    callers = []
    for c in range(CALLERS):
        assets = rng.choice(ASSET_UNIVERSE, size=40, replace=False)
        weights = 1.0 / np.arange(1, 41)
        tools = rng.choice(len(TOOLS), size=8, replace=False)
        start_h = rng.integers(6, 11)
        callers.append((f"u{c}", assets, weights / weights.sum(), tools, start_h))
    out: list[Message] = []
    for day in range(DAYS):
        rows = []
        for agent, assets, w, tools, start_h in callers:
            n = rng.poisson(CALLS_PER_DAY)
            ts = day * DAY_S + start_h * 3600 + np.sort(rng.uniform(0, 9 * 3600, n))
            for t in ts:
                a = assets[rng.choice(40, p=w)]
                tool = TOOLS[tools[rng.integers(len(tools))]]
                rows.append((t, agent, tool, f"org/repo{a}", int(rng.integers(200, 3000))))
        rows.sort()
        for t, agent, tool, asset, size in rows:
            out.append(Message(t, agent, "tools/call", f"{agent}-s{int(t // 3600)}", tool=tool,
                               asset=asset, sensitivity=2, operation="read",
                               address="10.1.2.3", client="cursor/1.0", size=size))
    return out


def crawler_cost(n_assets: int) -> float:
    """Median microseconds per warm call for a caller who already knows n_assets assets."""
    engine = BehaviourEngine(BehaviourConfig())
    t0 = 0.0
    per_day = -(-n_assets // 10)
    for i in range(n_assets):  # days 0..9, in arrival order: build history
        ts = t0 + (i // per_day) * DAY_S + 3600 * 9 + (i % per_day) * 0.5
        engine.observe(Message(ts, "crawler", "tools/call", None, tool="get_file",
                               asset=f"org/repo{i}", operation="read", size=500))
    times = []
    for j in range(400):
        ts = 12 * DAY_S + 3600 * 9 + j
        m = Message(ts, "crawler", "tools/call", None, tool="get_file",
                    asset=f"org/repo{j % n_assets}", operation="read", size=500)
        s = time.perf_counter()
        engine.observe(m)
        times.append(time.perf_counter() - s)
    return float(np.median(times) * 1e6)


def register_scan_ms(n_ids: int = 20_000) -> float:
    """Milliseconds for one AI-2-style lookup of a target value against every register id
    with ``name_coverage`` (synthetic ids), scaled to ASSET_UNIVERSE ids."""
    from mcp_security.binding.identifiers import canonical_id, name_coverage  # noqa: PLC0415

    rng = np.random.default_rng(SEED)
    kinds = ["api", "web", "db", "scada"]
    ids = [f"org{rng.integers(1000)}/service-{rng.integers(100000)}-{kinds[rng.integers(4)]}"
           for _ in range(n_ids)]
    value = canonical_id("Org7/Service-123-api")
    s = time.perf_counter()
    _ = [a for a in ids if name_coverage(value, a) >= 0.8]
    return (time.perf_counter() - s) * 1e3 * ASSET_UNIVERSE / n_ids


def main() -> None:
    rng = np.random.default_rng(SEED)
    stream = synthetic_stream(rng)
    engine = BehaviourEngine(BehaviourConfig())
    s = time.perf_counter()
    for m in stream:
        engine.observe(m)
    elapsed = time.perf_counter() - s
    s = time.perf_counter()
    blob = json.dumps(engine.snapshot())
    dump_s = time.perf_counter() - s
    per_caller = len(blob) / CALLERS
    scale = TARGET_IDENTITIES / CALLERS
    result = {
        "calls": len(stream),
        "us_per_call_mean": round(elapsed / len(stream) * 1e6, 1),
        "snapshot_bytes": len(blob),
        "snapshot_bytes_per_caller": round(per_caller),
        "snapshot_dump_s": round(dump_s, 3),
        "extrapolated_snapshot_MB_at_1e4": round(per_caller * TARGET_IDENTITIES / 1e6, 1),
        "extrapolated_dump_s_at_1e4": round(dump_s * scale, 2),
        "crawler_us_per_call": {n: round(crawler_cost(n), 1) for n in CRAWLER_ASSETS},
        "register_scan_ms_per_call_at_1e5_ids": round(register_scan_ms(), 1),
        "days": DAYS, "callers": CALLERS, "note": "synthetic traffic",
    }
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
