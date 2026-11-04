"""Design-phase probe (development world only): realised raise rate of the oversized-request line
learned as one agent-day budget, pooled over people and machines, with and without leaving out
the identity that holds most of the tail. No engine pass: flag raises only.

    PYTHONHASHSEED=0 uv run python reports/experiments/dynamic_dimensions/knowledge_base/probes/\\
        pooled_line_rates.py

Every number is from a burnt development world, not a test result.
"""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import normal_org_world as W  # noqa: E402
from red_flag_arms import ALPHA, LEARN_DAYS, cls_of, conformal, whole_kb  # noqa: E402

DAY = 86_400.0
WORLDS = ((7, 150, "main"), (11, 150, "main"), (7, 150, "heavy_files"), (7, 300, "main"),
          (7, 60, "main"))


def learn_line(days, leave_top_out: bool):
    """days: [(identity, {tool: size})] -> (k, reference, fallback by class)."""
    per_tool = defaultdict(list)
    for _, tools in days:
        for t, s in tools.items():
            per_tool[t].append(s)
    ref = {}
    for t, v in per_tool.items():
        if len(v) >= 100:
            v = sorted(v)
            ref[t] = v[min(len(v) - 1, math.ceil(0.99 * (len(v) + 1)) - 1)]
    by = defaultdict(list)
    for t, r in ref.items():
        by[cls_of(t)].append(r)
    cmed = {c: sorted(v)[len(v) // 2] for c, v in by.items()}
    top = max(ref.values())

    def reff(t):
        return ref.get(t) or cmed.get(cls_of(t)) or top

    ratios = [(a, max(s / reff(t) for t, s in tools.items())) for a, tools in days]
    k = conformal([r for _, r in ratios], 1 - ALPHA)
    if leave_top_out:  # the identity with most agent-days above k is left out, once
        tail = Counter(a for a, r in ratios if r > k)
        if tail:
            worst = tail.most_common(1)[0][0]
            k = conformal([r for a, r in ratios if a != worst], 1 - ALPHA)
    return k, (lambda t: whole_kb(k * reff(t)))


def main() -> None:
    for seed, n, prof in WORLDS:
        world, roles, _ = W.build_world(n, seed, W.PROFILES[prof])
        cut = (W.BASE_DAY + LEARN_DAYS) * DAY
        learn, evald = {}, {}
        for a, rows in world.items():
            for r in rows:
                d = int(r[0] // DAY) - W.BASE_DAY
                if r[0] < cut and r[1] == "tools/call":
                    x = learn.setdefault((a, d), {})
                    x[r[3]] = max(x.get(r[3], 0), r[9])
                if d >= 90:
                    rec = evald.setdefault((a, d), [False, {}, []])
                    rec[0] |= bool(r[11]) or bool(r[12])
                    if r[1] == "tools/call":
                        rec[1][r[3]] = max(rec[1].get(r[3], 0), r[9])
                        if r[12].startswith("big_paste"):
                            rec[2].append((r[3], r[9]))
        days = [(k[0], t) for k, t in learn.items()]
        out = []
        for lto in (False, True):
            k, line = learn_line(days, lto)
            ordinary = [v for v in evald.values() if not v[0]]
            raised = sum(any(s > line(t) for t, s in v[1].items()) for v in ordinary)
            pastes = [p for v in evald.values() for p in v[2]]
            caught = sum(s > line(t) for t, s in pastes)
            out.append(f"leave-top-out={lto}: k={k:.3f} raise={100 * raised / len(ordinary):.2f}% "
                       f"pastes={caught}/{len(pastes)} create_issue={line('create_issue')}")
        print(f"development world {seed}/{n}/{prof}: " + " | ".join(out), flush=True)


if __name__ == "__main__":
    main()
