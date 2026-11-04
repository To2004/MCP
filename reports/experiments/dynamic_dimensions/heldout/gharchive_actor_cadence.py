"""X2 (spec 6.4, EV-26b): per-actor cadence from GH Archive, pseudonymised, aggregates only.

Every number this module prints is "real public activity, not MCP traffic". GH Archive holds
public state changes only: there are no reads, no replies, no networks and no clients. So this
extracts the v5 Typical Cadence amounts except Read volume, the Hour of day, Tool and Asset
values, and the Burst and Sweep quantities, for people, ``[bot]`` accounts and coding agents
(``actor_class``). Batch 2 (J7) measures on them the record rate against 1/(A+1), the
per-dimension organisation-ranked spend by weekday class and the record path's realised rate.

**Caller key** (spec 2.1 and 8 D5). The unit is the GitHub account (``CALLER_KEY``). For
``[bot]`` and coding-agent accounts that is the per-agent key, v5's default: their streams are
the per-agent evidence. A person's account merges every agent and client the person uses, so it
is the analog of the opt-in ``baseline_key = "user"``, not of the v5 default. Its history is
longer and denser than a per-agent key's would be, so its records are rarer: person-account
record rates are biased low against per-agent keys. No user id is assumed.

**Extract parts.** A task reads one UTC day, plus the previous day's last hour (the lookback),
which only fills windows. Per (organisation, actor) it writes up to two :class:`CadencePart`
rows, 00:00-04:00 and 04:00-24:00 UTC (``EARLY``, ``LATE``). Merging parts rebuilds a day of
either convention (``gharchive_request_sizes``): v4's UTC day, or v5's day with the 04:00
rollover in the route zone UTC, B9's fallback for an unknown zone and spec 6.1's agent-day key.
Windows are the engine's (a call at ``ts`` sees the calls in ``(ts - w, ts]``, itself included),
and every value is evaluated at every event, as the engine scores every call. A part holds:

- ``events``, ``writes``: its events and content-changing events (:data:`WRITE_EVENTS`; stars,
  forks and membership changes are calls but not writes);
- ``maxima``, per amount (the engine's dimension keys), the part's largest per-call value:
  ``calls_last_hour`` (Call rate), ``writes_last_hour`` (Write rate), ``assets_last_hour``
  (Breadth, distinct repositories; also Sweep's quantity), ``same_call_10m`` (Repetition: the
  same (tool key, repository), the tool key being ``type:action``, ``PushEvent`` without an
  action) and ``burst`` (calls in 60 s);
- ``sums``, per amount the sum of the per-call values. With ``events`` that rebuilds the
  call-weighted usual of v4 and of v5 without B7 (``memory.DailyMean``, :func:`usual_mean`);
- ``slots``, B7's input: per amount the histogram {largest value in a slot: slots} over
  clock-hour slots (Call rate, Write rate, Breadth) or 10-minute slots (Repetition), from which
  ``memory.SlotQuantile`` takes its usual (:func:`usual_slot_quantile`). An amount's strength
  (spec 2.3, v4's excess over the usual) is then computable for J7's record ranks;
- ``runs`` (:class:`RunEdges`): the edges of the part's runs (E4: a run ends after more than 30
  idle minutes). Session duration needs a run's true start, which can lie in an earlier part
  or day. :func:`iter_actor_days` carries it across parts, as ``own_session.advance`` does over
  the whole stream, so an always-on account's session grows across days;
- the actor-hour stream ``hours`` (UTC hour -> events) and ``hour_assets`` (UTC hour ->
  distinct repositories), whose keys are the active hours (Hour of day); the values ``tools``
  (tool key -> events) and ``assets`` (repository pseudonyms).

**Days.** :func:`iter_actor_days` (streaming, one UTC day at a time) and :func:`actor_days` (in
memory) stitch runs, merge parts into :class:`CadenceDay` rows and drop the days of a convention
that are incomplete: v5's first and last day of the range and the days beside a missing one.
A day's ``maxima`` and ``sums`` add ``session_length``, the E4 minutes. After a missing day,
runs start afresh, so Session duration is then a lower bound for a run that crossed it.

**Privacy:** as ``gharchive_request_sizes`` (keyed pseudonyms from ``GHARCHIVE_PSEUDONYM_KEY``
with a key check in every file; no login, name, text or GitHub id in any output). The extracts
are per-actor aggregates of day parts under pseudonyms and stay on the cluster;
:func:`summarise_cadence` publishes only cells of at least ``MIN_PUBLISH_ACTORS`` distinct
actors.

    python -m reports.experiments.dynamic_dimensions.heldout.gharchive_actor_cadence \\
        extract --day 2024-12-02 --orgs selection.json --lookback 2024-12-01-23.json.gz \\
            --out cadence/2024-12-02.json.gz 2024-12-02-{0..23}.json.gz
        summarise [--days v5|v4] --out cadence_summary.json cadence/*.json.gz
"""

from __future__ import annotations

