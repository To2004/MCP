"""A large, server-agnostic pool of request-side dimensions, scored on world2 traffic.

Every dimension reads only what an agent->server message carries (gateway-log/2 fields) and
the static scan's labels: tool operation (read/write/remove/metadata) and each kept input's
effect (which/how_much/who/when/action/carried). No roles, teams or server replies are used:
"peers" are learned each week as the k agents whose tool+asset usage is most similar (cosine).
Each call is scored against history BEFORE it, then remembered. Scores are surprise in bits
(or a raw statistic that evaluation ranks against its own past; both are fine).

Run:  python dims2.py --world w2/<scenario>.csv.gz --out <scores>.npz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from detectors import Hist, vbin
from world2 import Profile, START

csv.field_size_limit(10**9)
W = 90                      # days of history per reference
PEER_K = 5
MAX_PEER_AGENTS = 3000
DAY = 86400.0
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

DIMS = [
    # volume / time
    "rate_1m", "rate_10m", "rate_1h", "calls_today", "sessions_1h", "burstiness_cv", "reach_today",
    # repetition
    "identical_10m", "identical_in_session",
    # size, via static input effects
    "how_much_value", "when_span", "who_count", "who_new", "request_bytes", "arg_keys_new", "action_value_new",
    # scope (which)
    "which_new", "which_new_peer_rare", "which_new_org_rare", "which_per_session", "which_per_day",
    "sens_above_own_max", "tool_asset_pair_new",
    # order
    "next_tool_self", "next_tool_peer", "next_tool_trigram", "op_transition", "write_first", "session_length",
    "tool_new_peer_rare",
    # time
    "hour_of_week", "dormancy",
    # wire / protocol
    "address_new", "addresses_1h", "client_new", "user_agent_new", "parallel_sessions", "call_without_list",
    "call_without_init", "inits_1h", "cancels_1h",
    # drift (weekly, anchored)
    "tool_mix_shift_week", "scope_shift_week",
]


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


class Novelty:
    """First-seen test with the agent's own base rate of novelty as the price."""
    def __init__(self):
        self.seen = defaultdict(dict)        # agent -> value -> last day
        self.rate = defaultdict(lambda: [0, 0])

    def score(self, agent, value, day):
        d = self.seen[agent].get(value)
        novel = d is None or d <= day - W
        n, k = self.rate[agent]
        s = bits((k + 1) / (n + 1)) if novel and n >= 20 else 0.0
        return novel, s

    def add(self, agent, value, day, novel):
        self.seen[agent][value] = day
        r = self.rate[agent]
        r[0] += 1
        r[1] += novel


