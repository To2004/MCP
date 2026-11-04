"""General statistics for the v5 held-out evaluation (spec sections 6.1 and 6.5; R2-8).

Nothing here knows about agents, days or episodes; :mod:`heldout_metrics` builds the endpoints
on top of it. The unit of replication is the **world**: every interval and test resamples or
permutes whole worlds and nothing inside them (R2-8).

- :func:`wilson`, :func:`binomial_upper_tail`: one binomial count;
- :func:`holm`: Holm's step-down adjustment;
- :func:`world_bootstrap`, :func:`paired_world_bootstrap`, :func:`bootstrap_p_above`: the
  world-only bootstrap (B = 10,000, percentile or BCa);
- :func:`sign_flip_test`, :func:`discordance_by_world`: the world-level sign-flip test of paired
  per-episode discordance (Hyp1);
- :func:`wilcoxon_signed_rank`: the Wilcoxon signed-rank test over worlds, for agent-day rates
  (spec 6.5) and Hyp6 (v5's benign rate at x3 below v4's: pass d_w = v5_w - v4_w with
  ``alternative="less"``).

Every number these functions give on a simulator world is a development-world or synthetic
number until it comes from a frozen held-out run.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
from numpy.typing import ArrayLike

# ── frozen constants (spec 6.1, 6.5) ─────────────────────────────────────────────────────────
WILSON_Z = 1.959963984540054  # two-sided 95%
CONFIDENCE = 0.95
BOOTSTRAP_B = 10_000  # world resamples (R2-8)
BOOTSTRAP_SEED = 20_261_026
MIN_BOOTSTRAP_WORLDS = 2  # fewer worlds: tests fall back to the exact binomial
SIGN_FLIP_EXACT_MAX = 20  # exact enumeration up to 2^20 sign patterns
SIGN_FLIP_DRAWS = 100_000  # Monte Carlo draws above that
SIGN_FLIP_CHUNK = 10_000
SIGN_FLIP_SEED = 20_261_027
RELATIVE_TIE = 1e-12  # sums within this relative distance of the observed one count as ties
HOLM_ALPHA = 0.05
WILCOXON_EXACT_MAX = 30  # exact signed-rank null distribution up to this many ranked worlds
GREATER, LESS, TWO_SIDED = "greater", "less", "two-sided"
ALTERNATIVES = (GREATER, LESS, TWO_SIDED)
ZERO_WILCOX, ZERO_PRATT = "wilcox", "pratt"
ZERO_METHODS = (ZERO_WILCOX, ZERO_PRATT)
HALF = 0.5


# ── one binomial count ───────────────────────────────────────────────────────────────────────
def wilson(k: float, n: float, z: float = WILSON_Z) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (NaN, NaN when n = 0)."""
    if n == 0:
        return (math.nan, math.nan)
    if not 0 <= k <= n:
        raise ValueError(f"need 0 <= k <= n, not k={k}, n={n}")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def binomial_upper_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), exact (log-space sum)."""
    if n < 0 or not 0 <= p <= 1:
        raise ValueError(f"need n >= 0 and 0 <= p <= 1, not n={n}, p={p}")
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p == 0:
        return 0.0
    if p == 1:
        return 1.0
    i = np.arange(k, n + 1, dtype=np.float64)
    log_choose = math.lgamma(n + 1) - np.array(
        [math.lgamma(x + 1) + math.lgamma(n - x + 1) for x in i]
    )
    log_pmf = log_choose + i * math.log(p) + (n - i) * math.log1p(-p)
    top = log_pmf.max()
    return float(min(1.0, math.exp(top) * np.exp(log_pmf - top).sum()))


# ── Holm ─────────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class HolmResult:
    """Holm's step-down procedure: rejections and adjusted p-values, in input order."""

    reject: np.ndarray
    adjusted: np.ndarray
    alpha: float


