"""Evaluate dimension scores at a fixed, label-free alert budget.

Thresholds never look at labels: for day d, a score column alerts above the (1 - budget)
quantile of that column over the previous 30 days of ALL calls (strange ones included, as
they would be in production), and never below MIN_BITS. Day 0 has no history and no alerts.

Reported per horizon (first month, year 1 after month 1, year 2):
  - episode detection per kind of strange usage (an episode counts if any of its calls alerts)
  - benign alert rate overall and per kind of legitimate change (new hire, role change, ...)
  - alerts per day (calls) and alerted sessions per day (what an analyst sees)

Run:  python evaluate.py --scores-dir ../../../runs/dynamic_dimensions --seed 1
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np

DAY = 86400.0
MIN_BITS = 1.0
CAL_DAYS = 30
CAP_FACTOR = 2.0
HORIZONS = {"month 1": (0, 30), "year 1": (30, 365), "year 2": (365, 10**6)}
KINDS = ["loop", "page_walk", "over_fetch", "fan_out", "off_role_tool", "workflow_skip",
         "off_hours", "burst", "dormant_wake", "sensitivity_escalation", "slow_creep", "repeated_habit"]
LEGIT = ["new_hire", "role_change", "team_transfer", "new_repo", "back_from_vacation",
         "oncall_incident", "legit_drift"]
SHORT = {"loop": "loop", "page_walk": "pgwalk", "over_fetch": "overfetch", "fan_out": "fanout",
         "off_role_tool": "offrole", "workflow_skip": "wfskip", "off_hours": "offhrs", "burst": "burst",
         "dormant_wake": "dormant", "sensitivity_escalation": "sensesc", "slow_creep": "creep",
         "repeated_habit": "habit"}
# the reference each dimension uses in the "default" configuration
DEFAULT = ["rep.hier", "rate.hier", "reach.hier", "breadth.hier", "asset.hier", "sensjump.self",
           "tool.hier", "order_rule.policy", "order_tr.hier", "time_cal.hier", "dormancy.hier", "size.hier"]


class Run:
    def __init__(self, path: Path):
        z = np.load(path)
        self.S = z["scores"]
        self.cols = list(z["cols"])
        self.day = (z["ts"].astype(float) // DAY).astype(int)
        self.strange, self.legit, self.episode = z["strange"], z["legit"], z["episode"]
        self.session, self.caller = z["session"], z["caller"]
        self.tool, self.sens = z["tool"], z["sens"].astype(int)
        self.ndays = self.day.max() + 1
        self.day_idx = [np.flatnonzero(self.day == d) for d in range(self.ndays)]
        self.benign = self.strange == ""
        # episodes: id -> (kind, first day, call indices)
        ep = defaultdict(list)
        for i in np.flatnonzero(~self.benign):
            ep[self.episode[i]].append(i)
        self.episodes = {e: (self.strange[ix[0]], self.day[ix[0]], np.array(ix)) for e, ix in ep.items()}

    def col(self, name):
        return self.S[:, self.cols.index(name)]

    def alerts(self, x: np.ndarray, budget: float) -> np.ndarray:
        """Label-free daily threshold from the previous CAL_DAYS days of the same score,
        plus a hard daily cap (CAP_FACTOR x budget x recent calls/day): an analyst queue has
        a fixed capacity, so on a flooded day only the highest-scoring calls are kept."""
        a = np.zeros(len(x), bool)
        for d in range(1, self.ndays):
            lo = max(0, d - CAL_DAYS)
            past = np.concatenate(self.day_idx[lo:d])
            idx = self.day_idx[d]
            if len(past) == 0 or len(idx) == 0:
                continue
            thr = max(MIN_BITS, float(np.quantile(x[past], 1 - budget)))
            hit = idx[x[idx] > thr]
            cap = max(1, int(np.ceil(CAP_FACTOR * budget * len(past) / (d - lo))))
            if len(hit) > cap:
                hit = hit[np.argsort(-x[hit], kind="stable")[:cap]]
            a[hit] = True
        return a

    def report(self, a: np.ndarray, horizon=None):
        lo, hi = HORIZONS[horizon] if horizon else (0, 10**6)
        m = (self.day >= lo) & (self.day < hi)
        out = {"benign_rate": a[m & self.benign].mean() if (m & self.benign).any() else np.nan}
        nd = len(np.unique(self.day[m]))
        out["alerts_per_day"] = a[m].sum() / max(1, nd)
        out["sessions_per_day"] = len(np.unique(self.session[m & a])) / max(1, nd)
        cd = np.char.add(self.caller[m & a].astype(str), self.day[m & a].astype(str))
        out["caller_days_per_day"] = len(np.unique(cd)) / max(1, nd)
        for tag in LEGIT:
            mm = m & self.benign & (self.legit == tag)
            out[tag] = a[mm].mean() if mm.any() else np.nan
        mm = m & self.benign & (self.legit == "")
        out["ordinary"] = a[mm].mean() if mm.any() else np.nan
        per = defaultdict(list)
        for kind, d0, ix in self.episodes.values():
            if lo <= d0 < hi:
                per[kind].append(bool(a[ix].any()))
        for k in KINDS:
            out[k] = float(np.mean(per[k])) if per[k] else np.nan
            out[k + "_n"] = len(per[k])
        return out


def fmt(v, pct=True):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:.0%}" if pct else f"{v:.1f}"


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def e1_dimension_by_kind(run: Run, budget: float):
    rows = []
    for c in DEFAULT:
        r = run.report(run.alerts(run.col(c), budget))
        rows.append([c] + [fmt(r[k]) for k in KINDS] + [f"{r['benign_rate']:.2%}", fmt(r["alerts_per_day"], False)])
    return table(rows, ["dimension"] + [SHORT[k] for k in KINDS] + ["benign", "alerts/day"])


def e2_references(run: Run, budget: float):
    dims = ["rep", "rate", "reach", "breadth", "asset", "tool", "order_tr", "time", "dormancy", "size"]
    rows = []
    for d in dims:
        for ref in ("self", "peer", "org", "hier", "anchor"):
            name = f"{d}.{ref}"
            if name not in run.cols:
                continue
            r = run.report(run.alerts(run.col(name), budget))
            hit = np.nanmean([r[k] for k in KINDS])
            rows.append([name, fmt(hit), f"{r['ordinary']:.2%}"] + [fmt(r[t]) for t in LEGIT])
    return table(rows, ["dimension.reference", "mean detect", "ordinary FP"] + LEGIT)


def combos(run: Run, budget: float, cols=DEFAULT):
    """Three ways to merge dimensions into one alert stream at the same total budget."""
    X = np.stack([run.col(c) for c in cols], 1)
    a_or = np.zeros(len(X), bool)
    for j in range(X.shape[1]):
        a_or |= run.alerts(X[:, j], budget / len(cols))
    a_sum = run.alerts(X.sum(1), budget)
    # per-dimension rank within its own recent distribution, then the strongest dimension
    R = np.zeros_like(X)
    for j in range(X.shape[1]):
        x = X[:, j]
        for d in range(1, run.ndays):
            past = np.concatenate(run.day_idx[max(0, d - CAL_DAYS):d])
            idx = run.day_idx[d]
            if len(past) and len(idx):
                srt = np.sort(x[past])
                R[idx, j] = np.searchsorted(srt, x[idx], side="left") / len(srt)
                R[idx, j] *= x[idx] > MIN_BITS
    a_max = run.alerts(-np.log2(1 - np.clip(R.max(1), 0, 1 - 1e-9)), budget)
    return {"OR (budget split)": a_or, "SUM of bits": a_sum, "MAX of ranks": a_max}


IMPACT_OF = None


def consequence_bits(run: Run) -> np.ndarray:
    """log2(impact x sensitivity) from the static layer, 0 when no repo is named."""
    from world import IMPACT
    imp = np.array([IMPACT[t] for t in run.tool], float)
    return np.log2(imp * np.maximum(run.sens, 1))


def e5b_consequence(run: Run, budget: float, strange_bits: np.ndarray):
    rows = []
    cons = consequence_bits(run)
    high = cons >= np.log2(4 * 4)
    for lam in (0.0, 0.5, 1.0):
        al = run.alerts(strange_bits + lam * cons, budget)
        r = run.report(al)
        rows.append([f"lambda={lam}"] + [fmt(r[k]) for k in KINDS]
                    + [f"{high[al].mean():.0%}" if al.any() else "–", f"{r['benign_rate']:.2%}"])
    return table(rows, ["strangeness + lambda*log2(impact*sens)"] + [SHORT[k] for k in KINDS]
                 + ["alerts on high-consequence calls", "benign"])


def caller_day_alerts(run: Run, cols, top_q: float, min_dims: int = 1) -> tuple[np.ndarray, float]:
    """Risk accumulation: per caller-day, add the strongest surprise of each dimension;
    alert caller-days above the top_q quantile of the previous 30 days' caller-day scores."""
    X = np.stack([run.col(c) for c in cols], 1)
    X = np.where(X > MIN_BITS, X, 0.0)
    keys = np.char.add(np.char.add(run.caller.astype(str), "|"), run.day.astype(str))
    uk, inv = np.unique(keys, return_inverse=True)
    best = np.zeros((len(uk), X.shape[1]))
    np.maximum.at(best, inv, X)
    score = best.sum(1) * ((best > 0).sum(1) >= min_dims)
    kday = np.zeros(len(uk), int)
    kday[inv] = run.day
    alert_k = np.zeros(len(uk), bool)
    for d in range(1, run.ndays):
        past = (kday >= d - CAL_DAYS) & (kday < d)
        now = kday == d
        if past.any() and now.any():
            alert_k[now] = score[now] > np.quantile(score[past], top_q)
    n_alert_days = alert_k.sum() / run.ndays
    return alert_k[inv], n_alert_days


