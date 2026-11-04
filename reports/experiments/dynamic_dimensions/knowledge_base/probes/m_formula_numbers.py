"""Every number in ``behaviour-multiplier-formula.md``, computed from the formula alone.

Usage: ``python3 m_formula_numbers.py [--trials 8000] [--seed 2]``

Part 1 is exact arithmetic: the constants, the guideline table, the new-agent ramp, the
false-alarm bounds and the bottom set by the offset τ. Part 2 is a Monte Carlo of ordinary
(exchangeable) days. It compares two ways to score a call on several dimensions: the strangest
dimension, and the rarest-dimension rank (the same count asked about the call as a whole). Part 3
measures the price of the rank: the M of a call that is new on one dimension only. Nothing here
reads a world or the simulator; it is synthetic. A full run takes about two minutes.
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
from collections.abc import Callable, Sequence

TOP = 5.0  # the static scale runs from 1 to 5, so its full width is x5
WINDOW_DAYS = 90  # H
DIMENSIONS = 8  # K: 5 amounts and 3 values
#: loading w on a common day effect; two dimensions are then correlated at w² (0.25 for w = 0.5)
SHARED_DAY_WEIGHTS = (0.0, 0.5)
GUIDELINE_ROWS = (
    ("every day", 90),
    ("every other day", 45),
    ("about once a week", 13),
    ("about once in 10 days", 9),
    ("about once a month", 3),
    ("once in 90 days", 1),
    ("never in 90 days", 0),
)
RAMP_DAYS = (0, 1, 3, 10, 30, 60, 90)
WINDOWS = (30, 60, 90, 180, 365)
LEVELS = (1.5, 2.0, 3.0, 4.0, 5.0)
EPS = 1e-9
OFFSETS = (1.0, 0.5)  # τ in the frequency (D + τ)/(A + 1); ½ is the mid-p choice
GUIDELINE_BOTTOM = 0.7  # the author's guideline for the bottom of M
POWER_DIMENSIONS = (1, 4, 8, 12)  # K values for the one-novel-dimension check


def exponent(window: int = WINDOW_DAYS, top: float = TOP) -> float:
    """γ = ln(top) / ln(H + 1): a full window of 'never before' lands exactly on ``top``."""
    return math.log(top) / math.log(window + 1)


def multiplier(active: int, as_unusual: float, window: int = WINDOW_DAYS) -> float:
    """M = ((A + 1) / (2D + 1))^γ for A active past days, D of them at least this unusual."""
    return ((active + 1) / (2 * as_unusual + 1)) ** exponent(window)


def false_alarm_bound(level: float, active: int, window: int = WINDOW_DAYS) -> float:
    """P(M >= level) for exchangeable days: ½ (H + 1)^(-log_5 level) + ½ / (A + 1)."""
    return 0.5 * (window + 1) ** (-math.log(level) / math.log(TOP)) + 0.5 / (active + 1)


def sharp_bound(level: float, active: int, window: int = WINDOW_DAYS) -> float:
    """The tie-valid sharper bound: floor((A + 1) t + ½) / (A + 1), with t the frequency cut."""
    cut = 0.5 * (window + 1) ** (-math.log(level) / math.log(TOP))
    return math.floor((active + 1) * cut + 0.5) / (active + 1)


def bottom_for_offset(offset: float, window: int = WINDOW_DAYS) -> float:
    """Lowest M when the frequency is (D + τ)/(A + 1): (τ (H + 1)/(H + τ))^γ."""
    return (offset * (window + 1) / (window + offset)) ** exponent(window)


def offset_for_bottom(bottom: float, window: int = WINDOW_DAYS) -> float:
    """The offset τ whose lowest M equals ``bottom``."""
    target = bottom ** (1 / exponent(window))
    return target * window / (window + 1 - target)


def exact_rate(level: float, active: int = WINDOW_DAYS) -> float:
    """P(M >= level) when D is uniform on 0..A (continuous values, no ties)."""
    hits = sum(1 for d in range(active + 1) if multiplier(active, d) >= level - EPS)
    return hits / (active + 1)


def part_one() -> None:
    """Print the exact numbers: constants, guideline table, ramps and bounds."""
    g = exponent()
    print(f"gamma(H={WINDOW_DAYS}) = {g:.4f}; factor per halving of frequency = {2**g:.4f}")
    for h in WINDOWS:
        print(
            f"  H={h:3d}: gamma={exponent(h):.4f} bottom={multiplier(h, h, h):.3f} "
            f"per halving={2 ** exponent(h):.3f} once before={multiplier(h, 1, h):.2f}"
        )
    print(f"\nGuideline table (A = {WINDOW_DAYS}):")
    for label, d in GUIDELINE_ROWS:
        ratio = (WINDOW_DAYS + 1) / (2 * d + 1)
        print(f"  {label:24s} D={d:2d} ratio={ratio:7.3f} M={multiplier(WINDOW_DAYS, d):.3f}")
    print(f"  new agent (A=0, D=0)     M={multiplier(0, 0):.3f}")
    print("Never before, by days of history:", {a: round(multiplier(a, 0), 2) for a in RAMP_DAYS})
    print("Every day, by days of history:   ", {a: round(multiplier(a, a), 3) for a in RAMP_DAYS})
    mean = sum(multiplier(WINDOW_DAYS, d) for d in range(WINDOW_DAYS + 1)) / (WINDOW_DAYS + 1)
    print(f"Mean M on ordinary days, one dimension (D uniform on 0..{WINDOW_DAYS}): {mean:.3f}")
    print("Top reachable values (A=90):", [round(multiplier(WINDOW_DAYS, d), 2) for d in range(6)])
    print(f"\nFalse alarms per agent-day, one dimension (A = H = {WINDOW_DAYS}):")
    for m in LEVELS:
        bound = false_alarm_bound(m, WINDOW_DAYS)
        print(
            f"  M>={m}: bound={bound:.4f} sharp={sharp_bound(m, WINDOW_DAYS):.4f} "
            f"exact={exact_rate(m):.4f} union over K={DIMENSIONS}: {min(1.0, DIMENSIONS * bound):.3f}"
        )
    print("\nThe bottom of M set by the offset τ in (D + τ)/(A + 1):")
    for tau in OFFSETS:
        print(f"  τ={tau}: bottom={bottom_for_offset(tau):.3f}")
    tau = offset_for_bottom(GUIDELINE_BOTTOM)
    print(f"  τ={tau:.4f}: bottom={bottom_for_offset(tau):.3f} (the guideline {GUIDELINE_BOTTOM})")


def ordinary_days(rng: random.Random, dims: int, weight: float) -> list[list[float]]:
    """H + 1 exchangeable days (index 0 is today) on ``dims`` correlated dimensions."""
    days = []
    for _ in range(WINDOW_DAYS + 1):
        shared = rng.gauss(0, 1)
        own = math.sqrt(1 - weight * weight)
        days.append([weight * shared + own * rng.gauss(0, 1) for _ in range(dims)])
    return days


def as_unusual_counts(days: Sequence[Sequence[float]]) -> list[list[int]]:
    """Per day and dimension, D against the other H days of the window (leave one out)."""
    n, dims = len(days), len(days[0])
    return [
        [sum(1 for j in range(n) if j != i and days[j][k] >= days[i][k]) for k in range(dims)]
        for i in range(n)
    ]


def strangest_dimension(counts: list[list[int]]) -> float:
    """Combiner 1: M of today's most unusual dimension."""
    return multiplier(WINDOW_DAYS, min(counts[0]))


