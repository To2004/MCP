"""Scale test: a lean, production-style engine for the selected dimensions, run with 10,000 agents.

What it measures:
  - per-call scoring latency (p50 / p99) and single-core throughput
  - memory: total and per agent, after a month of traffic
  - the weekly peer computation (who is similar to whom) for 10,000 agents

Design choices that make it scale (all state is per agent, so it shards by agent id):
  - "how unusual is this number" uses an exponentially decayed 32-bin log histogram per agent and
    measure (fixed size, no day buckets), so a call costs O(32) whatever the history length
  - "first time" sets keep value -> last-seen day and are pruned after 90 days; recipients are a
    bounded LRU so one agent cannot grow its state without limit
  - rolling counts (repeats in 10 min, addresses per hour) are short deques
  - peers: sparse agent x (tool, asset) matrix, top-k cosine via scipy sparse products in blocks

Run:  python engine_scale.py --agents 10000 --days 30 --calls-per-agent-day 40
"""
from __future__ import annotations

import argparse
import math
import random
import resource
import time
from collections import OrderedDict, defaultdict, deque

import numpy as np
from scipy import sparse

NB, HALF_LIFE_DAYS, TTL_DAYS, LRU_WHO = 32, 30.0, 90, 2000
DAY = 86400.0


def b(x: float) -> int:
    return min(NB - 1, int(2 * math.log2(1 + max(0.0, x))))


class DecayHist:
    """Fixed-size decayed histogram; upper-tail p-value of a value against the agent's own past."""
    __slots__ = ("h", "n", "t")

    def __init__(self):
        self.h = [0.0] * NB
        self.n = 0.0
        self.t = 0.0

    def surprise_and_add(self, x, ts):
        if ts > self.t:
            f = 0.5 ** ((ts - self.t) / (HALF_LIFE_DAYS * DAY))
            if f < 0.999:
                self.h = [v * f for v in self.h]
                self.n *= f
            self.t = ts
        k = b(x)
        s = -math.log2((sum(self.h[k:]) + 1) / (self.n + 1)) if self.n >= 20 else 0.0
        self.h[k] += 1
        self.n += 1
        return s


class Agent:
    __slots__ = ("hist", "seen", "rate", "recent", "addr", "who", "day", "calls", "reach", "ctx")

    def __init__(self):
        self.hist = {}
        self.seen = defaultdict(dict)            # kind -> value -> last day
        self.rate = defaultdict(lambda: [0, 0])  # kind -> [checks, novel]
        self.recent = deque()                    # (ts, call hash) for 10 minutes
        self.addr = deque()                      # (ts, address) for 1 hour
        self.who = OrderedDict()
        self.day, self.calls, self.reach = -1, 0, 0.0
        self.ctx = defaultdict(lambda: defaultdict(int))

    def novel(self, kind, value, day):
        seen = self.seen[kind]
        last = seen.get(value)
        new = last is None or last <= day - TTL_DAYS
        r = self.rate[kind]
        s = -math.log2((r[1] + 1) / (r[0] + 1)) if new and r[0] >= 20 else 0.0
        r[0] += 1
        r[1] += new
        seen[value] = day
        return s

    def prune(self, day):
        for seen in self.seen.values():
            for v in [v for v, d in seen.items() if d <= day - TTL_DAYS]:
                del seen[v]


