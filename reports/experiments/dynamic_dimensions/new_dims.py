"""Test dimensions added from the Dynamic Context Catalog that the synthetic world can exercise.

Only request-side facts, static-scan results and what the policy states are used:
  assets_per_session  distinct repos named in this session so far; Block 4 of github_helios says
                      "one repository at a time", so the count above 1 is scored directly
  consequence_day     static impact x sensitivity added up over the caller's day so far,
                      ranked against the caller's own previous days
  write_share_week    share of write/remove calls in the caller's week vs its previous 8 weeks
  unregistered_day    share of the caller's repo calls today that name an asset missing from the
                      policy register (Table 2), vs the caller's previous days
Scores are bits or z-scores; evaluate.py's label-free daily threshold and episode report are
reused, so results line up with E1 in results_seed*.md.

Run:  python new_dims.py
"""
from __future__ import annotations

import csv
import gzip
import math
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

from evaluate import KINDS, LEGIT, SHORT, Run, fmt, table
from world import IMPACT, SEED_REPOS, TOOL_CLASS

BUDGET = 0.005
REGISTERED = {r for rs in SEED_REPOS.values() for r, _ in rs}
WRITE_CLASSES = {"write", "merge", "admin", "review"}


def upper_p(hist, x):
    return (sum(1 for h in hist if h >= x) + 1) / (len(hist) + 1)


def score(path):
    sess_assets = defaultdict(set)
    day_cons, cons_hist = defaultdict(float), defaultdict(lambda: deque(maxlen=60))
    day_unreg = defaultdict(lambda: [0, 0])
    unreg_hist = defaultdict(lambda: deque(maxlen=60))
    week_ops = defaultdict(lambda: [0, 0])
    week_hist = defaultdict(lambda: deque(maxlen=8))
    last_day, last_week = {}, {}
    out = defaultdict(list)
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            c, ts = r["caller"], float(r["ts"])
            day, week = int(ts // 86400), int(ts // (7 * 86400))
            if last_day.get(c) not in (None, day):          # close the caller's previous day
                cons_hist[c].append(day_cons.pop(c, 0.0))
                n, u = day_unreg.pop(c, [0, 0])
                if n:
                    unreg_hist[c].append(u / n)
            if last_week.get(c) not in (None, week):
                n, w = week_ops.pop(c, [0, 0])
                if n >= 10:
                    week_hist[c].append(w / n)
            last_day[c], last_week[c] = day, week
            repo, sens = r["repo"], int(r["sens"])
            if repo:
                sess_assets[r["session"]].add(repo)
            out["assets_per_session"].append(float(max(0, len(sess_assets[r["session"]]) - 1)))
            day_cons[c] += IMPACT[r["tool"]] * max(1, sens)
            out["consequence_day"].append(-math.log2(upper_p(cons_hist[c], day_cons[c]))
                                          if len(cons_hist[c]) >= 10 else 0.0)
            if repo:
                d = day_unreg[c]
                d[0] += 1
                d[1] += repo not in REGISTERED
            n, u = day_unreg[c]
            share = u / n if n else 0.0
            out["unregistered_day"].append(-math.log2(upper_p(unreg_hist[c], share))
                                           if len(unreg_hist[c]) >= 10 and share > 0 else 0.0)
            wk = week_ops[c]
            wk[0] += 1
            wk[1] += TOOL_CLASS[r["tool"]] in WRITE_CLASSES
            hist = week_hist[c]
            if len(hist) >= 4 and wk[0] >= 10:
                p0 = min(0.97, max(0.03, float(np.mean(hist))))
                z = (wk[1] - wk[0] * p0) / math.sqrt(wk[0] * p0 * (1 - p0))
            else:
                z = 0.0
            out["write_share_week"].append(max(0.0, z))
    return {k: np.asarray(v, np.float32) for k, v in out.items()}


def main():
    here = Path(__file__).parent
    md = [f"# New dimensions from the Dynamic Context Catalog (per-dimension budget {BUDGET:.1%})\n"]
    for sd in ("1", "2"):
        run = Run(Path(f"/home/ovadyat/MCP/runs/dynamic_dimensions/scores_s{sd}_w90.npz"))
        sc = score(here / f"world_seed{sd}.csv.gz")
        rows = []
        for name, x in sc.items():
            r = run.report(run.alerts(x, BUDGET))
            rows.append([name] + [fmt(r[k]) for k in KINDS] + [f"{r['benign_rate']:.2%}"]
                        + [fmt(r[t]) for t in ("new_hire", "team_transfer", "new_repo", "oncall_incident")])
        md += [f"## seed {sd}\n", table(rows, ["dimension"] + [SHORT[k] for k in KINDS]
                                        + ["benign", "new_hire FP", "transfer FP", "new_repo FP", "incident FP"]), ""]
        print(md[-2], flush=True)
    (here / "results" / "new_dims.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
