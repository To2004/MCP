"""Small-sample statistics for the "Bot Day Check" analysis (standard library only).

Pure functions, no study objects: ranks and Spearman's rho, pooled shares, a two-way percentile
bootstrap (raters, and items within groups), Fleiss' kappa and Krippendorff's alpha (nominal,
ordinal or interval) on a units x categories count table. ``analyse_responses.py`` re-exports
them.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Mapping, Sequence

INTERVAL_LEVEL = 0.95
MIN_RANK_POINTS = 3
MIN_PAIRABLE = 2  # a unit needs two answers to be compared
#: Landis and Koch words for agreement, upper bound inclusive; above the last: "almost perfect".
AGREEMENT_BANDS = ((0.20, "slight"), (0.40, "fair"), (0.60, "moderate"), (0.80, "substantial"))
AGREEMENT_TOP_WORD = "almost perfect"
BELOW_CHANCE_WORD = "less than chance"
NOT_AVAILABLE = "n/a"
NOMINAL, ORDINAL, INTERVAL = "nominal", "ordinal", "interval"

Cells = Mapping[str, Mapping[str, int]]  # rater key -> item id -> answer


def quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolation quantile of an already sorted, non-empty sequence."""
    position = q * (len(sorted_values) - 1)
    below = math.floor(position)
    above = min(below + 1, len(sorted_values) - 1)
    weight = position - below
    return sorted_values[below] * (1 - weight) + sorted_values[above] * weight


def average_ranks(values: Sequence[float]) -> list[float]:
    """Ranks starting at 1, ties sharing their average rank."""
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        for position in range(start, end + 1):
            ranks[order[position]] = (start + end) / 2 + 1
        start = end + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Spearman's rho (Pearson on average ranks); None with fewer than 3 points or no spread."""
    if len(xs) != len(ys) or len(xs) < MIN_RANK_POINTS:
        return None
    rank_x, rank_y = average_ranks(xs), average_ranks(ys)
    mean_x, mean_y = statistics.fmean(rank_x), statistics.fmean(rank_y)
    covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(rank_x, rank_y, strict=True))
    spread_x = sum((a - mean_x) ** 2 for a in rank_x)
    spread_y = sum((b - mean_y) ** 2 for b in rank_y)
    if spread_x == 0 or spread_y == 0:
        return None
    return covariance / math.sqrt(spread_x * spread_y)


def pooled_share(
    cells: Cells, raters: Sequence[str], items: Sequence[str], predicate: Callable[[int], bool]
) -> float | None:
    """Share of the answers (rater x item, with repeats) that satisfy ``predicate``."""
    hits = total = 0
    for rater in raters:
        row = cells.get(rater)
        if not row:
            continue
        for item in items:
            value = row.get(item)
            if value is not None:
                total += 1
                hits += predicate(value)
    return hits / total if total else None


def bootstrap_interval(
    statistic: Callable[[Sequence[str], Sequence[str]], float | None],
    raters: Sequence[str],
    item_groups: Sequence[Sequence[str]],
    draws: int,
    seed_text: str,
) -> tuple[float | None, float | None, int]:
    """Two-way percentile bootstrap: resample raters, and items within each group.

    Returns:
        (low, high, draws that gave a value); (None, None, 0) when nothing can be resampled.
    """
    groups = [list(group) for group in item_groups if group]
    if not raters or not groups or draws <= 0:
        return None, None, 0
    rng = random.Random(seed_text)
    values = []
    for _ in range(draws):
        sample_raters = rng.choices(raters, k=len(raters))
        sample_items = [item for group in groups for item in rng.choices(group, k=len(group))]
        value = statistic(sample_raters, sample_items)
        if value is not None:
            values.append(value)
    if not values:
        return None, None, 0
    values.sort()
    tail = (1 - INTERVAL_LEVEL) / 2
    return quantile(values, tail), quantile(values, 1 - tail), len(values)


def fleiss_kappa(table: Sequence[Sequence[int]]) -> float | None:
    """Fleiss' kappa; rows are items, columns are answer counts. Items with <2 raters are dropped.

    Uses the form that allows a different number of raters per item. It treats the answers as
    unordered categories; ``krippendorff_alpha`` with ``ORDINAL`` respects their order.
    """
    rows = [row for row in table if sum(row) >= MIN_PAIRABLE]
    if not rows:
        return None
    total = sum(sum(row) for row in rows)
    shares = [sum(row[column] for row in rows) / total for column in range(len(rows[0]))]
    agreement = statistics.fmean(
        (sum(count * count for count in row) - sum(row)) / (sum(row) * (sum(row) - 1))
        for row in rows
    )
    chance = sum(share * share for share in shares)
    if chance >= 1:
        return None
    return (agreement - chance) / (1 - chance)


def _distance(metric: str, totals: Sequence[float]) -> Callable[[int, int], float]:
    """Krippendorff's squared difference between categories ``c`` and ``k`` (by position)."""
    if metric == NOMINAL:
        return lambda c, k: 0.0 if c == k else 1.0
    if metric == INTERVAL:
        return lambda c, k: float((c - k) ** 2)
    if metric == ORDINAL:

        def ordinal(c: int, k: int) -> float:
            low, high = min(c, k), max(c, k)
            between = sum(totals[low : high + 1]) - (totals[low] + totals[high]) / 2
            return between * between

        return ordinal
    raise ValueError(f"unknown metric {metric!r}")


def krippendorff_alpha(table: Sequence[Sequence[int]], metric: str = ORDINAL) -> float | None:
    """Krippendorff's alpha on a units x categories count table (categories in order).

    Units with fewer than two answers are not pairable and are dropped. Returns None when there
    is nothing to compare or no spread at all.
    """
    rows = [row for row in table if sum(row) >= MIN_PAIRABLE]
    if not rows:
        return None
    size = len(rows[0])
    coincidence = [[0.0] * size for _ in range(size)]
    for row in rows:
        m = sum(row)
        for c in range(size):
            for k in range(size):
                coincidence[c][k] += row[c] * (row[k] - (c == k)) / (m - 1)
    totals = [sum(coincidence[c]) for c in range(size)]
    n = sum(totals)
    distance = _distance(metric, totals)
    observed = sum(coincidence[c][k] * distance(c, k) for c in range(size) for k in range(size))
    expected = sum(totals[c] * totals[k] * distance(c, k) for c in range(size) for k in range(size))
    if expected == 0:
        return None
    return 1 - (n - 1) * observed / expected


def agreement_words(value: float | None) -> str:
    """Landis and Koch's plain-word band for a kappa or alpha value."""
    if value is None:
        return NOT_AVAILABLE
    if value < 0:
        return BELOW_CHANCE_WORD
    for upper, word in AGREEMENT_BANDS:
        if value <= upper:
            return word
    return AGREEMENT_TOP_WORD