import argparse
import math
from collections import Counter, defaultdict, deque
from collections.abc import Hashable, Iterable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from mcp_security.behaviour.clock import DAY_S, HOUR_S, is_weekend
from mcp_security.behaviour.engine import (
    ASSETS_LAST_HOUR,
    BURST,
    CALLS_LAST_HOUR,
    IDLE_GAP_S,
    MINUTE_S,
    SAME_CALL_10M,
    SAME_CALL_WINDOW_S,
    SESSION_LENGTH,
    WRITES_LAST_HOUR,
)
from mcp_security.behaviour.memory import (
    HOUR_SLOT_S,
    MIN_QUANTILE_SLOTS,
    REPETITION_SLOT_S,
    USUAL_QUANTILE,
    SlotQuantile,
    slot_of,
)
from mcp_security.gateway.pseudonym import Pseudonymizer
from reports.experiments.dynamic_dimensions.heldout.gharchive_request_sizes import (
    ACTOR_CLASSES,
    ACTOR_ROLE,
    AGENT_LOGINS,
    ALL_CLASSES,
    CALLER_KEY,
    CALLER_NOTE,
    DAY_NOTES,
    LABEL,
    MIN_PUBLISH_ACTORS,
    ORG_ROLE,
    PARTS,
    QUANTILES,
    REPO_ROLE,
    V4_DAYS,
    V5_DAYS,
    actor_class,
    actor_login,
    check_convention,
    convention_day,
    event_time,
    histogram_quantile,
    iso_day,
    iter_events,
    key_check,
    keyed_pseudonymizer,
    load_agent_logins,
    load_org_selection,
    org_login,
    parse_day,
    part_of,
    pseudonym,
    read_json,
    repo_name,
    utc_days_of,
    write_json,
)

#: Content-changing events: the "writes" of Write rate. Every other event is a call only.
WRITE_EVENTS = frozenset(
    {
        "PushEvent",
        "CreateEvent",
        "DeleteEvent",
        "IssuesEvent",
        "IssueCommentEvent",
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "PullRequestReviewCommentEvent",
        "CommitCommentEvent",
        "ReleaseEvent",
        "GollumEvent",
    }
)
LOOKBACK_S = HOUR_S  # the longest window that reaches back across midnight
WRITE_MARK = "write"  # the value the Write rate window holds (it counts, never distinguishes)
#: The amounts a part keeps the maximum of (engine keys); Sweep's quantity is Breadth's.
WINDOW_AMOUNTS = (CALLS_LAST_HOUR, WRITES_LAST_HOUR, ASSETS_LAST_HOUR, SAME_CALL_10M, BURST)
#: The amounts with a usual (Burst is a flag: its strength needs only its limit).
USUAL_AMOUNTS = (CALLS_LAST_HOUR, WRITES_LAST_HOUR, ASSETS_LAST_HOUR, SAME_CALL_10M)
#: B7: each usual's slot length (``memory.HOUR_SLOT_S``, ``memory.REPETITION_SLOT_S``).
SLOT_SECONDS = {
    CALLS_LAST_HOUR: HOUR_SLOT_S,
    WRITES_LAST_HOUR: HOUR_SLOT_S,
    ASSETS_LAST_HOUR: HOUR_SLOT_S,
    SAME_CALL_10M: REPETITION_SLOT_S,
}
#: A whole day adds the E4 Session duration (minutes) to its maxima and sums.
DAY_AMOUNTS = (*WINDOW_AMOUNTS, SESSION_LENGTH)
EVENTS, WRITES, ACTIVE_HOURS = "events", "writes", "active_hours"
DISTINCT_ASSETS, DISTINCT_TOOLS = "distinct_assets", "distinct_tools"
COUNT_AMOUNTS = (EVENTS, WRITES, ACTIVE_HOURS, DISTINCT_ASSETS, DISTINCT_TOOLS)
#: What :func:`summarise_cadence` reports quantiles of.
SUMMARY_AMOUNTS = (*DAY_AMOUNTS, *COUNT_AMOUNTS)
WEEKDAY, WEEKEND = "weekday", "weekend"
WEEKDAY_CLASSES = (WEEKDAY, WEEKEND)
ALL_DAYS = "all"
SCHEMA_CADENCE = "gharchive-actor-cadence/2"
SCHEMA_CADENCE_SUMMARY = "gharchive-actor-cadence-summary/2"


def tool_key(event: Mapping) -> str:
    """The event's tool key: ``type:action``, or ``type`` for an event without an action."""
    kind = event.get("type")
    if not isinstance(kind, str) or not kind:
        raise ValueError("event has no type")
    action = (event.get("payload") or {}).get("action")
    return f"{kind}:{action}" if isinstance(action, str) and action else kind


