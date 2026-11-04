"""v5 calibration (CAL-1..CAL-7): commonness, the record rank, budget shares, floors, the clock.

Design v5 prices every dimension by one rule (``knowledge_base/v5-design-spec.md`` sections
2.3-2.6 and 2.9). Everything here is pure Python, incremental and online; the engine (Batch 3,
K1) calls it after its scores dict. The notation is the spec's::

    q_d = (1 + D_d) / (A_d + 1)                     commonness (CAL-1)
    r_d = (1 + #{record-days in [t-89, t-1] with strength >= s}) / (N_d + 1)
    q_d = min(1 / (A_d + 1), r_d)                   on a record (CAL-2)
    q_stat = min_d q_d / w_d                        budget shares, never renormalised (CAL-3)
    q = min(q_stat, q_floor)                        alert floor alpha, watch floor 1/8 (CAL-4)
    s1 = 1 / (1 + 2q);  M = max(m_min, g(s1));  alert when q <= alpha        (CAL-5)

- :class:`DayRings` (CAL-1): one caller's closed days: day maxima of amounts, and on which days
  each value and each flag key was used, with DEP-7's cap on distinct keys. It answers D_d and
  A_d.
- :class:`RecordReference` (CAL-2): the route's ranked agent-days (record-days, and the raised
  days of the two flags priced against the organisation) and N_d, in one bucket per (filing day,
  ready day). Each rollover builds a :class:`ReferenceVersion`, one sorted array per dimension
  merged from the buckets' sorted runs, so a rank is one bisect.
- :func:`combine` (CAL-3), :func:`apply_floors` (CAL-4), :func:`outputs` (CAL-5).
- :class:`SurgeGuard` (CAL-6): on a day when records on d come in bulk, today's records are also
  ranked among today's agent-days so far, and q is the larger rank.
- :class:`RouteClock` (CAL-7): the route's zone and 04:00 rollover, the open-day buffer and the
  sweep that folds every caller whose local day ended, dormant callers included.
- :class:`GatewayReference` (GWR): one reference, surge guard and clock for several routes.

**Validity.** Every query says what it reads. *Frozen* means fixed before the caller's local day
began: his closed days (his rings), and the reference version that was current when his local day
began. A local day (B9) need not begin at the route's rollover, so the clock keeps the last
:data:`KEPT_VERSIONS` versions and prices a whole agent-day against one of them. Nothing a call
does during an agent-day moves a frozen answer, which is what makes the bound per agent-day (spec
2.6). *Open* means today's running state; only the surge guard reads it, and it can only raise q.

The tune variants (spec 4.4) are settings: ``record_hold_days`` (HOLD), ``leave_top_identity_out``
(TOP), ``record_reference = "established"`` (EST) and ``reference_scope = "gateway"`` (GWR).
Footprint watch-only (FP-1, D3 (b)) needs nothing here: its share is None and :func:`combine`
treats it as a watch-only term.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, OrderedDict
from collections.abc import Collection, Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from itertools import chain
from numbers import Real
from typing import TYPE_CHECKING

from mcp_security.behaviour.clock import (
    DAY_START_HOUR,
    DEFAULT_ZONE,
    check_day_start,
    local_day,
    zone,
)

if TYPE_CHECKING:  # the engine imports this module, so no runtime import back
    from mcp_security.behaviour.engine import BehaviourConfig

# ── constants (the spec's v5 defaults; the engine's config carries the live values) ─────────
HISTORY_DAYS = 90  # the window, today included
PAST_DAYS = HISTORY_DAYS - 1  # [t-89, t-1]: A_d <= 89
MIN_ACTIVE_DAYS = 20  # B5: the window stretches back until it holds this many active days
WATCH_CAP = 2 / 15  # CAL-3: a watch-only term's q/w never falls below this
WATCH_SHARE = 1 / 12  # CAL-3: watch-only terms are scaled as v_d = max(12 q_d, WATCH_CAP)
ALERT_ALPHA = 0.01  # CAL-5: the deployed 1% line
WATCH_FLOOR_RATE = 0.125  # CAL-4: q of the watch floor (x2.63)
SURGE_MIN = 5  # CAL-6: a surge needs at least this many record agent-days today ...
SURGE_FACTOR = 3.0  # ... and this many times the window's daily mean
ROUTE_WARMUP_DAYS = 14  # CAL-4: alert floors act as watch floors until the route has these
MAX_MULTIPLIER = 5.0  # g's top
MIN_MULTIPLIER = 1.0  # PS8, D2: v5's M never falls below 1
CURVE_LOW_BASE = 0.7  # the base of g's lower branch (engine.py's curve)
EDGE_OF_ORDINARY = 0.5  # s = 1/2, q = 1/2
DIGEST_CHARS = 12  # as the gateway's digests
CAP_TOLERANCE = 1e-12  # relative slack in the cap and path-activity tests (float rounding)
#: CAL-7: reference versions kept. A local day lasts at most 25 hours and a route day at least
#: 23, so the local day of any call began at most two rollovers before it.
KEPT_VERSIONS = 3
DAY_START_CACHE = 4096  # (day, zone) start instants kept by :func:`day_start_ts`
#: DEP-7 guard: a value or flag key past a cap is kept as this one value, priced as new
OVERFLOW = "\x00overflow"

#: Engine keys this module treats specially (tests check they equal the engine's).
REQUEST_TOO_BIG = "request_too_big"  # Oversized request: priced against the organisation
PROTOCOL_SKIP = "protocol_skip"  # Missing handshake: org-priced and watch-only
ORG_PRICED = frozenset({REQUEST_TOO_BIG, PROTOCOL_SKIP})
UNSURGED = frozenset({PROTOCOL_SKIP})  # the surge guard covers records and Oversized request

#: Floors (CAL-4, SEQ-2): their names are d* when they win, and their levels.
FIRST_ACCESS_FLOOR = "first_access_floor"
COPY_FLOOR = "copy_floor"
FLOOR_ORDER = (FIRST_ACCESS_FLOOR, COPY_FLOOR)  # floor_budget's order
ALERT, WATCH = "alert", "watch"
ALERT_SENSITIVITY, WATCH_SENSITIVITY = 5, 4

#: Settings choices (the config's tune switches).
ALL, ESTABLISHED = "all", "established"
ROUTE, GATEWAY = "route", "gateway"
_KEY_SEP = "\x1f"
#: GWR: the settings every member route shares with its gateway reference.
SHARED_SETTINGS = (
    "route_zone",
    "day_start_hour",
    "past_days",
    "surge_min",
    "surge_factor",
    "leave_top_identity_out",
    "record_reference",
)


# ── settings ────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CalibrationSettings:
    """The config fields calibration reads. :meth:`from_config` takes them from a
    ``BehaviourConfig``; tests and probes may build them directly. A None surge or warm-up
    field switches that part off (the spec's off values)."""

    past_days: int = PAST_DAYS
    route_zone: str = DEFAULT_ZONE
    day_start_hour: float = DAY_START_HOUR
    record_rank: bool = True  # CAL-2; off: a record is priced by its personal part only
    surge_min: int | None = SURGE_MIN
    surge_factor: float | None = SURGE_FACTOR
    route_warmup_days: int | None = ROUTE_WARMUP_DAYS
    record_hold_days: int | None = None  # HOLD
    leave_top_identity_out: bool = False  # TOP
    record_reference: str = ALL  # EST: ALL or ESTABLISHED
    reference_scope: str = ROUTE  # GWR: ROUTE or GATEWAY
    max_history_days: int | None = None  # B5: None keeps the fixed window
    min_active_days: int = MIN_ACTIVE_DAYS  # B5
    max_values: int | None = None  # DEP-7: distinct values (or flag keys) per caller and kind

    def __post_init__(self) -> None:
        for name in ("past_days", "min_active_days"):
            _check_positive_int(name, getattr(self, name))
        for name in ("surge_min", "route_warmup_days", "record_hold_days", "max_values"):
            if getattr(self, name) is not None:
                _check_positive_int(name, getattr(self, name))
        if self.surge_factor is not None and not self.surge_factor >= 1:
            raise ValueError(f"surge_factor must be at least 1, not {self.surge_factor!r}")
        if self.max_history_days is not None and self.max_history_days <= self.past_days:
            raise ValueError("max_history_days must exceed past_days (B5 only stretches back)")
        if self.record_reference not in (ALL, ESTABLISHED):
            raise ValueError(f"record_reference must be {ALL!r} or {ESTABLISHED!r}")
        if self.reference_scope not in (ROUTE, GATEWAY):
            raise ValueError(f"reference_scope must be {ROUTE!r} or {GATEWAY!r}")
        check_day_start(self.day_start_hour)
        zone(self.route_zone)  # ValueError for an unknown zone

    @property
    def surge_on(self) -> bool:
        """CAL-6 is on only when both of its fields are set."""
        return self.surge_min is not None and self.surge_factor is not None

    @classmethod
    def from_config(cls, config: BehaviourConfig) -> CalibrationSettings:
        """The settings of a (v5) behaviour config: its window is ``history_days`` (90, so
        89 past days), and the tune switches, B5 and DEP-7 fields are taken as they are."""
        return cls(
            past_days=config.history_days - 1,
            route_zone=config.route_zone,
            day_start_hour=config.day_start_hour,
            record_rank=config.record_rank,
            surge_min=config.surge_min,
            surge_factor=config.surge_factor,
            route_warmup_days=config.route_warmup_days,
            record_hold_days=config.record_hold_days,
            leave_top_identity_out=config.leave_top_identity_out,
            record_reference=config.record_reference,
            reference_scope=config.reference_scope,
            max_history_days=config.max_history_days,
            min_active_days=config.established_days or MIN_ACTIVE_DAYS,
            max_values=config.max_values_per_kind,
        )


# ── what a call brings ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CallMeasures:
    """One scored call, as calibration sees it. Each dimension appears in at most one of
    ``amounts``, ``values``, ``flags`` and ``org_flags``.

    - ``amounts``: raw amounts (calls, writes and assets in the hour, repeats, minutes, bytes).
    - ``values``: the values the call used (the strangest of them prices the call).
    - ``flags``: raised personal flags (Burst, Sweep, Unsafe sequence) -> key: None, or the
      (source, target) pair for Unsafe sequence (SEQ-1).
    - ``org_flags``: raised flags priced against the organisation -> strength (rho).
    - ``strengths``: a record's strength per dimension (amount: v4's excess score; value: see
      :func:`value_strength`; flag: rho). A record without one keeps its personal price.
    - ``took_part``: further dimensions evaluated but not raised (flags), for A_d and N_d.
    - ``established``: spec 2.7's predicate for the caller now (EST).
    - ``habit``: whether a raised flag counts as a habit day (RF11 passes False before the
      caller is established).
    """

    amounts: Mapping[str, float] = field(default_factory=dict)
    values: Mapping[str, tuple[Hashable, ...]] = field(default_factory=dict)
    flags: Mapping[str, Hashable] = field(default_factory=dict)
    org_flags: Mapping[str, float] = field(default_factory=dict)
    strengths: Mapping[str, float] = field(default_factory=dict)
    took_part: frozenset[str] = frozenset()
    established: bool = False
    habit: bool = True

    def __post_init__(self) -> None:
        kinds = (self.amounts, self.values, self.flags, self.org_flags)
        seen: set[str] = set()
        for kind in kinds:
            twice = seen & set(kind)
            if twice:
                raise ValueError(f"a dimension has one kind per call: {sorted(twice)}")
            seen |= set(kind)
        for dim, amount in self.amounts.items():
            _check_finite(f"amount of {dim}", amount)
        for dim, used in self.values.items():
            if not isinstance(used, tuple) or not used:
                raise ValueError(f"values of {dim} must be a non-empty tuple, not {used!r}")
        for name, mapping in (("org_flags", self.org_flags), ("strengths", self.strengths)):
            for dim, strength in mapping.items():
                _check_finite(f"{name}[{dim}]", strength)

    def dimensions(self) -> frozenset[str]:
        """Every dimension that took part in this call."""
        return (
            frozenset(self.took_part)
            | set(self.amounts)
            | set(self.values)
            | set(self.flags)
            | set(self.org_flags)
        )


@dataclass(frozen=True)
class Commonness:
    """CAL-1 for one dimension: ``earlier`` = D_d, ``days`` = A_d, q = (1 + D_d) / (A_d + 1)."""

    earlier: int
    days: int

    @property
    def q(self) -> float:
        """The commonness q_d = (1 + D_d) / (A_d + 1)."""
        return (1 + self.earlier) / (self.days + 1)

    @property
    def record(self) -> bool:
        """Stranger than every counted day (D_d = 0): a record."""
        return self.earlier == 0


@dataclass(frozen=True)
class Priced:
    """What :meth:`RouteClock.price` gives one call: q_d per dimension, the dimensions at a
    record, the strengths to file at commit (records with a strength, raised org-priced
    flags), the dimensions the surge guard raised, each personal :class:`Commonness`, and the
    route day of the reference version that priced it (``reference_day``, CAL-7)."""

    rates: Mapping[str, float]
    records: tuple[str, ...] = ()
    ranked: Mapping[str, float] = field(default_factory=dict)
    surged: tuple[str, ...] = ()
    commonness: Mapping[str, Commonness] = field(default_factory=dict)
    reference_day: int | None = None


@dataclass
class AgentDay:
    """One caller's running maxima for one local day: the open-day buffer's unit, and what a
    closed day keeps. Merging is idempotent (max and union), so a day folded twice is fine."""

    took: set[str] = field(default_factory=set)
    amounts: dict[str, float] = field(default_factory=dict)
    values: dict[str, set[Hashable]] = field(default_factory=dict)
    flags: dict[str, set[Hashable]] = field(default_factory=dict)  # habit keys raised
    ranked: dict[str, float] = field(default_factory=dict)  # strongest ranked strength
    records: set[str] = field(default_factory=set)  # dimensions it set a personal record on
    established: bool = False

    def add(self, measures: CallMeasures, priced: Priced, max_values: int | None = None) -> None:
        """Fold one committed call in: each caller adds one record-day per dimension per
        day, its strongest. Past ``max_values`` distinct values (or flag keys) of one dimension
        in the day, further ones are kept as :data:`OVERFLOW` (DEP-7)."""
        self.took |= measures.dimensions() | set(priced.ranked)
        for dim, amount in measures.amounts.items():
            self.amounts[dim] = max(self.amounts.get(dim, amount), amount)
        for dim, used in measures.values.items():
            _add_capped(self.values.setdefault(dim, set()), used, max_values)
        if measures.habit:
            for dim, key in measures.flags.items():
                _add_capped(self.flags.setdefault(dim, set()), (key,), max_values)
        for dim, strength in priced.ranked.items():
            self.ranked[dim] = max(self.ranked.get(dim, strength), strength)
        self.records |= set(priced.records)
        self.established = self.established or measures.established

    def merge(self, other: AgentDay, max_values: int | None = None) -> None:
        """Fold ``other`` (the same caller-day) into this one."""
        self.took |= other.took
        for dim, amount in other.amounts.items():
            self.amounts[dim] = max(self.amounts.get(dim, amount), amount)
        for dim, used in other.values.items():
            _add_capped(self.values.setdefault(dim, set()), used, max_values)
        for dim, keys in other.flags.items():
            _add_capped(self.flags.setdefault(dim, set()), keys, max_values)
        for dim, strength in other.ranked.items():
            self.ranked[dim] = max(self.ranked.get(dim, strength), strength)
        self.records |= other.records
        self.established = self.established or other.established

    def copy(self) -> AgentDay:
        """An independent copy."""
        out = AgentDay()
        out.merge(self)
        return out

    def to_json(self) -> dict:
        """The day as JSON (sets sorted, so equal days give equal JSON)."""
        return {
            "took": sorted(self.took),
            "amounts": dict(sorted(self.amounts.items())),
            "values": {d: _encode_set(v) for d, v in sorted(self.values.items())},
            "flags": {d: _encode_set(v) for d, v in sorted(self.flags.items())},
            "ranked": dict(sorted(self.ranked.items())),
            "records": sorted(self.records),
            "established": self.established,
        }

    @classmethod
    def from_json(cls, data: dict) -> AgentDay:
        """A day from :meth:`to_json`."""
        return cls(
            took=set(data["took"]),
            amounts={d: float(x) for d, x in data["amounts"].items()},
            values={d: {_decode(v) for v in vs} for d, vs in data["values"].items()},
            flags={d: {_decode(v) for v in vs} for d, vs in data["flags"].items()},
            ranked={d: float(x) for d, x in data["ranked"].items()},
            records=set(data["records"]),
            established=bool(data["established"]),
        )


# ── CAL-1: DayRings ─────────────────────────────────────────────────────────────────────────
_AMOUNT, _VALUE, _FLAG = "amount", "value", "flag"


class _KeyDays:
    """On which closed days each key of one dimension (a value, or a flag key) was used: a bit
    mask over days per key, least recently used first. Past ``cap`` keys the least recently
    used one folds into the overflow (DEP-7): it is forgotten, so it is priced as new if it
    comes back, and for values the days it was used on count as days with a value priced as
    new (:attr:`overflow`)."""

    __slots__ = ("masks", "overflow")

    def __init__(self) -> None:
        self.masks: OrderedDict[Hashable, int] = OrderedDict()
        self.overflow = 0

    def add(self, keys: Iterable[Hashable], bit: int, recent: bool, cap: int | None) -> None:
        """Mark ``keys`` used on the day of ``bit``. ``recent`` (the caller's newest day) moves
        them to the most recently used end."""
        for key in sorted(keys, key=repr):  # one order in every process
            if key == OVERFLOW:
                self.overflow |= bit
                continue
            mask = self.masks.get(key)
            if mask is not None:
                self.masks[key] = mask | bit
                if recent:
                    self.masks.move_to_end(key)
                continue
            if cap is not None and len(self.masks) >= cap:
                self.overflow |= self.masks.popitem(last=False)[1]
            self.masks[key] = bit

    def forget_before(self, low: int) -> None:
        """Drop least recently used keys with no day at bit ``low`` or later."""
        while self.masks:
            key, mask = next(iter(self.masks.items()))
            if mask >> low:
                return
            del self.masks[key]

    def shift(self, by: int) -> None:
        """Rebase every mask ``by`` days on; a key left with no day is forgotten."""
        for key in list(self.masks):
            mask = self.masks[key] >> by
            if mask:
                self.masks[key] = mask
            else:
                del self.masks[key]
        self.overflow >>= by


class DayRings:
    """One caller's closed days (CAL-1): per dimension the day maxima of amounts, and on which
    days each value was used (value-days) and each flag key raised, over the window J = his
    active days in [start(t), t-1]. J_d keeps the days on which d took part.

    - *Amounts*: D_d = #{j in J_d : day maximum of j >= this amount} (a tie counts).
    - *Values*: a value's count n_v is the days of J_d it was used on. Day j's strangeness is
      the smallest count among its values, with j itself left out (n_v - 1); D_d counts the
      days at most as common as this call's value, i.e. the days holding a value with
      n_v <= used + 1. A value never used is the strangest possible (count 0), so novelty is
      monotone (N7). Today's own calls never count (conservative: they would only raise the
      past days' counts).
    - *Flags*: D_d = the days of J_d with the flag raised under the same key (the habit
      discount; for Unsafe sequence the same (source, target) pair).

    The window is [t-89, t-1]; with ``max_history_days`` (B5) it stretches back until it holds
    ``min_active_days`` active days. ``record_hold_days`` (HOLD) keeps the caller's own
    record-days of the last ``record_hold_days`` days out of D_d (not out of A_d).

    Cost guards (DEP-7): per dimension at most ``max_values`` distinct values (or flag keys)
    are kept, the most recently used; the rest fold into one overflow value priced as new.
    Days are bit masks per key, so a value query costs one popcount per kept value at the
    first query of the caller's day and a bisect after; memory is bounded by the kept keys.

    Validity: every query is frozen. It reads only closed days, which change when the caller's
    previous day closes (:meth:`close_day`), never during its current day.
    """

    def __init__(
        self,
        past_days: int = PAST_DAYS,
        *,
        max_history_days: int | None = None,
        min_active_days: int = MIN_ACTIVE_DAYS,
        record_hold_days: int | None = None,
        max_values: int | None = None,
    ) -> None:
        _check_positive_int("past_days", past_days)
        self.past_days = past_days
        self.max_past = None if max_history_days is None else max_history_days - 1
        if self.max_past is not None and self.max_past < past_days:
            raise ValueError("max_history_days must exceed past_days")
        self.min_active_days = min_active_days
        self.record_hold_days = record_hold_days
        self.max_values = max_values
        self.days: dict[int, AgentDay] = {}  # closed days: took part, amounts, records
        self._keys: dict[tuple[str, str], _KeyDays] = {}  # (kind, dim) -> its keys' days
        self._base: int | None = None  # bit i of a day mask is day _base + i
        self._view_key: tuple[int, int | None] | None = None  # (today, start) of the cache
        self._window: tuple[int, ...] = ()
        self._views: dict[tuple[str, str], tuple] = {}

    @classmethod
    def for_settings(cls, settings: CalibrationSettings) -> DayRings:
        """Empty rings with the settings' window, B5, HOLD and DEP-7 fields."""
        return cls(
            settings.past_days,
            max_history_days=settings.max_history_days,
            min_active_days=settings.min_active_days,
            record_hold_days=settings.record_hold_days,
            max_values=settings.max_values,
        )

    @property
    def span(self) -> int:
        """The past days any window can reach: ``past_days``, or B5's longest stretch."""
        return self.past_days if self.max_past is None else self.max_past

    def close_day(self, day: int, agent_day: AgentDay) -> None:
        """Add a closed local day (merged into one already there) and forget what no later
        window can reach: days, and keys used on no day left. A day older than every
        reachable window is ignored."""
        latest = max(self.days, default=day)
        if day < latest + 1 - self.span:
            return
        if self._base is None:
            self._base = day - self.span
        kept = self.days.setdefault(day, AgentDay())
        kept.took |= agent_day.took
        for dim, amount in agent_day.amounts.items():
            kept.amounts[dim] = max(kept.amounts.get(dim, amount), amount)
        kept.records |= agent_day.records
        kept.established = kept.established or agent_day.established
        bit, recent = 1 << (day - self._base), day >= latest
        for kind, used in ((_VALUE, agent_day.values), (_FLAG, agent_day.flags)):
            for dim, keys in used.items():
                self._keys.setdefault((kind, dim), _KeyDays()).add(
                    keys, bit, recent, self.max_values
                )
        self._forget(max(latest, day))
        self._view_key = None

    def stored_keys(self) -> int:
        """Keys kept over all dimensions (DEP-7's memory bound: at most ``max_values`` each)."""
        return sum(len(keys.masks) for keys in self._keys.values())

    def window_start(self, today: int) -> int:
        """start(today) (B5): max(t - 364, min(t - 89, d_k(t))) with d_k his k-th most recent
        active day, or t - 89 without B5. Validity: frozen."""
        start = today - self.past_days
        if self.max_past is None:
            return start
        active = sorted(d for d, ad in self.days.items() if d < today and ad.took)
        kth = active[-self.min_active_days] if len(active) >= self.min_active_days else None
        floor = today - self.max_past
        return floor if kth is None else max(floor, min(start, kth))

    def window(self, today: int, start: int | None = None) -> tuple[int, ...]:
        """J: his active closed days in [start, today - 1], oldest first. ``start`` defaults
        to :meth:`window_start` (the engine may pass memory's B5 start instead).
        Validity: frozen."""
        if self._view_key != (today, start):
            lo = self.window_start(today) if start is None else start
            self._window = tuple(
                sorted(d for d, ad in self.days.items() if lo <= d < today and ad.took)
            )
            self._view_key, self._views = (today, start), {}
        return self._window

    def active_days(self, today: int, dim: str | None = None, start: int | None = None) -> int:
        """A (or A_d: only days on which ``dim`` took part). Validity: frozen."""
        days = self.window(today, start)
        if dim is None:
            return len(days)
        return sum(1 for d in days if dim in self.days[d].took)

    def amount(self, dim: str, amount: float, today: int, start: int | None = None) -> Commonness:
        """Commonness of an amount: past days whose maximum was at least ``amount``.
        Validity: frozen."""
        _check_finite(f"amount of {dim}", amount)
        days, maxima = self._view(_AMOUNT, dim, today, start)
        return Commonness(len(maxima) - bisect_left(maxima, amount), days)

    def value(
        self, dim: str, values: tuple[Hashable, ...], today: int, start: int | None = None
    ) -> Commonness:
        """Commonness of the strangest of ``values``: past days whose strangest value was used
        on at most as many days. Validity: frozen."""
        days, (took, keys, levels, at_most) = self._view(_VALUE, dim, today, start)
        used = min(0 if keys is None else (keys.masks.get(v, 0) & took).bit_count() for v in values)
        return Commonness(at_most[bisect_right(levels, used + 1)], days)

    def flag(self, dim: str, key: Hashable, today: int, start: int | None = None) -> Commonness:
        """Commonness of a raised flag: past days with it raised under ``key``. A key never
        raised in the window (or folded into the overflow) is a record. Validity: frozen."""
        days, (counted, keys) = self._view(_FLAG, dim, today, start)
        mask = 0 if keys is None else keys.masks.get(key, 0)
        return Commonness((mask & counted).bit_count(), days)

    def _view(self, kind: str, dim: str, today: int, start: int | None) -> tuple[int, object]:
        """(A_d, the reference of ``kind``) for ``today``, built once per caller-day."""
        window = self.window(today, start)  # resets the cache on a new (today, start)
        cached = self._views.get((kind, dim))
        if cached is not None:
            return cached
        took = [d for d in window if dim in self.days[d].took]
        hold = self.record_hold_days
        counted = [
            d
            for d in took
            if hold is None or not (dim in self.days[d].records and d >= today - hold)
        ]
        if kind == _AMOUNT:
            ref: object = sorted(
                self.days[d].amounts[dim] for d in counted if dim in self.days[d].amounts
            )
        elif kind == _VALUE:
            ref = _value_levels(self._keys.get((kind, dim)), self._mask(took), self._mask(counted))
        else:
            ref = (self._mask(counted), self._keys.get((kind, dim)))
        self._views[(kind, dim)] = (len(took), ref)
        return self._views[(kind, dim)]

    def _mask(self, days: Iterable[int]) -> int:
        """The bit mask of ``days`` (closed days, so the base is set)."""
        mask = 0
        for day in days:
            mask |= 1 << (day - self._base)
        return mask

    def _forget(self, latest: int) -> None:
        """Drop days and keys before every window that ``latest`` allows, and rebase the masks
        once they carry a span of dead days (so a mask holds at most two spans of bits)."""
        low = latest + 1 - self.span
        for old in [d for d in self.days if d < low]:
            del self.days[old]
        offset = low - self._base
        for keys in self._keys.values():
            keys.forget_before(offset)
        if offset >= self.span:
            for keys in self._keys.values():
                keys.shift(offset)
            self._base = low
        for kind_dim in [
            k for k, keys in self._keys.items() if not keys.masks and not keys.overflow
        ]:
            del self._keys[kind_dim]

    def to_json(self) -> dict:
        """The rings' state: closed days, and each key's days in least recently used order."""
        base = self._base
        return {
            "base": base,
            "days": {str(d): ad.to_json() for d, ad in sorted(self.days.items())},
            "keys": [
                [
                    kind,
                    dim,
                    [[_encode(key), _mask_days(mask, base)] for key, mask in keys.masks.items()],
                    _mask_days(keys.overflow, base),
                ]
                for (kind, dim), keys in sorted(self._keys.items())
            ],
        }

    @classmethod
    def from_json(cls, data: dict, settings: CalibrationSettings) -> DayRings:
        """Rings from :meth:`to_json`, with the settings' window and caps."""
        rings = cls.for_settings(settings)
        rings._base = data["base"]
        rings.days = {int(d): AgentDay.from_json(ad) for d, ad in data["days"].items()}
        for kind, dim, masks, overflow in data["keys"]:
            keys = rings._keys[(kind, dim)] = _KeyDays()
            for key, days in masks:
                keys.masks[_decode(key)] = _days_mask(days, rings._base)
            keys.overflow = _days_mask(overflow, rings._base)
        return rings


def _value_levels(keys: _KeyDays | None, took: int, counted: int) -> tuple:
    """A value view: (J_d's mask, the keys, the distinct counts n_v >= 1 in increasing order,
    and D for each prefix of them). ``at_most[i]`` counts the counted days that hold an
    overflowed value or a value whose count is among the first ``i`` levels."""
    if keys is None:
        return took, None, [], [0]
    by_level: dict[int, int] = {}
    for mask in keys.masks.values():
        used = (mask & took).bit_count()
        if used:
            by_level[used] = by_level.get(used, 0) | mask
    levels = sorted(by_level)
    union = keys.overflow
    at_most = [(union & counted).bit_count()]
    for level in levels:
        union |= by_level[level]
        at_most.append((union & counted).bit_count())
    return took, keys, levels, at_most


def value_strength(callers_using: int) -> float:
    """A value record's strength: how few of the route's callers used the value in the window
    (spec 2.3). A value new to the organisation (0 callers) is the strongest, 1."""
    if callers_using < 0:
        raise ValueError(f"callers_using must be at least 0, not {callers_using!r}")
    return 1.0 / (1.0 + callers_using)


# ── CAL-2: the record reference ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ReferenceEntry:
    """One agent-day in the route reference: its caller (``identity``), whether the caller was
    established, the dimensions that took part, and its strongest ranked strength per
    dimension."""

    identity: str
    established: bool
    took: frozenset[str]
    ranked: Mapping[str, float]

    def __post_init__(self) -> None:
        if not set(self.ranked) <= self.took:
            raise ValueError(f"ranked dimensions must have taken part: {sorted(self.ranked)}")

    def to_json(self) -> list:
        """The entry as a JSON list."""
        return [
            self.identity,
            self.established,
            sorted(self.took),
            dict(sorted(self.ranked.items())),
        ]

    @classmethod
    def from_json(cls, data: list) -> ReferenceEntry:
        """An entry from :meth:`to_json`."""
        identity, established, took, ranked = data
        return cls(
            identity, bool(established), frozenset(took), {d: float(s) for d, s in ranked.items()}
        )


class ReferenceVersion:
    """One frozen build of a route reference (CAL-2, CAL-7): per dimension, N_d and the sorted
    ranked strengths of the agent-days ready by rollover ``day`` and filed in
    [day - past_days, day - 1]. Nothing changes a version after its build::

        rank(d, s) = (1 + #{ranked days on d with strength >= s}) / (N_d + 1)
    """

    def __init__(
        self,
        day: int | None,
        past_days: int,
        ranked: dict[str, list[float]],
        n: dict[str, int],
        left_out: Mapping[str, str] | None = None,
    ) -> None:
        self.day = day
        self.past_days = past_days
        self._sorted = ranked
        self._n = n
        self.left_out = dict(left_out or {})  # TOP: dimension -> the identity left out
        self._digests: dict[str, str] | None = None

    def rank(self, dim: str, strength: float) -> float:
        """r_d: the add-one rank of ``strength`` among the ranked days, over N_d + 1."""
        _check_finite(f"strength of {dim}", strength)
        return (1 + self.count_at_least(dim, strength)) / (self.n(dim) + 1)

    def count_at_least(self, dim: str, strength: float) -> int:
        """Ranked days on ``dim`` with strength >= ``strength``."""
        ranked = self._sorted.get(dim, [])
        return len(ranked) - bisect_left(ranked, strength)

    def n(self, dim: str) -> int:
        """N_d: the window's agent-days on which ``dim`` took part."""
        return self._n.get(dim, 0)

    def ranked_days(self, dim: str) -> int:
        """R_d: the window's ranked days on ``dim``."""
        return len(self._sorted.get(dim, []))

    def daily_mean(self, dim: str) -> float:
        """The window's daily mean of ranked days (R_d over the window's length, as the O3
        probe counts it)."""
        return self.ranked_days(dim) / self.past_days

    def path_activity(self, shares: Mapping[str, float | None], alpha: float) -> dict[str, bool]:
        """Per alerting dimension, whether its path can reach line ``alpha``:
        N_d + 1 >= 1 / (w_d alpha) (RF5 reports the inactive ones)."""
        return {
            dim: path_active(self.n(dim), share, alpha)
            for dim, share in shares.items()
            if share is not None and share > 0
        }

    def digests(self) -> dict[str, str]:
        """One digest per dimension of the frozen arrays (the ``behaviour_fold`` line)."""
        if self._digests is None:
            self._digests = {
                dim: _digest_floats([self.day, self._n[dim]], self._sorted.get(dim, []))
                for dim in sorted(self._n)
            }
        return dict(self._digests)


@dataclass(frozen=True)
class _BucketSummary:
    """One bucket's part of a version: N per dimension and the sorted ranked strengths; for
    TOP also each identity's ranked strengths per dimension (``ranked_by``) and the dimensions
    each of its agent-days took part on (``took_of``)."""

    n: dict[str, int]
    ranked: dict[str, list[float]]
    ranked_by: dict[str, dict[str, list[float]]]
    took_of: dict[str, list[frozenset[str]]]


class RecordReference:
    """The route's ranked agent-days per dimension (CAL-2) and their frozen versions (CAL-7).

    For a personal dimension the ranked days are record-days; for Oversized request and Missing
    handshake they are the raised agent-days. N_d counts the agent-days on which d took part.

    An agent-day is filed once, in the bucket (filing day, ready day): the ready day is the
    first rollover at or after the end of its local day, and the filing day min(local day,
    ready - 1). The version of rollover t holds the agent-days ready by t and filed in
    [t - 89, t - 1], so it depends only on which agent-days had ended, never on when the clock
    swept them. :meth:`rebuild` merges each dimension's sorted runs, one per bucket, summarised
    once when the bucket fills, so a rollover costs one sort of already sorted runs, not a pass
    over every agent-day in Python. An agent-day reaches the reference once: a call that
    arrives after its day was filed (out of order) still reaches the caller's rings, not the
    reference.

    EST keeps only agent-days whose caller was established; TOP leaves out, per dimension, the
    caller with the most ranked days in the window (ties: the smallest key), both from the
    ranked days and from N_d. One reference may be shared by several routes (GWR, see
    :class:`GatewayReference`). The query methods read the current version.
    """

    def __init__(
        self,
        past_days: int = PAST_DAYS,
        *,
        leave_top_identity_out: bool = False,
        established_only: bool = False,
    ) -> None:
        _check_positive_int("past_days", past_days)
        self.past_days = past_days
        self.leave_top_identity_out = leave_top_identity_out
        self.established_only = established_only
        #: (filing day, ready day) -> agent key -> entry
        self.buckets: dict[tuple[int, int], dict[str, ReferenceEntry]] = {}
        self._filed: dict[str, tuple[int, int]] = {}  # agent key -> its bucket
        self._summaries: dict[tuple[int, int], _BucketSummary] = {}
        self.versions: dict[int, ReferenceVersion] = {}  # the last KEPT_VERSIONS builds
        self.current = ReferenceVersion(None, past_days, {}, {})

    @classmethod
    def for_settings(cls, settings: CalibrationSettings) -> RecordReference:
        """An empty reference with the settings' window, TOP and EST."""
        return cls(
            settings.past_days,
            leave_top_identity_out=settings.leave_top_identity_out,
            established_only=settings.record_reference == ESTABLISHED,
        )

    @property
    def today(self) -> int | None:
        """The rollover day of the current version (None before the first build)."""
        return self.current.day

    @property
    def left_out(self) -> dict[str, str]:
        """TOP: per dimension, the identity the current version leaves out."""
        return dict(self.current.left_out)

    def add(self, day: int, key: str, entry: ReferenceEntry, ready: int | None = None) -> bool:
        """File one agent-day under filing day ``day``, ready from rollover ``ready`` (default
        ``day + 1``). It counts from the next :meth:`rebuild` at or after ``ready``. False when
        ``key`` was filed already, or ``day`` is older than every kept version can reach."""
        ready = day + 1 if ready is None else ready
        if ready <= day:
            raise ValueError(f"an agent-day is ready only after its filing day: {day}, {ready}")
        if key in self._filed:
            return False
        if self.current.day is not None and day < self._keep_from(self.current.day):
            return False
        bucket = (day, ready)
        self.buckets.setdefault(bucket, {})[key] = entry
        self._filed[key] = bucket
        self._summaries.pop(bucket, None)
        return True

    def rebuild(self, today: int) -> ReferenceVersion:
        """Freeze the version of rollover ``today`` and make it current. Versions of the last
        :data:`KEPT_VERSIONS` days that a clock which skipped idle days never built are built
        too, as a clock that ticked daily would have (rebuilding ``today`` again refreshes
        it). Buckets that no kept version can reach are forgotten."""
        previous = self.current.day
        if previous is not None and today < previous:
            raise ValueError(f"the reference never goes back: {today} < {previous}")
        first = today - KEPT_VERSIONS + 1
        if previous is not None:
            first = max(first, min(previous + 1, today))
        for day in range(first, today + 1):
            self.versions[day] = self._build(day)
        for old in [d for d in self.versions if d <= today - KEPT_VERSIONS]:
            del self.versions[old]
        self.current = self.versions[today]
        line = self._keep_from(today)
        for bucket in [b for b in self.buckets if b[0] < line]:
            for key in self.buckets.pop(bucket):
                self._filed.pop(key, None)
            self._summaries.pop(bucket, None)
        return self.current

    def version(self, day: int | None) -> ReferenceVersion:
        """The version current when route day ``day`` began: the newest kept one built at or
        before it (the oldest kept when ``day`` is older still; the current one when none is
        kept). Validity: frozen."""
        if day is None or not self.versions:
            return self.current
        built = [d for d in self.versions if d <= day]
        return self.versions[max(built) if built else min(self.versions)]

    def rank(self, dim: str, strength: float) -> float:
        """r_d in the current version. Validity: frozen."""
        return self.current.rank(dim, strength)

    def count_at_least(self, dim: str, strength: float) -> int:
        """Ranked days on ``dim`` with strength >= ``strength`` (current version)."""
        return self.current.count_at_least(dim, strength)

    def n(self, dim: str) -> int:
        """N_d of the current version. Validity: frozen."""
        return self.current.n(dim)

    def ranked_days(self, dim: str) -> int:
        """R_d of the current version. Validity: frozen."""
        return self.current.ranked_days(dim)

    def daily_mean(self, dim: str) -> float:
        """R_d over the window's length, current version. Validity: frozen."""
        return self.current.daily_mean(dim)

    def path_activity(self, shares: Mapping[str, float | None], alpha: float) -> dict[str, bool]:
        """:meth:`ReferenceVersion.path_activity` of the current version. Validity: frozen."""
        return self.current.path_activity(shares, alpha)

    def digests(self) -> dict[str, str]:
        """The current version's digests (the ``behaviour_fold`` line). Validity: frozen."""
        return self.current.digests()

    def to_json(self) -> dict:
        """The filed agent-days and which versions are kept (versions are rebuilt on load:
        filed agent-days never change, so a load rebuilds the same arrays)."""
        return {
            "versions": sorted(self.versions),
            "buckets": [
                [day, ready, {k: e.to_json() for k, e in sorted(filed.items())}]
                for (day, ready), filed in sorted(self.buckets.items())
            ],
        }

    @classmethod
    def from_json(cls, data: dict, settings: CalibrationSettings) -> RecordReference:
        """A reference from :meth:`to_json`, with the settings' window, TOP and EST."""
        ref = cls.for_settings(settings)
        for day, ready, filed in data["buckets"]:
            for key, entry in filed.items():
                ref.add(day, key, ReferenceEntry.from_json(entry), ready)
        for day in data["versions"]:
            ref.versions[day] = ref._build(day)
        if ref.versions:
            ref.current = ref.versions[max(ref.versions)]
        return ref

    def _keep_from(self, today: int) -> int:
        """The oldest filing day a kept version of rollover ``today`` can reach."""
        return today - self.past_days - KEPT_VERSIONS + 1

    def _build(self, day: int) -> ReferenceVersion:
        """The version of rollover ``day`` from the buckets' summaries."""
        lo = day - self.past_days
        parts = [
            self._summary(bucket)
            for bucket in self.buckets
            if bucket[1] <= day and lo <= bucket[0] < day
        ]
        n: Counter = Counter()
        for part in parts:
            n.update(part.n)
        ranked: dict[str, list[float]] = {}
        left_out: dict[str, str] = {}
        for dim in sorted(n):
            values = sorted(chain.from_iterable(p.ranked[dim] for p in parts if dim in p.ranked))
            if self.leave_top_identity_out and values:
                top, took, strengths = _top_identity(parts, dim)
                left_out[dim] = top
                n[dim] -= took
                for strength in strengths:
                    del values[bisect_left(values, strength)]
            ranked[dim] = values
        return ReferenceVersion(day, self.past_days, ranked, dict(n), left_out)

    def _summary(self, bucket: tuple[int, int]) -> _BucketSummary:
        """A bucket's summary, built once (a new agent-day in the bucket rebuilds it)."""
        summary = self._summaries.get(bucket)
        if summary is None:
            summary = self._summaries[bucket] = self._summarise(self.buckets[bucket].values())
        return summary

    def _summarise(self, entries: Iterable[ReferenceEntry]) -> _BucketSummary:
        """N, sorted strengths and (TOP) per-identity strengths of some agent-days."""
        n: Counter = Counter()
        ranked: dict[str, list[float]] = {}
        ranked_by: dict[str, dict[str, list[float]]] = {}
        took_of: dict[str, list[frozenset[str]]] = {}
        top = self.leave_top_identity_out
        for entry in entries:
            if self.established_only and not entry.established:
                continue
            n.update(entry.took)
            for dim, strength in entry.ranked.items():
                ranked.setdefault(dim, []).append(strength)
                if top:
                    ranked_by.setdefault(dim, {}).setdefault(entry.identity, []).append(strength)
            if top:
                took_of.setdefault(entry.identity, []).append(entry.took)
        for values in ranked.values():
            values.sort()
        return _BucketSummary(dict(n), ranked, ranked_by, took_of)


def _top_identity(parts: list[_BucketSummary], dim: str) -> tuple[str, int, list[float]]:
    """TOP: the identity with the most ranked days on ``dim`` (ties: the smallest key), its
    agent-days on ``dim`` and its ranked strengths."""
    strengths: dict[str, list[float]] = {}
    for part in parts:
        for identity, values in part.ranked_by.get(dim, {}).items():
            strengths.setdefault(identity, []).extend(values)
    top = min(strengths, key=lambda identity: (-len(strengths[identity]), identity))
    took = sum(1 for part in parts for days in part.took_of.get(top, ()) if dim in days)
    return top, took, strengths[top]


def record_price(active_days: int, rank: float) -> float:
    """q_d on a record: min(1 / (A_d + 1), r_d). Under the cap condition the personal part
    never reaches a stated line, so only the rank can alert."""
    if active_days < 0:
        raise ValueError(f"active_days must be at least 0, not {active_days!r}")
    return min(1.0 / (active_days + 1), rank)


def cap_condition(share: float, alpha: float, past_days: int = PAST_DAYS) -> bool:
    """True when the personal part 1/(A_d + 1), A_d <= ``past_days``, cannot reach line
    ``alpha`` for a dimension of budget share ``share``: (past_days + 1) w alpha < 1. With 89
    past days it fails only at alpha >= 1 / (90 w): 13.3% for w = 1/12."""
    return (past_days + 1) * share * alpha < 1 - CAP_TOLERANCE


def path_active(n_days: int, share: float, alpha: float) -> bool:
    """Path activity: a rank over N_d + 1 can reach line ``alpha`` at share ``share`` only if
    N_d + 1 >= 1 / (w alpha) (1,800 agent-days at w = 1/18 and 1%; 2,100 at 1/21)."""
    return (n_days + 1) * share * alpha >= 1 - CAP_TOLERANCE


# ── CAL-6: the surge guard ──────────────────────────────────────────────────────────────────
class SurgeGuard:
    """On a route day when the ranked agent-days on d from distinct callers reach
    max(surge_min, surge_factor x the window's daily mean), a call's q_d also gets the rank of
    its strength among today's ranked agent-days so far, over today's agent-days on d plus
    one, and keeps the larger of the two. The current call's agent-day counts as one of today's
    (a ranked one), so offline, with the whole day noted, this is the O3 probe's rule.

    Validity: open. It reads today's running counts (and the frozen window mean); taking the
    larger of two valid ranks only raises q, so it keeps the bound.
    """

    def __init__(
        self,
        surge_min: int | None = SURGE_MIN,
        surge_factor: float | None = SURGE_FACTOR,
    ) -> None:
        self.surge_min, self.surge_factor = surge_min, surge_factor
        self.took: dict[str, set[str]] = {}  # dimension -> today's callers on it
        self.ranked: dict[str, dict[str, float]] = {}  # dimension -> caller -> strongest today
        self.noticed: set[str] = set()  # dimensions whose flag_surge was logged today

    @property
    def on(self) -> bool:
        """CAL-6 is on only when both of its fields are set."""
        return self.surge_min is not None and self.surge_factor is not None

    def reset(self) -> None:
        """A new route day: forget today's counts."""
        self.took, self.ranked, self.noticed = {}, {}, set()

    def note(self, caller: str, took: Iterable[str], ranked: Mapping[str, float]) -> None:
        """Count one committed call: the dimensions it took part on and its ranked strengths."""
        for dim in took:
            self.took.setdefault(dim, set()).add(caller)
        for dim, strength in ranked.items():
            self.took.setdefault(dim, set()).add(caller)
            today = self.ranked.setdefault(dim, {})
            today[caller] = max(today.get(caller, strength), strength)

    def threshold(self, dim: str, reference: RecordReference | ReferenceVersion) -> float:
        """Today's ranked agent-days needed for a surge on ``dim``. Validity: frozen (the
        window mean of the last fold)."""
        if not self.on:
            return math.inf
        return max(self.surge_min, self.surge_factor * reference.daily_mean(dim))

    def surging(
        self, dim: str, reference: RecordReference | ReferenceVersion, caller: str | None = None
    ) -> bool:
        """Whether ``dim`` is in a surge, counting ``caller``'s agent-day as ranked.
        Validity: open (today's counts so far)."""
        today = self.ranked.get(dim, {})
        count = len(today) + (caller is not None and caller not in today)
        return count >= self.threshold(dim, reference)

    def price(
        self,
        dim: str,
        caller: str,
        strength: float,
        q: float,
        reference: RecordReference | ReferenceVersion,
    ) -> tuple[float, bool]:
        """(q_d after the guard, whether the dimension is surging). Never below ``q``.
        Validity: open (today's counts so far), and it only raises q."""
        if not self.surging(dim, reference, caller):
            return q, False
        today = self.ranked.get(dim, {})
        at_least = 1 + sum(1 for c, s in today.items() if c != caller and s >= strength)
        took = self.took.get(dim, set())
        agent_days = len(took) + (caller not in took)
        return max(q, at_least / (agent_days + 1)), True

    def notice(self, dim: str) -> bool:
        """True the first time per route day it is asked for ``dim`` (log one ``flag_surge``)."""
        if dim in self.noticed:
            return False
        self.noticed.add(dim)
        return True

    def to_json(self) -> dict:
        """Today's counts as JSON."""
        return {
            "took": {d: sorted(c) for d, c in sorted(self.took.items())},
            "ranked": {d: dict(sorted(c.items())) for d, c in sorted(self.ranked.items())},
            "noticed": sorted(self.noticed),
        }

    def load_json(self, data: dict) -> None:
        """Restore today's counts from :meth:`to_json`."""
        self.took = {d: set(c) for d, c in data["took"].items()}
        self.ranked = {d: {k: float(s) for k, s in c.items()} for d, c in data["ranked"].items()}
        self.noticed = set(data["noticed"])


# ── CAL-3: budget shares ────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Statistic:
    """CAL-3: q_stat = min_d v_d, d* its dimension, q2 and the runner-up; ``values`` = v_d."""

    q: float
    dimension: str | None
    q2: float
    runner_up: str | None
    values: Mapping[str, float]


def combine(
    rates: Mapping[str, float],
    shares: Mapping[str, float | None],
    *,
    watch_cap: float | None = WATCH_CAP,
    watch_share: float = WATCH_SHARE,
) -> Statistic:
    """Weighted minimum of commonness: v_d = q_d / w_d for an alerting dimension, and
    v_d = max(q_d / watch_share, watch_cap) for a watch-only one (share None or 0: Missing
    handshake, Footprint under D3 (b)), so it orders the list but stays above every stated
    line. Shares come from :func:`shares_for` and are never renormalised. Ties go to the
    dimension that comes first in ``shares`` (the design's order), whatever the order of
    ``rates``. A rate of inf (the dimension did not take part) never wins.
    Validity: pure (reads no state)."""
    position = {dim: i for i, dim in enumerate(shares)}
    values: dict[str, float] = {}
    for dim, q in rates.items():
        if dim not in shares:
            raise ValueError(f"no budget share for {dim!r}")
        if math.isnan(q) or q < 0:
            raise ValueError(f"rate of {dim} must be at least 0, not {q!r}")
        share = shares[dim]
        if share is None or share <= 0:
            cap = 0.0 if watch_cap is None else watch_cap
            values[dim] = max(q, cap * watch_share) / watch_share  # the O3 probe's arithmetic
        else:
            values[dim] = q / share
    order = sorted(values, key=lambda dim: (values[dim], position[dim]))
    q = values[order[0]] if order else math.inf
    q2 = values[order[1]] if len(order) > 1 else math.inf
    return Statistic(
        q,
        order[0] if math.isfinite(q) else None,
        q2,
        order[1] if math.isfinite(q2) else None,
        values,
    )


def shares_for(config: BehaviourConfig) -> dict[str, float | None]:
    """Every dimension the config scores -> its budget share w_d (``engine.budget_share``),
    None for a watch-only one, in the design's order."""
    # imported here: the engine imports this module at its top, so a top-level import of the
    # engine would be circular
    from mcp_security.behaviour.engine import READ_VOLUME, budget_share, dimension_groups

    if config.budget_shares is None:
        raise ValueError(f"design {config.design} with budget_shares=None has no shares")
    return {
        dim: budget_share(config, dim)
        for dims in dimension_groups(config.design).values()
        for dim in dims
        if dim != READ_VOLUME or config.reply_volume
    }


# ── CAL-4: floors ───────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Decision:
    """q = min(q_stat, q_floor). When a floor wins, ``dimension`` (d*) is the floor and
    ``q2`` = q_stat with ``runner_up`` the statistic's d*. ``floors`` lists every floor that
    fired; ``alert_floors`` those that acted at the alert level."""

    q: float
    dimension: str | None
    q2: float
    runner_up: str | None
    floors: tuple[str, ...] = ()
    alert_floors: tuple[str, ...] = ()


def apply_floors(
    stat: Statistic,
    *,
    alert: Iterable[str] = (),
    watch: Iterable[str] = (),
    alert_rate: float = ALERT_ALPHA,
    watch_rate: float = WATCH_FLOOR_RATE,
    route_warm: bool = True,
    demoted: Collection[str] = (),
) -> Decision:
    """The floors outside the statistic (CAL-4).

    ``alert``: alert floors that fired (first access to a sensitivity-5 asset not touched in 90
    days; the SEQ-2 copy). ``watch``: watch floors (first access to sensitivity 4). An alert
    floor acts as a watch floor before the route is warm (14 days of v5 state, or a
    bootstrapped caller: pass ``route_warm=True``) and when RF5 ``demoted`` it on this route
    (floor budgets). A floor wins only when its q is strictly smaller than q_stat.
    Validity: pure (reads no state; the caller passes route warm-up and demotions)."""
    for name, rate in (("alert_rate", alert_rate), ("watch_rate", watch_rate)):
        if not 0 < rate < 1:
            raise ValueError(f"{name} must be in (0, 1), not {rate!r}")
    alerts = tuple(dict.fromkeys(alert))
    fired = tuple(dict.fromkeys(alerts + tuple(watch)))
    acting = tuple(f for f in alerts if route_warm and f not in demoted)
    watching = tuple(f for f in fired if f not in acting)
    if acting:
        q_floor, name = alert_rate, acting[0]
    elif watching:
        q_floor, name = watch_rate, watching[0]
    else:
        q_floor, name = math.inf, None
    if q_floor < stat.q:
        return Decision(q_floor, name, stat.q, stat.dimension, fired, acting)
    return Decision(stat.q, stat.dimension, stat.q2, stat.runner_up, fired, acting)


def first_access_floor(sensitivity: int | None, *, touched: bool, unique_match: bool) -> str | None:
    """The first-access floor's level: ALERT for sensitivity 5, WATCH for 4, None otherwise or
    when the caller touched the asset in its last 90 days or the register match was not unique
    (AI-13)."""
    if touched or not unique_match or sensitivity is None:
        return None
    if sensitivity >= ALERT_SENSITIVITY:
        return ALERT
    if sensitivity >= WATCH_SENSITIVITY:
        return WATCH
    return None


def floor_budgets(floor_budget: tuple[float, float]) -> dict[str, float]:
    """The config's ``floor_budget`` (beta for first access, beta for the copy) by floor name,
    for RF5's demotion check."""
    return dict(zip(FLOOR_ORDER, floor_budget, strict=True))


# ── CAL-5: outputs ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Outputs:
    """s1 = 1/(1 + 2q), s2 from q2, M = max(m_min, g(s1)) and the alert (q <= alpha)."""

    s1: float
    s2: float
    multiplier: float
    alert: bool


def strangeness(q: float) -> float:
    """s = 1 / (1 + 2q); 0 when nothing took part (q = inf)."""
    if math.isnan(q) or q < 0:
        raise ValueError(f"q must be at least 0, not {q!r}")
    return 0.0 if math.isinf(q) else 1.0 / (1.0 + 2.0 * q)


def curve(score: float, top: float = MAX_MULTIPLIER, low_base: float = CURVE_LOW_BASE) -> float:
    """g(s): top^(2s - 1) from s = 1/2 up, low_base^(1 - 2s) below (the engine's curve)."""
    if score >= EDGE_OF_ORDINARY:
        return top ** (2 * score - 1)
    return low_base ** (1 - 2 * score)


def alert_line(alpha: float, top: float = MAX_MULTIPLIER, bottom: float = MIN_MULTIPLIER) -> float:
    """M_alpha = max(bottom, g(1/(1 + 2 alpha))): q <= alpha is the same event as M >= M_alpha
    (x4.69 at 1%, x4.29 at 2.5%, x3.73 at 5%)."""
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), not {alpha!r}")
    return max(bottom, curve(1 / (1 + 2 * alpha), top))


