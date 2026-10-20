"""How many self-only dimensions are needed, with no user id and no comparison with other users?

Reads the score files of self_only_dims.py. Each dimension's surprise is turned into a risk event
in one of two ways:
    self    rank against the SAME identity's own last 30 days (no other user is involved)
    pooled  rank against all identities' last 30 days (the organisation sets the scale)
An event is the top 0.5% (rank >= 0.995); its weight is -log2(1 - rank) bits; each agent-day keeps
each dimension's strongest event. Detection uses eval2's rule (at least 2 dimensions add up past T,
or one passes B), read at <= 2 or <= 4 flagged identity-days per day, so the numbers line up with
the earlier dimension searches. Greedy forward selection adds the dimension that helps most.

Identities compared on github_M, slack_M and calendar_M:
    per_agent  one agent token per person (the plain worlds)
    shared10   one token shared by 10 people (the gateway cannot tell them apart)
    session    no stable identity: every session is a new caller

Run:  python self_only_eval.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from eval2 import Scenario

HERE = Path(__file__).parent
D = HERE.resolve().parents[2] / "runs" / "dynamic_dimensions" / "self"
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
ID_ORGS = ["github_M", "slack_M", "calendar_M"]
CAL_DAYS, EVENT_RANK, MIN_PAST, MIN_RAW = 30, 0.995, 200, 1e-6
LOADS = (2.0, 4.0)


def pooled_ranks(S: np.ndarray, day: np.ndarray) -> np.ndarray:
    """Rank of each value among all identities' values in the previous 30 days."""
    R = np.zeros(S.shape, np.float32)
    day_idx = [np.flatnonzero(day == d) for d in range(day.max() + 1)]
    for d in range(1, len(day_idx)):
        past = np.concatenate(day_idx[max(0, d - CAL_DAYS):d])
        idx = day_idx[d]
        if len(past) < MIN_PAST or not len(idx):
            continue
        P = np.sort(S[past], axis=0)
        for j in range(S.shape[1]):
            x = S[idx, j]
            R[idx, j] = np.searchsorted(P[:, j], x, side="left") / len(past) * (x > MIN_RAW)
    return R


def self_ranks(S: np.ndarray, day: np.ndarray, ident: np.ndarray) -> np.ndarray:
    """Rank of each value among the SAME identity's own values in the previous 30 days."""
    R = np.zeros(S.shape, np.float32)
    order = np.lexsort((day, ident))
    ids, d_sorted = ident[order], day[order]
    bounds = np.flatnonzero(np.r_[True, ids[1:] != ids[:-1], True])
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        rows, days = order[lo:hi], d_sorted[lo:hi]
        if hi - lo <= MIN_PAST:
            continue
        for d in np.unique(days):
            a = np.searchsorted(days, d - CAL_DAYS, "left")
            b = np.searchsorted(days, d, "left")
            if b - a < MIN_PAST:
                continue
            today = rows[b:np.searchsorted(days, d, "right")]
            P = np.sort(S[rows[a:b]], axis=0)
            for j in range(S.shape[1]):
                x = S[today, j]
                R[today, j] = np.searchsorted(P[:, j], x, side="left") / (b - a) * (x > MIN_RAW)
    return R


