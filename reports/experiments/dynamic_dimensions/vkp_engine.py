"""Reference engine for the Velocity / Knowledge / Place baseline, for the scenario tests.

Every dimension is a surprise u (bits) of this agent's behaviour against its own last 90 days, or,
for the two organisation dimensions, against the organisation. Its signal is the excess over the
organisation's normal level for that dimension, x = max(0, u - B), B = the 99.5th percentile of u
over the previous 30 days. Inside a family the signals are joined one of four ways (the variants);
across families the e-terms multiply:

    average       F = mean of x          R = R_static * e^(lambda * sum of family F)
    average_of_e  factor = mean of e^(lambda * x)          R = R_static * product of factors
    max           F = largest x
    sum           F = sum of x

The engine reads only: time, agent, session, tool name, client address and client name.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

from dims4 import asset_type
from dynamic_engine import Call

DAY = 86400.0
HISTORY_DAYS, ORG_DAYS, BASELINE_DAYS = 90, 30, 30
REPEAT_WINDOW_S, HOUR = 600.0, 3600.0
MIN_HISTORY = 20
BASELINE_QUANTILE = 0.995
LAMBDA = math.log(2) / 10
CAP = 8.0
FAMILIES = {
    "velocity": ("repeat_10m", "calls_today", "calls_1h", "session_duration"),
    "knowledge": ("next_tool", "tool_new", "tool_rarity_self", "tool_new_org_rare", "tool_rarity_org",
                  "asset_types_today"),
    "place": ("network_new", "client_new", "pair_new", "networks_1h", "clients_1h"),
}
DIMENSIONS = tuple(d for dims in FAMILIES.values() for d in dims)
VARIANTS = ("average", "average_of_e", "max", "sum")


def bits(p: float) -> float:
    return -math.log2(min(1.0, max(p, 1e-12)))


def network_range(address: str) -> str:
    return ".".join(address.split(".")[:2])


def client_family(client: str) -> str:
    return client.split("/")[0].strip().lower()


def log_bin(x: float) -> int:
    return int(4 * math.log2(1 + max(0.0, x)))


class Window:
    """Counts of keys over the last `days` days."""

    def __init__(self, days: int):
        self.days, self.counts, self.total, self.log = days, Counter(), 0, deque()

    def prune(self, day: int) -> None:
        while self.log and self.log[0][0] <= day - self.days:
            _, key = self.log.popleft()
            self.counts[key] -= 1
            self.total -= 1

    def add(self, day: int, key) -> None:
        self.counts[key] += 1
        self.total += 1
        self.log.append((day, key))

    def upper(self, key: int) -> float:
        """Share of the history at least as large as key (keys are ordered bins)."""
        return (sum(n for k, n in self.counts.items() if k >= key) + 1) / (self.total + 1)


@dataclass
class Scored:
    call: Call
    u: dict[str, float]
    x: dict[str, float]
    r_static: float
    multiplier: dict[str, float] = field(default_factory=dict)

    def risk(self, variant: str) -> float:
        return self.r_static * self.multiplier[variant]

    def fired(self) -> list[str]:
        return [d for d in DIMENSIONS if self.x[d] > 0]


class Agent:
    def __init__(self):
        self.steps, self.froms = Window(HISTORY_DAYS), Window(HISTORY_DAYS)
        self.tools = Window(HISTORY_DAYS)
        self.last_tool: dict[str, str] = {}
        self.session_start: dict[str, float] = {}
        self.recent: deque = deque()
        self.hour: deque = deque()
        self.hists = defaultdict(lambda: Window(HISTORY_DAYS))
        self.seen: dict[str, dict[str, int]] = defaultdict(dict)
        self.rate: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self.day, self.calls_today, self.types_today = -1, 0, set()
        self.daily_calls: deque = deque(maxlen=HISTORY_DAYS)
        self.daily_types: deque = deque(maxlen=HISTORY_DAYS)


class Engine:
    def __init__(self, n_tools: int, dims: tuple[str, ...] = DIMENSIONS):
        """dims: the dimensions to use; each family keeps only the ones listed."""
        self.n_tools = n_tools
        self.families = {f: tuple(d for d in ds if d in dims) for f, ds in FAMILIES.items()}
        self.families = {f: ds for f, ds in self.families.items() if ds}
        self.agents: dict[str, Agent] = defaultdict(Agent)
        self.org_tools = Window(ORG_DAYS)
        self.tool_users: dict[str, dict[str, int]] = defaultdict(dict)
        self.last_seen: dict[str, int] = {}
        self.values = {d: deque() for d in DIMENSIONS}
        self.today_values = {d: [] for d in DIMENSIONS}
        self.baseline = {d: math.inf for d in DIMENSIONS}
        self.day, self.days_seen = -1, 0
        self.day_scores: dict[tuple[str, int], dict[str, float]] = defaultdict(
            lambda: dict.fromkeys(VARIANTS, 0.0))

    def _roll(self, day: int) -> None:
        if self.day >= 0:
            for d in DIMENSIONS:
                self.values[d].append(self.today_values[d])
                while len(self.values[d]) > BASELINE_DAYS:
                    self.values[d].popleft()
                self.today_values[d] = []
            self.days_seen += 1
        self.day = day
        if self.days_seen >= BASELINE_DAYS:
            for d in DIMENSIONS:
                v = sorted(x for vs in self.values[d] for x in vs)
                self.baseline[d] = v[min(len(v) - 1, int(BASELINE_QUANTILE * len(v)))]

    def _hist(self, st: Agent, key: str, value: float, day: int) -> float:
        h = st.hists[key]
        h.prune(day)
        b = log_bin(value)
        s = bits(h.upper(b)) if h.total >= MIN_HISTORY else 0.0
        h.add(day, b)
        return s

    def _novel(self, st: Agent, kind: str, value: str, day: int) -> tuple[float, bool]:
        last = st.seen[kind].get(value)
        new = last is None or last <= day - HISTORY_DAYS
        calls, news = st.rate[kind]
        s = bits((news + 1) / (calls + 1)) if new and calls >= MIN_HISTORY else 0.0
        st.rate[kind] = [calls + 1, news + int(new)]
        st.seen[kind][value] = day
        return s, new

    def _surprises(self, st: Agent, c: Call, day: int) -> dict[str, float]:
        u = dict.fromkeys(DIMENSIONS, 0.0)
        net, fam = network_range(c.address), client_family(c.client)
        u["network_new"] = self._novel(st, "net", net, day)[0]
        u["client_new"] = self._novel(st, "client", fam, day)[0]
        u["pair_new"] = self._novel(st, "pair", f"{net}|{fam}", day)[0]
        # several origins within an hour: distinct networks and client families in the last hour
        st.hour.append((c.ts, net, fam))
        while st.hour[0][0] < c.ts - HOUR:
            st.hour.popleft()
        u["networks_1h"] = self._hist(st, "nets1h", len({n for _, n, _ in st.hour}), day)
        u["clients_1h"] = self._hist(st, "clients1h", len({f for _, _, f in st.hour}), day)
        # velocity
        st.recent.append((c.ts, c.tool))
        while st.recent[0][0] < c.ts - REPEAT_WINDOW_S:
            st.recent.popleft()
        u["repeat_10m"] = self._hist(st, "repeat", sum(1 for _, t in st.recent if t == c.tool), day)
        if st.day != day:
            if st.day >= 0:
                st.daily_calls.append(st.calls_today)
                st.daily_types.append(len(st.types_today))
            st.day, st.calls_today, st.types_today = day, 0, set()
        st.calls_today += 1
        st.types_today.add(asset_type(c.tool))
        if len(st.daily_calls) >= 10:
            u["calls_today"] = bits((sum(1 for v in st.daily_calls if v >= st.calls_today) + 1)
                                    / (len(st.daily_calls) + 1))
            u["asset_types_today"] = bits((sum(1 for v in st.daily_types if v >= len(st.types_today))
                                           + 1) / (len(st.daily_types) + 1))
        calls_hour = sum(1 for t, _, _ in st.hour if t >= c.ts - HOUR)
        u["calls_1h"] = self._hist(st, "calls1h", calls_hour, day)
        start = st.session_start.setdefault(c.session, c.ts)
        u["session_duration"] = self._hist(st, "session", (c.ts - start) / 60, day)
        # knowledge
        prev = st.last_tool.get(c.session, "<start>")
        for w in (st.steps, st.froms, st.tools):
            w.prune(day)
        if st.tools.total >= MIN_HISTORY:
            u["next_tool"] = bits((st.steps.counts[(prev, c.tool)] + 1)
                                  / (st.froms.counts[prev] + self.n_tools))
            u["tool_rarity_self"] = bits((st.tools.counts[c.tool] + 1) / (st.tools.total + self.n_tools))
        st.steps.add(day, (prev, c.tool))
        st.froms.add(day, prev)
        st.tools.add(day, c.tool)
        st.last_tool[c.session] = c.tool
        u["tool_new"], new_tool = self._novel(st, "tool", c.tool, day)
        if new_tool and st.rate["tool"][0] > MIN_HISTORY:
            users = self.tool_users[c.tool]
            live = sum(1 for d in users.values() if d > day - HISTORY_DAYS)
            active = sum(1 for d in self.last_seen.values() if d > day - HISTORY_DAYS)
            u["tool_new_org_rare"] = bits((live + 1) / (active + 1))
        self.tool_users[c.tool][c.agent] = day
        self.org_tools.prune(day)
        if self.org_tools.total >= MIN_HISTORY:
            u["tool_rarity_org"] = bits((self.org_tools.counts[c.tool] + 1)
                                        / (self.org_tools.total + self.n_tools))
        self.org_tools.add(day, c.tool)
        return u

    def score(self, c: Call, r_static: float) -> Scored:
        day = int(c.ts // DAY)
        if day != self.day:
            self._roll(day)
        self.last_seen[c.agent] = day
        st = self.agents[c.agent]
        u = self._surprises(st, c, day)
        for d in DIMENSIONS:
            self.today_values[d].append(u[d])
        x = {d: max(0.0, u[d] - self.baseline[d]) for d in DIMENSIONS}
        s = Scored(c, u, x, r_static)
        rec = self.day_scores[(c.agent, day)]
        for v in VARIANTS:
            total = 0.0
            for dims in self.families.values():
                vals = [x[d] for d in dims]
                if v == "average":
                    total += sum(vals) / len(vals)
                elif v == "max":
                    total += max(vals)
                elif v == "sum":
                    total += sum(vals)
                else:
                    total += math.log(sum(math.exp(LAMBDA * a) for a in vals) / len(vals)) / LAMBDA
            s.multiplier[v] = min(CAP, math.exp(LAMBDA * total))
            rec[v] = max(rec[v], total)
        return s

    def daily_flags(self, budget: int, variant: str):
        """Flag the top `budget` agent-days of each day (score > 0). Returns flags, ranks, scores."""
        by_day: dict[int, list[tuple[float, str]]] = defaultdict(list)
        for (a, d), v in self.day_scores.items():
            by_day[d].append((v[variant], a))
        flags, ranks = {}, {}
        for d, rows in by_day.items():
            rows.sort(reverse=True)
            for i, (s, a) in enumerate(rows):
                ranks[(a, d)] = i + 1
                flags[(a, d)] = i < budget and s > 0 and d >= 2 * BASELINE_DAYS
        return flags, ranks, {k: v[variant] for k, v in self.day_scores.items()}
