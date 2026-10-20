"""One simple formula per dimension, each giving a level 0-5 (the static scan's scale), GitHub only.

Two kinds of dimension:
  rule (policy)    broken -> the policy's level, otherwise 0
  vs himself       p = how often in his own last 90 days he did at least this much (or, for a share,
                   how much of his own use goes to this tool / asset / hour of the week)
                   level 1-5 by rarity: 1 in 10 / 30 / 100 / 300 / 1000

Dimensions:
  calls per hour            vs himself
  same tool in 10 minutes   vs himself
  tool share                vs himself, capped by the tool's impact
  asset share               vs himself, capped by the asset's sensitivity (unregistered = 5)
  request size              vs himself, for this tool
  off-hours                 vs himself: share of his calls in this hour of the day, on this
                            kind of day (weekday / weekend): 48 slots
  first-time tool           rule: level = tool impact (unknown = 5)
  first-time asset          rule: level = asset sensitivity (unregistered = 5)
  first-time IP, client     rule: level 4
  burst (> 20 a minute), request > 10 KB, problematic sequence, protocol skip   rule: level 4
  session > 10 minutes      rule: level 3

Two ways of reading the levels are compared:
  rarity  as above, per call
  excess  "vs himself" levels from the excess over his own normal (his 99.5th percentile over 30
          days): level = ceil(excess bits / 2), so every 2 bits (4x rarer) above normal is a level
and two ways of turning a day's levels into a ranking:
  highest  the day's highest level, ties broken by the sum of the other levels
  sum      the sum over dimensions of each dimension's highest level that day

Run:  python levels_github.py      (writes results/levels_github.json)
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict, deque
from multiprocessing import Pool

import numpy as np

from detectors import vbin
from policy_github import (DAY, HERE, MIN_HISTORY, NEW_ASSET, ORGS, REVIEW_TOOLS, RUNS, SCAN,
                           SENSITIVE, WORST, Agent, self_excess)
from vkp_eval import CAL_DAYS, alerts

csv.field_size_limit(10**9)
W, BURST, SESSION_MIN, REQUEST_BYTES, READ_MEMORY_DAYS = 90, 20, 10.0, 10_000, 7
TIME_SLOTS = 48                   # hour of the day x (weekday, weekend)
RARITY = [(1 / 1000, 5), (1 / 300, 4), (1 / 100, 3), (1 / 30, 2), (1 / 10, 1)]
RULE_LEVEL = {"first_ip": 4, "first_client": 4, "burst": 4, "request_big": 4, "sequence": 4,
              "protocol_skip": 4, "session_long": 3}
VS_SELF = ["calls_1h", "repeat_10m", "tool_share", "asset_share", "request_size", "off_hours"]
RULES = ["first_tool", "first_asset", "first_ip", "first_client", "burst", "session_long",
         "sequence", "request_big", "protocol_skip"]
REUSED = {"self/{n}.npz": {"tool_repeat_10m": "repeat_10m"},
          "w2/{n}.npz": {"request_bytes": "request_size"},
          "w2/{n}_p.npz": {"call_without_init": "protocol_skip"}}
LOADS = (2.0, 4.0)


class Window:
    def __init__(self):
        self.counts, self.total, self.log = Counter(), 0, deque()

    def p_share(self, key, day: int, smooth: int) -> float:
        """Share of his last-90-day items equal to key (smoothed), then records it."""
        while self.log and self.log[0][0] <= day - W:
            _, k = self.log.popleft()
            self.counts[k] -= 1
            self.total -= 1
        p = (self.counts[key] + 1) / (self.total + smooth) if self.total >= MIN_HISTORY else 1.0
        self.counts[key] += 1
        self.total += 1
        self.log.append((day, key))
        return p


def rarity_level(p: np.ndarray) -> np.ndarray:
    lvl = np.zeros(p.shape, np.int8)
    for limit, level in reversed(RARITY):
        lvl[p <= limit] = level
    return lvl


def extract(name: str, impacts: dict[str, int]):
    agents: dict[str, Agent] = defaultdict(Agent)
    tools, assets, hours = defaultdict(Window), defaultdict(Window), defaultdict(Window)
    seen: dict[tuple[str, str], set] = defaultdict(set)
    last_read: dict[tuple[str, str], int] = {}
    sessions: dict[str, dict] = {}
    cols = ["p_calls_1h", "p_tool_share", "p_asset_share", "p_off_hours", "impact", "asset_level",
            "first_tool", "first_asset", "first_ip", "first_client", "burst", "session_long",
            "sequence", "request_big"]
    out = {c: [] for c in cols}
    meta = {k: [] for k in ("ts", "agent", "strange", "episode")}
    with gzip.open(HERE / "w2" / f"{name}.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            ts = float(r["ts"])
            day = int(ts // DAY)
            a, st = r["agent"], agents[r["agent"]]
            row = dict.fromkeys(cols, 0.0)
            row.update(p_calls_1h=1.0, p_tool_share=1.0, p_asset_share=1.0, p_off_hours=1.0)
            sess = sessions.setdefault(r["session"], {"start": ts, "read_sens": set(), "review": False})
            history = st.rate["any"][0] >= MIN_HISTORY
            st.rate["any"][0] += 1
            for kind, value in (("ip", r["address"]), ("client", r["client"].split("/")[0].lower())):
                if value not in seen[(a, kind)] and history:
                    row[f"first_{kind}"] = 1
                seen[(a, kind)].add(value)
            if r["method"] == "tools/call":
                tool, op, asset, sens = r["tool"], r["op"], r["which"], int(r["sens"] or 0)
                st.calls.append(ts)
                while st.calls[0] < ts - 3600:
                    st.calls.popleft()
                st.hist_1h.expire(day)
                b = vbin(len(st.calls))
                if st.hist_1h.n >= MIN_HISTORY:
                    row["p_calls_1h"] = st.hist_1h.p_upper(b)
                st.hist_1h.add(day, b)
                row["burst"] = int(sum(1 for t in st.calls if t >= ts - 60) > BURST)
                row["session_long"] = int(ts - sess["start"] > SESSION_MIN * 60)
                row["request_big"] = int(int(r["bytes"] or 0) > REQUEST_BYTES)
                row["impact"] = impacts.get(tool, WORST)
                row["p_tool_share"] = tools[a].p_share(tool, day, len(impacts))
                if tool not in seen[(a, "tool")] and history:
                    row["first_tool"] = 1
                seen[(a, "tool")].add(tool)
                slot = int((ts % DAY) // 3600) + 24 * int(day % 7 >= 5)
                row["p_off_hours"] = hours[a].p_share(slot, day, TIME_SLOTS)
                if asset and asset != "null" and sens > 0:
                    level = WORST if NEW_ASSET.search(asset) else sens
                    row["asset_level"] = level
                    row["p_asset_share"] = assets[a].p_share(asset, day, len(assets[a].counts) + 1)
                    if asset not in seen[(a, "asset")] and history:
                        row["first_asset"] = 1
                    seen[(a, "asset")].add(asset)
                    blind = op == "write" and level >= SENSITIVE and \
                        last_read.get((a, asset), -10**6) < day - READ_MEMORY_DAYS
                    if (op == "write" and sess["read_sens"] - {asset}) or blind:
                        row["sequence"] = 1
                    if op in ("read", "metadata"):
                        last_read[(a, asset)] = day
                        if level >= SENSITIVE:
                            sess["read_sens"].add(asset)
                if tool == "merge_pull_request" and not sess["review"]:
                    row["sequence"] = 1
                if tool in REVIEW_TOOLS:
                    sess["review"] = True
            for c in cols:
                out[c].append(row[c])
            for k, v in (("ts", ts), ("agent", a), ("strange", r["strange"]), ("episode", r["episode"])):
                meta[k].append(v)
    return {c: np.array(v, dtype=np.float64) for c, v in out.items()}, \
        {k: np.array(v) for k, v in meta.items()}


def evaluate(name: str) -> dict:
    impacts = {t["tool"]: t["impact"] for t in json.loads(SCAN.read_text())["tools"]}
    raw, meta = extract(name, impacts)
    for pattern, dims in REUSED.items():
        f = np.load(RUNS / pattern.format(n=name))
        fc = [str(c) for c in f["cols"]]
        for src, dst in dims.items():
            raw[f"u_{dst}"] = f["scores"][:, fc.index(src)].astype(np.float64)
    day = (meta["ts"] // DAY).astype(int)
    _, ident = np.unique(meta["agent"], return_inverse=True)
    impact, alevel = raw["impact"], raw["asset_level"]
    # p for every vs-himself dimension (surprise u = -log2 p from the earlier score files)
    p = {"calls_1h": raw["p_calls_1h"], "tool_share": raw["p_tool_share"],
         "asset_share": raw["p_asset_share"], "off_hours": raw["p_off_hours"],
         "repeat_10m": 2.0 ** -raw["u_repeat_10m"], "request_size": 2.0 ** -raw["u_request_size"]}
    cap = {"tool_share": impact, "asset_share": alevel}
    rule = {"first_tool": raw["first_tool"] * impact, "first_asset": raw["first_asset"] * alevel,
            "protocol_skip": (raw["u_protocol_skip"] > 0) * RULE_LEVEL["protocol_skip"]}
    for c in ("first_ip", "first_client", "burst", "session_long", "sequence", "request_big"):
        rule[c] = raw[c] * RULE_LEVEL[c]
    levels = {}
    U = np.stack([-np.log2(np.clip(p[d], 1e-12, 1)) for d in VS_SELF], 1).astype(np.float32)
    X = self_excess(U, day, ident)
    for i, d in enumerate(VS_SELF):
        by_rarity = rarity_level(p[d])
        by_excess = np.minimum(5, np.ceil(X[:, i] / 2)).astype(np.int8)
        if d in cap:
            by_rarity = np.minimum(by_rarity, cap[d]).astype(np.int8)
            by_excess = np.minimum(by_excess, cap[d]).astype(np.int8)
        levels[("rarity", d)], levels[("excess", d)] = by_rarity, by_excess
    for d, v in rule.items():
        levels[("rarity", d)] = levels[("excess", d)] = v.astype(np.int8)
    dims = VS_SELF + RULES
    _, inv = np.unique(ident.astype(np.int64) * 100000 + day, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    strange, episode = meta["strange"].astype(str), meta["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    benign = np.ones(nk, bool)
    benign[inv[strange != ""]] = False
    benign &= kday >= CAL_DAYS
    out = {"detection": {}, "benign_day_rate": {}, "fires_on": {}}
    for mode in ("rarity", "excess"):
        L = np.stack([levels[(mode, d)] for d in dims], 1).astype(np.float32)
        AD = np.zeros((nk, len(dims)), np.float32)
        np.maximum.at(AD, inv, L)
        ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (L[ix] > 0).any(0))
              for ix in map(np.array, eps.values())]
        top = AD.max(1)
        scores = {"highest": top + (AD.sum(1) - top) / 100.0, "sum": AD.sum(1)}
        for how, score in scores.items():
            for lo in LOADS:
                al = alerts(score, kday, n_eval, lo)
                per: dict[str, list[bool]] = {}
                for cds, kind, after, has in ep:
                    if after:
                        per.setdefault(kind, []).append(bool(al[cds].any() and has.any()))
                out["detection"][f"{mode}|{how}|{lo:g}"] = {k: float(np.mean(v)) for k, v in per.items()}
        for j, d in enumerate(dims):
            for t in (1, 3, 5):
                out["benign_day_rate"][f"{mode}|{d}|>={t}"] = float((AD[benign, j] >= t).mean())
            per = {}
            for _, kind, after, has in ep:
                if after:
                    per.setdefault(kind, []).append(bool(has[j]))
            out["fires_on"][f"{mode}|{d}"] = {k: float(np.mean(v)) for k, v in per.items()}
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
    (HERE / "results" / "levels_github.json").write_text(json.dumps(res, indent=1))
    print("\nDetection, 3 GitHub organisations, mean over 21 kinds (<= 2 / <= 4 a day)")
    for mode in ("rarity", "excess"):
        for how in ("highest", "sum"):
            m = {lo: mean_kinds([res[n]["detection"][f"{mode}|{how}|{lo}"] for n in ORGS])
                 for lo in ("2", "4")}
            print(f"  levels by {mode:<7} day = {how:<8} {np.mean(list(m['2'].values())):.1%} / "
                  f"{np.mean(list(m['4'].values())):.1%}")
    for mode in ("rarity", "excess"):
        print(f"\nPer dimension ({mode}): ordinary agent-days reaching level >=1 / >=3 / >=5, "
              "and the kinds it fires on")
        for d in VS_SELF + RULES:
            r = [np.mean([res[n]["benign_day_rate"][f"{mode}|{d}|>={t}"] for n in ORGS]) for t in (1, 3, 5)]
            hits = mean_kinds([res[n]["fires_on"][f"{mode}|{d}"] for n in ORGS])
            topk = sorted(hits.items(), key=lambda kv: -kv[1])[:3]
            print(f"  {d:<14} {r[0]:6.1%} {r[1]:6.1%} {r[2]:6.1%}   "
                  + ", ".join(f"{k} {v:.0%}" for k, v in topk if v > 0))


if __name__ == "__main__":
    main()
