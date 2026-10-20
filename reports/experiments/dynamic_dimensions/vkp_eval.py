"""Velocity / Knowledge / Place baseline: which dimensions matter, and which formula.

Every dimension is a surprise u (bits) of the agent's behaviour; its signal is the excess over the
organisation's normal level, x = max(0, u - B), B = the 99.5th percentile of u over the previous
30 days (as in FORMULA.md). Reported on the 9 simulated organisations, mean over 21 kinds:

1. each dimension alone (detection at <= 4 flagged agent-days a day, and its best kinds)
2. each dimension's unique value: the full set's detection without it (drop-one)
3. greedy order: the smallest set that reaches most of the full set's detection
4. formulas inside a family: average (the user's idea), e of the average, average of e, maximum,
   sum. Across families the e-terms multiply (exponents add). Per call, then the agent-day keeps
   its riskiest call. Thresholds are label-free (lowest score whose average load fits).
5. per kind: what the recommended set catches and what it cannot

Run:  python vkp_eval.py
"""
from __future__ import annotations

import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RUNS = HERE.resolve().parents[2] / "runs" / "dynamic_dimensions"
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
SOURCES = {  # file pattern -> dimensions taken from it (all files are row-aligned with the world CSV)
    "self/{n}.npz": ["next_tool", "tool_repeat_10m", "calls_today", "tool_new", "network_new",
                     "client_new", "networks_1h", "clients_1h"],
    "w2/{n}.npz": ["rate_1h", "which_per_day", "address_new"],
    "w2/{n}_h.npz": ["asset_types_today", "tool_new_org_rare"],
    "w2/{n}_p.npz": ["session_duration"],
    "vkp/{n}.npz": ["tool_rarity_self", "tool_rarity_org", "pair_new"],
}
FAMILIES = {
    "velocity": ["tool_repeat_10m", "calls_today", "rate_1h", "session_duration"],
    "knowledge": ["next_tool", "tool_new", "tool_rarity_self", "tool_new_org_rare", "tool_rarity_org",
                  "asset_types_today"],
    "place": ["network_new", "address_new", "client_new", "pair_new", "networks_1h", "clients_1h"],
}
NEEDS_INPUTS = ["which_per_day"]             # distinct assets per day: needs the asset in the call
ALL = [d for ds in FAMILIES.values() for d in ds]
CAL_DAYS, Q, MIN_RAW = 30, 0.995, 1e-6
LAMBDA = math.log(2) / 10
LOADS = (2.0, 4.0)


def load(name: str):
    z = np.load(RUNS / "self" / f"{name}.npz")
    cols, X = [], []
    for pattern, dims in SOURCES.items():
        f = np.load(RUNS / pattern.format(n=name))
        fc = [str(c) for c in f["cols"]]
        X.append(np.stack([f["scores"][:, fc.index(d)] for d in dims], 1).astype(np.float32))
        cols += dims
    return z, cols, np.concatenate(X, 1)


def excess(X: np.ndarray, day: np.ndarray) -> np.ndarray:
    """x = max(0, u - B), B = the previous 30 days' 99.5th percentile (all agents)."""
    out = np.zeros_like(X)
    day_idx = [np.flatnonzero(day == d) for d in range(day.max() + 1)]
    for d in range(1, len(day_idx)):
        past = np.concatenate(day_idx[max(0, d - CAL_DAYS):d])
        idx = day_idx[d]
        if not len(past) or not len(idx):
            continue
        B = np.quantile(X[past], Q, axis=0)
        out[idx] = np.maximum(0.0, X[idx] - B) * (X[idx] > MIN_RAW)
    return out


def alerts(score, kday, n_eval_days, load_):
    ev = (kday >= CAL_DAYS) & (score > 0)
    v = np.sort(score[ev])[::-1]
    k = int(load_ * n_eval_days)
    return ev if k >= len(v) else ev & (score > v[k])


