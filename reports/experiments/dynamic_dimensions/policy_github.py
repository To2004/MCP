"""The user's Timing / Footprint / Request design with policy limits, tested on the GitHub worlds.

Learned dimensions compare an agent only with his own past (surprise u = -log2 p against his own
90 days; signal x = max(0, u - B), B = his own 99.5th percentile over his last 30 days). Policy
dimensions are fixed limits: a breach counts as POLICY_BITS, otherwise 0. Inside a family the
signals are averaged; families add in the exponent: R = R_static * e^(lambda * sum of families).

Learned:
    calls_1h           calls in the last hour vs his usual
    new_tool_w         a tool he has not used in 90 days, x (tool impact / 5); unknown tool = 5
    new_asset_w        an asset he has not touched in 90 days, x (asset sensitivity / 5);
                       an asset not in the register (created after day 0) counts as 5, the worst
    repeat_10m, network_16, request_size, call_without_init   (recommended additions; from the
                       earlier score files, all self-relative except request size per tool)
Policy (limits from the policy):
    burst              more than BURST_PER_MIN calls in the last minute
    session_long       session open longer than SESSION_LIMIT_H hours
    sequence           one of three GitHub sequences: a sensitive read then a write to another
                       asset; a write to a sensitive asset not read first; a merge without looking
                       at the pull request or its reviews first (all within the session)
    new_ip             an exact IP he has not used in 90 days
    request_big        request larger than REQUEST_LIMIT_BYTES

Run:  python policy_github.py      (writes results/policy_github.json)
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import re
from collections import defaultdict, deque
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from detectors import Hist, vbin
from vkp_eval import CAL_DAYS, alerts

csv.field_size_limit(10**9)
HERE = Path(__file__).parent
RUNS = HERE.resolve().parents[2] / "runs" / "dynamic_dimensions"
SCAN = Path.home() / "mcp-static-scan/examples/github-helios/reference/github-helios.scan.json"
ORGS = ["github_M", "github_S", "github_bots"]
DAY, W, MIN_HISTORY = 86400.0, 90, 20
BURST_PER_MIN, SESSION_LIMIT_H, REQUEST_LIMIT_BYTES, POLICY_BITS = 10, 4.0, 10_000, 10.0
SENSITIVE, WORST = 4, 5
REVIEW_TOOLS = {"get_pull_request", "get_pull_request_reviews", "get_pull_request_status"}
NEW_ASSET = re.compile(r"-n\d+\"?$")
LEARNED = ["calls_1h", "new_tool_w", "new_asset_w"]
POLICY = ["burst", "session_long", "sequence", "sequence_clean", "new_ip", "request_big"]
SEQUENCES = ["seq_read_then_write", "seq_blind_sensitive_write", "seq_merge_no_review"]
REUSED = {"self/{n}.npz": {"tool_repeat_10m": "repeat_10m", "network_new": "network_16",
                           "client_new": "client_new"},
          "w2/{n}.npz": {"request_bytes": "request_size"},
          "w2/{n}_p.npz": {"call_without_init": "call_without_init"}}
CONFIGS = {
    "your design": {"timing": ["calls_1h", "burst", "session_long", "sequence"],
                    "footprint": ["new_tool_w", "new_asset_w"],
                    "request": ["new_ip", "request_big"]},
    "your design, no sequences": {"timing": ["calls_1h", "burst", "session_long"],
                                  "footprint": ["new_tool_w", "new_asset_w"],
                                  "request": ["new_ip", "request_big"]},
    "your design, unknown asset = its register level": None,      # filled in evaluate()
    "recommended": {"timing": ["calls_1h", "repeat_10m", "burst", "session_long", "sequence"],
                    "footprint": ["new_tool_w", "new_asset_w"],
                    "request": ["network_16", "request_size", "request_big", "call_without_init"]},
    "fixed": {"timing": ["calls_1h", "repeat_10m", "sequence_clean"],
              "footprint": ["new_tool_w", "new_asset_w"],
              "request": ["new_ip", "client_new", "request_big", "call_without_init"]},
    "fixed, 4 families": {"timing": ["calls_1h", "repeat_10m", "sequence_clean"],
                          "footprint": ["new_tool_w", "new_asset_w"],
                          "origin": ["new_ip", "client_new"],
                          "request": ["request_big", "call_without_init"]},
    "fixed, 4 families + learned request size": {"timing": ["calls_1h", "repeat_10m", "sequence_clean"],
                                                 "footprint": ["new_tool_w", "new_asset_w"],
                                                 "origin": ["new_ip", "client_new"],
                                                 "request": ["request_big", "request_size",
                                                             "call_without_init"]},
    "fixed + full sequence rule": {"timing": ["calls_1h", "repeat_10m", "sequence"],
                                   "footprint": ["new_tool_w", "new_asset_w"],
                                   "request": ["new_ip", "client_new", "request_big",
                                               "call_without_init"]},
    "fixed + burst limit": {"timing": ["calls_1h", "repeat_10m", "burst", "sequence_clean"],
                            "footprint": ["new_tool_w", "new_asset_w"],
                            "request": ["new_ip", "client_new", "request_big", "call_without_init"]},
    "fixed + learned request size": {"timing": ["calls_1h", "repeat_10m", "sequence_clean"],
                                     "footprint": ["new_tool_w", "new_asset_w"],
                                     "request": ["new_ip", "client_new", "request_big", "request_size",
                                                 "call_without_init"]},
}
LOADS = (2.0, 4.0)


def bits(p: float) -> float:
    return -math.log2(min(1.0, max(p, 1e-12)))


class Agent:
    def __init__(self):
        self.calls: deque = deque()
        self.hist_1h = Hist(W)
        self.seen: dict[str, dict[str, int]] = defaultdict(dict)
        self.rate: dict[str, list[int]] = defaultdict(lambda: [0, 0])


def novelty(st: Agent, kind: str, value: str, day: int) -> float:
    last = st.seen[kind].get(value)
    new = last is None or last <= day - W
    calls, news = st.rate[kind]
    s = bits((news + 1) / (calls + 1)) if new and calls >= MIN_HISTORY else 0.0
    st.rate[kind] = [calls + 1, news + int(new)]
    st.seen[kind][value] = day
    return s


def extract(name: str, impacts: dict[str, int]):
    """One pass over the world: learned surprises and policy breaches per message."""
    agents: dict[str, Agent] = defaultdict(Agent)
    sessions: dict[str, dict] = {}
    cols = LEARNED + ["new_asset_registered"] + POLICY + SEQUENCES
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
            row["new_ip"] = POLICY_BITS if (novelty(st, "ip", r["address"], day) > 0) else 0.0
            if r["method"] == "tools/call":
                tool, op, asset = r["tool"], r["op"], r["which"]
                sens = int(r["sens"] or 0)
                st.calls.append(ts)
                while st.calls[0] < ts - 3600:
                    st.calls.popleft()
                st.hist_1h.expire(day)
                b = vbin(len(st.calls))
                if st.hist_1h.n >= MIN_HISTORY:
                    row["calls_1h"] = bits(st.hist_1h.p_upper(b))
                st.hist_1h.add(day, b)
                row["burst"] = POLICY_BITS if sum(1 for t in st.calls if t >= ts - 60) > BURST_PER_MIN else 0
                row["session_long"] = POLICY_BITS if ts - sess["start"] > SESSION_LIMIT_H * 3600 else 0
                row["request_big"] = POLICY_BITS if int(r["bytes"] or 0) > REQUEST_LIMIT_BYTES else 0
                row["new_tool_w"] = novelty(st, "tool", tool, day) * impacts.get(tool, WORST) / WORST
                if asset and asset != "null" and sens > 0:
                    level = WORST if NEW_ASSET.search(asset) else sens
                    u = novelty(st, "asset", asset, day)
                    row["new_asset_w"] = u * level / WORST
                    row["new_asset_registered"] = u * sens / WORST
                    if op == "write" and sess["read_sens"] - {asset}:
                        row["seq_read_then_write"] = POLICY_BITS
                    if op == "write" and level >= SENSITIVE and asset not in sess["read"]:
                        row["seq_blind_sensitive_write"] = POLICY_BITS
                    if op in ("read", "metadata"):
                        sess["read"].add(asset)
                        if level >= SENSITIVE:
                            sess["read_sens"].add(asset)
                if tool == "merge_pull_request" and not sess["review"]:
                    row["seq_merge_no_review"] = POLICY_BITS
                if tool in REVIEW_TOOLS:
                    sess["review"] = True
                row["sequence"] = max(row[s] for s in SEQUENCES)
                row["sequence_clean"] = max(row["seq_read_then_write"], row["seq_merge_no_review"])
            for c in cols:
                out[c].append(row[c])
            meta["ts"].append(ts)
            meta["agent"].append(a)
            meta["strange"].append(r["strange"])
            meta["episode"].append(r["episode"])
    X = np.array([out[c] for c in cols], dtype=np.float32).T
    return cols, X, {k: np.array(v) for k, v in meta.items()}


def self_excess(X: np.ndarray, day: np.ndarray, ident: np.ndarray) -> np.ndarray:
    """x = max(0, u - B), B = the agent's own 99.5th percentile over his previous 30 days."""
    out = np.zeros_like(X)
    order = np.lexsort((day, ident))
    ids, ds = ident[order], day[order]
    bounds = np.flatnonzero(np.r_[True, ids[1:] != ids[:-1], True])
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        rows, days = order[lo:hi], ds[lo:hi]
        for d in np.unique(days):
            a = np.searchsorted(days, d - CAL_DAYS, "left")
            b = np.searchsorted(days, d, "left")
            today = rows[b:np.searchsorted(days, d, "right")]
            if b - a < MIN_HISTORY * 10:
                continue
            B = np.quantile(X[rows[a:b]], 0.995, axis=0)
            out[today] = np.maximum(0.0, X[today] - B) * (X[today] > 1e-6)
    return out


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
    learned = [c for c in cols if c not in POLICY and c not in SEQUENCES]
    x = X.copy()                                   # policy columns stay as they are (0 or 10)
    jj = [col[c] for c in learned]
    x[:, jj] = self_excess(X[:, jj], day, ident)
    _, inv = np.unique(ident.astype(np.int64) * 100000 + day, return_inverse=True)
    nk = inv.max() + 1
    kday = np.zeros(nk, int)
    kday[inv] = day
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    strange, episode = meta["strange"].astype(str), meta["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, (x[ix] > 0).any(0))
          for ix in map(np.array, eps.values())]
    benign_day = np.ones(nk, bool)
    benign_day[inv[strange != ""]] = False
    benign_day &= kday >= CAL_DAYS
    configs = dict(CONFIGS)
    configs["your design, unknown asset = its register level"] = {
        "timing": ["calls_1h", "burst", "session_long", "sequence"],
        "footprint": ["new_tool_w", "new_asset_registered"], "request": ["new_ip", "request_big"]}

    def detect(fams: dict[str, list[str]], load_: float, how: str = "average") -> dict[str, float]:
        total = np.zeros(len(day), np.float32)
        for dims in fams.values():
            v = x[:, [col[d] for d in dims]]
            total += v.max(1) if how == "max" else v.mean(1)
        score = np.zeros(nk, np.float32)
        np.maximum.at(score, inv, total)
        al = alerts(score, kday, n_eval, load_)
        used = [col[d] for ds in fams.values() for d in ds]
        per: dict[str, list[bool]] = {}
        for cds, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(al[cds].any() and has[used].any()))
        return {k: float(np.mean(v)) for k, v in per.items()}

    def day_rate(c: str) -> float:
        m = np.zeros(nk, bool)
        np.logical_or.at(m, inv, x[:, col[c]] > 0)
        return float(m[benign_day].mean())

    def kind_hit(c: str) -> dict[str, float]:
        per: dict[str, list[bool]] = {}
        for _, kind, after, has in ep:
            if after:
                per.setdefault(kind, []).append(bool(has[col[c]]))
        return {k: float(np.mean(v)) for k, v in per.items()}

    out = {"configs": {k: {f"{lo:g}": detect(f, lo) for lo in LOADS} for k, f in configs.items()},
           "max": {k: {f"{lo:g}": detect(f, lo, "max") for lo in LOADS} for k, f in configs.items()},
           "benign_day_rate": {c: day_rate(c) for c in cols},
           "fires_on_kind": {c: kind_hit(c) for c in POLICY + SEQUENCES + ["new_asset_w", "new_tool_w"]}}
    print(f"done {name}", flush=True)
    return out


