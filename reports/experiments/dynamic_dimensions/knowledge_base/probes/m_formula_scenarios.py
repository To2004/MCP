"""Scenario checks for the one-formula behaviour multiplier and its 11 dimensions.

Usage: ``python3 -I m_formula_scenarios.py [--seed 101] [--routine-days 40]``

A small prototype, not the engine. One synthetic agent with a stable habit gets 90 active days of
history; then each scenario builds one "today" and scores the calls it injects. Every scenario
states its expectation before it runs (quiet, rise, top). Two designs are scored side by side:
"proposed" (the 11 dimensions as first proposed) and "fixed" (three fixes the first run called
for: Step tells a never-touched asset from a blind write, Tool on asset is a frequency among the
days that asset was touched, and Area, the asset's folder, is a 12th dimension). The script prints
M per scenario with PASS/FAIL and exits 1 if the fixed design fails a check. Synthetic data only:
these are design checks, not results. See ``behaviour-multiplier-formula.md``.
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace

WINDOW_DAYS = 90
TOP = 5.0
GAMMA = math.log(TOP) / math.log(WINDOW_DAYS + 1)
HOUR_MIN = 60
REPEAT_MIN = 10
NOTHING, NEW = "nothing", "new"  # Step's "before": nothing in the last hour; never touched
PROBE, NEXT = "probe", "next"  # tags of the calls a scenario scores

# Expectations, fixed before running.
QUIET_MAX = 1.75  # "about once in 10 days" on one dimension
RISE_MIN = 2.5  # "about once a month" on one dimension
ALERT_LINE = 3.0
ROUTINE_MEDIAN_MAX = 1.25
ROUTINE_HIGH_SHARE_MAX = 0.05

QUANTITIES = ("call_rate", "breadth", "repetition", "read_volume")
PER_TOOL = ("tool_rate", "request_size")  # history: the days the agent used this tool
CATEGORIES = ("tool", "asset", "tool_on_asset", "hour", "step")
AREA = "area"

WORK_FILES = tuple(f"src/mod{i:02d}.py" for i in range(40))
CORE_FILES = WORK_FILES[:10]
README, SRC_DIR, TESTS = "README.md", "src", "tests"
DATA_FILES = tuple(f"data/r{i:03d}.csv" for i in range(80))


@dataclass(frozen=True)
class Design:
    """Which version of the dimensions to score with."""

    name: str
    step_new: bool = False  # Step: "never touched this asset" apart from "nothing in the hour"
    pair_per_asset: bool = False  # Tool on asset: frequency among the days the asset was touched
    area: bool = False  # Area: the asset's folder, a 12th dimension


PROPOSED = Design("proposed")
FIXED = Design("fixed", step_new=True, pair_per_asset=True, area=True)


def categories(design: Design) -> tuple[str, ...]:
    """The category dimensions of a design."""
    return CATEGORIES + ((AREA,) if design.area else ())


def folder(asset: str) -> str:
    """The asset's folder (the asset itself at the top level)."""
    return asset.rsplit("/", 1)[0] if "/" in asset else asset


@dataclass(frozen=True)
class Call:
    """One tool call: minute of the day, tool, touched asset, argument and reply sizes."""

    minute: int
    tool: str
    asset: str | None
    arg_bytes: int
    reply_bytes: int
    tag: str = ""


@dataclass(frozen=True)
class Features:
    """A call's value on every dimension (quantities as doublings)."""

    quantity: dict[str, int]
    per_tool: dict[str, int]
    tool: str
    category: dict[str, object]


@dataclass
class DaySummary:
    """A day's peaks: largest doubling per quantity (and per tool), values used per category."""

    quantity: dict[str, int]
    per_tool: dict[str, dict[str, int]]
    category: dict[str, set[object]]


def doubling(amount: int) -> int:
    """The doubling an amount falls in: 0 for none, then 1, 2-3, 4-7, 8-15, ..."""
    return max(0, int(amount)).bit_length()


