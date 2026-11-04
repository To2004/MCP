"""The author's ten Pinecrest scenarios, scored by our formula, against the deck's own charts.

Usage: ``python3 -I m_formula_pinecrest.py [--seed 7] [--plot <png>]``

The scenarios come from "Dynamic score scenario report" (26 slides): Pinecrest Books, five tools
(search_orders, read_customer, reply_to_customer, refund_order, read_file), and seven users (Dana,
Omer, Avi, Maya, Lior, Noa, Tal). Each scenario compares two users making the same call. The deck's
seven "what should happen" charts give the expected curve.

Four variants of our formula, M = ((n + 1)/(2k + 1))^γ with the rarest dimension first:
- J: counting calls, the current choice (Tool, Asset, Tool on asset, Calls this hour, Breadth,
  Time of day).
- K: the same, counting days.
- J4: the author's design of 2026-11-01, counting calls with only four dimensions: Calls this hour,
  Time of day, Tool and Asset (burst and tool order are policy rules, outside this probe).
- J4s: J4 with a smooth k (near past calls count partly; see ``Smooth``), beta 2 and 3.
- J+ and K+: J and K plus the three things the deck asks for that the current design lacks:
  - Time of day split by weekday/weekend, where the other kind of day counts as 10% familiar;
  - Run length, the minutes since the current run of calls began (a run ends after 30 idle minutes);
  - a cold start: a new user starts at ×2 and comes down to ×1 over its first 12 calls.

History is the last 90 calendar days. Synthetic data only: design checks, not results.
"""

from __future__ import annotations

import argparse
import math
import random
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

TOP = 5.0
MIN_CALLS = 1000  # warm-up: "never seen" reaches ×5 only from this many past calls
HISTORY_DAYS = 90
IDLE_RUN_MIN = 30  # a run of calls ends after this many idle minutes
HOUR_WINDOW = 1  # Time of day: calls within one hour of this time
OTHER_DAY_WEIGHT = 0.1  # J+, K+: a usual hour on the other kind of day counts as 10% familiar
COLD_START_TOP, COLD_START_CALLS = 2.0, 12  # J+, K+: ×2 for a new user, down to ×1 over 12 calls
WEEKEND = frozenset({5, 6})  # Friday and Saturday; days are numbered Sunday = 0
COUNT_FLOOR = 3  # amounts of 1-3 share one bin

CLEARLY_HIGHER, NORMAL_MAX = 1.5, 1.15  # the deck: "clearly higher" / "normal or a little below"
NEW_USER_BAND = (1.5, 3.0)  # the deck: "higher, but not very high"


@dataclass(frozen=True)
class Call:
    """One past or present call: day (0 = today, negative = past), minute of day, tool, asset."""

    day: int
    minute: int
    tool: str
    asset: str | None


@dataclass(frozen=True)
class Obs:
    """A call's values on every dimension."""

    tool: str
    asset: str | None
    pair: tuple[str, str] | None
    hour: int
    weekend: bool
    rate: int
    breadth: int
    run: int


def doubling(amount: int) -> int:
    """Bins 1-3, 4-7, 8-15, ...; 0 for none."""
    return max(int(amount), COUNT_FLOOR).bit_length() if amount > 0 else 0


def observe(calls: Sequence[Call], today_weekday: int) -> list[Obs]:
    """Every call's values; ``calls`` sorted by (day, minute)."""
    out, left, run_start = [], 0, None
    for i, c in enumerate(calls):
        stamp = c.day * 1440 + c.minute
        while stamp - (calls[left].day * 1440 + calls[left].minute) >= 60:
            left += 1
        hour_calls = calls[left : i + 1]
        if i == 0 or stamp - (calls[i - 1].day * 1440 + calls[i - 1].minute) >= IDLE_RUN_MIN:
            run_start = stamp
        weekday = (today_weekday + c.day) % 7
        out.append(
            Obs(
                c.tool,
                c.asset,
                (c.tool, c.asset) if c.asset else None,
                c.minute // 60,
                weekday in WEEKEND,
                len(hour_calls),
                len({(x.tool, x.asset) for x in hour_calls}),
                stamp - run_start,  # type: ignore[operator]
            )
        )
    return out