def holm(p_values: ArrayLike, alpha: float = HOLM_ALPHA) -> HolmResult:
    """Holm (1979): sort p ascending; adjusted p_(i) = max over j <= i of min(1, (m - j + 1)
    p_(j)); reject where the adjusted p is at most alpha."""
    p = np.asarray(p_values, dtype=np.float64)
    if p.ndim != 1 or np.isnan(p).any() or ((p < 0) | (p > 1)).any():
        raise ValueError("p_values must be a one-dimensional array of values in [0, 1]")
    m = len(p)
    order = np.argsort(p, kind="stable")
    stepped = np.minimum(1.0, (m - np.arange(m)) * p[order])
    adjusted = np.empty(m)
    adjusted[order] = np.maximum.accumulate(stepped) if m else stepped
    return HolmResult(reject=adjusted <= alpha, adjusted=adjusted, alpha=alpha)


# ── world-only bootstrap (R2-8) ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Interval:
    """A world-bootstrap estimate: the plug-in value, the SE over resamples, the two-sided
    interval at ``level`` and one-sided bounds at ``level``."""

    estimate: float
    se: float
    lower: float
    upper: float
    lower_one_sided: float
    upper_one_sided: float
    level: float
    b: int  # resamples with a defined statistic
    method: str


def bootstrap_counts(n_worlds: int, b: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED) -> np.ndarray:
    """``b`` x ``n_worlds`` resample counts: how often each world is drawn in each resample.
    Share one matrix across arms to pair them."""
    if n_worlds < 1 or b < 1:
        raise ValueError(f"need n_worlds >= 1 and b >= 1, not {n_worlds}, {b}")
    rng = np.random.default_rng(seed)
    probs = np.full(n_worlds, 1.0 / n_worlds)
    return rng.multinomial(n_worlds, probs, size=b).astype(np.float64)


def _per_world(num: ArrayLike, den: ArrayLike | None) -> tuple[np.ndarray, np.ndarray]:
    top = np.asarray(num, dtype=np.float64)
    bottom = np.ones_like(top) if den is None else np.asarray(den, dtype=np.float64)
    if top.ndim != 1 or top.shape != bottom.shape or len(top) == 0:
        raise ValueError("num and den must be non-empty one-dimensional arrays of one length")
    if np.isnan(top).any() or np.isnan(bottom).any() or (bottom < 0).any():
        raise ValueError("num must not be NaN; den must be non-negative")
    return top, bottom


def _ratio(counts: np.ndarray, num: np.ndarray, den: np.ndarray) -> np.ndarray:
    top, bottom = counts @ num, counts @ den
    return np.divide(top, bottom, out=np.full(len(top), np.nan), where=bottom > 0)


