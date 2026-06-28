"""Hand-rolled evaluation metrics for ordinal risk bands and binary detection.

Kept dependency-free (no numpy/scipy) so the evaluation scripts run anywhere the
project runs. All functions operate on plain Python numbers/lists.

Two metric families are provided:

* **Ordinal agreement** (for comparing a scorer's bands to an oracle on the same
  cells): quadratic-weighted Cohen's kappa, mean absolute error, Spearman rank
  correlation. These are chance-corrected / magnitude-aware, unlike raw exact
  agreement, which a low-skewed 4-band distribution inflates.
* **Binary detection** (for the dynamic call evaluation): ROC AUC via the
  Mann-Whitney U identity, plus a Wilson confidence interval for any proportion.

The ordinal scale is 1..K (K=4: low/medium/high/critical). Callers map band
strings to ints before calling.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

BANDS = ("low", "medium", "high", "critical")
BAND_RANK = {b: i + 1 for i, b in enumerate(BANDS)}  # low=1 .. critical=4


def quadratic_weighted_kappa(a: Sequence[int], b: Sequence[int], k: int = 4) -> float | None:
    """Cohen's kappa with quadratic weights over a 1..k ordinal scale.

    Returns ``None`` when undefined (fewer than two paired observations, or no
    expected disagreement). QWK rewards near-misses far less harshly than exact
    agreement, which is the right currency for an ordinal risk band.
    """
    if len(a) != len(b) or len(a) < 2:
        return None
    # Confusion and marginals over classes 1..k.
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b, strict=True):
        obs[x - 1][y - 1] += 1.0
    n = float(len(a))
    row = [sum(obs[i]) for i in range(k)]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    w = [[((i - j) ** 2) / ((k - 1) ** 2) for j in range(k)] for i in range(k)]
    num = sum(w[i][j] * obs[i][j] for i in range(k) for j in range(k))
    den = sum(w[i][j] * row[i] * col[j] / n for i in range(k) for j in range(k))
    if den == 0:
        return None
    return 1.0 - num / den


def ordinal_mae(a: Sequence[int], b: Sequence[int]) -> float | None:
    """Mean absolute band distance (0 = identical, k-1 = opposite extremes)."""
    if len(a) != len(b) or not a:
        return None
    return sum(abs(x - y) for x, y in zip(a, b, strict=True)) / len(a)


def _avg_ranks(values: Sequence[float]) -> list[float]:
    """Fractional ranks with ties averaged (1-based), for Spearman."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # average of the 1-based positions i..j
        for t in range(i, j + 1):
            ranks[order[t]] = avg
        i = j + 1
    return ranks


def spearman_rho(a: Sequence[float], b: Sequence[float]) -> float | None:
    """Spearman rank correlation (Pearson on average-ranks). ``None`` if undefined."""
    if len(a) != len(b) or len(a) < 2:
        return None
    ra, rb = _avg_ranks(a), _avg_ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if va == 0 or vb == 0:
        return None
    return cov / (va * vb)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n (default 95%)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def band_distribution(bands: Sequence[str]) -> dict[str, float | int]:
    """Counts per band plus the *over-block* fraction (share rated high|critical)."""
    c = Counter(bands)
    n = sum(c.values())
    over = (c.get("high", 0) + c.get("critical", 0)) / n if n else 0.0
    out: dict[str, float | int] = {b: c.get(b, 0) for b in BANDS}
    out["n"] = n
    out["over_block"] = over
    return out


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> float | None:
    """ROC AUC via the Mann-Whitney U identity, with tie handling.

    ``labels`` are 0/1 (1 = positive/risky). Equals the probability a random
    positive outranks a random negative; 0.5 = chance. ``None`` if one class is
    absent.
    """
    pos = [s for s, y in zip(scores, labels, strict=True) if y == 1]
    neg = [s for s, y in zip(scores, labels, strict=True) if y == 0]
    if not pos or not neg:
        return None
    # Rank-sum over the pooled sample with averaged tie ranks.
    pooled = list(scores)
    ranks = _avg_ranks(pooled)
    rank_pos = sum(r for r, y in zip(ranks, labels, strict=True) if y == 1)
    n_pos, n_neg = len(pos), len(neg)
    u = rank_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def binary_at_threshold(
    scores: Sequence[float], labels: Sequence[int], threshold: float
) -> dict[str, float | int]:
    """Confusion counts and rates for ``predict positive iff score >= threshold``."""
    tp = fp = tn = fn = 0
    for s, y in zip(scores, labels, strict=True):
        pred = 1 if s >= threshold else 0
        if pred and y:
            tp += 1
        elif pred and not y:
            fp += 1
        elif not pred and y:
            fn += 1
        else:
            tn += 1
    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tpr
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {
        "threshold": threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "tpr": tpr, "fpr": fpr, "precision": prec, "recall": rec, "f1": f1,
        "errors": fp + fn,
    }


def best_f1(scores: Sequence[float], labels: Sequence[int]) -> dict[str, float | int]:
    """Sweep every distinct score as a threshold; return the operating point with
    the highest F1 (ties broken toward higher recall). Lets score-based scorers be
    compared at their own best cut rather than an arbitrary fixed one."""
    cands = sorted(set(scores))
    best: dict[str, float | int] | None = None
    for t in cands:
        r = binary_at_threshold(scores, labels, t)
        if best is None or (r["f1"], r["recall"]) > (best["f1"], best["recall"]):
            best = r
    return best or binary_at_threshold(scores, labels, 0.0)


def recall_at_fpr(
    scores: Sequence[float], labels: Sequence[int], max_fpr: float
) -> dict[str, float | int]:
    """Highest recall (TPR) achievable while keeping FPR <= ``max_fpr``.

    The standard conservative-operating-point metric: how many attacks are caught
    when the gate is tuned to almost never block benign traffic. Sweeps thresholds
    at each distinct score (plus a +inf cut that predicts all-negative)."""
    cands = sorted(set(scores)) + [float("inf")]
    best = {"recall": 0.0, "fpr": 0.0, "threshold": float("inf"), "precision": 0.0}
    for t in cands:
        r = binary_at_threshold(scores, labels, t)
        if r["fpr"] <= max_fpr and r["recall"] >= best["recall"]:
            best = {"recall": r["recall"], "fpr": r["fpr"],
                    "threshold": t, "precision": r["precision"]}
    best["max_fpr"] = max_fpr
    return best


def detection_by_class(
    scores: Sequence[float],
    classes: Sequence[str | None],
    labels: Sequence[int],
    threshold: float,
) -> dict[str, tuple[int, int]]:
    """Per attack-class detection at a threshold: {class: (detected, total)}.

    Only positive (label==1) items contribute; ``classes`` aligns with ``scores``."""
    out: dict[str, list[int]] = {}
    for s, c, y in zip(scores, classes, labels, strict=True):
        if y != 1:
            continue
        key = c or "?"
        d = out.setdefault(key, [0, 0])
        d[1] += 1
        if s >= threshold:
            d[0] += 1
    return {k: (v[0], v[1]) for k, v in sorted(out.items())}