def rarest_dimension_rank(counts: list[list[int]]) -> float:
    """Combiner 2: rank today against past days by their sorted D profiles (most unusual first)."""
    profiles = [sorted(row) for row in counts]
    today = profiles[0]
    return multiplier(WINDOW_DAYS, sum(1 for p in profiles[1:] if p <= today))


def one_novel_dimension(rng: random.Random, dims: int) -> list[list[float]]:
    """Ordinary days, except that today is a strict record on dimension 0."""
    days = ordinary_days(rng, dims, 0.0)
    days[0][0] = max(day[0] for day in days[1:]) + 1.0
    return days


def part_three(trials: int, seed: int) -> None:
    """Power: M of a call that is new on one dimension and ordinary on the others."""
    rng = random.Random(seed)
    print(
        f"\nOne dimension never seen in {WINDOW_DAYS} days, the others ordinary ({trials} calls):"
    )
    for dims in POWER_DIMENSIONS:
        xs = [
            rarest_dimension_rank(as_unusual_counts(one_novel_dimension(rng, dims)))
            for _ in range(trials)
        ]
        at5 = sum(x >= TOP - EPS for x in xs) / len(xs)
        print(f"  K={dims}: median M={statistics.median(xs):.2f} P(M=5)={at5:.3f}")


def part_two(trials: int, seed: int) -> None:
    """Monte Carlo: typical M and false-alarm rates of the two combiners on ordinary days."""
    combiners: dict[str, Callable[[list[list[int]]], float]] = {
        "strangest dimension": strangest_dimension,
        "rarest-dimension rank": rarest_dimension_rank,
    }
    rng = random.Random(seed)
    print(f"\nOrdinary days, K={DIMENSIONS}, {trials} agent-days per row:")
    for weight in SHARED_DAY_WEIGHTS:
        scores: dict[str, list[float]] = {name: [] for name in combiners}
        for _ in range(trials):
            counts = as_unusual_counts(ordinary_days(rng, DIMENSIONS, weight))
            for name, combine in combiners.items():
                scores[name].append(combine(counts))
        for name, xs in scores.items():
            at3 = sum(x >= 3 - EPS for x in xs) / len(xs)
            at5 = sum(x >= TOP - EPS for x in xs) / len(xs)
            print(
                f"  loading {weight} (corr {weight * weight:.2f}): {name:22s} "
                f"median M={statistics.median(xs):.2f} "
                f"P(M>=3)={at3:.4f} P(M=5)={at5:.4f}"
            )


def main() -> None:
    """Parse arguments and print both parts."""
    parser = argparse.ArgumentParser(description="Every number in the M-formula report.")
    parser.add_argument("--trials", type=int, default=8000)
    parser.add_argument("--seed", type=int, default=2)
    args = parser.parse_args()
    part_one()
    part_two(args.trials, args.seed)
    part_three(args.trials // 2, args.seed)


if __name__ == "__main__":
    main()
