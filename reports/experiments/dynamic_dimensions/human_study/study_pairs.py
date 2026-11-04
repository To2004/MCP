"""Eight same-day pairs for the study: the reviewer's real choice on one day.

Each pair is two agent-days of the same day, none reused from the cards (no agent twice):

- ``gray_over_ordinary`` (3): the engine prefers a listed gray day over the unlisted ordinary
  day closest to the cut;
- ``false_alarm_over_gray`` (3): it prefers a listed false alarm over an unlisted gray day (the
  engine is wrong);
- ``rank1_vs_rank4`` (2): both are listed, rank 1 against rank 4.

The preferred agent-day is the one higher on the engine's list. The engine must prefer it by a
clear margin: its M at least ``MIN_MARGIN`` times the other's. A pair type that cannot be filled
with that margin falls back to any margin above an exact tie on M (never a tie decided by s2
alone); ``rank1_vs_rank4`` never falls back. The key stores each pair's margin and whether it
is close, and the analysis reports close pairs apart. Gray kinds already on the cards are
avoided where possible, so the pairs add kinds rather than repeat them.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from study_select import GRAY, LIST_SIZE, ORDINARY, AgentDay, Usage, shown_gray

PAIR_TYPES: dict[str, int] = {
    "gray_over_ordinary": 3,
    "false_alarm_over_gray": 3,
    "rank1_vs_rank4": 2,
}
#: M of the preferred card over M of the other: below this the pair is "close" (a coin flip)
MIN_MARGIN = 1.25
MARGIN_DIGITS = 4  # M is compared as the key rounds it
#: pair types that never fall back to a close pair
STRICT_MARGIN_TYPES = frozenset({"rank1_vs_rank4"})


@dataclass(frozen=True)
class Pair:
    """Two agent-days of one day; ``preferred`` is the one higher on the engine's list."""

    pair_type: str
    preferred: AgentDay
    other: AgentDay

    @property
    def gray(self) -> AgentDay | None:
        return next((d for d in (self.preferred, self.other) if d.category == GRAY), None)

    @property
    def margin(self) -> float:
        """M of the preferred card over M of the other."""
        return margin_of(self.preferred, self.other)

    @property
    def tie_on_m(self) -> bool:
        """Both cards have the same M (the list order was set by s2)."""
        return round(self.preferred.multiplier, MARGIN_DIGITS) == round(
            self.other.multiplier, MARGIN_DIGITS
        )

    @property
    def close(self) -> bool:
        """The engine barely prefers one card."""
        return self.margin < MIN_MARGIN


def margin_of(preferred: AgentDay, other: AgentDay) -> float:
    """``M_preferred / M_other`` as the key rounds them."""
    high = round(preferred.multiplier, MARGIN_DIGITS)
    low = round(other.multiplier, MARGIN_DIGITS)
    return high / low if low > 0 else float("inf")


def clear_enough(preferred: AgentDay, other: AgentDay, wide: bool) -> bool:
    """A wide margin (``MIN_MARGIN``) when ``wide``, else anything above an exact tie on M."""
    margin = margin_of(preferred, other)
    return margin >= MIN_MARGIN if wide else margin > 1.0


@dataclass
class PairVariety:
    """What the pairs so far used: gray kinds (per pair type and overall) and alarm causes."""

    kinds: set[str | None] = field(default_factory=set)
    kinds_by_type: dict[str, set[str | None]] = field(default_factory=lambda: defaultdict(set))
    causes: set[str | None] = field(default_factory=set)
    card_kinds: set[str | None] = field(default_factory=set)  # gray kinds on the cards

    def avoid(self, pair_type: str, level: int) -> tuple[set, set]:
        """(gray kinds, alarm causes) to avoid: at ``FULL_VARIETY`` every kind the cards and the
        pairs used, at ``TYPE_VARIETY`` the kinds of this pair type, at ``CAUSE_VARIETY`` no
        kind; the alarm causes used so far at all three; nothing at ``NO_VARIETY``."""
        if level == FULL_VARIETY:
            return self.card_kinds | self.kinds | self.kinds_by_type[pair_type], self.causes
        if level == TYPE_VARIETY:
            return self.kinds_by_type[pair_type], self.causes
        if level == CAUSE_VARIETY:
            return set(), self.causes
        return set(), set()

    def take(self, pair: Pair) -> None:
        if pair.gray:
            self.kinds.add(pair.gray.gray_kind)
            self.kinds_by_type[pair.pair_type].add(pair.gray.gray_kind)
        if pair.pair_type == "false_alarm_over_gray":
            self.causes.add(pair.preferred.strongest)


