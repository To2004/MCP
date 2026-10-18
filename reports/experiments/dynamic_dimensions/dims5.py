"""More high-level dimensions (no tool inputs, no specific asset, client/network only in general form).

  call_without_list        a tools/call in a session that never sent tools/list (priced by how often
                           this agent does that)                                   (protocol, MCP-specific)
  call_without_init        a tools/call in a session that never sent initialize      (protocol, MCP-specific)
  tool_recency_gap         days since this agent last used this tool              (Sentinel LastTimeUserPerformedAction)
  op_escalation_session    highest operation reached in the session: metadata < read < write < remove
  read_to_write_fast       a write/remove arriving unusually soon after the session's last read
                                                                                   (OWASP API6 flow-completion time)
  session_tool_diversity   distinct tools in the session                           (Tan & Kumar width)
  session_duration         seconds since the session started                       (Tan & Kumar totalTime)
  write_share_today        today's share of write/remove calls
  tool_periodicity         regularity of the gaps between this agent's calls of the same tool (1/CV)
                                                                                   (PUBCRAWL / periodicity)
  peer_deviation_week      distance of this week's tool mix from tool-peers' mix (peer group analysis,
                           Bolton & Hand; peers learned from TOOL usage only)
  tool_new_tool_peer_rare  first use of a tool, priced by how many tool-peers use it
  networks_in_session      distinct /16 network ranges inside one session          (Tan & Kumar MultiIP, generalised)
  networks_1h              distinct /16 network ranges used by the agent in the last hour
  client_families_1h       distinct client software families used by the agent in the last hour

Same rows as dims2/3/4; eval2.py merges this file (<scenario>_p.npz).

Run:  python dims5.py --world w2/<scenario>.csv.gz --server <s> --out <scenario>_p.npz
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
W, DAY, PEER_K = 90, 86400.0, 5
OP_LEVEL = {"metadata": 0, "read": 1, "write": 2, "remove": 3}
DIMS5 = ["call_without_list", "call_without_init", "tool_recency_gap", "op_escalation_session",
         "read_to_write_fast", "session_tool_diversity", "session_duration", "write_share_today",
         "tool_periodicity", "peer_deviation_week", "tool_new_tool_peer_rare", "networks_in_session",
         "networks_1h", "client_families_1h"]


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


class Engine5:
    def __init__(self, profile: Profile):
        self.p = profile
        self.h = {}
        self.sess = {}
        self.rate = defaultdict(lambda: [0, 0])
        self.tool_last = {}
        self.tool_gaps = defaultdict(lambda: deque(maxlen=12))
        self.q = defaultdict(lambda: defaultdict(deque))
        self.today = {}
        self.dhist = defaultdict(lambda: deque(maxlen=90))
        self.week_mix = defaultdict(Counter)
        self.all_mix = defaultdict(Counter)
        self.peers = {}
        self.tool_users = defaultdict(dict)
        self.seen_tool = defaultdict(set)
        self.dev_hist = defaultdict(lambda: deque(maxlen=26))
        self.day = self.week = -1

    def up(self, key, x):
        hist = self.h.get(key)
        if hist is None:
            hist = self.h[key] = Hist(W)
        b = vbin(x)
        s = bits(hist.p_upper(b)) if hist.n >= 20 else 0.0
        hist.add(self.day, b)
        return s

    def win(self, a, name, ts, span, x):
        dq = self.q[a][name]
        dq.append((ts, x))
        while dq[0][0] < ts - span:
            dq.popleft()
        return dq

    def priced(self, a, kind, hit):
        r = self.rate[(kind, a)]
        s = bits((r[1] + 1) / (r[0] + 1)) if hit and r[0] >= 20 else 0.0
        r[0] += 1
        r[1] += hit
        return s

    def new_week(self, week):
        agents = [a for a in self.all_mix if sum(self.all_mix[a].values()) >= 20]
        tools = sorted({t for a in agents for t in self.all_mix[a]})
        if len(agents) >= 3 and len(agents) <= 3000:
            idx = {t: i for i, t in enumerate(tools)}
            M = np.zeros((len(agents), len(tools)), np.float32)
            for i, a in enumerate(agents):
                for t, c in self.all_mix[a].items():
                    M[i, idx[t]] = c
            M /= M.sum(1, keepdims=True) + 1e-9
            N = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
            S = N @ N.T
            np.fill_diagonal(S, -1)
            for i, a in enumerate(agents):
                self.peers[a] = [agents[j] for j in np.argsort(-S[i])[:PEER_K]]
            # weekly deviation of each agent's last-week mix from its peers' all-time mix
            for i, a in enumerate(agents):
                wm = self.week_mix.get(a)
                if not wm or sum(wm.values()) < 10:
                    continue
                v = np.zeros(len(tools), np.float32)
                for t, c in wm.items():
                    if t in idx:
                        v[idx[t]] = c
                v /= v.sum() + 1e-9
                peer_rows = [agents.index(q) for q in self.peers[a]]
                centroid = M[peer_rows].mean(0)
                self.dev_hist[a].append(float(0.5 * np.abs(v - centroid).sum()))
        self.week_mix = defaultdict(Counter)
        self.week = week

    def score(self, r):
        ts = float(r["ts"])
        day = int(ts // DAY)
        if day != self.day:
            for hst in self.h.values():
                hst.expire(day)
            self.day = day
            if day // 7 != self.week:
                self.new_week(day // 7)
        a, sid, method = r["agent"], r["session"], r["method"]
        out = dict.fromkeys(DIMS5, 0.0)
        st = self.sess.get(sid)
        if st is None:
            st = self.sess[sid] = {"init": False, "list": False, "start": ts, "tools": set(), "maxop": -1,
                                   "last_read": None, "nets": set(), "counted": False}
        net = ".".join(r["address"].split(".")[:2])
        st["nets"].add(net)
        out["networks_in_session"] = float(len(st["nets"]) - 1)
        out["networks_1h"] = self.up(("nets", a), len({x for _, x in self.win(a, "nets", ts, 3600, net)}))
        fam = r["client"].split("/")[0]
        out["client_families_1h"] = self.up(("fams", a), len({x for _, x in self.win(a, "fams", ts, 3600, fam)}))
        if method == "initialize":
            st["init"] = True
        elif method == "tools/list":
            st["list"] = True
        if method != "tools/call":
            return out
        tool = r["tool"]
        op = r["op"] or self.p.op.get(tool, "read")
        if not st["counted"]:                       # protocol checks are priced once per session
            st["counted"] = True
            out["call_without_list"] = self.priced(a, "nolist", not st["list"])
            out["call_without_init"] = self.priced(a, "noinit", not st["init"])
        last = self.tool_last.get((a, tool))
        if last is not None:
            gap = ts - last
            out["tool_recency_gap"] = self.up(("trec", a), gap / DAY) if gap > DAY else 0.0
            g = self.tool_gaps[(a, tool)]
            g.append(gap)
            if len(g) >= 8:
                m = sum(g) / len(g)
                sd = math.sqrt(sum((x - m) ** 2 for x in g) / len(g))
                out["tool_periodicity"] = self.up(("tper", a), min(50.0, m / (sd + 1e-3)))
        self.tool_last[(a, tool)] = ts
        lvl = OP_LEVEL.get(op, 1)
        if lvl > st["maxop"]:
            st["maxop"] = lvl
            out["op_escalation_session"] = self.up(("opesc", a), 4 * lvl)
        if lvl >= 2 and st["last_read"] is not None:
            fast = 1.0 / max(ts - st["last_read"], 0.05)
            out["read_to_write_fast"] = self.up(("r2w", a), 10 * fast)
        if lvl <= 1:
            st["last_read"] = ts
        st["tools"].add(tool)
        out["session_tool_diversity"] = self.up(("sdiv", a), len(st["tools"]))
        out["session_duration"] = self.up(("sdur", a), (ts - st["start"]) / 60)
        td = self.today.get(a)
        if td is None or td["day"] != day:
            if td is not None and td["n"] >= 5:
                self.dhist[a].append(td["w"] / td["n"])
            td = self.today[a] = {"day": day, "n": 0, "w": 0}
        td["n"] += 1
        td["w"] += lvl >= 2
        hist = self.dhist[a]
        if td["n"] >= 5 and len(hist) >= 10:
            share = td["w"] / td["n"]
            out["write_share_today"] = bits((sum(1 for v in hist if v >= share) + 1) / (len(hist) + 1))
        dev = self.dev_hist.get(a)
        if dev and len(dev) >= 4:
            cur = dev[-1]
            out["peer_deviation_week"] = bits((sum(1 for v in list(dev)[:-1] if v >= cur) + 1) / len(dev))
        if tool not in self.seen_tool[a]:
            peers = self.peers.get(a, [])
            if peers and len(self.seen_tool[a]) >= 3:
                pu = sum(1 for q in peers if self.tool_users[tool].get(q, -10**9) > day - W)
                out["tool_new_tool_peer_rare"] = bits((pu + 1) / (len(peers) + 1))
            self.seen_tool[a].add(tool)
        self.tool_users[tool][a] = day
        self.week_mix[a][tool] += 1
        self.all_mix[a][tool] += 1
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine5(Profile(a.server))
    cols = {d: array("f") for d in DIMS5}
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            o = eng.score(r)
            for d in DIMS5:
                cols[d].append(o[d])
    arr = np.stack([np.frombuffer(cols[d], dtype=np.float32) for d in DIMS5], 1)
    np.savez_compressed(a.out, scores=arr, cols=np.array(DIMS5))
    print(f"{a.world.name}: {arr.shape[0]:,} messages x {arr.shape[1]} more high-level dimensions -> {a.out.name}")


if __name__ == "__main__":
    main()
