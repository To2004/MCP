"""Five candidate formulas for the behaviour multiplier M, on the six agreed dimensions.

Usage: ``python3 -I m_formula_candidates.py [--seed 101] [--routine-days 10]``

The six dimensions (all against the same agent id's own history):
- Typical Footprint: Tool, Asset, Tool on asset;
- Typical Cadence: Calls this hour, Breadth (distinct tool-asset pairs in the hour), Time of day.

The candidates:
- A, the deck's dimension slides (v4): an excess score for amounts, a "times per day" rarity score
  for categories, the strangest dimension wins, M = 5^(2s-1) or 0.7^(1-2s).
- B, the deck's formal model, fixed: per dimension (Baseline / Likelihood)^γ with an add-one
  likelihood, counted on calls; the strangest dimension wins; clipped to [0.7, 5].
- C, the same ratios as B, multiplied over the dimensions (naive Bayes, as in risk-based
  authentication); clipped to [0.7, 5].
- D, a rank on calls: how many of the agent's past calls were at least as unusual,
  M = ((H + 1)/(2D + 1))^γ.
- E, the same rank on days: each past day is one observation.
- F, E with Tool on asset as a frequency among the days that asset was used.
- G, the strangest dimension: each dimension gets its own M from F's day count; the call gets the
  highest (no whole-call rank).
- I, the author's choice for now: count calls, not days. It is D with Tool on asset per asset.
  γ = ln 5 / ln(max(n, 1000) + 1), so "never seen" gives ×5 once the agent has 1,000 past calls,
  and a new agent ramps up until then.
- J, the current design: I plus the minor fixes (Time of day within one hour; amounts of 1-3 share
  one bin). K: F with the same fixes. Denied calls never enter any history.
- H, total surprise: F's per-dimension frequencies turned into surprise, log(1/f), added up over
  the dimensions, and the sum ranked against the past days' sums.

Scenarios and agents come from ``m_formula_servers.py``: general behaviours on seven kinds of
agent. Two probes for counting calls are added: a tool used every day but in few calls (should stay
quiet), and a burst after one huge burst day in the history (should still rise). Expectations are
fixed before running. Synthetic data only: design checks, not results.
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
import sys
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from itertools import accumulate
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m_formula_servers as base  # noqa: E402  (the agents, the routine and the call helpers)

TOP, FLOOR = 5.0, 0.7
HOUR_MIN = base.HOUR_MIN
CATS = ("tool", "asset", "pair", "hour")
AMOUNTS = ("rate", "breadth")
QUIET_MAX, RISE_MIN, ALERT_LINE = 1.75, 2.0, 3.0
MIN_CALLS = 1000  # I: "never seen" reaches ×5 only once the agent has this many past calls
HOUR_WINDOW = 1  # J, K: Time of day counts calls within one hour of this time (the deck's rule)
COUNT_FLOOR = 3  # J, K: amounts of 1-3 share one bin, so a third call in an hour is no record
DENIED = "denied"  # a call the gateway refused: scored, never learned
T95 = {
    1: 12.71,
    2: 4.30,
    3: 3.18,
    4: 2.78,
    5: 2.57,
    6: 2.45,
    7: 2.36,
    8: 2.31,
    9: 2.26,
    10: 2.23,
    14: 2.14,
    19: 2.09,
    29: 2.05,
}  # Student t, two-sided 95%
ROUTINE_MEDIAN_MAX, ROUTINE_HIGH_SHARE_MAX = 1.25, 0.05
FOOTPRINT_CEILING = {"tool": 0.9, "pair": 0.9, "asset": 1.0}  # v4's c
MINOR_TOOL = ("audit_note", 40, 200)  # used once a day, every day
HUGE_BURST = 300  # calls in one hour on one past day (the poisoning probe)


@dataclass(frozen=True)
class Obs:
    """One call's six dimension values: categories, and raw amounts in its hour."""

    tool: str
    asset: str | None
    pair: tuple[str, str] | None
    hour: int
    rate: int
    breadth: int

    def value(self, dim: str) -> object:
        """The value on one dimension."""
        return getattr(self, dim)


Day = list[Obs]


