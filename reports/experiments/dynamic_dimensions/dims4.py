"""High-level ("coarse") dimensions: never look inside a call.

Allowed: which tool, its operation (read / write / remove / metadata) and static impact, the TYPE of
asset the tool works on (derived from the tool's name: search_repositories -> repository,
create-event -> event), time, volume, sessions, and the client and network only in a general
form (client software family without version, user-agent family, /16 network range).
Not allowed: tool inputs of any kind, the specific asset, exact addresses or version strings.

Same rows as dims2/dims3; eval2.py merges this file (<scenario>_h.npz) into the scenario.

Run:  python dims4.py --world w2/<scenario>.csv.gz --server <s> --out <scenario>_h.npz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
import re
from array import array
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

from detectors import Hist, vbin
from world2 import Profile

csv.field_size_limit(10**9)
W, DAY = 90, 86400.0
VERBS = {"get", "list", "search", "create", "update", "delete", "add", "merge", "push", "fork", "mark",
         "join", "leave", "me", "respond", "to", "manage", "or", "current"}
DIMS4 = ["asset_type_new", "asset_type_new_org_rare", "asset_types_today", "tool_new_org_rare",
         "writes_today", "removes_today", "impact_sum_today", "distinct_tools_today", "tool_repeat_10m",
         "tool_repeat_in_session", "client_family_new", "ua_family_new", "network_range_new"]


def asset_type(tool: str) -> str:
    """The kind of thing a tool works on, from its name alone (no inputs)."""
    toks = [t for t in re.split(r"[_\-]", tool.lower()) if t]
    if "pull" in toks:
        return "pull_request"
    nouns = [t for t in toks if t not in VERBS] or toks[-1:]
    n = nouns[0]
    if n.endswith("ies"):
        return n[:-3] + "y"
    return n[:-1] if n.endswith("s") and not n.endswith("ss") else n


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


class Engine4:
    def __init__(self, profile: Profile):
        self.p = profile
        self.h = {}
        self.seen = defaultdict(dict)
        self.rate = defaultdict(lambda: [0, 0])
        self.users = defaultdict(dict)          # (kind, value) -> agent -> last day (org-wide use)
        self.agents_seen = {}
        self.today = {}
        self.dhist = defaultdict(lambda: defaultdict(lambda: deque(maxlen=90)))
        self.q = defaultdict(deque)
        self.sess = defaultdict(lambda: defaultdict(int))
        self.day = -1

    def up(self, key, x):
        hist = self.h.get(key)
        if hist is None:
            hist = self.h[key] = Hist(W)
        b = vbin(x)
        s = bits(hist.p_upper(b)) if hist.n >= 20 else 0.0
        hist.add(self.day, b)
        return s

    def novel(self, kind, a, value, day):
        seen = self.seen[(kind, a)]
        last = seen.get(value)
        new = last is None or last <= day - W
        r = self.rate[(kind, a)]
        s = bits((r[1] + 1) / (r[0] + 1)) if new and r[0] >= 20 else 0.0
        r[0] += 1
        r[1] += new
        seen[value] = day
        return s, new

    def org_rare(self, kind, value, day):
        users = self.users[(kind, value)]
        live = sum(1 for d in users.values() if d > day - W)
        active = sum(1 for d in self.agents_seen.values() if d > day - W)
        return bits((live + 1) / (active + 1))

    def daily(self, a, name, x):
        hist = self.dhist[a][name]
        return bits((sum(1 for v in hist if v >= x) + 1) / (len(hist) + 1)) if len(hist) >= 10 else 0.0

    def score(self, r):
        ts = float(r["ts"])
        day = int(ts // DAY)
        if day != self.day:
            for hst in self.h.values():
                hst.expire(day)
            self.day = day
        a, method = r["agent"], r["method"]
        self.agents_seen[a] = day
        out = dict.fromkeys(DIMS4, 0.0)
        out["client_family_new"] = self.novel("family", a, r["client"].split("/")[0], day)[0]
        out["ua_family_new"] = self.novel("ua", a, r["ua"].split("/")[0], day)[0]
        out["network_range_new"] = self.novel("net", a, ".".join(r["address"].split(".")[:2]), day)[0]
        if method != "tools/call":
            return out
        tool = r["tool"]
        op = r["op"] or self.p.op.get(tool, "read")
        kind = asset_type(tool)
        td = self.today.get(a)
        if td is None or td["day"] != day:
            if td is not None:
                for k in ("writes", "removes", "impact"):
                    self.dhist[a][k].append(td[k])
                self.dhist[a]["tools"].append(len(td["tools"]))
                self.dhist[a]["types"].append(len(td["types"]))
            td = self.today[a] = {"day": day, "writes": 0, "removes": 0, "impact": 0, "tools": set(), "types": set()}
        td["writes"] += op == "write"
        td["removes"] += op == "remove"
        td["impact"] += self.p.impact.get(tool, 3)
        td["tools"].add(tool)
        td["types"].add(kind)
        out["writes_today"] = self.daily(a, "writes", td["writes"]) if op == "write" else 0.0
        out["removes_today"] = self.daily(a, "removes", td["removes"]) if op == "remove" else 0.0
        out["impact_sum_today"] = self.daily(a, "impact", td["impact"])
        out["distinct_tools_today"] = self.daily(a, "tools", len(td["tools"]))
        out["asset_types_today"] = self.daily(a, "types", len(td["types"]))
        s, new = self.novel("type", a, kind, day)
        out["asset_type_new"] = s
        if new:
            out["asset_type_new_org_rare"] = self.org_rare("type", kind, day)
        self.users[("type", kind)][a] = day
        s, new = self.novel("tool", a, tool, day)
        if new:
            out["tool_new_org_rare"] = self.org_rare("tool", tool, day)
        self.users[("tool", tool)][a] = day
        q = self.q[a]
        q.append((ts, tool))
        while q[0][0] < ts - 600:
            q.popleft()
        out["tool_repeat_10m"] = self.up(("trep", a), sum(1 for _, t in q if t == tool))
        self.sess[r["session"]][tool] += 1
        out["tool_repeat_in_session"] = self.up(("treps", a), self.sess[r["session"]][tool])
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine4(Profile(a.server))
    cols = {d: array("f") for d in DIMS4}
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            o = eng.score(r)
            for d in DIMS4:
                cols[d].append(o[d])
    arr = np.stack([np.frombuffer(cols[d], dtype=np.float32) for d in DIMS4], 1)
    np.savez_compressed(a.out, scores=arr, cols=np.array(DIMS4))
    print(f"{a.world.name}: {arr.shape[0]:,} messages x {arr.shape[1]} high-level dimensions -> {a.out.name}")


if __name__ == "__main__":
    main()
