"""The behaviour layer's bounded memory: 90 days kept per day, and short sliding windows.

- :class:`DailyCounts`: how often each value (tool, asset, hour of day) was seen, per day.
  With ``daily=True`` (design v3) the counts a call is compared with stop at yesterday: today's
  calls are kept apart and folded in when the next day starts.
- :class:`DailyMean`: an agent's average of a number (calls in the last hour, ...), per day.
- :class:`SlidingCounts`: how often each value was seen in the last N seconds.
- :class:`FirstUses`: who started using what in the last N days, across all agents (v3's org
  discount: something new for many agents at once is an org-wide change).

Design v5 adds new classes and leaves the ones above exactly as v1-v4 use them (the only
addition there is the read-only :meth:`DailyMean.mean`). Spec references are to
``knowledge_base/v5-design-spec.md`` (revision 2):

- :class:`MinimumHistory` (B5): which past days a caller's history holds. His last 90 days,
  stretched back up to 365 days until they hold 20 active days; the window's start never moves
  back. Also :func:`is_established` (RF7, RF11, the floor budget).
- :class:`ValueDays` (CAL-1 values, DEP-7): on how many past days of his window he used each
  value, kept as count-of-counts, with at most ``max_values`` values per kind. The least
  recently used values fold into an overflow that is priced as new.
- :class:`SlotQuantile` (B7): the robust usual, the 0.75 quantile of a count over his active
  clock-hour (or 10-minute) slots. It feeds only an amount's strength.
- :class:`WindowMean` (B5): :class:`DailyMean` over the B5 window.
- :class:`SlidingTotal` (AI-8): a bounded sum over the last N seconds (Read volume: reply bytes
  in the last hour).
- :class:`OrgFirstSeen` (RF7, Footprint strength): per value, when the route's current run of
  use began (new to the organisation) and how many of the route's callers used it.
- :class:`ColleagueFirstUses` (RF7): first uses by established callers in the last 7 days,
  each caller counted once; and :func:`org_discount_applies`, the discount's condition.

A *caller* is the key the engine keeps a history under. On v5 that is the agent (spec 2.1,
decision D5): the signed-in agent, or the reported client family and address. It is a person
only on a route that opts in with ``baseline_key = "user"``.

Every v5 day store follows one protocol. ``roll(today, start)`` folds the open day into the
past and drops past days before ``start`` (the caller's :meth:`MinimumHistory.roll`); reads
see only the past days ``[start, today - 1]``; adds go to the open day. Rolling depends only
on the clock: rolling at one day and again at a later one leaves the state that rolling once
at the later day leaves. Day numbers never go back for one store; a day earlier than the open
day is counted on the open day.

Reads never change what a later read returns (a memo aside), and rolling depends only on the
clock, so the score path can read the live state: it needs no copy of it. Copying is costly:
a :class:`ValueDays` at its cap holds ``max_values`` entries per day, and pickling one would
blow DEP-7's 5 ms scoring budget.
"""

from __future__ import annotations

import math
import operator
from bisect import bisect_left
from collections import Counter, OrderedDict, deque
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field

from mcp_security.behaviour import clock

# ── v5 defaults: the spec's values. The engine passes its config's values (engine.py's
# DESIGN_VALUES holds the same numbers); these defaults let each class stand alone. ──────────
WINDOW_DAYS = 90  # v4's history: the last 90 days, today included (A_d <= 89 past days)
ESTABLISHED_DAYS = 20  # B5: active days the window must hold; RF7's established
ONBOARDING_DAYS = 14  # established also needs this many days since his first call
MAX_HISTORY_DAYS = 365  # B5: the window never reaches further back than this
USUAL_QUANTILE = 0.75  # B7: three in four of his active slots stay at or below the usual
MIN_QUANTILE_SLOTS = 4  # B7: with fewer active slots the usual is their maximum
HOUR_SLOT_S = clock.HOUR_S  # B7: Call rate, Write rate and Breadth use clock hours
REPETITION_SLOT_S = 600.0  # B7: Repetition uses 10-minute slots
QUANTILE_TOLERANCE = 1e-9  # q * n within this of an integer counts as that integer
MAX_VALUES_PER_KIND = 4_096  # DEP-7: one caller's distinct values per kind
#: Route-wide values kept per kind: 32 callers' worth of DEP-7's cap, so a 10^5-asset register
#: (AI-13's scale row) fits whole and only a flood ever evicts.
ORG_MAX_VALUES_PER_KIND = 32 * MAX_VALUES_PER_KIND
ORG_CALLERS_PRUNE_AT = 64  # a value's callers are pruned of stale ones past this many
ORG_NEW_DAYS = 30  # RF7: new to the organisation if its run of use began this recently
ORG_DISCOUNT_AGENTS = 3  # RF7: established colleagues who must have started it
ORG_DISCOUNT_MAX_STATIC = 3  # RF7: a tool above this static level is never discounted
FIRST_USE_SECONDS = 7 * clock.DAY_S  # RF7: colleagues' first uses count for 7 days
MAX_FIRST_USE_KEYS = ORG_MAX_VALUES_PER_KIND  # ColleagueFirstUses: keys kept before dropping
SLIDING_TOTAL_RESOLUTION_S = 1.0  # SlidingTotal: one entry per second at most
TOOL_KIND = "tool"  # the org discount's kind names, as the engine keys first uses
#: engine.READ and engine.WRITE (memory cannot import the engine: it imports us)
READ_OPERATION, WRITE_OPERATION = "read", "write"
#: AI-7's tool key is ``tool`` or ``tool:operation`` (binding.touched_asset.KEY_SEPARATOR);
#: a server's tool listing carries the bare tool names.
TOOL_KEY_SEPARATOR = ":"


def is_weekend(day: int) -> bool:
    """Day number since 1970-01-01 (a Thursday) -> Saturday or Sunday, as v1-v4 count it (UTC
    days). The calendar lives in :mod:`mcp_security.behaviour.clock`; v5's local days with
    their own weekend days use :func:`mcp_security.behaviour.clock.is_weekend` directly."""
    return clock.is_weekend(day)


def as_key(value):
    """A JSON list back to the tuple it was saved from: time-of-day keys are (weekend, hour),
    same-call keys (tool, asset)."""
    return tuple(value) if isinstance(value, list) else value


