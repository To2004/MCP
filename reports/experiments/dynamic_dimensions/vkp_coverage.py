"""Coverage of the chosen Velocity / Knowledge / Place set, kind by kind, and candidate additions.

Base set (6): repeat in 10 min, calls today, session duration (Velocity); tool rarity for this
agent, asset types today (Knowledge); new network + client pair (Place). Average inside a family,
families added in the exponent (the user's formula). Candidates, each compared with the agent's
own past, all from the request log without reading tool inputs:
    hour_of_week        time of week this agent rarely works      (Velocity, timing)
    dormancy            silence before this call vs his usual gaps (Velocity, timing)
    list_to_call_delay  delay from listing tools to the first call (Velocity, timing)
    request_bytes       request size vs his usual for this tool    (Knowledge, how much he asks for)
    call_without_init   a call in a session that never initialised (Place, how he connects)
    call_without_list   a call in a session that never listed tools (Place, how he connects)

Run:  python vkp_coverage.py
"""
from __future__ import annotations

import json
from multiprocessing import Pool

import numpy as np

from vkp_eval import CAL_DAYS, HERE, NAMES, RUNS, alerts, excess

SOURCES = {
    "self/{n}.npz": ["tool_repeat_10m", "calls_today"],
    "w2/{n}.npz": ["hour_of_week", "dormancy", "request_bytes"],
    "w2/{n}_x.npz": ["list_to_call_delay"],
    "w2/{n}_h.npz": ["asset_types_today"],
    "w2/{n}_p.npz": ["session_duration", "call_without_init", "call_without_list"],
    "vkp/{n}.npz": ["tool_rarity_self", "pair_new"],
}
BASE = {"velocity": ["tool_repeat_10m", "calls_today", "session_duration"],
        "knowledge": ["tool_rarity_self", "asset_types_today"],
        "place": ["pair_new"]}
CANDIDATES = {"hour_of_week": "velocity", "dormancy": "velocity", "list_to_call_delay": "velocity",
              "request_bytes": "knowledge", "call_without_init": "place", "call_without_list": "place"}
COMBOS = {"8: + init + size": ["call_without_init", "request_bytes"],
          "9: + init + size + hour": ["call_without_init", "request_bytes", "hour_of_week"]}
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
    AD = np.zeros((nk, len(cols)), np.float32)
    np.maximum.at(AD, inv, x)
    col = {c: i for i, c in enumerate(cols)}
    strange, episode = z["strange"].astype(str), z["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (x[ix] > 0).any(0))
          for ix in map(np.array, eps.values())]
    benign_days = np.ones(nk, bool)
    benign_days[inv[strange != ""]] = False

    def detect(families: dict[str, list[str]], load_: float) -> dict[str, float]:
        score = np.zeros(nk, np.float32)
        for dims in families.values():
            if dims:
                score += AD[:, [col[d] for d in dims]].mean(1)
        al = alerts(score, kday, n_eval, load_)
        jj = [col[d] for ds in families.values() for d in ds]
        per: dict[str, list[bool]] = {}
        for cds, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(al[cds].any() and has[jj].any()))
        return {k: float(np.mean(v)) for k, v in per.items()}

    def alone(dim: str, load_: float) -> dict[str, float]:
        al = alerts(AD[:, col[dim]], kday, n_eval, load_)
        per: dict[str, list[bool]] = {}
        for cds, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(al[cds].any() and has[col[dim]]))
        return {k: float(np.mean(v)) for k, v in per.items()}

    out = {"base": {f"{lo:g}": detect(BASE, lo) for lo in LOADS}, "with": {}, "alone": {},
           "benign_day_rate": {}}
    for d in [c for ds in BASE.values() for c in ds] + list(CANDIDATES):
        out["alone"][d] = alone(d, 4.0)
        out["benign_day_rate"][d] = float((AD[benign_days & (kday >= CAL_DAYS), col[d]] > 0).mean())
    for cand, fam in CANDIDATES.items():
        fams = {f: list(ds) + ([cand] if f == fam else []) for f, ds in BASE.items()}
        out["with"][cand] = {f"{lo:g}": detect(fams, lo) for lo in LOADS}
    out["combos"] = {}
    for label, adds in COMBOS.items():
        fams = {f: list(ds) + [c for c in adds if CANDIDATES[c] == f] for f, ds in BASE.items()}
        out["combos"][label] = {f"{lo:g}": detect(fams, lo) for lo in LOADS}
    print(f"done {name}", flush=True)
    return out


def mean_kinds(rows: list[dict]) -> dict[str, float]:
    kinds: dict[str, list[float]] = {}
    for r in rows:
        for k, v in r.items():
            kinds.setdefault(k, []).append(v)
    return {k: float(np.mean(v)) for k, v in kinds.items()}


def main():
    with Pool(3) as pool:
        res = dict(zip(NAMES, pool.map(evaluate, NAMES)))
    (HERE / "results" / "vkp_coverage.json").write_text(json.dumps(res, indent=1))
    base = {lo: mean_kinds([res[n]["base"][lo] for n in NAMES]) for lo in ("2", "4")}
    alone = {d: mean_kinds([res[n]["alone"][d] for n in NAMES]) for d in res[NAMES[0]]["alone"]}
    base_dims = [c for ds in BASE.values() for c in ds]
    print(f"\nBase 6 (average formula): <= 2: {np.mean(list(base['2'].values())):.1%}   "
          f"<= 4: {np.mean(list(base['4'].values())):.1%}")
    print("\nPer kind at <= 4: base set, and the base dimension that catches it best alone")
    for k in sorted(base["4"], key=lambda k: -base["4"][k]):
        best = max(base_dims, key=lambda d: alone[d].get(k, 0))
        print(f"  {k:<24} {base['4'][k]:4.0%}   best alone: {best} {alone[best][k]:.0%}")
    print("\nCandidates: base + one (overall <= 2 / <= 4), benign agent-days touched, kinds it lifts")
    for cand in CANDIDATES:
        w = {lo: mean_kinds([res[n]["with"][cand][lo] for n in NAMES]) for lo in ("2", "4")}
        rate = np.mean([res[n]["benign_day_rate"][cand] for n in NAMES])
        lifts = {k: w["4"][k] - base["4"][k] for k in base["4"]}
        big = ", ".join(f"{k} {base['4'][k]:.0%}->{w['4'][k]:.0%}"
                        for k, v in sorted(lifts.items(), key=lambda kv: -kv[1]) if abs(v) >= 0.03)
        print(f"  +{cand:<20} {np.mean(list(w['2'].values())):.1%} / {np.mean(list(w['4'].values())):.1%}"
              f"   benign days {rate:.1%}   {big}")
    for label in COMBOS:
        w = {lo: mean_kinds([res[n]["combos"][label][lo] for n in NAMES]) for lo in ("2", "4")}
        print(f"\n{label}: {np.mean(list(w['2'].values())):.1%} / {np.mean(list(w['4'].values())):.1%}")
        print("  per kind <= 4: " + ", ".join(f"{k} {v:.0%}" for k, v in
                                            sorted(w["4"].items(), key=lambda kv: -kv[1])))
    print("\nBenign agent-days touched by each base dimension: " + ", ".join(
        f"{d} {np.mean([res[n]['benign_day_rate'][d] for n in NAMES]):.1%}" for d in base_dims))


if __name__ == "__main__":
    main()