def features(calls: Sequence[Call], known: frozenset[str], design: Design) -> list[Features]:
    """Every call's dimension values; ``calls`` is one day sorted by minute, ``known`` the assets
    of earlier days."""
    out = []
    for i, call in enumerate(calls):
        hour = [c for c in calls[: i + 1] if call.minute - c.minute < HOUR_MIN]
        before = hour[:-1]  # Read volume sees only replies that have already arrived
        recent = [c for c in hour if call.minute - c.minute < REPEAT_MIN]
        pair = (call.tool, call.asset)
        previous = next((c.tool for c in reversed(before) if c.asset == call.asset), NOTHING)
        seen_today = any(c.asset == call.asset for c in calls[:i])
        if design.step_new and previous == NOTHING and call.asset not in known and not seen_today:
            previous = NEW
        has_asset = call.asset is not None
        out.append(
            Features(
                quantity={
                    "call_rate": doubling(len(hour)),
                    "breadth": doubling(len({(c.tool, c.asset) for c in hour})),
                    "repetition": doubling(sum(1 for c in recent if (c.tool, c.asset) == pair)),
                    "read_volume": doubling(sum(c.reply_bytes for c in before)),
                },
                per_tool={
                    "tool_rate": doubling(sum(1 for c in hour if c.tool == call.tool)),
                    "request_size": doubling(call.arg_bytes),
                },
                tool=call.tool,
                category={
                    "tool": call.tool,
                    "asset": call.asset,
                    "tool_on_asset": pair if has_asset else None,
                    "hour": call.minute // HOUR_MIN,
                    "step": (previous, call.tool) if has_asset else None,
                    **({AREA: folder(call.asset) if call.asset else None} if design.area else {}),
                },
            )
        )
    return out


def summarise(feats: Iterable[Features], design: Design) -> DaySummary:
    """The day's peak on every dimension."""
    day = DaySummary({}, {d: {} for d in PER_TOOL}, {d: set() for d in categories(design)})
    for f in feats:
        for dim, value in f.quantity.items():
            day.quantity[dim] = max(day.quantity.get(dim, 0), value)
        for dim, value in f.per_tool.items():
            day.per_tool[dim][f.tool] = max(day.per_tool[dim].get(f.tool, 0), value)
        for dim, value in f.category.items():
            if value is not None:
                day.category[dim].add(value)
    return day


def frequency(at_least: int, active: int) -> float:
    """f = (n + ½)/(A + 1): how often something at least this unusual happened."""
    return (at_least + 0.5) / (active + 1)


def multiplier(active: int, at_least: int) -> float:
    """M = ((A + 1)/(2D + 1))^γ."""
    return ((active + 1) / (2 * at_least + 1)) ** GAMMA


def leave_one_out(values: Sequence[float | None], j: int, larger_is_rarer: bool) -> float:
    """f of day j against the other days on which the dimension applied (1.0 if it did not)."""
    ref = values[j]
    if ref is None:
        return 1.0
    others = [v for k, v in enumerate(values) if k != j and v is not None]
    if larger_is_rarer:
        at_least = sum(1 for v in others if v >= ref)
    else:
        at_least = sum(1 for v in others if v <= ref)
    return frequency(at_least, len(others))


def category_rarity(window: Sequence[DaySummary], dim: str) -> tuple[Counter, list[int | None]]:
    """Days each value was used on, and each day's rarest value (count over the other days)."""
    counts = Counter(v for day in window for v in day.category[dim])
    rarest = [min((counts[v] - 1 for v in day.category[dim]), default=None) for day in window]
    return counts, rarest


def pair_frequency(used: int, touched: int) -> float:
    """Tool on asset, fixed design: how often this tool, among the days the asset was touched."""
    return frequency(used, touched)


def day_frequencies(window: Sequence[DaySummary], design: Design) -> list[dict[str, float]]:
    """Per day, f on every dimension, each day against all other days of the window."""
    n = len(window)
    out: list[dict[str, float]] = [{} for _ in range(n)]
    for dim in QUANTITIES:
        peaks = [day.quantity.get(dim) for day in window]
        for j in range(n):
            out[j][dim] = leave_one_out(peaks, j, larger_is_rarer=True)
    for dim in PER_TOOL:
        tools = {t for day in window for t in day.per_tool[dim]}
        by_tool = {t: [day.per_tool[dim].get(t) for day in window] for t in tools}
        for j in range(n):
            used = window[j].per_tool[dim]
            out[j][dim] = min((leave_one_out(by_tool[t], j, True) for t in used), default=1.0)
    pair_days = Counter(p for day in window for p in day.category["tool_on_asset"])
    asset_days = Counter(a for day in window for a in day.category["asset"])
    for dim in categories(design):
        if dim == "tool_on_asset" and design.pair_per_asset:
            for j in range(n):
                out[j][dim] = min(
                    (
                        pair_frequency(pair_days[p] - 1, asset_days[p[1]] - 1)
                        for p in window[j].category[dim]
                    ),
                    default=1.0,
                )
            continue
        _, rarest = category_rarity(window, dim)
        for j in range(n):
            out[j][dim] = leave_one_out(rarest, j, larger_is_rarer=False)
    return out