def outputs(
    decision: Decision,
    alpha: float | None = ALERT_ALPHA,
    *,
    top: float = MAX_MULTIPLIER,
    bottom: float = MIN_MULTIPLIER,
    line: float | None = None,
) -> Outputs:
    """CAL-5. The alert is q <= alpha; with no alpha it is M >= ``line`` (when given).
    Validity: pure (reads no state)."""
    s1 = strangeness(decision.q)
    value = max(bottom, curve(s1, top))
    if alpha is not None:
        alert = decision.q <= alpha
    else:
        alert = line is not None and value >= line
    return Outputs(s1, strangeness(decision.q2), value, alert)


# ── CAL-7: the route clock ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class FoldResult:
    """One sweep: the new route day, the agent-days folded, the callers swept and the
    reference digests (what the ``behaviour_fold`` line carries)."""

    day: int
    folded: int
    callers: int
    digests: Mapping[str, str]

    def notice(self) -> dict:
        """The ``behaviour_fold`` line's fields."""
        return {"day": self.day, "folded": self.folded, "digests": dict(self.digests)}


@dataclass
class _OpenCaller:
    """A caller's buffered local days, not yet swept into the route reference."""

    zone: str
    days: dict[int, AgentDay] = field(default_factory=dict)
    personal: set[int] = field(default_factory=set)  # days already in his rings


