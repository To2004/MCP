"""Three concept families and the formula that joins them: which form works?

Families (high level: no tool inputs, no specific asset):
    Pace   how much / how fast, against the agent's own normal   (deviation)
    Path   what it does and in what order                         (access anomaly, at tool level)
    Place  from where and with what program                       (novelty of context)

Each dimension gives u = the agent's own rarity in bits (dims2/dims4/dims5). Three ways to turn u
into a signal, each compared with the organisation's last 30 days (all agents):
    cal   rank calibration: bits = -log2(share of the month at least this rare), counted from the
          top 0.5% (what eval2 does)
    exc   the e-form: excess over a per-dimension baseline, x = max(0, u - B_f), B_f = the month's
          99.5th percentile of u; multiplier exp(lambda * x)
    raw   CARMA's sigma(u) = min(1, log10(2^u) / 3), no organisation comparison
    share the methodology deck's form exp(lambda * (B - L)), clamped at 0: L = p = 2^-u is the
          support share, B = the share at the month's 99.5th percentile of u
A family's signal is its strongest dimension. Per agent-day each family keeps its strongest call.
Joining the families:
    max       the strongest family                 R = R_static * exp(lambda * max)
    sum       all families add up                  R = R_static * exp(lambda * sum)  (= product of e-terms)
    prod      (1 + s_pace)(1 + s_path)(1 + s_place), s scaled to 0..1
    max+      strongest family + a quarter of the second
Thresholds are label-free: the lowest score whose load fits (average per day, or a hard daily cap).
An episode counts when one of its agent-days alerts and it has a top-0.5% event on a used dimension.

Run:  python family_formula.py
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

D = Path("/home/ovadyat/MCP/runs/dynamic_dimensions/w2")
HERE = Path(__file__).parent
NAMES = ["github_M", "calendar_M", "slack_M", "github_S", "calendar_L", "slack_churn", "github_bots",
         "calendar_M2", "slack_M2"]
FILES = {"": ["next_tool_self", "calls_today"],
         "_h": ["tool_repeat_10m", "writes_today", "tool_new_org_rare", "asset_types_today",
                "network_range_new", "client_family_new"],
         "_p": ["session_duration", "networks_1h", "client_families_1h"]}
SETS = {
    "core4": {"pace": ["tool_repeat_10m"], "path": ["next_tool_self"],
              "place": ["network_range_new", "client_family_new"]},
    "core5": {"pace": ["tool_repeat_10m", "calls_today"], "path": ["next_tool_self"],
              "place": ["network_range_new", "client_family_new"]},
    "full11": {"pace": ["tool_repeat_10m", "calls_today", "writes_today", "session_duration"],
               "path": ["next_tool_self", "tool_new_org_rare", "asset_types_today"],
               "place": ["network_range_new", "client_family_new", "networks_1h", "client_families_1h"]},
}
CAL_DAYS, EVENT_RANK, MIN_RAW, BITS_FULL = 30, 0.995, 1e-6, 20.0
LOG10_2 = float(np.log10(2))
LOADS = (2.0, 4.0)


def load_org(name: str):
    """Raw per-call rarity for the needed dimensions, plus ids."""
    z = np.load(D / f"{name}.npz")
    cols, X = [], []
    for suf, want in FILES.items():
        f = z if suf == "" else np.load(D / f"{name}{suf}.npz")
        fc = list(f["cols"])
        cols += want
        X.append(np.stack([f["scores"][:, fc.index(c)] for c in want], 1))
    return z, cols, np.concatenate(X, 1).astype(np.float32)


def signals(X: np.ndarray, day: np.ndarray):
    """cal (rank bits), exc (excess over the month's 99.5th percentile), raw (sigma), share."""
    ndays = day.max() + 1
    day_idx = [np.flatnonzero(day == d) for d in range(ndays)]
    cal, exc, share = np.zeros_like(X), np.zeros_like(X), np.zeros_like(X)
    for d in range(1, ndays):
        past = np.concatenate(day_idx[max(0, d - CAL_DAYS):d])
        idx = day_idx[d]
        if not len(past) or not len(idx):
            continue
        P = np.sort(X[past], axis=0)
        k = min(len(P) - 1, int(EVENT_RANK * len(P)))
        for j in range(X.shape[1]):
            x = X[idx, j]
            live = x > MIN_RAW
            R = np.searchsorted(P[:, j], x, side="left") / len(P) * live
            cal[idx, j] = np.where(R >= EVENT_RANK, -np.log2(np.clip(1 - R, 1e-6, 1)), 0.0)
            exc[idx, j] = np.maximum(0.0, x - P[k, j]) * live
            share[idx, j] = np.maximum(0.0, 2.0 ** -P[k, j] - 2.0 ** -x) * live
    raw = np.minimum(1.0, X * LOG10_2 / 3.0)
    return {"cal": cal, "exc": exc, "raw": raw, "share": share}


def combine(F: dict[str, np.ndarray], how: str, scale: float) -> np.ndarray:
    S = np.stack(list(F.values()), 1)
    srt = -np.sort(-S, 1)
    if how == "max":
        return srt[:, 0]
    if how == "sum":
        return S.sum(1)
    if how == "prod":
        return np.prod(1 + np.minimum(1.0, S / scale), 1) - 1
    if how == "max+":
        return srt[:, 0] + 0.25 * srt[:, 1]
    raise ValueError(how)


def alerts(score, kday, n_eval_days, load, hard_cap):
    ev = (kday >= CAL_DAYS) & (score > 0)
    if hard_cap:
        out = np.zeros(len(score), bool)
        for d in np.unique(kday[ev]):
            idx = np.flatnonzero(ev & (kday == d))
            out[idx[np.argsort(-score[idx], kind="stable")[: int(load)]]] = True
        return out
    v = np.sort(score[ev])[::-1]
    k = int(load * n_eval_days)
    return ev if k >= len(v) else ev & (score > v[k])


def evaluate(name: str) -> dict:
    z, cols, X = load_org(name)
    day = (z["ts"].astype(float) // 86400).astype(int)
    agent, episode, strange = z["agent"].astype(str), z["episode"].astype(str), z["strange"].astype(str)
    sig = signals(X, day)
    keys = np.char.add(np.char.add(agent, "|"), day.astype(str))
    _, inv = np.unique(keys, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    n_eval_days = max(1, day.max() + 1 - CAL_DAYS)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    ep_ix = [np.array(v) for v in eps.values()]
    ep_kind = np.array([strange[ix[0]] for ix in ep_ix])
    ep_after = np.array([day[ix[0]] >= CAL_DAYS for ix in ep_ix])
    ep_cds = [np.unique(inv[ix]) for ix in ep_ix]
    event = sig["cal"] > 0

    def detection(alert, dims):
        jj = [cols.index(c) for c in dims]
        per: dict[str, list[bool]] = {}
        for ix, cds, kind, after in zip(ep_ix, ep_cds, ep_kind, ep_after):
            if after:
                per.setdefault(kind, []).append(bool(alert[cds].any() and event[ix][:, jj].any()))
        return {k: float(np.mean(v)) for k, v in per.items()}

    def family_day(kind, dims):
        s = sig[kind][:, [cols.index(c) for c in dims]].max(1)
        m = np.zeros(nk, np.float32)
        np.maximum.at(m, inv, s)
        return m

    out = {}
    for set_name, fams in SETS.items():
        dims = [c for v in fams.values() for c in v]
        for kind in ("cal", "exc", "raw", "share"):
            F = {f: family_day(kind, dims_f) for f, dims_f in fams.items()}
            scale = BITS_FULL if kind == "cal" else (float(np.percentile(np.concatenate(
                [v[v > 0] for v in F.values()]), 99)) if kind == "exc" else 1.0)
            if kind == "share" and set_name != "core4":
                continue
            for how in ("max", "sum", "prod", "max+"):
                score = combine(F, how, scale)
                for load in LOADS:
                    for cap in (False, True):
                        key = f"{set_name}|{kind}|{how}|{load:g}|{'cap' if cap else 'avg'}"
                        out[key] = detection(alerts(score, kday, n_eval_days, load, cap), dims)
            if kind == "cal":
                for f, dims_f in fams.items():
                    for load in LOADS:
                        out[f"{set_name}|cal|only:{f}|{load:g}|avg"] = detection(
                            alerts(F[f], kday, n_eval_days, load, False), dims_f)
    print(f"done {name}", flush=True)
    return out


def main():
    with Pool(3) as pool:
        res = dict(zip(NAMES, pool.map(evaluate, NAMES)))
    (HERE / "results" / "family_formula.json").write_text(json.dumps(res, indent=1))
    keys = list(res[NAMES[0]])
    table = {}
    for k in keys:
        kinds = {}
        for n in NAMES:
            for kind, v in res[n][k].items():
                kinds.setdefault(kind, []).append(v)
        table[k] = (float(np.mean([np.mean(v) for v in kinds.values()])),
                    {kind: float(np.mean(v)) for kind, v in kinds.items()})
    for k, (m, _) in table.items():
        print(f"{k:<44} {m:.0%}")


if __name__ == "__main__":
    main()
