"""Reference engine for the dynamic formula in FORMULA.md, with the two new ideas as switches.

    R_dynamic = R_static x min(CAP, e^(LAMBDA * (X_pace + X_path + X_place)))

Per call and dimension: surprise u = -log2(p) against the agent's own last 90 days, excess
x = max(0, u - B), where B is the organisation's 99.5th percentile of u over the last 30 days.
Each family keeps its largest x.

Idea A, crowd ("one agent, or everyone?"): a thing is "shared" when at least ORG_NOTICE_AGENTS
agents were clearly above normal on it (X >= CROWD_MIN_X) in the window: the same step, the same tool
in the same hour, or the same new network or client. A shared thing becomes one organisation notice
and stops counting for each agent (its X is 0). Calls show the crowd so far; the daily check runs at
the end of the day and counts the whole day. Variant "graded" is the version tried first:
X / (1 + c / CROWD_HALF) instead of the fold.
Idea B, settling ("changed, or misbehaving?"): a step this agent made on at least SETTLE_DAYS
different days of the last 7 is a new habit, so its Path excess is 0.

The engine reads only: time, agent (user + agent app), team, session, tool name, client address and
client name. It never reads tool inputs or which asset a call touches.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

DAY = 86400.0
HISTORY_DAYS = 90
REPEAT_WINDOW_S = 600.0
TEAM_FILL_CALLS = 20.0
MIN_STEP_HISTORY = 10
MIN_CALLS = 20
BASELINE_QUANTILE = 0.995
BASELINE_DAYS = 30
LAMBDA = math.log(2) / 10
CAP = 8.0
CROWD_MIN_X = 3.0
CROWD_HALF = 3.0
CROWD_WINDOW_S = {"pace": 3600.0, "path": 7 * DAY, "place": 7 * DAY}
ORG_NOTICE_AGENTS = 5
SETTLE_DAYS, SETTLE_WINDOW_DAYS = 3, 7
FAMILIES = {"pace": ("repeat_10m",), "path": ("next_tool",), "place": ("new_network", "new_client")}
DIMENSIONS = tuple(d for dims in FAMILIES.values() for d in dims)
VARIANTS = ("base", "graded", "crowd", "settle", "both")


@dataclass(frozen=True)
class Call:
    """What the gateway log gives for one tools/call request."""
    ts: float
    agent: str
    team: str
    session: str
    tool: str
    address: str
    client: str


@dataclass
class Scored:
    """One scored call: surprises, excesses, family values and the multiplier per variant."""
    call: Call
    u: dict[str, float]
    x: dict[str, float]
    family: dict[str, float]
    keys: dict[str, str]
    crowd: dict[str, int]
    settled: bool
    r_static: float
    multiplier: dict[str, float] = field(default_factory=dict)

    def risk(self, variant: str = "base") -> float:
        """R_dynamic = R_static x multiplier; never below the static score."""
        return self.r_static * self.multiplier[variant]


def network_range(address: str) -> str:
    """The /16 range of an IPv4 address (general form: no specific host)."""
    return ".".join(address.split(".")[:2])


def client_family(client: str) -> str:
    """Client program name without its version."""
    return client.split("/")[0].strip().lower()


def bits(p: float) -> float:
    return -math.log2(max(p, 1e-12))


def adjusted(family: str, x: float, settled: bool, crowd: int, variant: str) -> float:
    """A family's excess under a variant: settling zeroes a settled Path step; a shared thing
    (crowd = other agents on it) is folded into an organisation notice."""
    if variant in ("settle", "both") and family == "path" and settled:
        return 0.0
    if variant in ("crowd", "both") and crowd + 1 >= ORG_NOTICE_AGENTS:
        return 0.0
    if variant == "graded":
        return x / (1 + crowd / CROWD_HALF)
    return x


class WindowCounter:
    """Counts of keys seen in the last HISTORY_DAYS days."""

    def __init__(self):
        self.counts: Counter = Counter()
        self.log: deque = deque()

    def add(self, day: int, key) -> None:
        self.counts[key] += 1
        self.log.append((day, key))

    def prune(self, day: int) -> None:
        while self.log and self.log[0][0] <= day - HISTORY_DAYS:
            _, key = self.log.popleft()
            self.counts[key] -= 1


class AgentState:
    def __init__(self):
        self.steps, self.froms = WindowCounter(), WindowCounter()
        self.step_days: dict[tuple[str, str], deque] = defaultdict(deque)
        self.last_tool: dict[str, str] = {}
        self.recent: deque = deque()
        self.repeat_counts = WindowCounter()
        self.seen: dict[str, dict[str, int]] = {"new_network": {}, "new_client": {}}
        self.novel: dict[str, list[int]] = {"new_network": [0, 0], "new_client": [0, 0]}


class Engine:
    """Scores calls one by one; keeps per-agent and per-organisation state."""

    def __init__(self, n_tools: int, team_fill: bool = True):
        self.n_tools = n_tools
        self.team_fill = team_fill
        self.agents: dict[str, AgentState] = defaultdict(AgentState)
        self.team_steps: dict[str, WindowCounter] = defaultdict(WindowCounter)
        self.team_froms: dict[str, WindowCounter] = defaultdict(WindowCounter)
        self.values: dict[str, deque] = {d: deque() for d in DIMENSIONS}
        self.today_values: dict[str, list[float]] = {d: [] for d in DIMENSIONS}
        self.baseline: dict[str, float] = {d: math.inf for d in DIMENSIONS}
        self.day = -1
        self.days_seen = 0
        self.crowd_events: dict[tuple[str, str], list[tuple[float, str]]] = defaultdict(list)
        self.entries: dict[tuple[str, int], list[tuple[str, float, bool, str, float]]] = \
            defaultdict(list)
        self.active: dict[int, set[str]] = defaultdict(set)

    def _roll_day(self, day: int) -> None:
        """New day: B = the 99.5th percentile of each dimension's surprise over the last 30 days."""
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
                self.baseline[d] = v[min(len(v) - 1, int(BASELINE_QUANTILE * len(v)))] if v else math.inf

    def _path(self, st: AgentState, c: Call, day: int) -> tuple[float, str, bool]:
        """Surprise of this step for this agent, the previous tool, and whether it has settled."""
        prev = st.last_tool.get(c.session, "<start>")
        ts_, tf = self.team_steps[c.team], self.team_froms[c.team]
        for w in (st.steps, st.froms, ts_, tf):
            w.prune(day)
        p_team = (ts_.counts[(prev, c.tool)] + 1) / (tf.counts[prev] + self.n_tools)
        fill = TEAM_FILL_CALLS if self.team_fill else 0.0
        n_prev = st.froms.counts[prev]
        p = (st.steps.counts[(prev, c.tool)] + fill * p_team) / (n_prev + fill) if n_prev + fill else 1.0
        enough = n_prev + (tf.counts[prev] if self.team_fill else 0) >= MIN_STEP_HISTORY
        days = st.step_days[(prev, c.tool)]
        while days and days[0] < day - SETTLE_WINDOW_DAYS:
            days.popleft()
        settled = sum(1 for d in days if d < day) >= SETTLE_DAYS
        if not days or days[-1] != day:
            days.append(day)
        for w, key in ((st.steps, (prev, c.tool)), (st.froms, prev), (ts_, (prev, c.tool)), (tf, prev)):
            w.add(day, key)
        st.last_tool[c.session] = c.tool
        return (bits(p) if enough else 0.0), prev, settled

    def _pace(self, st: AgentState, c: Call, day: int) -> float:
        """Surprise of this tool's count in the last 10 minutes, against this agent's usual counts."""
        while st.recent and st.recent[0][0] < c.ts - REPEAT_WINDOW_S:
            st.recent.popleft()
        st.recent.append((c.ts, c.tool))
        count = sum(1 for _, t in st.recent if t == c.tool)
        st.repeat_counts.prune(day)
        n_hist = len(st.repeat_counts.log)
        at_least = sum(n for k, n in st.repeat_counts.counts.items() if k >= count)
        st.repeat_counts.add(day, count)
        return bits((at_least + 1) / (n_hist + 1)) if n_hist >= MIN_CALLS else 0.0

    def _place(self, st: AgentState, c: Call, day: int) -> dict[str, float]:
        """Surprise of a network range or client family not used in 90 days."""
        u = {}
        for dim, value in (("new_network", network_range(c.address)),
                           ("new_client", client_family(c.client))):
            last = st.seen[dim].get(value)
            new = last is None or last <= day - HISTORY_DAYS
            calls, news = st.novel[dim]
            u[dim] = bits((news + 1) / (calls + 1)) if new and calls >= MIN_CALLS else 0.0
            st.novel[dim] = [calls + 1, news + int(new)]
            st.seen[dim][value] = day
        return u

    def _crowd(self, family: str, key: str, agent: str, start: float, end: float) -> int:
        """Distinct other agents clearly above normal on the same thing between start and end."""
        return len({a for t, a in self.crowd_events[(family, key)] if start <= t <= end and a != agent})

    def score(self, c: Call, r_static: float) -> Scored:
        day = int(c.ts // DAY)
        if day != self.day:
            self._roll_day(day)
        self.active[day].add(c.agent)
        st = self.agents[c.agent]
        u_path, prev, settled = self._path(st, c, day)
        u = {"next_tool": u_path, "repeat_10m": self._pace(st, c, day), **self._place(st, c, day)}
        for d in DIMENSIONS:
            self.today_values[d].append(u[d])
        x = {d: max(0.0, u[d] - self.baseline[d]) for d in DIMENSIONS}
        fam = {f: max(x[d] for d in dims) for f, dims in FAMILIES.items()}
        keys = {"pace": f"{c.tool}@{int(c.ts // 3600)}", "path": f"{prev}>{c.tool}",
                "place": f"net:{network_range(c.address)}" if x["new_network"] >= x["new_client"]
                else f"client:{client_family(c.client)}"}
        crowd = {}
        for f in FAMILIES:
            crowd[f] = 0
            if fam[f] > 0:
                if fam[f] >= CROWD_MIN_X:
                    crowd[f] = self._crowd(f, keys[f], c.agent, c.ts - CROWD_WINDOW_S[f], c.ts)
                    self.crowd_events[(f, keys[f])].append((c.ts, c.agent))
                self.entries[(c.agent, day)].append((f, fam[f], settled and f == "path", keys[f], c.ts))
        s = Scored(c, u, x, fam, keys, crowd, settled, r_static)
        for v in VARIANTS:
            total = sum(adjusted(f, fam[f], settled, crowd[f], v) for f in FAMILIES)
            s.multiplier[v] = min(CAP, math.exp(LAMBDA * total))
        return s

    def day_score(self, agent: str, day: int, variant: str) -> float:
        """End-of-day score: each family's strongest adjusted call, summed; crowd counts the day."""
        best = {f: 0.0 for f in FAMILIES}
        end = (day + 1) * DAY
        crowd_on = variant in ("graded", "crowd", "both")
        for f, x, settled, key, ts in self.entries.get((agent, day), []):
            c = self._crowd(f, key, agent, ts - CROWD_WINDOW_S[f], end) if crowd_on and x >= CROWD_MIN_X else 0
            best[f] = max(best[f], adjusted(f, x, settled, c, variant))
        return sum(best.values())

    def org_notices(self) -> list[tuple[int, str, str, int]]:
        """(day, family, thing, agents) once ORG_NOTICE_AGENTS agents share a thing in a day."""
        out = []
        for (f, key), ev in self.crowd_events.items():
            per_day: dict[int, set[str]] = defaultdict(set)
            for t, a in ev:
                per_day[int(t // DAY)].add(a)
            out += [(d, f, key, len(a)) for d, a in per_day.items() if len(a) >= ORG_NOTICE_AGENTS]
        return sorted(out)

    def daily_flags(self, budget: float, variant: str, floor: float = 0.0):
        """Flag agent-days above a threshold set from the previous 30 days (budget alerts/day),
        and never below floor (bits).

        Returns ({(agent, day): flagged}, {day: threshold}, {(agent, day): score}).
        """
        scores = {(a, d): self.day_score(a, d, variant) for d, agents in self.active.items()
                  for a in agents}
        by_day: dict[int, list[tuple[str, float]]] = defaultdict(list)
        for (a, d), s in scores.items():
            by_day[d].append((a, s))
        flags, thresholds = {}, {}
        for d in sorted(by_day):
            past = sorted((s for dd in range(d - BASELINE_DAYS, d) for _, s in by_day.get(dd, [])
                           if s > 0), reverse=True)
            if d < 2 * BASELINE_DAYS or not past:
                continue
            k = int(budget * BASELINE_DAYS)
            thresholds[d] = thr = max(floor, past[k] if k < len(past) else 0.0)
            for a, s in by_day[d]:
                flags[(a, d)] = s > thr
        return flags, thresholds, scores
