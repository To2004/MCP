"""Which TOPIC to focus on: three dimension bundles (no policy rules) at equal analyst load.

  A  volume over short time      repetition, rate, reach, size          (session / hour / day)
  B  what is touched vs peers    asset first-touch (self, team), breadth (self, team)
  C  order and time              next-tool rarity, new tool, time of week, dormancy

Each bundle: every column ranked against its own previous 30 days, strongest column wins,
knob swept, detection read at <= LOAD alerted caller-days per day. Pairs and all three are
reported too, to show what adding a second topic buys.

Run:  python focus.py --scores-dir ../../../runs/dynamic_dimensions
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from evaluate import KINDS, SHORT, Run, table
from plans import at_load, caller_days, evaluate_points, ranks

FOCUS = {
    "A volume, short time": ["rep.hier", "rate.hier", "reach.hier", "size.hier"],
    "B what is touched, vs peers": ["asset.hier", "asset.peer", "breadth.hier", "breadth.peer"],
    "C order and time": ["order_tr.hier", "tool.hier", "time_cal.hier", "dormancy.hier"],
}
FOCUS["A+B"] = FOCUS["A volume, short time"] + FOCUS["B what is touched, vs peers"]
FOCUS["A+C"] = FOCUS["A volume, short time"] + FOCUS["C order and time"]
FOCUS["B+C"] = FOCUS["B what is touched, vs peers"] + FOCUS["C order and time"]
FOCUS["A+B+C"] = FOCUS["A+B"] + FOCUS["C order and time"]
THRESHOLDS = (0.98, 0.99, 0.995, 0.998, 0.999, 0.9995, 0.9998, 0.99995)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-dir", type=Path, required=True)
    ap.add_argument("--load", type=float, default=2.0)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results" / "focus.md")
    a = ap.parse_args()
    groups = {"month 1 of a new deployment": (["11", "12"], (0, 30)),
              "year 1": (["1", "2"], (30, 365)),
              "year 2": (["1", "2"], (365, 10**6))}
    runs = {}
    md = [f"# Three topics to focus on, at <= {a.load:g} alerted caller-days per day (no rules)\n"]
    for gname, (seeds, hz) in groups.items():
        rows = []
        for fname, cols in FOCUS.items():
            pts_all = []
            for sd in seeds:
                if sd not in runs:
                    runs[sd] = Run(a.scores_dir / f"scores_s{sd}_w90.npz")
                run = runs[sd]
                inv, kday = caller_days(run)
                R = ranks(run, cols).max(1)
                pts = [evaluate_points(run, R >= t, None, inv, kday, None, hz) for t in THRESHOLDS]
                pts_all.append(at_load(pts, a.load))
            pts_all = [p for p in pts_all if p is not None]
            if not pts_all:
                rows.append([fname, "–", "unreachable"] + ["–"] * len(KINDS))
                continue
            det = {k: np.nanmean([p[1][k] for p in pts_all]) for k in KINDS}
            rows.append([fname, f"{np.mean([p[0] for p in pts_all]):.1f}",
                         f"{np.nanmean(list(det.values())):.0%}"]
                        + ["–" if np.isnan(det[k]) else f"{det[k]:.0%}" for k in KINDS])
        md += [f"## {gname}\n", table(rows, ["focus", "load", "mean detect"] + [SHORT[k] for k in KINDS]), ""]
        print(md[-2], flush=True)
    a.out.write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()


def accumulate(run, cols, hz):
    """Same bundle, combined by adding risk events per caller-day (>= 2 dimensions agree,
    or one is extreme) instead of taking the strongest column."""
    from plans import EVENT_RANK
    inv, kday = caller_days(run)
    R = ranks(run, cols)
    ev = R >= EVENT_RANK
    bits = np.where(ev, -np.log2(np.clip(1 - R, 1e-6, 1)), 0.0)
    best = np.zeros((inv.max() + 1, bits.shape[1]))
    np.maximum.at(best, inv, bits)
    S, D, top = best.sum(1), (best > 0).sum(1), best.max(1)
    credit = ev.any(1)
    pts = []
    for T in (10, 14, 18, 24, 32, 45):
        for B in (12, 15, 99):
            cd = ((S >= T) & (D >= 2)) | (top >= B)
            pts.append(evaluate_points(run, None, cd, inv, kday, credit, hz))
    return pts


def main_accumulated(scores_dir: Path, load: float, out: Path):
    groups = {"month 1 of a new deployment": (["11", "12"], (0, 30)),
              "year 1": (["1", "2"], (30, 365)), "year 2": (["1", "2"], (365, 10**6))}
    runs = {}
    md = [f"# Topics combined by adding risk per caller-day, at <= {load:g} caller-days per day\n"]
    for gname, (seeds, hz) in groups.items():
        rows = []
        for fname, cols in FOCUS.items():
            ps = []
            for sd in seeds:
                runs.setdefault(sd, Run(scores_dir / f"scores_s{sd}_w90.npz"))
                ps.append(at_load(accumulate(runs[sd], cols, hz), load))
            ps = [p for p in ps if p is not None]
            if not ps:
                rows.append([fname, "–", "unreachable"] + ["–"] * len(KINDS))
                continue
            det = {k: np.nanmean([p[1][k] for p in ps]) for k in KINDS}
            rows.append([fname, f"{np.mean([p[0] for p in ps]):.1f}", f"{np.nanmean(list(det.values())):.0%}"]
                        + ["–" if np.isnan(det[k]) else f"{det[k]:.0%}" for k in KINDS])
        md += [f"## {gname}\n", table(rows, ["focus", "load", "mean detect"] + [SHORT[k] for k in KINDS]), ""]
        print(md[-2], flush=True)
    out.write_text("\n".join(md) + "\n")