@dataclass(frozen=True)
class Variant:
    """Which version of the formula to score with."""

    name: str
    by_day: bool
    extras: bool  # J+ / K+: weekday split, Run length, cold start
    # J4: only Calls this hour, Time of day, Tool and Asset (the author, 2026-11-01)
    four: bool = False
    # J4s: smooth k; less busy past hours count (their calls / this call's)^beta
    smooth_beta: float = 0.0
    # J4s: Time of day split into weekday and weekend; the other kind of day counts this much
    other_day: float = 0.0


VARIANTS = (
    Variant("J4 calls, 4 dimensions", False, False, four=True),
    Variant("J4s smooth k", False, False, four=True, smooth_beta=3.0),
    Variant("J4s + weekday 1/10", False, False, four=True, smooth_beta=3.0, other_day=0.1),
    Variant("J4s + weekday 1/16", False, False, four=True, smooth_beta=3.0, other_day=1 / 16),
)


DIMENSIONS_LOOKED_AT = 4  # J4s: Sidak correction for taking the rarest of four dimensions
HOUR_DECAY = 0.5  # J4s: a past call one hour away counts 1/2, two hours away 1/4, ...


class Smooth:
    """J4s: smooth k per dimension, the rarest dimension, Sidak-corrected for four.

    k_d counts past calls at least as unusual as this one on dimension d, and near ones partly:
    - Tool, Asset: calls whose value was used as rarely or more rarely (no partial credit);
    - Time of day: every past call, weighted 1/2 per hour of distance;
    - Calls this hour: past calls whose hour was at least as busy, plus less busy ones weighted
      (their count / this count)^beta.
    s = (min_d k_d + 1/2)/(n + 1); share = 1 - (1 - s)^4; M = (1/2 / share)^gamma, with gamma set so
    that never seen (k = 0) gives x5 once the user has 1,000 calls.
    """

    def __init__(self, past: Sequence[Obs], v: Variant) -> None:
        self.v, self.n = v, len(past)
        self.counts = {
            c: Counter(getattr(o, c) for o in past if getattr(o, c) is not None)
            for c in ("tool", "asset")
        }
        self.by_hour = Counter((o.hour, o.weekend) for o in past)
        self.rates = sorted(o.rate for o in past)
        n_eff = max(self.n, MIN_CALLS)
        never = 1 - (1 - 0.5 / (n_eff + 1)) ** DIMENSIONS_LOOKED_AT
        self.gamma = math.log(TOP) / math.log(0.5 / never)

    def _k_tail(self, dim: str, value: object) -> float:
        if value is None:
            return float(self.n)
        q = self.counts[dim].get(value, 0)
        return float(sum(c for c in self.counts[dim].values() if c - 1 <= q))

    def _k_hour(self, hour: int, weekend: bool) -> float:
        """Past calls weighted 1/2 per hour of distance; with a weekday split, calls on the other
        kind of day (weekday vs weekend) count ``other_day`` as much."""
        total = 0.0
        for (h, w), cnt in self.by_hour.items():
            weight = HOUR_DECAY ** min(abs(hour - h), 24 - abs(hour - h))
            if self.v.other_day and w != weekend:
                weight *= self.v.other_day
            total += cnt * weight
        return total

    def _k_rate(self, x: int) -> float:
        i = bisect_left(self.rates, x)
        return (len(self.rates) - i) + sum((r / x) ** self.v.smooth_beta for r in self.rates[:i])

    def score(self, o: Obs, calls_so_far: int) -> float:
        if self.n == 0:
            return 1.0
        k = min(
            self._k_tail("tool", o.tool),
            self._k_tail("asset", o.asset),
            self._k_hour(o.hour, o.weekend),
            self._k_rate(o.rate),
        )
        s = (k + 0.5) / (self.n + 1)
        share = 1 - (1 - s) ** DIMENSIONS_LOOKED_AT
        return (0.5 / share) ** self.gamma