def evaluate(name: str) -> dict:
    z, cols, X = load(name)
    day = (z["ts"] // 86400).astype(int)
    x = excess(X, day)
    _, ident = np.unique(z["agent"], return_inverse=True)
    _, inv = np.unique(ident.astype(np.int64) * 100000 + day, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    strange, episode = z["strange"].astype(str), z["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (x[ix] > 0).any(0))
          for ix in map(np.array, eps.values())]
    AD = np.zeros((nk, len(cols)), np.float32)              # agent-day maximum per dimension
    np.maximum.at(AD, inv, x)
    col = {c: i for i, c in enumerate(cols)}

    def detect(score, dims, load_):
        al = alerts(score, kday, n_eval, load_)
        jj = [col[d] for d in dims]
        per: dict[str, list[bool]] = {}
        for cds, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(al[cds].any() and has[jj].any()))
        return {k: float(np.mean(v)) for k, v in per.items()}

    def family_max_score(dims):
        s = np.zeros(nk, np.float32)
        for fdims in FAMILIES.values():
            jj = [col[d] for d in fdims if d in dims]
            if jj:
                s += AD[:, jj].max(1)
        return s

    def per_call_score(dims, how):
        total = np.zeros(len(day), np.float32)
        for fdims in FAMILIES.values():
            jj = [col[d] for d in fdims if d in dims]
            if not jj:
                continue
            v = x[:, jj]
            if how == "average":
                total += v.mean(1)
            elif how == "max":
                total += v.max(1)
            elif how == "sum":
                total += v.sum(1)
            elif how == "average_of_e":
                total += np.log(np.exp(LAMBDA * v).mean(1)) / LAMBDA
        s = np.zeros(nk, np.float32)
        np.maximum.at(s, inv, total)
        return s

    out = {"alone": {}, "dropone": {}, "subsets": {}, "formulas": {}}
    for d in ALL + NEEDS_INPUTS:
        out["alone"][d] = {f"{lo:g}": detect(AD[:, col[d]], [d], lo) for lo in LOADS}
    out["full"] = {f"{lo:g}": detect(family_max_score(ALL), ALL, lo) for lo in LOADS}
    for d in ALL:
        rest = [e for e in ALL if e != d]
        out["dropone"][d] = {f"{lo:g}": detect(family_max_score(rest), rest, lo) for lo in LOADS}
    np.savez_compressed(RUNS / "vkp" / f"{name}.ad.npz", AD=AD, kday=kday, n_eval=n_eval,
                        cols=np.array(cols))
    for how in ("average", "max", "sum", "average_of_e"):
        out["formulas"][how] = {f"{lo:g}": detect(per_call_score(ALL, how), ALL, lo) for lo in LOADS}
    out["episodes"] = [(cds.tolist(), kind, bool(after), has.tolist()) for cds, kind, after, has in ep]
    print(f"done {name}", flush=True)
    return out


def mean_kinds(per_org: list[dict]) -> float:
    kinds: dict[str, list[float]] = {}
    for r in per_org:
        for k, v in r.items():
            kinds.setdefault(k, []).append(v)
    return float(np.mean([np.mean(v) for v in kinds.values()]))


def main():
    with Pool(3) as pool:
        res = dict(zip(NAMES, pool.map(evaluate, NAMES)))
    summary = {}
    for lo in ("2", "4"):
        full = mean_kinds([res[n]["full"][lo] for n in NAMES])
        summary[f"full|{lo}"] = full
        print(f"\n== <= {lo} flagged agent-days a day: all {len(ALL)} dimensions (max inside family): "
              f"{full:.1%}")
        print(f"{'dimension':<20} {'alone':>6} {'without it':>11} {'unique':>7}")
        for d in ALL + NEEDS_INPUTS:
            alone = mean_kinds([res[n]["alone"][d][lo] for n in NAMES])
            line = f"{d:<20} {alone:6.1%}"
            if d in ALL:
                drop = mean_kinds([res[n]["dropone"][d][lo] for n in NAMES])
                line += f" {drop:11.1%} {full - drop:+7.1%}"
                summary[f"dropone|{d}|{lo}"] = drop
            summary[f"alone|{d}|{lo}"] = alone
            print(line)
        print("formulas (inside a family; families multiply as e-terms):")
        for how in ("average", "average_of_e", "max", "sum"):
            m = mean_kinds([res[n]["formulas"][how][lo] for n in NAMES])
            summary[f"formula|{how}|{lo}"] = m
            print(f"   {how:<14} {m:.1%}")
    (HERE / "results" / "vkp_eval.json").write_text(json.dumps(
        {"summary": summary, "per_org": {n: {k: v for k, v in r.items() if k != "episodes"}
                                         for n, r in res.items()}}, indent=1))
    for n in NAMES:
        (RUNS / "vkp" / f"{n}.episodes.json").write_text(json.dumps(res[n]["episodes"]))


if __name__ == "__main__":
    main()