@lru_cache(maxsize=DAY_START_CACHE)
def day_start_ts(day: int, zone_name: str, day_start_hour: float) -> float:
    """The instant local day ``day`` begins in the zone: ``day_start_hour`` on its wall clock
    (B9's rollover; 04:00 by default)."""
    start = datetime(1970, 1, 1, tzinfo=zone(zone_name))
    return (start + timedelta(days=day, hours=day_start_hour)).timestamp()


class RouteClock:
    """The route clock (CAL-7): the route's zone and rollover (04:00 by default), an open-day
    buffer of every caller's running maxima, and the sweep.

    At each route rollover :meth:`advance` visits every caller whose local day had ended at the
    rollover instant, a dormant caller's last day included. It folds those days into the
    caller's :class:`DayRings` (if its next call has not already done so) and files each in the
    :class:`RecordReference` once, with its ready day (the first rollover after its local day
    ended) and its filing day min(local day, ready day - 1). It then builds the new reference
    version and resets the :class:`SurgeGuard`. A version depends only on which agent-days had
    ended by its rollover, so the reference and every price are the same whether the clock
    ticks at every rollover or only at the next call.

    A call is priced against the version current when the caller's local day began
    (:meth:`reference_day`), so a local day that straddles the route's rollover (an APAC
    caller on a UTC route) keeps one reference all day. A caller's own closed days reach its
    rings at its next call (:meth:`rings`), since its J_d is its own local days.

    Under GWR the clock is a member of a :class:`GatewayReference`, which owns the reference,
    the surge guard and the clock's day; the member keeps its callers' rings and open days.
    """

    def __init__(
        self,
        settings: CalibrationSettings | None = None,
        *,
        route: str = "",
        gateway: GatewayReference | None = None,
    ) -> None:
        self.settings = settings or CalibrationSettings()
        if self.settings.reference_scope == GATEWAY and gateway is None:
            raise ValueError("reference_scope 'gateway' needs the gateway's GatewayReference")
        if self.settings.reference_scope == ROUTE and gateway is not None:
            raise ValueError("reference_scope 'route' keeps its own reference: pass no gateway")
        self.route = route
        self.gateway = gateway
        self._day: int | None = None
        self.first_day: int | None = None
        self.open: dict[str, _OpenCaller] = {}
        self.callers: dict[str, DayRings] = {}
        if gateway is None:
            self.reference = RecordReference.for_settings(self.settings)
            self.surge = SurgeGuard(self.settings.surge_min, self.settings.surge_factor)
        else:
            gateway.join(self)
            self.reference, self.surge = gateway.reference, gateway.surge

    @classmethod
    def from_config(
        cls,
        config: BehaviourConfig,
        *,
        route: str = "",
        gateway: GatewayReference | None = None,
    ) -> RouteClock:
        """The clock of a (v5) behaviour config (pass the gateway's reference under GWR)."""
        return cls(CalibrationSettings.from_config(config), route=route, gateway=gateway)

    # ── calendar ──
    @property
    def day(self) -> int | None:
        """The current route day (the gateway's under GWR); None before the first call."""
        return self._day if self.gateway is None else self.gateway.day

    def route_day(self, ts: float) -> int:
        """The route's local day of ``ts`` (its zone, its rollover hour)."""
        s = self.settings
        return local_day(ts, s.route_zone, s.day_start_hour)

    def caller_day(self, ts: float, zone_name: str | None = None) -> int:
        """The caller's local day of ``ts`` (its zone, or the route's when None)."""
        return local_day(ts, zone_name or self.settings.route_zone, self.settings.day_start_hour)

    def rollover_ts(self, day: int) -> float:
        """The instant route day ``day`` begins (``day_start_hour`` on the route's clock)."""
        return day_start_ts(day, self.settings.route_zone, self.settings.day_start_hour)

    def reference_day(self, local: int, zone_name: str | None) -> int:
        """The route day whose reference version prices the caller's local day ``local``: the
        route day in which that local day began, and never later than the clock's day.
        Validity: frozen (it depends only on the day and the zone)."""
        name = zone_name or self.settings.route_zone
        if name == self.settings.route_zone:
            began = local
        else:
            began = self.route_day(day_start_ts(local, name, self.settings.day_start_hour))
        return began if self.day is None else min(began, self.day)

    @property
    def route_warm(self) -> bool:
        """CAL-4 route warm-up: the route has ``route_warmup_days`` days of v5 state.
        Validity: frozen (moves only at a rollover)."""
        warmup = self.settings.route_warmup_days
        if warmup is None:
            return True
        if self.day is None or self.first_day is None:
            return False
        return self.day - self.first_day >= warmup

    # ── the fold ──
    def advance(self, ts: float) -> FoldResult | None:
        """Move the clock to ``ts``. At a rollover, sweep and rebuild, and return what the
        ``behaviour_fold`` line logs; otherwise None. Time never goes back. Under GWR the
        gateway folds every member route at once (see :class:`GatewayReference`)."""
        if self.gateway is not None:
            fold = self.gateway.advance(ts)
            if self.first_day is None:
                self.first_day = self.gateway.day
            return fold
        day = self.route_day(ts)
        if self._day is None:
            self._day = self.first_day = day
            self.reference.rebuild(day)  # empty versions, so every price names one
            return None
        if day <= self._day:
            return None
        folded, swept = self._sweep(self.rollover_ts(day), day)
        self._day = day
        self.reference.rebuild(day)
        self.surge.reset()
        return FoldResult(day, folded, swept, self.reference.digests())

    def rings(self, caller: str, today: int) -> DayRings:
        """The caller's rings with every buffered day before ``today`` in them (idempotent; a
        new caller gets empty rings). Validity: what it returns is frozen for ``today``."""
        rings = self._rings_of(caller)
        held = self.open.get(caller)
        if held is not None:
            for d in sorted(held.days):
                if d < today and d not in held.personal:
                    rings.close_day(d, held.days[d])
                    held.personal.add(d)
        return rings

    # ── per call ──
    def price(
        self, caller: str, ts: float, zone_name: str | None, measures: CallMeasures
    ) -> Priced:
        """q_d for every dimension of one call (CAL-1, CAL-2, CAL-6). A record is priced
        min(1/(A_d + 1), r_d) when it has a strength; Oversized request and Missing handshake
        only against the organisation. Call :meth:`advance` first.

        Validity: frozen (rings, and the version of :meth:`reference_day`), except the surge
        guard (open), which only raises q."""
        self._check_current(ts)
        today = self.caller_day(ts, zone_name)
        version = self.reference.version(self.reference_day(today, zone_name))
        rings = self.rings(caller, today)
        agent = self._agent(caller)
        common: dict[str, Commonness] = {}
        for dim, amount in measures.amounts.items():
            common[dim] = rings.amount(dim, amount, today)
        for dim, used in measures.values.items():
            common[dim] = rings.value(dim, used, today)
        for dim, key in measures.flags.items():
            common[dim] = rings.flag(dim, key, today)
        rates: dict[str, float] = {}
        records: list[str] = []
        ranked: dict[str, float] = {}
        surged: list[str] = []
        for dim, personal in common.items():
            q = personal.q
            strength = measures.strengths.get(dim)
            if personal.record:
                records.append(dim)
                if strength is not None:
                    ranked[dim] = strength
                    if self.settings.record_rank:
                        q = record_price(personal.days, version.rank(dim, strength))
                        q, hot = self.surge.price(dim, agent, strength, q, self.reference.current)
                        if hot:
                            surged.append(dim)
            rates[dim] = q
        for dim, strength in measures.org_flags.items():
            ranked[dim] = strength
            q = version.rank(dim, strength)
            if dim not in UNSURGED:
                q, hot = self.surge.price(dim, agent, strength, q, self.reference.current)
                if hot:
                    surged.append(dim)
            rates[dim] = q
        return Priced(rates, tuple(records), ranked, tuple(surged), common, version.day)

    def commit(
        self,
        caller: str,
        ts: float,
        zone_name: str | None,
        measures: CallMeasures,
        priced: Priced,
    ) -> None:
        """Learn from one accepted call: its caller-day's running maxima and today's surge
        counts. ``priced`` is what :meth:`price` gave it (its records and ranked strengths)."""
        self._check_current(ts)
        today = self.caller_day(ts, zone_name)
        held = self.open.setdefault(caller, _OpenCaller(zone_name or self.settings.route_zone))
        held.zone = zone_name or self.settings.route_zone
        held.days.setdefault(today, AgentDay()).add(measures, priced, self.settings.max_values)
        held.personal.discard(today)  # merged again into the rings when it closes
        self.surge.note(self._agent(caller), measures.dimensions(), priced.ranked)

    def path_activity(self, shares: Mapping[str, float | None], alpha: float) -> dict[str, bool]:
        """:meth:`RecordReference.path_activity` of this route's reference. Validity: frozen."""
        return self.reference.path_activity(shares, alpha)

    # ── state ──
    def to_json(self) -> dict:
        """The clock's state. Under GWR the reference, the surge guard and the day belong to
        the :class:`GatewayReference`, which saves them."""
        own = self.gateway is None
        return {
            "day": self._day if own else None,
            "first_day": self.first_day,
            "open": {
                c: {
                    "zone": h.zone,
                    "personal": sorted(h.personal),
                    "days": {str(d): ad.to_json() for d, ad in sorted(h.days.items())},
                }
                for c, h in sorted(self.open.items())
            },
            "callers": {c: r.to_json() for c, r in sorted(self.callers.items())},
            "surge": self.surge.to_json() if own else None,
            "reference": self.reference.to_json() if own else None,
        }

    @classmethod
    def from_json(
        cls,
        data: dict,
        settings: CalibrationSettings | None = None,
        *,
        route: str = "",
        gateway: GatewayReference | None = None,
    ) -> RouteClock:
        """A clock from :meth:`to_json`. Under GWR pass the restored gateway reference; a
        route-scope snapshot must carry its own reference and surge counts."""
        settings = settings or CalibrationSettings()
        own = data["reference"] is not None and data["surge"] is not None
        if gateway is None and not own:
            raise ValueError("this snapshot has no reference: restore it with its gateway")
        if gateway is not None and data["reference"] is not None:
            raise ValueError("a route-scope snapshot cannot join a gateway reference")
        clock = cls(settings, route=route, gateway=gateway)
        if gateway is None:
            clock.reference = RecordReference.from_json(data["reference"], settings)
            clock.surge.load_json(data["surge"])
            clock._day = data["day"]
        clock.first_day = data["first_day"]
        clock.open = {
            c: _OpenCaller(
                h["zone"],
                {int(d): AgentDay.from_json(ad) for d, ad in h["days"].items()},
                set(h["personal"]),
            )
            for c, h in data["open"].items()
        }
        clock.callers = {c: DayRings.from_json(r, settings) for c, r in data["callers"].items()}
        return clock

    # ── internals ──
    def _sweep(self, at: float, day: int) -> tuple[int, int]:
        """Fold every buffered caller-day that had ended at instant ``at`` (route day ``day``
        begins): into the caller's rings, and once into the reference. Returns (agent-days
        folded, callers swept). The rebuild is the caller's (the clock, or its gateway)."""
        folded, swept = 0, 0
        for caller in sorted(self.open):
            held = self.open[caller]
            now = self.caller_day(at, held.zone)  # his local day at the rollover instant
            ended = [d for d in sorted(held.days) if d < now]
            if ended:
                swept += 1
            for d in ended:
                agent_day = held.days.pop(d)
                if d not in held.personal:
                    self._rings_of(caller).close_day(d, agent_day)
                held.personal.discard(d)
                ready = self._ready_day(d, held.zone)
                self.reference.add(
                    min(d, ready - 1), self._key(caller, d), _entry(caller, agent_day), ready
                )
                folded += 1
            if not held.days:
                del self.open[caller]
        self._forget_unreachable(day)
        return folded, swept

    def _ready_day(self, local: int, zone_name: str) -> int:
        """The first route rollover at or after the end of local day ``local`` in the zone."""
        s = self.settings
        if zone_name == s.route_zone:
            return local + 1
        end = day_start_ts(local + 1, zone_name, s.day_start_hour)
        day = self.route_day(end)
        return day if self.rollover_ts(day) >= end else day + 1

    def _forget_unreachable(self, day: int) -> None:
        """Drop the rings of callers whose every closed day is older than any window can reach
        (one spare day: a caller's local day and the route's differ by at most one)."""
        s = self.settings
        span = s.past_days if s.max_history_days is None else s.max_history_days - 1
        for caller in [c for c, r in self.callers.items() if c not in self.open]:
            days = self.callers[caller].days
            if not days or max(days) < day - span - 1:
                del self.callers[caller]

    def _rings_of(self, caller: str) -> DayRings:
        rings = self.callers.get(caller)
        if rings is None:
            rings = self.callers[caller] = DayRings.for_settings(self.settings)
        return rings

    def _agent(self, caller: str) -> str:
        """The surge guard's key: the caller, or (route, caller) on a shared reference."""
        return caller if self.gateway is None else _KEY_SEP.join((self.route, caller))

    def _key(self, caller: str, day: int) -> str:
        return _KEY_SEP.join((self.route, caller, str(day)))

    def _check_current(self, ts: float) -> None:
        if self.day is None or self.route_day(ts) > self.day:
            raise ValueError("the route clock is behind this call: advance(ts) first")