def observe(calls: Sequence[base.Call]) -> Day:
    """The six values of every call of one day (``calls`` sorted by minute)."""
    out, left = [], 0
    for i, c in enumerate(calls):
        while c.minute - calls[left].minute >= HOUR_MIN:
            left += 1
        hour = calls[left : i + 1]
        out.append(
            Obs(
                c.tool,
                c.asset,
                (c.tool, c.asset) if c.asset else None,
                c.minute // HOUR_MIN,
                len(hour),
                len({(x.tool, x.asset) for x in hour}),
            )
        )
    return out


def clip(m: float) -> float:
    """Keep M within [0.7, 5]."""
    return min(TOP, max(FLOOR, m))


def curve(s: float) -> float:
    """v4's curve from a 0-1 score to M."""
    return 5 ** (2 * s - 1) if s >= 0.5 else 0.7 ** (1 - 2 * s)


class V4:
    """A: excess and "times per day" rarity scores; the strangest dimension wins."""

    name = "A v4 (deck dims)"

    def __init__(self, days: Sequence[Day]) -> None:
        calls = [o for d in days for o in d]
        self.active = len(days)
        self.mean = {
            a: statistics.fmean(o.value(a) for o in calls) if calls else 0.0 for a in AMOUNTS
        }
        self.counts = {
            c: Counter(o.value(c) for o in calls if o.value(c) is not None) for c in CATS
        }
        self.sorted = {c: sorted(self.counts[c].values()) for c in CATS}
        self.prefix = {c: [0, *accumulate(self.sorted[c])] for c in CATS}
        seen: dict[str, set] = {c: set() for c in CATS}
        self.started = dict.fromkeys(CATS, 0)  # new values started after the first day
        for i, d in enumerate(days):
            for o in d:
                for c in CATS:
                    v = o.value(c)
                    if v is not None and v not in seen[c]:
                        seen[c].add(v)
                        self.started[c] += i > 0

    def score(self, o: Obs) -> float:
        """M of one call."""
        if self.active == 0:
            return 1.0
        scores = []
        for a in AMOUNTS:
            x, mu = o.value(a), self.mean[a]
            scores.append((x + 1) / (x + 1 + 2 * (mu + 1)))
        for c in ("tool", "asset", "pair"):
            v = o.value(c)
            if v is None:
                continue
            q = self.counts[c].get(v, 0)
            rare = self.prefix[c][bisect_right(self.sorted[c], q)] if q else self.started[c]
            scores.append(FOOTPRINT_CEILING[c] / (1 + 2 * (rare + 1) / (self.active + 1)))
        near = sum(self.counts["hour"].get(h, 0) for h in (o.hour - 1, o.hour, o.hour + 1))
        scores.append(1 / (1 + 2 * (near + 1) / (self.active + 1)))
        return curve(max(scores))


class Ratio:
    """B and C: per dimension (Baseline / Likelihood)^γ on calls; max (B) or product (C)."""

    def __init__(self, days: Sequence[Day], product: bool) -> None:
        calls = [o for d in days for o in d]
        self.product = product
        self.name = "C product of ratios" if product else "B deck model, fixed"
        self.h = len(calls)
        self.counts = {
            c: Counter(o.value(c) for o in calls if o.value(c) is not None) for c in CATS
        }
        self.bins = {a: sorted(base.doubling(o.value(a)) for o in calls) for a in AMOUNTS}

    def _one(self, likelihood: float, baseline: float, ceiling: float) -> float:
        gamma = math.log(TOP) / math.log(ceiling) if ceiling > 1 else 0.0
        return clip((baseline / likelihood) ** gamma)

    def score(self, o: Obs) -> float:
        """M of one call."""
        if self.h == 0:
            return 1.0
        ms = []
        for c in CATS:
            v = o.value(c)
            if v is None:
                continue
            k = len(self.counts[c]) + 1
            lik = (self.counts[c].get(v, 0) + 1) / (self.h + k)
            ms.append(self._one(lik, 1 / k, (self.h + k) / k))
        for a in AMOUNTS:
            b = base.doubling(o.value(a))
            at_least = len(self.bins[a]) - bisect_left(self.bins[a], b)
            ms.append(self._one((at_least + 1) / (self.h + 2), 0.5, (self.h + 2) / 2))
        return clip(math.prod(ms)) if self.product else max(ms)


def surprise(fs: Sequence[float]) -> float:
    """Total surprise of a call or day: the sum of log(1/f) over its dimensions."""
    return sum(-math.log(f) for f in fs)


