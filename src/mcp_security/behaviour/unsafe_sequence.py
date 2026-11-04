"""E5, SEQ-1, SEQ-2 and the E14 hook (v5): Unsafe sequence over the caller's own recent calls.

Design v4 looks for an unsafe sequence inside one MCP protocol session, so a missing or new
session id hides it (and a sessionless call to a guarded tool was always raised: bug E1).
Design v5 looks back over fixed windows of the caller's own calls, across sessions, and never
reads a session id. Three parts, each raised on its own (spec 4.4, E5)::

    (A) required step   raised <=> need(tool) != {} and no call of his to a tool in need(tool)
                        in [ts - 24 h, ts], on the same asset or with either asset unresolved
                        (requires_same_asset; off: the tool alone)
    (B) read then write raised <=> a write to asset T, and he read a different asset S of
                        sensitivity >= 4 in [ts - 10 min, ts]           (a "copy" from S to T)
    (C) blind write     raised <=> a write to a sensitivity >= 4 asset T he has not read on
                        day >= today - 7 (v4's rule, unchanged)

SEQ-1: each raise is kept as a record keyed by the (source asset, target asset) pair. A pair
the caller never raised before in his window (his past days, today excluded) is a **record**;
a pair raised on earlier days is **habit**, and its count of past days is what the habit
discount prices (spec 2.3)::

    strength = max(0, sens(source) - sens(target)) + (1 if the target is public else 0)

An unknown target sensitivity counts as the lowest level (fail closed). Parts (A) and (C)
have no source asset: their source is a marker (``(no step before <tool>)``, ``(no read)``)
and their drop is 0, so only the public bonus adds to their strength. An unresolved target is
the marker ``(unresolved)``, so every part-(A) raise on an unresolved asset shares one pair per
guarded tool: after its first raised day, later ones on any asset are habit (open question
for the author, with the markers themselves).

SEQ-2, the copy floor: a part-(B) copy out of a sensitivity-5 source into a target that is
public, that a different owner holds (both owners known and unequal), or that is new for the
caller. The floor's price, budget and demotion are the calibration's (CAL-4); this module
only says that it fired, and why.

E14: :func:`ledger_reads` reads other routes' sensitive reads from the gateway's
:class:`~mcp_security.gateway.framework.ReadLedger`, and :func:`share_read` adds this route's;
:class:`WindowReadLedger` is a bounded in-memory ledger. The engine passes the cross-route
reads to :func:`evaluate` (only for writes the scan marks outbound, once it does). Another
route's asset is named ``<route>:<asset>`` (:func:`source_id`), so an asset with the same id
on another route is a different source and a different pair.

Usage, in the engine's score/commit split (ARG-1)::

    finding = evaluate(state, message, day, rules, target_new=..., cross_reads=...)  # pure
    commit(state, message, day, finding, rules, habit=established)  # once accepted

``evaluate`` never changes ``state``; ``commit`` learns the call's step, its sensitive read
and the pair days. A late message never replaces a newer step or read of the same key (one
entry per key, the newest). Every container is bounded in time and in size (DEP-7).
"""

from __future__ import annotations

import bisect
import math
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mcp_security.behaviour.engine import BehaviourConfig
    from mcp_security.gateway.framework import LedgerRead, ReadLedger

MINUTE_S = 60.0
DAY_S = 86_400.0
#: Message values, equal to ``engine.READ``, ``engine.WRITE`` and ``engine.PUBLIC`` (this
#: module cannot import the engine, which imports it).
READ, WRITE = "read", "write"
PUBLIC = "public"

SEQUENCE_WINDOW_S = 10 * MINUTE_S  # E5 (B): read then write within 10 minutes
REQUIRES_WINDOW_S = DAY_S  # E5 (A): the required step within 24 hours
READ_MEMORY_DAYS = 7  # E5 (C): v4's blind-write memory, in days
SENSITIVE_LEVEL = 4  # reads at or above this sensitivity are remembered
COPY_SOURCE_LEVEL = 5  # SEQ-2: a copy out of a source this sensitive can fire the floor
HISTORY_DAYS = 90  # SEQ-1: pair days are counted over his last 90 days
MAX_ENTRIES = 4_096  # DEP-7: reads, steps, read days and pairs kept per caller, at most
MIN_SENSITIVITY, MAX_SENSITIVITY = 1, 5
PUBLIC_BONUS = 1  # SEQ-1: a public target adds one to the strength