def _jackknife(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    top, bottom = num.sum() - num, den.sum() - den
    return np.divide(top, bottom, out=np.full(len(top), np.nan), where=bottom > 0)


def _bca_probs(
    estimate: float, boot: np.ndarray, jack: np.ndarray, probs: np.ndarray
) -> np.ndarray | None:
    """BCa-adjusted quantile levels (Efron and Tibshirani), or None when the correction is
    undefined: z0 from the share of resamples below the estimate, the acceleration from the
    leave-one-world-out jackknife."""
    share = (np.sum(boot < estimate) + HALF * np.sum(boot == estimate)) / len(boot)
    jack = jack[~np.isnan(jack)]
    if not 0 < share < 1 or len(jack) < MIN_BOOTSTRAP_WORLDS:
        return None
    nd = NormalDist()
    z0 = nd.inv_cdf(share)
    dev = jack.mean() - jack
    spread = float(np.sum(dev**2))
    accel = float(np.sum(dev**3)) / (6 * spread**1.5) if spread > 0 else 0.0
    out = []
    for p in probs:
        zp = nd.inv_cdf(float(p))
        out.append(nd.cdf(z0 + (z0 + zp) / (1 - accel * (z0 + zp))))
    return np.array(out)


def _interval(
    estimate: float,
    boot: np.ndarray,
    level: float,
    method: str,
    jack: np.ndarray | None,
) -> Interval:
    valid = boot[~np.isnan(boot)]
    if len(valid) == 0:
        raise ValueError("no bootstrap resample has a defined statistic")
    probs = np.array([(1 - level) / 2, (1 + level) / 2, 1 - level, level])
    used = method
    if method == "bca":
        adjusted = _bca_probs(estimate, valid, jack, probs) if jack is not None else None
        if adjusted is None:
            used = "percentile (BCa undefined)"
        else:
            probs = adjusted
    elif method != "percentile":
        raise ValueError(f"method must be 'percentile' or 'bca', not {method!r}")
    q = np.quantile(valid, probs)
    return Interval(
        estimate=estimate,
        se=float(valid.std(ddof=1)) if len(valid) > 1 else 0.0,
        lower=float(q[0]),
        upper=float(q[1]),
        lower_one_sided=float(q[2]),
        upper_one_sided=float(q[3]),
        level=level,
        b=len(valid),
        method=used,
    )


def world_bootstrap(
    num: ArrayLike,
    den: ArrayLike | None = None,
    *,
    b: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
    level: float = CONFIDENCE,
    method: str = "percentile",
    counts: np.ndarray | None = None,
) -> Interval:
    """World-only bootstrap of the pooled ratio sum(num) / sum(den), one entry per world.

    With ``den`` None the statistic is the mean over worlds (a per-world pAUC); with counts
    (alerts, agent-days) it is the pooled rate. Worlds are resampled whole; nothing inside a
    world is (R2-8). ``counts`` reuses a :func:`bootstrap_counts` matrix to pair statistics.
    """
    top, bottom = _per_world(num, den)
    w = bootstrap_counts(len(top), b, seed) if counts is None else counts
    if w.shape[1] != len(top):
        raise ValueError(f"counts has {w.shape[1]} worlds, the data {len(top)}")
    if bottom.sum() <= 0:
        raise ValueError("the denominator sums to zero")
    estimate = float(top.sum() / bottom.sum())
    return _interval(estimate, _ratio(w, top, bottom), level, method, _jackknife(top, bottom))


def paired_world_bootstrap(
    num_a: ArrayLike,
    num_b: ArrayLike,
    den_a: ArrayLike | None = None,
    den_b: ArrayLike | None = None,
    *,
    b: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
    level: float = CONFIDENCE,
    counts: np.ndarray | None = None,
) -> Interval:
    """World-paired bootstrap of (ratio a) - (ratio b): both arms see the same resampled
    worlds. Its SE times 1.64 is the spec's margin (section 6.1)."""
    ta, ba = _per_world(num_a, den_a)
    tb, bb = _per_world(num_b, den_b)
    if len(ta) != len(tb):
        raise ValueError("both arms must be measured on the same worlds")
    if ba.sum() <= 0 or bb.sum() <= 0:
        raise ValueError("a denominator sums to zero")
    w = bootstrap_counts(len(ta), b, seed) if counts is None else counts
    estimate = float(ta.sum() / ba.sum() - tb.sum() / bb.sum())
    boot = _ratio(w, ta, ba) - _ratio(w, tb, bb)
    return _interval(estimate, boot, level, "percentile", None)


def bootstrap_p_above(
    num: ArrayLike,
    den: ArrayLike | None,
    bound: float,
    *,
    b: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
    counts: np.ndarray | None = None,
) -> float:
    """One-sided world-bootstrap p-value for H0: ratio <= bound against ratio > bound:
    (1 + #{resamples <= bound}) / (1 + resamples)."""
    top, bottom = _per_world(num, den)
    w = bootstrap_counts(len(top), b, seed) if counts is None else counts
    boot = _ratio(w, top, bottom)
    boot = boot[~np.isnan(boot)]
    return float((1 + np.sum(boot <= bound)) / (1 + len(boot)))


# ── world-level sign-flip test ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SignFlipResult:
    """A world-level sign-flip (paired permutation) test of sum_w d_w."""

    statistic: float
    p_value: float
    worlds: int
    exact: bool
    alternative: str


def _check_alternative(alternative: str) -> None:
    if alternative not in ALTERNATIVES:
        raise ValueError(f"alternative must be one of {ALTERNATIVES}, not {alternative!r}")


def _flip_sums(d: np.ndarray) -> np.ndarray:
    sums = np.zeros(1)
    for x in d:
        sums = np.concatenate([sums + x, sums - x])
    return sums


def sign_flip_test(
    differences: ArrayLike,
    *,
    alternative: str = GREATER,
    draws: int = SIGN_FLIP_DRAWS,
    seed: int = SIGN_FLIP_SEED,
    exact_max: int = SIGN_FLIP_EXACT_MAX,
) -> SignFlipResult:
    """Sign-flip test of T = sum_w d_w over worlds: under H0 each world's sign is a fair coin.
    Exact up to ``exact_max`` non-zero worlds, Monte Carlo with add-one above that.

    For paired arms pass d_w = b_w - c_w, the per-world discordance
    (:func:`discordance_by_world`), or per-world endpoint differences.
    """
    d = np.asarray(differences, dtype=np.float64)
    if d.ndim != 1 or len(d) == 0 or np.isnan(d).any():
        raise ValueError("differences must be a non-empty one-dimensional array without NaN")
    _check_alternative(alternative)
    t = float(d.sum())
    nonzero = d[d != 0]
    if len(nonzero) == 0:
        return SignFlipResult(t, 1.0, len(d), True, alternative)
    tol = RELATIVE_TIE * max(1.0, float(np.abs(nonzero).sum()))

    def extreme(sums: np.ndarray) -> np.ndarray:
        if alternative == GREATER:
            return sums >= t - tol
        if alternative == LESS:
            return sums <= t + tol
        return np.abs(sums) >= abs(t) - tol

    if len(nonzero) <= exact_max:
        sums = _flip_sums(nonzero)
        return SignFlipResult(t, float(extreme(sums).mean()), len(d), True, alternative)
    rng = np.random.default_rng(seed)
    hits, done = 0, 0
    while done < draws:
        n = min(SIGN_FLIP_CHUNK, draws - done)
        signs = rng.integers(0, 2, size=(n, len(nonzero))) * 2 - 1
        hits += int(extreme(signs @ nonzero).sum())
        done += n
    return SignFlipResult(t, (1 + hits) / (1 + draws), len(d), False, alternative)


def discordance_by_world(
    caught_a: ArrayLike, caught_b: ArrayLike, episode_world: ArrayLike, n_worlds: int
) -> np.ndarray:
    """Per world: sum over its episodes of (caught by a) - (caught by b) = b_w - c_w, the
    discordant pairs (works with expected catches too)."""
    a = np.asarray(caught_a, dtype=np.float64)
    b = np.asarray(caught_b, dtype=np.float64)
    w = np.asarray(episode_world, dtype=np.int64)
    if not a.shape == b.shape == w.shape:
        raise ValueError("caught_a, caught_b and episode_world must have one shape")
    return np.bincount(w, weights=a - b, minlength=n_worlds)


# ── Wilcoxon signed-rank test over worlds (Hyp6; spec 6.5) ───────────────────────────────────
@dataclass(frozen=True)
class WilcoxonResult:
    """A Wilcoxon signed-rank test of per-world differences d_w.

    ``statistic`` is T+, the sum of the ranks of |d_w| over the positive differences (ties
    share their mean rank). ``n`` counts the ranked differences: the non-zero ones.
    """

    statistic: float
    p_value: float
    n: int
    exact: bool
    alternative: str
    zero_method: str


def _midranks(values: np.ndarray) -> np.ndarray:
    """Ranks 1..n of ``values``; tied values share their mean rank."""
    order = np.argsort(values, kind="stable")
    ordered = values[order]
    start = np.flatnonzero(np.r_[True, ordered[1:] != ordered[:-1]])
    end = np.r_[start[1:], len(values)]
    ranks = np.empty(len(values))
    ranks[order] = np.repeat((start + end + 1) / 2, end - start)
    return ranks


def _signed_rank_counts(doubled: np.ndarray) -> np.ndarray:
    """counts[s] = the number of the 2^n sign patterns whose positive doubled ranks sum to s
    (exact in float64 for n <= 52)."""
    total = int(doubled.sum())
    counts = np.zeros(total + 1)
    counts[0] = 1.0
    for r in doubled:
        shifted = counts.copy()
        shifted[r:] += counts[: total + 1 - r]
        counts = shifted
    return counts


def wilcoxon_signed_rank(
    differences: ArrayLike,
    *,
    alternative: str = TWO_SIDED,
    zero_method: str = ZERO_WILCOX,
    exact_max: int = WILCOXON_EXACT_MAX,
) -> WilcoxonResult:
    """Wilcoxon signed-rank test of per-world differences d_w, H0: each sign a fair coin given
    the ranks. ``greater`` tests for positive differences, ``less`` for negative ones.

    - Zeros: ``wilcox`` drops them before ranking; ``pratt`` ranks them with the others and
      then drops their ranks.
    - Ties in |d_w| share their mean rank. The p-value is exact, from the conditional null
      distribution of T+ given those ranks, up to ``exact_max`` ranked worlds (30 by default),
      so ties need no correction there. Above that it is the normal approximation with mean
      sum(r) / 2 and variance sum(r^2) / 4, which is tie-corrected and has no continuity
      correction.
    - No ranked difference (every d_w zero) gives p = 1.
    """
    d = np.asarray(differences, dtype=np.float64)
    if d.ndim != 1 or len(d) == 0 or np.isnan(d).any():
        raise ValueError("differences must be a non-empty one-dimensional array without NaN")
    _check_alternative(alternative)
    if zero_method not in ZERO_METHODS:
        raise ValueError(f"zero_method must be one of {ZERO_METHODS}, not {zero_method!r}")
    nonzero = d != 0
    if zero_method == ZERO_WILCOX:
        kept = d[nonzero]
        ranks = _midranks(np.abs(kept))
    else:
        kept = d[nonzero]
        ranks = _midranks(np.abs(d))[nonzero]
    n = len(kept)
    if n == 0:
        return WilcoxonResult(0.0, 1.0, 0, True, alternative, zero_method)
    t_plus = float(ranks[kept > 0].sum())
    if n <= exact_max:
        doubled = np.rint(2 * ranks).astype(np.int64)  # mean ranks are whole or halves
        total = int(doubled.sum())
        observed = int(doubled[kept > 0].sum())
        counts = _signed_rank_counts(doubled)
        s = np.arange(total + 1)
        if alternative == GREATER:
            hit = s >= observed
        elif alternative == LESS:
            hit = s <= observed
        else:
            hit = np.abs(2 * s - total) >= abs(2 * observed - total)
        p = float(counts[hit].sum() / counts.sum())
        return WilcoxonResult(t_plus, p, n, True, alternative, zero_method)
    z = (t_plus - ranks.sum() / 2) / math.sqrt(float(np.sum(ranks**2)) / 4)
    nd = NormalDist()
    if alternative == GREATER:
        p = 1 - nd.cdf(z)
    elif alternative == LESS:
        p = nd.cdf(z)
    else:
        p = min(1.0, 2 * (1 - nd.cdf(abs(z))))
    return WilcoxonResult(t_plus, float(p), n, False, alternative, zero_method)
