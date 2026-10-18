"""Dimensions the gateway-log/2 wire log makes possible, tested where the synthetic world allows.

Request-side fields only (agent->server lines): agent, session id + position (gateway.seq),
timestamps, tool name, the argument KEYS of the call (not their values).
  arg_keys_new     this caller has never passed this set of argument keys to this tool
                   (attribute presence, Kruegel & Vigna 2003), priced by how often the caller
                   produces new key sets at all
  session_length   position of the call in its session (gateway.seq) vs the caller's past sessions
  sessions_per_hour  sessions this caller started in the last hour vs its own history
Each is added to the five focus dimensions and the marginal gain is measured at <= 2
caller-days per day, picking nothing: the same set is scored on both worlds.

Run:  python wire_dims.py
"""
from __future__ import annotations

import csv
import gzip
import json
import math
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

from evaluate import KINDS, SHORT, Run, fmt, table
from focus_select import DETECTOR_COLS, SCORES, Scorer, mean_det

HERE = Path(__file__).parent
FOCUS5 = ["order: next-step rarity", "size of each request", "first touch of an asset (self)",
          "calls per hour", "new tool for this caller"]


def upper_bits(hist, x):
    return -math.log2((sum(1 for h in hist if h >= x) + 1) / (len(hist) + 1)) if len(hist) >= 20 else 0.0


def wire_scores(path):
    seen_keys = defaultdict(set)                 # (caller, tool) -> key sets seen
    new_rate = defaultdict(lambda: [0, 0])       # caller -> [calls, novel key sets]
    sess_pos = {}
    sess_len_hist = defaultdict(lambda: deque(maxlen=500))
    sess_open = defaultdict(dict)                # caller -> session -> last position
    starts = defaultdict(deque)                  # caller -> session start times (1 h)
    sph_hist = defaultdict(lambda: deque(maxlen=2000))
    out = defaultdict(list)
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            c, s, ts = r["caller"], r["session"], float(r["ts"])
            keys = tuple(sorted(json.loads(r["args"])))
            st = new_rate[c]
            novel = keys not in seen_keys[(c, r["tool"])]
            out["arg keys new for caller+tool"].append(
                -math.log2((st[1] + 1) / (st[0] + 1)) if novel and st[0] >= 20 else 0.0)
            st[0] += 1
            st[1] += novel
            seen_keys[(c, r["tool"])].add(keys)
            first = s not in sess_pos
            if first:                              # a new session: close the caller's older ones
                for old, n in list(sess_open[c].items()):
                    sess_len_hist[c].append(n)
                    del sess_open[c][old]
                q = starts[c]
                q.append(ts)
                while q[0] < ts - 3600:
                    q.popleft()
                out["sessions started per hour"].append(upper_bits(sph_hist[c], len(q)))
                sph_hist[c].append(len(q))
            else:
                out["sessions started per hour"].append(0.0)
            sess_pos[s] = sess_pos.get(s, 0) + 1
            sess_open[c][s] = sess_pos[s]
            out["session length so far"].append(upper_bits(sess_len_hist[c], sess_pos[s]))
    return {k: np.asarray(v, np.float32) for k, v in out.items()}


def main():
    rows, md = [], ["# Wire-log dimensions added to the five focus dimensions (<= 2 caller-days/day)\n"]
    results = {}
    for sd in ("1", "2"):
        run = Run(SCORES / f"scores_s{sd}_w90.npz")
        X = {name: run.col(col) for name, col in DETECTOR_COLS.items()}
        X.update(wire_scores(HERE / f"world_seed{sd}.csv.gz"))
        sc = Scorer(run, X)
        H = [(30, 365), (365, 10**6)]
        sets = {"five focus dimensions": FOCUS5}
        for extra in ("arg keys new for caller+tool", "session length so far", "sessions started per hour"):
            sets[f"five + {extra}"] = FOCUS5 + [extra]
        sets["five + all three"] = FOCUS5 + ["arg keys new for caller+tool", "session length so far",
                                             "sessions started per hour"]
        for name, cols in sets.items():
            res = sc.detect(cols, H)
            per = {k: np.nanmean([p[1][k] for p in res.values() if p]) for k in KINDS}
            results.setdefault(name, []).append((mean_det(res), per))
        print(f"seed {sd} done", flush=True)
    for name, ps in results.items():
        per = {k: np.nanmean([p[1][k] for p in ps]) for k in KINDS}
        rows.append([name, f"{np.mean([p[0] for p in ps]):.0%}"] + [fmt(per[k]) for k in KINDS])
    md.append(table(rows, ["dimension set", "mean detect (2 seeds, years 1-2)"] + [SHORT[k] for k in KINDS]))
    (HERE / "results" / "wire_dims.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