class Model:
    """The formula fitted on one user's history (one observation per call, or per day)."""

    def __init__(self, past: Sequence[Obs], past_days: Sequence[int], v: Variant) -> None:
        self.v = v
        self.n_calls = len(past)
        self.cats = ("tool", "asset", "pair")
        self.amounts = ("rate",) if v.four else ("rate", "breadth") + (("run",) if v.extras else ())
        if v.by_day:
            groups: dict[int, list[Obs]] = {}
            for o, d in zip(past, past_days, strict=True):
                groups.setdefault(d, []).append(o)
            self.obs = [self._as_day(g) for g in groups.values()]
        else:
            self.obs = [self._as_call(o) for o in past]
        self.h = len(self.obs)
        self.gamma = (
            math.log(TOP) / math.log(max(self.h, MIN_CALLS if not v.by_day else 90) + 1)
            if self.h
            else 0.0
        )
        self.counts = {
            c: Counter(v_ for cats, _, _ in self.obs for v_ in cats[c]) for c in self.cats
        }
        self.hours = {
            flag: Counter(h for _, hrs, _ in self.obs for (h, w) in hrs if w == flag)
            for flag in (False, True)
        }
        rar = {
            c: [
                min((self.counts[c][x] - 1 for x in cats[c]), default=None)
                for cats, _, _ in self.obs
            ]
            for c in ("tool", "asset")
        }
        if not v.extras:  # J, K: Time of day is a tail rank, as defined in the report
            rar["hour"] = [
                min((self._near(h, w) - 1 for h, w in hrs), default=None) for _, hrs, _ in self.obs
            ]
        self.rare_sorted = {c: sorted(r for r in rar[c] if r is not None) for c in rar}
        self.bins_sorted = {a: sorted(amts[a] for _, _, amts in self.obs) for a in self.amounts}
        profiles = []
        for i, (cats, hrs, amts) in enumerate(self.obs):
            fs = []
            for c in ("tool", "asset"):
                r = rar[c][i]
                fs.append(
                    1.0
                    if r is None
                    else (bisect_right(self.rare_sorted[c], r) - 1 + 0.5) / len(self.rare_sorted[c])
                )
            if not v.four:
                fs.append(min((self._pair(p, 1) for p in cats["pair"]), default=1.0))
            if v.extras:
                fs.append(min((self._hour(h, w, 1) for h, w in hrs), default=1.0))
            else:
                r = rar["hour"][i]
                fs.append(
                    1.0
                    if r is None
                    else (bisect_right(self.rare_sorted["hour"], r) - 1 + 0.5)
                    / len(self.rare_sorted["hour"])
                )
            for a in self.amounts:
                fs.append(
                    (len(self.bins_sorted[a]) - bisect_left(self.bins_sorted[a], amts[a]) - 1 + 0.5)
                    / self.h
                )
            profiles.append(tuple(sorted(fs)))
        self.profiles = sorted(profiles)

    def _as_call(self, o: Obs):
        return (
            {"tool": {o.tool}, "asset": {o.asset} - {None}, "pair": {o.pair} - {None}},
            {(o.hour, o.weekend)},
            {a: doubling(getattr(o, a)) for a in self.amounts},
        )

    def _as_day(self, g: Sequence[Obs]):
        return (
            {
                "tool": {o.tool for o in g},
                "asset": {o.asset for o in g} - {None},
                "pair": {o.pair for o in g} - {None},
            },
            {(o.hour, o.weekend) for o in g},
            {a: max(doubling(getattr(o, a)) for o in g) for a in self.amounts},
        )

    def _pair(self, pair: tuple[str, str], leave_out: int = 0) -> float:
        used = self.counts["pair"].get(pair, 0) - leave_out
        touched = self.counts["asset"].get(pair[1], 0) - leave_out
        return (used + 0.5) / (touched + 1)

    def _near(self, hour: int, weekend: bool) -> float:
        """Past observations within one hour of this time. J+/K+: on this kind of day, plus the
        other kind of day at 10%; J, K: any day."""

        def near(flag: bool) -> int:
            return sum(
                self.hours[flag].get((hour + d) % 24, 0)
                for d in range(-HOUR_WINDOW, HOUR_WINDOW + 1)
            )

        if self.v.extras:
            return near(weekend) + OTHER_DAY_WEIGHT * near(not weekend)
        return near(False) + near(True)

    def _hour(self, hour: int, weekend: bool, leave_out: int = 0) -> float:
        """J+/K+: the share of past observations at this time on this kind of day."""
        return (self._near(hour, weekend) - leave_out + 0.5) / (self.h + 1)

    def score(self, o: Obs, calls_so_far: int) -> float:
        """M of one call; ``calls_so_far`` counts every earlier call of this user (cold start)."""
        cold = 1.0
        if self.v.extras:
            cold = 1 + (COLD_START_TOP - 1) * max(0.0, 1 - calls_so_far / COLD_START_CALLS)
        if self.h == 0:
            return max(1.0, cold)
        fs = []
        for c in ("tool", "asset"):
            x = getattr(o, c)
            if x is None or not self.rare_sorted[c]:
                fs.append(1.0)
                continue
            fs.append(
                (bisect_right(self.rare_sorted[c], self.counts[c].get(x, 0)) + 0.5)
                / (len(self.rare_sorted[c]) + 1)
            )
        if not self.v.four:
            fs.append(self._pair(o.pair) if o.pair else 1.0)
        if self.v.extras:
            fs.append(self._hour(o.hour, o.weekend))
        elif self.rare_sorted["hour"]:
            q = self._near(o.hour, o.weekend)
            fs.append(
                (bisect_right(self.rare_sorted["hour"], q) + 0.5)
                / (len(self.rare_sorted["hour"]) + 1)
            )
        else:
            fs.append(1.0)
        for a in self.amounts:
            b = doubling(getattr(o, a))
            fs.append(
                (len(self.bins_sorted[a]) - bisect_left(self.bins_sorted[a], b) + 0.5)
                / (self.h + 1)
            )
        k = bisect_right(self.profiles, tuple(sorted(fs)))
        return max(((self.h + 1) / (2 * k + 1)) ** self.gamma, cold)