#: The parts of Unsafe sequence (the kind named in a verdict's reason, RF6 (c)).
REQUIRED_STEP = "required_step"  # (A): e.g. a merge with no review
READ_THEN_WRITE = "read_then_write"  # (B): a copy
BLIND_WRITE = "blind_write"  # (C)
PARTS = (REQUIRED_STEP, READ_THEN_WRITE, BLIND_WRITE)

#: Source and target markers for parts with no source asset, or an unresolved target.
NO_READ = "(no read)"
UNRESOLVED = "(unresolved)"
_NO_STEP = "(no step before {tool})"
#: E14: how another route's asset is named as a source (in pair keys and copy floors)
_CROSS_ROUTE_SOURCE = "{route}:{asset}"

#: SEQ-2: why the copy floor fired.
PUBLIC_TARGET, FOREIGN_OWNER, NEW_TARGET = "public_target", "foreign_owner", "new_target"

PairKey = tuple[str, str]  # (source asset, target asset)


def missing_step_source(tool: str) -> str:
    """Part (A)'s source marker: the guarded tool whose required step is missing."""
    return _NO_STEP.format(tool=tool)


def source_id(read: SensitiveRead) -> str:
    """A read's source id: its asset, qualified with its route for another route's read
    (E14), so the same asset id on two routes names two different sources."""
    if read.route is None:
        return read.asset
    return _CROSS_ROUTE_SOURCE.format(route=read.route, asset=read.asset)


class SequenceCall(Protocol):
    """What the checks read from a call. The engine's ``Message`` has every field."""

    @property
    def ts(self) -> float: ...

    @property
    def tool(self) -> str | None: ...

    @property
    def asset(self) -> str | None: ...

    @property
    def sensitivity(self) -> int | None: ...

    @property
    def operation(self) -> str | None: ...

    @property
    def exposure(self) -> str | None: ...

    @property
    def owner(self) -> str | None: ...


@dataclass(frozen=True)
class SensitiveRead:
    """One remembered read of a sensitive asset. ``route`` is None for this route's own
    reads and names the other route for a read from the ledger (E14)."""

    ts: float
    asset: str
    sensitivity: int
    owner: str | None = None
    route: str | None = None


