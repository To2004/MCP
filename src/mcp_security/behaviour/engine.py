"""The dynamic layer's behaviour multiplier: how strange is this call for this agent?

Each dimension compares the agent only with his own last 90 days and gives a score ``s``
between 0 and 1, where 0.5 is the edge of ordinary ("twice his usual"). The strangest
dimension sets the call's multiplier::

    M = 5   ** (2S - 1)    when S >= 0.5     (the edge of ordinary -> 1, the strangest -> 5)
    M = 0.7 ** (1 - 2S)    when S <  0.5     (familiar -> below 1, very familiar -> 0.7)

so ``M`` lies in [0.7, 5] by its shape alone (no clipping), and a static level of 1-5 times
``M`` lies in [0.7, 25]. Three kinds of score:

- **more than his usual** (calls in the last hour, session length, request size)::

      s = (v + u) / (v + u + 2 * (his average + u))      u = 1 call, 1 minute or 1 KB

- **rarer than his usual** (tool, asset, time of day): how many times a day he does
  something this rare, ``e = (his calls on things at most this common + 1) / (active days + 1)``,
  then ``s = c / (1 + 2 * e)`` with ``c = 0.9`` for tools (a first-time tool ~x3.2-3.6);
- **policy rules**: broken -> the rule's value (0.9 by default, x3.6; protocol skip 0.7, x1.9).

The design and its stress test: ``reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md``.
Messages must reach :meth:`BehaviourEngine.observe` in arrival order; every request message
counts (``initialize`` and ``tools/list`` too: they carry the origin and the handshake).
"""

from __future__ import annotations

from collections import Counter, OrderedDict, deque
from dataclasses import dataclass, field
from ipaddress import ip_address

DAY_S = 86_400.0
HOUR_S = 3_600.0
MINUTE_S = 60.0
CALL_METHOD = "tools/call"
INIT_METHOD = "initialize"
WRITE = "write"
READ = "read"

MAX_MULTIPLIER = 5.0
MIN_MULTIPLIER = 0.7
EDGE_OF_ORDINARY = 0.5

#: Dimension names, as they appear in a verdict's ``scores`` and ``strongest``.
CALLS_LAST_HOUR = "calls_last_hour"
SESSION_LENGTH = "session_length"
REQUEST_SIZE = "request_size"
TOOL = "tool"
ASSET = "asset"
TIME_OF_DAY = "time_of_day"
NEW_NETWORK = "new_network"
NEW_CLIENT = "new_client"
BURST = "burst"
SEQUENCE = "sequence"
REQUEST_TOO_BIG = "request_too_big"
PROTOCOL_SKIP = "protocol_skip"