# ---------------------------------------------------------------- the Pinecrest users

Mix = Sequence[tuple[str, str | None, int]]
SUPPORT: Mix = (
    ("search_orders", "orders", 3),
    ("read_customer", "customers", 3),
    ("reply_to_customer", "emails", 2),
    ("read_file", "orders", 1),
    ("read_file", "customers", 1),
    ("read_file", "emails", 1),
)


@dataclass(frozen=True)
class User:
    """A Pinecrest user's habit."""

    name: str
    workdays: frozenset[int]
    hours: tuple[int, ...]
    mix: Mix
    burst: int = 6  # calls per working hour, inside 10 minutes (runs of about 10 minutes)
    steady_every: int = 0  # if set: one call every N minutes all through the working hours
    extra: Callable[[int, int, random.Random], list[tuple[int, str, str | None]]] = field(
        default=lambda d, w, r: []
    )


def pick(mix: Mix, rng: random.Random) -> tuple[str, str | None]:
    tools = [(t, a) for t, a, w in mix for _ in range(w)]
    return rng.choice(tools)


def history(u: User, rng: random.Random, today_weekday: int, away: range = range(0)) -> list[Call]:
    """The user's calls over the last 90 calendar days (none on days in ``away``)."""
    calls = []
    for day in range(-HISTORY_DAYS, 0):
        if -day in away:
            continue
        weekday = (today_weekday + day) % 7
        if weekday not in u.workdays:
            continue
        for hour in u.hours:
            if u.steady_every:
                minutes = range(0, 60, u.steady_every)
            else:
                start = rng.randrange(0, 50)
                minutes = sorted(start + rng.randrange(0, 10) for _ in range(u.burst))
            for m in minutes:
                t, a = pick(u.mix, rng)
                calls.append(Call(day, hour * 60 + m, t, a))
        calls += [Call(day, m, t, a) for m, t, a in u.extra(day, weekday, rng)]
    return sorted(calls, key=lambda c: (c.day, c.minute))