class Rank:
    """D and E: how many past observations were at least as unusual (rarest dimension first)."""

    def __init__(
        self,
        days: Sequence[Day],
        by_day: bool,
        pair_per_asset: bool = False,
        combine: str = "rank",
        min_calls: int = 0,
        hour_window: int = 0,
        count_floor: int = 0,
    ) -> None:
        self.name = "E rank on days" if by_day else "D rank on calls"
        self.pair_per_asset = pair_per_asset  # F: tool on asset among the days the asset was used
        self.combine = combine  # "rank" (D, E, F, I, J, K), "max" (G) or "sum" (H)
        self.hour_window, self.count_floor = hour_window, count_floor
        if by_day:
            obs = [
                (
                    {c: {o.value(c) for o in d} - {None} for c in CATS},
                    {a: max(self._bin(o.value(a)) for o in d) for a in AMOUNTS},
                )
                for d in days
                if d
            ]
        else:
            obs = [
                (
                    {c: {o.value(c)} - {None} for c in CATS},
                    {a: self._bin(o.value(a)) for a in AMOUNTS},
                )
                for d in days
                for o in d
            ]
        self.h = len(obs)
        # I: with too few past calls, γ uses MIN_CALLS, so a new agent ramps up instead of jumping to ×5
        scale = max(self.h, min_calls)
        self.gamma = math.log(TOP) / math.log(scale + 1) if self.h else 0.0
        self.counts = {c: Counter(v for cats, _ in obs for v in cats[c]) for c in CATS}
        rarity = {
            c: [min((self._count(c, v) - 1 for v in cats[c]), default=None) for cats, _ in obs]
            for c in CATS
        }
        self.rare_sorted = {c: sorted(r for r in rarity[c] if r is not None) for c in CATS}
        self.bins_sorted = {a: sorted(amts[a] for _, amts in obs) for a in AMOUNTS}
        profiles = []
        for i, (cats, amts) in enumerate(obs):
            fs = []
            for c in CATS:
                if c == "pair" and pair_per_asset:
                    fs.append(min((self._pair(v, leave_out=1) for v in cats[c]), default=1.0))
                    continue
                r = rarity[c][i]
                if r is None:
                    fs.append(1.0)
                    continue
                n = bisect_right(self.rare_sorted[c], r) - 1  # leave this observation out
                fs.append((n + 0.5) / len(self.rare_sorted[c]))
            for a in AMOUNTS:
                n = len(self.bins_sorted[a]) - bisect_left(self.bins_sorted[a], amts[a]) - 1
                fs.append((n + 0.5) / self.h)
            profiles.append(tuple(sorted(fs)))
        self.profiles = sorted(profiles)
        self.sums = sorted(surprise(p) for p in profiles)

    def _bin(self, amount: object) -> int:
        """The doubling of an amount; with a floor, 1 to the floor share one bin."""
        return base.doubling(max(int(amount), self.count_floor))  # type: ignore[call-overload]

    def _count(self, dim: str, value: object) -> int:
        """Past observations with this value; for Time of day, within the hour window."""
        if dim != "hour" or not self.hour_window:
            return self.counts[dim].get(value, 0)
        w = self.hour_window
        return sum(self.counts["hour"].get((value + d) % 24, 0) for d in range(-w, w + 1))  # type: ignore[operator]

    def _pair(self, pair: tuple[str, str], leave_out: int = 0) -> float:
        """How often this tool, among the observations that used this asset."""
        used = self.counts["pair"].get(pair, 0) - leave_out
        touched = self.counts["asset"].get(pair[1], 0) - leave_out
        return (used + 0.5) / (touched + 1)

    def frequencies(self, o: Obs) -> dict[str, float]:
        """Per dimension, the share of past observations at least as unusual as this call."""
        named: dict[str, float] = {}
        for c in CATS:
            v = o.value(c)
            if c == "pair" and self.pair_per_asset and o.pair is not None:
                named[c] = self._pair(o.pair)
                continue
            if v is None or not self.rare_sorted[c]:
                named[c] = 1.0
                continue
            n = bisect_right(self.rare_sorted[c], self._count(c, v))
            named[c] = (n + 0.5) / (len(self.rare_sorted[c]) + 1)
        for a in AMOUNTS:
            b = self._bin(o.value(a))
            n = len(self.bins_sorted[a]) - bisect_left(self.bins_sorted[a], b)
            named[a] = (n + 0.5) / (self.h + 1)
        return named

    def explain(self, o: Obs) -> str:
        """The reason shown with M: the most unusual dimension and how often it happened."""
        named = self.frequencies(o)
        dim = min(named, key=named.get)  # type: ignore[arg-type]
        label = {
            "tool": "Tool",
            "asset": "Asset",
            "pair": "Tool on asset",
            "hour": "Time of day",
            "rate": "Calls this hour",
            "breadth": "Breadth",
        }[dim]
        share = named[dim]
        return (
            f"{label}: as unusual in {share:.2%} of past calls" if share < 1 else "nothing unusual"
        )

    def score(self, o: Obs) -> float:
        """M of one call."""
        if self.h == 0:
            return 1.0
        fs = list(self.frequencies(o).values())
        if self.combine == "max":  # G: each dimension's own M; the highest wins
            return max((1 / (2 * f)) ** self.gamma for f in fs)
        if self.combine == "sum":  # H: rank the total surprise against the past days' totals
            at_least = len(self.sums) - bisect_left(self.sums, surprise(fs))
        else:
            at_least = bisect_right(self.profiles, tuple(sorted(fs)))
        return ((self.h + 1) / (2 * at_least + 1)) ** self.gamma


