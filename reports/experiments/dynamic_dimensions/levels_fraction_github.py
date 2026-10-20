"""Per-dimension levels 0-5 without bits: fractions and averages only. GitHub only.

The "vs himself" dimensions use one of two plain quantities:
  share     the methodology deck's likelihood, L = (N(v) + 1) / (N_total + K), over his last 90 days
            tool share       K = tools in the catalog          level at most the tool's impact
            asset share      K = assets he has used + 1       level at most the asset's sensitivity
            off-hours share  K = 48 slots (hour x weekday/weekend)
            a small share is strange: level = how many share thresholds L is below
  average   ratio = value / his own average of that value over his last 90 days
            calls in the last hour, same tool in 10 minutes, request size (per tool)
            a big ratio is strange: level = how many ratio thresholds it reaches
The rules (first-time tool / asset / IP / client, burst, session, sequence, request size, protocol
skip) are the same as in levels_github.py.

Threshold sets compared:
  A  ratio 2 / 3 / 5 / 10 / 20        share 5% / 2% / 1% / 0.5% / 0.2%
  B  ratio 3 / 5 / 10 / 20 / 50       share 2% / 1% / 0.5% / 0.2% / 0.1%
  C  ratio 2 / 3 / 5 / 10 / 20        share 2% / 1% / 0.5% / 0.2% / 0.1%
  D  C, off-hours as the share of his calls within one hour of this time (3 slots, K = 16)
  E  C, off-hours with stricter thresholds 0.5% / 0.2% / 0.1% / 0.05% / 0.02%
  F  D with E's off-hours thresholds
Day score = the day's highest level, ties broken by the other levels (sum / 100), as before.

Run:  python levels_fraction_github.py      (writes results/levels_fraction_github.json)
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict, deque
from multiprocessing import Pool

import numpy as np

from levels_github import (BURST, READ_MEMORY_DAYS, REQUEST_BYTES, RULE_LEVEL, SESSION_MIN,
                           TIME_SLOTS, Window, mean_kinds)
from policy_github import (DAY, HERE, MIN_HISTORY, NEW_ASSET, ORGS, REVIEW_TOOLS, RUNS, SCAN,
                           SENSITIVE, WORST)
from vkp_eval import CAL_DAYS, alerts

csv.field_size_limit(10**9)
W = 90
STRICT = [0.005, 0.002, 0.001, 0.0005, 0.0002]
SETS = {"A": ([2, 3, 5, 10, 20], [0.05, 0.02, 0.01, 0.005, 0.002], "off_hours", None),
        "B": ([3, 5, 10, 20, 50], [0.02, 0.01, 0.005, 0.002, 0.001], "off_hours", None),
        "C": ([2, 3, 5, 10, 20], [0.02, 0.01, 0.005, 0.002, 0.001], "off_hours", None),
        "D": ([2, 3, 5, 10, 20], [0.02, 0.01, 0.005, 0.002, 0.001], "off_hours_pm1", None),
        "E": ([2, 3, 5, 10, 20], [0.02, 0.01, 0.005, 0.002, 0.001], "off_hours", STRICT),
        "F": ([2, 3, 5, 10, 20], [0.02, 0.01, 0.005, 0.002, 0.001], "off_hours_pm1", STRICT)}
AVERAGE_DIMS = ["calls_1h", "repeat_10m", "request_size"]
SHARE_DIMS = ["tool_share", "asset_share", "off_hours"]
RULES = ["first_tool", "first_asset", "first_ip", "first_client", "burst", "session_long",
         "sequence", "request_big", "protocol_skip"]
LOADS = (2.0, 4.0)


class RunningMean:
    """His average of a value over the last 90 days (read before adding today's value)."""

    def __init__(self):
        self.log, self.total = deque(), 0.0

    def ratio_then_add(self, value: float, day: int) -> float:
        while self.log and self.log[0][0] <= day - W:
            self.total -= self.log.popleft()[1]
        n = len(self.log)
        r = value / (self.total / n) if n >= MIN_HISTORY and self.total > 0 else 0.0
        self.log.append((day, value))
        self.total += value
        return r


def extract(name: str, impacts: dict[str, int]):
    calls: dict[str, deque] = defaultdict(deque)
    recent: dict[str, deque] = defaultdict(deque)
    mean_1h, mean_rep = defaultdict(RunningMean), defaultdict(RunningMean)
    mean_size = defaultdict(RunningMean)
    tools, assets, hours = defaultdict(Window), defaultdict(Window), defaultdict(Window)
    seen: dict[tuple[str, str], set] = defaultdict(set)
    n_msgs: dict[str, int] = defaultdict(int)
    last_read: dict[tuple[str, str], int] = {}
    sessions: dict[str, dict] = {}
    cols = ["calls_1h", "repeat_10m", "request_size", "tool_share", "asset_share", "off_hours",
            "off_hours_pm1", "impact", "asset_level"] + RULES[:-1]
    out = {c: [] for c in cols}
    meta = {k: [] for k in ("ts", "agent", "strange", "episode")}
    with gzip.open(HERE / "w2" / f"{name}.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            ts = float(r["ts"])
            day = int(ts // DAY)
            a = r["agent"]
            row = dict.fromkeys(cols, 0.0)
            row.update(tool_share=1.0, asset_share=1.0, off_hours=1.0, off_hours_pm1=1.0)
            sess = sessions.setdefault(r["session"], {"start": ts, "read_sens": set(), "review": False})
            history = n_msgs[a] >= MIN_HISTORY
            n_msgs[a] += 1
            for kind, value in (("ip", r["address"]), ("client", r["client"].split("/")[0].lower())):
                if value not in seen[(a, kind)] and history:
                    row[f"first_{kind}"] = 1
                seen[(a, kind)].add(value)
            if r["method"] == "tools/call":
                tool, op, asset, sens = r["tool"], r["op"], r["which"], int(r["sens"] or 0)
                q = calls[a]
                q.append(ts)
                while q[0] < ts - 3600:
                    q.popleft()
                row["calls_1h"] = mean_1h[a].ratio_then_add(len(q), day)
                rq = recent[a]
                rq.append((ts, tool))
                while rq[0][0] < ts - 600:
                    rq.popleft()
                row["repeat_10m"] = mean_rep[a].ratio_then_add(sum(1 for _, t in rq if t == tool), day)
                row["request_size"] = mean_size[(a, tool)].ratio_then_add(float(r["bytes"] or 0), day)
                row["burst"] = int(sum(1 for t in q if t >= ts - 60) > BURST)
                row["session_long"] = int(ts - sess["start"] > SESSION_MIN * 60)
                row["request_big"] = int(int(r["bytes"] or 0) > REQUEST_BYTES)
                row["impact"] = impacts.get(tool, WORST)
                row["tool_share"] = tools[a].p_share(tool, day, len(impacts))
                if tool not in seen[(a, "tool")] and history:
                    row["first_tool"] = 1
                seen[(a, "tool")].add(tool)
                slot = int((ts % DAY) // 3600) + 24 * int(day % 7 >= 5)
                hw = hours[a]
                row["off_hours"] = hw.p_share(slot, day, TIME_SLOTS)
                if hw.total - 1 >= MIN_HISTORY:                 # counts now include this call
                    base = 24 * (slot // 24)
                    near = sum(hw.counts[base + (slot % 24 + k) % 24] for k in (-1, 0, 1)) - 1
                    row["off_hours_pm1"] = (near + 1) / (hw.total - 1 + 16)
                if asset and asset != "null" and sens > 0:
                    level = WORST if NEW_ASSET.search(asset) else sens
                    row["asset_level"] = level
                    row["asset_share"] = assets[a].p_share(asset, day, len(assets[a].counts) + 1)
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


def ratio_level(r: np.ndarray, thresholds: list[float]) -> np.ndarray:
    return sum((r >= t).astype(np.int8) for t in thresholds).astype(np.int8)


def share_level(share: np.ndarray, thresholds: list[float]) -> np.ndarray:
    return sum((share < t).astype(np.int8) for t in thresholds).astype(np.int8)


def evaluate(name: str) -> dict:
    impacts = {t["tool"]: t["impact"] for t in json.loads(SCAN.read_text())["tools"]}
    raw, meta = extract(name, impacts)
    f = np.load(RUNS / f"w2/{name}_p.npz")
    raw["protocol_skip"] = f["scores"][:, [str(c) for c in f["cols"]].index("call_without_init")] > 0
    day = (meta["ts"] // DAY).astype(int)
    _, ident = np.unique(meta["agent"], return_inverse=True)
    rule = {"first_tool": raw["first_tool"] * raw["impact"],
            "first_asset": raw["first_asset"] * raw["asset_level"],
            "protocol_skip": raw["protocol_skip"] * RULE_LEVEL["protocol_skip"]}
    for c in ("first_ip", "first_client", "burst", "session_long", "sequence", "request_big"):
        rule[c] = raw[c] * RULE_LEVEL[c]
    cap = {"tool_share": raw["impact"], "asset_share": raw["asset_level"]}
    dims = AVERAGE_DIMS + SHARE_DIMS + RULES
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
    for set_name, (ratios, shares, off_col, off_thr) in SETS.items():
        lv = {d: ratio_level(raw[d], ratios) for d in AVERAGE_DIMS}
        for d in SHARE_DIMS:
            src = off_col if d == "off_hours" else d
            lv[d] = share_level(raw[src], off_thr if d == "off_hours" and off_thr else shares)
            if d in cap:
                lv[d] = np.minimum(lv[d], cap[d]).astype(np.int8)
        lv.update({d: v.astype(np.int8) for d, v in rule.items()})
        L = np.stack([lv[d] for d in dims], 1).astype(np.float32)
        AD = np.zeros((nk, len(dims)), np.float32)
        np.maximum.at(AD, inv, L)
        ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (L[ix] > 0).any(0))
              for ix in map(np.array, eps.values())]
        top = AD.max(1)
        score = top + (AD.sum(1) - top) / 100.0
        for lo in LOADS:
            al = alerts(score, kday, n_eval, lo)
            per: dict[str, list[bool]] = {}
            for cds, kind, after, has in ep:
                if after:
                    per.setdefault(kind, []).append(bool(al[cds].any() and has.any()))
            out["detection"][f"{set_name}|{lo:g}"] = {k: float(np.mean(v)) for k, v in per.items()}
        for j, d in enumerate(dims):
            for t in (1, 3, 5):
                out["benign_day_rate"][f"{set_name}|{d}|>={t}"] = float((AD[benign, j] >= t).mean())
            per = {}
            for _, kind, after, has in ep:
                if after:
                    per.setdefault(kind, []).append(bool(has[j]))
            out["fires_on"][f"{set_name}|{d}"] = {k: float(np.mean(v)) for k, v in per.items()}
    print(f"done {name}", flush=True)
    return out


def main():
    with Pool(3) as pool:
        res = dict(zip(ORGS, pool.map(evaluate, ORGS)))
    (HERE / "results" / "levels_fraction_github.json").write_text(json.dumps(res, indent=1))
    print("\nDetection, 3 GitHub organisations, mean over 21 kinds (<= 2 / <= 4 a day)")
    for s in SETS:
        m = {lo: mean_kinds([res[n]["detection"][f"{s}|{lo}"] for n in ORGS]) for lo in ("2", "4")}
        print(f"  set {s}: {np.mean(list(m['2'].values())):.1%} / {np.mean(list(m['4'].values())):.1%}")
    for s in SETS:
        print(f"\nSet {s}: ordinary agent-days at level >=1 / >=3 / >=5, and the kinds it fires on")
        for d in AVERAGE_DIMS + SHARE_DIMS:
            r = [np.mean([res[n]["benign_day_rate"][f"{s}|{d}|>={t}"] for n in ORGS]) for t in (1, 3, 5)]
            hits = mean_kinds([res[n]["fires_on"][f"{s}|{d}"] for n in ORGS])
            topk = sorted(hits.items(), key=lambda kv: -kv[1])[:3]
            print(f"  {d:<14} {r[0]:6.1%} {r[1]:6.1%} {r[2]:6.1%}   "
                  + ", ".join(f"{k} {v:.0%}" for k, v in topk if v > 0))


if __name__ == "__main__":
    main()
