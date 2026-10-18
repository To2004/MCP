"""Compare the three candidate plans at EQUAL analyst load (alerted caller-days per day).

  P1  guardrails + per-caller counters: policy rules, role tool check, own-history counters
  P2  per-call multi-dimension baselines, self shrunk toward peers, strongest dimension wins
  P3  two stages: P2's dimensions emit risk events; a caller-day alerts when its events add up
      across at least two dimensions, or one event is extreme, or a policy rule fired

Every per-dimension score is first turned into a rank against the same dimension's previous
30 days (label-free), so dimensions with different scales are comparable. Policy-rule hits
always alert, in every plan. Each plan's knob is swept; detection is read at the sweep point
whose load is closest to (and not above) each target load.

Run:  python plans.py --scores-dir ../../../runs/dynamic_dimensions --seeds 1 2 --month-seeds 11 12
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from evaluate import CAL_DAYS, KINDS, MIN_BITS, SHORT, Run, table

P1 = ["tool.peer", "rep.self", "rate.self", "reach.self", "size.self", "dormancy.self"]
P2 = ["rep.hier", "rate.hier", "reach.hier", "breadth.hier", "asset.hier", "tool.hier",
      "order_tr.hier", "time_cal.hier", "dormancy.hier", "size.hier"]
RULE = "order_rule.policy"
EVENT_RANK = 0.995
LOADS = (1.0, 2.0, 4.0)


def ranks(run: Run, cols) -> np.ndarray:
    """Rank of each call's score within the same column's previous CAL_DAYS days."""
    R = np.zeros((len(run.day), len(cols)), np.float32)
    for j, c in enumerate(cols):
        x = run.col(c)
        for d in range(1, run.ndays):
            past = np.concatenate(run.day_idx[max(0, d - CAL_DAYS):d])
            idx = run.day_idx[d]
            if len(past) and len(idx):
                srt = np.sort(x[past])
                R[idx, j] = np.searchsorted(srt, x[idx], side="left") / len(srt) * (x[idx] > MIN_BITS)
    return R


def caller_days(run: Run):
    keys = np.char.add(np.char.add(run.caller.astype(str), "|"), run.day.astype(str))
    uk, inv = np.unique(keys, return_inverse=True)
    kday = np.zeros(len(uk), int)
    kday[inv] = run.day
    return inv, kday


def evaluate_points(run, call_alert, cd_alert, inv, kday, credit, horizon):
    """Detection per kind and load for one operating point."""
    lo, hi = horizon
    m = (run.day >= lo) & (run.day < hi)
    nd = len(np.unique(run.day[m]))
    if cd_alert is None:
        load = len(np.unique(inv[call_alert & m])) / max(1, nd)
        hit = call_alert
    else:
        load = (cd_alert & (kday >= lo) & (kday < hi)).sum() / max(1, nd)
        hit = cd_alert[inv] & credit
    det = {}
    for k in KINDS:
        eps = [ix for kind, d0, ix in run.episodes.values() if kind == k and lo <= d0 < hi]
        det[k] = float(np.mean([hit[ix].any() for ix in eps])) if eps else np.nan
    return load, det


def sweep(run: Run, horizon):
    inv, kday = caller_days(run)
    rule = run.col(RULE) > 0
    out = {}
    for name, cols in (("P1 guardrails + counters", P1), ("P2 per-call baselines", P2)):
        R = ranks(run, cols).max(1)
        pts = []
        for t in (0.98, 0.99, 0.995, 0.998, 0.999, 0.9995, 0.9998, 0.99995):
            pts.append(evaluate_points(run, (R >= t) | rule, None, inv, kday, None, horizon))
        out[name] = pts
    R = ranks(run, P2)
    ev = R >= EVENT_RANK
    bits = np.where(ev, -np.log2(np.clip(1 - R, 1e-6, 1)), 0.0)
    nk = inv.max() + 1
    best = np.zeros((nk, bits.shape[1]))
    np.maximum.at(best, inv, bits)
    S, D, top = best.sum(1), (best > 0).sum(1), best.max(1)
    rule_cd = np.zeros(nk, bool)
    np.logical_or.at(rule_cd, inv, rule)
    credit = ev.any(1) | rule                       # the episode itself must have raised risk
    pts = []
    for T in (10, 14, 18, 24, 32, 45):
        for B in (12, 15, 99):
            cd = rule_cd | ((S >= T) & (D >= 2)) | (top >= B)
            pts.append(evaluate_points(run, None, cd, inv, kday, credit, horizon))
    out["P3 risk events -> caller-day"] = pts
    return out


def at_load(pts, target):
    ok = [p for p in pts if p[0] <= target]
    if not ok:
        return None
    return max(ok, key=lambda p: (np.nanmean(list(p[1].values())), p[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-dir", type=Path, required=True)
    ap.add_argument("--seeds", nargs="+", default=["1", "2"])
    ap.add_argument("--month-seeds", nargs="+", default=["11", "12"])
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results" / "plans.md")
    a = ap.parse_args()
    groups = {"month 1 (new deployment)": (a.month_seeds, (0, 30)),
              "months 2-2.5 (new deployment)": (a.month_seeds, (30, 75)),
              "year 1 (after month 1)": (a.seeds, (30, 365)),
              "year 2": (a.seeds, (365, 10**6))}
    cache = {}
    md = ["# The three plans at equal analyst load\n",
          "Load = alerted caller-days per day. Detection = share of strange-usage episodes caught, "
          "averaged over seeds. Policy-rule hits always alert.\n"]
    for gname, (seeds, hz) in groups.items():
        res = {}
        for sd in seeds:
            key = (sd, hz)
            if key not in cache:
                run = Run(a.scores_dir / f"scores_s{sd}_w90.npz")
                cache[key] = sweep(run, hz)
            for plan, pts in cache[key].items():
                for L in LOADS:
                    p = at_load(pts, L)
                    res.setdefault((plan, L), []).append(p)
        rows = []
        for (plan, L), ps in res.items():
            ps = [p for p in ps if p is not None]
            if not ps:
                rows.append([plan, f"<= {L:g}", "–", "unreachable"] + ["–"] * len(KINDS))
                continue
            det = {k: np.nanmean([p[1][k] for p in ps]) for k in KINDS}
            load = np.mean([p[0] for p in ps])
            rows.append([plan, f"<= {L:g}", f"{load:.1f}", f"{np.nanmean(list(det.values())):.0%}"]
                        + ["–" if np.isnan(det[k]) else f"{det[k]:.0%}" for k in KINDS])
        md += [f"## {gname}\n", table(rows, ["plan", "load target", "load", "mean detect"]
                                      + [SHORT[k] for k in KINDS]), ""]
        print(md[-2], flush=True)
    a.out.write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
