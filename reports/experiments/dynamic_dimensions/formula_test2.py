"""The simple formula, with the calibration step that made the tested version work.

Step 1  rarity for this agent (bits, from dims2/dims4), per dimension, per call.
Step 2  calibration: rank that value among ALL agents' values of the same dimension in the previous
        30 days; p = share at least as high. The signal counts only in the month's top 0.5%:
            s = min(1, log10(1/p) / 3)   if p <= 0.005,   else 0
Step 3  three groups, each counted once (strongest signal):
            step   = s(next-tool rarity)
            volume = max( s(same tool repeated in 10 min), s(calls today) )
            origin = max( s(new network range), s(new client family) )
Variant A (per call):       L = (1+step)(1+volume)(1+origin);  agent-day score = highest L that day
Variant B (per agent-day):  each group's strongest signal that day; score = product of (1 + group max)
Each day the top N agent-days (score > 1) are flagged, N = 2 or 4.

Run:  python formula_test2.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
CAL_DAYS, TOP_SHARE = 30, 0.005
GROUPS = {"step": ["next_tool_self"], "volume": ["tool_repeat_10m", "calls_today"],
          "origin": ["network_range_new", "client_family_new"]}


def calibrated_signal(x, day_idx, ndays):
    """p = share of the previous 30 days' values (all agents) at least this high -> 0..1 signal."""
    s = np.zeros(len(x), np.float32)
    for d in range(1, ndays):
        past = np.concatenate(day_idx[max(0, d - CAL_DAYS):d])
        idx = day_idx[d]
        if not len(past) or not len(idx):
            continue
        srt = np.sort(x[past])
        p = (len(srt) - np.searchsorted(srt, x[idx], side="left") + 1) / (len(srt) + 1)
        sig = np.minimum(1.0, np.log10(1 / p) / 3)
        s[idx] = np.where((p <= TOP_SHARE) & (x[idx] > 0), sig, 0.0)
    return s


def evaluate(name, loads=(2, 4)):
    z = np.load(D / f"{name}.npz")
    h = np.load(D / f"{name}_h.npz")
    cols, hc = list(z["cols"]), list(h["cols"])

    def col(c):
        return z["scores"][:, cols.index(c)] if c in cols else h["scores"][:, hc.index(c)]

    day = (z["ts"].astype(float) // 86400).astype(int)
    ndays = day.max() + 1
    day_idx = [np.flatnonzero(day == d) for d in range(ndays)]
    G = {g: np.max(np.stack([calibrated_signal(col(c), day_idx, ndays) for c in cs]), axis=0)
         for g, cs in GROUPS.items()}
    agent, episode, strange = z["agent"].astype(str), z["episode"].astype(str), z["strange"].astype(str)
    keys = np.char.add(np.char.add(agent, "|"), day.astype(str))
    _, inv = np.unique(keys, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    # variant A: per-call product, the day's highest call
    L = np.ones(len(day), np.float32)
    for g in G.values():
        L *= 1 + g
    scoreA = np.zeros(nk, np.float32)
    np.maximum.at(scoreA, inv, L)
    # variant B: per agent-day, each group's strongest signal, then the product
    scoreB = np.ones(nk, np.float32)
    for g in G.values():
        m = np.zeros(nk, np.float32)
        np.maximum.at(m, inv, g)
        scoreB *= 1 + m
    any_sig = np.zeros(len(day), bool)
    for g in G.values():
        any_sig |= g > 0
    eps = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    out = {}
    for label, score in (("A per call", scoreA), ("B per agent-day", scoreB)):
        for N in loads:
            flagged = np.zeros(nk, bool)
            for d in range(CAL_DAYS, ndays):
                idx = np.flatnonzero(kday == d)
                idx = idx[score[idx] > 1.0]
                flagged[idx[np.argsort(-score[idx])[:N]]] = True
            per = {}
            for e, ix in eps.items():
                ix = np.array(ix)
                if day[ix[0]] < CAL_DAYS:
                    continue
                hit = bool((flagged[inv[ix]] & any_sig[ix]).any())   # flagged because of this episode
                per.setdefault(strange[ix[0]], []).append(hit)
            out[(label, N)] = {k: float(np.mean(v)) for k, v in per.items()}
    return out


def main():
    agg = {}
    for n in NAMES:
        r = evaluate(n)
        for key, per in r.items():
            for k, v in per.items():
                agg.setdefault(key, {}).setdefault(k, []).append(v)
        print(n, " ".join(f"{k[0][0]}{k[1]}:{np.mean(list(v.values())):.0%}" for k, v in r.items()), flush=True)
    for key, per in agg.items():
        m = {k: np.mean(v) for k, v in per.items()}
        print(f"\n{key[0]}, top {key[1]} agent-days/day: mean {np.mean(list(m.values())):.0%}")
        print("  " + ", ".join(f"{k} {v:.0%}" for k, v in sorted(m.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