NO_VARIETY, CAUSE_VARIETY, TYPE_VARIETY, FULL_VARIETY = 0, 1, 2, 3
#: relaxation order (wide margin, two people, variety level): the margin is given up last
PAIR_PASSES = tuple(
    (wide, people, level)
    for wide in (True, False)
    for level in (FULL_VARIETY, TYPE_VARIETY, CAUSE_VARIETY, NO_VARIETY)
    for people in (True, False)
)


def select_pairs(days: Iterable[AgentDay], rng: random.Random, usage: Usage) -> list[Pair]:
    """The eight pairs (see the module docstring); every agent-day, agent and day is new. Each
    pair type is filled in passes (``PAIR_PASSES``): a wide margin with two people, a gray kind
    and an alarm cause not used by the cards or any pair yet (then allowing a bot); then a kind
    new to this pair type; then any kind with a new cause; then anything; and only then the same
    eight with a close margin."""
    by_day: dict[int, list[AgentDay]] = defaultdict(list)
    for d in sorted(days, key=lambda d: d.key):
        if d.usable:
            by_day[d.day].append(d)
    order = sorted(by_day)
    rng.shuffle(order)
    pairs: list[Pair] = []
    used_days: set[int] = set()
    variety = PairVariety(card_kinds=set(usage.gray_kinds))

    def first(candidates: Iterable[AgentDay]) -> AgentDay | None:
        """The free agent-day highest on the list, people before bots."""
        free = [d for d in candidates if usage.free(d)]
        return min(free, key=lambda d: (d.is_bot, d.rank, d.agent)) if free else None

    def gray_over_ordinary(
        today: list[AgentDay], kinds: set, causes: set, wide: bool
    ) -> tuple | None:
        gray = first(d for d in today if shown_gray(d) and d.listed and d.gray_kind not in kinds)
        if gray is None:
            return None
        ordinary = first(
            d
            for d in today
            if d.category == ORDINARY and d.unlisted and clear_enough(gray, d, wide)
        )
        return (gray, ordinary) if ordinary else None

    def false_alarm_over_gray(
        today: list[AgentDay], kinds: set, causes: set, wide: bool
    ) -> tuple | None:
        alarm = first(
            d for d in today if d.category == ORDINARY and d.listed and d.strongest not in causes
        )
        if alarm is None:
            return None
        gray = first(
            d
            for d in today
            if shown_gray(d)
            and d.unlisted
            and d.gray_kind not in kinds
            and clear_enough(alarm, d, wide)
        )
        return (alarm, gray) if gray else None

    def rank1_vs_rank4(today: list[AgentDay], kinds: set, causes: set, wide: bool) -> tuple | None:
        top = [d for d in today if d.listed and d.rank == 1 and usage.free(d)]
        last = [d for d in today if d.listed and d.rank == LIST_SIZE and usage.free(d)]
        if len(top) != 1 or len(last) != 1 or not clear_enough(top[0], last[0], True):
            return None
        repeated = any(d.category == GRAY and d.gray_kind in kinds for d in (top[0], last[0]))
        return None if repeated else (top[0], last[0])

    choosers = {
        "gray_over_ordinary": gray_over_ordinary,
        "false_alarm_over_gray": false_alarm_over_gray,
        "rank1_vs_rank4": rank1_vs_rank4,
    }
    for pair_type, choose in choosers.items():
        found = 0
        for wide, people_only, level in PAIR_PASSES:
            if not wide and pair_type in STRICT_MARGIN_TYPES:
                continue
            for day in order:
                if found == PAIR_TYPES[pair_type] or day in used_days:
                    continue
                chosen = choose(by_day[day], *variety.avoid(pair_type, level), wide)
                if chosen is None or (people_only and any(d.is_bot for d in chosen)):
                    continue
                pair = Pair(pair_type, *chosen)
                pairs.append(pair)
                for d in chosen:
                    usage.take(d)
                used_days.add(day)
                variety.take(pair)
                found += 1
    counts = Counter(p.pair_type for p in pairs)
    if counts != Counter(PAIR_TYPES):
        raise ValueError(f"pairs found {dict(counts)}, wanted {PAIR_TYPES}")
    return pairs