MAKERS: tuple[Callable[[Sequence[Day]], object], ...] = (
    V4,
    lambda d: Ratio(d, product=False),
    lambda d: Ratio(d, product=True),
    lambda d: Rank(d, by_day=False),
    lambda d: Rank(d, by_day=True),
    lambda d: Rank(d, by_day=True, pair_per_asset=True),
    lambda d: Rank(d, by_day=True, pair_per_asset=True, combine="max"),
    lambda d: Rank(d, by_day=True, pair_per_asset=True, combine="sum"),
    lambda d: Rank(d, by_day=False, pair_per_asset=True, min_calls=MIN_CALLS),
    lambda d: Rank(
        d,
        by_day=False,
        pair_per_asset=True,
        min_calls=MIN_CALLS,
        hour_window=HOUR_WINDOW,
        count_floor=COUNT_FLOOR,
    ),
    lambda d: Rank(
        d, by_day=True, pair_per_asset=True, hour_window=HOUR_WINDOW, count_floor=COUNT_FLOOR
    ),
)
NAMES = (
    "A v4 (deck dims)",
    "B deck model, fixed",
    "C product of ratios",
    "D rank on calls",
    "E rank on days",
    "F days, pair per asset",
    "G strangest dimension",
    "H total surprise",
    "I calls, pair per asset",
    "J calls + fixes (current)",
    "K days + fixes",
)

Extra = Callable[[int, list[base.Call]], list[base.Call]]


def history(
    seed: int, p: base.Profile, extra: Extra | None = None, options=None, learn_denied: bool = False
) -> list[Day]:
    """90 active days of raw observations. Calls the gateway denied never enter the history."""
    rng = random.Random(seed)
    days = []
    for d in range(base.WINDOW_DAYS):
        calls = base.day_of(rng, p, **(options(d) if options else {}))
        if extra is not None:
            calls = sorted(extra(d, calls), key=lambda c: c.minute)
        if not learn_denied:
            calls = [c for c in calls if c.tag != DENIED]
        days.append(observe(calls))
    return days


def models(days: Sequence[Day]) -> list:
    """All five candidates, fitted on one history."""
    return [make(days) for make in MAKERS]


def tagged_max(fitted: list, calls: Sequence[base.Call], tag: str = base.PROBE) -> list[float]:
    """Per candidate, the highest M among the tagged calls of today."""
    obs = observe(calls)
    idx = [i for i, c in enumerate(calls) if c.tag == tag]
    return [max(m.score(obs[i]) for i in idx) for m in fitted]


def day_max(fitted: list, calls: Sequence[base.Call]) -> list[float]:
    """Per candidate, the agent-day's M: the highest M among all of today's calls."""
    obs = observe(calls)
    return [max(m.score(o) for o in obs) for m in fitted]