def call_frequencies(
    history: Sequence[DaySummary], today: DaySummary, f: Features, design: Design
) -> dict:
    """f on every dimension for one call of today, against the past days."""
    out: dict[str, float] = {}
    for dim in QUANTITIES:
        past = [day.quantity[dim] for day in history if dim in day.quantity]
        out[dim] = frequency(sum(1 for v in past if v >= f.quantity[dim]), len(past))
    for dim in PER_TOOL:
        past = [day.per_tool[dim][f.tool] for day in history if f.tool in day.per_tool[dim]]
        out[dim] = frequency(sum(1 for v in past if v >= f.per_tool[dim]), len(past))
    window = [*history, today]
    for dim in categories(design):
        value = f.category[dim]
        if value is None:
            out[dim] = 1.0
            continue
        if dim == "tool_on_asset" and design.pair_per_asset:
            used = sum(1 for day in history if value in day.category[dim])
            touched = sum(1 for day in history if value[1] in day.category["asset"])
            out[dim] = pair_frequency(used, touched)
            continue
        counts, rarest = category_rarity(window, dim)
        past = [r for r in rarest[:-1] if r is not None]
        out[dim] = frequency(sum(1 for r in past if r <= counts[value] - 1), len(past))
    return out


def profile(freqs: dict[str, float]) -> tuple[float, ...]:
    """The rarest-dimension profile: frequencies sorted, most unusual first."""
    return tuple(sorted(freqs.values()))


def known_assets(history: Sequence[DaySummary]) -> frozenset[str]:
    """Every asset the agent touched in its history."""
    return frozenset(a for day in history for a in day.category["asset"])


def score_call(
    history: Sequence[DaySummary], calls: Sequence[Call], index: int, design: Design
) -> tuple:
    """M of calls[index] (the day so far), with its per-dimension frequencies."""
    feats = features(calls[: index + 1], known_assets(history), design)
    today = summarise(feats, design)
    past_profiles = [profile(p) for p in day_frequencies([*history, today], design)[:-1]]
    freqs = call_frequencies(history, today, feats[-1], design)
    mine = profile(freqs)
    return multiplier(len(history), sum(1 for p in past_profiles if p <= mine)), freqs


def score_day(history: Sequence[DaySummary], calls: Sequence[Call], design: Design) -> float:
    """M of a whole day (its peak profile), the unit of the false-alarm bound."""
    today = summarise(features(calls, known_assets(history), design), design)
    profiles = [profile(p) for p in day_frequencies([*history, today], design)]
    return multiplier(len(history), sum(1 for p in profiles[:-1] if p <= profiles[-1]))


@dataclass(frozen=True)
class Habit:
    """The synthetic agent's habit."""

    reads_before_write: bool = True
    new_file_chance: float = 0.1
    tasks_per_hour: tuple[int, int] = (2, 4)


def size(rng: random.Random, typical: int) -> int:
    """A byte count around ``typical``."""
    return max(1, int(typical * rng.lognormvariate(0, 0.4)))


def routine_day(rng: random.Random, habit: Habit, day: int, busy: float = 1.0) -> list[Call]:
    """One ordinary working day: list, search, read and write the usual files, 8-18 h."""
    start, end = rng.choice((8, 9, 9, 10)), rng.choice((16, 17, 17, 18))
    calls = [Call(start * HOUR_MIN + rng.randrange(5), "read_file", README, 60, size(rng, 4000))]
    for hour in range(start, end):
        for _ in range(round(rng.randint(*habit.tasks_per_hour) * busy)):
            m = hour * HOUR_MIN + rng.randrange(50)
            if rng.random() < 0.3:
                calls.append(Call(m, "list_dir", SRC_DIR, 40, size(rng, 1500)))
            if rng.random() < 0.4:
                calls.append(Call(m + 1, "search", SRC_DIR, 80, size(rng, 3000)))
            target = rng.choice(CORE_FILES) if rng.random() < 0.7 else rng.choice(WORK_FILES)
            write = rng.random() < 0.5
            if habit.reads_before_write or not write:
                calls.append(Call(m + 2, "read_file", target, 60, size(rng, 6000)))
            if write:
                calls.append(Call(m + 5, "write_file", target, size(rng, 2000), 80))
    if rng.random() < habit.new_file_chance:
        m = rng.randrange(start * HOUR_MIN, end * HOUR_MIN)
        calls.append(Call(m, "write_file", f"src/new_{day}.py", size(rng, 2000), 80))
    return sorted(calls, key=lambda c: c.minute)


Extra = Callable[[int, list[Call]], list[Call]]