# ── rows ───────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RunEdges:
    """The runs (E4) of one part's events, in seconds from the start of the UTC day.

    ``runs`` counts them; the first run spans ``first_event_s`` to ``first_run_end_s`` over
    ``first_run_events`` events; the last one starts at ``last_run_start_s`` and the part's last
    event is at ``last_event_s``; ``longest_later_run_s`` is the longest run after the first (0
    with one run); ``run_s_sum`` sums, over the part's events, the seconds since the start of
    their run within the part."""

    runs: int
    first_event_s: float
    first_run_end_s: float
    first_run_events: int
    last_run_start_s: float
    last_event_s: float
    longest_later_run_s: float
    run_s_sum: float

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json`."""
        return asdict(self)

    @classmethod
    def from_json(cls, data: Mapping) -> RunEdges:
        """:meth:`to_json` output back."""
        return cls(**data)


@dataclass(frozen=True)
class CadencePart:
    """One actor's part (``EARLY`` or ``LATE``) of UTC day ``day`` in one organisation
    (pseudonyms): an extract row; see the module docstring."""

    org: str
    actor: str
    actor_class: str
    day: int
    part: int
    events: int
    writes: int
    maxima: Mapping[str, int]
    sums: Mapping[str, int]
    slots: Mapping[str, Mapping[int, int]]
    runs: RunEdges
    hours: Mapping[int, int] = field(default_factory=dict)
    hour_assets: Mapping[int, int] = field(default_factory=dict)
    tools: Mapping[str, int] = field(default_factory=dict)
    assets: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str, int, int]:
        """(organisation, actor, UTC day, part)."""
        return (self.org, self.actor, self.day, self.part)

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json` (integer keys become strings)."""
        return {
            "org": self.org,
            "actor": self.actor,
            "class": self.actor_class,
            "day": self.day,
            "part": self.part,
            "events": self.events,
            "writes": self.writes,
            "maxima": dict(sorted(self.maxima.items())),
            "sums": dict(sorted(self.sums.items())),
            "slots": {
                name: {str(v): n for v, n in sorted(hist.items())}
                for name, hist in sorted(self.slots.items())
            },
            "runs": self.runs.to_json(),
            "hours": {str(h): n for h, n in sorted(self.hours.items())},
            "hour_assets": {str(h): n for h, n in sorted(self.hour_assets.items())},
            "tools": dict(sorted(self.tools.items())),
            "assets": list(self.assets),
        }

    @classmethod
    def from_json(cls, data: Mapping) -> CadencePart:
        """:meth:`to_json` output back."""
        return cls(
            org=data["org"],
            actor=data["actor"],
            actor_class=data["class"],
            day=int(data["day"]),
            part=int(data["part"]),
            events=data["events"],
            writes=data["writes"],
            maxima=dict(data["maxima"]),
            sums=dict(data["sums"]),
            slots={
                name: {int(v): n for v, n in hist.items()} for name, hist in data["slots"].items()
            },
            runs=RunEdges.from_json(data["runs"]),
            hours={int(h): n for h, n in data["hours"].items()},
            hour_assets={int(h): n for h, n in data["hour_assets"].items()},
            tools=dict(data["tools"]),
            assets=tuple(data["assets"]),
        )


@dataclass(frozen=True)
class CadenceDay:
    """One actor's day of ``convention`` in one organisation: its parts merged, runs
    stitched. ``maxima`` and ``sums`` hold :data:`DAY_AMOUNTS` (Session duration in minutes);
    ``slots`` B7's histograms; the rest as in :class:`CadencePart`."""

    org: str
    actor: str
    actor_class: str
    day: int
    convention: str
    events: int
    writes: int
    maxima: Mapping[str, float]
    sums: Mapping[str, float]
    slots: Mapping[str, Mapping[int, int]]
    hours: Mapping[int, int]
    hour_assets: Mapping[int, int]
    tools: Mapping[str, int]
    assets: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str, int]:
        """(organisation, actor, day)."""
        return (self.org, self.actor, self.day)

    @property
    def weekday_class(self) -> str:
        """:data:`WEEKEND` when the day (of its convention) is a Saturday or a Sunday."""
        return WEEKEND if is_weekend(self.day) else WEEKDAY

    def amounts(self) -> dict[str, float]:
        """The day's value of each of :data:`SUMMARY_AMOUNTS`."""
        return {name: self.maxima[name] for name in DAY_AMOUNTS} | {
            EVENTS: self.events,
            WRITES: self.writes,
            ACTIVE_HOURS: len(self.hours),
            DISTINCT_ASSETS: len(self.assets),
            DISTINCT_TOOLS: len(self.tools),
        }