@dataclass(frozen=True)
class BehaviourConfig:
    """Every knob of the behaviour multiplier; the defaults are the stress-tested design."""

    history_days: int = 90
    warmup_calls: int = 5  # until an agent has made this many tool calls, M = 1
    tolerance: float = 2.0  # up to twice his usual (or every other day) is ordinary
    call_unit: float = 1.0
    minute_unit: float = 1.0
    byte_unit: float = 1_000.0  # requests under ~1 KB never matter
    tool_ceiling: float = 0.9  # a first-time tool tops out near x3.6
    rule_score: float = 0.9  # x3.6
    protocol_skip_score: float = 0.7  # x1.9
    burst_per_minute: int = 20
    request_limit_bytes: int = 10_000
    ipv4_prefix: int = 16  # a "new network" is a new /16, not a new address
    ipv6_prefix: int = 48
    sensitive_level: int = 4  # asset sensitivity at or above which reads and writes are watched
    read_memory_days: int = 7  # a write to a sensitive asset not read in this long is blind
    normally_initializes_after: int = 3  # sessions seen before "he normally initializes" counts
    max_sessions: int = 50_000  # open sessions remembered across all agents (oldest dropped)
    #: tool -> tools one of which must come earlier in the session (e.g. merge after a review)
    requires_before: dict[str, frozenset[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    """What the gateway knows about one request message, without reading its arguments."""

    ts: float
    agent: str
    method: str
    session: str | None = None
    tool: str | None = None
    asset: str | None = None  # the asset the call resolves to (the static side's binding)
    sensitivity: int | None = None  # that asset's sensitivity 1-5 (static scan)
    operation: str | None = None  # "read" or "write" (static scan)
    address: str | None = None
    client: str | None = None  # "name/version" from initialize or _meta
    size: int = 0  # bytes of the message


@dataclass(frozen=True)
class Verdict:
    """The behaviour multiplier for one message, and why."""

    multiplier: float
    strongest: str | None  # the dimension that set it; None when nothing took part
    score: float | None  # that dimension's score (S)
    scores: dict[str, float]  # every dimension that took part
    learning: bool  # still in warm-up: M is 1 whatever happened

    @property
    def above_ordinary(self) -> list[str]:
        """Dimensions past the edge of ordinary, strongest first (a tie-breaker for ranking)."""
        hot = [(s, d) for d, s in self.scores.items() if s > EDGE_OF_ORDINARY]
        return [d for _, d in sorted(hot, reverse=True)]


def multiplier(score: float) -> float:
    """The curve from a score in [0, 1] to a multiplier in [0.7, 5]; exactly 1 at 0.5."""
    if score >= EDGE_OF_ORDINARY:
        return MAX_MULTIPLIER ** (2 * score - 1)
    return MIN_MULTIPLIER ** (1 - 2 * score)


def network_of(address: str | None, config: BehaviourConfig) -> str | None:
    """The address's network (IPv4 /16, IPv6 /48 by default); the raw text if not an IP."""
    if not address:
        return None
    try:
        ip = ip_address(address)
    except ValueError:
        return address
    bits = config.ipv4_prefix if ip.version == 4 else config.ipv6_prefix
    width = 32 if ip.version == 4 else 128
    masked = int(ip) >> (width - bits) << (width - bits)
    return f"{type(ip)(masked)}/{bits}"


def client_family(client: str | None) -> str | None:
    """The client program's name without its version: ``cursor/1.4.2`` -> ``cursor``."""
    if not client:
        return None
    family = client.split("/")[0].strip().lower()
    return family or None


# ── 90-day memory, kept per day so it stays bounded whatever the call rate ──────────────────
class DailyCounts:
    """How often each value was seen, per day, over the last ``days`` days."""

    def __init__(self, days: int) -> None:
        self.days = days
        self.by_day: OrderedDict[int, Counter] = OrderedDict()
        self.new_by_day: Counter = Counter()
        self.counts: Counter = Counter()
        self.new_uses = 0

    def expire(self, today: int) -> None:
        while self.by_day and next(iter(self.by_day)) <= today - self.days:
            day, counts = self.by_day.popitem(last=False)
            self.counts.subtract(counts)
            self.counts += Counter()  # drop zero and negative entries
            self.new_uses -= self.new_by_day.pop(day, 0)

    def add(self, today: int, value, count_as_new: bool) -> None:
        if count_as_new and value not in self.counts:
            self.new_by_day[today] += 1
            self.new_uses += 1
        self.by_day.setdefault(today, Counter())[value] += 1
        self.counts[value] += 1

    def active_days(self, weekend: bool | None = None) -> int:
        if weekend is None:
            return len(self.by_day)
        return sum(1 for day in self.by_day if is_weekend(day) == weekend)

    def per_day(self, values, tail: bool, weekend: bool | None = None) -> float:
        """How many times a day he does something this rare: (calls + 1) / (active days + 1).

        ``tail``: count his calls on every value at most this common; for a value he never
        used, how often he starts using something new. Otherwise: calls on ``values`` only.
        """
        n = sum(self.counts.get(v, 0) for v in values)
        if not tail:
            rare = n
        elif n == 0:
            rare = self.new_uses
        else:
            rare = sum(c for c in self.counts.values() if c <= n)
        return (rare + 1) / (self.active_days(weekend) + 1)

    def to_json(self) -> dict:
        return {
            "by_day": [[d, list(c.items())] for d, c in self.by_day.items()],
            "new_by_day": list(self.new_by_day.items()),
        }

    @classmethod
    def from_json(cls, days: int, data: dict) -> DailyCounts:
        out = cls(days)
        for day, items in data["by_day"]:
            counts = Counter({_key(k): v for k, v in items})
            out.by_day[day] = counts
            out.counts.update(counts)
        out.new_by_day = Counter({d: n for d, n in data["new_by_day"]})
        out.new_uses = sum(out.new_by_day.values())
        return out


class DailyMean:
    """His average of a value over the last ``days`` days, kept as per-day sums."""

    def __init__(self, days: int) -> None:
        self.days = days
        self.by_day: OrderedDict[int, list[float]] = OrderedDict()  # day -> [sum, count]
        self.total, self.n = 0.0, 0

    def mean_then_add(self, today: int, value: float) -> float | None:
        while self.by_day and next(iter(self.by_day)) <= today - self.days:
            _, (s, n) = self.by_day.popitem(last=False)
            self.total -= s
            self.n -= int(n)
        mean = self.total / self.n if self.n else None
        bucket = self.by_day.setdefault(today, [0.0, 0])
        bucket[0] += value
        bucket[1] += 1
        self.total += value
        self.n += 1
        return mean

    def to_json(self) -> list:
        return [[d, s, n] for d, (s, n) in self.by_day.items()]

    @classmethod
    def from_json(cls, days: int, data: list) -> DailyMean:
        out = cls(days)
        for day, s, n in data:
            out.by_day[day] = [s, n]
            out.total += s
            out.n += int(n)
        return out


@dataclass
class AgentState:
    """One agent's memory: what the dimensions compare him with."""

    calls_last_hour: DailyMean
    session_minutes: DailyMean
    tools: DailyCounts
    assets: DailyCounts
    hours: DailyCounts  # (weekend, hour of day)
    tool_calls: int = 0
    recent: deque = field(default_factory=deque)  # his tool-call times, last hour
    sizes: dict[str, DailyMean] = field(default_factory=dict)  # per tool
    networks: dict[str, int] = field(default_factory=dict)  # value -> last day seen
    clients: dict[str, int] = field(default_factory=dict)
    last_read: dict[str, int] = field(default_factory=dict)  # sensitive asset -> day read
    sessions_seen: int = 0
    sessions_initialized: int = 0

    @classmethod
    def new(cls, days: int) -> AgentState:
        return cls(
            DailyMean(days),
            DailyMean(days),
            DailyCounts(days),
            DailyCounts(days),
            DailyCounts(days),
        )


@dataclass
class SessionState:
    start: float
    initialized: bool = False
    counted: bool = False
    tools: set = field(default_factory=set)
    read_sensitive: set = field(default_factory=set)


class BehaviourEngine:
    """Scores messages one at a time, in arrival order, learning from each."""

    def __init__(self, config: BehaviourConfig | None = None) -> None:
        self.config = config or BehaviourConfig()
        self.agents: dict[str, AgentState] = {}
        self.sessions: OrderedDict[str, SessionState] = OrderedDict()

    # ── scoring ──────────────────────────────────────────────────────────────────────────
    def observe(self, message: Message) -> Verdict:
        """The behaviour verdict for one request message; then remember it."""
        cfg = self.config
        st = self._agent(message.agent)
        today = int(message.ts // DAY_S)
        session = self._session(message)
        if message.method == INIT_METHOD and session:
            session.initialized = True
        warm = st.tool_calls >= cfg.warmup_calls
        scores: dict[str, float] = {}
        self._origin(st, message, today, warm, scores)
        if message.method == CALL_METHOD:
            self._call(st, session, message, today, warm, scores)
        if not warm or not scores:
            return Verdict(1.0, None, None, scores if warm else {}, learning=not warm)
        strongest = max(scores, key=lambda d: scores[d])
        top = scores[strongest]
        return Verdict(multiplier(top), strongest, top, scores, learning=False)

    def _origin(
        self, st: AgentState, m: Message, today: int, warm: bool, scores: dict[str, float]
    ) -> None:
        """New network (/16) and new client program: rules, on every message."""
        for name, value, seen in (
            (NEW_NETWORK, network_of(m.address, self.config), st.networks),
            (NEW_CLIENT, client_family(m.client), st.clients),
        ):
            if value is None:
                continue
            last = seen.get(value)
            if warm and (last is None or last <= today - self.config.history_days):
                scores[name] = self.config.rule_score
            seen[value] = today
        for seen in (st.networks, st.clients):  # forget what has not been seen in 90 days
            if len(seen) > 64:
                for value in [v for v, d in seen.items() if d <= today - self.config.history_days]:
                    del seen[value]

    def _call(
        self,
        st: AgentState,
        session: SessionState | None,
        m: Message,
        today: int,
        warm: bool,
        scores: dict[str, float],
    ) -> None:
        cfg = self.config
        tool = m.tool or ""
        # counts and sizes: more than his usual
        recent = st.recent
        recent.append(m.ts)
        while recent and recent[0] <= m.ts - HOUR_S:
            recent.popleft()
        usual_hour = st.calls_last_hour.mean_then_add(today, len(recent))
        minutes = (m.ts - session.start) / MINUTE_S if session else 0.0
        usual_session = st.session_minutes.mean_then_add(today, minutes)
        usual_size = st.sizes.setdefault(tool, DailyMean(cfg.history_days)).mean_then_add(
            today, float(m.size)
        )
        for counts in (st.tools, st.assets, st.hours):
            counts.expire(today)
        weekend = is_weekend(today)
        hour = int((m.ts % DAY_S) // HOUR_S)
        around = [(weekend, (hour + k) % 24) for k in (-1, 0, 1)]
        normally_initializes = (
            st.sessions_seen >= cfg.normally_initializes_after
            and 2 * st.sessions_initialized >= st.sessions_seen
        )
        if warm:
            self._more(scores, CALLS_LAST_HOUR, len(recent), usual_hour, cfg.call_unit)
            if session:
                self._more(scores, SESSION_LENGTH, minutes, usual_session, cfg.minute_unit)
            self._more(scores, REQUEST_SIZE, m.size, usual_size, cfg.byte_unit)
            scores[TOOL] = cfg.tool_ceiling / (1 + cfg.tolerance * st.tools.per_day([tool], True))
            if m.asset:
                scores[ASSET] = 1 / (1 + cfg.tolerance * st.assets.per_day([m.asset], True))
            scores[TIME_OF_DAY] = 1 / (1 + cfg.tolerance * st.hours.per_day(around, False, weekend))
            if sum(1 for t in recent if t > m.ts - MINUTE_S) > cfg.burst_per_minute:
                scores[BURST] = cfg.rule_score
            if m.size > cfg.request_limit_bytes:
                scores[REQUEST_TOO_BIG] = cfg.rule_score
            if session and not session.initialized and normally_initializes:
                scores[PROTOCOL_SKIP] = cfg.protocol_skip_score
            if self._problematic_sequence(st, session, m, tool, today):
                scores[SEQUENCE] = cfg.rule_score
        # remember
        st.tools.add(today, tool, count_as_new=warm)
        st.hours.add(today, (weekend, hour), count_as_new=False)
        if m.asset:
            st.assets.add(today, m.asset, count_as_new=warm)
            sensitive = (m.sensitivity or 0) >= cfg.sensitive_level
            if m.operation == READ and sensitive:
                st.last_read[m.asset] = today
                if session:
                    session.read_sensitive.add(m.asset)
        if session:
            if not session.counted:
                session.counted = True
                st.sessions_seen += 1
                st.sessions_initialized += int(session.initialized)
            session.tools.add(tool)
        st.tool_calls += 1

    def _problematic_sequence(
        self, st: AgentState, session: SessionState | None, m: Message, tool: str, today: int
    ) -> bool:
        cfg = self.config
        needed = cfg.requires_before.get(tool)
        if needed and not (session and session.tools & needed):
            return True  # e.g. a merge with no review earlier in the session
        if m.operation != WRITE or not m.asset:
            return False
        if session and session.read_sensitive - {m.asset}:
            return True  # a write after reading a different sensitive asset
        sensitive = (m.sensitivity or 0) >= cfg.sensitive_level
        last = st.last_read.get(m.asset)
        return sensitive and (last is None or last < today - cfg.read_memory_days)

    def _more(
        self, scores: dict[str, float], name: str, value: float, usual: float | None, unit: float
    ) -> None:
        if usual is None:
            return  # no history for this yet: the dimension does not take part
        scores[name] = (value + unit) / (value + unit + self.config.tolerance * (usual + unit))

    def _agent(self, agent: str) -> AgentState:
        st = self.agents.get(agent)
        if st is None:
            st = self.agents[agent] = AgentState.new(self.config.history_days)
        return st

    def _session(self, m: Message) -> SessionState | None:
        if not m.session:
            return None
        key = f"{m.agent}\x1f{m.session}"
        session = self.sessions.get(key)
        if session is None:
            session = self.sessions[key] = SessionState(start=m.ts)
            if len(self.sessions) > self.config.max_sessions:
                self.sessions.popitem(last=False)
        else:
            self.sessions.move_to_end(key)
        return session

    # ── state that survives a restart ───────────────────────────────────────────────────
    def snapshot(self) -> dict:
        """Everything the engine has learned, as JSON-safe data (open sessions excluded)."""
        return {"agents": {a: _agent_json(st) for a, st in self.agents.items()}}

    def restore(self, data: dict) -> None:
        """Load :meth:`snapshot` output, so a restart continues where it stopped."""
        days = self.config.history_days
        for agent, d in data.get("agents", {}).items():
            st = AgentState(
                tool_calls=d["tool_calls"],
                recent=deque(d["recent"]),
                calls_last_hour=DailyMean.from_json(days, d["calls_last_hour"]),
                session_minutes=DailyMean.from_json(days, d["session_minutes"]),
                sizes={t: DailyMean.from_json(days, v) for t, v in d["sizes"].items()},
                tools=DailyCounts.from_json(days, d["tools"]),
                assets=DailyCounts.from_json(days, d["assets"]),
                hours=DailyCounts.from_json(days, d["hours"]),
                networks=dict(d["networks"]),
                clients=dict(d["clients"]),
                last_read=dict(d["last_read"]),
                sessions_seen=d["sessions_seen"],
                sessions_initialized=d["sessions_initialized"],
            )
            self.agents[agent] = st


def is_weekend(day: int) -> bool:
    """Day number since 1970-01-01 (a Thursday) -> Saturday or Sunday."""
    return (day + 3) % 7 >= 5


def _key(value):
    """JSON turns tuple keys into lists; time-of-day keys are (weekend, hour) tuples."""
    return tuple(value) if isinstance(value, list) else value


def _agent_json(st: AgentState) -> dict:
    return {
        "tool_calls": st.tool_calls,
        "recent": list(st.recent),
        "calls_last_hour": st.calls_last_hour.to_json(),
        "session_minutes": st.session_minutes.to_json(),
        "sizes": {t: m.to_json() for t, m in st.sizes.items()},
        "tools": st.tools.to_json(),
        "assets": st.assets.to_json(),
        "hours": st.hours.to_json(),
        "networks": st.networks,
        "clients": st.clients,
        "last_read": st.last_read,
        "sessions_seen": st.sessions_seen,
        "sessions_initialized": st.sessions_initialized,
    }