def every(n_days: int, tool: str, asset: str, minute: int = 10 * 60 + 30):
    """An extra call on every n-th working day."""
    return lambda d, w, r: [(minute, tool, asset)] if d % n_days == 0 else []


def on_days(days: set[int], tool: str, asset: str, minute: int = 10 * 60 + 30):
    """An extra call on these past days only."""
    return lambda d, w, r: [(minute, tool, asset)] if d in days else []


SUN_THU = frozenset(range(5))
DAY_HOURS = tuple(range(9, 17))
NIGHT_HOURS = (22, 23, 0, 1, 2, 3, 4, 5)


def dana(**kw) -> User:
    return User("Dana", SUN_THU, DAY_HOURS, SUPPORT, **kw)


def lior(extra=None) -> User:
    folders = tuple(("read_file", f"f{i:02d}", 1) for i in range(30))

    def new_folders(d, w, r, extra=extra):
        out = [(13 * 60 + 5, "read_file", f"new{d}")] if r.random() < 0.7 else []
        return out + (extra(d, w, r) if extra else [])

    return User(
        "Lior", SUN_THU, DAY_HOURS, (("search_orders", "orders", 2),) + folders, extra=new_folders
    )


OMER = User("Omer", SUN_THU, DAY_HOURS, SUPPORT + (("refund_order", "orders", 2),))
AVI = User(
    "Avi", SUN_THU, NIGHT_HOURS, SUPPORT, extra=every(2, "refund_order", "orders", 23 * 60 + 35)
)
MAYA = User(
    "Maya",
    WEEKEND,
    DAY_HOURS,
    (("search_orders", "orders", 3), ("read_file", "stock", 3), ("read_file", "orders", 1)),
    steady_every=1,
)
NOA = User(
    "Noa",
    SUN_THU,
    tuple(range(8, 18)),
    (("read_file", "reports", 4), ("search_orders", "orders", 1)),
    steady_every=8,
)


# ---------------------------------------------------------------- scoring helpers


@dataclass
class Fitted:
    """One user's history, fitted by every variant."""

    past: list[Call]
    today_weekday: int
    models: list[Model] = field(default_factory=list)

    def __post_init__(self) -> None:
        obs = observe(self.past, self.today_weekday)
        self.models = [
            Smooth(obs, v) if v.smooth_beta else Model(obs, [c.day for c in self.past], v)
            for v in VARIANTS
        ]

    def score(self, today: Sequence[Call]) -> list[float]:
        """M of the last of today's calls, per variant (today's earlier calls set its hour and run)."""
        calls = [*self.past, *today]
        o = observe(calls, self.today_weekday)[-1]
        return [m.score(o, len(calls) - 1) for m in self.models]


def at(hour: int, minute: int = 5) -> int:
    return hour * 60 + minute


def one(tool: str, asset: str | None, minute: int) -> list[Call]:
    return [Call(0, minute, tool, asset)]


def fit(u: User, seed: int, today_weekday: int = 0, away: range = range(0)) -> Fitted:
    return Fitted(history(u, random.Random(seed), today_weekday, away), today_weekday)


