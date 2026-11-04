"""The behaviour engine with switches: the documented v2 and each proposed fix, one at a time.

``Variant(Flags())`` reproduces the shipped engine (``src/mcp_security/behaviour/engine.py``)
call for call; ``normal_org_sim.py`` checks that before it trusts any variant. The switches:

- ``v2``: DIMENSION_FORMULAS.md v2. Request size is only the 10 KB rule (the "more than his
  usual" size dimension is gone), and a tool he has not used in 90 days is a rule (0.9).
- ``days``: tool, asset and time of day count *days* instead of calls, so 30 calls in one night
  count as one night, not as "30 times".
- ``daily``: his history updates once a day; a call is compared with his history up to
  yesterday, so the "+1" in ``(rare + 1) / (active days + 1)`` is exactly "today".
- ``tiebreak``: ``S = s1 + tiebreak * s2 * (1 - s1)``: the second-strongest score nudges S.
- ``rule_rarity``: a habit rule (burst, sequence, request size, protocol skip) is scaled by how
  often he broke it before: ``value / (1 + 2 * broken_days / (active_days + 1))``.
- ``org_discount``: something new for him that at least this many *other* agents also started in
  the last 7 days (an org-wide change) scores at most 0.5 (x1). Other agents only ever lower a
  score here, never raise it.
- ``novelty_warmup_days``: first uses in his first N days are not counted as "starting
  something new" (today only his first 5 calls are excluded).
- ``rarity_rules``: which rules ``rule_rarity`` scales (default: all four habit rules).
- ``extra_dims``: three more "more than his usual" counts: distinct assets in the last hour,
  writes in the last hour, and the same call (tool and asset) in the last 10 minutes.
- ``sensitive_this_only``: for an asset at or above the sensitive level, the asset score is also
  computed on "this thing only" and the higher score is kept, so an agent who often starts new
  things still flares on a first look at a sensitive asset.
- ``sensitive_first_look``: the same, but only for a sensitive asset he has not touched in 90
  days (a first look), so occasional visits to a known sensitive asset stay ordinary.
- ``tod_fallback``: when he has fewer than this many active days of today's kind (weekday or
  weekend), time of day compares with all his days, not only that kind.
- ``per_tool_size``: the request-size rule uses a limit per tool (``size_limits``), not one limit.

v3 candidate switches (one dimension each, instead of ``extra_dims``):

- ``same_call_10m``, ``writes_per_hour``: Typical Cadence counts, "more than his usual".
- ``assets_per_hour``: distinct assets in the last hour, either ``"count"`` (Typical Cadence,
  more than his usual), ``"rule"`` (Policy: over an org-wide learned limit, ``breadth_limit``)
  or ``"both"`` (the count, with the rule as a backstop).
- ``sensitive_rule``: Policy rule, a first look at a sensitive asset (at or above the sensitive
  level, not touched in 90 days) -> 0.9.
- ``sensitive_steps``: (asset step, tool step) grades that rule by the asset's sensitivity and
  the tool's static level: ``0.9 - asset step * (5 - sensitivity) - tool step * (anchor -
  level)``, so 0.9 is a tool at the ``sensitive_anchor`` level (4, a write, by default) on a
  sensitivity-5 asset. (0, 0) keeps it flat at 0.9.
- ``weekend``: how time of day treats weekends:
  ``"split"`` (today: weekends compared only with his weekend days);
  ``"fallback"`` (fewer than 4 weekend days -> compare with all his days);
  ``"blend"`` (different counts: his weekend profile, shrunk toward his all-days profile with 4
  pseudo-days, ``e = (n_weekend + 4 e_all) / (weekend days + 4)``, so there is no cliff);
  ``"flag"`` (time of day ignores the weekday/weekend split; a separate Policy flag, 0.7, fires
  on a weekend for someone who worked fewer than a quarter of his weekends).
- ``sensitive_org_discount``: the org discount also caps the first-look rule. Off: several agents
  first touching the same sensitive asset in one week is not taken as an org-wide change.
- ``first_day_warmup``: with ``daily``, nothing is in his history until his first day ends, so
  every tool would be "new" all that day; the warm-up lasts his whole first day instead.
- ``warmup_rules``: during warm-up, the rules that need none of his past still fire: burst,
  request size, many assets, a first look at a sensitive asset, risky order.

v4 switches (every "new for him" check in Typical Footprint, none as a rule):

- ``origin_rarity``: network (/16) and client app are Typical Footprint dimensions, "rarer
  than his usual" like tool and asset (ceiling ``origin_ceiling``), instead of the new-network
  and new-app rules.
- ``tool_rarity_first_use``: no new-tool rule; a tool he has not used in 90 days is scored by
  tool rarity (how often he starts new tools), with the org discount.
- ``sensitive_floor``: the first look at a sensitive asset is a floor on the asset's score
  instead of a rule of its own (same value, so the same M; it changes only the name of the
  strongest dimension and the second-strongest score).
"""