def prepare(name: str, mode: str) -> Scenario:
    """A Scenario object (compact form) that eval2's detect() can read."""
    cache = D / f"{name}.{mode}.compact.npz"
    if cache.exists():
        return Scenario.load(cache)
    z = np.load(D / f"{name}.npz")
    S, cols = z["scores"], [str(c) for c in z["cols"]]
    day = (z["ts"] // 86400).astype(int)
    _, ident = np.unique(z["agent"], return_inverse=True)
    strange, episode = z["strange"].astype(str), z["episode"].astype(str)
    R = pooled_ranks(S, day) if mode == "pooled" else self_ranks(S, day, ident)
    ev = R >= EVENT_RANK
    bits = np.where(ev, -np.log2(np.clip(1 - R, 1e-6, 1)), 0.0).astype(np.float32)
    keys = ident.astype(np.int64) * 100000 + day
    _, inv = np.unique(keys, return_inverse=True)
    nk = inv.max() + 1
    s = Scenario.__new__(Scenario)
    s.name, s.cols = f"{name}.{mode}", cols
    s.kday = np.zeros(nk, int)
    s.kday[inv] = day
    s.cd = np.zeros((nk, len(cols)), np.float32)
    np.maximum.at(s.cd, inv, bits)
    eps = defaultdict(list)
    for i in np.flatnonzero(strange != ""):
        eps[episode[i]].append(i)
    names = list(eps)
    s.ep_kind = np.array([strange[eps[e][0]] for e in names])
    s.ep_int = np.zeros(len(names), int)
    s.ep_day = np.array([day[eps[e][0]] for e in names])
    s.ep_ev = np.array([ev[eps[e]].any(0) for e in names])
    s.ep_single = s.ep_ev.copy()
    cds, ptr = [], [0]
    for e in names:
        cds.extend(np.unique(inv[eps[e]]))
        ptr.append(len(cds))
    s.ep_cds, s.ep_ptr = np.array(cds), np.array(ptr)
    s.after = s.ep_day >= CAL_DAYS
    s.n_eval_days = max(1, day.max() + 1 - CAL_DAYS)
    np.savez_compressed(cache, cols=np.array(cols), n_eval_days=s.n_eval_days, single="{}",
                        **{k: getattr(s, k) for k in ("cd", "kday", "ep_kind", "ep_int", "ep_day",
                                                       "ep_ev", "ep_single", "ep_cds", "ep_ptr",
                                                       "after")})
    print(f"prepared {name}.{mode}", flush=True)
    return s


def detection(scens: list[Scenario], cols: list[str], load: float) -> float:
    return float(np.mean([s.detect([s.cols.index(c) for c in cols], load)[0] for s in scens]))


def greedy(scens: list[Scenario], load: float) -> list[tuple[str, float]]:
    chosen, trail = [], []
    pool = list(scens[0].cols)
    while pool:
        best = max(pool, key=lambda c: detection(scens, chosen + [c], load))
        chosen.append(best)
        pool.remove(best)
        trail.append((best, detection(scens, chosen, load)))
    return trail


def main():
    jobs = [(n, m) for n in NAMES for m in ("self", "pooled")]
    jobs += [(f"{n}__{v}", m) for n in ID_ORGS for v in ("shared10", "session") for m in ("self", "pooled")]
    with Pool(4) as pool:
        pool.starmap(prepare, jobs)
    out = {}
    for mode in ("self", "pooled"):
        scens = [prepare(n, mode) for n in NAMES]
        for load in LOADS:
            trail = greedy(scens, load)
            out[f"9orgs|{mode}|{load:g}"] = trail
            print(f"\n9 organisations, calibration={mode}, <= {load:g}/day")
            prev = 0.0
            for i, (c, m) in enumerate(trail, 1):
                print(f"  {i}. +{c:<16} {m:5.1%}  (+{m - prev:4.1%})")
                prev = m
    for mode in ("self", "pooled"):
        for load in LOADS:
            row = {}
            for ident in ("per_agent", "shared10", "session"):
                scens = [prepare(n if ident == "per_agent" else f"{n}__{ident}", mode) for n in ID_ORGS]
                trail = greedy(scens, load)
                row[ident] = trail
            out[f"identity|{mode}|{load:g}"] = row
            print(f"\nidentity (github_M, slack_M, calendar_M), calibration={mode}, <= {load:g}/day")
            for ident, trail in row.items():
                print(f"  {ident:<10} " + "  ".join(f"{i}:{m:.0%}" for i, (_, m) in enumerate(trail, 1))
                      + "   order: " + ", ".join(c for c, _ in trail[:4]))
    (HERE / "results" / "self_only.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