class GatewayReference:
    """GWR (spec 4.4): one route reference, one surge guard and one clock for several routes.

    Every member route (a :class:`RouteClock` built with ``gateway=``) shares the gateway's
    zone, day start, window, surge and TOP/EST settings (:data:`SHARED_SETTINGS`), and keeps
    its own callers' rings and open days. The first member call after a gateway rollover folds
    every member route, in route-name order, and builds the shared version once; no member
    rebuilds it, so a price never depends on which route advanced first. The surge guard
    counts today's agent-days of every member route, each keyed by (route, caller), against
    the same gateway-wide window mean.

    Live equals offline only when offline replay feeds every member route's calls in timestamp
    order (one merged log), as they reached the gateway.
    """

    def __init__(self, settings: CalibrationSettings) -> None:
        if settings.reference_scope != GATEWAY:
            raise ValueError("a gateway reference needs reference_scope 'gateway'")
        self.settings = settings
        self.reference = RecordReference.for_settings(settings)
        self.surge = SurgeGuard(settings.surge_min, settings.surge_factor)
        self.day: int | None = None
        self.members: dict[str, RouteClock] = {}

    @classmethod
    def from_config(cls, config: BehaviourConfig) -> GatewayReference:
        """The gateway reference of a (v5) behaviour config with ``reference_scope="gateway"``."""
        return cls(CalibrationSettings.from_config(config))

    def join(self, clock: RouteClock) -> None:
        """Register a member route: its name is unique and it shares :data:`SHARED_SETTINGS`."""
        if clock.route in self.members:
            raise ValueError(f"route {clock.route!r} already uses this gateway reference")
        for name in SHARED_SETTINGS:
            if getattr(clock.settings, name) != getattr(self.settings, name):
                raise ValueError(f"a member route must share the gateway's {name}")
        self.members[clock.route] = clock

    def route_day(self, ts: float) -> int:
        """The gateway's day of ``ts`` (its zone, its rollover hour)."""
        return local_day(ts, self.settings.route_zone, self.settings.day_start_hour)

    def advance(self, ts: float) -> FoldResult | None:
        """Move the gateway clock to ``ts``. At a rollover, sweep every member route and build
        the shared version once; return what the ``behaviour_fold`` line logs, else None."""
        day = self.route_day(ts)
        if self.day is None:
            self.day = day
            self.reference.rebuild(day)  # empty versions, so every price names one
            return None
        if day <= self.day:
            return None
        at = day_start_ts(day, self.settings.route_zone, self.settings.day_start_hour)
        folded, swept = 0, 0
        for route in sorted(self.members):
            route_folded, route_swept = self.members[route]._sweep(at, day)
            folded, swept = folded + route_folded, swept + route_swept
        self.day = day
        self.reference.rebuild(day)
        self.surge.reset()
        return FoldResult(day, folded, swept, self.reference.digests())

    def to_json(self) -> dict:
        """The shared state: the day, the reference and today's surge counts."""
        return {
            "day": self.day,
            "reference": self.reference.to_json(),
            "surge": self.surge.to_json(),
        }

    @classmethod
    def from_json(cls, data: dict, settings: CalibrationSettings) -> GatewayReference:
        """A gateway reference from :meth:`to_json`; restore its member clocks after it."""
        gateway = cls(settings)
        gateway.day = data["day"]
        gateway.reference = RecordReference.from_json(data["reference"], settings)
        gateway.surge.load_json(data["surge"])
        return gateway