def e7_plans(run: Run, total: float):
    """The three candidate plans at the same total budget."""
    p1_cols = ["order_rule.policy", "tool.peer", "rep.self", "rate.self", "reach.self", "dormancy.self"]
    plans = {"P1 rules + counters": combos(run, total, p1_cols)["MAX of ranks"],
             "P2 all dimensions, hierarchy": combos(run, total, DEFAULT)["MAX of ranks"]}
    a3, _ = caller_day_alerts(run, DEFAULT, 0.97)
    plans["P3 caller-day risk (RBA)"] = a3
    a3b, _ = caller_day_alerts(run, DEFAULT, 0.97, min_dims=2)
    plans["P3b caller-day risk, >=2 dimensions"] = a3b
    rows = []
    for name, al in plans.items():
        for h in HORIZONS:
            r = run.report(al, h)
            rows.append([name, h] + [fmt(r[k]) for k in KINDS]
                        + [f"{r['benign_rate']:.2%}", f"{r['caller_days_per_day']:.1f}"])
    return table(rows, ["plan", "horizon"] + [SHORT[k] for k in KINDS]
                 + ["benign calls flagged", "caller-days flagged / day"])


def e3_windows(runs: dict, budget: float):
    rows = []
    for w, run in runs.items():
        for c in ("asset.hier", "asset.peer", "asset.anchor", "reach.self", "reach.peer", "reach.hier"):
            r = run.report(run.alerts(run.col(c), budget))
            rows.append([f"{c} (W={w})", fmt(r["slow_creep"]), fmt(r["repeated_habit"]),
                         fmt(r["fan_out"]), fmt(r["legit_drift"]), fmt(r["team_transfer"]), fmt(r["new_repo"]),
                         f"{r['ordinary']:.2%}"])
    return table(rows, ["score (window)", "creep", "habit", "fanout", "legit_drift FP", "transfer FP",
                        "new_repo FP", "ordinary FP"])


