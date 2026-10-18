"""Streaming dimension scores for every call: dimension x reference x window.

Every score is a surprise in bits, s = -log2(p), where p says how ordinary the call's value
is against a reference history. The call is scored first and only then added to history.

Dimensions (request side only; server responses are not used):
  rep        identical calls by this caller in the last 10 minutes
  rate       calls by this caller in the last 60 minutes
  reach      items requested by this caller in the last 24 h (page size for list/search, 1 otherwise)
  breadth    distinct repos touched by this caller in the last 24 h
  asset      first touch of this repo by this caller, priced by how foreign it is
  sensjump   sensitivity above the most sensitive repo this caller (or its team) touched
  tool       first use of this tool by this caller, priced by how rare it is in the role
  order_rule policy workflow rules (merge without review, push to main, repo admin by non-admin)
  order_tr   rarity of the tool-class transition inside the session
  time       hour-of-week (UTC, gateway clock) against the caller's activity profile
  time_cal   same, with public holidays treated as Sundays
  dormancy   days since this caller's previous call
  size       page / per_page values against history for that tool and argument

References: self (the caller), peer (its role; its team for asset and sensjump), org (everyone),
hier (self shrunk toward peer: (n*p_self + K*p_peer)/(n + K)), anchor (asset only: repos
outside the caller's first 60 active days and outside its team).

Run:  python detectors.py --world world_seed1.csv.gz --window 90 --out scores_w90.npz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict, deque
from datetime import timedelta
from pathlib import Path

import numpy as np

from world import DAY, HOLIDAYS, IMPACT, START, TOOL_CLASS

K_SHRINK = 200          # observations of self history that weigh as much as the peer prior
REP_WINDOW, RATE_WINDOW, REACH_WINDOW = 600.0, 3600.0, DAY
SIZE_ARGS = ("page", "per_page", "perPage")
ANCHOR_DAYS = 60
CLASSES = sorted(set(TOOL_CLASS.values())) + ["start"]
CI = {c: i for i, c in enumerate(CLASSES)}
NB = 64


def vbin(x: float) -> int:
    """Quarter-octave bins for counts and sizes."""
    return min(NB - 1, int(4 * math.log2(1 + max(0.0, x))))


class Hist:
    """Day-bucketed histogram over NB bins with an optional sliding window (in days)."""
    __slots__ = ("nb", "tot", "n", "days", "window")

    def __init__(self, window, nb=NB):
        self.nb, self.window = nb, window
        self.tot, self.n = [0] * nb, 0
        self.days = deque()

    def add(self, day, b):
        if not self.days or self.days[-1][0] != day:
            self.days.append((day, defaultdict(int)))
        self.days[-1][1][b] += 1
        self.tot[b] += 1
        self.n += 1

    def expire(self, day):
        if self.window is None:
            return
        while self.days and self.days[0][0] <= day - self.window:
            _, cnt = self.days.popleft()
            for b, c in cnt.items():
                self.tot[b] -= c
                self.n -= c

    def p_upper(self, b):
        """Conformal p-value of a value in bin b: share of history at least as large."""
        return (sum(self.tot[b:]) + 1) / (self.n + 1)

    def p_bin(self, b):
        """Smoothed probability of exactly bin b, relative to uniform (1.0 = average bin)."""
        return (self.tot[b] + 1) / (self.n + self.nb) * self.nb


def bits(p):
    return -math.log2(min(1.0, max(p, 1e-12)))


def hier(n_self, p_self, p_peer):
    return (n_self * p_self + K_SHRINK * p_peer) / (n_self + K_SHRINK)


class Engine:
    def __init__(self, window):
        self.W = window
        self.hists: dict = {}
        self.recent = {}                          # caller -> rolling 10 min / 60 min / 24 h counters
        self.last_seen = {}                       # (caller, repo) -> day
        self.first_day = {}                       # caller -> first active day
        self.anchor = defaultdict(set)            # caller -> repos in first ANCHOR_DAYS
        self.repo_touch = defaultdict(dict)       # (scope, repo) -> {caller: day}
        self.members = defaultdict(dict)          # scope -> {caller: day}
        self.tool_seen = {}                       # (caller, tool) -> day
        self.tool_users = defaultdict(dict)       # (role, tool) -> {caller: day}
        self.maxsens = defaultdict(deque)         # caller / team:<t> -> deque[(day, sens)]
        self.new_rate = defaultdict(lambda: [deque(), 0, 0])   # caller -> [days, calls, firsts]
        self.reviewed = set()                     # (repo, pr) with a review seen
        self.prev_class = {}                      # session -> class
        self.last_ts = {}
        self.day = -1

    # ---------- history helpers ----------
    def H(self, key, nb=NB):
        h = self.hists.get(key)
        if h is None:
            h = self.hists[key] = Hist(self.W, nb)
        return h

    def live(self, d: dict, day):
        return d if self.W is None else {k: v for k, v in d.items() if v > day - self.W}

    def roll(self, day):
        for h in self.hists.values():
            h.expire(day)
        if self.W is not None:
            for dq in self.maxsens.values():
                while dq and dq[0][0] <= day - self.W:
                    dq.popleft()
            for st in self.new_rate.values():
                while st[0] and st[0][0][0] <= day - self.W:
                    _, c, f = st[0].popleft()
                    st[1] -= c
                    st[2] -= f

    def triple(self, dim, caller, peer, b, nb=NB, kind="upper"):
        """Score bin b of dimension dim against self, peer, org and the shrunk self->peer mix."""
        hs, hp, ho = self.H((dim, "s", caller), nb), self.H((dim, "p", peer), nb), self.H((dim, "o"), nb)
        f = (lambda h: h.p_upper(b)) if kind == "upper" else (lambda h: min(1.0, h.p_bin(b) / nb))
        ps, pp, po = f(hs), f(hp), f(ho)
        out = (bits(ps), bits(pp), bits(po), bits(hier(hs.n, ps, pp)))
        return out, (hs, hp, ho)

    # ---------- one call ----------
    def score(self, e):
        ts, caller, role, team, sess, tool, args, repo, sens = e
        day = int(ts // DAY)
        if day != self.day:
            self.roll(day)
            self.day = day
        self.first_day.setdefault(caller, day)
        cls = TOOL_CLASS[tool]
        canon = tool + args
        a = json.loads(args)
        items = float(a.get("per_page") or a.get("perPage") or 30) if cls in ("list", "search") else 1.0
        out = {}
        pend = []                                 # (hist, bin) to add after scoring

        # rolling per-caller windows, kept as running counters
        w = self.recent.get(caller)
        if w is None:
            w = self.recent[caller] = {"q10": deque(), "c10": defaultdict(int), "q60": deque(),
                                       "q24": deque(), "reach": 0.0, "r24": defaultdict(int)}
        w["q10"].append((ts, canon)); w["c10"][canon] += 1
        while w["q10"][0][0] < ts - REP_WINDOW:
            _, c0 = w["q10"].popleft(); w["c10"][c0] -= 1
        w["q60"].append(ts)
        while w["q60"][0] < ts - RATE_WINDOW:
            w["q60"].popleft()
        w["q24"].append((ts, items, repo)); w["reach"] += items
        if repo:
            w["r24"][repo] += 1
        while w["q24"][0][0] < ts - REACH_WINDOW:
            _, i0, r0 = w["q24"].popleft(); w["reach"] -= i0
            if r0:
                w["r24"][r0] -= 1
                if not w["r24"][r0]:
                    del w["r24"][r0]
        rep, rate, reach, breadth = w["c10"][canon], len(w["q60"]), w["reach"], len(w["r24"])
        rq = w["q24"]
        for dim, x in (("rep", rep), ("rate", rate), ("reach", reach), ("breadth", breadth)):
            b = vbin(x)
            sc, hs = self.triple(dim, caller, role, b)
            for ref, v in zip(("self", "peer", "org", "hier"), sc):
                out[f"{dim}.{ref}"] = v
            pend += [(h, b) for h in hs]

        # asset novelty and sensitivity jump
        ls = self.last_seen.get((caller, repo))
        novel = bool(repo) and (ls is None or (self.W is not None and ls <= day - self.W))
        st = self.new_rate[caller]
        p_new = (st[2] + 1) / (st[1] + 1)
        tm = self.live(self.members[team], day)
        touch_t = self.live(self.repo_touch[(team, repo)], day) if repo else {}
        touch_o = self.live(self.repo_touch[("*", repo)], day) if repo else {}
        org_n = len(self.live(self.members["*"], day))
        p_team = (len(touch_t) + 1) / (len(tm) + 1)
        p_org = (len(touch_o) + 1) / (org_n + 1)
        out["asset.self"] = bits(p_new) if novel else 0.0
        out["asset.peer"] = bits(p_team) if repo else 0.0
        out["asset.org"] = bits(p_org) if repo else 0.0
        out["asset.hier"] = bits(hier(st[1], p_new, p_team)) if novel else 0.0
        in_anchor = repo in self.anchor[caller] or bool(touch_t) and len(touch_t) >= max(1, len(tm) // 2)
        out["asset.anchor"] = bits(p_team) if repo and day - self.first_day[caller] >= ANCHOR_DAYS and not in_anchor else 0.0
        ms = max((s for _, s in self.maxsens[caller]), default=0)
        mt = max((s for _, s in self.maxsens["team:" + team]), default=0)
        out["sensjump.self"] = float(max(0, sens - ms)) if self.maxsens[caller] else 0.0
        out["sensjump.peer"] = float(max(0, sens - mt)) if self.maxsens["team:" + team] else 0.0

        # tool novelty, priced by how many role peers use the tool
        tsn = self.tool_seen.get((caller, tool))
        tnovel = tsn is None or (self.W is not None and tsn <= day - self.W)
        users = self.live(self.tool_users[(role, tool)], day)
        rmem = self.live(self.members["role:" + role], day)
        p_role = (len(users) + 1) / (len(rmem) + 1)
        allu = self.live(self.tool_users[("*", tool)], day)
        p_all = (len(allu) + 1) / (org_n + 1)
        n_self_tools = sum(1 for (c, _), d in self.tool_seen.items() if c == caller) if tnovel else 0
        p_self_t = 1 / (n_self_tools + 2)
        out["tool.self"] = bits(p_self_t) if tnovel else 0.0
        out["tool.peer"] = bits(p_role)
        out["tool.org"] = bits(p_all)
        out["tool.hier"] = bits(hier(len(rq), p_self_t, p_role)) if tnovel else 0.0

        # order: written workflow rules, then learned class transitions inside the session
        pr = (repo, a.get("pull_number"))
        rule = 0.0
        if tool == "merge_pull_request" and pr not in self.reviewed:
            rule = 10.0
        if tool in ("push_files", "create_or_update_file") and a.get("branch") in ("main", "master"):
            rule = 10.0
        if cls == "admin" and role != "admin":
            rule = 10.0
        out["order_rule.policy"] = rule
        prev = self.prev_class.get(sess, "start")
        b = CI[prev] * len(CLASSES) + CI[cls]
        nbt = len(CLASSES) ** 2
        sc, hs = self.triple("trans", caller, role, b, nb=nbt, kind="bin")
        # condition on the previous class: renormalise by the row's share
        for ref, v in zip(("self", "peer", "org", "hier"), sc):
            out[f"order_tr.{ref}"] = max(0.0, v - math.log2(len(CLASSES)))
        pend += [(h, b) for h in hs]

        # time of week, with and without the holiday calendar
        dt = START + timedelta(seconds=ts)
        how = dt.weekday() * 24 + dt.hour
        sc, hs = self.triple("time", caller, role, how, nb=168, kind="bin")
        for ref, v in zip(("self", "peer", "org", "hier"), sc):
            out[f"time.{ref}"] = max(0.0, v - math.log2(168))
        pend += [(h, how) for h in hs]
        how_c = 6 * 24 + dt.hour if dt.date() in HOLIDAYS else how
        sc, hs = self.triple("timec", caller, role, how_c, nb=168, kind="bin")
        out["time_cal.hier"] = max(0.0, sc[3] - math.log2(168))
        pend += [(h, how_c) for h in hs]

        # dormancy: only the first call after a gap of more than a day is graded
        gap = (ts - self.last_ts[caller]) / DAY if caller in self.last_ts else 0.0
        if gap > 1.0:
            b = vbin(gap)
            sc, hs = self.triple("dorm", caller, role, b)
            for ref, v in zip(("self", "peer", "org", "hier"), sc):
                out[f"dormancy.{ref}"] = v
            pend += [(h, b) for h in hs]
        else:
            for ref in ("self", "peer", "org", "hier"):
                out[f"dormancy.{ref}"] = 0.0

        # size arguments
        best = [0.0, 0.0, 0.0, 0.0]
        for k in SIZE_ARGS:
            if k in a:
                try:
                    v = float(a[k])
                except (TypeError, ValueError):
                    continue
                b = vbin(v)
                sc, hs = self.triple(f"size:{tool}:{k}", caller, role, b)
                best = [max(x, y) for x, y in zip(best, sc)]
                pend += [(h, b) for h in hs]
        for ref, v in zip(("self", "peer", "org", "hier"), best):
            out[f"size.{ref}"] = v

        # ---------- remember (after scoring) ----------
        for h, b in pend:
            h.add(day, b)
        if repo:
            self.last_seen[(caller, repo)] = day
            self.repo_touch[(team, repo)][caller] = day
            self.repo_touch[("*", repo)][caller] = day
            if day - self.first_day[caller] < ANCHOR_DAYS:
                self.anchor[caller].add(repo)
            for key in (caller, "team:" + team):          # one entry per day: the day's maximum
                dq = self.maxsens[key]
                if dq and dq[-1][0] == day:
                    dq[-1] = (day, max(dq[-1][1], sens))
                else:
                    dq.append((day, sens))
        if not st[0] or st[0][-1][0] != day:
            st[0].append([day, 0, 0])
        st[0][-1][1] += 1
        st[0][-1][2] += int(novel)
        st[1] += 1
        st[2] += int(novel)
        self.members[team][caller] = day
        self.members["*"][caller] = day
        self.members["role:" + role][caller] = day
        self.tool_seen[(caller, tool)] = day
        self.tool_users[(role, tool)][caller] = day
        self.tool_users[("*", tool)][caller] = day
        if tool == "create_pull_request_review":
            self.reviewed.add(pr)
        self.prev_class[sess] = cls
        self.last_ts[caller] = ts
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, required=True)
    ap.add_argument("--window", default="90", help="days, or 'life' for no window")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    eng = Engine(None if a.window == "life" else int(a.window))
    cols, data, meta = None, [], {k: [] for k in ("ts", "caller", "role", "team", "tool", "repo", "sens",
                                                  "strange", "legit", "episode", "session")}
    with gzip.open(a.world, "rt") as fh:
        for r in csv.DictReader(fh):
            e = (float(r["ts"]), r["caller"], r["role"], r["team"], r["session"], r["tool"], r["args"],
                 r["repo"], int(r["sens"]))
            s = eng.score(e)
            if cols is None:
                cols = list(s)
            data.append([s[c] for c in cols])
            for k in meta:
                meta[k].append(r[k])
    arr = np.asarray(data, dtype=np.float32)
    np.savez_compressed(a.out, scores=arr, cols=np.array(cols),
                        **{k: np.array(v) for k, v in meta.items()})
    print(f"{arr.shape[0]:,} calls x {arr.shape[1]} scores -> {a.out}")


if __name__ == "__main__":
    main()
