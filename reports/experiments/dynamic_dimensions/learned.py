"""Option 3 test: one learned model over generic call tokens, no hand-built dimensions.

Each call becomes generic tokens built only from what any MCP exposes plus the static scan's
input effects: the tool, the value of its `which` input (an opaque asset handle), a log bucket
of its `how_much` inputs, and the tool-to-tool step inside the session. A caller-day is scored
by how surprising its tokens are given the history BEFORE that day (self mixed with the role's
peers, counts decaying with a 45-day half-life), then compared with the caller's own recent days.
Detection is read at <= LOAD alerted caller-days per day, as in focus.py.

Run:  python learned.py
"""
from __future__ import annotations

import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from evaluate import KINDS, SHORT, table

HALF_LIFE = 45.0
ALPHA = 50.0            # pseudo-count weight of the peer prior in the self estimate
LOAD = 2.0
SIZE_KEYS = ("per_page", "perPage", "page")


class Decayed:
    """Counts that halve every HALF_LIFE days."""
    def __init__(self):
        self.c, self.t, self.n, self.nt = {}, {}, 0.0, 0

    def _decay(self, v, last, day):
        return v * 0.5 ** ((day - last) / HALF_LIFE)

    def get(self, k, day):
        return self._decay(self.c[k], self.t[k], day) if k in self.c else 0.0

    def total(self, day):
        return self._decay(self.n, self.nt, day)

    def add(self, k, day, w=1.0):
        self.c[k] = self.get(k, day) + w
        self.t[k] = day
        self.n = self.total(day) + w
        self.nt = day


def tokens(row, prev_tool):
    a = json.loads(row["args"])
    size = 1.0
    for k in SIZE_KEYS:
        if k in a:
            try:
                size *= max(1.0, float(a[k]))
            except (TypeError, ValueError):
                pass
    sb = int(math.log2(size)) if size > 1 else 0
    return [f"u|{row['tool']}|{row['repo'] or '-'}|{sb}", f"b|{prev_tool}>{row['tool']}"]


def surprise(tok, me, peer, day):
    pp = (peer.get(tok, day) + 1.0) / (peer.total(day) + len(peer.c) + 1.0)
    ps = (me.get(tok, day) + ALPHA * pp) / (me.total(day) + ALPHA)
    return -math.log2(ps)


def score_world(path):
    """Return {(caller, day): score} and per caller-day episode ids."""
    me, peer = defaultdict(Decayed), defaultdict(Decayed)
    prev = {}
    day_rows = []
    cur = None
    S = defaultdict(float)
    eps = defaultdict(set)
    kinds = {}

    def flush(day, rows):
        for caller, role, toks in rows:                 # remember the day only after scoring it
            for t in toks:
                me[caller].add(t, day)
                peer[role].add(t, day)

    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            day = int(float(r["ts"]) // 86400)
            if day != cur:
                if cur is not None:
                    flush(cur, day_rows)
                day_rows, cur = [], day
            key = (r["caller"], r["session"])
            toks = tokens(r, prev.get(key, "start"))
            prev[key] = r["tool"]
            S[(r["caller"], day)] += sum(surprise(t, me[r["caller"]], peer[r["role"]], day) for t in toks)
            day_rows.append((r["caller"], r["role"], toks))
            if r["episode"]:
                eps[(r["caller"], day)].add(r["episode"])
                kinds[r["episode"]] = r["strange"]
    return S, eps, kinds


def evaluate(S, eps, kinds, horizon):
    by_caller = defaultdict(list)
    for (c, d), s in S.items():
        by_caller[c].append((d, s))
    z = {}
    for c, seq in by_caller.items():
        seq.sort()
        for i, (d, s) in enumerate(seq):
            past = [x for _, x in seq[max(0, i - 30):i]]
            if len(past) < 5:
                z[(c, d)] = 0.0
                continue
            med = float(np.median(past))
            mad = float(np.median(np.abs(np.array(past) - med))) + 1.0
            z[(c, d)] = (s - med) / mad
    lo, hi = horizon
    days = {d for (_, d) in S if lo <= d < hi}
    all_eps = {e for k, es in eps.items() if lo <= k[1] < hi for e in es}
    best = None
    for thr in (3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 64):
        al = {k for k, v in z.items() if v > thr and lo <= k[1] < hi}
        load = len(al) / max(1, len(days))
        if load <= LOAD:
            caught = {e for k in al for e in eps.get(k, ())}
            det = {}
            for kind in KINDS:
                es = [e for e in all_eps if kinds[e] == kind]
                det[kind] = len([e for e in es if e in caught]) / len(es) if es else np.nan
            best = (load, det)
            break
    return best


def main():
    groups = {"month 1": (["month_seed11", "month_seed12"], (0, 30)),
              "year 1": (["seed1", "seed2"], (30, 365)), "year 2": (["seed1", "seed2"], (365, 10**6))}
    cache = {}
    md = [f"# One learned model over generic tokens, <= {LOAD:g} caller-days per day\n"]
    for g, (worlds, hz) in groups.items():
        ps = []
        for w in worlds:
            if w not in cache:
                cache[w] = score_world(Path(__file__).parent / f"world_{w}.csv.gz")
            ps.append(evaluate(*cache[w], hz))
        ps = [p for p in ps if p]
        det = {k: np.nanmean([p[1][k] for p in ps]) for k in KINDS}
        row = ["learned token model", f"{np.mean([p[0] for p in ps]):.1f}", f"{np.nanmean(list(det.values())):.0%}"]
        row += ["–" if np.isnan(det[k]) else f"{det[k]:.0%}" for k in KINDS]
        md += [f"## {g}\n", table([row], ["model", "load", "mean detect"] + [SHORT[k] for k in KINDS]), ""]
        print(md[-2], flush=True)
    (Path(__file__).parent / "results" / "learned.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