from __future__ import annotations

import bisect
from collections import Counter, OrderedDict, deque
from dataclasses import dataclass, field

from mcp_security.behaviour.engine import (
    ASSET,
    BURST,
    CALL_METHOD,
    CALLS_LAST_HOUR,
    CLIENT,
    DAY_S,
    HOUR_S,
    INIT_METHOD,
    MINUTE_S,
    NETWORK,
    NEW_CLIENT,
    NEW_NETWORK,
    PROTOCOL_SKIP,
    READ,
    REQUEST_SIZE,
    REQUEST_TOO_BIG,
    SEQUENCE,
    SESSION_LENGTH,
    TIME_OF_DAY,
    TOOL,
    WRITE,
    BehaviourConfig,
    Message,
    client_family,
    is_weekend,
    multiplier,
    network_of,
)

NEW_TOOL = "new_tool"
ASSETS_LAST_HOUR = "assets_last_hour"
WRITES_LAST_HOUR = "writes_last_hour"
SAME_CALL_10M = "same_call_10m"
TEN_MINUTES_S = 600.0
MANY_ASSETS = "many_assets"
SENSITIVE_FIRST_LOOK = "sensitive_first_look"
WEEKEND_WORK = "weekend_work"
WEEKEND_PRIOR_DAYS = 4  # "blend": pseudo-days of his all-days profile
WEEKEND_FALLBACK_DAYS = 4  # "fallback": below this many weekend days, use all days
WEEKEND_RARE_SHARE = 0.25  # "flag": he worked fewer than this share of his weekends
WEEKEND_MIN_SEEN = 4  # "flag": weekend days he must have had before the flag can fire
WEEKEND_FLAG_SCORE = 0.7  # x1.9, a weak signal like a skipped "hello"
TOP_SENSITIVITY = 5  # the graded first-look rule is at its full value on these assets
WRITE_LEVEL = 4  # ... with a tool at the anchor level, by default a write (4)
HABIT_RULES = frozenset({BURST, SEQUENCE, REQUEST_TOO_BIG, PROTOCOL_SKIP})
ORG_WINDOW_S = 7 * DAY_S
EDGE = 0.5


@dataclass(frozen=True)
class Flags:
    v2: bool = False
    days: bool = False
    daily: bool = False
    tiebreak: float = 0.0
    rule_rarity: bool = False
    org_discount: int = 0
    novelty_warmup_days: int = 0
    rarity_rules: frozenset = HABIT_RULES
    extra_dims: bool = False
    sensitive_this_only: bool = False
    sensitive_first_look: bool = False
    tod_fallback: int = 0
    per_tool_size: bool = False
    same_call_10m: bool = False
    writes_per_hour: bool = False
    assets_per_hour: str = ""
    sensitive_rule: bool = False
    sensitive_steps: tuple[float, float] = (0.0, 0.0)
    sensitive_anchor: int = WRITE_LEVEL  # 3 anchors the full value at a read
    sensitive_org_discount: bool = True
    weekend: str = "split"
    first_day_warmup: bool = False
    warmup_rules: bool = False
    origin_rarity: bool = False
    tool_rarity_first_use: bool = False
    sensitive_floor: bool = False


