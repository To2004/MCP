"""Slow drift over months: weekly out-of-team share, against a frozen or a rolling baseline.

Per caller and ISO week: x = calls on repos that are not "in-team" (a repo is in-team when, so
far, most of its calls come from the caller's current team; learned without labels), n = calls
naming a repo. The week alerts when x is improbably high for the caller's baseline share p0
(one-sided binomial z-score):
  frozen   p0 = share over the caller's first BASE_WEEKS active weeks, never updated
  rolling  p0 = share over the previous BASE_WEEKS weeks
The z cut-off is swept; detection of slow_creep episodes and false alarms on legitimate drift
and team transfers are read at a fixed load of caller-weeks per week.

Run:  python drift.py world_seed1.csv.gz world_seed2.csv.gz
"""
from __future__ import annotations

import csv
import gzip
import math
import sys
from collections import Counter, defaultdict, deque

BASE_WEEKS = 8
REVIEW_WEEKS = 26
P_FLOOR = 0.03
WEEK = 7 * 86400.0


def weekly(path):
    """Per (caller, week): n, x, labels. In-team ownership is learned online, week by week."""
    owner = defaultdict(Counter)                     # repo -> team -> calls so far
    weeks = defaultdict(lambda: {"n": 0, "x": 0, "creep": set(), "legit": Counter(), "team": ""})
    pending = []
    cur = None
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            w = int(float(r["ts"]) // WEEK)
            if w != cur:                              # ownership learned from previous weeks only
                for repo, team in pending:
                    owner[repo][team] += 1
                pending, cur = [], w
            repo, team = r["repo"], r["team"]
            if not repo or team == "org":
                continue
            k = weeks[(r["caller"], w)]
            k["n"] += 1
            k["team"] = team
            top = owner[repo].most_common(1)
            k["x"] += int(bool(top) and top[0][0] != team)
            if r["strange"] == "slow_creep":
                k["creep"].add(r["episode"])
            if r["legit"]:
                k["legit"][r["legit"]] += 1
            pending.append((repo, team))
    return weeks


def zscores(weeks):
    by_caller = defaultdict(list)
    for (c, w), v in sorted(weeks.items(), key=lambda kv: kv[0][1]):
        by_caller[c].append((w, v))
    out = []
    for c, seq in by_caller.items():
        hist = deque(maxlen=BASE_WEEKS)
        frozen, reanch, anchor_w, team = [], [], None, None
        for w, v in seq:
            if v["n"] < 10:
                continue
            # re-anchor on an accepted change (declared team change) and at a semi-annual review
            if v["team"] != team or (anchor_w is not None and w - anchor_w >= REVIEW_WEEKS):
                reanch, anchor_w, team = [], w, v["team"]
            res = {"w": w, "v": v}
            for name, base in (("frozen", frozen if len(frozen) >= BASE_WEEKS else None),
                               ("reanchored", reanch if len(reanch) >= BASE_WEEKS else None),
                               ("rolling", list(hist) if len(hist) >= BASE_WEEKS else None)):
                if base is None:
                    res[name] = 0.0
                    continue
                p0 = min(0.97, max(P_FLOOR, sum(b["x"] for b in base) / max(1, sum(b["n"] for b in base))))
                res[name] = (v["x"] - v["n"] * p0) / math.sqrt(v["n"] * p0 * (1 - p0))
            out.append(res)
            hist.append(v)
            if len(frozen) < BASE_WEEKS:
                frozen.append(v)
            if len(reanch) < BASE_WEEKS:
                reanch.append(v)
    return out


def main():
    rows = []
    for path in sys.argv[1:]:
        res = zscores(weekly(path))
        n_weeks = len({r["w"] for r in res})
        episodes = {e for r in res for e in r["v"]["creep"]}
        for name in ("frozen", "reanchored", "rolling"):
            for target in (0.5, 1.0, 2.0):
                best = None
                for z in (2, 3, 4, 5, 6, 8, 10, 13, 16, 20):
                    al = [r for r in res if r[name] > z]
                    load = len(al) / n_weeks
                    if load <= target:
                        caught = {e for r in al for e in r["v"]["creep"]}
                        legit_w = [r for r in res if r["v"]["legit"].get("legit_drift") or r["v"]["legit"].get("team_transfer")]
                        fp = sum(r[name] > z for r in legit_w) / max(1, len(legit_w))
                        best = (z, load, len(caught) / max(1, len(episodes)), fp)
                        break
                rows.append((path.split("/")[-1], name, target) + (best or (None,) * 4))
    print(f"{'world':<22}{'baseline':<9}{'target':>7}{'z':>5}{'load/wk':>9}{'creep caught':>14}{'FP on legit-drift/transfer weeks':>34}")
    for r in rows:
        if r[3] is None:
            print(f"{r[0]:<22}{r[1]:<9}{r[2]:>7}   unreachable")
        else:
            print(f"{r[0]:<22}{r[1]:<9}{r[2]:>7}{r[3]:>5}{r[4]:>9.2f}{r[5]:>14.0%}{r[6]:>34.0%}")


if __name__ == "__main__":
    main()
