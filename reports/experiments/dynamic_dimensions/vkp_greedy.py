"""Smallest Velocity / Knowledge / Place set: greedy forward selection over the user's dimensions.

Reads the agent-day maxima and episodes saved by vkp_eval.py. A set is scored as the sum over
families of each family's strongest dimension that agent-day; detection is read at <= 2 and <= 4
flagged agent-days a day with label-free thresholds, mean over 21 kinds and 9 organisations.

Run:  python vkp_greedy.py      (after vkp_eval.py)
"""
from __future__ import annotations

import json

import numpy as np

from vkp_eval import ALL, FAMILIES, HERE, LOADS, NAMES, RUNS, alerts


def load(name: str):
    z = np.load(RUNS / "vkp" / f"{name}.ad.npz")
    eps = json.loads((RUNS / "vkp" / f"{name}.episodes.json").read_text())
    cols = [str(c) for c in z["cols"]]
    ep = [(np.array(cds), kind, after, np.array(has)) for cds, kind, after, has in eps]
    return {"AD": z["AD"], "kday": z["kday"], "n_eval": int(z["n_eval"]), "cols": cols, "ep": ep}


def detection(org: dict, dims: list[str], load_: float) -> dict[str, float]:
    col = {c: i for i, c in enumerate(org["cols"])}
    score = np.zeros(len(org["kday"]), np.float32)
    for fdims in FAMILIES.values():
        jj = [col[d] for d in fdims if d in dims]
        if jj:
            score += org["AD"][:, jj].max(1)
    al = alerts(score, org["kday"], org["n_eval"], load_)
    jj = [col[d] for d in dims]
    per: dict[str, list[bool]] = {}
    for cds, kind, after, has in org["ep"]:
        if after:
            per.setdefault(kind, []).append(bool(al[cds].any() and has[jj].any()))
    return {k: float(np.mean(v)) for k, v in per.items()}


def mean_over(orgs: list[dict], dims: list[str], load_: float, per_kind: bool = False):
    kinds: dict[str, list[float]] = {}
    for o in orgs:
        for k, v in detection(o, dims, load_).items():
            kinds.setdefault(k, []).append(v)
    m = {k: float(np.mean(v)) for k, v in kinds.items()}
    return m if per_kind else float(np.mean(list(m.values())))


def main():
    orgs = [load(n) for n in NAMES]
    out = {}
    for load_ in LOADS:
        chosen, trail, pool = [], [], list(ALL)
        while pool:
            best = max(pool, key=lambda d: mean_over(orgs, chosen + [d], load_))
            chosen.append(best)
            pool.remove(best)
            trail.append((best, mean_over(orgs, chosen, load_)))
        out[f"{load_:g}"] = trail
        print(f"\n<= {load_:g} flagged agent-days a day")
        prev = 0.0
        for i, (d, m) in enumerate(trail, 1):
            fam = next(f for f, ds in FAMILIES.items() if d in ds)
            print(f"  {i:>2}. +{d:<19} ({fam:<9}) {m:5.1%}  (+{m - prev:4.1%})")
            prev = m
        for k in (3, 4, 5):
            kinds = mean_over(orgs, [d for d, _ in trail[:k]], load_, per_kind=True)
            out[f"{load_:g}|kinds|{k}"] = kinds
    (HERE / "results" / "vkp_greedy.json").write_text(json.dumps(out, indent=1))
    kinds = out["4|kinds|4"]
    print("\nper kind, best 4 at <= 4 a day: " + ", ".join(
        f"{k} {v:.0%}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