class Memory:
    """90 days of values per day. Scoring sees calls (or days) per value, either including
    today (learning after every call) or only up to yesterday (learning once a day)."""

    def __init__(self, window: int, count_days: bool, daily: bool) -> None:
        self.window, self.count_days, self.daily = window, count_days, daily
        self.by_day: OrderedDict[int, Counter] = OrderedDict()
        self.weight: Counter = Counter()
        self.new_by_day: Counter = Counter()
        self.new_total = 0
        self.folded_through = -(10**9)
        self._past_any: dict = {}

    def _fold(self, counts: Counter, sign: int) -> None:
        w = self.weight
        for value, c in counts.items():
            w[value] += sign * (1 if self.count_days else c)
            if w[value] <= 0:
                del w[value]

    def expire(self, today: int) -> None:
        if self.daily and self.by_day:
            last = next(reversed(self.by_day))
            if self.folded_through < last < today:
                self._fold(self.by_day[last], +1)
                self.folded_through = last
        while self.by_day and next(iter(self.by_day)) <= today - self.window:
            day, counts = self.by_day.popitem(last=False)
            if not self.daily or day <= self.folded_through:
                self._fold(counts, -1)
            self.new_total -= self.new_by_day.pop(day, 0)

    def known(self, value) -> bool:
        return value in self.weight

    def add(self, today: int, value, count_as_new: bool) -> None:
        todays = self.by_day.get(today)
        if todays is None:
            todays = self.by_day[today] = Counter()
        if count_as_new and value not in self.weight and value not in todays:
            self.new_by_day[today] += 1
            self.new_total += 1
        first_today = value not in todays
        todays[value] += 1
        if not self.daily and (first_today or not self.count_days):
            self.weight[value] += 1

    def active_days(self, today: int, weekend: bool | None = None) -> int:
        if weekend is None and not self.daily:
            return len(self.by_day)
        return sum(
            1
            for d in self.by_day
            if not (self.daily and d == today) and (weekend is None or is_weekend(d) == weekend)
        )

    def _days_with_any(self, values: tuple, today: int) -> int:
        key = (today, values)
        past = self._past_any.get(key)
        if past is None:
            if len(self._past_any) > 256:
                self._past_any.clear()
            past = sum(
                1 for d, c in self.by_day.items() if d < today and any(v in c for v in values)
            )
            self._past_any[key] = past
        todays = self.by_day.get(today)
        now = int(not self.daily and todays is not None and any(v in todays for v in values))
        return past + now

    def count(self, values: tuple, today: int) -> int:
        """His calls (or days) on ``values``, as scoring sees them."""
        if self.count_days:
            return self._days_with_any(values, today)
        return sum(self.weight.get(v, 0) for v in values)

    def per_day(self, values: tuple, tail: bool, weekend: bool | None, today: int) -> float:
        if self.count_days and not tail:
            n = self._days_with_any(values, today)
        else:
            n = sum(self.weight.get(v, 0) for v in values)
        if not tail:
            rare = n
        elif n == 0:
            rare = self.new_total - (self.new_by_day.get(today, 0) if self.daily else 0)
        else:
            rare = sum(c for c in self.weight.values() if c <= n)
        return (rare + 1) / (self.active_days(today, weekend) + 1)


class MeanMemory:
    """His average of a value over 90 days, optionally excluding today."""

    def __init__(self, window: int, daily: bool) -> None:
        self.window, self.daily = window, daily
        self.by_day: OrderedDict[int, list] = OrderedDict()
        self.total, self.n = 0.0, 0

    def mean_then_add(self, today: int, value: float) -> float | None:
        while self.by_day and next(iter(self.by_day)) <= today - self.window:
            _, (s, n) = self.by_day.popitem(last=False)
            self.total -= s
            self.n -= n
        total, n = self.total, self.n
        if self.daily and today in self.by_day:
            total -= self.by_day[today][0]
            n -= self.by_day[today][1]
        mean = total / n if n else None
        bucket = self.by_day.setdefault(today, [0.0, 0])
        bucket[0] += value
        bucket[1] += 1
        self.total += value
        self.n += 1
        return mean