@dataclass
class CadenceExtract:
    """One UTC day's parts, with the key check and the counts of what was read and dropped."""

    day: int
    key_check: str = ""
    files_read: list[str] = field(default_factory=list)
    stats: Counter = field(default_factory=Counter)
    parts: list[CadencePart] = field(default_factory=list)

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json`."""
        return {
            "schema": SCHEMA_CADENCE,
            "label": LABEL,
            "day": self.day,
            "key_check": self.key_check,
            "files_read": sorted(self.files_read),
            "stats": dict(sorted(self.stats.items())),
            "parts": [p.to_json() for p in sorted(self.parts, key=lambda p: p.key)],
        }

    @classmethod
    def from_json(cls, data: Mapping) -> CadenceExtract:
        """:meth:`to_json` output back."""
        if data.get("schema") != SCHEMA_CADENCE:
            raise ValueError(f"not a cadence extract ({SCHEMA_CADENCE})")
        return cls(
            int(data["day"]),
            str(data["key_check"]),
            list(data["files_read"]),
            Counter(data["stats"]),
            [CadencePart.from_json(p) for p in data["parts"]],
        )


# ── extraction ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Event:
    """One kept event, pseudonymised: what the sweep needs."""

    ts: float
    order: int  # arrival order, to break timestamp ties stably
    tool: str
    write: bool
    asset: str


class _Window:
    """Events in a sliding window ``(ts - span, ts]``, with distinct-value counts."""

    def __init__(self, span: float) -> None:
        self.span = span
        self.items: deque[tuple[float, Hashable]] = deque()
        self.counts: Counter = Counter()

    def add(self, ts: float, value: Hashable) -> None:
        """Add an event at ``ts`` (non-decreasing) and drop the ones that left the window."""
        self.items.append((ts, value))
        self.counts[value] += 1
        self.expire(ts)

    def expire(self, ts: float) -> None:
        """Drop the events at or before ``ts - span`` (the engine's ``SlidingCounts.expire``)."""
        while self.items and self.items[0][0] <= ts - self.span:
            _, old = self.items.popleft()
            self.counts[old] -= 1
            if not self.counts[old]:
                del self.counts[old]

    def __len__(self) -> int:
        return len(self.items)

    def distinct(self) -> int:
        """Distinct values in the window."""
        return len(self.counts)


class _PartBuilder:
    """Folds one part's events, in time order, into a :class:`CadencePart`."""

    def __init__(self) -> None:
        self.events = 0
        self.writes = 0
        self.maxima: Counter = Counter()
        self.sums: Counter = Counter()
        self.slot_max: dict[str, dict[int, int]] = defaultdict(dict)
        self.runs = 0
        self.first_event_s = self.first_run_end_s = self.run_start_s = self.last_s = 0.0
        self.first_run_events = 0
        self.longest_later_s = self.run_s_sum = 0.0
        self.hours: Counter = Counter()
        self.hour_assets: dict[int, set[str]] = defaultdict(set)
        self.tools: Counter = Counter()
        self.assets: set[str] = set()

    def add(self, e: _Event, offset_s: float, values: Mapping[str, int]) -> None:
        """One event at ``offset_s`` seconds into the UTC day, with its window values."""
        self.events += 1
        self.writes += e.write
        for name, value in values.items():
            self.maxima[name] = max(self.maxima[name], value)
        for name in USUAL_AMOUNTS:
            value = values[name]
            self.sums[name] += value
            slots = self.slot_max[name]
            slot = slot_of(e.ts, SLOT_SECONDS[name])  # zone UTC: the wall clock is ts
            slots[slot] = max(slots.get(slot, 0), value)
        if not self.runs:
            self.runs, self.first_event_s, self.run_start_s = 1, offset_s, offset_s
        elif offset_s - self.last_s > IDLE_GAP_S:
            self.runs += 1
            self.run_start_s = offset_s
        if self.runs == 1:
            self.first_run_end_s = offset_s
            self.first_run_events += 1
        else:
            self.longest_later_s = max(self.longest_later_s, offset_s - self.run_start_s)
        self.run_s_sum += offset_s - self.run_start_s
        self.last_s = offset_s
        hour = int(offset_s // HOUR_S)
        self.hours[hour] += 1
        self.hour_assets[hour].add(e.asset)
        self.tools[e.tool] += 1
        self.assets.add(e.asset)

    def build(self, org: str, actor: str, cls_name: str, day: int, part: int) -> CadencePart:
        """The part's row."""
        return CadencePart(
            org=org,
            actor=actor,
            actor_class=cls_name,
            day=day,
            part=part,
            events=self.events,
            writes=self.writes,
            maxima={name: self.maxima[name] for name in WINDOW_AMOUNTS},
            sums={name: self.sums[name] for name in USUAL_AMOUNTS},
            slots={
                name: dict(sorted(Counter(self.slot_max[name].values()).items()))
                for name in USUAL_AMOUNTS
            },
            runs=RunEdges(
                runs=self.runs,
                first_event_s=self.first_event_s,
                first_run_end_s=self.first_run_end_s,
                first_run_events=self.first_run_events,
                last_run_start_s=self.run_start_s,
                last_event_s=self.last_s,
                longest_later_run_s=self.longest_later_s,
                run_s_sum=self.run_s_sum,
            ),
            hours=dict(sorted(self.hours.items())),
            hour_assets={h: len(r) for h, r in sorted(self.hour_assets.items())},
            tools=dict(sorted(self.tools.items())),
            assets=tuple(sorted(self.assets)),
        )


def _sweep_actor_day(
    org: str, actor: str, cls_name: str, day: int, stream: Iterable[_Event]
) -> list[CadencePart]:
    """One actor's parts of UTC ``day`` from his events (any order; those before ``day``
    only fill the windows). Empty when no event falls on ``day``."""
    start, end = day * DAY_S, (day + 1) * DAY_S
    calls, writes, minute = _Window(HOUR_S), _Window(HOUR_S), _Window(MINUTE_S)
    same: dict[tuple[str, str], _Window] = {}
    builders = {part: _PartBuilder() for part in PARTS}
    for e in sorted(stream, key=lambda x: (x.ts, x.order)):
        calls.add(e.ts, e.asset)
        minute.add(e.ts, e.asset)
        if e.write:
            writes.add(e.ts, WRITE_MARK)
        writes.expire(e.ts)  # Write rate is read at every call, writes or not
        repeat = same.get((e.tool, e.asset))
        if repeat is None:
            repeat = same[(e.tool, e.asset)] = _Window(SAME_CALL_WINDOW_S)
        repeat.add(e.ts, e.asset)
        if not start <= e.ts < end:
            continue
        values = {
            CALLS_LAST_HOUR: len(calls),
            WRITES_LAST_HOUR: len(writes),
            ASSETS_LAST_HOUR: calls.distinct(),
            SAME_CALL_10M: len(repeat),
            BURST: len(minute),
        }
        builders[part_of(e.ts)].add(e, e.ts - start, values)
    return [b.build(org, actor, cls_name, day, p) for p, b in builders.items() if b.events]


def extract_cadence(
    events: Iterable[Mapping],
    pseudonymizer: Pseudonymizer,
    day: int,
    *,
    lookback: Iterable[Mapping] = (),
    orgs: frozenset[str] | None = None,
    exclude_orgs: Iterable[str] = (),
    agent_logins: Iterable[str] = AGENT_LOGINS,
) -> CadenceExtract:
    """Every actor's parts of UTC ``day`` in an organisation repository. ``events`` are the
    day's files and ``lookback`` the hour before; events in the hour before ``day`` fill the
    windows, earlier and later ones are dropped and counted. ``orgs`` (pseudonyms) keeps only
    those organisations (None: all), ``exclude_orgs`` drops some."""
    out = CadenceExtract(day, key_check(pseudonymizer))
    stats = out.stats
    start, end = day * DAY_S, (day + 1) * DAY_S
    excluded = frozenset(exclude_orgs)
    agents = frozenset(name.lower() for name in agent_logins)
    names: dict[tuple[str, str], str] = {}  # (role, name) -> pseudonym, in memory only
    streams: dict[tuple[str, str], list[_Event]] = defaultdict(list)
    classes: dict[tuple[str, str], str] = {}

    def named(role: str, value: str) -> str:
        found = names.get((role, value))
        if found is None:
            found = names[(role, value)] = pseudonym(pseudonymizer, role, value)
        return found

    order = 0
    for source, stream in (("lookback", lookback), ("day", events)):
        for event in stream:
            stats[f"{source}_events"] += 1
            org = org_login(event)
            if org is None:
                stats["no_org"] += 1
                continue
            org_p = named(ORG_ROLE, org)
            if org_p in excluded or (orgs is not None and org_p not in orgs):
                stats["other_org"] += 1
                continue
            try:
                ts, login = event_time(event), actor_login(event)
                tool, repo = tool_key(event), repo_name(event)
            except ValueError:
                stats["bad_events"] += 1
                continue
            if not start - LOOKBACK_S <= ts < end:
                stats["outside_day"] += 1
                continue
            key = (org_p, named(ACTOR_ROLE, login))
            classes.setdefault(key, actor_class(login, agents))
            write = tool.split(":", 1)[0] in WRITE_EVENTS
            streams[key].append(_Event(ts, order, tool, write, named(REPO_ROLE, repo)))
            order += 1
    for (org_p, actor_p), stream in sorted(streams.items()):
        out.parts.extend(_sweep_actor_day(org_p, actor_p, classes[(org_p, actor_p)], day, stream))
    return out


# ── days: stitched runs, merged parts ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class PartSession:
    """E4 over one part, with its first run's true start carried in: the part's longest
    Session duration and the sum over its events, in minutes."""

    longest: float
    total: float


@dataclass(frozen=True)
class _Carry:
    """Where one actor's latest run stands after a part (absolute seconds)."""

    last_event: float
    run_start: float


def _session(
    part: CadencePart, carry: _Carry | None, idle_gap_s: float
) -> tuple[PartSession, _Carry]:
    """The part's E4 values given the carry from the actor's previous part, and the carry
    after it. The first run continues the carried one when the idle time from its last event is
    at most ``idle_gap_s`` (``own_session.continues``)."""
    edges, base = part.runs, part.day * DAY_S
    first = base + edges.first_event_s
    continued = carry is not None and first - carry.last_event <= idle_gap_s
    start = carry.run_start if continued else first
    shift = first - start
    first_run = edges.first_run_end_s - edges.first_event_s + shift
    longest = max(first_run, edges.longest_later_run_s)
    total = edges.run_s_sum + edges.first_run_events * shift
    last_start = start if edges.runs == 1 else base + edges.last_run_start_s
    return (
        PartSession(longest / MINUTE_S, total / MINUTE_S),
        _Carry(base + edges.last_event_s, last_start),
    )


def stitch_runs(stream: Sequence[CadencePart], idle_gap_s: float = IDLE_GAP_S) -> list[PartSession]:
    """E4 Session duration over one (organisation, actor) stream of parts in time order: each
    part's :class:`PartSession`, its first run's start carried across parts and days, as
    ``own_session.advance`` does over the whole stream. ``ValueError`` for parts out of order
    or of several actors."""
    out: list[PartSession] = []
    carry: _Carry | None = None
    previous: tuple[int, int] | None = None
    for part in stream:
        if previous is not None and (part.day, part.part) <= previous:
            raise ValueError("stitch_runs needs one actor's parts in time order")
        if out and (part.org, part.actor) != (stream[0].org, stream[0].actor):
            raise ValueError("stitch_runs needs one (organisation, actor) stream")
        session, carry = _session(part, carry, idle_gap_s)
        out.append(session)
        previous = (part.day, part.part)
    return out


def _merge(
    day: int, convention: str, items: Sequence[tuple[CadencePart, PartSession]]
) -> CadenceDay:
    """One actor's parts of one day, in time order, as a :class:`CadenceDay`."""
    parts = [p for p, _ in items]
    maxima: dict[str, float] = {name: max(p.maxima[name] for p in parts) for name in WINDOW_AMOUNTS}
    maxima[SESSION_LENGTH] = max(s.longest for _, s in items)
    sums: dict[str, float] = {name: sum(p.sums[name] for p in parts) for name in USUAL_AMOUNTS}
    sums[SESSION_LENGTH] = math.fsum(s.total for _, s in items)
    slots: dict[str, Counter] = defaultdict(Counter)
    hours: Counter = Counter()
    hour_assets: dict[int, int] = {}
    tools: Counter = Counter()
    assets: set[str] = set()
    for p in parts:
        for name, hist in p.slots.items():
            slots[name].update(hist)
        hours.update(p.hours)
        hour_assets.update(p.hour_assets)  # an hour lies in one part
        tools.update(p.tools)
        assets.update(p.assets)
    first = parts[0]
    return CadenceDay(
        org=first.org,
        actor=first.actor,
        actor_class=first.actor_class,
        day=day,
        convention=convention,
        events=sum(p.events for p in parts),
        writes=sum(p.writes for p in parts),
        maxima=maxima,
        sums=sums,
        slots={name: dict(sorted(slots[name].items())) for name in USUAL_AMOUNTS},
        hours=dict(sorted(hours.items())),
        hour_assets=dict(sorted(hour_assets.items())),
        tools=dict(sorted(tools.items())),
        assets=tuple(sorted(assets)),
    )


Batch = tuple[int, Sequence[CadencePart] | None]


def iter_actor_days(
    batches: Iterable[Batch],
    convention: str = V5_DAYS,
    *,
    idle_gap_s: float = IDLE_GAP_S,
) -> Iterator[CadenceDay]:
    """Stream the :class:`CadenceDay` rows of ``convention`` from ``batches``: one per UTC
    day, consecutive and in order, each ``(day, its parts)``, or ``(day, None)`` for a day
    that was not read (:func:`read_batches`). Rows come out a day at a time, sorted by
    (organisation, actor). Runs are stitched across parts and days; a missing day ends every
    run. A day is yielded only when every UTC day it spans was read. Memory holds a day's
    parts and the actors active in the last ``idle_gap_s`` before midnight."""
    check_convention(convention)
    carries: dict[tuple[str, str], _Carry] = {}
    pending: dict[int, dict[tuple[str, str], list]] = defaultdict(lambda: defaultdict(list))
    read: set[int] = set()
    previous: int | None = None
    for day, parts in batches:
        if previous is not None and day != previous + 1:
            raise ValueError(f"batches must be consecutive UTC days: {day} after {previous}")
        previous = day
        if parts is None:
            carries.clear()  # nobody's run can be followed across a day nobody read
        else:
            read.add(day)
            for part in sorted(parts, key=lambda p: p.key):
                if part.day != day:
                    raise ValueError(f"a part of UTC day {part.day} in the batch of day {day}")
                who = (part.org, part.actor)
                session, carries[who] = _session(part, carries.get(who), idle_gap_s)
                target = convention_day(part.day, part.part, convention)
                pending[target][who].append((part, session))
        done = day if convention == V4_DAYS else day - 1  # no later part reaches these days
        for target in sorted(t for t in pending if t <= done):
            group = pending.pop(target)
            if read.issuperset(utc_days_of(target, convention)):
                for who in sorted(group):
                    yield _merge(target, convention, group[who])
        horizon = (day + 1) * DAY_S - idle_gap_s  # no run ending before this continues
        for who in [w for w, c in carries.items() if c.last_event < horizon]:
            del carries[who]


def read_batches(paths: Iterable[str | Path]) -> Iterator[Batch]:
    """The parts of extract files as :func:`iter_actor_days` batches. The files must come in
    UTC day order (``YYYY-MM-DD`` names sort so); a day missing between two files becomes
    ``(day, None)``. ``ValueError`` for a day read twice or out of order, or files made under
    different pseudonym keys."""
    previous: int | None = None
    check: str | None = None
    for path in paths:
        extract = CadenceExtract.from_json(read_json(path))
        if check is not None and extract.key_check != check:
            raise ValueError(f"{path} was made under another pseudonym key than the files before")
        check = extract.key_check
        if previous is not None:
            if extract.day <= previous:
                raise ValueError(f"{path}: UTC day {extract.day} is out of order or read twice")
            for missing in range(previous + 1, extract.day):
                yield missing, None
        previous = extract.day
        yield extract.day, extract.parts


def load_cadence(paths: Iterable[str | Path]) -> list[CadencePart]:
    """The parts of several extract files, in memory (small runs and tests);
    ``ValueError`` if one part appears twice (each day must be extracted once)."""
    seen: dict[tuple[str, str, int, int], CadencePart] = {}
    for path in paths:
        for row in CadenceExtract.from_json(read_json(path)).parts:
            if row.key in seen:
                raise ValueError(f"actor-day part extracted twice (day {row.day}) in {path}")
            seen[row.key] = row
    return [seen[key] for key in sorted(seen)]


def actor_days(
    parts: Iterable[CadencePart],
    convention: str = V5_DAYS,
    *,
    utc_range: tuple[int, int] | None = None,
    idle_gap_s: float = IDLE_GAP_S,
) -> list[CadenceDay]:
    """:func:`iter_actor_days` over parts held in memory, as if every UTC day of
    ``utc_range`` (default: the parts' first to last day) was read. ``ValueError`` when a
    part lies outside ``utc_range``."""
    rows = list(parts)
    if not rows:
        return []
    first, last = utc_range or (min(p.day for p in rows), max(p.day for p in rows))
    by_day: dict[int, list[CadencePart]] = defaultdict(list)
    for row in rows:
        if not first <= row.day <= last:
            raise ValueError(f"a part of UTC day {row.day} outside the range {first}-{last}")
        by_day[row.day].append(row)
    batches = ((day, by_day.get(day, [])) for day in range(first, last + 1))
    return list(iter_actor_days(batches, convention, idle_gap_s=idle_gap_s))


def actor_streams(
    parts: Iterable[CadencePart], convention: str = V5_DAYS
) -> dict[tuple[str, str], list[CadenceDay]]:
    """(organisation, actor) -> his days of ``convention`` in day order, runs stitched: one
    GitHub account's history, which the v5 commonness compares a day with (J7's checks). Per
    spec 8 D5 a ``[bot]`` or agent account's stream is a per-agent history and a person's is
    the per-user (opt-in) analog; see the module docstring."""
    out: dict[tuple[str, str], list[CadenceDay]] = defaultdict(list)
    for row in actor_days(parts, convention):
        out[(row.org, row.actor)].append(row)
    return {who: sorted(days, key=lambda d: d.day) for who, days in out.items()}


# ── usuals: rebuilding the engine's from the days ──────────────────────────────────────────


def usual_mean(days: Iterable[CadenceDay], amount: str) -> float | None:
    """The call-weighted usual of ``amount`` over ``days`` (the caller's past days in the
    window): the sum of its per-call values over their calls, as ``memory.DailyMean`` keeps it
    (v4; v5 without B7). None for no call."""
    rows = list(days)
    calls = sum(d.events for d in rows)
    return math.fsum(d.sums[amount] for d in rows) / calls if calls else None


def usual_slot_quantile(
    days: Iterable[CadenceDay],
    amount: str,
    quantile: float = USUAL_QUANTILE,
    min_slots: int = MIN_QUANTILE_SLOTS,
) -> float | None:
    """B7's usual of ``amount`` over ``days`` (the caller's past days in the window): the
    ``quantile`` of his slot maxima, taken by ``memory.SlotQuantile`` itself from the days'
    slot histograms. None for no active slot. ``amount`` is one of :data:`USUAL_AMOUNTS`."""
    if amount not in SLOT_SECONDS:
        raise ValueError(f"B7 has no usual for {amount!r}")
    snapshot = {
        "by_day": [[d.day, sorted(d.slots[amount].items())] for d in days if d.slots.get(amount)],
        "open_day": None,
        "open": [],
    }
    return SlotQuantile.from_json(snapshot, quantile, min_slots).usual()


# ── the publishable summary ────────────────────────────────────────────────────────────────


#: The summary's cells, (actor class or all, weekday class or all), and each one's bit.
CELLS = tuple(
    (cls_name, week)
    for cls_name in (*ACTOR_CLASSES, ALL_CLASSES)
    for week in (*WEEKDAY_CLASSES, ALL_DAYS)
)
CELL_BITS = {cell: 1 << i for i, cell in enumerate(CELLS)}


def summarise_cadence(
    days: Iterable[CadenceDay],
    quantiles: Sequence[float] = QUANTILES,
    min_actors: int = MIN_PUBLISH_ACTORS,
) -> dict:
    """The publishable X2 summary, streamed: per actor class and weekday class (each also
    pooled as ``all``), the distinct actors, organisations and actor-days, and nearest-rank
    quantiles of each of :data:`SUMMARY_AMOUNTS`. A cell of fewer than ``min_actors`` distinct
    actors shows only that it was suppressed. Memory holds one histogram per cell and amount
    and one bit mask per actor and organisation. ``ValueError`` for days of two conventions."""
    histograms: dict[tuple[str, str], dict[str, Counter]] = {
        cell: {amount: Counter() for amount in SUMMARY_AMOUNTS} for cell in CELLS
    }
    day_counts: Counter = Counter()
    actor_cells: dict[tuple[str, str], int] = defaultdict(int)
    org_cells: dict[str, int] = defaultdict(int)
    conventions: set[str] = set()
    for row in days:
        conventions.add(row.convention)
        values = row.amounts()
        for cls_name in (row.actor_class, ALL_CLASSES):
            for week in (row.weekday_class, ALL_DAYS):
                cell = (cls_name, week)
                day_counts[cell] += 1
                actor_cells[(row.org, row.actor)] |= CELL_BITS[cell]
                org_cells[row.org] |= CELL_BITS[cell]
                for amount, value in values.items():
                    histograms[cell][amount][value] += 1
    if len(conventions) > 1:
        raise ValueError(f"days of several conventions: {sorted(conventions)}")
    (convention,) = conventions or {V5_DAYS}
    out: dict = {}
    for cell in CELLS:
        bit = CELL_BITS[cell]
        actors = sum(1 for mask in actor_cells.values() if mask & bit)
        cls_name, week = cell
        if actors < min_actors:
            out.setdefault(cls_name, {})[week] = {"suppressed": True}
            continue
        out.setdefault(cls_name, {})[week] = {
            "actors": actors,
            "orgs": sum(1 for mask in org_cells.values() if mask & bit),
            "actor_days": day_counts[cell],
            "quantiles": {
                amount: {f"q{q}": histogram_quantile(hist, q) for q in quantiles}
                for amount, hist in histograms[cell].items()
            },
        }
    return {
        "schema": SCHEMA_CADENCE_SUMMARY,
        "label": LABEL,
        "caller_key": CALLER_KEY,
        "caller_note": CALLER_NOTE,
        "days": DAY_NOTES[convention],
        "convention": convention,
        "min_publish_actors": min_actors,
        "cells": out,
    }


# ── command line ───────────────────────────────────────────────────────────────────────────


def _command_extract(args: argparse.Namespace) -> None:
    read_stats: Counter = Counter()
    pseudonymizer = keyed_pseudonymizer()
    extract = extract_cadence(
        iter_events(args.files, read_stats),
        pseudonymizer,
        parse_day(args.day),
        lookback=iter_events(args.lookback or (), read_stats),
        orgs=load_org_selection(args.orgs, pseudonymizer) if args.orgs else None,
        exclude_orgs=load_org_selection(args.exclude_orgs, pseudonymizer)
        if args.exclude_orgs
        else (),
        agent_logins=load_agent_logins(args.agents),
    )
    extract.stats.update(read_stats)
    extract.files_read = [Path(f).name for f in (*args.files, *(args.lookback or ()))]
    write_json(args.out, extract.to_json())


def _command_summarise(args: argparse.Namespace) -> None:
    days_seen: list[int] = []
    missing: list[int] = []

    def batches() -> Iterator[Batch]:
        for day, parts in read_batches(sorted(args.parts)):
            days_seen.append(day)
            if parts is None:
                missing.append(day)
            yield day, parts

    summary = summarise_cadence(iter_actor_days(batches(), args.days))
    summary["utc_days"] = {
        "first": iso_day(days_seen[0]) if days_seen else None,
        "last": iso_day(days_seen[-1]) if days_seen else None,
        "missing": [iso_day(d) for d in missing],
    }
    write_json(args.out, summary)


def build_parser() -> argparse.ArgumentParser:
    """The command line (see the module docstring)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract", help="actor day parts of one UTC day from hourly files")
    extract.add_argument("files", nargs="+", help="the day's GH Archive hourly files")
    extract.add_argument("--day", required=True, help="the UTC day, YYYY-MM-DD")
    extract.add_argument(
        "--lookback", action="append", help="the previous day's last hour file (repeatable)"
    )
    extract.add_argument("--orgs", help="keep only this selection's organisations")
    extract.add_argument("--exclude-orgs", help="drop this selection's organisations")
    extract.add_argument("--agents", help="file of coding-agent logins (default AGENT_LOGINS)")
    extract.add_argument("--out", required=True)
    summary = sub.add_parser("summarise", help="publishable aggregates from extract parts")
    summary.add_argument("parts", nargs="+", help="extract files, one per UTC day")
    summary.add_argument("--days", choices=(V5_DAYS, V4_DAYS), default=V5_DAYS)
    summary.add_argument("--out", required=True)
    return parser


COMMANDS = {"extract": _command_extract, "summarise": _command_summarise}


def main(argv: Sequence[str] | None = None) -> None:
    """Run one stage."""
    args = build_parser().parse_args(argv)
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