# ---------------------------------------------------------------- the ten scenarios and seven charts


def run(seed: int):
    charts: dict[str, dict[str, list[list[float]]]] = {}
    rows = []

    def pair_row(n, name, hi_name, hi, lo_name, lo, ok_hi=None, ok_lo=None):
        rows.append((n, name, hi_name, hi, lo_name, lo, ok_hi, ok_lo))

    def refund(minute: int = at(10, 30)) -> list[Call]:
        return one("refund_order", "orders", minute)

    # 1 First time using a tool
    d_never, omer = fit(dana(), seed), fit(OMER, seed)
    pair_row(
        1,
        "First time using a tool",
        "Dana: never",
        d_never.score(refund()),
        "Omer: daily",
        omer.score(refund()),
    )
    # 2 A tool used rarely (chart 1)
    work_days = [d for d in range(-HISTORY_DAYS, 0) if d % 7 in SUN_THU]
    chart = {"Any user (Dana-like)": []}
    for count in (0, 1, 2, 5, 10, "every other day", "every day"):
        days = (
            set(work_days[::2])
            if count == "every other day"
            else set(work_days)
            if count == "every day"
            else set(random.Random(seed).sample(work_days, count))
        )
        chart["Any user (Dana-like)"].append(
            fit(dana(extra=on_days(days, "refund_order", "orders")), seed).score(refund())
        )
    d_twice = chart["Any user (Dana-like)"][2]
    avi = fit(AVI, seed)
    avi_refund = avi.score(refund(at(23, 40)))
    chart["Avi"] = [avi_refund]
    charts["1 refund_order uses before"] = chart
    pair_row(2, "A tool used rarely", "Dana: twice", d_twice, "Avi: every other day", avi_refund)
    # 3 A very busy hour (chart 2)
    maya = fit(MAYA, seed, today_weekday=6)
    dana_sun = d_never
    chart = {"Dana": [], "Maya": []}
    for x in (6, 12, 18, 30, 60, 120):
        busy = [Call(0, at(11, 0) + i * 60 // x, "search_orders", "orders") for i in range(x)]
        chart["Dana"].append(dana_sun.score(busy))
        chart["Maya"].append(maya.score(busy))
    charts["2 calls in one hour (6,12,18,30,60,120)"] = chart
    pair_row(
        3,
        "A very busy hour (60 calls)",
        "Dana: usually few",
        chart["Dana"][4],
        "Maya: usually many",
        chart["Maya"][4],
    )
    # 4 A call at night (chart 3)
    chart = {"Dana": [], "Avi": []}
    for h in range(0, 24, 2):
        chart["Dana"].append(dana_sun.score(one("search_orders", "orders", at(h))))
        chart["Avi"].append(avi.score(one("search_orders", "orders", at(h))))
    charts["3 hour of the call (0-22)"] = chart
    pair_row(
        4, "A call at 2 am", "Dana: by day", chart["Dana"][1], "Avi: at night", chart["Avi"][1]
    )
    # 5 A call on the weekend (chart 4)
    chart = {"Dana": [], "Maya": []}
    for wd in (5, 6):
        chart["Dana"].append(
            fit(dana(), seed, today_weekday=wd).score(one("search_orders", "orders", at(11)))
        )
        chart["Maya"].append(
            fit(MAYA, seed, today_weekday=wd).score(one("search_orders", "orders", at(11)))
        )
    charts["4 Friday / Saturday at 11:00"] = chart
    night_dana = charts["3 hour of the call (0-22)"]["Dana"][1]
    pair_row(
        5,
        "A call on Saturday 11:00",
        "Dana: Sun-Thu",
        chart["Dana"][1],
        "Maya: weekends",
        chart["Maya"][1],
        ok_hi=[
            a >= CLEARLY_HIGHER and a < b for a, b in zip(chart["Dana"][1], night_dana, strict=True)
        ],
    )
    # 6 A new folder
    lior_fit = fit(lior(), seed)
    q4 = one("read_file", "Q4-plan", at(10, 30))
    pair_row(
        6,
        "A new folder (Q4-plan)",
        "Dana: never new ones",
        d_never.score(q4),
        "Lior: often new ones",
        lior_fit.score(q4),
    )
    # 7 A rare folder (chart 5)
    chart = {"Dana": [], "Lior": []}
    payroll = one("read_file", "payroll", at(10, 30))
    for count in (1, 2, 5, 10, "every other day", "every day"):
        days = (
            set(work_days[::2])
            if count == "every other day"
            else set(work_days)
            if count == "every day"
            else set(random.Random(seed + 1).sample(work_days, count))
        )
        chart["Dana"].append(
            fit(dana(extra=on_days(days, "read_file", "payroll")), seed).score(payroll)
        )
        chart["Lior"].append(
            fit(lior(extra=on_days(days, "read_file", "payroll")), seed).score(payroll)
        )
    charts["5 payroll opened before"] = chart
    pair_row(
        7,
        "A rare folder (payroll, twice)",
        "Dana: 3 folders",
        chart["Dana"][1],
        "Lior: many folders",
        chart["Lior"][1],
    )
    # 8 A very long session: removed by the author (2026-11-01)
    # 9 A new user (chart 7)
    tal = Fitted([], 0)
    chart = {"Tal": [], "Dana": []}
    rng = random.Random(seed + 2)
    first_day = [Call(0, at(9, 0) + 5 * i, *pick(SUPPORT, rng)) for i in range(12)]
    for i in range(12):
        chart["Tal"].append(tal.score(first_day[: i + 1]))
        chart["Dana"].append(dana_sun.score(first_day[: i + 1]))
    charts["7 Tal's first 12 calls"] = chart
    pair_row(
        9,
        "A new user's first call",
        "Tal: no history",
        chart["Tal"][0],
        "Dana: normal",
        chart["Dana"][0],
        ok_hi=[NEW_USER_BAND[0] <= m <= NEW_USER_BAND[1] for m in chart["Tal"][0]],
    )
    # 10 Back after a long break
    lior_away = fit(lior(), seed, away=range(0, 121))
    noa_away = fit(NOA, seed, away=range(0, 15))
    back = one("read_file", "reports", at(9, 5))
    l_back = lior_away.score(one("search_orders", "orders", at(9, 5)))
    pair_row(
        10,
        "Back after a break",
        "Lior: 4 months",
        l_back,
        "Noa: 2 weeks",
        noa_away.score(back),
        ok_hi=[NEW_USER_BAND[0] <= m <= NEW_USER_BAND[1] for m in l_back],
    )
    return rows, charts


DECK = {  # the deck's own chart values (slides 10-24)
    "1 refund_order uses before": {
        "Any user (Dana-like)": [3.04, 2.60, 2.27, 1.62, 1.09, 0.96, 0.87],
        "Avi": [0.96],
    },
    "2 calls in one hour (6,12,18,30,60,120)": {
        "Dana": [0.81, 0.92, 1.18, 1.97, 2.90, 3.71],
        "Maya": [0.71, 0.73, 0.76, 0.81, 0.89, 1.0],
    },
    "3 hour of the call (0-22)": {
        "Dana": [4.11, 4.11, 4.11, 1.31, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.85, 4.11],
        "Avi": [0.71, 0.71, 0.71, 0.74, 1.53, 4.11, 4.11, 4.11, 4.11, 2.58, 0.80, 0.71],
    },
    "4 Friday / Saturday at 11:00": {"Dana": [2.30, 2.30], "Maya": [0.75, 0.73]},
    "5 payroll opened before": {
        "Dana": [3.46, 2.97, 2.04, 1.31, 0.99, 0.89],
        "Lior": [0.95, 0.85, 0.77, 0.75, 0.74, 0.74],
    },
    "7 Tal's first 12 calls": {
        "Tal": [2, 1.95, 1.9, 1.8, 1.7, 1.55, 1.45, 1.35, 1.25, 1.15, 1.1, 1.05],
        "Dana": [0.71] * 12,
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pinecrest scenarios against the deck's charts.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--plot", type=str, default="")
    args = parser.parse_args()
    rows, charts = run(args.seed)
    names = [v.name for v in VARIANTS]
    print("Ten scenarios: M of the higher-risk user / the lower-risk user, per variant")
    print(f"{'#':>2} {'scenario':<32}" + "".join(f"{n:>26}" for n in names))
    passes = [0] * len(names)
    for n, name, hi_name, hi, lo_name, lo, ok_hi, ok_lo in rows:
        cells = []
        for i in range(len(names)):
            good_hi = ok_hi[i] if ok_hi is not None else hi[i] >= CLEARLY_HIGHER
            good_lo = lo[i] <= NORMAL_MAX
            passes[i] += good_hi and good_lo
            cells.append(
                f"{hi[i]:5.2f}/{lo[i]:4.2f} {'ok' if good_hi and good_lo else ('hi?' if not good_hi else 'lo?') if good_hi or good_lo else 'both?':>5}"
            )
        print(f"{n:>2} {name:<32}" + "".join(f"{c:>26}" for c in cells))
    print(
        f"{'':>2} {'scenarios as the deck expects':<32}"
        + "".join(f"{str(p) + '/' + str(len(rows)):>26}" for p in passes)
    )
    print("\nThe deck's charts against ours (deck, then each variant in order)")
    for title, series in charts.items():
        print(f"\n  {title}")
        for who, per_point in series.items():
            deck = DECK[title].get(who, [])
            print(f"    {who:<22} deck  " + " ".join(f"{x:5.2f}" for x in deck))
            for i, name in enumerate(names):
                print(
                    f"    {'':<22} {name.split()[0]:<5} "
                    + " ".join(f"{p[i]:5.2f}" for p in per_point)
                )
    if args.plot:
        plot(charts, args.plot)


def plot(charts, path: str) -> None:
    """Draw each deck chart (grey dashed) against J4 (jumps) and J4s beta 3 (smooth k)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    shown = {
        "J4 calls, 4 dimensions": ("#C0602A", "-", "plain k"),
        "J4s + weekday 1/16": ("#2F6FB0", "-", "smooth k + weekday"),
    }
    idx = {v.name: i for i, v in enumerate(VARIANTS)}
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for ax, (title, series) in zip(axes.flat, charts.items(), strict=False):
        for who, per_point in series.items():
            deck = DECK[title].get(who, [])
            xs = range(len(per_point))
            alpha = 1 if who in ("Dana", "Any user (Dana-like)", "Tal") else 0.5
            if len(deck) == len(per_point):
                ax.plot(xs, deck, color="#6B7280", ls="--", lw=2, alpha=alpha, label=f"{who}: deck")
            for name, (color, ls, label) in shown.items():
                ax.plot(
                    xs,
                    [p[idx[name]] for p in per_point],
                    color=color,
                    ls=ls,
                    lw=1.8,
                    marker="o",
                    ms=3,
                    alpha=alpha,
                    label=f"{who}: {label}",
                )
        ax.axhline(1, color="#9CA3AF", lw=0.8)
        ax.set_title(title, fontsize=11)
        ax.set_ylim(0.6, 5.2)
        ax.legend(fontsize=7, ncol=2)
    fig.suptitle(
        "Pinecrest: the deck's expected curves (grey dashed) against the 4-dimension formula "
        "counting calls: orange = plain k, blue = smooth k with the weekday split",
        fontsize=13,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    print(f"\nfigure: {path}")


if __name__ == "__main__":
    main()