class Engine:
    def __init__(self):
        self.agents: dict[int, Agent] = {}
        self.touch = defaultdict(set)            # asset -> agents (for peer-rare first touch)

    def score(self, ag, ts, tool, keys, asset, how_much, who, addr, client, ua, call_hash, nbytes):
        a = self.agents.get(ag)
        if a is None:
            a = self.agents[ag] = Agent()
        day = int(ts // DAY)
        if day != a.day:
            if a.day >= 0 and day % 7 == 0:
                a.prune(day)
            a.day, a.calls, a.reach = day, 0, 0.0
        a.calls += 1
        a.reach += how_much
        out = {}
        out["arg_keys_new"] = a.novel("keys", (tool, keys), day)
        out["which_new"] = a.novel("asset", asset, day) if asset >= 0 else 0.0
        s = 0.0
        for k, v in (("addr", addr), ("client", client), ("ua", ua)):
            c = a.ctx[k]
            n, m = sum(c.values()), len(c)
            p0 = (c[v] / n) * (1 - m / (n + m)) if c[v] else 1 / (n + m + 1)
            s += -math.log2(p0) if n >= 20 else 0.0
            c[v] += 1
        out["client_context"] = s
        a.recent.append((ts, call_hash))
        while a.recent[0][0] < ts - 600:
            a.recent.popleft()
        reps = sum(1 for _, h in a.recent if h == call_hash)
        a.addr.append((ts, addr))
        while a.addr[0][0] < ts - 3600:
            a.addr.popleft()
        for name, x in (("identical_10m", reps), ("addresses_1h", len({x for _, x in a.addr})),
                        ("calls_today", a.calls), ("reach_today", a.reach), ("bytes", nbytes / 20)):
            h = a.hist.get(name)
            if h is None:
                h = a.hist[name] = DecayHist()
            out[name] = h.surprise_and_add(x, ts)
        out["user_agent_new"] = a.novel("ua", ua, day)
        best = 0.0
        for w in who:
            if w not in a.who:
                best = max(best, a.novel("who", w, day))
            a.who[w] = day
            a.who.move_to_end(w)
            if len(a.who) > LRU_WHO:
                a.who.popitem(last=False)
        out["who_new"] = best
        if asset >= 0:
            self.touch[asset].add(ag)
        return out


def make_population(n_agents, rng):
    tools = list(range(26))
    key_sets = {t: [rng.getrandbits(32) for _ in range(rng.randint(2, 6))] for t in tools}
    pop = []
    for i in range(n_agents):
        team = i % 500
        pop.append({"tools": rng.sample(tools, rng.randint(4, 10)), "assets": [team * 20 + j for j in range(20)],
                    "shared": list(range(10000, 10050)), "addr": [rng.getrandbits(32), rng.getrandbits(32)],
                    "client": rng.randrange(6), "ua": rng.randrange(6)})
    return pop, key_sets


def peers_benchmark(engine, n_agents, k=5, block=2000):
    """Top-k cosine neighbours of every agent over a sparse agent x asset matrix."""
    rows, cols = [], []
    for asset, ags in engine.touch.items():
        for ag in ags:
            rows.append(ag)
            cols.append(asset)
    M = sparse.csr_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(n_agents, max(cols) + 1))
    norms = np.sqrt(np.asarray(M.multiply(M).sum(1)).ravel()) + 1e-9
    M = sparse.diags(1 / norms) @ M
    t0 = time.perf_counter()
    top = np.zeros((n_agents, k), np.int32)
    for s in range(0, n_agents, block):
        S = (M[s:s + block] @ M.T).toarray()
        for i in range(S.shape[0]):
            S[i, s + i] = -1
        top[s:s + block] = np.argpartition(-S, k, axis=1)[:, :k]
    return time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=10000)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--calls-per-agent-day", type=int, default=40)
    a = ap.parse_args()
    rng = random.Random(7)
    pop, key_sets = make_population(a.agents, rng)
    eng = Engine()
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    lat, n = [], 0
    t_all = time.perf_counter()
    for day in range(a.days):
        order = [ag for ag in range(a.agents) for _ in range(a.calls_per_agent_day)]
        rng.shuffle(order)
        for j, ag in enumerate(order):
            p = pop[ag]
            ts = day * DAY + j * (DAY / len(order))
            tool = rng.choice(p["tools"])
            asset = rng.choice(p["assets"]) if rng.random() < 0.8 else rng.choice(p["shared"])
            who = [rng.getrandbits(20) for _ in range(rng.randint(0, 3))] if tool < 4 else []
            t0 = time.perf_counter_ns()
            eng.score(ag, ts, tool, rng.choice(key_sets[tool]), asset, float(rng.choice((10, 30, 50, 100))), who,
                      rng.choice(p["addr"]), p["client"], p["ua"], hash((tool, asset)), rng.randint(150, 400))
            if n % 50 == 0:
                lat.append(time.perf_counter_ns() - t0)
            n += 1
        print(f"day {day + 1}: {n:,} calls, {n / (time.perf_counter() - t_all):,.0f} calls/s", flush=True)
    wall = time.perf_counter() - t_all
    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peer_s = peers_benchmark(eng, a.agents)
    lat = np.array(lat) / 1000
    print(f"\nRESULT agents={a.agents} calls={n:,} days={a.days}")
    print(f"RESULT throughput_single_core={n / wall:,.0f} calls/s")
    print(f"RESULT latency_us p50={np.percentile(lat, 50):.1f} p99={np.percentile(lat, 99):.1f} max={lat.max():.0f}")
    print(f"RESULT memory_peak_MB={rss1 / 1024:.0f} (start {rss0 / 1024:.0f}) per_agent_KB={(rss1 - rss0) / a.agents:.1f}")
    print(f"RESULT weekly_peer_topk_seconds={peer_s:.1f}")


if __name__ == "__main__":
    main()
