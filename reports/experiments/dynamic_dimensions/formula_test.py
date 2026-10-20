"""Test the simple formula proposed for reviewers and clients, on the 9 simulated organisations.

Five dimensions, each a rarity against the agent's own last 90 days (already computed as bits by
dims2.py / dims4.py), turned into a 0-1 signal:  s = min(1, log10(1/p) / 3),  p = 2^-bits.
Three groups, each counted once (strongest signal in the group):
    step     = s(next-tool rarity)
    volume   = max( s(same tool repeated in 10 min), s(calls today) )
    origin   = max( s(new network range), s(new client family) )
Per call:       L = (1 + step) x (1 + volume) x (1 + origin)            between x1 and x8
Per agent-day:  score = the day's highest L; each day the top N agent-days are flagged (N = 2 or 4).
An episode counts as caught only if one of its own calls is the top call of a flagged agent-day.

Run:  python formula_test.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
CAL_DAYS = 30
LOG10_2 = math.log10(2)


def signal(bits):
    return np.minimum(1.0, bits * LOG10_2 / 3.0)


def evaluate(name, loads=(2, 4)):
    z = np.load(D / f"{name}.npz")
    cols = list(z["cols"])
    S = z["scores"]
    h = np.load(D / f"{name}_h.npz")
    hc = list(h["cols"])
    H = h["scores"]
    step = signal(S[:, cols.index("next_tool_self")])
    volume = np.maximum(signal(H[:, hc.index("tool_repeat_10m")]), signal(S[:, cols.index("calls_today")]))
    origin = np.maximum(signal(H[:, hc.index("network_range_new")]), signal(H[:, hc.index("client_family_new")]))
    L = (1 + step) * (1 + volume) * (1 + origin)
    day = (z["ts"].astype(float) // 86400).astype(int)
    agent = z["agent"].astype(str)
    episode, strange = z["episode"].astype(str), z["strange"].astype(str)
    keys = np.char.add(np.char.add(agent, "|"), day.astype(str))
    _, inv = np.unique(keys, return_inverse=True)
    nk = inv.max() + 1
    order = np.lexsort((-L, inv))                     # per agent-day, highest L first
    first = np.ones(len(order), bool)
    first[1:] = inv[order][1:] != inv[order][:-1]
    top_call = np.full(nk, -1)
    top_call[inv[order][first]] = order[first]
    score = L[top_call]
    kday = day[top_call]
    out = {}
    for N in loads:
        flagged = np.zeros(nk, bool)
        for d in np.unique(kday[kday >= CAL_DAYS]):
            idx = np.flatnonzero(kday == d)
            idx = idx[score[idx] > 1.0]
            flagged[idx[np.argsort(-score[idx])[:N]]] = True
        caught_calls = set(top_call[flagged].tolist())
        per_kind = {}
        eps = {}
        for i in np.flatnonzero(strange != ""):
            eps.setdefault(episode[i], []).append(i)
        for e, ix in eps.items():
            if day[ix[0]] < CAL_DAYS:
                continue
            k = strange[ix[0]]
            per_kind.setdefault(k, []).append(any(i in caught_calls for i in ix))
        out[N] = {k: float(np.mean(v)) for k, v in per_kind.items()}
    return out


def main():
    res = {N: {} for N in (2, 4)}
    for n in NAMES:
        r = evaluate(n)
        for N in r:
            for k, v in r[N].items():
                res[N].setdefault(k, []).append(v)
        print(f"{n}: load<=2 {np.mean(list(r[2].values())):.0%}  load<=4 {np.mean(list(r[4].values())):.0%}", flush=True)
    for N in (2, 4):
        per = {k: np.mean(v) for k, v in res[N].items()}
        print(f"\nformula, top {N} agent-days per day: mean {np.mean(list(per.values())):.0%}")
        print("  " + ", ".join(f"{k} {v:.0%}" for k, v in sorted(per.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
