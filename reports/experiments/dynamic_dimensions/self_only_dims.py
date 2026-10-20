"""Self-only high-level dimensions: every dimension compares an identity with its own past only.

Constraints (from the user): no tool-type-specific dimensions (no "writes today"), no user id
(the identity is whatever the log carries: the agent, a shared token, or only the session), and no
comparison with other users (no team fill-in, no org-rare, no peers).

Dimensions, each a surprise in bits against the identity's own last 90 days:
    next_tool        this tool right after the previous one in the session (own counts, Laplace)
    tool_repeat_10m  same tool calls in the last 10 minutes vs own usual counts
    calls_today      tool calls so far today vs own past days
    tool_new         a tool not used by this identity in 90 days, vs own novelty rate
    network_new      a /16 network range not used in 90 days, vs own novelty rate
    client_new       a client family (name without version) not used in 90 days
    networks_1h      distinct /16 ranges in the last hour vs own usual
    clients_1h       distinct client families in the last hour vs own usual

Run:  python self_only_dims.py w2/github_M.csv.gz [w2/github_M__shared10.csv.gz ...]
      (writes ../../../runs/dynamic_dimensions/self/<name>.npz)
"""
from __future__ import annotations

import csv
import gzip
import math
import sys
from array import array
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

from detectors import Hist, vbin

csv.field_size_limit(10**9)
W, DAY = 90, 86400.0
MIN_HISTORY = 20
OUT = Path(__file__).resolve().parents[3] / "runs" / "dynamic_dimensions" / "self"
DIMS = ["next_tool", "tool_repeat_10m", "calls_today", "tool_new", "network_new", "client_new",
        "networks_1h", "clients_1h"]
LABELS = ["agent", "strange", "episode", "legit"]


def bits(p: float) -> float:
    return -math.log2(min(1.0, max(p, 1e-12)))


class Identity:
    """Everything kept for one identity (agent, shared token or session)."""
    __slots__ = ("steps", "froms", "log", "calls", "last_tool", "recent", "hists", "seen", "rate",
                 "today", "today_calls", "daily", "hour_nets", "hour_clients")

    def __init__(self):
        self.steps, self.froms, self.log, self.calls = Counter(), Counter(), deque(), 0
        self.last_tool: dict[str, str] = {}
        self.recent: deque = deque()
        self.hists: dict[str, Hist] = {}
        self.seen: dict[str, dict[str, int]] = defaultdict(dict)
        self.rate: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self.today, self.today_calls = -1, 0
        self.daily: deque = deque(maxlen=W)
        self.hour_nets: deque = deque()
        self.hour_clients: deque = deque()


class Engine:
    def __init__(self, n_tools: int):
        self.n_tools = n_tools
        self.ids: dict[str, Identity] = defaultdict(Identity)
        self.day = -1

    def _hist(self, st: Identity, key: str, x: float) -> float:
        h = st.hists.get(key)
        if h is None:
            h = st.hists[key] = Hist(W)
        h.expire(self.day)
        b = vbin(x)
        s = bits(h.p_upper(b)) if h.n >= MIN_HISTORY else 0.0
        h.add(self.day, b)
        return s

    def _novel(self, st: Identity, kind: str, value: str) -> float:
        last = st.seen[kind].get(value)
        new = last is None or last <= self.day - W
        r = st.rate[kind]
        s = bits((r[1] + 1) / (r[0] + 1)) if new and r[0] >= MIN_HISTORY else 0.0
        r[0] += 1
        r[1] += new
        st.seen[kind][value] = self.day
        return s

    def _window(self, q: deque, ts: float, value: str) -> int:
        q.append((ts, value))
        while q[0][0] < ts - 3600:
            q.popleft()
        return len({v for _, v in q})

    def score(self, r: dict, key: str) -> list[float]:
        ts = float(r["ts"])
        self.day = int(ts // DAY)
        st = self.ids[key]
        out = dict.fromkeys(DIMS, 0.0)
        net = ".".join(r["address"].split(".")[:2])
        fam = r["client"].split("/")[0].strip().lower()
        out["network_new"] = self._novel(st, "net", net)
        out["client_new"] = self._novel(st, "client", fam)
        out["networks_1h"] = self._hist(st, "nets1h", self._window(st.hour_nets, ts, net))
        out["clients_1h"] = self._hist(st, "clients1h", self._window(st.hour_clients, ts, fam))
        if r["method"] != "tools/call":
            return [out[d] for d in DIMS]
        tool = r["tool"]
        # next tool after the previous one in the session, own counts only (90-day window)
        while st.log and st.log[0][0] <= self.day - W:
            _, p_, t_ = st.log.popleft()
            st.steps[(p_, t_)] -= 1
            st.froms[p_] -= 1
            st.calls -= 1
        prev = st.last_tool.get(r["session"], "<start>")
        n_prev = st.froms[prev]
        if st.calls >= MIN_HISTORY:
            out["next_tool"] = bits((st.steps[(prev, tool)] + 1) / (n_prev + self.n_tools))
        st.steps[(prev, tool)] += 1
        st.froms[prev] += 1
        st.calls += 1
        st.log.append((self.day, prev, tool))
        st.last_tool[r["session"]] = tool
        # same tool in the last 10 minutes
        st.recent.append((ts, tool))
        while st.recent[0][0] < ts - 600:
            st.recent.popleft()
        out["tool_repeat_10m"] = self._hist(st, "trep", sum(1 for _, t in st.recent if t == tool))
        # calls so far today against own past days
        if st.today != self.day:
            if st.today >= 0:
                st.daily.append(st.today_calls)
            st.today, st.today_calls = self.day, 0
        st.today_calls += 1
        if len(st.daily) >= 10:
            out["calls_today"] = bits((sum(1 for v in st.daily if v >= st.today_calls) + 1)
                                      / (len(st.daily) + 1))
        out["tool_new"] = self._novel(st, "tool", tool)
        return [out[d] for d in DIMS]


def run(path: Path) -> None:
    with gzip.open(path, "rt") as fh:
        tools = set()
        for r in csv.DictReader(fh):                           # one pass to learn the catalogue size
            if r["tool"]:
                tools.add(r["tool"])
    eng = Engine(max(1, len(tools)))
    cols = [array("f") for _ in DIMS]
    ts, labels = array("d"), {k: [] for k in LABELS}
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            for c, v in zip(cols, eng.score(r, r["agent"])):
                c.append(v)
            ts.append(float(r["ts"]))
            for k in LABELS:
                labels[k].append(r[k])
    OUT.mkdir(parents=True, exist_ok=True)
    name = path.name.replace(".csv.gz", "")
    np.savez_compressed(OUT / f"{name}.npz", cols=np.array(DIMS), ts=np.frombuffer(ts),
                        scores=np.stack([np.frombuffer(c, dtype=np.float32) for c in cols], 1),
                        **{k: np.array(v) for k, v in labels.items()})
    print(f"{name}: {len(ts):,} messages x {len(DIMS)} self-only dimensions", flush=True)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(Path(p))