@dataclass
class AgentMemory:
    hour_mean: MeanMemory
    session_mean: MeanMemory
    tools: Memory
    assets: Memory
    hours: Memory
    sizes: dict = field(default_factory=dict)
    tool_calls: int = 0
    recent: deque = field(default_factory=deque)
    networks: dict = field(default_factory=dict)
    clients: dict = field(default_factory=dict)
    fresh: dict = field(default_factory=dict)
    last_read: dict = field(default_factory=dict)
    sessions_seen: int = 0
    sessions_initialized: int = 0
    first_day: int | None = None
    rule_days: dict = field(default_factory=dict)
    hour_assets: deque = field(default_factory=deque)  # (ts, asset), last hour
    hour_asset_counts: Counter = field(default_factory=Counter)
    hour_writes: deque = field(default_factory=deque)
    ten_calls: deque = field(default_factory=deque)  # (ts, (tool, asset)), last 10 minutes
    ten_counts: Counter = field(default_factory=Counter)
    extra_means: dict = field(default_factory=dict)
    network_counts: Memory | None = None  # ``origin_rarity``
    client_counts: Memory | None = None


@dataclass
class Session:
    start: float
    initialized: bool = False
    counted: bool = False
    tools: set = field(default_factory=set)
    read_sensitive: set = field(default_factory=set)


