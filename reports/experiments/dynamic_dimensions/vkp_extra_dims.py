"""Extra dimensions for the Velocity / Knowledge / Place baseline (rows aligned with the world CSV).

    tool_rarity_self  how rare this tool is in this agent's own last 90 days (percentage-based):
                      p = (own calls of the tool + 1) / (own tool calls + n_tools)
    tool_rarity_org   how rare this tool is in the whole organisation's last 30 days:
                      p = (org calls of the tool + 1) / (org tool calls + n_tools)
    pair_new          a (network /16, client family) pair this agent has not used in 90 days,
                      against its own novelty rate

Run:  python vkp_extra_dims.py w2/github_M.csv.gz ...   (writes runs/dynamic_dimensions/vkp/<name>.npz)
"""
from __future__ import annotations

import csv
import gzip
import math
import sys
from array import array
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

csv.field_size_limit(10**9)
OWN_DAYS, ORG_DAYS, DAY, MIN_HISTORY = 90, 30, 86400.0, 20
OUT = Path(__file__).resolve().parents[3] / "runs" / "dynamic_dimensions" / "vkp"
DIMS = ["tool_rarity_self", "tool_rarity_org", "pair_new"]


def bits(p: float) -> float:
    return -math.log2(min(1.0, max(p, 1e-12)))


class WindowCount:
    """Counts of keys over the last `days` days (day-bucketed)."""

    def __init__(self, days: int):
        self.days, self.counts, self.total, self.log = days, Counter(), 0, deque()

    def prune(self, day: int) -> None:
        while self.log and self.log[0][0] <= day - self.days:
            _, key = self.log.popleft()
            self.counts[key] -= 1
            self.total -= 1

    def add(self, day: int, key: str) -> None:
        self.counts[key] += 1
        self.total += 1
        self.log.append((day, key))


def run(path: Path) -> None:
    with gzip.open(path, "rt") as fh:
        n_tools = max(1, len({r["tool"] for r in csv.DictReader(fh) if r["tool"]}))
    own: dict[str, WindowCount] = defaultdict(lambda: WindowCount(OWN_DAYS))
    org = WindowCount(ORG_DAYS)
    seen: dict[str, dict[str, int]] = defaultdict(dict)
    rate: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    cols = [array("f") for _ in DIMS]
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            day = int(float(r["ts"]) // DAY)
            a = r["agent"]
            out = dict.fromkeys(DIMS, 0.0)
            pair = ".".join(r["address"].split(".")[:2]) + "|" + r["client"].split("/")[0].lower()
            last = seen[a].get(pair)
            new = last is None or last <= day - OWN_DAYS
            calls, news = rate[a]
            if new and calls >= MIN_HISTORY:
                out["pair_new"] = bits((news + 1) / (calls + 1))
            rate[a] = [calls + 1, news + int(new)]
            seen[a][pair] = day
            if r["method"] == "tools/call":
                tool, w = r["tool"], own[a]
                w.prune(day)
                org.prune(day)
                if w.total >= MIN_HISTORY:
                    out["tool_rarity_self"] = bits((w.counts[tool] + 1) / (w.total + n_tools))
                if org.total >= MIN_HISTORY:
                    out["tool_rarity_org"] = bits((org.counts[tool] + 1) / (org.total + n_tools))
                w.add(day, tool)
                org.add(day, tool)
            for c, d in zip(cols, DIMS):
                c.append(out[d])
    OUT.mkdir(parents=True, exist_ok=True)
    name = path.name.replace(".csv.gz", "")
    np.savez_compressed(OUT / f"{name}.npz", cols=np.array(DIMS),
                        scores=np.stack([np.frombuffer(c, dtype=np.float32) for c in cols], 1))
    print(f"{name}: {len(cols[0]):,} messages x {len(DIMS)} extra dimensions", flush=True)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(Path(p))