def _entry(caller: str, agent_day: AgentDay) -> ReferenceEntry:
    return ReferenceEntry(
        caller, agent_day.established, frozenset(agent_day.took), dict(agent_day.ranked)
    )


# ── small helpers ───────────────────────────────────────────────────────────────────────────
def _check_positive_int(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, not {value!r}")


def _check_finite(name: str, value: float) -> None:
    if not isinstance(value, Real) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, not {value!r}")


def _add_capped(target: set[Hashable], values: Iterable[Hashable], cap: int | None) -> None:
    """Add values to a day's set; past ``cap`` distinct ones they become :data:`OVERFLOW`."""
    for value in values:
        if value in target or cap is None or len(target) - (OVERFLOW in target) < cap:
            target.add(value)
        else:
            target.add(OVERFLOW)


def _mask_days(mask: int, base: int | None) -> list[int]:
    """The days of a bit mask (bit i is day ``base`` + i), oldest first."""
    days, i = [], 0
    while mask:
        if mask & 1:
            days.append(base + i)
        mask >>= 1
        i += 1
    return days


def _days_mask(days: Iterable[int], base: int | None) -> int:
    """The bit mask of ``days`` (the inverse of :func:`_mask_days`)."""
    mask = 0
    for day in days:
        mask |= 1 << (day - base)
    return mask


def _encode_set(values: set[Hashable]) -> list:
    return sorted((_encode(v) for v in values), key=repr)


def _encode(value: Hashable) -> object:
    return [_encode(v) for v in value] if isinstance(value, tuple) else value


def _decode(value: object) -> Hashable:
    return tuple(_decode(v) for v in value) if isinstance(value, list) else value


def _digest_floats(head: list, values: list[float]) -> str:
    """A digest of ``head`` (JSON) and ``values`` (little-endian doubles)."""
    packed = array("d", values)
    if sys.byteorder == "big":
        packed.byteswap()
    digest = hashlib.sha256(json.dumps(head, separators=(",", ":")).encode())
    digest.update(packed.tobytes())
    return digest.hexdigest()[:DIGEST_CHARS]
