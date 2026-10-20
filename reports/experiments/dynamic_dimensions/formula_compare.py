"""Fair comparison of ways to combine the same five high-level dimensions into one agent-day score.

All methods read the same prepared scenarios (eval2.Scenario compact files): per agent-day, each
dimension's strongest calibrated event in bits (rank >= 0.995 among the previous 30 days of all
agents; bits = -log2(1 - rank), so 7.6 bits at the top 0.5% and up to ~20 bits).

Methods
  validated   eval2's rule: (sum >= T and >= 2 dims) or one dim >= B; (T, B) is the best of a grid
              chosen WITH labels (optimistic: this is how the earlier 43% / 56% numbers were read)
  validated_cv the same rule, (T, B) chosen on the other eight organisations (no peeking)
  product     three groups counted once, s = bits / 20, score = (1+step)(1+volume)(1+origin)
  group_sum   three groups counted once, score = sum of the group bits
  max_only    score = the single strongest dimension
For the one-number scores the threshold is set without labels: the lowest one whose load is within
budget. Load is read two ways: on average over the evaluation days (as before), and as a hard cap
of N agent-days on every day.

Run:  python formula_compare.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from eval2 import CAL_DAYS, GRID, Scenario

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
GROUPS = {"step": ["next_tool_self"], "volume": ["tool_repeat_10m", "calls_today"],
          "origin": ["network_range_new", "client_family_new"]}
DIMS = [c for cs in GROUPS.values() for c in cs]
BITS_FULL = 20.0
LOADS = (2.0, 4.0)


def group_bits(s: Scenario) -> dict[str, np.ndarray]:
    """Per agent-day, each group's strongest event in bits (0 if none)."""
    return {g: s.cd[:, [s.cols.index(c) for c in cs]].max(1) for g, cs in GROUPS.items()}


def detection(s: Scenario, alert: np.ndarray, credit: np.ndarray) -> float:
    """Mean over kinds of the share of episodes whose agent-days include an alert."""
    hit = np.logical_or.reduceat(alert[s.ep_cds], s.ep_ptr[:-1]) & credit & s.after
    kinds = np.unique(s.ep_kind[s.after])
    return float(np.mean([hit[(s.ep_kind == k) & s.after].mean() for k in kinds]))


def alerts_average(s: Scenario, score: np.ndarray, load: float) -> np.ndarray:
    """Lowest threshold whose mean alerts per evaluation day stay within load."""
    ev = (s.kday >= CAL_DAYS) & (score > 0)
    v = np.sort(score[ev])[::-1]
    k = int(load * s.n_eval_days)
    if k >= len(v):
        return ev
    return ev & (score > v[k])


def alerts_daily_cap(s: Scenario, score: np.ndarray, load: float) -> np.ndarray:
    """The top N agent-days of every day (score > 0)."""
    out = np.zeros(len(score), bool)
    for d in np.unique(s.kday[s.kday >= CAL_DAYS]):
        idx = np.flatnonzero((s.kday == d) & (score > 0))
        out[idx[np.argsort(-score[idx], kind="stable")[: int(load)]]] = True
    return out


def rule_alerts(s: Scenario, T: float, B: float) -> np.ndarray:
    C = s.cd[:, [s.cols.index(c) for c in DIMS]]
    return ((C.sum(1) >= T) & ((C > 0).sum(1) >= 2)) | (C.max(1) >= B)


def rule_load(s: Scenario, alert: np.ndarray) -> float:
    return float((alert & (s.kday >= CAL_DAYS)).sum() / s.n_eval_days)


def best_rule(scens: list[Scenario], credits: list[np.ndarray], load: float):
    """(T, B) with the best mean detection over scens, each within load on average."""
    best = None
    for T, B in GRID:
        ms = []
        for s, cr in zip(scens, credits):
            a = rule_alerts(s, T, B)
            ms.append(detection(s, a, cr) if rule_load(s, a) <= load else 0.0)
        if best is None or np.mean(ms) > best[0]:
            best = (float(np.mean(ms)), T, B)
    return best


def main():
    scens = [Scenario.load(D / f"{n}.compact.npz") for n in NAMES]
    credits = [s.ep_ev[:, [s.cols.index(c) for c in DIMS]].any(1) for s in scens]
    rows = {}
    for load in LOADS:
        r = {}
        r["validated (grid best, labels)"] = np.mean(
            [best_rule([s], [cr], load)[0] for s, cr in zip(scens, credits)])
        cv = []
        for i, (s, cr) in enumerate(zip(scens, credits)):
            _, T, B = best_rule([x for j, x in enumerate(scens) if j != i],
                                [x for j, x in enumerate(credits) if j != i], load)
            a = rule_alerts(s, T, B)
            cv.append(detection(s, a, cr) if rule_load(s, a) <= load else detection(
                s, a & alerts_average(s, s.cd[:, [s.cols.index(c) for c in DIMS]].sum(1), load), cr))
        r["validated (T,B from other orgs)"] = np.mean(cv)
        for name, make in (("product (1+s)(1+s)(1+s)", lambda G: np.prod([1 + g / BITS_FULL for g in G.values()], 0) - 1),
                           ("group sum of bits", lambda G: sum(G.values())),
                           ("strongest dimension only", lambda G: np.max(np.stack(list(G.values())), 0))):
            avg, cap = [], []
            for s, cr in zip(scens, credits):
                score = make(group_bits(s))
                avg.append(detection(s, alerts_average(s, score, load), cr))
                cap.append(detection(s, alerts_daily_cap(s, score, load), cr))
            r[name + " | average load"] = np.mean(avg)
            r[name + " | hard daily cap"] = np.mean(cap)
        rows[load] = r
        print(f"\nload <= {load:g} agent-days per day")
        for k, v in r.items():
            print(f"  {k:<48} {v:.0%}", flush=True)


if __name__ == "__main__":
    main()