class DailyCounts:
    """How often each value was seen, per day, over the last ``days`` days.

    ``daily``: scoring sees the counts up to yesterday (``counts``), and today's calls are folded
    in when the next day starts; otherwise ``counts`` includes every call so far.
    """

    def __init__(self, days: int, daily: bool = False) -> None:
        self.days, self.daily = days, daily
        self.by_day: OrderedDict[int, Counter] = OrderedDict()
        self.new_by_day: Counter = Counter()
        self.counts: Counter = Counter()
        self.new_uses = 0
        self.folded_through: int | None = None  # daily: the last day in ``counts``

    def expire(self, today: int) -> None:
        if self.daily and self.by_day:
            last = next(reversed(self.by_day))
            if last < today and (self.folded_through is None or last > self.folded_through):
                self.counts.update(self.by_day[last])
                self.folded_through = last
        while self.by_day and next(iter(self.by_day)) <= today - self.days:
            day, counts = self.by_day.popitem(last=False)
            if not self.daily or (self.folded_through is not None and day <= self.folded_through):
                self.counts.subtract(counts)
                self.counts += Counter()  # drop zero and negative entries
            self.new_uses -= self.new_by_day.pop(day, 0)

    def known(self, value) -> bool:
        """Seen in the counts scoring uses (daily: up to yesterday)."""
        return value in self.counts

    def is_new(self, value, today: int) -> bool:
        """Not seen in the last ``days`` days, today included."""
        return value not in self.counts and value not in self.by_day.get(today, ())

    def add(self, today: int, value, count_as_new: bool) -> None:
        todays = self.by_day.get(today)
        if todays is None:
            todays = self.by_day[today] = Counter()
        if count_as_new and value not in self.counts and value not in todays:
            self.new_by_day[today] += 1
            self.new_uses += 1
        todays[value] += 1
        if not self.daily:
            self.counts[value] += 1

    def count(self, values) -> int:
        """His calls on ``values``, as scoring sees them."""
        return sum(self.counts.get(v, 0) for v in values)

    def active_days(self, weekend: bool | None = None, today: int | None = None) -> int:
        """Days with a call (daily: not counting today), optionally only weekend or weekdays."""
        if weekend is None:
            return len(self.by_day) - int(self.daily and today in self.by_day)
        return sum(
            1
            for day in self.by_day
            if is_weekend(day) == weekend and not (self.daily and day == today)
        )

    def per_day(self, values, tail: bool, weekend: bool | None = None, today: int | None = None):
        """How many times a day he does something this rare: (calls + 1) / (active days + 1).

        ``tail``: count his calls on every value at most this common; for a value he never
        used, how often he starts using something new. Otherwise: calls on ``values`` only.
        """
        n = self.count(values)
        if not tail:
            rare = n
        elif n == 0:
            rare = self.new_uses - (self.new_by_day.get(today, 0) if self.daily else 0)
        else:
            rare = sum(c for c in self.counts.values() if c <= n)
        return (rare + 1) / (self.active_days(weekend, today) + 1)

    def to_json(self) -> dict:
        data = {
            "by_day": [[d, list(c.items())] for d, c in self.by_day.items()],
            "new_by_day": list(self.new_by_day.items()),
        }
        if self.daily:
            data["folded_through"] = self.folded_through
        return data

    @classmethod
    def from_json(cls, days: int, data: dict, daily: bool = False) -> DailyCounts:
        """Saved counts back. Counts saved without ``daily`` (design v1 or v2) are read as
        folded through the day before their last day, which is what learning once a day
        would have folded by then."""
        out = cls(days, daily)
        for day, items in data["by_day"]:
            out.by_day[day] = Counter({as_key(k): v for k, v in items})
        if daily and out.by_day:
            last = next(reversed(out.by_day))
            out.folded_through = data.get("folded_through", last - 1)
        for day, counts in out.by_day.items():
            if not daily or (out.folded_through is not None and day <= out.folded_through):
                out.counts.update(counts)
        out.new_by_day = Counter({d: n for d, n in data["new_by_day"]})
        out.new_uses = sum(out.new_by_day.values())
        return out


class DailyMean:
    """His average of a value over the last ``days`` days, kept as per-day sums.

    ``daily``: the average leaves out today (it is his history up to yesterday).
    """

    def __init__(self, days: int, daily: bool = False) -> None:
        self.days, self.daily = days, daily
        self.by_day: OrderedDict[int, list[float]] = OrderedDict()  # day -> [sum, count]
        self.total, self.n = 0.0, 0

    def mean_then_add(self, today: int, value: float) -> float | None:
        while self.by_day and next(iter(self.by_day)) <= today - self.days:
            _, (s, n) = self.by_day.popitem(last=False)
            self.total -= s
            self.n -= int(n)
        total, n = self.total, self.n
        if self.daily and today in self.by_day:
            total -= self.by_day[today][0]
            n -= int(self.by_day[today][1])
        mean = total / n if n else None
        bucket = self.by_day.setdefault(today, [0.0, 0])
        bucket[0] += value
        bucket[1] += 1
        self.total += value
        self.n += 1
        return mean

    def mean(self, today: int) -> float | None:
        """The average :meth:`mean_then_add` would return at ``today``, bit for bit, without
        adding a value or dropping a day (AI-8: the reply verdict reads his usual this way)."""
        total, n = self.total, self.n
        for day, (s, k) in self.by_day.items():
            if day > today - self.days:
                break
            total -= s  # the same subtractions, in the same order, as mean_then_add
            n -= int(k)
        if self.daily and today in self.by_day:
            total -= self.by_day[today][0]
            n -= int(self.by_day[today][1])
        return total / n if n else None

    def to_json(self) -> list:
        return [[d, s, n] for d, (s, n) in self.by_day.items()]

    @classmethod
    def from_json(cls, days: int, data: list, daily: bool = False) -> DailyMean:
        out = cls(days, daily)
        for day, s, n in data:
            out.by_day[day] = [s, n]
            out.total += s
            out.n += int(n)
        return out


