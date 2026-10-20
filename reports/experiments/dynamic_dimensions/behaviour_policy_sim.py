"""Simulate the production behaviour layer (src/mcp_security/behaviour) on the 9 simulated
organisations, with the default policy and with a policy learned from each organisation's
first 30 days (behaviour/policy.py: burst and request limits at the agent-days' 99.5th
percentile, required earlier steps at 99.5% of sessions).

Ties are not broken: an agent-day scores its highest multiplier, and every agent-day tied at
the review list's cut-off is flagged (so the real load can exceed the budget; it is reported).

Run:  uv run python reports/experiments/dynamic_dimensions/behaviour_policy_sim.py
      (writes results/behaviour_policy_sim.json)
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message
from mcp_security.behaviour.policy import config_to_json, derive_policy

HERE = Path(__file__).parent
NAMES = ["github_M", "github_S", "github_bots", "calendar_M", "calendar_M2", "calendar_L", "slack_M",
         "slack_M2", "slack_churn"]
START = datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp()  # world2's day 0, a Monday
DAY = 86_400.0
CAL_DAYS = 30
LOADS = (2.0, 4.0)
WRITE_OPS = {"write", "remove", "delete"}


def messages(name: str) -> tuple[list[Message], dict]:
    csv.field_size_limit(10**9)
    out, meta = [], {"strange": [], "legit": [], "episode": [], "bot": []}
    with gzip.open(HERE / "w2" / f"{name}.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            asset = r["which"] if r["which"] not in ("", "null") else None
            out.append(Message(
                ts=START + float(r["ts"]), agent=r["agent"], method=r["method"],
                session=r["session"] or None, tool=r["tool"] or None, asset=asset,
                sensitivity=int(r["sens"] or 0) or None,
                operation="write" if r["op"] in WRITE_OPS else ("read" if r["op"] else None),
                address=r["address"] or None, client=r["client"] or None, size=int(r["bytes"] or 0)))
            for k in ("strange", "legit", "episode"):
                meta[k].append(r[k])
            meta["bot"].append("bot" in r["role"])
    return out, {k: np.array(v) for k, v in meta.items()}


def score(stream: list[Message], config: BehaviourConfig) -> tuple[np.ndarray, list[str | None]]:
    engine = BehaviourEngine(config)
    M, top = np.empty(len(stream), np.float32), []
    for i, m in enumerate(stream):
        v = engine.observe(m)
        M[i] = v.multiplier
        top.append(v.strongest if v.multiplier > 1 else None)
    return M, top


def measure(M: np.ndarray, top: list, stream: list[Message], meta: dict) -> dict:
    day = ((np.array([m.ts for m in stream]) - START) // DAY).astype(int)
    _, ident = np.unique(np.array([m.agent for m in stream]), return_inverse=True)
    _, inv = np.unique(ident.astype(np.int64) * 100_000 + day, return_inverse=True)
    nk = inv.max() + 1
    dmax = np.zeros(nk, np.float32)
    np.maximum.at(dmax, inv, M)
    kday, kbot = np.zeros(nk, int), np.zeros(nk, bool)
    kday[inv], kbot[inv] = day, meta["bot"]
    strange, legit, episode = meta["strange"], meta["legit"], meta["episode"]
    k_strange = np.zeros(nk, bool)
    np.logical_or.at(k_strange, inv, strange != "")
    k_legit = np.full(nk, "", dtype=object)
    ben = (legit != "") & (strange == "")
    k_legit[inv[ben]] = legit[ben]
    after = kday >= CAL_DAYS
    ordinary = after & ~k_strange & (k_legit == "")
    cause = {}
    for i in np.argsort(-M, kind="stable"):
        cause.setdefault(inv[i], top[i])
    hot = ordinary & (dmax >= 3)
    causes = Counter(cause[k] for k in np.flatnonzero(hot))
    out = {"range": [float(M.min()), float(M.max())],
           "ordinary_days_M>=3": float((dmax[ordinary] >= 3).mean()),
           "ordinary_days_M>=2": float((dmax[ordinary] >= 2).mean()),
           "ordinary_days_M>=3_bots": float((dmax[ordinary & kbot] >= 3).mean()) if (ordinary & kbot).any() else None,
           "ordinary_days_M>=3_people": float((dmax[ordinary & ~kbot] >= 3).mean()) if (ordinary & ~kbot).any() else None,
           "ordinary_causes": {str(k): v / max(1, int(hot.sum())) for k, v in causes.most_common()},
           "legit_days_M>=3": {t: float((dmax[after & (k_legit == t)] >= 3).mean())
                               for t in set(k_legit[after]) if t}}
    eps: dict[str, list[int]] = defaultdict(list)
    for i in np.flatnonzero(strange != ""):
        eps[episode[i]].append(i)
    kinds: dict[str, list[float]] = defaultdict(list)
    ep_days = []
    for ix in map(np.array, eps.values()):
        if day[ix[0]] >= CAL_DAYS:
            kinds[strange[ix[0]]].append(float(M[ix].max()))
            ep_days.append((strange[ix[0]], np.unique(inv[ix]), bool((M[ix] > 1).any())))
    out["episode_M>=3"] = {k: float(np.mean(np.array(v) >= 3)) for k, v in kinds.items()}
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    for load in LOADS:
        scores = np.where(after & (dmax > 1), dmax, 0.0)
        ranked = np.sort(scores[scores > 0])[::-1]
        k = int(load * n_eval)
        cut = ranked[k - 1] if k <= len(ranked) else (ranked[-1] if len(ranked) else np.inf)
        flagged = scores >= cut  # ties at the cut-off are all flagged
        det: dict[str, list[bool]] = defaultdict(list)
        for kind, cds, has in ep_days:
            det[kind].append(bool(flagged[cds].any() and has))
        out[f"list_{load:g}"] = {"detection": {kk: float(np.mean(v)) for kk, v in det.items()},
                                 "real_load": float(flagged.sum() / n_eval), "cut": float(cut)}
    return out


def run(name: str) -> dict:
    stream, meta = messages(name)
    learned = derive_policy(m for m in stream if m.ts < START + CAL_DAYS * DAY)
    result = {"policy": config_to_json(learned)}
    for label, config in (("default", BehaviourConfig()), ("learned", learned)):
        M, top = score(stream, config)
        result[label] = measure(M, top, stream, meta)
    print(f"done {name}", flush=True)
    return result


def main():
    with Pool(3) as pool:
        res = dict(zip(NAMES, pool.map(run, NAMES)))
    (HERE / "results" / "behaviour_policy_sim.json").write_text(json.dumps(res, indent=1))
    print("\nLEARNED POLICY (from the first 30 days)")
    for n, r in res.items():
        p = r["policy"]
        ex = list(p["requires_before"].items())[:3]
        print(f"  {n:<12} burst > {p['burst_per_minute']}/min, request > {p['request_limit_bytes']} B, "
              f"{len(p['requires_before'])} tools with a required step, e.g. {ex}")
    for label in ("default", "learned"):
        print(f"\n{label.upper()} POLICY")
        for n, r in res.items():
            o = r[label]
            d = {lo: np.mean(list(o[f"list_{lo:g}"]["detection"].values())) for lo in LOADS}
            print(f"  {n:<12} M {o['range'][0]:.2f}-{o['range'][1]:.2f} | ordinary days >=3 "
                  f"{o['ordinary_days_M>=3']:.1%} (bots {o['ordinary_days_M>=3_bots']:.1%}, people "
                  f"{o['ordinary_days_M>=3_people']:.1%}) >=2 {o['ordinary_days_M>=2']:.1%} | list <=2: "
                  f"{d[2.0]:.0%} (real load {o['list_2']['real_load']:.1f}), <=4: {d[4.0]:.0%} "
                  f"(real {o['list_4']['real_load']:.1f})")
            print("      causes:", {k: f"{v:.0%}" for k, v in list(o["ordinary_causes"].items())[:5]})
        kinds = defaultdict(list)
        for r in res.values():
            for k, v in r[label]["episode_M>=3"].items():
                kinds[k].append(v)
        print("  episodes M>=3:", ", ".join(f"{k} {np.mean(v):.0%}" for k, v in
                                           sorted(kinds.items(), key=lambda kv: -np.mean(kv[1]))))
        leg = defaultdict(list)
        for r in res.values():
            for k, v in r[label]["legit_days_M>=3"].items():
                leg[k].append(v)
        print("  legit days M>=3:", {k: f"{np.mean(v):.0%}" for k, v in sorted(leg.items())})


if __name__ == "__main__":
    main()