@dataclass(frozen=True)
class Row:
    """One scenario on one agent: expectation, and M per candidate."""

    group: str
    name: str
    expect: str
    ms: tuple[float, ...] | None  # None: does not apply to this agent
    ok: Callable[[float], bool]


def run(p: base.Profile, seed: int, routine_days: int) -> list[Row]:
    """Every scenario on one agent, scored by all five candidates."""
    days = history(seed, p)
    fitted = models(days)
    today_base = base.day_of(random.Random(seed + 1), p)
    core, reader, occasional = p.usual[0], p.usual[2], p.usual[3:]
    read0 = p.read[0]
    write0 = p.write[0] if p.write else None
    rows: list[Row] = []

    def today(*injected: base.Call) -> list[base.Call]:
        return sorted([*today_base, *injected], key=lambda c: c.minute)

    def add(group, name, expect, ms, ok) -> None:
        rows.append(Row(group, name, expect, None if ms is None else tuple(ms), ok))

    quiet, rise = (lambda m: m <= QUIET_MAX), (lambda m: m >= RISE_MIN)

    # Stay quiet.
    per_day = [
        day_max(fitted, base.day_of(random.Random(1000 + i), p)) for i in range(routine_days)
    ]
    med = [statistics.median(col) for col in zip(*per_day, strict=True)]
    add(
        "quiet",
        "ordinary days (median)",
        f"≤ {ROUTINE_MEDIAN_MAX}",
        med,
        lambda m: m <= ROUTINE_MEDIAN_MAX,
    )
    high = [sum(m >= ALERT_LINE for m in col) / len(col) for col in zip(*per_day, strict=True)]
    add(
        "quiet",
        "ordinary days: share at ≥ 3",
        f"≤ {ROUTINE_HIGH_SHARE_MAX:.0%}",
        high,
        lambda m: m <= ROUTINE_HIGH_SHARE_MAX,
    )
    busy = [day_max(fitted, base.day_of(random.Random(2000 + i), p, busy=1.3)) for i in range(5)]
    add(
        "quiet",
        "busy day, 30% more (median)",
        f"≤ {QUIET_MAX}",
        [statistics.median(col) for col in zip(*busy, strict=True)],
        quiet,
    )
    new_action = base.call(base.at(11), p.unused, core)

    def adopts(d: int, calls: list[base.Call]) -> list[base.Call]:
        late = d >= base.WINDOW_DAYS - base.SETTLE_DAYS
        return calls + ([replace(new_action, tag="")] if late else [])

    add(
        "quiet",
        f"new tool, daily for {base.SETTLE_DAYS} days",
        f"≤ {QUIET_MAX}",
        tagged_max(models(history(seed, p, adopts)), today(new_action)),
        quiet,
    )
    minor = base.call(base.at(12), MINOR_TOOL, core)

    def minor_daily(d: int, calls: list[base.Call]) -> list[base.Call]:
        return calls + [replace(minor, tag="")]

    add(
        "quiet",
        "tool used every day, in few calls",
        f"≤ {QUIET_MAX}",
        tagged_max(models(history(seed, p, minor_daily)), today(minor)),
        quiet,
    )
    job = [base.call(base.at(15, i * 50 // len(p.usual)), read0, a) for i, a in enumerate(p.usual)]

    def periodic(d: int, calls: list[base.Call]) -> list[base.Call]:
        hit = d % base.MONTHLY_EVERY == 5
        return calls + [replace(c, tag="") for c in job] if hit else calls

    add(
        "quiet",
        "periodic big job (4 in history)",
        f"< {ALERT_LINE:.0f}",
        tagged_max(models(history(seed, p, periodic)), today(*job)),
        lambda m: m < ALERT_LINE,
    )
    add(
        "quiet",
        "explorer opens another resource",
        f"≤ {QUIET_MAX}",
        tagged_max(fitted, today(base.call(base.at(14), read0, "c:0badf00d")))
        if p.explores
        else None,
        quiet,
    )

    def growing(d: int) -> dict:
        return {"busy": 1 + base.GROWTH_PER_DAY * d}

    grown_fit = models(history(seed, p, options=growing))
    trend = 1 + base.GROWTH_PER_DAY * base.WINDOW_DAYS
    grown = [
        day_max(grown_fit, base.day_of(random.Random(4000 + i), p, busy=trend)) for i in range(5)
    ]
    add(
        "quiet",
        "steady growth, today on trend",
        f"≤ {QUIET_MAX}",
        [statistics.median(col) for col in zip(*grown, strict=True)],
        quiet,
    )

    # One unusual thing.
    burst = [base.call(base.at(14, i * 2), read0, p.usual[i % 3]) for i in range(30)]
    singles = [
        (
            "new resource (rarely explores)",
            None if p.explores else [base.call(base.at(14), read0, p.sensitive)],
        ),
        ("known resource, new action", [base.call(base.at(14), write0 or p.unused, reader)]),
        ("new tool", [new_action]),
        ("unusual hour (3 am)", None if p.always_on else [base.call(base.at(3), read0, core)]),
        ("far more calls in an hour", burst),
        (
            "many resources in an hour",
            [base.call(base.at(14, i * 2), read0, a) for i, a in enumerate(p.usual[:25])],
        ),
    ]
    for name, injected in singles:
        add(
            "rise",
            name,
            f"≥ {RISE_MIN:.0f}",
            None if injected is None else tagged_max(fitted, today(*injected)),
            rise,
        )

    def huge_day(d: int, calls: list[base.Call]) -> list[base.Call]:
        if d != base.WINDOW_DAYS // 2:
            return calls
        return calls + [
            base.call(base.at(14, i // 5), read0, p.usual[i % 3], "") for i in range(HUGE_BURST)
        ]

    add(
        "rise",
        "burst after one huge burst day",
        f"≥ {RISE_MIN:.0f}",
        tagged_max(models(history(seed, p, huge_day)), today(*burst)),
        rise,
    )

    def probes(d: int, calls: list[base.Call]) -> list[base.Call]:
        if d < base.WINDOW_DAYS - 5:
            return calls
        return calls + [replace(new_action, minute=base.at(10, i), tag=DENIED) for i in range(20)]

    add(
        "rise",
        "probe then strike (denied calls not learned)",
        f"≥ {RISE_MIN:.0f}",
        tagged_max(models(history(seed, p, probes)), today(new_action)),
        rise,
    )
    add(
        "info",
        "same, if denied calls were learned",
        "lower",
        tagged_max(models(history(seed, p, probes, learn_denied=True)), today(new_action)),
        lambda m: True,
    )

    # Several at once.
    night = [*(base.call(base.at(3, i), read0, a) for i, a in enumerate(occasional[:20]))]
    look = [
        new_action,
        *(base.call(base.at(14, 1 + i), read0, a) for i, a in enumerate(occasional[:20])),
    ]
    add(
        "several",
        "night: many resources at 3 am",
        f"= {TOP:.0f}",
        tagged_max(fitted, today(*night)),
        lambda m: m >= TOP - 1e-9,
    )
    add(
        "several",
        "new tool, then many resources",
        f"= {TOP:.0f}",
        tagged_max(fitted, today(*look)),
        lambda m: m >= TOP - 1e-9,
    )

    # Expected to get through.
    mimic = [base.call(base.at(13, i * 10), read0, a) for i, a in enumerate(p.usual[:3])]
    add(
        "through",
        "mimicry inside the habit",
        "< 2",
        tagged_max(fitted, today(*mimic)),
        lambda m: m < RISE_MIN,
    )
    b2 = base.call(base.at(14), write0 or p.unused, reader)

    def habit(d: int, calls: list[base.Call]) -> list[base.Call]:
        return calls + [replace(b2, tag="")] if d % 2 == 0 else calls

    add(
        "through",
        "habit building: half the days",
        "< 2",
        tagged_max(models(history(seed, p, habit)), today(b2)),
        lambda m: m < RISE_MIN,
    )
    return rows


def tallies(results: dict[str, list[Row]]) -> dict[str, dict[str, tuple[int, int]]]:
    """Per candidate and group (and "total"): checks as expected, out of checks run."""
    first = next(iter(results.values()))
    groups = [g for g in dict.fromkeys(r.group for r in first) if g != "info"]
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for k, cand in enumerate(NAMES):
        out[cand] = {}
        tot = ran = 0
        for g in groups:
            rs = [r for rows in results.values() for r in rows if r.group == g and r.ms is not None]
            ok = sum(r.ok(r.ms[k]) for r in rs)  # type: ignore[index]
            out[cand][g] = (ok, len(rs))
            tot, ran = tot + ok, ran + len(rs)
        out[cand]["total"] = (tot, ran)
    return out


def interval(xs: Sequence[int]) -> str:
    """Mean and two-sided 95% Student-t interval."""
    mean = statistics.fmean(xs)
    if len(xs) < 2:
        return f"{mean:5.1f}"
    df = len(xs) - 1
    t = T95.get(df) or T95[max(k for k in T95 if k <= df)]
    half = t * statistics.stdev(xs) / math.sqrt(len(xs))
    return f"{mean:5.1f} ± {half:3.1f}"


def explain_examples(seed: int) -> None:
    """The reason shown with M for a few calls of the GitHub-shaped agent (current design J)."""
    p = base.PROFILES[0]
    model = models(history(seed, p))[NAMES.index("J calls + fixes (current)")]
    base_day = base.day_of(random.Random(seed + 1), p)
    core, reader = p.usual[0], p.usual[2]
    cases = {
        "a routine read": [base.call(base.at(10, 30), p.read[0], core)],
        "a write on a repository it only reads": [base.call(base.at(14), p.write[0], reader)],
        "a tool it never used": [base.call(base.at(14), p.unused, core)],
        "a read at 3 am": [base.call(base.at(3), p.read[0], core)],
        "30 calls in one hour": [
            base.call(base.at(14, i * 2), p.read[0], p.usual[i % 3]) for i in range(30)
        ],
    }
    print(f"\n=== the reason shown with M (current design, {p.name}-shaped agent) ===")
    for name, injected in cases.items():
        calls = sorted([*base_day, *injected], key=lambda c: c.minute)
        obs = observe(calls)
        idx = [k for k, c in enumerate(calls) if c.tag == base.PROBE]
        best = max(idx, key=lambda k: model.score(obs[k]))
        print(
            f"  {name:<40} M = {model.score(obs[best]):4.2f}   reason: {model.explain(obs[best])}"
        )


def main() -> None:
    """Score every scenario on every agent with every candidate; print the tallies."""
    parser = argparse.ArgumentParser(description="Candidate formulas for M.")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--seeds", type=str, default="", help="comma list: print mean ± 95%% CI")
    parser.add_argument("--routine-days", type=int, default=10)
    parser.add_argument("--explain", action="store_true", help="print the reason shown with M")
    args = parser.parse_args()
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
        per_seed = [
            tallies({p.name: run(p, s, args.routine_days) for p in base.PROFILES}) for s in seeds
        ]
        groups = list(per_seed[0][NAMES[0]])
        print(f"{len(seeds)} seeds: mean ± 95% CI of checks as expected")
        print(f"{'candidate':<27}" + "".join(f"{g:>17}" for g in groups))
        for cand in NAMES:
            cells = []
            for g in groups:
                ran = per_seed[0][cand][g][1]
                cells.append(f"{interval([t[cand][g][0] for t in per_seed]):>12}/{ran:<4}")
            print(f"{cand:<27}" + "".join(cells))
        return
    results = {p.name: run(p, args.seed, args.routine_days) for p in base.PROFILES}
    first = next(iter(results.values()))
    width = max(len(r.name) for r in first)
    agents = list(results)
    for k, cand in enumerate(NAMES):
        print(f"\n=== {cand} ===")
        print(f"{'scenario':<{width}}  {'expected':<9}" + "".join(f"{a[:10]:>11}" for a in agents))
        for i, row in enumerate(first):
            cells = []
            for a in agents:
                r = results[a][i]
                if r.ms is None:
                    cells.append(f"{'n/a':>11}")
                else:
                    m = r.ms[k]
                    cells.append(f"{m:6.2f}{'  ok ' if r.ok(m) else ' FAIL'}")
            print(f"{row.name:<{width}}  {row.expect:<9}" + "".join(cells))
    print("\n=== as expected, per candidate and group ===")
    table = tallies(results)
    groups = list(table[NAMES[0]])
    print(f"{'candidate':<27}" + "".join(f"{g:>10}" for g in groups))
    for cand in NAMES:
        print(
            f"{cand:<27}"
            + "".join(f"{table[cand][g][0]:>4}/{table[cand][g][1]:<5}" for g in groups)
        )
    if args.explain:
        explain_examples(args.seed)


if __name__ == "__main__":
    main()