def mean_kinds(rows: list[dict]) -> dict[str, float]:
    kinds: dict[str, list[float]] = {}
    for r in rows:
        for k, v in r.items():
            kinds.setdefault(k, []).append(v)
    return {k: float(np.mean(v)) for k, v in kinds.items()}


def main():
    with Pool(3) as pool:
        res = dict(zip(ORGS, pool.map(evaluate, ORGS)))
    (HERE / "results" / "policy_github.json").write_text(json.dumps(res, indent=1))
    print("\nDetection on the 3 GitHub organisations, mean over 21 kinds (<= 2 / <= 4 a day)")
    per_kind = {}
    print(f"  {'':<48} {'average inside':>16}   {'max inside':>14}")
    for cfg in CONFIGS:
        m = {lo: mean_kinds([res[n]["configs"][cfg][lo] for n in ORGS]) for lo in ("2", "4")}
        mx = {lo: mean_kinds([res[n]["max"][cfg][lo] for n in ORGS]) for lo in ("2", "4")}
        per_kind[cfg] = m["4"]
        per_kind[cfg + "|max"] = mx["4"]
        print(f"  {cfg:<48} {np.mean(list(m['2'].values())):6.1%} / {np.mean(list(m['4'].values())):5.1%}"
              f"   {np.mean(list(mx['2'].values())):6.1%} / {np.mean(list(mx['4'].values())):5.1%}")
    print("\nPer kind at <= 4: your design (average) | 4 families (average) | 4 families (max)")
    a, b, c = per_kind["your design"], per_kind["fixed, 4 families"], per_kind["fixed, 4 families|max"]
    for k in sorted(a, key=lambda k: -b[k]):
        print(f"  {k:<24} {a[k]:4.0%} | {b[k]:4.0%} | {c[k]:4.0%}")
    print("\nOrdinary agent-days on which each check fires (false-alarm load), and the kinds it fires on")
    for c in POLICY + SEQUENCES + ["new_tool_w", "new_asset_w", "new_asset_registered", "calls_1h",
                                    "network_16", "client_new", "request_size", "call_without_init"]:
        rate = np.mean([res[n]["benign_day_rate"][c] for n in ORGS])
        line = f"  {c:<26} {rate:6.1%}"
        if c in res[ORGS[0]]["fires_on_kind"]:
            hits = mean_kinds([res[n]["fires_on_kind"][c] for n in ORGS])
            top = sorted(hits.items(), key=lambda kv: -kv[1])[:4]
            line += "   fires on: " + ", ".join(f"{k} {v:.0%}" for k, v in top if v > 0)
        print(line)


if __name__ == "__main__":
    main()
