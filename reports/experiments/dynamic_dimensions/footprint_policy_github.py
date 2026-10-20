"""Footprint as shares, and every policy limit kept but recalibrated (GitHub worlds).

Footprint (learned, the agent against himself only):
    tool_share    p = (his calls of this tool in 90 days + 1) / (his calls + number of tools),
                  surprise -log2 p, times tool impact / 5 (unknown tool = 5)
    asset_share   p = (his calls on this asset in 90 days + 1) / (his asset calls + his distinct
                  assets + 1), times asset sensitivity / 5 (asset not in the register = 5)
A never-used tool or asset is the rarest share, so "new" is the extreme of the same measure.

Policy limits, recalibrated from ordinary traffic (none dropped):
    burst          more than BURST calls in one minute          (was 10; ordinary p99 is 15-16)
    session        session open longer than SESSION_MIN minutes  (was 4 hours; never reached)
    sequences      sensitive read then write to another asset; merge without looking at the pull
                   request first; write to a sensitive asset he has not read in 7 days
                   (was: not read in this session, which fired on 15% of ordinary days)
    new_ip, request over REQUEST_BYTES, call without initialize
Each family carries ONE policy check: 10 bits if any of its limits is broken.

Run:  python footprint_policy_github.py      (writes results/footprint_policy_github.json)
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict, deque
from multiprocessing import Pool

import numpy as np

from detectors import vbin
from policy_github import (DAY, HERE, MIN_HISTORY, NEW_ASSET, ORGS, POLICY_BITS, REVIEW_TOOLS,
                           RUNS, SCAN, SENSITIVE, WORST, Agent, bits, novelty, self_excess)
from vkp_eval import CAL_DAYS, alerts

csv.field_size_limit(10**9)
BURST, SESSION_MIN, REQUEST_BYTES, READ_MEMORY_DAYS, W = 20, 10.0, 10_000, 7, 90
LEARNED = ["calls_1h", "tool_share", "asset_share", "new_tool", "new_asset"]
RAW = ["calls_last_min", "session_min", "seq_read_then_write", "seq_merge_no_review",
       "seq_blind_write_7d", "seq_blind_write_session", "new_ip", "request_big"]
REUSED = {"self/{n}.npz": {"tool_repeat_10m": "repeat_10m", "client_new": "client_new"},
          "w2/{n}_p.npz": {"call_without_init": "call_without_init"}}
LOADS = (2.0, 4.0)


class Shares:
    """Counts of keys over the last W days, for one agent."""

    def __init__(self):
        self.counts, self.total, self.log = Counter(), 0, deque()

    def share_bits(self, key: str, day: int, smooth: int) -> float:
        while self.log and self.log[0][0] <= day - W:
            _, k = self.log.popleft()
            self.counts[k] -= 1
            self.total -= 1
            if not self.counts[k]:
                del self.counts[k]
        s = bits((self.counts[key] + 1) / (self.total + smooth)) if self.total >= MIN_HISTORY else 0.0
        self.counts[key] += 1
        self.total += 1
        self.log.append((day, key))
        return s


def extract(name: str, impacts: dict[str, int]):
    agents: dict[str, Agent] = defaultdict(Agent)
    tools: dict[str, Shares] = defaultdict(Shares)
    assets: dict[str, Shares] = defaultdict(Shares)
    last_read: dict[tuple[str, str], int] = {}
    sessions: dict[str, dict] = {}
    cols = LEARNED + RAW
    out = {c: [] for c in cols}
    meta = {k: [] for k in ("ts", "agent", "strange", "episode")}
    with gzip.open(HERE / "w2" / f"{name}.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            ts = float(r["ts"])
            day = int(ts // DAY)
            a, st = r["agent"], agents[r["agent"]]
            row = dict.fromkeys(cols, 0.0)
            sess = sessions.setdefault(r["session"], {"start": ts, "read_sens": set(), "read": set(),
                                                      "review": False})
            row["new_ip"] = POLICY_BITS if novelty(st, "ip", r["address"], day) > 0 else 0.0
            if r["method"] == "tools/call":
                tool, op, asset, sens = r["tool"], r["op"], r["which"], int(r["sens"] or 0)
                st.calls.append(ts)
                while st.calls[0] < ts - 3600:
                    st.calls.popleft()
                st.hist_1h.expire(day)
                b = vbin(len(st.calls))
                if st.hist_1h.n >= MIN_HISTORY:
                    row["calls_1h"] = bits(st.hist_1h.p_upper(b))
                st.hist_1h.add(day, b)
                row["calls_last_min"] = sum(1 for t in st.calls if t >= ts - 60)
                row["session_min"] = (ts - sess["start"]) / 60
                row["request_big"] = POLICY_BITS if int(r["bytes"] or 0) > REQUEST_BYTES else 0.0
                weight_t = impacts.get(tool, WORST) / WORST
                row["tool_share"] = tools[a].share_bits(tool, day, len(impacts)) * weight_t
                row["new_tool"] = novelty(st, "tool", tool, day) * weight_t
                if asset and asset != "null" and sens > 0:
                    level = WORST if NEW_ASSET.search(asset) else sens
                    shares = assets[a]
                    row["asset_share"] = shares.share_bits(asset, day, len(shares.counts) + 1) * level / WORST
                    row["new_asset"] = novelty(st, "asset", asset, day) * level / WORST
                    if op == "write" and sess["read_sens"] - {asset}:
                        row["seq_read_then_write"] = POLICY_BITS
                    if op == "write" and level >= SENSITIVE:
                        if asset not in sess["read"]:
                            row["seq_blind_write_session"] = POLICY_BITS
                        if last_read.get((a, asset), -10**6) < day - READ_MEMORY_DAYS:
                            row["seq_blind_write_7d"] = POLICY_BITS
                    if op in ("read", "metadata"):
                        sess["read"].add(asset)
                        last_read[(a, asset)] = day
                        if level >= SENSITIVE:
                            sess["read_sens"].add(asset)
                if tool == "merge_pull_request" and not sess["review"]:
                    row["seq_merge_no_review"] = POLICY_BITS
                if tool in REVIEW_TOOLS:
                    sess["review"] = True
            for c in cols:
                out[c].append(row[c])
            for k, v in (("ts", ts), ("agent", a), ("strange", r["strange"]), ("episode", r["episode"])):
                meta[k].append(v)
    X = np.array([out[c] for c in cols], dtype=np.float32).T
    return cols, X, {k: np.array(v) for k, v in meta.items()}


def evaluate(name: str) -> dict:
    impacts = {t["tool"]: t["impact"] for t in json.loads(SCAN.read_text())["tools"]}
    cols, X, meta = extract(name, impacts)
    for pattern, dims in REUSED.items():
        f = np.load(RUNS / pattern.format(n=name))
        fc = [str(c) for c in f["cols"]]
        X = np.concatenate([X, np.stack([f["scores"][:, fc.index(s)] for s in dims], 1)], 1)
        cols += list(dims.values())
    col = {c: i for i, c in enumerate(cols)}
    day = (meta["ts"] // DAY).astype(int)
    _, ident = np.unique(meta["agent"], return_inverse=True)
    learned = LEARNED + ["repeat_10m", "client_new"]
    xl = self_excess(X[:, [col[c] for c in learned]], day, ident)
    sig = {c: xl[:, i] for i, c in enumerate(learned)}
    raw = {c: X[:, col[c]] for c in RAW + ["call_without_init"]}
    pb = POLICY_BITS
    sig["burst_10"] = np.where(raw["calls_last_min"] > 10, pb, 0.0)
    sig["burst_20"] = np.where(raw["calls_last_min"] > BURST, pb, 0.0)
    sig["session_4h"] = np.where(raw["session_min"] > 240, pb, 0.0)
    sig["session_10m"] = np.where(raw["session_min"] > SESSION_MIN, pb, 0.0)
    for c in ("seq_read_then_write", "seq_merge_no_review", "seq_blind_write_7d",
              "seq_blind_write_session", "new_ip", "request_big"):
        sig[c] = raw[c]
    sig["call_without_init"] = np.where(raw["call_without_init"] > 0, pb, 0.0)
    sig["seq_clean"] = np.maximum(sig["seq_read_then_write"], sig["seq_merge_no_review"])
    sig["seq_recal"] = np.maximum(sig["seq_clean"], sig["seq_blind_write_7d"])
    sig["timing_limits"] = np.maximum.reduce([sig["burst_20"], sig["session_10m"], sig["seq_recal"]])
    sig["timing_limits_old"] = np.maximum.reduce([sig["burst_10"], sig["session_4h"],
                                                 sig["seq_clean"], sig["seq_blind_write_session"]])
    sig["request_limits"] = np.maximum(sig["request_big"], sig["call_without_init"])
    configs = {
        "A. previous best (new tool/asset, limits dropped)": {
            "timing": ["calls_1h", "repeat_10m", "seq_clean"], "footprint": ["new_tool", "new_asset"],
            "origin": ["new_ip", "client_new"], "request": ["request_big", "call_without_init"]},
        "B. A with footprint as shares": {
            "timing": ["calls_1h", "repeat_10m", "seq_clean"], "footprint": ["tool_share", "asset_share"],
            "origin": ["new_ip", "client_new"], "request": ["request_big", "call_without_init"]},
        "C. shares + every limit kept, OLD values": {
            "timing": ["calls_1h", "repeat_10m", "timing_limits_old"],
            "footprint": ["tool_share", "asset_share"], "origin": ["new_ip", "client_new"],
            "request": ["request_limits"]},
        "D. shares + every limit kept, RECALIBRATED": {
            "timing": ["calls_1h", "repeat_10m", "timing_limits"],
            "footprint": ["tool_share", "asset_share"], "origin": ["new_ip", "client_new"],
            "request": ["request_limits"]},
        "E. D + new tool/asset as well": {
            "timing": ["calls_1h", "repeat_10m", "timing_limits"],
            "footprint": ["tool_share", "asset_share", "new_tool", "new_asset"],
            "origin": ["new_ip", "client_new"], "request": ["request_limits"]},
    }
    _, inv = np.unique(ident.astype(np.int64) * 100000 + day, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    strange, episode = meta["strange"].astype(str), meta["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    names = list(sig)
    S = np.stack([sig[c] for c in names], 1)
    ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (S[ix] > 0).any(0))
          for ix in map(np.array, eps.values())]
    pos = {c: i for i, c in enumerate(names)}
    benign = np.ones(nk, bool)
    benign[inv[strange != ""]] = False
    benign &= kday >= CAL_DAYS

    def detect(fams, load_):
        total = np.zeros(len(day), np.float32)
        for dims in fams.values():
            total += S[:, [pos[d] for d in dims]].mean(1)
        score = np.zeros(nk, np.float32)
        np.maximum.at(score, inv, total)
        al = alerts(score, kday, n_eval, load_)
        used = [pos[d] for ds in fams.values() for d in ds]
        per: dict[str, list[bool]] = {}
        for cds, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(al[cds].any() and has[used].any()))
        return {k: float(np.mean(v)) for k, v in per.items()}

    def day_rate(c):
        m = np.zeros(nk, bool)
        np.logical_or.at(m, inv, S[:, pos[c]] > 0)
        return float(m[benign].mean())

    def kind_hits(c):
        per: dict[str, list[bool]] = {}
        for _, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(has[pos[c]]))
        return {k: float(np.mean(v)) for k, v in per.items()}

    checks = ["burst_10", "burst_20", "session_4h", "session_10m", "seq_read_then_write",
              "seq_merge_no_review", "seq_blind_write_session", "seq_blind_write_7d", "new_ip",
              "request_big", "call_without_init", "timing_limits", "timing_limits_old", "tool_share",
              "asset_share", "new_tool", "new_asset", "client_new"]
    out = {"configs": {k: {f"{lo:g}": detect(f, lo) for lo in LOADS} for k, f in configs.items()},
           "benign_day_rate": {c: day_rate(c) for c in checks},
           "fires_on": {c: kind_hits(c) for c in checks}}
    print(f"done {name}", flush=True)
    return out


def mean_kinds(rows):
    kinds: dict[str, list[float]] = {}
    for r in rows:
        for k, v in r.items():
            kinds.setdefault(k, []).append(v)
    return {k: float(np.mean(v)) for k, v in kinds.items()}


def main():
    with Pool(3) as pool:
        res = dict(zip(ORGS, pool.map(evaluate, ORGS)))
    (HERE / "results" / "footprint_policy_github.json").write_text(json.dumps(res, indent=1))
    print("\nDetection, 3 GitHub organisations, mean over 21 kinds (<= 2 / <= 4 a day)")
    per = {}
    for cfg in res[ORGS[0]]["configs"]:
        m = {lo: mean_kinds([res[n]["configs"][cfg][lo] for n in ORGS]) for lo in ("2", "4")}
        per[cfg] = m
        print(f"  {cfg:<52} {np.mean(list(m['2'].values())):.1%} / {np.mean(list(m['4'].values())):.1%}")
    a = per["A. previous best (new tool/asset, limits dropped)"]["4"]
    d = per["D. shares + every limit kept, RECALIBRATED"]["4"]
    print("\nPer kind at <= 4: A previous best | D shares + recalibrated limits")
    for k in sorted(a, key=lambda k: -d[k]):
        print(f"  {k:<24} {a[k]:4.0%} | {d[k]:4.0%}")
    print("\nEach check: ordinary agent-days it fires on, and the kinds it fires on")
    for c in res[ORGS[0]]["benign_day_rate"]:
        rate = np.mean([res[n]["benign_day_rate"][c] for n in ORGS])
        hits = mean_kinds([res[n]["fires_on"][c] for n in ORGS])
        top = sorted(hits.items(), key=lambda kv: -kv[1])[:4]
        print(f"  {c:<24} {rate:6.1%}   " + ", ".join(f"{k} {v:.0%}" for k, v in top if v > 0))


if __name__ == "__main__":
    main()