def habit_decay(run: Run, budget: float):
    """Self-normalisation: alert rate of a weekly strange habit, week by week."""
    rows = []
    for c in ("reach.self", "reach.peer", "reach.hier", "size.self", "size.peer", "size.hier"):
        a = run.alerts(run.col(c), budget)
        by_week = defaultdict(list)
        for kind, d0, ix in run.episodes.values():
            if kind != "repeated_habit":
                continue
            for i in ix:
                by_week[(run.day[i] - d0) // 7].append(a[i])
        rows.append([c] + [fmt(np.mean(by_week[w])) if by_week[w] else "–" for w in (0, 1, 2, 4, 8, 12)])
    return table(rows, ["score", "wk1", "wk2", "wk3", "wk5", "wk9", "wk13"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-dir", type=Path, required=True)
    ap.add_argument("--seed", default="1")
    ap.add_argument("--budget", type=float, default=0.005)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args()
    a.out.mkdir(exist_ok=True)
    runs = {w: Run(a.scores_dir / f"scores_s{a.seed}_w{w}.npz") for w in ("30", "90", "life")}
    r90 = runs["90"]
    md = [f"# Dynamic dimensions — seed {a.seed}, per-dimension budget {a.budget:.1%}\n"]
    md += ["## E1 — which dimension catches which strange usage (W=90, default references)\n",
           e1_dimension_by_kind(r90, a.budget), ""]
    md += ["## E2 — compared with whom (W=90)\n", e2_references(r90, a.budget), ""]
    md += ["## E3 — window length and anchoring\n", e3_windows(runs, a.budget), ""]
    md += ["## E3b — self-normalisation of a weekly habit (W=90)\n", habit_decay(r90, a.budget), ""]
    total = a.budget * 2
    md += [f"## E4/E5 — combined detector over time (total budget {total:.1%}, W=90)\n"]
    rows = []
    for name, al in combos(r90, total).items():
        for h in HORIZONS:
            r = r90.report(al, h)
            rows.append([name, h] + [fmt(r[k]) for k in KINDS]
                        + [f"{r['benign_rate']:.2%}", fmt(r["sessions_per_day"], False)])
    md.append(table(rows, ["combination", "horizon"] + [SHORT[k] for k in KINDS] + ["benign", "sessions/day"]))
    X = np.stack([r90.col(c) for c in DEFAULT], 1)
    md += ["", f"## E5b — weighting strangeness by consequence (budget {total:.1%}, W=90)\n",
           e5b_consequence(r90, total, X.max(1)), ""]
    md += [f"## E7 — the three plans at the same budget ({total:.1%} of calls; P3: top 3% caller-days)\n",
           e7_plans(r90, total), ""]
    md += ["", "## E6 — holiday calendar (time dimension, W=90)\n"]
    rows = []
    from world import HOLIDAYS, START
    import datetime as _dt
    is_hol = np.array([(START + _dt.timedelta(days=int(d))).date() in HOLIDAYS for d in r90.day])
    for c in ("time.hier", "time_cal.hier"):
        al = r90.alerts(r90.col(c), a.budget)
        rows.append([c, f"{al[is_hol & r90.benign].mean():.2%}", f"{al[~is_hol & r90.benign].mean():.2%}",
                     fmt(r90.report(al)["off_hours"])])
    md.append(table(rows, ["score", "benign FP on holidays", "benign FP other days", "off_hours detect"]))
    (a.out / f"results_seed{a.seed}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