@dataclass(frozen=True)
class SequenceRules:
    """The checks' settings. A window at None switches its part off here (the engine then
    keeps v4's session-scoped check for it); :meth:`from_config` reads a v5 config.
    ``requires_before`` is copied into a read-only mapping (left out of the hash)."""

    requires_before: Mapping[str, frozenset[str]] = field(default_factory=dict, hash=False)
    read_window_s: float | None = SEQUENCE_WINDOW_S  # (B)
    step_window_s: float | None = REQUIRES_WINDOW_S  # (A)
    same_asset: bool = True  # (A): the step must be on the same asset (or either unresolved)
    read_memory_days: int = READ_MEMORY_DAYS  # (C)
    sensitive_level: int = SENSITIVE_LEVEL
    copy_source_level: int = COPY_SOURCE_LEVEL  # SEQ-2
    history_days: int = HISTORY_DAYS  # SEQ-1
    track_pairs: bool = True  # SEQ-1 (``sequence_record``); off: no pair days are kept
    copy_floor: bool = True  # SEQ-2 (``copy_floor``)
    max_entries: int = MAX_ENTRIES  # DEP-7
    step_tools: frozenset[str] = field(init=False)  # every tool some guarded tool requires

    def __post_init__(self) -> None:
        needs = MappingProxyType(
            {tool: frozenset(steps) for tool, steps in self.requires_before.items()}
        )
        object.__setattr__(self, "requires_before", needs)
        object.__setattr__(self, "step_tools", frozenset().union(*needs.values()))
        for name in ("read_window_s", "step_window_s"):
            value = getattr(self, name)
            if value is not None and not _positive(value):
                raise ValueError(f"{name} must be positive seconds or None, not {value!r}")
        for name in ("read_memory_days", "history_days", "max_entries"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer, not {value!r}")
        for name in ("sensitive_level", "copy_source_level"):
            value = getattr(self, name)
            if not MIN_SENSITIVITY <= value <= MAX_SENSITIVITY:
                raise ValueError(f"{name} must be a sensitivity 1-5, not {value!r}")

    @classmethod
    def from_config(cls, config: BehaviourConfig) -> SequenceRules:
        """The rules of a behaviour config (v5: E5's windows, SEQ-1's ``sequence_record``,
        SEQ-2's ``copy_floor``, DEP-7's ``max_values_per_kind``)."""
        return cls(
            requires_before=config.requires_before,
            read_window_s=config.sequence_window_s,
            step_window_s=config.requires_window_s,
            same_asset=config.requires_same_asset,
            read_memory_days=config.read_memory_days,
            sensitive_level=config.sensitive_level,
            history_days=config.history_days,
            track_pairs=config.sequence_record,
            copy_floor=config.copy_floor,
            max_entries=config.max_values_per_kind or MAX_ENTRIES,
        )


@dataclass(frozen=True)
class PairFlag:
    """One raised (source, target) pair (SEQ-1). ``past_days`` is how many of the caller's
    past days in his window (today excluded) raised the same pair; None when pairs are not
    tracked (``track_pairs`` off)."""

    source: str
    target: str
    part: str
    strength: int
    past_days: int | None

    @property
    def key(self) -> PairKey:
        """The pair's key in the caller's pair days: (source, target)."""
        return (self.source, self.target)

    @property
    def record(self) -> bool:
        """A new pair: the first raise of this pair in his window (spec 2.3)."""
        return self.past_days == 0


@dataclass(frozen=True)
class CopyFloor:
    """SEQ-2: a copy out of a sensitivity-5 source that fired the copy floor, and why.
    ``source`` is the pair's source id (:func:`source_id`)."""

    source: str
    target: str
    reasons: tuple[str, ...]  # PUBLIC_TARGET, FOREIGN_OWNER, NEW_TARGET
    route: str | None = None  # the source read's route when it came from the ledger (E14)


@dataclass(frozen=True)
class SequenceFinding:
    """What :func:`evaluate` found for one call: the parts raised, one pair per raise, and
    the copies that fired the copy floor."""

    parts: tuple[str, ...] = ()
    pairs: tuple[PairFlag, ...] = ()
    copy_floors: tuple[CopyFloor, ...] = ()

    @property
    def raised(self) -> bool:
        """Some part of Unsafe sequence was raised."""
        return bool(self.parts)

    @property
    def lead(self) -> PairFlag | None:
        """The pair that prices the call: the strangest (fewest past days), then the
        strongest; None when nothing was raised."""
        if not self.pairs:
            return None
        return min(
            self.pairs,
            key=lambda p: (p.past_days or 0, -p.strength, PARTS.index(p.part), p.key),
        )

    @property
    def record(self) -> bool:
        """The call raised a pair new in the caller's window (SEQ-1's record path)."""
        lead = self.lead
        return lead is not None and lead.record

    @property
    def strength(self) -> int | None:
        """The lead pair's strength, compared across callers by the record rank."""
        lead = self.lead
        return None if lead is None else lead.strength


@dataclass
class SequenceState:
    """One caller's memory for Unsafe sequence, saved in the engine's snapshot.

    Insertion order is recency (each update moves its entry to the end; a late message
    never does), so pruning by time and by size pops from the front. A late message for a
    new key can sit behind newer entries, which only delays its pruning: every lookup
    checks its own window."""

    #: (B) the latest sensitive read of each asset in the read window
    reads: OrderedDict[str, SensitiveRead] = field(default_factory=OrderedDict)
    #: (A) (step tool, asset or None) -> the latest call, in the step window
    steps: OrderedDict[tuple[str, str | None], float] = field(default_factory=OrderedDict)
    #: (C) sensitive asset -> the last day he read it, within the read memory
    last_read: OrderedDict[str, int] = field(default_factory=OrderedDict)
    #: SEQ-1: pair -> the days it was raised (ascending), within his window
    pair_days: OrderedDict[PairKey, list[int]] = field(default_factory=OrderedDict)

    def past_days(self, pair: PairKey, today: int, history_days: int = HISTORY_DAYS) -> int:
        """Days in [today - history_days + 1, today - 1] on which ``pair`` was raised."""
        days = self.pair_days.get(pair)
        if not days:
            return 0
        start = bisect.bisect_left(days, today - history_days + 1)
        return bisect.bisect_left(days, today) - start

    def to_json(self) -> dict[str, list]:
        """JSON-safe data for the engine's snapshot."""
        return {
            "reads": [[r.ts, r.asset, r.sensitivity, r.owner] for r in self.reads.values()],
            "steps": [[tool, asset, ts] for (tool, asset), ts in self.steps.items()],
            "last_read": [[asset, day] for asset, day in self.last_read.items()],
            "pairs": [[s, t, list(days)] for (s, t), days in self.pair_days.items()],
        }

    @classmethod
    def from_json(cls, data: dict[str, list] | None) -> SequenceState:
        """Saved state back; empty for a caller saved without one (a v4 snapshot)."""
        out = cls()
        if not data:
            return out
        for ts, asset, sensitivity, owner in data.get("reads", []):
            out.reads[asset] = SensitiveRead(float(ts), asset, int(sensitivity), owner)
        for tool, asset, ts in data.get("steps", []):
            out.steps[(tool, asset)] = float(ts)
        for asset, day in data.get("last_read", []):
            out.last_read[asset] = int(day)
        for source, target, days in data.get("pairs", []):
            out.pair_days[(source, target)] = sorted(int(d) for d in days)
        return out


def evaluate(
    state: SequenceState,
    call: SequenceCall,
    day: int,
    rules: SequenceRules,
    *,
    target_new: bool = False,
    cross_reads: Iterable[SensitiveRead] = (),
) -> SequenceFinding:
    """Unsafe sequence for ``call`` on the caller's local ``day``, without changing ``state``.

    ``target_new``: the target is new for the caller (not touched in his last 90 days; the
    engine knows his assets), one of SEQ-2's triggers. ``cross_reads``: other routes'
    sensitive reads in the read window (:func:`ledger_reads`, E14). No session id is read
    anywhere, so a sessionless call is judged exactly like a sessioned one (E5)."""
    tool = call.tool or ""
    public = call.exposure == PUBLIC
    parts: list[str] = []
    pairs: list[PairFlag] = []
    floors: tuple[CopyFloor, ...] = ()

    def flag(source: str, target: str, part: str, drop: int) -> None:
        past = None
        if rules.track_pairs:
            past = state.past_days((source, target), day, rules.history_days)
        strength = max(0, drop) + (PUBLIC_BONUS if public else 0)
        pairs.append(PairFlag(source, target, part, strength, past))

    needed = rules.requires_before.get(tool)
    if needed and rules.step_window_s is not None:  # (A)
        if not _step_done(state, needed, call.asset, call.ts, rules):
            parts.append(REQUIRED_STEP)
            flag(missing_step_source(tool), call.asset or UNRESOLVED, REQUIRED_STEP, 0)
    writes = call.operation == WRITE and bool(call.asset)
    if writes and rules.read_window_s is not None:  # (B)
        sources = _sources(state, cross_reads, call, rules)
        if sources:
            parts.append(READ_THEN_WRITE)
            target_level = MIN_SENSITIVITY if call.sensitivity is None else call.sensitivity
            for read in sources:
                drop = read.sensitivity - target_level
                flag(source_id(read), call.asset, READ_THEN_WRITE, drop)
            if rules.copy_floor:
                floors = _copy_floors(sources, call, rules, target_new)
    if writes and (call.sensitivity or 0) >= rules.sensitive_level:  # (C)
        last = state.last_read.get(call.asset)
        if last is None or last < day - rules.read_memory_days:
            parts.append(BLIND_WRITE)
            flag(NO_READ, call.asset, BLIND_WRITE, 0)
    return SequenceFinding(tuple(parts), tuple(pairs), floors)


def commit(
    state: SequenceState,
    call: SequenceCall,
    day: int,
    finding: SequenceFinding,
    rules: SequenceRules,
    *,
    habit: bool = True,
) -> None:
    """Learn from an accepted call: its required-step use, its sensitive read, and the days
    of the pairs ``finding`` raised. ``habit`` False keeps the pair days out (RF11: habit
    days count only once the caller is established). A late message (stamped before the
    step or read already held for its key) never replaces the newer one."""
    tool = call.tool or ""
    if habit and rules.track_pairs:
        for pair in finding.pairs:
            _add_day(state.pair_days, pair.key, day, rules.history_days)
    step = (tool, call.asset)
    if tool in rules.step_tools and state.steps.get(step, -math.inf) < call.ts:
        _put(state.steps, step, call.ts)
    sensitivity = call.sensitivity or 0
    if call.operation == READ and call.asset and sensitivity >= rules.sensitive_level:
        held = state.reads.get(call.asset)
        if held is None or held.ts <= call.ts:
            _put(
                state.reads, call.asset, SensitiveRead(call.ts, call.asset, sensitivity, call.owner)
            )
        if state.last_read.get(call.asset, day) <= day:  # never an older day
            _put(state.last_read, call.asset, day)
    _prune(state, call.ts, day, rules)


# ── E14: the cross-route read ledger ─────────────────────────────────────────────────────
def ledger_reads(
    ledger: ReadLedger | None,
    caller: str,
    route: str,
    ts: float,
    window_s: float = SEQUENCE_WINDOW_S,
    sensitive_level: int = SENSITIVE_LEVEL,
) -> tuple[SensitiveRead, ...]:
    """``caller``'s sensitive reads on routes other than ``route`` in [ts - window_s, ts],
    for :func:`evaluate`'s ``cross_reads``; () without a ledger. This route's own reads are
    left out: they are already in the caller's :class:`SequenceState`."""
    if ledger is None:
        return ()
    return tuple(
        SensitiveRead(read_ts, asset, sensitivity, owner, other)
        for read_ts, other, asset, sensitivity, owner in ledger.reads_since(caller, ts - window_s)
        if other != route and read_ts <= ts and sensitivity >= sensitive_level
    )


def share_read(
    ledger: ReadLedger | None,
    caller: str,
    route: str,
    call: SequenceCall,
    sensitive_level: int = SENSITIVE_LEVEL,
) -> bool:
    """Tell the ledger about an accepted sensitive read on ``route``, so other routes can see
    it; whether it was noted (not without a ledger, and not for other calls)."""
    sensitivity = call.sensitivity or 0
    if ledger is None or call.operation != READ or not call.asset or sensitivity < sensitive_level:
        return False
    ledger.note_read(caller, route, call.asset, sensitivity, call.ts, owner=call.owner)
    return True


class WindowReadLedger:
    """An in-memory :class:`~mcp_security.gateway.framework.ReadLedger`: each caller's
    sensitive reads over the last ``window_s``, at most ``max_reads`` per caller. Callers
    with nothing in the window are forgotten, so memory follows the active callers."""

    def __init__(self, window_s: float = SEQUENCE_WINDOW_S, max_reads: int = MAX_ENTRIES) -> None:
        if not _positive(window_s):
            raise ValueError(f"window_s must be positive seconds, not {window_s!r}")
        if isinstance(max_reads, bool) or not isinstance(max_reads, int) or max_reads <= 0:
            raise ValueError(f"max_reads must be a positive integer, not {max_reads!r}")
        self.window_s, self.max_reads = window_s, max_reads
        #: caller -> his reads, oldest first; callers ordered by their latest read
        self._reads: OrderedDict[str, deque[LedgerRead]] = OrderedDict()

    def note_read(
        self,
        caller: str,
        route: str,
        asset: str,
        sensitivity: int,
        ts: float,
        owner: str | None = None,
    ) -> None:
        """Remember one read (the protocol's ``note_read``)."""
        reads = self._reads.pop(caller, None) or deque(maxlen=self.max_reads)
        reads.append((ts, route, asset, sensitivity, owner))
        self._reads[caller] = reads
        horizon = ts - self.window_s
        while self._reads:  # forget callers whose latest read left the window
            first = next(iter(self._reads))
            if self._reads[first][-1][0] >= horizon:
                break
            del self._reads[first]
        while reads and reads[0][0] < horizon:
            reads.popleft()

    def reads_since(self, caller: str, since: float) -> list[LedgerRead]:
        """``caller``'s remembered reads at or after ``since``, oldest first."""
        return [read for read in self._reads.get(caller, ()) if read[0] >= since]

    def __len__(self) -> int:
        """Reads held, over every caller."""
        return sum(len(reads) for reads in self._reads.values())


# ── helpers ──────────────────────────────────────────────────────────────────────────────
def _positive(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _step_done(
    state: SequenceState, needed: frozenset[str], asset: str | None, ts: float, rules: SequenceRules
) -> bool:
    """(A): some tool in ``needed`` was called in [ts - window, ts], on the same asset when
    both are resolved (or on any asset when ``same_asset`` is off)."""
    since = ts - rules.step_window_s

    def recent(key: tuple[str, str | None]) -> bool:
        step_ts = state.steps.get(key)
        return step_ts is not None and since <= step_ts <= ts

    if rules.same_asset and asset is not None:
        return any(recent((tool, asset)) or recent((tool, None)) for tool in needed)
    return any(tool in needed and since <= t <= ts for (tool, _), t in state.steps.items())


def _sources(
    state: SequenceState,
    cross_reads: Iterable[SensitiveRead],
    call: SequenceCall,
    rules: SequenceRules,
) -> tuple[SensitiveRead, ...]:
    """(B): the latest sensitive read of each source other than the target in the read
    window, keyed by (route, asset) and ordered by :func:`source_id`. Only this route's own
    asset can be the target: another route's asset never is, whatever its id (E14)."""
    since = call.ts - rules.read_window_s
    target = (None, call.asset)
    latest: dict[tuple[str | None, str], SensitiveRead] = {}
    for read in (*state.reads.values(), *cross_reads):
        key = (read.route, read.asset)
        if (
            key != target
            and since <= read.ts <= call.ts
            and read.sensitivity >= rules.sensitive_level
            and (key not in latest or read.ts > latest[key].ts)
        ):
            latest[key] = read
    return tuple(sorted(latest.values(), key=lambda read: (source_id(read), read.route or "")))


def _copy_floors(
    sources: tuple[SensitiveRead, ...], call: SequenceCall, rules: SequenceRules, target_new: bool
) -> tuple[CopyFloor, ...]:
    """SEQ-2: the copies out of a sensitivity-5 source into a public, foreign-owned or new
    target. An unknown owner is never foreign, and an unknown exposure is not public."""
    floors = []
    for read in sources:
        if read.sensitivity < rules.copy_source_level:
            continue
        reasons = []
        if call.exposure == PUBLIC:
            reasons.append(PUBLIC_TARGET)
        if read.owner is not None and call.owner is not None and read.owner != call.owner:
            reasons.append(FOREIGN_OWNER)
        if target_new:
            reasons.append(NEW_TARGET)
        if reasons:
            floors.append(CopyFloor(source_id(read), call.asset, tuple(reasons), read.route))
    return tuple(floors)


def _put[K, V](entries: OrderedDict[K, V], key: K, value: V) -> None:
    """Set ``key`` and move it to the most recent end."""
    entries[key] = value
    entries.move_to_end(key)


def _add_day(
    pair_days: OrderedDict[PairKey, list[int]], pair: PairKey, day: int, history_days: int
) -> None:
    """Record that ``pair`` was raised on ``day`` (once per day), dropping its days that
    left the window."""
    days = pair_days.get(pair)
    if days is None:
        days = pair_days[pair] = []
    index = bisect.bisect_left(days, day)
    if index == len(days) or days[index] != day:
        days.insert(index, day)
    del days[: bisect.bisect_right(days, day - history_days)]
    pair_days.move_to_end(pair)


def _prune(state: SequenceState, ts: float, day: int, rules: SequenceRules) -> None:
    """Drop what no window can use any more, then cap every container (DEP-7)."""
    if rules.read_window_s is not None:
        _pop_while(state.reads, lambda read: read.ts < ts - rules.read_window_s)
    if rules.step_window_s is not None:
        _pop_while(state.steps, lambda step_ts: step_ts < ts - rules.step_window_s)
    # a read before day - read_memory_days makes a write as blind as no read at all
    _pop_while(state.last_read, lambda read_day: read_day < day - rules.read_memory_days)
    _pop_while(state.pair_days, lambda days: not days or days[-1] <= day - rules.history_days)
    for entries in (state.reads, state.steps, state.last_read, state.pair_days):
        while len(entries) > rules.max_entries:
            entries.popitem(last=False)


def _pop_while[K, V](entries: OrderedDict[K, V], stale: Callable[[V], bool]) -> None:
    """Pop entries from the oldest end while ``stale(value)`` holds."""
    while entries and stale(next(iter(entries.values()))):
        entries.popitem(last=False)