class Variant:
    """The shipped engine's scoring with :class:`Flags`; returns (M, strongest, scores)."""

    def __init__(
        self,
        flags: Flags,
        config: BehaviourConfig,
        first_uses: dict | None = None,
        size_limits: dict | None = None,
        breadth_limit: int | None = None,
        tool_levels: dict | None = None,
    ) -> None:
        self.flags, self.config = flags, config
        self.first_uses = first_uses or {}
        self.size_limits = size_limits or {}
        self.breadth_limit = breadth_limit
        self.tool_levels = tool_levels or {}
        self.agents: dict[str, AgentMemory] = {}
        self.sessions: OrderedDict[str, Session] = OrderedDict()

    # ── one message ────────────────────────────────────────────────────────────────────
    def observe(self, m: Message) -> tuple[float, str | None, dict]:
        cfg, fl = self.config, self.flags
        st = self._agent(m.agent)
        today = int(m.ts // DAY_S)
        if st.first_day is None:
            st.first_day = today
        session = self._session(m)
        if m.method == INIT_METHOD and session:
            session.initialized = True
        warm = st.tool_calls >= cfg.warmup_calls
        if fl.first_day_warmup:  # learning once a day: no history until his first day ends
            warm = warm and today > st.first_day
        scores: dict[str, float] = {}
        self._origin(st, m, today, warm, scores)
        if m.method == CALL_METHOD:
            self._call(st, session, m, today, warm, scores)
        if not scores:  # in warm-up, scores holds only rules that fired (``warmup_rules``)
            return 1.0, None, {}
        strongest = max(scores, key=lambda d: scores[d])
        top = scores[strongest]
        if fl.tiebreak and len(scores) > 1:
            second = sorted(scores.values(), reverse=True)[1]
            top = top + fl.tiebreak * second * (1 - top)
        return multiplier(top), strongest, scores

    def _origin(self, st, m: Message, today: int, warm: bool, scores: dict) -> None:
        cfg, fl = self.config, self.flags
        if fl.origin_rarity:
            self._origin_rarity(st, m, today, warm, scores)
            return
        for name, kind, value, seen in (
            (NEW_NETWORK, "network", network_of(m.address, cfg), st.networks),
            (NEW_CLIENT, "client", client_family(m.client), st.clients),
        ):
            if value is None:
                continue
            last = seen.get(value)
            new = last is None or last <= today - cfg.history_days
            if new and warm:
                st.fresh[(kind, value)] = today
            elif fl.daily and st.fresh.get((kind, value)) == today:
                new = True
            if warm and new:
                score = cfg.rule_score
                if self._org_started(kind, value, m.ts, m.agent):
                    score = min(score, EDGE)
                scores[name] = score
            seen[value] = today

    def _origin_rarity(self, st, m: Message, today: int, warm: bool, scores: dict) -> None:
        """``origin_rarity``: network and client app, rarer than his usual, every message."""
        cfg, fl = self.config, self.flags
        count_new = warm and (
            not fl.novelty_warmup_days or today - st.first_day >= fl.novelty_warmup_days
        )
        for name, kind, value, mem in (
            (NETWORK, "network", network_of(m.address, cfg), st.network_counts),
            (CLIENT, "client", client_family(m.client), st.client_counts),
        ):
            if value is None:
                continue
            mem.expire(today)
            if warm and mem.active_days(today):
                e = mem.per_day((value,), True, None, today)
                score = cfg.origin_ceiling / (1 + cfg.tolerance * e)
                if not mem.known(value) and self._org_started(kind, value, m.ts, m.agent):
                    score = min(score, EDGE)
                scores[name] = score
            mem.add(today, value, count_new)

    def _call(self, st, session, m: Message, today: int, warm: bool, scores: dict) -> None:
        cfg, fl = self.config, self.flags
        tool = m.tool or ""
        recent = st.recent
        recent.append(m.ts)
        while recent and recent[0] <= m.ts - HOUR_S:
            recent.popleft()
        usual_hour = st.hour_mean.mean_then_add(today, len(recent))
        minutes = (m.ts - session.start) / MINUTE_S if session else 0.0
        usual_session = st.session_mean.mean_then_add(today, minutes)
        sizes = st.sizes.get(tool)
        if sizes is None:
            sizes = st.sizes[tool] = MeanMemory(cfg.history_days, fl.daily)
        usual_size = sizes.mean_then_add(today, float(m.size))
        for mem in (st.tools, st.assets, st.hours):
            mem.expire(today)
        weekend = is_weekend(today)
        hour = int((m.ts % DAY_S) // HOUR_S)
        around = ((weekend, (hour - 1) % 24), (weekend, hour), (weekend, (hour + 1) % 24))
        normally_initializes = (
            st.sessions_seen >= cfg.normally_initializes_after
            and 2 * st.sessions_initialized >= st.sessions_seen
        )
        wanted = tuple(
            name
            for name, on in (
                (ASSETS_LAST_HOUR, fl.extra_dims or fl.assets_per_hour in ("count", "both")),
                (WRITES_LAST_HOUR, fl.extra_dims or fl.writes_per_hour),
                (SAME_CALL_10M, fl.extra_dims or fl.same_call_10m),
            )
            if on
        )
        extra, breadth = {}, 0
        if wanted or fl.assets_per_hour in ("rule", "both"):
            extra, breadth = self._extra_counts(st, m, tool, today, wanted)
        fired: list[tuple[str, float]] = []
        if warm:
            for name, (value, usual) in extra.items():
                self._more(scores, name, value, usual, cfg.call_unit)
            self._more(scores, CALLS_LAST_HOUR, len(recent), usual_hour, cfg.call_unit)
            if session:
                self._more(scores, SESSION_LENGTH, minutes, usual_session, cfg.minute_unit)
            if not fl.v2:
                self._more(scores, REQUEST_SIZE, m.size, usual_size, cfg.byte_unit)
            if fl.v2 and not fl.tool_rarity_first_use and not st.tools.known(tool):
                score = cfg.rule_score
                if self._org_started("tool", tool, m.ts, m.agent):
                    score = min(score, EDGE)
                scores[NEW_TOOL] = score
            else:
                e = st.tools.per_day((tool,), True, None, today)
                score = cfg.tool_ceiling / (1 + cfg.tolerance * e)
                if not st.tools.known(tool) and self._org_started("tool", tool, m.ts, m.agent):
                    score = min(score, EDGE)
                scores[TOOL] = score
            if m.asset:
                e = st.assets.per_day((m.asset,), True, None, today)
                score = 1 / (1 + cfg.tolerance * e)
                if (
                    fl.sensitive_this_only
                    and (m.sensitivity or 0) >= cfg.sensitive_level
                    and not (fl.sensitive_first_look and st.assets.known(m.asset))
                ):
                    e_this = st.assets.per_day((m.asset,), False, None, today)
                    score = max(score, 1 / (1 + cfg.tolerance * e_this))
                if not st.assets.known(m.asset) and self._org_started(
                    "asset", m.asset, m.ts, m.agent
                ):
                    score = min(score, EDGE)
                scores[ASSET] = score
            e = self._time_of_day(st, around, weekend, today)
            scores[TIME_OF_DAY] = 1 / (1 + cfg.tolerance * e)
            if fl.weekend == "flag" and weekend and self._rarely_works_weekends(st, today):
                fired.append((WEEKEND_WORK, WEEKEND_FLAG_SCORE))
        if warm or fl.warmup_rules:  # in warm-up, only the rules that need none of his past
            if (
                fl.sensitive_rule
                and m.asset
                and (m.sensitivity or 0) >= cfg.sensitive_level
                and not st.assets.known(m.asset)
            ):
                score = self._sensitive_value(m.sensitivity or 0, tool)
                if fl.sensitive_org_discount and self._org_started("asset", m.asset, m.ts, m.agent):
                    score = min(score, EDGE)
                if fl.sensitive_floor:  # Typical Footprint: a floor on the asset's score
                    scores[ASSET] = max(scores.get(ASSET, 0.0), score)
                else:
                    fired.append((SENSITIVE_FIRST_LOOK, score))
            if (
                fl.assets_per_hour in ("rule", "both")
                and self.breadth_limit is not None
                and breadth > self.breadth_limit
            ):
                fired.append((MANY_ASSETS, cfg.rule_score))
            if sum(1 for t in recent if t > m.ts - MINUTE_S) > cfg.burst_per_minute:
                fired.append((BURST, cfg.rule_score))
            limit = cfg.request_limit_bytes
            if fl.per_tool_size:
                limit = self.size_limits.get(tool, limit)
            if m.size > limit:
                fired.append((REQUEST_TOO_BIG, cfg.rule_score))
            if warm and session and not session.initialized and normally_initializes:
                fired.append((PROTOCOL_SKIP, cfg.protocol_skip_score))
            if self._problematic_sequence(st, session, m, tool, today):
                fired.append((SEQUENCE, cfg.rule_score))
            for rule, value in fired:
                scores[rule] = self._rule_value(st, rule, value, today)
        count_new = warm and (
            not fl.novelty_warmup_days or today - st.first_day >= fl.novelty_warmup_days
        )
        st.tools.add(today, tool, count_new)
        st.hours.add(today, (weekend, hour), False)
        if m.asset:
            st.assets.add(today, m.asset, count_new)
            if m.operation == READ and (m.sensitivity or 0) >= cfg.sensitive_level:
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
        for rule, _ in fired:
            days = st.rule_days.setdefault(rule, deque())
            if not days or days[-1] != today:
                days.append(today)

    def _rule_value(self, st, rule: str, value: float, today: int) -> float:
        if not (self.flags.rule_rarity and rule in self.flags.rarity_rules):
            return value
        days = st.rule_days.get(rule)
        if not days:
            return value
        while days and days[0] <= today - self.config.history_days:
            days.popleft()
        broken = len(days) - int(self.flags.daily and bool(days) and days[-1] == today)
        e = broken / (st.tools.active_days(today) + 1)
        return value / (1 + self.config.tolerance * e)

    def _sensitive_value(self, sensitivity: int, tool: str) -> float:
        """The first-look rule's value: full for a tool at the anchor level on the most sensitive
        assets, lower for a less sensitive asset or a milder tool, higher (up to 1) for a
        stronger one; a tool with no level counts as the anchor."""
        asset_step, tool_step = self.flags.sensitive_steps
        anchor = self.flags.sensitive_anchor
        level = self.tool_levels.get(tool, anchor)
        value = (
            self.config.rule_score
            - asset_step * (TOP_SENSITIVITY - sensitivity)
            - tool_step * (anchor - level)
        )
        return min(1.0, value)

    def _time_of_day(self, st, around: tuple, weekend: bool, today: int) -> float:
        """``e`` for time of day under the weekend mode."""
        fl, hours = self.flags, st.hours
        pooled = around + tuple((not weekend, h) for _, h in around)
        kind_days = hours.active_days(today, weekend)
        if fl.weekend == "flag":
            return hours.per_day(pooled, False, None, today)
        if fl.weekend == "blend":
            e_all = hours.per_day(pooled, False, None, today)
            return (hours.count(around, today) + WEEKEND_PRIOR_DAYS * e_all) / (
                kind_days + WEEKEND_PRIOR_DAYS
            )
        fallback = fl.tod_fallback or (WEEKEND_FALLBACK_DAYS if fl.weekend == "fallback" else 0)
        if fallback and kind_days < fallback:
            return hours.per_day(pooled, False, None, today)
        return hours.per_day(around, False, weekend, today)

    def _rarely_works_weekends(self, st, today: int) -> bool:
        start = max(st.first_day, today - self.config.history_days + 1)
        seen = sum(1 for d in range(start, today) if is_weekend(d))
        worked = st.hours.active_days(today, True) - int(
            not self.flags.daily and today in st.hours.by_day
        )
        return seen >= WEEKEND_MIN_SEEN and worked < WEEKEND_RARE_SHARE * seen

    def _extra_counts(self, st, m: Message, tool: str, today: int, wanted: tuple) -> tuple:
        """Distinct assets and writes in the last hour, the same call in the last 10 minutes:
        ({dimension: (value now, his usual)} for the ``wanted`` ones, distinct assets now)."""
        ha, hc = st.hour_assets, st.hour_asset_counts
        if m.asset:
            ha.append((m.ts, m.asset))
            hc[m.asset] += 1
        while ha and ha[0][0] <= m.ts - HOUR_S:
            _, old = ha.popleft()
            hc[old] -= 1
            if not hc[old]:
                del hc[old]
        hw = st.hour_writes
        if m.operation == WRITE:
            hw.append(m.ts)
        while hw and hw[0] <= m.ts - HOUR_S:
            hw.popleft()
        key = (tool, m.asset)
        tc, tk = st.ten_calls, st.ten_counts
        tc.append((m.ts, key))
        tk[key] += 1
        while tc and tc[0][0] <= m.ts - TEN_MINUTES_S:
            _, old = tc.popleft()
            tk[old] -= 1
            if not tk[old]:
                del tk[old]
        out = {}
        values = {ASSETS_LAST_HOUR: len(hc), WRITES_LAST_HOUR: len(hw), SAME_CALL_10M: tk[key]}
        for name in wanted:
            value = values[name]
            means = st.extra_means.get(name)
            if means is None:
                means = st.extra_means[name] = MeanMemory(
                    self.config.history_days, self.flags.daily
                )
            out[name] = (value, means.mean_then_add(today, value))
        return out, len(hc)

    def _org_started(self, kind: str, value, ts: float, agent: str) -> bool:
        need = self.flags.org_discount
        if not need:
            return False
        starts = self.first_uses.get((kind, value))
        if not starts:
            return False
        times, agents = starts
        lo, hi = bisect.bisect_left(times, ts - ORG_WINDOW_S), bisect.bisect_left(times, ts)
        return sum(1 for a in agents[lo:hi] if a != agent) >= need

    def _problematic_sequence(self, st, session, m: Message, tool: str, today: int) -> bool:
        cfg = self.config
        needed = cfg.requires_before.get(tool)
        if needed and not (session and session.tools & needed):
            return True
        if m.operation != WRITE or not m.asset:
            return False
        if session and session.read_sensitive - {m.asset}:
            return True
        sensitive = (m.sensitivity or 0) >= cfg.sensitive_level
        last = st.last_read.get(m.asset)
        return sensitive and (last is None or last < today - cfg.read_memory_days)

    def _more(self, scores: dict, name: str, value: float, usual, unit: float) -> None:
        if usual is None:
            return
        scores[name] = (value + unit) / (value + unit + self.config.tolerance * (usual + unit))

    def _agent(self, agent: str) -> AgentMemory:
        st = self.agents.get(agent)
        if st is None:
            w, fl = self.config.history_days, self.flags
            st = self.agents[agent] = AgentMemory(
                MeanMemory(w, fl.daily),
                MeanMemory(w, fl.daily),
                Memory(w, fl.days, fl.daily),
                Memory(w, fl.days, fl.daily),
                Memory(w, fl.days, fl.daily),
                network_counts=Memory(w, fl.days, fl.daily),
                client_counts=Memory(w, fl.days, fl.daily),
            )
        return st

    def _session(self, m: Message) -> Session | None:
        if not m.session:
            return None
        key = f"{m.agent}\x1f{m.session}"
        session = self.sessions.get(key)
        if session is None:
            session = self.sessions[key] = Session(start=m.ts)
            if len(self.sessions) > self.config.max_sessions:
                self.sessions.popitem(last=False)
        else:
            self.sessions.move_to_end(key)
        return session
