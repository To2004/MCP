"""Research-recommended high-level dimensions (no tool inputs, no specific asset; client and network
only in general form). Same rows as dims2-5; eval2.py merges this file (<scenario>_q.npz).

  session_count_distance   L1 distance of this session's tool-count vector (so far, IDF-weighted) to the
                           nearest of the caller's past sessions                    (Landauer et al. 2024 ECVC)
  session_pattern_rarity   the session's operation-type sequence so far (repeats collapsed) is rare
                           among the caller's past sessions                         (Bezerra & Wainer 2013)
  peer_next_tool           next tool given the previous two, pooled over the caller's tool-peers
                                                                                    (Nolle et al. 2018, t-STIDE+)
  pair_gap_unusual         the gap between this pair of consecutive tools is outside its usual range
                           for the caller                                           (Landauer 2024 event timing)
  tool_rate_1m             calls of THIS tool by the caller in the last minute       (CloudTrail Insights per-API rate)
  context_new_on_write     a (client family, user-agent family, /16) combination new for the caller in
                           7 days, at a write or remove                             (Elastic K8s rule; GuardDuty)
  shared_session_rule      one session with >1 /16 network AND (>1 client family OR >1 user-agent family)
                                                                                    (Splunk session-cookie rule)

Run:  python dims6.py --world w2/<scenario>.csv.gz --server <s> --out <scenario>_q.npz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
from array import array
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

from detectors import Hist, vbin
from world2 import Profile

csv.field_size_limit(10**9)
W, DAY, PEER_K, PAST_SESSIONS, MAX_PREFIX = 90, 86400.0, 5, 200, 8
DIMS6 = ["session_count_distance", "session_pattern_rarity", "peer_next_tool", "pair_gap_unusual",
         "tool_rate_1m", "context_new_on_write", "shared_session_rule"]
OP_CODE = {"metadata": "m", "read": "r", "write": "w", "remove": "x"}


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


class Engine6:
    def __init__(self, profile: Profile):
        self.p = profile
        self.tools = {t: i for i, t in enumerate(profile.tools)}
        self.h = {}
        self.sess = {}
        self.past = defaultdict(lambda: deque(maxlen=PAST_SESSIONS))    # agent -> past session count vectors
        self.prefix = defaultdict(lambda: defaultdict(Counter))         # agent -> length -> prefix counts
        self.n_sessions = defaultdict(int)
        self.df = np.zeros(len(self.tools), np.float32)                 # sessions containing each tool (IDF)
        self.n_all = 0
        self.tri = defaultdict(Counter)                                 # agent -> (p2, p1, tool) counts
        self.tri_n = defaultdict(Counter)                               # agent -> (p2, p1) counts
        self.mix = defaultdict(Counter)
        self.peers = {}
        self.gaps = defaultdict(lambda: deque(maxlen=60))
        self.trate = defaultdict(deque)
        self.ctx_seen = defaultdict(dict)
        self.day = self.week = -1

    def up(self, key, x):
        hist = self.h.get(key)
        if hist is None:
            hist = self.h[key] = Hist(W)
        b = vbin(x)
        s = bits(hist.p_upper(b)) if hist.n >= 20 else 0.0
        hist.add(self.day, b)
        return s

    def close_session(self, st):
        a = st["agent"]
        if st["vec"].sum() > 0:
            self.past[a].append(st["vec"].copy())
            self.df += st["vec"] > 0
            self.n_all += 1
            seq = st["ops"]
            for L in range(1, min(len(seq), MAX_PREFIX) + 1):
                self.prefix[a][L][seq[:L]] += 1
            self.n_sessions[a] += 1

    def new_week(self):
        agents = [a for a in self.mix if sum(self.mix[a].values()) >= 20]
        if 3 <= len(agents) <= 3000:
            tools = sorted({t for a in agents for t in self.mix[a]})
            idx = {t: i for i, t in enumerate(tools)}
            M = np.zeros((len(agents), len(tools)), np.float32)
            for i, a in enumerate(agents):
                for t, c in self.mix[a].items():
                    M[i, idx[t]] = c
            M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
            S = M @ M.T
            np.fill_diagonal(S, -1)
            for i, a in enumerate(agents):
                self.peers[a] = [agents[j] for j in np.argsort(-S[i])[:PEER_K]]

    def score(self, r):
        ts = float(r["ts"])
        day = int(ts // DAY)
        if day != self.day:
            for hst in self.h.values():
                hst.expire(day)
            self.day = day
            if day // 7 != self.week:
                self.week = day // 7
                self.new_week()
        a, sid, method = r["agent"], r["session"], r["method"]
        out = dict.fromkeys(DIMS6, 0.0)
        st = self.sess.get(sid)
        if st is None:
            for old_sid in [s for s, x in self.sess.items() if x["agent"] == a]:
                self.close_session(self.sess.pop(old_sid))      # a new session closes the caller's older ones
            st = self.sess[sid] = {"agent": a, "vec": np.zeros(len(self.tools), np.float32), "ops": "",
                                   "prev": ("<s>", "<s>"), "last_ts": None, "nets": set(), "fams": set(),
                                   "uas": set()}
        net = ".".join(r["address"].split(".")[:2])
        fam, uaf = r["client"].split("/")[0], r["ua"].split("/")[0]
        st["nets"].add(net)
        st["fams"].add(fam)
        st["uas"].add(uaf)
        if len(st["nets"]) > 1 and (len(st["fams"]) > 1 or len(st["uas"]) > 1):
            out["shared_session_rule"] = 10.0
        if method != "tools/call":
            return out
        tool = r["tool"]
        op = r["op"] or self.p.op.get(tool, "read")
        # per-tool rate in the last minute
        q = self.trate[(a, tool)]
        q.append(ts)
        while q[0] < ts - 60:
            q.popleft()
        out["tool_rate_1m"] = self.up(("trate", a), len(q))
        # new client/network combination at a write or remove
        ctx = (fam, uaf, net)
        seen = self.ctx_seen[a]
        if ctx not in seen or seen[ctx][0] < ts - 90 * DAY:
            seen[ctx] = [ts, False]                     # [first seen, has written from it]
        first, wrote = seen[ctx]
        if op in ("write", "remove") and not wrote and len(seen) > 1 and ts - first < 7 * DAY:
            out["context_new_on_write"] = 8.0          # first write from a client/network seen < 7 days
        if op in ("write", "remove"):
            seen[ctx][1] = True
        # session count vector vs the caller's nearest past session (IDF-weighted)
        if tool in self.tools:
            st["vec"][self.tools[tool]] += 1
        past = self.past[a]
        if len(past) >= 20:
            idf = np.log((self.n_all + 1) / (self.df + 1)) + 1
            P = np.stack(past)
            d = float(np.min(np.abs(P - st["vec"]) @ idf))
            out["session_count_distance"] = self.up(("ecvc", a), d)
        # rarity of the operation-type sequence so far (consecutive repeats collapsed)
        code = OP_CODE.get(op, "r")
        if not st["ops"] or st["ops"][-1] != code:
            st["ops"] += code
        n = self.n_sessions[a]
        L = len(st["ops"])
        if n >= 20 and L <= MAX_PREFIX:
            out["session_pattern_rarity"] = bits((self.prefix[a][L][st["ops"]] + 1) / (n + 1))
        # next tool given the previous two, pooled over the caller's tool-peers
        p2, p1 = st["prev"]
        peers = self.peers.get(a, [])
        if peers:
            c = sum(self.tri[q2][(p2, p1, tool)] for q2 in peers)
            m = sum(self.tri_n[q2][(p2, p1)] for q2 in peers)
            if m >= 10:
                out["peer_next_tool"] = bits((c + 1) / (m + len(self.tools)))
        self.tri[a][(p2, p1, tool)] += 1
        self.tri_n[a][(p2, p1)] += 1
        self.mix[a][tool] += 1
        # gap between this pair of consecutive tools, against its usual range for the caller
        if st["last_ts"] is not None:
            g = ts - st["last_ts"]
            hist = self.gaps[(a, p1, tool)]
            if len(hist) >= 20:
                rank = (sum(1 for x in hist if x <= g) + 0.5) / (len(hist) + 1)
                out["pair_gap_unusual"] = bits(2 * min(rank, 1 - rank))
            hist.append(g)
        st["prev"] = (p1, tool)
        st["last_ts"] = ts
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine6(Profile(a.server))
    cols = {d: array("f") for d in DIMS6}
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            o = eng.score(r)
            for d in DIMS6:
                cols[d].append(o[d])
    arr = np.stack([np.frombuffer(cols[d], dtype=np.float32) for d in DIMS6], 1)
    np.savez_compressed(a.out, scores=arr, cols=np.array(DIMS6))
    print(f"{a.world.name}: {arr.shape[0]:,} messages x {arr.shape[1]} research dimensions -> {a.out.name}")


if __name__ == "__main__":
    main()
