"""Second batch of dimensions, taken from the published feature catalog (request-side only).

Same input and alignment as dims2.py (one row per agent->server message), written to a separate
file and merged by eval2.py. Each feature cites where it comes from:
  fano_1h               count dispersion over 1-minute bins in the last hour (index of dispersion)
  gap_memory            correlation of consecutive inter-call gaps (Goh & Barabasi 2008, memory M)
  low_revisit           1 - share of recent asset calls revisiting an asset (PUBCRAWL "low revisit")
  monotone_run          run of strictly increasing page / asset values in a session (PUBCRAWL sorted order)
  asset_entropy_1h      entropy of assets named in the last hour (Lakhina et al. 2005)
  tool_entropy_1h       entropy of tools called in the last hour (Lakhina et al. 2005)
  unpopular_share_day   share of today's asset calls on assets few others touch (Beehive; Elastic freq_rare)
  new_edges_today       first-time agent->asset pairs today (Beehive "new destinations"; Metelli & Heard)
  cusum_calls           CUSUM of daily call counts vs the agent's previous 28 days (Page 1954)
  cusum_new_edges       CUSUM of daily new edges (Page 1954)
  addresses_in_session  distinct client addresses inside one session (Tan & Kumar MultiIP)
  non_dominant_client   1 - share of today's messages from the agent's main (address, client) (PUBCRAWL)
  client_context        -log p(address, client, user agent | agent), smoothed (Freeman et al. NDSS 2016)
  list_to_call_delay    how unusual the delay from tools/list to the first call is for this agent (OWASP API6)
  distinct_who_day      distinct recipients named today (Elastic distinct_count; Le et al. n_des)
  retry_after_cancel    the same call re-sent after a cancellation in this session (back-off signature)
  non_call_share        share of non-call messages among the agent's last 30 (method mix, Tan & Kumar)

Run:  python dims3.py --world w2/<scenario>.csv.gz --server <s> --out <scenario>_x.npz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from array import array
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

from detectors import Hist, vbin
from world2 import Profile

csv.field_size_limit(10**9)
W, DAY = 90, 86400.0
DIMS3 = ["fano_1h", "gap_memory", "low_revisit", "monotone_run", "asset_entropy_1h", "tool_entropy_1h",
         "unpopular_share_day", "new_edges_today", "cusum_calls", "cusum_new_edges", "addresses_in_session",
         "non_dominant_client", "client_context", "list_to_call_delay", "distinct_who_day",
         "retry_after_cancel", "non_call_share"]


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


def entropy(c: Counter):
    n = sum(c.values())
    return -sum(v / n * math.log2(v / n) for v in c.values() if v) if n else 0.0


class Engine3:
    def __init__(self, profile):
        self.p = profile
        self.h = {}
        self.q = defaultdict(lambda: defaultdict(deque))
        self.sess = {}
        self.today = {}
        self.daily = defaultdict(lambda: defaultdict(lambda: deque(maxlen=28)))
        self.cusum = defaultdict(lambda: defaultdict(float))
        self.edges = defaultdict(set)
        self.touch = defaultdict(dict)
        self.ctx = defaultdict(lambda: defaultdict(Counter))
        self.last30 = defaultdict(lambda: deque(maxlen=30))
        self.day = -1

    def up(self, key, x):
        hist = self.h.get(key)
        if hist is None:
            hist = self.h[key] = Hist(W)
        b = vbin(x)
        s = bits(hist.p_upper(b)) if hist.n >= 20 else 0.0
        hist.add(self.day, b)
        return s

    def win(self, a, name, ts, span, x=1):
        dq = self.q[a][name]
        dq.append((ts, x))
        while dq[0][0] < ts - span:
            dq.popleft()
        return dq

    def close_day(self, a, td):
        for name, x in (("calls", td["calls"]), ("edges", td["edges"])):
            hist = self.daily[a][name]
            if len(hist) >= 7:
                mu = sum(hist) / len(hist)
                sd = math.sqrt(sum((v - mu) ** 2 for v in hist) / len(hist)) + 1.0
                self.cusum[a][name] = max(0.0, self.cusum[a][name] + (x - mu) / sd - 0.5)
            hist.append(x)

    def score(self, r):
        ts = float(r["ts"])
        day = int(ts // DAY)
        if day != self.day:
            for hst in self.h.values():
                hst.expire(day)
            self.day = day
        a, sid, method = r["agent"], r["session"], r["method"]
        out = dict.fromkeys(DIMS3, 0.0)
        st = self.sess.get(sid)
        if st is None:
            st = self.sess[sid] = {"addr": set(), "list_ts": None, "first_call": True, "last_page": {},
                                   "run": 0, "cancelled": set(), "prev_canon": None}
        st["addr"].add(r["address"])
        out["addresses_in_session"] = float(len(st["addr"]) - 1)
        td = self.today.get(a)
        if td is None or td["day"] != day:
            if td is not None:
                self.close_day(a, td)
            td = self.today[a] = {"day": day, "calls": 0, "edges": 0, "asset_calls": 0, "unpop": 0,
                                  "pairs": Counter(), "who": set()}
        pair = (r["address"], r["client"])
        td["pairs"][pair] += 1
        tot = sum(td["pairs"].values())
        if tot >= 5:
            out["non_dominant_client"] = self.up(("ndc", a), 20 * (1 - max(td["pairs"].values()) / tot))
        # smoothed categorical likelihood of the client context (Freeman et al. 2016)
        s = 0.0
        for k, v in (("addr", r["address"]), ("client", r["client"]), ("ua", r["ua"])):
            c = self.ctx[a][k]
            n, m = sum(c.values()), len(c)
            p0 = (c[v] / n) * (1 - m / (n + m)) if c[v] else 1 / (n + m + 1)
            s += bits(p0) if n >= 20 else 0.0
            c[v] += 1
        out["client_context"] = s
        self.last30[a].append(method != "tools/call")
        out["non_call_share"] = self.up(("ncs", a), 20 * sum(self.last30[a]) / len(self.last30[a]))
        if method == "tools/list":
            st["list_ts"] = ts
        elif method == "notifications/cancelled" and st["prev_canon"]:
            st["cancelled"].add(st["prev_canon"])
        if method != "tools/call":
            return out
        td["calls"] += 1
        tool, which = r["tool"], r["which"]
        args = json.loads(r["args"]) if r["args"] else {}
        canon = tool + r["args"]
        out["cusum_calls"] = self.cusum[a]["calls"]
        if canon in st["cancelled"]:
            out["retry_after_cancel"] = 5.0
        st["prev_canon"] = canon
        if st["first_call"]:
            st["first_call"] = False
            if st["list_ts"] is not None:
                d = math.log10(max(ts - st["list_ts"], 0.01))
                med = self.q[a]["l2c_med"]
                past = sorted(x for _, x in med)
                if len(past) >= 20:
                    out["list_to_call_delay"] = 4 * abs(d - past[len(past) // 2])
                self.win(a, "l2c_med", ts, 30 * DAY, d)
        # timing shape
        mins = self.win(a, "minutes", ts, 3600, int(ts // 60))
        if len(mins) >= 10:
            c = Counter(x for _, x in mins)
            counts = [c.get(m, 0) for m in range(int(ts // 60) - 59, int(ts // 60) + 1)]
            mu = sum(counts) / 60
            var = sum((x - mu) ** 2 for x in counts) / 60
            out["fano_1h"] = self.up(("fano", a), 2 * var / mu if mu else 0.0)
        gaps = self.win(a, "gaps", ts, 7 * DAY, ts)
        if len(gaps) >= 22:
            t = [x for _, x in list(gaps)[-22:]]
            g = [y - x for x, y in zip(t, t[1:])]
            g1, g2 = g[:-1], g[1:]
            m1, m2 = sum(g1) / len(g1), sum(g2) / len(g2)
            s1 = math.sqrt(sum((x - m1) ** 2 for x in g1) / len(g1)) + 1e-9
            s2 = math.sqrt(sum((x - m2) ** 2 for x in g2) / len(g2)) + 1e-9
            mcoef = sum((x - m1) * (y - m2) for x, y in zip(g1, g2)) / (len(g1) * s1 * s2)
            out["gap_memory"] = self.up(("mem", a), 10 * max(0.0, mcoef))
        out["tool_entropy_1h"] = self.up(("tent", a), 4 * entropy(Counter(x for _, x in self.win(a, "tools", ts, 3600, tool))))
        # pages / ordering
        page = next((args[k] for k in ("page", "cursor", "offset") if k in args), None)
        key = which or page
        if key is not None:
            last = st["last_page"].get(tool)
            try:
                inc = last is not None and (float(key) > float(last) if not isinstance(key, str) else str(key) > str(last))
            except (TypeError, ValueError):
                inc = last is not None and str(key) > str(last)
            st["run"] = st["run"] + 1 if inc else 0
            st["last_page"][tool] = key
            out["monotone_run"] = self.up(("mono", a), st["run"])
        who = []
        for k in self.p.keys(tool, "who"):
            v = args.get(k)
            if isinstance(v, list):
                who += [json.dumps(x, sort_keys=True)[:60] for x in v]
            elif v is not None and not isinstance(v, bool):
                who += [str(v)]
        if who:
            td["who"].update(who[:500])
            out["distinct_who_day"] = self.up(("dwho", a), len(td["who"]))
        if which:
            recent = self.win(a, "assets", ts, DAY, which)
            last20 = [x for _, x in list(recent)[-20:]]
            if len(last20) >= 10:
                rev = sum(1 for i, x in enumerate(last20) if x in last20[:i]) / len(last20)
                out["low_revisit"] = self.up(("rev", a), 20 * (1 - rev))
            hour = Counter(x for _, x in recent if _ >= ts - 3600)
            out["asset_entropy_1h"] = self.up(("aent", a), 4 * entropy(hour))
            new = which not in self.edges[a]
            if new:
                self.edges[a].add(which)
                td["edges"] += 1
            out["new_edges_today"] = self.up(("edges", a), td["edges"]) if new else 0.0
            out["cusum_new_edges"] = self.cusum[a]["edges"] if new else 0.0
            others = sum(1 for ag, d in self.touch[which].items() if ag != a and d > day - W)
            td["asset_calls"] += 1
            td["unpop"] += others <= 2
            if td["asset_calls"] >= 5:
                out["unpopular_share_day"] = self.up(("unpop", a), 20 * td["unpop"] / td["asset_calls"])
            self.touch[which][a] = day
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine3(Profile(a.server))
    cols = {d: array("f") for d in DIMS3}
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            o = eng.score(r)
            for d in DIMS3:
                cols[d].append(o[d])
    arr = np.stack([np.frombuffer(cols[d], dtype=np.float32) for d in DIMS3], 1)
    np.savez_compressed(a.out, scores=arr, cols=np.array(DIMS3))
    print(f"{a.world.name}: {arr.shape[0]:,} messages x {arr.shape[1]} extra dimensions -> {a.out.name}")


if __name__ == "__main__":
    main()
