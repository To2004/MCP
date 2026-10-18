"""Which dimensions to focus on: greedy forward selection at a fixed analyst load.

Candidate pool = every dimension built only from the request, the static scan or the policy
(no server responses, no rules that need roles or hours the policy does not state):
  per-call dimension scores from detectors.py, the four catalog dimensions from new_dims.py,
  a per-call weekly scope-drift score (re-anchored baseline, see drift.py) and the learned
  caller-day model (learned.py).
Dimensions are combined by adding risk events per caller-day (>= 2 dimensions agree, or one is
extreme), the best combiner found earlier. Selection runs on one world and is checked on the
other, so the ranking is not tuned to one random draw.

Run:  python focus_select.py --pick-seed 1 --check-seed 2
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

import learned
import new_dims
from evaluate import CAL_DAYS, KINDS, MIN_BITS, SHORT, Run, table
from plans import EVENT_RANK, at_load, caller_days, evaluate_points

HERE = Path(__file__).parent
SCORES = Path("/home/ovadyat/MCP/runs/dynamic_dimensions")
DETECTOR_COLS = {
    "repeat (same call within minutes)": "rep.hier",
    "calls per hour": "rate.hier",
    "items requested per day": "reach.hier",
    "size of each request": "size.hier",
    "assets per day": "breadth.hier",
    "first touch of an asset (self)": "asset.hier",
    "asset foreign to the team": "asset.peer",
    "new tool for this caller": "tool.hier",
    "order: next-step rarity": "order_tr.hier",
    "hour of week": "time_cal.hier",
    "dormancy": "dormancy.hier",
}
LOAD = 2.0
REVIEW_WEEKS, BASE_WEEKS = 26, 8


def scope_drift(path):
    """Per call: running out-of-team share of the caller's current week, z-scored against a
    baseline re-anchored on team change and every REVIEW_WEEKS (label-free ownership)."""
    owner = defaultdict(Counter)
    pending, cur_w = [], None
    week = {}                                     # caller -> [week, n, x]
    base = defaultdict(list)                      # caller -> closed weeks since anchor
    anchor = {}                                   # caller -> (week, team)
    out = []
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            w = int(float(r["ts"]) // (7 * 86400))
            if w != cur_w:
                for repo, team in pending:
                    owner[repo][team] += 1
                pending, cur_w = [], w
            c, team, repo = r["caller"], r["team"], r["repo"]
            wk = week.get(c)
            if wk and wk[0] != w:
                if wk[1] >= 10 and len(base[c]) < BASE_WEEKS:
                    base[c].append((wk[1], wk[2]))
                wk = None
            a = anchor.get(c)
            if a is None or a[1] != team or w - a[0] >= REVIEW_WEEKS:
                anchor[c], base[c] = (w, team), []
            if wk is None:
                wk = week[c] = [w, 0, 0]
            if repo and team != "org":
                top = owner[repo].most_common(1)
                wk[1] += 1
                wk[2] += int(bool(top) and top[0][0] != team)
                pending.append((repo, team))
            z = 0.0
            if len(base[c]) >= BASE_WEEKS and wk[1] >= 10:
                p0 = min(0.97, max(0.03, sum(x for _, x in base[c]) / max(1, sum(n for n, _ in base[c]))))
                z = max(0.0, (wk[2] - wk[1] * p0) / math.sqrt(wk[1] * p0 * (1 - p0)))
            out.append(z)
    return np.asarray(out, np.float32)


def learned_per_call(path, run: Run):
    """Caller-day surprise from the learned token model, z-scored per caller, copied to calls."""
    S, _, _ = learned.score_world(path)
    by = defaultdict(list)
    for (c, d), s in S.items():
        by[c].append((d, s))
    z = {}
    for c, seq in by.items():
        seq.sort()
        for i, (d, s) in enumerate(seq):
            past = [x for _, x in seq[max(0, i - 30):i]]
            if len(past) >= 5:
                med = float(np.median(past))
                z[(c, d)] = max(0.0, (s - med) / (float(np.median(np.abs(np.array(past) - med))) + 1.0))
    return np.array([z.get((str(c), int(d)), 0.0) for c, d in zip(run.caller, run.day)], np.float32)


def candidates(seed: str, world: str):
    run = Run(SCORES / f"scores_s{seed}_w90.npz")
    X = {name: run.col(col) for name, col in DETECTOR_COLS.items()}
    nd = new_dims.score(HERE / f"world_{world}.csv.gz")
    X["assets per session (policy: one at a time)"] = nd["assets_per_session"]
    X["consequence added up over the day"] = nd["consequence_day"]
    X["weekly write share"] = nd["write_share_week"]
    X["weekly scope drift (re-anchored)"] = scope_drift(HERE / f"world_{world}.csv.gz")
    X["learned day model"] = learned_per_call(HERE / f"world_{world}.csv.gz", run)
    return run, X


def rank_column(run: Run, x: np.ndarray) -> np.ndarray:
    R = np.zeros(len(x), np.float32)
    for d in range(1, run.ndays):
        past = np.concatenate(run.day_idx[max(0, d - CAL_DAYS):d])
        idx = run.day_idx[d]
        if len(past) and len(idx):
            srt = np.sort(x[past])
            R[idx] = np.searchsorted(srt, x[idx], side="left") / len(srt) * (x[idx] > MIN_BITS)
    return R


class Scorer:
    def __init__(self, run, X):
        self.run = run
        self.inv, self.kday = caller_days(run)
        self.R = {k: rank_column(run, v) for k, v in X.items()}

    def detect(self, names, horizons):
        ev = np.stack([self.R[n] >= EVENT_RANK for n in names], 1)
        bits = np.where(ev, -np.log2(np.clip(1 - np.stack([self.R[n] for n in names], 1), 1e-6, 1)), 0.0)
        best = np.zeros((self.inv.max() + 1, len(names)))
        np.maximum.at(best, self.inv, bits)
        S, D, top = best.sum(1), (best > 0).sum(1), best.max(1)
        credit = ev.any(1)
        res = {}
        for hz in horizons:
            pts = []
            for T in (10, 14, 18, 24, 32, 45, 60):
                for B in (12, 15, 99):
                    cd = ((S >= T) & (D >= 2)) | (top >= B)
                    pts.append(evaluate_points(self.run, None, cd, self.inv, self.kday, credit, hz))
            res[hz] = at_load(pts, LOAD)
        return res


def mean_det(res):
    vals = [np.nanmean(list(p[1].values())) for p in res.values() if p is not None]
    return float(np.mean(vals)) if vals else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pick-seed", default="1")
    ap.add_argument("--check-seed", default="2")
    ap.add_argument("--steps", type=int, default=9)
    ap.add_argument("--exclude", nargs="*", default=[], help="candidate names to leave out")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    H = [(30, 365), (365, 10**6)]
    pick = Scorer(*candidates(a.pick_seed, f"seed{a.pick_seed}"))
    check = Scorer(*candidates(a.check_seed, f"seed{a.check_seed}"))
    chosen, rows, prev = [], [], 0.0
    pool = [c for c in pick.R if c not in a.exclude]
    for step in range(a.steps):
        best = max((c for c in pool if c not in chosen),
                   key=lambda c: mean_det(pick.detect(chosen + [c], H)))
        chosen.append(best)
        rp, rc = pick.detect(chosen, H), check.detect(chosen, H)
        mp, mc = mean_det(rp), mean_det(rc)
        per = {k: np.nanmean([p[1][k] for p in rc.values() if p]) for k in KINDS}
        rows.append([str(step + 1), best, f"{mp:.0%}", f"+{mp - prev:.0%}", f"{mc:.0%}"]
                    + ["–" if np.isnan(per[k]) else f"{per[k]:.0%}" for k in KINDS])
        prev = mp
        print(" | ".join(rows[-1][:5]), flush=True)
    md = [f"# Greedy focus selection (pick on seed {a.pick_seed}, check on seed {a.check_seed}; "
          f"years 1-2; <= {LOAD:g} caller-days/day)\n",
          table(rows, ["step", "dimension added", "pick seed", "gain", "check seed"] + [SHORT[k] for k in KINDS])]
    (HERE / "results" / f"select_pick{a.pick_seed}{a.tag}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