class SlidingCounts:
    """How often each value was seen in the last ``seconds`` seconds."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self.events: deque = deque()  # (ts, value), oldest first
        self.counts: Counter = Counter()

    def add(self, ts: float, value) -> None:
        self.events.append((ts, value))
        self.counts[value] += 1

    def expire(self, now: float) -> None:
        while self.events and self.events[0][0] <= now - self.seconds:
            _, old = self.events.popleft()
            self.counts[old] -= 1
            if not self.counts[old]:
                del self.counts[old]

    def distinct(self) -> int:
        return len(self.counts)

    def total(self) -> int:
        return len(self.events)

    def count(self, value) -> int:
        return self.counts.get(value, 0)

    def to_json(self) -> list:
        return [[ts, v] for ts, v in self.events]

    @classmethod
    def from_json(cls, seconds: float, data: list) -> SlidingCounts:
        out = cls(seconds)
        for ts, value in data:
            out.add(ts, as_key(value))
        return out


class FirstUses:
    """Who started using what (an agent's first use in 90 days) over the last ``seconds``."""

    #: values with nothing left in the window are dropped once this many are kept
    PRUNE_AT = 4_096

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self.by_value: dict[tuple, deque] = {}  # (kind, value) -> (ts, agent), oldest first
        self._prune_at = self.PRUNE_AT

    def add(self, key: tuple, ts: float, agent: str) -> None:
        uses = self.by_value.get(key)
        if uses is None:
            if len(self.by_value) >= self._prune_at:
                self._prune(ts)
            uses = self.by_value[key] = deque()
        uses.append((ts, agent))

    def others(self, key: tuple, ts: float, agent: str, distinct: bool = False) -> int:
        """How many other agents first used ``key`` in the window before ``ts``.

        ``distinct`` (RF9, under ``legacy_fixes``): count each other agent once. Without it
        every recorded first use counts, as in v1-v4, so one agent whose first use was
        recorded twice counts twice.
        """
        uses = self.by_value.get(key)
        if not uses:
            return 0
        while uses and uses[0][0] < ts - self.seconds:
            uses.popleft()
        if distinct:
            return len({a for t, a in uses if t < ts and a != agent})
        return sum(1 for t, a in uses if t < ts and a != agent)

    def subset(self, keys: Iterable[tuple]) -> FirstUses:
        """A copy holding only ``keys``: what one message can read or add, so it can be
        scored on the copy without touching this one."""
        out = FirstUses(self.seconds)
        for key in keys:
            uses = self.by_value.get(key)
            if uses is not None:
                out.by_value[key] = deque(uses)
        return out

    def _prune(self, ts: float) -> None:
        """Drop values whose newest first use left the window; prune again only once the
        kept values have doubled, so pruning stays rare."""
        cutoff = ts - self.seconds
        stale = [k for k, uses in self.by_value.items() if not uses or uses[-1][0] < cutoff]
        for key in stale:
            del self.by_value[key]
        self._prune_at = max(self.PRUNE_AT, 2 * len(self.by_value))

    def to_json(self) -> list:
        return [
            [list(key), [[t, a] for t, a in uses]] for key, uses in self.by_value.items() if uses
        ]

    @classmethod
    def from_json(cls, seconds: float, data: list) -> FirstUses:
        out = cls(seconds)
        for key, uses in data:
            out.by_value[tuple(key)] = deque((t, a) for t, a in uses)
        return out


# ── design v5 ────────────────────────────────────────────────────────────────────────────────
def is_established(
    active_days: int,
    first_day: int,
    today: int,
    established_days: int = ESTABLISHED_DAYS,
    onboarding_days: int = ONBOARDING_DAYS,
) -> bool:
    """Spec 2.7's *established*: at least ``established_days`` active days in his history
    window and ``onboarding_days`` days since his first call (RF7, RF11, the floor budget and
    the established reference). ``active_days`` counts completed days, today left out."""
    return active_days >= established_days and today - first_day >= onboarding_days


class MinimumHistory:
    """B5: the past days a caller's history holds, ``[start(t), t - 1]``::

        start(t) = max(t - H + 1, min(t - W + 1, d_k(t)))

    with W = ``window_days`` (90), H = ``max_days`` (365), k = ``min_active_days`` (20) and
    d_k(t) his k-th most recent active day before t. So the window is his last W days (today
    included, as v4 counts them) when they hold k active days; otherwise it reaches back to his
    k-th most recent active day, at most H days, and a long absence does not erase his past.
    A caller with k or more active days in the last W days sees exactly v4's window.

    ``start`` never decreases: d_k(t) only moves forward as days pass, and :meth:`roll` keeps
    the larger of the old and new start in case a day number ever goes back.
    """

    def __init__(
        self,
        window_days: int = WINDOW_DAYS,
        min_active_days: int = ESTABLISHED_DAYS,
        max_days: int = MAX_HISTORY_DAYS,
    ) -> None:
        if not 1 <= window_days <= max_days:
            raise ValueError(f"need 1 <= window_days <= max_days, not {window_days}, {max_days}")
        if min_active_days < 1:
            raise ValueError(f"min_active_days must be at least 1, not {min_active_days}")
        self.window_days, self.min_active_days, self.max_days = (
            window_days,
            min_active_days,
            max_days,
        )
        self.active: list[int] = []  # his active days, sorted; the open day included
        self.start: int | None = None  # the window's start at the last roll

    def note(self, day: int) -> None:
        """``day`` had a scored call of his. Days that no later window can reach are dropped."""
        i = bisect_left(self.active, day)
        if i == len(self.active) or self.active[i] != day:
            self.active.insert(i, day)
        unreachable = bisect_left(self.active, self.active[-1] - self.max_days + 1)
        if unreachable:
            del self.active[:unreachable]

    def window_start(self, today: int) -> int:
        """start(today), without changing anything."""
        before = bisect_left(self.active, today)  # his active days before today
        start = today - self.max_days + 1
        if before >= self.min_active_days:
            kth = self.active[before - self.min_active_days]
            start = max(start, min(today - self.window_days + 1, kth))
        return start if self.start is None else max(start, self.start)

    def roll(self, today: int) -> int:
        """Move the window to ``today``, forget the days before it, and return its start."""
        self.start = self.window_start(today)
        gone = bisect_left(self.active, self.start)
        if gone:
            del self.active[:gone]
        return self.start

    def active_days(self, today: int) -> int:
        """His active days in the window, ``[start(today), today - 1]``."""
        start = self.window_start(today)
        return bisect_left(self.active, today) - bisect_left(self.active, start)

    def is_established(
        self, today: int, first_day: int, onboarding_days: int = ONBOARDING_DAYS
    ) -> bool:
        """:func:`is_established` with his active days and ``min_active_days`` (both 20 in
        the spec: B5 and RF7 share ``established_days``). Only active days inside his window
        count, so a caller away for longer than ``max_days`` is no longer established."""
        return is_established(
            self.active_days(today), first_day, today, self.min_active_days, onboarding_days
        )

    def to_json(self) -> dict:
        """JSON-safe snapshot; :meth:`from_json` reads it back to the same state."""
        return {"active": list(self.active), "start": self.start}

    @classmethod
    def from_json(
        cls,
        data: dict,
        window_days: int = WINDOW_DAYS,
        min_active_days: int = ESTABLISHED_DAYS,
        max_days: int = MAX_HISTORY_DAYS,
    ) -> MinimumHistory:
        """A history from :meth:`to_json`'s snapshot (give the same window, k and horizon)."""
        out = cls(window_days, min_active_days, max_days)
        out.active = sorted(set(data["active"]))
        out.start = data["start"]
        return out


class ValueDays:
    """CAL-1's value-days for one caller and one kind (tool, asset, network, client, hour),
    with DEP-7's cost guards.

    :meth:`days_used` is on how many past days of his window he used a value: each day counts
    once, however often he used it that day, and today counts only once the day has ended. A
    value he never used scores 0 and is the strangest possible.

    Count-of-counts: :meth:`count_of_counts` maps k to how many values were used on exactly k
    days, so tail sums (:meth:`values_at_most`, :meth:`value_days_at_most`) cost the number of
    distinct day counts, not the number of values (v4's ``DailyCounts.per_day`` tail is
    O(distinct values)).

    Value cap: at most ``max_values`` values are kept, the most recently used. Adding one more
    folds the least recently used into the overflow: it is forgotten, and from then on it is
    priced as new (0 days) until it is used again. :attr:`overflowed` counts these folds. A
    flood of distinct values therefore costs at most ``max_values`` entries a day, and makes the
    flooder's own values look new, which can only raise his scores.
    """

    def __init__(self, max_values: int = MAX_VALUES_PER_KIND) -> None:
        if max_values < 1:
            raise ValueError(f"max_values must be at least 1, not {max_values}")
        self.max_values = max_values
        self.overflowed = 0  # values folded into the overflow so far
        self._kept: OrderedDict[Hashable, int] = OrderedDict()  # value -> generation, LRU first
        self._days: dict[Hashable, int] = {}  # value -> past days used (only values with >= 1)
        self._cc: Counter = Counter()  # k -> values with exactly k past days
        self._by_day: OrderedDict[int, dict[Hashable, int]] = OrderedDict()  # day -> {value: gen}
        self._open_day: int | None = None
        self._open: dict[Hashable, int] = {}  # the open day's values -> generation
        self._next_gen = 0

    # ── the clock ──
    def roll(self, today: int, start: int) -> None:
        """Fold the open day into the past if ``today`` is later, then forget past days before
        ``start``. A value with no day left in the window and not used today is forgotten."""
        self._fold(today)
        while self._by_day and next(iter(self._by_day)) < start:
            _, values = self._by_day.popitem(last=False)
            for value, gen in values.items():
                if self._kept.get(value) == gen:
                    self._lose_day(value)

    def add(self, today: int, value: Hashable) -> None:
        """He used ``value`` today (it counts in :meth:`days_used` once the day has ended)."""
        self._fold(today)
        gen = self._kept.get(value)
        if gen is None:
            if len(self._kept) >= self.max_values:
                self._overflow()
            gen = self._kept[value] = self._next_gen
            self._next_gen += 1
        else:
            self._kept.move_to_end(value)
        self._open[value] = gen

    # ── reads: the past days of the window ──
    def days_used(self, value: Hashable) -> int:
        """On how many past days of the window he used ``value``; 0 if never, or if it was
        folded into the overflow (priced as new)."""
        return self._days.get(value, 0)

    def used_on(self, value: Hashable, day: int) -> bool:
        """Whether he used ``value`` on past ``day`` (for leaving a day out of its own count,
        as Hour of day's day maxima do). A use from before the value was folded into the
        overflow never counts again, even once the value is used again."""
        gen = self._kept.get(value)
        return gen is not None and self._by_day.get(day, {}).get(value) == gen

    def used_today(self, value: Hashable) -> bool:
        """Whether he used ``value`` on the open day."""
        return value in self._open

    def is_new(self, value: Hashable) -> bool:
        """Not used in the window, today included (v4's ``DailyCounts.is_new``)."""
        return not self.days_used(value) and not self.used_today(value)

    def active_days(self) -> int:
        """Past days of the window on which he used a value of this kind (A_d)."""
        return len(self._by_day)

    def distinct(self) -> int:
        """Values used on at least one past day of the window."""
        return len(self._days)

    def count_of_counts(self) -> dict[int, int]:
        """k -> how many values he used on exactly k past days (k >= 1)."""
        return dict(self._cc)

    def values_at_most(self, k: int) -> int:
        """How many values he used on between 1 and ``k`` past days."""
        return sum(n for c, n in self._cc.items() if c <= k)

    def value_days_at_most(self, k: int) -> int:
        """His value-days on values used on at most ``k`` past days (the tail v4 sums over
        calls, here over days)."""
        return sum(c * n for c, n in self._cc.items() if c <= k)

    def __len__(self) -> int:
        """Values kept: used in the window or today (at most ``max_values``)."""
        return len(self._kept)

    def stored_entries(self) -> int:
        """Value-day entries held, those of values folded into the overflow included: at most
        ``max_values`` per day kept, which is DEP-7's memory bound."""
        return len(self._open) + sum(len(values) for values in self._by_day.values())

    # ── internals ──
    def _fold(self, today: int) -> None:
        if self._open_day is None:
            self._open_day = today
        elif self._open_day < today:
            if self._open:
                for value in self._open:
                    self._gain_day(value)
                self._by_day[self._open_day] = self._open
            self._open, self._open_day = {}, today

    def _gain_day(self, value: Hashable) -> None:
        n = self._days.get(value, 0)
        if n:
            self._dec_count(n)
        self._days[value] = n + 1
        self._cc[n + 1] += 1

    def _lose_day(self, value: Hashable) -> None:
        n = self._days[value]
        self._dec_count(n)
        if n > 1:
            self._days[value] = n - 1
            self._cc[n - 1] += 1
            return
        del self._days[value]
        if value not in self._open:
            del self._kept[value]  # nothing left in the window: an unknown value again

    def _dec_count(self, k: int) -> None:
        if self._cc[k] == 1:
            del self._cc[k]
        else:
            self._cc[k] -= 1

    def _overflow(self) -> None:
        """Fold the least recently used value into the overflow. Its past entries stay in
        their days (each day keeps counting toward ``active_days``) but no longer match a
        kept generation, so they never count again."""
        value, _ = self._kept.popitem(last=False)
        n = self._days.pop(value, 0)
        if n:
            self._dec_count(n)
        self._open.pop(value, None)
        self.overflowed += 1

    # ── state ──
    def to_json(self) -> dict:
        """JSON-safe snapshot. It leaves out the dead entries of values folded into the
        overflow and keeps their days, so :meth:`from_json` reads back the same counts."""

        def live(values: dict[Hashable, int]) -> list:
            return [v for v, gen in values.items() if self._kept.get(v) == gen]

        return {
            "kept": list(self._kept),
            "by_day": [[day, live(values)] for day, values in self._by_day.items()],
            "open_day": self._open_day,
            "open": list(self._open),
            "overflowed": self.overflowed,
        }

    @classmethod
    def from_json(cls, data: dict, max_values: int = MAX_VALUES_PER_KIND) -> ValueDays:
        """A store from :meth:`to_json`'s snapshot (give the same ``max_values``)."""
        out = cls(max_values)
        out._kept = OrderedDict((as_key(v), gen) for gen, v in enumerate(data["kept"]))
        out._next_gen = len(out._kept)
        for day, values in data["by_day"]:
            out._by_day[day] = {(v := as_key(raw)): out._kept[v] for raw in values}
            for value in out._by_day[day]:
                out._gain_day(value)
        out._open_day = data["open_day"]
        out._open = {(v := as_key(raw)): out._kept[v] for raw in data["open"]}
        out.overflowed = data["overflowed"]
        return out


def slot_of(local_s: float, slot_s: float = HOUR_SLOT_S) -> int:
    """The slot a time falls in, for :class:`SlotQuantile`. Pass the caller's wall-clock
    seconds (``clock.local_seconds``) so slots are his clock hours (or 10-minute slots)."""
    return math.floor(local_s / slot_s)


class SlotQuantile:
    """B7: the robust usual of an amount, for its strength only (commonness compares raw day
    maxima and does not use it)::

        usual = Q_q { the amount's largest value in slot b : b an active slot of his in the
                      window, before today }

    with q = ``quantile`` (0.75), as the inverted CDF: the smallest value that at least q of
    his active slots stay at or below. With fewer than ``min_slots`` active slots it is their
    maximum; with none, None (the dimension does not take part). One extreme hour cannot move
    it (breakdown point 1 - q), unlike v4's call-weighted mean, where a busy hour adds one
    sample per call.

    Kept as one histogram per past day (value -> slots), so the window's quantile is computed
    once a day, when the window changes, and memory is one entry per distinct slot value a day.
    """

    def __init__(
        self, quantile: float = USUAL_QUANTILE, min_slots: int = MIN_QUANTILE_SLOTS
    ) -> None:
        if not 0 < quantile <= 1:
            raise ValueError(f"quantile must be in (0, 1], not {quantile}")
        if min_slots < 1:
            raise ValueError(f"min_slots must be at least 1, not {min_slots}")
        self.quantile, self.min_slots = quantile, min_slots
        self._by_day: OrderedDict[int, Counter] = OrderedDict()  # day -> value -> slots
        self._window: Counter = Counter()  # the past days' histograms added up
        self._slots = 0
        self._open_day: int | None = None
        self._open: dict[int, float] = {}  # the open day's slot -> its largest value
        self._usual: float | None = None
        self._stale = True

    def observe(self, today: int, slot: int, value: float) -> None:
        """The amount was ``value`` in ``slot`` of today (:func:`slot_of`); a slot keeps its
        largest value."""
        self._fold(today)
        old = self._open.get(slot)
        if old is None or value > old:
            self._open[slot] = value

    def roll(self, today: int, start: int) -> None:
        """Fold the open day if ``today`` is later; forget past days before ``start``."""
        self._fold(today)
        while self._by_day and next(iter(self._by_day)) < start:
            _, counts = self._by_day.popitem(last=False)
            for value, n in counts.items():
                left = self._window[value] - n
                if left:
                    self._window[value] = left
                else:
                    del self._window[value]
                self._slots -= n
            self._stale = True

    def usual(self) -> float | None:
        """His usual over the window's past days (see the class docstring)."""
        if self._stale:
            self._usual, self._stale = self._quantile(), False
        return self._usual

    def slots(self) -> int:
        """His active slots in the window's past days."""
        return self._slots

    def _quantile(self) -> float | None:
        if not self._slots:
            return None
        values = sorted(self._window)
        if self._slots < self.min_slots:
            return float(values[-1])
        rank = max(1, math.ceil(self.quantile * self._slots - QUANTILE_TOLERANCE))
        seen = 0
        for value in values:
            seen += self._window[value]
            if seen >= rank:
                return float(value)
        return float(values[-1])  # unreachable: the counts add up to _slots

    def _fold(self, today: int) -> None:
        if self._open_day is None:
            self._open_day = today
        elif self._open_day < today:
            if self._open:
                counts = Counter(self._open.values())
                self._by_day[self._open_day] = counts
                self._window.update(counts)
                self._slots += len(self._open)
                self._stale = True
            self._open, self._open_day = {}, today

    def to_json(self) -> dict:
        """JSON-safe snapshot; :meth:`from_json` reads it back to the same usual."""
        return {
            "by_day": [[day, list(counts.items())] for day, counts in self._by_day.items()],
            "open_day": self._open_day,
            "open": list(self._open.items()),
        }

    @classmethod
    def from_json(
        cls, data: dict, quantile: float = USUAL_QUANTILE, min_slots: int = MIN_QUANTILE_SLOTS
    ) -> SlotQuantile:
        """A store from :meth:`to_json`'s snapshot (give the same quantile and slot minimum)."""
        out = cls(quantile, min_slots)
        for day, items in data["by_day"]:
            counts = out._by_day[day] = Counter({v: n for v, n in items})
            out._window.update(counts)
            out._slots += sum(counts.values())
        out._open_day = data["open_day"]
        out._open = {slot: value for slot, value in data["open"]}
        return out


class WindowMean:
    """B5's version of :class:`DailyMean`: his average of a value over the past days of his
    window, ``[start, today - 1]`` (today is left out, as v3-v4 learn once a day).

    The mean is summed afresh (``math.fsum``) whenever the window changes, so it does not
    depend on the order days came and went: a restored copy gives the same mean, bit for bit.
    """

    def __init__(self) -> None:
        self._by_day: OrderedDict[int, list[float]] = OrderedDict()  # day -> [sum, count]
        self._open_day: int | None = None
        self._open = [0.0, 0]
        self._mean: float | None = None
        self._stale = True

    def add(self, today: int, value: float) -> None:
        """A sample of today (it counts once the day has ended)."""
        self._fold(today)
        self._open[0] += value
        self._open[1] += 1

    def roll(self, today: int, start: int) -> None:
        """Fold the open day if ``today`` is later; forget past days before ``start``."""
        self._fold(today)
        while self._by_day and next(iter(self._by_day)) < start:
            self._by_day.popitem(last=False)
            self._stale = True

    def mean(self) -> float | None:
        """His average over the window's past days; None without a sample."""
        if self._stale:
            n = sum(int(k) for _, k in self._by_day.values())
            total = math.fsum(s for s, _ in self._by_day.values())
            self._mean, self._stale = (total / n if n else None), False
        return self._mean

    def _fold(self, today: int) -> None:
        if self._open_day is None:
            self._open_day = today
        elif self._open_day < today:
            if self._open[1]:
                self._by_day[self._open_day] = self._open
                self._stale = True
            self._open, self._open_day = [0.0, 0], today

    def to_json(self) -> dict:
        """JSON-safe snapshot; :meth:`from_json` reads it back to the same mean, bit for bit."""
        return {
            "by_day": [[d, s, n] for d, (s, n) in self._by_day.items()],
            "open_day": self._open_day,
            "open": list(self._open),
        }

    @classmethod
    def from_json(cls, data: dict) -> WindowMean:
        """A mean from :meth:`to_json`'s snapshot."""
        out = cls()
        for day, s, n in data["by_day"]:
            out._by_day[day] = [s, n]
        out._open_day = data["open_day"]
        out._open = list(data["open"])
        return out


class SlidingTotal:
    """AI-8: the sum of integer amounts added in ``(now - seconds, now]`` (Read volume: reply
    bytes in the last hour).

    Bounded: adds within one ``resolution_s`` bucket share an entry, and every add drops what
    left the window by its own time. So the store holds at most ``seconds / resolution_s + 1``
    entries however many replies arrive, even when it is only added to and read with the pure
    :meth:`total_at` (the score path). ``resolution_s = None`` keeps one entry per distinct
    time: exact, and bounded by the replies of one window, as v4's :class:`SlidingCounts` is
    by its calls.

    Tolerance: an entry leaves the window when its newest add does, so a bucket's earlier bytes
    may count up to ``resolution_s`` longer than AI-8's exact window. With the default 1 s
    buckets, Read volume at t sums the replies in ``(t - 3600 - delta, t]`` with ``0 <= delta
    < 1 s``. That errs toward counting more, and it is deterministic, so live and offline
    agree. Amounts are integers, so the total is exact and a restored total equals the live
    one. Times should not go back; an earlier time is counted at the newest entry's time.
    """

    def __init__(
        self, seconds: float, resolution_s: float | None = SLIDING_TOTAL_RESOLUTION_S
    ) -> None:
        if seconds <= 0:
            raise ValueError(f"seconds must be positive, not {seconds}")
        if resolution_s is not None and resolution_s <= 0:
            raise ValueError(f"resolution_s must be positive or None, not {resolution_s}")
        self.seconds, self.resolution_s = seconds, resolution_s
        self.entries: deque[list] = deque()  # [newest time, amount], oldest first
        self._total = 0

    def add(self, ts: float, amount: int) -> None:
        """``amount`` (a non-negative integer, numpy's included) arrived at ``ts``; what left
        the window by then is dropped."""
        if isinstance(amount, bool):
            raise TypeError("amount must be an int, not bool")
        amount = operator.index(amount)  # TypeError for a float; a numpy int becomes an int
        if amount < 0:
            raise ValueError(f"amount must not be negative, not {amount}")
        last = self.entries[-1] if self.entries else None
        if last is not None:
            ts = max(ts, last[0])
        if last is not None and (ts == last[0] or self._same_bucket(ts, last[0])):
            last[0] = ts
            last[1] += amount
        else:
            self.entries.append([ts, amount])
        self._total += amount
        self.expire(ts)

    def expire(self, now: float) -> None:
        """Drop what left the window by ``now``."""
        while self.entries and self.entries[0][0] <= now - self.seconds:
            self._total -= self.entries.popleft()[1]

    def total(self) -> int:
        """The window's sum at the latest time given to :meth:`add` or :meth:`expire`."""
        return self._total

    def total_at(self, now: float) -> int:
        """The window's sum at ``now``, without dropping anything. ``now`` should not be
        earlier than the newest add: what left the window by then is gone."""
        total = self._total
        for ts, amount in self.entries:
            if ts > now - self.seconds:
                break
            total -= amount
        return total

    def __len__(self) -> int:
        """Entries held: at most ``seconds / resolution_s + 1`` with buckets."""
        return len(self.entries)

    def _same_bucket(self, ts: float, other: float) -> bool:
        """Whether two times share a ``resolution_s`` bucket; never in exact mode."""
        if self.resolution_s is None:
            return False
        return math.floor(ts / self.resolution_s) == math.floor(other / self.resolution_s)

    def to_json(self) -> list:
        """JSON-safe snapshot, ``[[newest time, amount], ...]`` oldest first; :meth:`from_json`
        reads it back to the same entries and total."""
        return [list(entry) for entry in self.entries]

    @classmethod
    def from_json(
        cls, seconds: float, data: list, resolution_s: float | None = SLIDING_TOTAL_RESOLUTION_S
    ) -> SlidingTotal:
        """A store from :meth:`to_json`'s snapshot (give the same window and resolution)."""
        out = cls(seconds, resolution_s)
        for ts, amount in data:
            out.entries.append([ts, amount])
            out._total += amount
        return out


def value_strength(callers: int) -> float:
    """A value record's strength (spec 2.3): the fewer of the route's callers used the value
    in the window, the stronger; a value new to the organisation (0 callers) is strongest, 1."""
    if callers < 0:
        raise ValueError(f"callers must not be negative, not {callers}")
    return 1.0 / (1 + callers)


def _used_between(days: list[int | None], low: int, high: int) -> bool:
    """Whether a caller's previous or last day of use (``[previous, last]``) lies in
    ``[low, high)``. Unpacked, not looped: it runs once per caller of a value."""
    previous, last = days
    return (last is not None and low <= last < high) or (
        previous is not None and low <= previous < high
    )


def _listed_name(listed: Mapping[Hashable, int | None], value: Hashable) -> Hashable:
    """``value`` as a listing names it: itself when listed; else, for an AI-7 tool key
    ``tool:operation``, its longest listed prefix before a :data:`TOOL_KEY_SEPARATOR`."""
    if value in listed or not isinstance(value, str):
        return value
    cut = value.rfind(TOOL_KEY_SEPARATOR)
    while cut > 0:
        if value[:cut] in listed:
            return value[:cut]
        cut = value.rfind(TOOL_KEY_SEPARATOR, 0, cut)
    return value


@dataclass(slots=True)
class _OrgValue:
    """One value's record in :class:`OrgFirstSeen`."""

    run_start: int  # the day its current run of use began
    last_day: int  # the last day it was used
    #: caller -> [the caller's previous day of use, its last day of use]
    seen_by: dict[str, list[int | None]] = field(default_factory=dict)
    prune_at: int = ORG_CALLERS_PRUNE_AT  # stale callers are pruned past this many
    memo_day: int | None = None  # the day ``memo_count`` answers for; None: no memo
    memo_count: int = 0  # callers(today=memo_day), nobody excluded


class OrgFirstSeen:
    """The route's memory of each value, per kind, on the route's days (CAL-7's clock):

    - RF7's *new to the organisation*: the value's current run of use began (its first use
      after ``window_days`` with no use) within the last ``org_new_days``, and the store saw
      every one of the ``window_days`` before that run (:attr:`observed_since`). A use from
      before the store began (a DEP-6 bootstrap, or a gateway put in front of a server already
      in use) could otherwise hide. For a kind with a listing (the server's tool list,
      :meth:`note_listing`), the value instead entered the listing that recently; the first
      listing seen is the baseline, so nothing in it entered.
    - Footprint's record strength: :meth:`callers`, how many of the route's callers used the
      value in the window's past days, ``[today - window_days + 1, today - 1]``.

    Bounded: a value with no use in the window is dropped, and at most ``max_values`` values
    are kept per kind (least recently used out first). An evicted value counts no callers
    (strongest) and, as long as an eviction could have hidden its earlier use, is never new to
    the organisation, so a flood cannot buy an org discount.

    Trade-off (open for I1 and J1): the cap is shared by the route. One caller who floods a
    kind whose values it chooses (clientInfo families, asset pseudonyms) evicts other callers'
    values: those count no callers until used again, and no run of that kind that begins
    within ``window_days`` after the flood is new to the organisation. Both fail toward
    alerting, but one identity can raise false alarms across the route. A per-caller quota
    would not stop it, since an unsigned caller can take a new identity at will (D5).
    """

    def __init__(
        self,
        window_days: int = WINDOW_DAYS,
        max_values: int = ORG_MAX_VALUES_PER_KIND,
        observed_since: int | None = None,
    ) -> None:
        """``observed_since``: the first route day whose calls this store sees, such as the
        first day of a replayed log (DEP-6); None takes the day of the first :meth:`note`. A
        route known to have had no calls before day ``d0`` may pass ``d0 - window_days + 1``,
        so that values count as new from its first day on."""
        if window_days < 1 or max_values < 1:
            raise ValueError(
                f"need positive window_days and max_values: {window_days}, {max_values}"
            )
        self.window_days, self.max_values = window_days, max_values
        self.observed_since = observed_since
        #: kind -> value -> its record, least recently used first
        self.kinds: dict[str, OrderedDict[Hashable, _OrgValue]] = {}
        self.evictions: dict[str, deque[int]] = {}  # kind -> days with an eviction, oldest first
        self.listed: dict[str, dict[Hashable, int | None]] = {}  # kind -> value -> day it entered

    def note(self, kind: str, value: Hashable, caller: str, day: int) -> None:
        """``caller`` used ``value`` (of ``kind``) on route day ``day``."""
        if self.observed_since is None:
            self.observed_since = day
        values = self.kinds.setdefault(kind, OrderedDict())
        while values and next(iter(values.values())).last_day <= day - self.window_days:
            values.popitem(last=False)  # no use left in the window
        record = values.get(value)
        if record is None:
            if len(values) >= self.max_values:
                values.popitem(last=False)
                self._evicted(kind, day)
            record = values[value] = _OrgValue(day, day)
        else:
            if record.last_day <= day - self.window_days:
                record.run_start = day  # a new run after a gap (a late note can leave one here)
            elif record.run_start - self.window_days < day < record.run_start:
                record.run_start = day  # a late note (a slow reply's commit) from the run's start
            record.last_day = max(record.last_day, day)
            values.move_to_end(value)
            if day != record.memo_day:
                record.memo_day = None  # a use on another day can change the memo's answer
        seen = record.seen_by.get(caller)
        if seen is None:
            record.seen_by[caller] = [None, day]
        elif day > seen[1]:
            record.seen_by[caller] = [seen[1], day]
        elif day < seen[1] and (seen[0] is None or day > seen[0]):
            seen[0] = day  # a late note: the caller's latest day of use before its last
        if len(record.seen_by) > record.prune_at:
            low = day - self.window_days + 1
            for stale in [c for c, (_, last) in record.seen_by.items() if last < low]:
                del record.seen_by[stale]
            record.prune_at = max(ORG_CALLERS_PRUNE_AT, 2 * len(record.seen_by))

    def note_listing(self, kind: str, values: Iterable[Hashable], day: int) -> None:
        """The route's current listing of ``kind``: the bare tool names of a ``tools/list``
        reply, on a catalog change. A value absent from the previous listing entered it on
        ``day``, so a tool removed and listed again enters again; values gone from the
        listing are dropped. From then on, newness for ``kind`` uses the listing."""
        current = sorted(set(values), key=repr)  # the same order in every process
        before = self.listed.get(kind)
        if before is None:
            self.listed[kind] = dict.fromkeys(current)  # baseline: nothing entered
            return
        self.listed[kind] = {v: (before[v] if v in before else day) for v in current}

    def is_new_to_org(
        self, kind: str, value: Hashable, today: int, new_days: int = ORG_NEW_DAYS
    ) -> bool:
        """RF7's *new to the organisation* (see the class docstring). A value never seen in
        the window is not: the org discount needs colleagues who used it. For a kind with a
        listing, ``value`` may be the bare tool name or the Footprint value, AI-7's
        ``tool:operation`` key: a key the listing lacks is read as its tool name."""
        if not 1 <= new_days <= self.window_days:
            raise ValueError(f"new_days must be in [1, {self.window_days}], not {new_days}")
        listed = self.listed.get(kind)
        if listed is not None:
            entered = listed.get(_listed_name(listed, value))
            return entered is not None and 0 <= today - entered < new_days
        record = self.kinds.get(kind, {}).get(value)
        if record is None or record.last_day <= today - self.window_days:
            return False
        run_start = record.run_start
        if not 0 <= today - run_start < new_days:
            return False
        low = run_start - self.window_days + 1  # a use before the run would lie in [low, run)
        if self.observed_since is None or low < self.observed_since:
            return False  # the store did not see all of those days: a use may hide there
        return not any(low <= d <= run_start for d in self.evictions.get(kind, ()))

    def callers(self, kind: str, value: Hashable, today: int, exclude: str | None = None) -> int:
        """How many of the route's callers (other than ``exclude``) used ``value`` on a past
        day of the window, ``[today - window_days + 1, today - 1]``. Today's uses do not
        count, so the answer holds all day: it is counted once per value and day (a memo,
        dropped when a use on another day arrives)."""
        record = self.kinds.get(kind, {}).get(value)
        if record is None:
            return 0
        low = today - self.window_days + 1
        if record.memo_day != today:
            record.memo_count = sum(
                1 for days in record.seen_by.values() if _used_between(days, low, today)
            )
            record.memo_day = today
        seen = None if exclude is None else record.seen_by.get(exclude)
        excluded = seen is not None and _used_between(seen, low, today)
        return record.memo_count - int(excluded)

    def run_start(self, kind: str, value: Hashable) -> int | None:
        """The day the value's current run of use began; None if it is not kept."""
        record = self.kinds.get(kind, {}).get(value)
        return None if record is None else record.run_start

    def __len__(self) -> int:
        """Values kept, over every kind (at most ``max_values`` per kind)."""
        return sum(len(values) for values in self.kinds.values())

    def _evicted(self, kind: str, day: int) -> None:
        """Remember that ``day`` evicted a value of ``kind``: a use before it may be hidden."""
        days = self.evictions.setdefault(kind, deque())
        if not days or days[-1] != day:
            days.append(day)
        while days and days[0] <= day - 2 * self.window_days:  # covers every run new_days allows
            days.popleft()

    def to_json(self) -> dict:
        """JSON-safe snapshot; :meth:`from_json` reads it back to the same answers (memos and
        prune thresholds start afresh)."""
        return {
            "kinds": {
                kind: [
                    [value, r.run_start, r.last_day, [[c, p, d] for c, (p, d) in r.seen_by.items()]]
                    for value, r in values.items()
                ]
                for kind, values in self.kinds.items()
            },
            "evictions": {kind: list(days) for kind, days in self.evictions.items()},
            "listed": {kind: list(values.items()) for kind, values in self.listed.items()},
            "observed_since": self.observed_since,
        }

    @classmethod
    def from_json(
        cls, data: dict, window_days: int = WINDOW_DAYS, max_values: int = ORG_MAX_VALUES_PER_KIND
    ) -> OrgFirstSeen:
        """A store from :meth:`to_json`'s snapshot (give the same window and cap)."""
        out = cls(window_days, max_values, data["observed_since"])
        for kind, rows in data["kinds"].items():
            values = out.kinds[kind] = OrderedDict()
            for value, start, last, seen_by in rows:
                callers = {c: [p, d] for c, p, d in seen_by}
                prune_at = max(ORG_CALLERS_PRUNE_AT, 2 * len(callers))
                values[as_key(value)] = _OrgValue(start, last, callers, prune_at)
        out.evictions = {kind: deque(days) for kind, days in data["evictions"].items()}
        out.listed = {
            kind: {as_key(v): entered for v, entered in rows}
            for kind, rows in data["listed"].items()
        }
        return out


class ColleagueFirstUses:
    """RF7: who started using what in the last ``seconds`` (7 days), counting only callers who
    were established when they started (:func:`is_established`). A first use by a caller who
    was not established is never kept, so new identities (Sybils) can neither count nor fill
    the memory. Each caller counts once per value (his latest first use).

    Bounded: at most ``max_keys`` values, least recently started out first; a dropped value
    counts no colleagues, which only withholds a discount.
    """

    def __init__(
        self, seconds: float = FIRST_USE_SECONDS, max_keys: int = MAX_FIRST_USE_KEYS
    ) -> None:
        if seconds <= 0 or max_keys < 1:
            raise ValueError(f"need positive seconds and max_keys: {seconds}, {max_keys}")
        self.seconds, self.max_keys = seconds, max_keys
        self.dropped = 0  # values dropped at the cap (saved with the state)
        #: (kind, value) -> {caller: time of his latest first use}, least recently started first
        self.by_value: OrderedDict[tuple, dict[str, float]] = OrderedDict()

    def add(self, key: tuple, ts: float, agent: str, *, established: bool) -> None:
        """``agent`` first used ``key`` (a (kind, value) pair) at ``ts``; kept only when he was
        ``established`` then."""
        if not established:
            return
        uses = self.by_value.get(key)
        if uses is None:
            self._make_room(ts)
            uses = self.by_value[key] = {}
        else:
            self.by_value.move_to_end(key)
        uses.pop(agent, None)
        uses[agent] = ts  # time order, oldest first
        while uses and next(iter(uses.values())) < ts - self.seconds:
            del uses[next(iter(uses))]

    def colleagues(self, key: tuple, ts: float, agent: str) -> int:
        """How many other established callers first used ``key`` in ``[ts - seconds, ts)``
        (the window ``FirstUses.others`` uses)."""
        uses = self.by_value.get(key)
        if not uses:
            return 0
        low = ts - self.seconds
        return sum(1 for a, t in uses.items() if a != agent and low <= t < ts)

    def subset(self, keys: Iterable[tuple]) -> ColleagueFirstUses:
        """A copy holding only ``keys``, for scoring one message on a copy."""
        out = ColleagueFirstUses(self.seconds, self.max_keys)
        for key in keys:
            uses = self.by_value.get(key)
            if uses is not None:
                out.by_value[key] = dict(uses)
        return out

    def __len__(self) -> int:
        """Values kept (at most ``max_keys``)."""
        return len(self.by_value)

    def _make_room(self, ts: float) -> None:
        """Before a new value: drop values whose first uses all left the window, then the
        least recently started ones while the cap is reached."""
        cutoff = ts - self.seconds
        while self.by_value:
            uses = next(iter(self.by_value.values()))
            if uses and max(uses.values()) >= cutoff and len(self.by_value) < self.max_keys:
                return
            self.by_value.popitem(last=False)
            if uses and max(uses.values()) >= cutoff:
                self.dropped += 1  # still in the window: a real drop, not an expiry

    def to_json(self) -> dict:
        """JSON-safe snapshot, the drop count included; :meth:`from_json` reads it back to
        the same state."""
        return {
            "keys": [
                [list(key), [[a, t] for a, t in uses.items()]]
                for key, uses in self.by_value.items()
            ],
            "dropped": self.dropped,
        }

    @classmethod
    def from_json(
        cls, data: dict, seconds: float = FIRST_USE_SECONDS, max_keys: int = MAX_FIRST_USE_KEYS
    ) -> ColleagueFirstUses:
        """A store from :meth:`to_json`'s snapshot (give the same window and cap)."""
        out = cls(seconds, max_keys)
        for key, uses in data["keys"]:
            out.by_value[tuple(as_key(k) for k in key)] = {a: t for a, t in uses}
        out.dropped = data["dropped"]
        return out


def org_discount_applies(
    kind: str,
    colleagues: int,
    new_to_org: bool,
    operation: str | None = None,
    static: int | None = None,
    *,
    min_colleagues: int = ORG_DISCOUNT_AGENTS,
    reads_only: bool = True,
    max_static: int | None = ORG_DISCOUNT_MAX_STATIC,
) -> bool:
    """RF7 (spec 2.7): something new for the caller counts as ordinary when at least
    ``min_colleagues`` established colleagues started it in the last 7 days
    (:meth:`ColleagueFirstUses.colleagues`) and it is new to the organisation
    (:meth:`OrgFirstSeen.is_new_to_org`; pass True when ``org_new_days`` is off), unless it is
    a write tool (``reads_only``) or a high-impact tool (static level above ``max_static``).

    The tool exclusions apply to the tool dimension only: a new network or client is still
    discounted on a write call. They fail closed: while an exclusion is on, a tool whose
    label it reads is unknown (``operation`` not ``"read"``, or ``static`` None) is not
    discounted. A tool new to the organisation is often one the static scan has not labelled
    yet, and the server is the protected asset. ``reads_only = False`` and
    ``max_static = None`` are v1-v4's values (no exclusion, so unknown labels do not matter)."""
    if colleagues < min_colleagues or not new_to_org:
        return False
    if kind != TOOL_KIND:
        return True
    if reads_only and operation != READ_OPERATION:
        return False  # a write tool, or one not labelled yet
    return max_static is None or (static is not None and static <= max_static)
