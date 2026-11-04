"""Which agent-days go on the study's cards and pairs (pure functions, no simulator needed).

Sixteen scored cards in five strata, chosen from the v4 engine's daily review list (top 4
agent-days a day):

- ``A`` caught: a gray agent-day on the list, 4, each a different gray kind;
- ``B`` false alarm: an ordinary agent-day on the list, 3, each a different strongest dimension;
- ``C`` missed: a gray agent-day not on the list, 3, each a different gray kind;
- ``D`` life or org change: a labelled benign change day, 3, at least one at x3 or more and one
  below, each a different change;
- ``E`` plain: an ordinary agent-day not on the list with ``M <= 1``, 3.

"On the list" means sure to be on it (``chance == 1``), "not on the list" sure to be off it
(``chance == 0``): agent-days tied at the cut are never used. An agent-day is usable only when all
its actions fall on one date of the owner's own calendar, the server's day itself, so the weekday
and the hours on a card always describe the same local day. No agent appears twice. Within a
stratum the picks spread over roles and weekdays; at least one gray card falls on a day with a
company note, so a note is never a cue for "benign"; gray kinds differ across A and C where they
can; C takes kinds the engine usually misses; at least one non-gray card falls on a weekend, so a
weekend is never a cue for "gray"; and at least one false alarm has no latent benign cause (see
``study_notes.latent_cause``).

The eight same-day pairs are ``study_pairs.py``; ids and the card order are here too.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")

GRAY, CHANGE, ORDINARY = "gray", "change", "ordinary"
STRATA: dict[str, int] = {"A": 4, "B": 3, "C": 3, "D": 3, "E": 3}
STRATUM_NAMES = {
    "A": "listed gray (caught)",
    "B": "listed ordinary (false alarm)",
    "C": "gray not listed (missed)",
    "D": "benign life or org change",
    "E": "plain ordinary",
}
ALERT = 3.0  # x3: the alert line of the simulation
ORDINARY_CEILING = 1.0  # stratum E: M at most x1
LIST_SIZE = 4
MIN_HISTORY_DAYS = 10  # active days in its 90-day window, so "usual" means something
#: gray kinds a card cannot show: over-fetching is the page size of list calls, not recorded
HIDDEN_GRAY_KINDS = frozenset({"overfetch"})
#: kinds the engine usually misses (v4, main org: listed on 6%, 11% and 17% of their days), whose
#: signal a card shows (projects new to it, many changes, a sensitive project read then a write)
PREFERRED_MISSED = ("scope_creep", "mass_cleanup", "cross_copy")
#: strongest dimensions the card's rows show; session length, risky order and the skipped
#: hello have no row of their own
VISIBLE_CAUSES = frozenset(
    {
        "calls_last_hour",
        "time_of_day",
        "same_call_10m",
        "writes_last_hour",
        "assets_last_hour",
        "tool",
        "asset",
        "network",
        "client",
        "burst",
        "many_assets",
        "request_too_big",
    }
)
#: change labels for stratum D, most telling first
CHANGE_TAGS = (
    "back_from_vacation",
    "travel",
    "new_hire",
    "team_transfer",
    "role_change",
    "client_switch",
    "isp_change",
    "on_call_incident",
    "release_crunch",
    "org_vpn_change",
    "org_tool_rollout",
    "org_repo_migration",
    "monthly_report",
    "new_project",
)
#: change label -> the dimensions that change moves (D prefers a day the change itself lifted)
CHANGE_CAUSES: dict[str, frozenset[str]] = {
    "back_from_vacation": frozenset({"calls_last_hour", "session_length", "asset", "tool"}),
    "travel": frozenset({"time_of_day", "network"}),
    "new_hire": frozenset({"tool", "asset", "sequence", "assets_last_hour"}),
    "team_transfer": frozenset({"asset", "assets_last_hour", "many_assets"}),
    "role_change": frozenset({"tool", "asset", "writes_last_hour"}),
    "client_switch": frozenset({"client", "protocol_skip"}),
    "isp_change": frozenset({"network"}),
    "on_call_incident": frozenset({"time_of_day", "session_length", "asset"}),
    "release_crunch": frozenset({"time_of_day", "session_length", "calls_last_hour"}),
    "org_vpn_change": frozenset({"network"}),
    "org_tool_rollout": frozenset({"tool"}),
    "org_repo_migration": frozenset({"asset", "assets_last_hour", "many_assets"}),
    "monthly_report": frozenset({"calls_last_hour", "assets_last_hour", "many_assets"}),
    "new_project": frozenset({"asset"}),
}
#: change labels that say little about the day (D prefers the others)
WEAK_CHANGES = frozenset({"new_project", "monthly_report"})
MAX_BOT_CARDS, MAX_BOTS_PER_STRATUM = 3, 1  # bots are 14% of agents; keep them a minority
ROLE_WEIGHT, WEEKDAY_WEIGHT, PREFERENCE_BONUS = 1.0, 1.0, 3.0
ID_HEX = 4
MAX_SHUFFLES = 10_000
DAYS_PER_WEEK = 7
WEEKEND_DAYS = frozenset({5, 6})


@dataclass(frozen=True)
class AgentDay:
    """One scored agent-day and its labels, as selection sees it."""

    agent: str
    day: int
    role: str
    multiplier: float
    risk: float
    strongest: str | None
    second: float
    above_ordinary: tuple[str, ...]
    rank: int
    chance: float
    tags: tuple[str, ...] = ()
    gray_kinds: tuple[str, ...] = ()
    history_days: int = 0
    org_event: str | None = None
    actions: int = 0  # tool calls that day (a day can hold only handshakes)
    local_dates: tuple[int, ...] = ()  # the owner's calendar dates its actions fall on
    latent_cause: str | None = None  # a benign change the simulator did not label that day

    @property
    def key(self) -> tuple[str, int]:
        return (self.agent, self.day)

    @property
    def category(self) -> str:
        return GRAY if self.gray_kinds else CHANGE if self.tags else ORDINARY

    @property
    def listed(self) -> bool:
        return self.chance >= 1.0

    @property
    def unlisted(self) -> bool:
        return self.chance <= 0.0

    @property
    def weekday(self) -> int:
        return self.day % DAYS_PER_WEEK

    @property
    def is_weekend(self) -> bool:
        return self.weekday in WEEKEND_DAYS

    @property
    def gray_kind(self) -> str | None:
        return self.gray_kinds[0] if self.gray_kinds else None

    @property
    def change_tag(self) -> str | None:
        return next((t for t in CHANGE_TAGS if t in self.tags), None)

    @property
    def usable(self) -> bool:
        """Enough history for "usual" to mean something, at least one action today, and every
        action on the owner's own calendar date of the day (the card's weekday and hours agree)."""
        return (
            self.history_days >= MIN_HISTORY_DAYS
            and self.actions > 0
            and self.local_dates == (self.day,)
        )

    @property
    def is_bot(self) -> bool:
        return "bot" in self.role


@dataclass
class Usage:
    """What the picks so far used: agents, agent-days, roles and weekdays."""

    agents: set[str] = field(default_factory=set)
    keys: set[tuple[str, int]] = field(default_factory=set)
    roles: Counter = field(default_factory=Counter)
    weekdays: Counter = field(default_factory=Counter)
    bots: int = 0
    gray_with_note: bool = False
    gray_kinds: set[str | None] = field(default_factory=set)
    weekend_other: int = 0  # non-gray picks on a weekend

    def take(self, day: AgentDay) -> None:
        self.agents.add(day.agent)
        self.keys.add(day.key)
        self.roles[day.role] += 1
        self.weekdays[day.weekday] += 1
        self.bots += day.is_bot
        if day.category == GRAY:
            self.gray_kinds.add(day.gray_kind)
            self.gray_with_note = self.gray_with_note or bool(day.org_event)
        elif day.is_weekend:
            self.weekend_other += 1

    def free(self, day: AgentDay) -> bool:
        return day.agent not in self.agents and day.key not in self.keys


@dataclass(frozen=True)
class Pick:
    """A scored card: its stratum and agent-day."""

    stratum: str
    day: AgentDay


def seeded_order(items: Iterable[AgentDay], rng: random.Random) -> list[AgentDay]:
    """A fixed shuffle: sorted first, so the input order never matters."""
    out = sorted(items, key=lambda d: d.key)
    rng.shuffle(out)
    return out


def pick_spread(
    candidates: Sequence[AgentDay],
    n: int,
    usage: Usage,
    distinct: Callable[[AgentDay], object],
    prefer: Callable[[AgentDay, Usage], int] = lambda d, u: 0,
    allowed: Callable[[AgentDay, list[AgentDay]], bool] = lambda d, chosen: True,
) -> list[AgentDay]:
    """``n`` picks, one at a time: each a new ``distinct`` value and a free agent, the cheapest in
    roles and weekdays already used (each point of ``prefer`` lowers the cost), with few bots.
    ``candidates`` is in a seeded order, which breaks ties."""
    chosen: list[AgentDay] = []
    for _ in range(n):
        seen = {distinct(d) for d in chosen}
        bots_full = (
            usage.bots >= MAX_BOT_CARDS or sum(c.is_bot for c in chosen) >= MAX_BOTS_PER_STRATUM
        )
        best, best_cost = None, None
        for d in candidates:
            if not usage.free(d) or distinct(d) in seen or not allowed(d, chosen):
                continue
            if d.is_bot and bots_full:
                continue
            cost = ROLE_WEIGHT * usage.roles[d.role] + WEEKDAY_WEIGHT * usage.weekdays[d.weekday]
            cost -= PREFERENCE_BONUS * prefer(d, usage)
            if best_cost is None or cost < best_cost:
                best, best_cost = d, cost
        if best is None:
            raise ValueError(f"only {len(chosen)} of {n} picks found")
        chosen.append(best)
        usage.take(best)
    return chosen


def gray_note_wanted(day: AgentDay, usage: Usage) -> int:
    """Prefer a gray day with a company note until one is chosen."""
    return int(bool(day.org_event) and not usage.gray_with_note)


def weekend_wanted(day: AgentDay, usage: Usage) -> int:
    """Prefer a non-gray weekend day until one is chosen."""
    return int(day.is_weekend and not usage.weekend_other)


def caught_first(day: AgentDay, usage: Usage) -> int:
    """A: a note still wanted."""
    return gray_note_wanted(day, usage)


def shown_gray(day: AgentDay) -> bool:
    """A gray day whose kind the card can show."""
    return day.category == GRAY and day.gray_kind not in HIDDEN_GRAY_KINDS


def select_cards(days: Iterable[AgentDay], rng: random.Random, usage: Usage) -> list[Pick]:
    """The sixteen scored cards (see the module docstring)."""
    pool = seeded_order([d for d in days if d.usable], rng)
    caught = [d for d in pool if shown_gray(d) and d.listed]
    false_alarms = [d for d in pool if d.category == ORDINARY and d.listed]
    missed = [d for d in pool if shown_gray(d) and d.unlisted]
    changes = [d for d in pool if d.category == CHANGE and d.change_tag]
    plain = [
        d
        for d in pool
        if d.category == ORDINARY and d.unlisted and d.multiplier <= ORDINARY_CEILING
    ]

    def missed_first(d: AgentDay, u: Usage) -> int:
        """C: a kind the engine usually misses, missed by the alert line too, a kind A did not
        use, or a note still wanted."""
        return (
            (d.gray_kind in PREFERRED_MISSED)
            + (d.multiplier < ALERT)
            + (d.gray_kind not in u.gray_kinds)
            + gray_note_wanted(d, u)
        )

    def real_alarm(d: AgentDay, u: Usage) -> int:
        """B: a cause the card shows, at the alert line (most false alarms are), with no latent
        benign cause, or a weekend still wanted."""
        return (
            (d.strongest in VISIBLE_CAUSES)
            + (d.multiplier >= ALERT)
            + (d.latent_cause is None)
            + weekend_wanted(d, u)
        )

    def one_without_cause(d: AgentDay, chosen: list[AgentDay]) -> bool:
        """B: the last pick must have no latent cause if none so far is free of one."""
        last = len(chosen) == STRATA["B"] - 1
        return not last or any(c.latent_cause is None for c in chosen) or d.latent_cause is None

    def telling_change(d: AgentDay, u: Usage) -> int:
        """D: a change that says something, and that set the day's score itself."""
        lifted = d.multiplier <= ORDINARY_CEILING or d.strongest in CHANGE_CAUSES[d.change_tag]
        return (d.change_tag not in WEAK_CHANGES) + lifted + weekend_wanted(d, u)

    def both_sides(d: AgentDay, chosen: list[AgentDay]) -> bool:
        """D: the last pick must supply whichever side of x3 is still missing."""
        high = sum(c.multiplier >= ALERT for c in chosen)
        low = len(chosen) - high
        remaining = STRATA["D"] - len(chosen)
        if remaining == 1 and high == 0:
            return d.multiplier >= ALERT
        if remaining == 1 and low == 0:
            return d.multiplier < ALERT
        return True

    picks = [Pick("A", d) for d in pick_spread(caught, STRATA["A"], usage, _kind, caught_first)]
    picks += [Pick("C", d) for d in pick_spread(missed, STRATA["C"], usage, _kind, missed_first)]
    picks += [
        Pick("B", d)
        for d in pick_spread(
            false_alarms, STRATA["B"], usage, _cause, real_alarm, one_without_cause
        )
    ]
    picks += [
        Pick("D", d)
        for d in pick_spread(changes, STRATA["D"], usage, _tag, telling_change, both_sides)
    ]
    picks += [Pick("E", d) for d in pick_spread(plain, STRATA["E"], usage, _agent, weekend_wanted)]
    return picks


def _kind(day: AgentDay) -> object:
    return day.gray_kind


def _cause(day: AgentDay) -> object:
    return day.strongest


def _tag(day: AgentDay) -> object:
    return day.change_tag


def _agent(day: AgentDay) -> object:
    return day.agent


def opaque_id(prefix: str, parts: Sequence[object], taken: set[str]) -> str:
    """``prefix`` + 4 hex characters of a hash of ``parts``; rehashed on a collision."""
    salt = 0
    while True:
        text = "|".join(str(p) for p in (*parts, salt))
        candidate = prefix + hashlib.sha256(text.encode()).hexdigest()[:ID_HEX]
        if candidate not in taken:
            taken.add(candidate)
            return candidate
        salt += 1


def shuffle_apart(items: Sequence[T], group: Callable[[T], object], rng: random.Random) -> list[T]:
    """A seeded shuffle in which no two neighbours share a ``group`` (hand-built attention
    cards are their own group each)."""
    out = list(items)
    for _ in range(MAX_SHUFFLES):
        rng.shuffle(out)
        if all(group(a) != group(b) for a, b in zip(out, out[1:])):
            return out
    raise ValueError("no shuffle keeps the groups apart")