def build_history(
    seed: int, habit: Habit, design: Design, extra: Extra | None = None
) -> list[DaySummary]:
    """90 active days of the habit, optionally changed per day by ``extra``."""
    rng = random.Random(seed)
    days: list[DaySummary] = []
    for d in range(WINDOW_DAYS):
        calls = routine_day(rng, habit, d)
        if extra is not None:
            calls = sorted(extra(d, calls), key=lambda c: c.minute)
        days.append(summarise(features(calls, known_assets(days), design), design))
    return days


def at(hour: int, minute: int = 0) -> int:
    """Minute of the day."""
    return hour * HOUR_MIN + minute


def unused_familiar_file(calls: Sequence[Call]) -> str:
    """A working file the agent knows but has not touched today."""
    touched = {c.asset for c in calls}
    return next(f for f in WORK_FILES[10:] if f not in touched)


def monthly_report(start: int) -> list[Call]:
    """Read every working and data file once within one hour."""
    assets = WORK_FILES + DATA_FILES
    return [
        Call(start + i * 50 // len(assets), "read_file", a, 60, 5000, PROBE)
        for i, a in enumerate(assets)
    ]


def with_probe(base: list[Call], injected: list[Call]) -> list[Call]:
    """Today: the routine day plus the scenario's calls (tagged), sorted by minute."""
    return sorted(base + injected, key=lambda c: c.minute)


def score_tagged(
    history: Sequence[DaySummary], calls: Sequence[Call], tag: str, design: Design
) -> tuple:
    """The highest M among calls with ``tag``, and that call's frequencies."""
    scored = [score_call(history, calls, i, design) for i, c in enumerate(calls) if c.tag == tag]
    return max(scored, key=lambda s: s[0])


def drivers(freqs: dict[str, float], k: int = 2) -> str:
    """The k most unusual dimensions of a call."""
    rarest = sorted(freqs.items(), key=lambda kv: kv[1])[:k]
    return ", ".join(f"{d} {f:.3f}" for d, f in rarest)


Row = tuple[str, str, float, str, bool]


def run(design: Design, seed: int, routine_days: int) -> list[Row]:
    """Every scenario under one design."""
    habit = Habit()
    history = build_history(seed, habit, design)
    base = routine_day(random.Random(seed + 1), habit, WINDOW_DAYS)
    rows: list[Row] = []

    def check(name: str, expect: str, m: float, freqs: dict, ok: bool) -> None:
        rows.append((name, expect, m, drivers(freqs), ok))

    # Calibration: ordinary days, whole-day M (the unit of the bound).
    routine = [
        score_day(history, routine_day(random.Random(1000 + i), habit, WINDOW_DAYS), design)
        for i in range(routine_days)
    ]
    high = sum(m >= ALERT_LINE for m in routine) / len(routine)
    med = statistics.median(routine)
    rows.append(
        (
            f"routine days (n={len(routine)})",
            f"median ≤ {ROUTINE_MEDIAN_MAX}, ≥{ALERT_LINE} on ≤ {ROUTINE_HIGH_SHARE_MAX:.0%}",
            med,
            f"≥{ALERT_LINE} on {high:.0%} of days, max {max(routine):.2f}",
            med <= ROUTINE_MEDIAN_MAX and high <= ROUTINE_HIGH_SHARE_MAX,
        )
    )
    busy = [
        score_day(history, routine_day(random.Random(2000 + i), habit, WINDOW_DAYS, 1.3), design)
        for i in range(10)
    ]
    rows.append(
        (
            "busy day, 1.3x the work (n=10)",
            f"median ≤ {QUIET_MAX}",
            statistics.median(busy),
            f"max {max(busy):.2f}",
            statistics.median(busy) <= QUIET_MAX,
        )
    )

    # Quiet.
    fresh = [score_call([], base, i, design)[0] for i in range(len(base))]
    rows.append(
        (
            "brand-new agent id",
            "every call = 1",
            max(fresh),
            "A = 0",
            all(abs(m - 1) < 1e-9 for m in fresh),
        )
    )
    tests_call = [Call(at(11), "run_tests", TESTS, 30, 2000, PROBE)]

    def runs_tests(d: int, calls: list[Call]) -> list[Call]:
        return calls + ([replace(tests_call[0], tag="")] if d >= WINDOW_DAYS - 5 else [])

    m, fr = score_tagged(
        build_history(seed, habit, design, runs_tests), with_probe(base, tests_call), PROBE, design
    )
    check("new tool after 5 days of daily use", f"≤ {QUIET_MAX}", m, fr, m <= QUIET_MAX)
    blind = Habit(reads_before_write=False)
    target = unused_familiar_file(base)
    blind_write = [Call(at(14, 30), "write_file", target, 2000, 80, PROBE)]
    m, fr = score_tagged(
        build_history(seed, blind, design), with_probe(base, blind_write), PROBE, design
    )
    check("blind write, agent always writes blind", f"≤ {QUIET_MAX}", m, fr, m <= QUIET_MAX)

    def monthly(d: int, calls: list[Call]) -> list[Call]:
        return (
            calls + [replace(c, tag="") for c in monthly_report(at(15))] if d % 22 == 5 else calls
        )

    m, fr = score_tagged(
        build_history(seed, habit, design, monthly),
        with_probe(base, monthly_report(at(15))),
        PROBE,
        design,
    )
    check("monthly report (4 in history)", f"< {ALERT_LINE}", m, fr, m < ALERT_LINE)

    # Rise.
    core = CORE_FILES[0]
    singles = {
        "new tool, first day": tests_call,
        "new asset": [Call(at(14), "read_file", "secrets/keys.txt", 60, 4000, PROBE)],
        "familiar asset, new tool on it": [
            Call(at(14), "read_file", README, 60, 4000),
            Call(at(14, 2), "write_file", README, 2000, 80, PROBE),
        ],
        "sweep: 35 familiar files in an hour": [
            Call(at(14, i), "read_file", f, 60, 6000, PROBE) for i, f in enumerate(WORK_FILES[:35])
        ],
        "read + write at 3 am": [
            Call(at(3), "read_file", core, 60, 6000, PROBE),
            Call(at(3, 2), "write_file", core, 2000, 80, PROBE),
        ],
        "blind write on a familiar file": blind_write,
        "30 writes in an hour": [
            c
            for i in range(30)
            for c in (
                Call(at(14, i), "read_file", CORE_FILES[i % 10], 60, 6000),
                Call(at(14, i), "write_file", CORE_FILES[i % 10], 2000, 80, PROBE),
            )
        ],
        "2 MB request": [
            Call(at(14), "read_file", core, 60, 6000),
            Call(at(14, 2), "write_file", core, 2_000_000, 80, PROBE),
        ],
        "same call 25 times in 10 min": [
            Call(at(14, i * 10 // 25), "read_file", core, 60, 6000, PROBE) for i in range(25)
        ],
    }
    single_scores = []
    for name, injected in singles.items():
        m, fr = score_tagged(history, with_probe(base, injected), PROBE, design)
        single_scores.append(m)
        check(name, f"≥ {RISE_MIN}", m, fr, m >= RISE_MIN)
    big_read = [
        Call(at(14), "read_file", core, 60, 50_000_000, PROBE),
        Call(at(14, 5), "list_dir", SRC_DIR, 40, 1500, NEXT),
    ]
    today = with_probe(base, big_read)
    m, fr = score_tagged(history, today, PROBE, design)
    check("50 MB read: the read itself", "low (reply not yet seen)", m, fr, True)
    m, fr = score_tagged(history, today, NEXT, design)
    single_scores.append(m)
    check("50 MB read: the next call", f"≥ {RISE_MIN}", m, fr, m >= RISE_MIN)
    several = [
        Call(at(3, i // 2), "read_file", f"secrets/k{i:02d}", 60, 6000, PROBE) for i in range(40)
    ]
    m, fr = score_tagged(history, with_probe(base, several), PROBE, design)
    check(
        "several at once: 3 am, 40 new assets",
        f"= {TOP:.0f} and ≥ every single",
        m,
        fr,
        m >= TOP - 1e-9 and m >= max(single_scores),
    )

    return rows


def main() -> None:
    """Score every scenario under both designs and print one PASS/FAIL table."""
    parser = argparse.ArgumentParser(description="Scenario checks for the one-formula M.")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--routine-days", type=int, default=40)
    args = parser.parse_args()
    before = run(PROPOSED, args.seed, args.routine_days)
    after = run(FIXED, args.seed, args.routine_days)
    width = max(len(r[0]) for r in before)
    print(f"{'scenario':<{width}}  {PROPOSED.name:>14}  {FIXED.name:>11}  expected / why (fixed)")
    for (name, expect, m0, _, ok0), (_, _, m1, why, ok1) in zip(before, after, strict=True):
        mark0, mark1 = "ok" if ok0 else "FAIL", "ok" if ok1 else "FAIL"
        print(f"{name:<{width}}  {m0:5.2f} {mark0:>4}  {m1:5.2f} {mark1:>4}  [{expect}] {why}")
    for design, rows in ((PROPOSED, before), (FIXED, after)):
        print(f"{design.name}: {sum(r[4] for r in rows)}/{len(rows)} checks pass")
    sys.exit(0 if all(r[4] for r in after) else 1)


if __name__ == "__main__":
    main()