class Engine:
    def __init__(self, profile: Profile):
        self.p = profile
        self.h = {}
        self.nov = defaultdict(Novelty)
        self.win = defaultdict(lambda: defaultdict(deque))   # agent -> name -> deque[(ts, x)]
        self.sess = {}
        self.today = {}
        self.last_ts = {}
        self.maxsens = defaultdict(deque)
        self.trans_self = defaultdict(Counter)
        self.trans_self_n = defaultdict(Counter)
        self.trans_all = defaultdict(Counter)                # (a->b) per agent kept for peers
        self.tri = Counter()
        self.tri_n = Counter()
        self.usage = defaultdict(Counter)                    # agent -> tool/asset counts (for peers)
        self.peers = {}
        self.peer_day = -1
        self.touch = defaultdict(dict)                       # asset -> agent -> day
        self.tool_users = defaultdict(dict)                  # tool -> agent -> day
        self.week = {}
        self.anchor = {}
        self.day = -1

    def H(self, key):
        x = self.h.get(key)
        if x is None:
            x = self.h[key] = Hist(W)
        return x

    def up(self, key, value, pend):
        b = vbin(value)
        hist = self.H(key)
        s = bits(hist.p_upper(b)) if hist.n >= 20 else 0.0
        pend.append((hist, b))
        return s

    def window(self, agent, name, ts, span, x=1):
        q = self.win[agent][name]
        q.append((ts, x))
        while q and q[0][0] < ts - span:
            q.popleft()
        return q

    def roll(self, day):
        for x in self.h.values():
            x.expire(day)
        if day // 7 != self.peer_day // 7 or self.peer_day < 0:
            self.peer_day = day
            self._recompute_peers()

    def _recompute_peers(self):
        agents = list(self.usage)
        if len(agents) < 3:
            return
        if len(agents) > MAX_PEER_AGENTS:      # no stable identity (e.g. one id per session): peers are meaningless
            self.peers = {}
            return
        keys = sorted({k for a in agents for k in self.usage[a]})
        idx = {k: i for i, k in enumerate(keys)}
        M = np.zeros((len(agents), len(keys)), np.float32)
        for i, a in enumerate(agents):
            for k, v in self.usage[a].items():
                M[i, idx[k]] = math.log1p(v)
        M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
        S = M @ M.T
        np.fill_diagonal(S, -1)
        for i, a in enumerate(agents):
            self.peers[a] = [agents[j] for j in np.argsort(-S[i])[:PEER_K]]

    # ------------------------------------------------------------------ one message
    def score(self, r):
        ts = float(r["ts"])
        day = int(ts // DAY)
        if day != self.day:
            self.roll(day)
            self.day = day
        a, sid, method, tool = r["agent"], r["session"], r["method"], r["tool"]
        out = dict.fromkeys(DIMS, 0.0)
        pend = []
        nov_pend = []
        # ---------------- session + wire state for every message
        st = self.sess.get(sid)
        if st is None:
            st = self.sess[sid] = {"agent": a, "init": False, "list": False, "calls": 0, "prev": "<start>",
                                   "prev2": "<start>", "prevop": "<start>", "which": set(), "canon": Counter(),
                                   "read": False}
            q = self.window(a, "sessions", ts, 3600)
            out["sessions_1h"] = self.up(("sessions_1h", a), len(q), pend)
        last = self.last_ts.get(a)
        if last is not None and ts - last > DAY:
            out["dormancy"] = self.up(("dormancy", a), (ts - last) / DAY, pend)
        self.last_ts[a] = ts
        for name, val in (("address_new", r["address"]), ("client_new", r["client"]), ("user_agent_new", r["ua"])):
            novel, s = self.nov[name].score(a, val, day)
            out[name] = s
            nov_pend.append((name, a, val, novel))
        qa = self.window(a, "addr", ts, 3600, r["address"])
        out["addresses_1h"] = self.up(("addresses_1h", a), len({x for _, x in qa}), pend)
        qs = self.window(a, "live_sessions", ts, 600, sid)
        out["parallel_sessions"] = self.up(("parallel", a), len({x for _, x in qs}), pend)
        if method == "initialize":
            st["init"] = True
            q = self.window(a, "inits", ts, 3600)
            out["inits_1h"] = self.up(("inits_1h", a), len(q), pend)
        elif method == "tools/list":
            st["list"] = True
        elif method == "notifications/cancelled":
            q = self.window(a, "cancels", ts, 3600)
            out["cancels_1h"] = self.up(("cancels_1h", a), len(q), pend)
        if method == "tools/call":
            self._call(r, ts, day, a, st, tool, out, pend, nov_pend)
        # ---------------- remember
        for hist, b in pend:
            hist.add(day, b)
        for name, ag, val, novel in nov_pend:
            self.nov[name].add(ag, val, day, novel)
        return out

    def _call(self, r, ts, day, a, st, tool, out, pend, nov_pend):
        p = self.p
        args = json.loads(r["args"]) if r["args"] else {}
        op = r["op"] or p.op.get(tool, "read")
        which = r["which"]
        canon = tool + r["args"]
        st["calls"] += 1
        # volume
        for name, span in (("rate_1m", 60), ("rate_10m", 600), ("rate_1h", 3600)):
            out[name] = self.up((name, a), len(self.window(a, name, ts, span)), pend)
        td = self.today.get(a)
        if td is None or td["day"] != day:
            if td is not None:
                for k in ("calls", "reach"):
                    self.H(("hist_" + k, a)).add(day, vbin(td[k]))
                self.H(("hist_wpd", a)).add(day, vbin(len(td["which"])))
            td = self.today[a] = {"day": day, "calls": 0, "reach": 0.0, "which": set()}
        td["calls"] += 1
        hm = []
        for k in p.keys(tool, "how_much"):
            v = args.get(k)
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                hm.append(float(v))
            elif isinstance(v, list):
                hm.append(float(len(v)))
        td["reach"] += max(hm) if hm else 1.0
        if which:
            td["which"].add(which)

        def daily(key, x):
            hist = self.H(("hist_" + key, a))
            return bits(hist.p_upper(vbin(x))) if hist.n >= 10 else 0.0
        out["calls_today"] = daily("calls", td["calls"])
        out["reach_today"] = daily("reach", td["reach"])
        out["which_per_day"] = daily("wpd", len(td["which"]))
        gaps = self.window(a, "gaps", ts, 10 * DAY, ts)
        g = [y - x for (x, _), (y, _) in zip(list(gaps)[-21:-1], list(gaps)[-20:])]
        if len(g) >= 10:
            m = sum(g) / len(g)
            cv = (math.sqrt(sum((x - m) ** 2 for x in g) / len(g)) / m) if m > 0 else 0.0
            out["burstiness_cv"] = self.up(("cv", a), cv * 4, pend)
        # repetition
        q = self.window(a, "canon", ts, 600, canon)
        out["identical_10m"] = self.up(("ident", a), sum(1 for _, c in q if c == canon), pend)
        st["canon"][canon] += 1
        out["identical_in_session"] = self.up(("ident_s", a), st["canon"][canon], pend)
        # size, via effects
        if hm:
            out["how_much_value"] = self.up(("hm", a, tool), max(hm), pend)
        span = self._span(tool, args, ts)
        if span is not None:
            out["when_span"] = self.up(("span", a, tool), span, pend)
        who = self._who(tool, args)
        if who is not None:
            out["who_count"] = self.up(("whoc", a, tool), len(who), pend)
            best = 0.0
            for v in who[:200]:
                novel, s = self.nov["who"].score(a, v, day)
                best = max(best, s)
                nov_pend.append(("who", a, v, novel))
            out["who_new"] = best
        out["request_bytes"] = self.up(("bytes", a, tool), float(r["bytes"]) / 20.0, pend)
        keys = tool + "|" + ",".join(sorted(args))
        novel, s = self.nov["argkeys"].score(a, keys, day)
        out["arg_keys_new"] = s
        nov_pend.append(("argkeys", a, keys, novel))
        best = 0.0
        for k in p.keys(tool, "action"):
            if k in args:
                v = f"{tool}|{k}={json.dumps(args[k], sort_keys=True)[:80]}"
                novel, s = self.nov["action"].score(a, v, day)
                best = max(best, s)
                nov_pend.append(("action", a, v, novel))
        out["action_value_new"] = best
        # scope
        peers = self.peers.get(a, [])
        if which:
            novel, s = self.nov["which"].score(a, which, day)
            out["which_new"] = s
            nov_pend.append(("which", a, which, novel))
            if novel:
                t = self.touch[which]
                live = lambda x: x > day - W
                pt = sum(1 for q2 in peers if live(t.get(q2, -10**9)))
                out["which_new_peer_rare"] = bits((pt + 1) / (len(peers) + 1))
                org = sum(1 for d in t.values() if live(d))
                out["which_new_org_rare"] = bits((org + 1) / (len(self.last_ts) + 1))
            st["which"].add(which)
            out["which_per_session"] = self.up(("wps", a), len(st["which"]), pend)
            sens = int(r["sens"] or 0)
            ms = max((s2 for _, s2 in self.maxsens[a]), default=0)
            out["sens_above_own_max"] = float(max(0, sens - ms)) if self.maxsens[a] else 0.0
            dq = self.maxsens[a]
            if dq and dq[-1][0] == day:
                dq[-1] = (day, max(dq[-1][1], sens))
            else:
                dq.append((day, sens))
            while dq and dq[0][0] <= day - W:
                dq.popleft()
            pair = tool + "|" + which
            novel, s = self.nov["pair"].score(a, pair, day)
            out["tool_asset_pair_new"] = s
            nov_pend.append(("pair", a, pair, novel))
            self.touch[which][a] = day
            self.usage[a]["A:" + which] += 1
        # order
        prev, prev2 = st["prev"], st["prev2"]
        ts_ = self.trans_self[a]
        n_prev = self.trans_self_n[a][prev]
        peer_c = sum(self.trans_self[q2][(prev, tool)] for q2 in peers)
        peer_n = sum(self.trans_self_n[q2][prev] for q2 in peers)
        p_peer = (peer_c + 1) / (peer_n + len(p.tools))
        p_self = (ts_[(prev, tool)] + 20 * p_peer) / (n_prev + 20)
        out["next_tool_self"] = bits(p_self) if n_prev + peer_n >= 10 else 0.0
        out["next_tool_peer"] = bits(p_peer) if peer_n >= 10 else 0.0
        k3 = (prev2, prev, tool)
        n3 = self.tri_n[(prev2, prev)]
        out["next_tool_trigram"] = bits((self.tri[k3] + 1) / (n3 + len(p.tools))) if n3 >= 10 else 0.0
        opk = f"{st['prevop']}>{op}"
        novel, s = self.nov["optrans"].score(a, opk, day)
        out["op_transition"] = s
        nov_pend.append(("optrans", a, opk, novel))
        if st["calls"] == 1:
            wf = op in ("write", "remove")
            n, k = self.nov["wf"].rate[a]
            out["write_first"] = bits((k + 1) / (n + 1)) if wf and n >= 20 else 0.0
            self.nov["wf"].rate[a][0] += 1
            self.nov["wf"].rate[a][1] += wf
        out["session_length"] = self.up(("slen", a), st["calls"], pend)
        novel, _ = self.nov["tool"].score(a, tool, day)
        if novel:
            users = self.tool_users[tool]
            pu = sum(1 for q2 in peers if users.get(q2, -10**9) > day - W)
            out["tool_new_peer_rare"] = bits((pu + 1) / (len(peers) + 1))
        nov_pend.append(("tool", a, tool, novel))
        ts_[(prev, tool)] += 1
        self.trans_self_n[a][prev] += 1
        self.tri[k3] += 1
        self.tri_n[(prev2, prev)] += 1
        self.tool_users[tool][a] = day
        self.usage[a]["T:" + tool] += 1
        st["prev2"], st["prev"], st["prevop"] = prev, tool, op
        # time of week vs own profile (smoothed with everyone's)
        dt = datetime.fromtimestamp(START.timestamp() + ts, timezone.utc)
        how = dt.weekday() * 24 + dt.hour
        hs, ho = self.H(("how", a)), self.H(("how_all",))
        if len(hs.tot) < 168:
            self.h[("how", a)] = hs = Hist(W, 168)
        if len(ho.tot) < 168:
            self.h[("how_all",)] = ho = Hist(W, 168)
        po = (ho.tot[how] + 1) / (ho.n + 168)
        ps = (hs.tot[how] + 50 * po) / (hs.n + 50)
        out["hour_of_week"] = max(0.0, bits(ps) - math.log2(168)) if hs.n >= 50 else 0.0
        pend += [(hs, how), (ho, how)]
        # weekly drift against an anchor re-set every 26 weeks
        wk = day // 7
        w = self.week.get(a)
        if w is None or w["wk"] != wk:
            if w is not None:
                anc = self.anchor.setdefault(a, {"wk": w["wk"], "tools": Counter(), "assets": set(), "n": 0})
                if w["wk"] - anc["wk"] >= 26:
                    anc = self.anchor[a] = {"wk": w["wk"], "tools": Counter(), "assets": set(), "n": 0}
                if anc["n"] < 4:
                    anc["tools"].update(w["tools"])
                    anc["assets"] |= w["assets"]
                    anc["n"] += 1
            w = self.week[a] = {"wk": wk, "tools": Counter(), "assets": set(), "calls": 0, "out": 0}
        w["tools"][tool] += 1
        w["calls"] += 1
        anc = self.anchor.get(a)
        if which:
            w["assets"].add(which)
            if anc and anc["n"] >= 4 and which not in anc["assets"]:
                w["out"] += 1
        if anc and anc["n"] >= 4 and w["calls"] >= 10:
            out["tool_mix_shift_week"] = 10 * js(w["tools"], anc["tools"])
            out["scope_shift_week"] = 10 * w["out"] / w["calls"]

    def _span(self, tool, args, ts):
        dates = []
        for k in self.p.keys(tool, "when"):
            v = args.get(k)
            if isinstance(v, dict):
                v = v.get("dateTime") or v.get("date")
            if isinstance(v, str) and DATE_RE.match(v):
                try:
                    dates.append(datetime.fromisoformat(v.replace("Z", "+00:00")[:25]).timestamp())
                except ValueError:
                    pass
        if not dates:
            return None
        if len(dates) == 1:
            return abs(dates[0] - (START.timestamp() + ts)) / DAY
        return (max(dates) - min(dates)) / DAY

    def _who(self, tool, args):
        out = None
        for k in self.p.keys(tool, "who"):
            v = args.get(k)
            if v is None or isinstance(v, bool):
                continue
            out = out or []
            if isinstance(v, list):
                out += [json.dumps(x, sort_keys=True)[:80] for x in v]
            else:
                out += [s.strip() for s in str(v).split(",") if s.strip()]
        return out


def js(p: Counter, q: Counter) -> float:
    keys = set(p) | set(q)
    sp, sq = sum(p.values()) or 1, sum(q.values()) or 1
    m = {k: (p[k] / sp + q[k] / sq) / 2 for k in keys}
    kl = lambda x, s: sum((x[k] / s) * math.log2((x[k] / s) / m[k]) for k in keys if x[k])
    return 0.5 * kl(p, sp) + 0.5 * kl(q, sq)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine(Profile(a.server))
    S = []
    meta = defaultdict(list)
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            o = eng.score(r)
            S.append([o[d] for d in DIMS])
            for k in ("ts", "agent", "session", "method", "tool", "strange", "legit", "episode", "intensity", "which"):
                meta[k].append(r[k])
    arr = np.asarray(S, np.float32)
    np.savez_compressed(a.out, scores=arr, cols=np.array(DIMS), **{k: np.array(v) for k, v in meta.items()})
    print(f"{a.world.name}: {arr.shape[0]:,} messages x {arr.shape[1]} dimensions -> {a.out.name}")


if __name__ == "__main__":
    main()
