"""Known-answer tests for the held-out statistics (heldout/heldout_stats.py).

Every fixture is synthetic: textbook Wilson, Holm and Wilcoxon values, bootstrap quantiles that
can be enumerated or recomputed independently on the same resample matrix, exact sign-flip
distributions and brute-force signed-rank enumerations.
"""

from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np
import pytest

from reports.experiments.dynamic_dimensions.heldout import heldout_stats as hs

SMALL_B = 4_000  # enough resamples for 3% SE checks, fast in CI
SE_TOLERANCE = 0.05  # relative
# Darwin's Zea mays differences (Fisher's example; scipy.stats.wilcoxon's docs): T- = 24,
# exact two-sided p = 0.041259765625.
DARWIN = (6, 8, 14, 16, 23, 24, 28, 29, 41, -48, 49, 56, 60, -67, 75)
DARWIN_T_PLUS = 96.0  # 1 + ... + 15 = 120, minus T- = 24
DARWIN_P = 0.041259765625


# ── one binomial count, Holm ─────────────────────────────────────────────────────────────────
def test_wilson_textbook_values() -> None:
    lo, hi = hs.wilson(5, 10)
    assert (lo, hi) == pytest.approx((0.2366, 0.7634), abs=1e-4)
    assert hs.wilson(0, 10) == pytest.approx((0.0, 0.2775), abs=1e-4)
    assert all(math.isnan(x) for x in hs.wilson(0, 0))


def test_binomial_upper_tail_known_values() -> None:
    assert hs.binomial_upper_tail(4, 5, 0.5) == pytest.approx(6 / 32)
    assert hs.binomial_upper_tail(0, 5, 0.3) == 1.0
    assert hs.binomial_upper_tail(6, 5, 0.3) == 0.0
    brute = sum(math.comb(20, i) * 0.13**i * 0.87 ** (20 - i) for i in range(5, 21))
    assert hs.binomial_upper_tail(5, 20, 0.13) == pytest.approx(brute)


def test_holm_textbook_example() -> None:
    res = hs.holm([0.01, 0.04, 0.03, 0.005], alpha=0.05)
    assert list(res.adjusted) == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert list(res.reject) == [True, False, False, True]


def test_holm_with_one_test_is_the_plain_test() -> None:
    assert list(hs.holm([0.049]).reject) == [True]
    with pytest.raises(ValueError):
        hs.holm([1.2])


# ── world bootstrap ──────────────────────────────────────────────────────────────────────────
def test_two_world_bootstrap_has_known_quantiles_and_se() -> None:
    # Resampled means of worlds {0, 1}: 0, 1/2 or 1 with probabilities 1/4, 1/2, 1/4.
    res = hs.world_bootstrap([0.0, 1.0], b=SMALL_B, seed=4)
    assert res.estimate == 0.5
    assert (res.lower, res.upper) == (0.0, 1.0)
    assert res.se == pytest.approx(math.sqrt(1 / 8), rel=SE_TOLERANCE)


def test_bootstrap_of_equal_worlds_has_no_spread() -> None:
    res = hs.world_bootstrap([3.0, 3.0, 3.0, 3.0], b=500)
    assert res.se == 0.0 and res.lower == res.upper == 3.0


def test_bootstrap_se_equals_the_plug_in_se_of_a_mean() -> None:
    x = np.random.default_rng(8).normal(size=20)
    plug_in = math.sqrt(np.mean((x - x.mean()) ** 2) / len(x))
    assert hs.world_bootstrap(x, b=SMALL_B, seed=9).se == pytest.approx(plug_in, rel=SE_TOLERANCE)


def test_bootstrap_pools_a_ratio_and_resamples_whole_worlds() -> None:
    # Worlds (10 alerts / 100 days) and (0 / 100): a resample can only give 0, 5% or 10%.
    counts = hs.bootstrap_counts(2, 1_000, 1)
    res = hs.world_bootstrap([10, 0], [100, 100], counts=counts)
    assert res.estimate == pytest.approx(0.05)
    boot = (counts @ np.array([10.0, 0.0])) / (counts @ np.array([100.0, 100.0]))
    assert set(np.round(boot, 9)) <= {0.0, 0.05, 0.1}


def test_percentile_bounds_are_the_stated_quantiles_of_the_resamples() -> None:
    # The two-sided interval takes the 2.5% and 97.5% quantiles, the one-sided bounds the 5%
    # and 95% ones, all of one resample matrix (recomputed here independently).
    x = np.linspace(0.002, 0.02, 20)
    counts = hs.bootstrap_counts(len(x), 3_000, 2)
    res = hs.world_bootstrap(x, counts=counts)
    boot = counts @ x / len(x)
    want = np.quantile(boot, [0.025, 0.975, 0.05, 0.95])
    got = [res.lower, res.upper, res.lower_one_sided, res.upper_one_sided]
    assert got == pytest.approx(list(want), rel=1e-12)
    assert res.upper_one_sided < res.upper and res.lower_one_sided > res.lower


def test_bca_equals_an_independent_efron_tibshirani_computation() -> None:
    # A skewed sample, so both the bias correction z0 and the acceleration a are material.
    nd = NormalDist()
    x = np.random.default_rng(3).exponential(size=15)
    counts = hs.bootstrap_counts(len(x), 20_000, 1)
    res = hs.world_bootstrap(x, counts=counts, method="bca")
    boot = counts @ x / len(x)
    z0 = nd.inv_cdf(np.mean(boot < x.mean()) + 0.5 * np.mean(boot == x.mean()))
    jack = (x.sum() - x) / (len(x) - 1)
    dev = jack.mean() - jack
    accel = np.sum(dev**3) / (6 * np.sum(dev**2) ** 1.5)
    assert abs(z0) > 0.05 and accel > 0.05  # the fixture exercises both corrections
    levels = []
    for p in (0.025, 0.975, 0.05, 0.95):
        zp = nd.inv_cdf(p)
        levels.append(nd.cdf(z0 + (z0 + zp) / (1 - accel * (z0 + zp))))
    want = np.quantile(boot, levels)
    got = [res.lower, res.upper, res.lower_one_sided, res.upper_one_sided]
    assert res.method == "bca"
    assert got == pytest.approx(list(want), rel=1e-12)
    percentile = hs.world_bootstrap(x, counts=counts)
    assert res.lower > percentile.lower and res.upper > percentile.upper  # right skew


def test_bca_matches_percentile_on_a_symmetric_statistic() -> None:
    x = np.linspace(-1, 1, 21)
    pct = hs.world_bootstrap(x, b=SMALL_B, seed=3)
    bca = hs.world_bootstrap(x, b=SMALL_B, seed=3, method="bca")
    assert bca.method == "bca"
    assert bca.lower == pytest.approx(pct.lower, abs=0.03)
    assert bca.upper == pytest.approx(pct.upper, abs=0.03)
    with pytest.raises(ValueError):
        hs.world_bootstrap(x, method="studentised")


def test_paired_bootstrap_of_identical_arms_is_zero() -> None:
    x = np.random.default_rng(1).random(12)
    res = hs.paired_world_bootstrap(x, x, b=500)
    assert res.estimate == 0.0 and res.se == 0.0


def test_paired_bootstrap_resamples_both_arms_together() -> None:
    # Arm b = arm a + 1 per world: every paired resample differs by exactly 1.
    x = np.random.default_rng(2).random(9)
    res = hs.paired_world_bootstrap(x + 1, x, b=500)
    assert res.estimate == pytest.approx(1.0) and res.se == pytest.approx(0.0, abs=1e-12)


def test_bootstrap_p_above_separates_over_and_under() -> None:
    days = np.full(10, 1_000)
    assert hs.bootstrap_p_above(np.full(10, 50), days, 0.01, b=500) < 0.01
    assert hs.bootstrap_p_above(np.full(10, 5), days, 0.01, b=500) == 1.0


# ── sign-flip test ───────────────────────────────────────────────────────────────────────────
def test_sign_flip_exact_known_answers() -> None:
    assert hs.sign_flip_test([1.0] * 5).p_value == pytest.approx(1 / 32)
    assert hs.sign_flip_test([1.0, -1.0]).p_value == pytest.approx(0.75)
    assert hs.sign_flip_test([2.0, 1.0]).p_value == pytest.approx(0.25)
    assert hs.sign_flip_test([1.0] * 5, alternative="two-sided").p_value == pytest.approx(2 / 32)
    assert hs.sign_flip_test([1.0] * 5, alternative="less").p_value == pytest.approx(1.0)
    assert hs.sign_flip_test([0.0, 0.0]).p_value == 1.0


def test_sign_flip_zeros_change_nothing() -> None:
    assert hs.sign_flip_test([1.0, 0.0, 1.0]).p_value == pytest.approx(1 / 4)


def test_sign_flip_monte_carlo_agrees_with_exact() -> None:
    d = np.random.default_rng(6).normal(0.4, 1.0, 12)
    exact = hs.sign_flip_test(d)
    approx = hs.sign_flip_test(d, exact_max=0, draws=20_000)
    assert exact.exact and not approx.exact
    assert approx.p_value == pytest.approx(exact.p_value, abs=0.01)


def test_discordance_by_world() -> None:
    a = [1, 1, 0, 1, 0]
    b = [0, 1, 1, 0, 0]
    out = hs.discordance_by_world(a, b, [0, 0, 0, 1, 1], 2)
    assert list(out) == [0.0, 1.0]


# ── Wilcoxon signed-rank test ────────────────────────────────────────────────────────────────
def _brute_force_p(differences: np.ndarray, zero_method: str, alternative: str) -> float:
    """Enumerate every sign pattern of the ranked differences (an independent reference)."""
    nonzero = differences != 0
    magnitude = np.abs(differences)
    if zero_method == "wilcox":
        magnitude = magnitude[nonzero]
    ranks = np.array(
        [(np.sum(magnitude < m) + (np.sum(magnitude == m) + 1) / 2) for m in magnitude]
    )
    if zero_method == "pratt":
        ranks = ranks[nonzero]
    kept = differences[nonzero]
    observed, total = ranks[kept > 0].sum(), ranks.sum()
    sums = np.array([np.dot(s, ranks) for s in itertools.product((0, 1), repeat=len(ranks))])
    if alternative == "greater":
        return float(np.mean(sums >= observed - 1e-9))
    if alternative == "less":
        return float(np.mean(sums <= observed + 1e-9))
    return float(np.mean(np.abs(2 * sums - total) >= abs(2 * observed - total) - 1e-9))


def test_wilcoxon_textbook_example() -> None:
    res = hs.wilcoxon_signed_rank(DARWIN)
    assert res.statistic == DARWIN_T_PLUS and res.n == len(DARWIN) and res.exact
    assert res.p_value == pytest.approx(DARWIN_P, rel=1e-12)
    greater = hs.wilcoxon_signed_rank(DARWIN, alternative="greater")
    assert greater.p_value == pytest.approx(DARWIN_P / 2, rel=1e-12)


@pytest.mark.parametrize("zero_method", ["wilcox", "pratt"])
@pytest.mark.parametrize("alternative", ["two-sided", "greater", "less"])
def test_wilcoxon_exact_with_ties_and_zeros_equals_enumeration(
    zero_method: str, alternative: str
) -> None:
    d = np.array([1.5, -1.5, 2.0, 2.0, -3.0, 0.0, 4.0, -0.5, 0.0, 2.0, 5.0, -1.5])
    res = hs.wilcoxon_signed_rank(d, alternative=alternative, zero_method=zero_method)
    assert res.n == 10 and res.exact
    assert res.p_value == pytest.approx(_brute_force_p(d, zero_method, alternative), rel=1e-12)


def test_wilcoxon_normal_approximation_is_close_to_exact() -> None:
    d = np.random.default_rng(4).normal(0.4, 1.0, 40)
    exact = hs.wilcoxon_signed_rank(d, exact_max=40)
    approx = hs.wilcoxon_signed_rank(d, exact_max=0)
    assert exact.exact and not approx.exact
    assert approx.p_value == pytest.approx(exact.p_value, abs=0.005)  # n = 40
    # without ties the variance is n (n + 1) (2n + 1) / 24
    z = (approx.statistic - 40 * 41 / 4) / math.sqrt(40 * 41 * 81 / 24)
    assert approx.p_value == pytest.approx(2 * (1 - NormalDist().cdf(abs(z))))


def test_wilcoxon_hyp6_direction_and_degenerate_input() -> None:
    v4 = np.array([0.031, 0.029, 0.034, 0.030, 0.028, 0.033])
    v5 = v4 - np.array([0.004, 0.006, 0.003, 0.005, 0.002, 0.007])
    below = hs.wilcoxon_signed_rank(v5 - v4, alternative="less")
    assert below.statistic == 0.0 and below.p_value == pytest.approx(1 / 64)
    assert hs.wilcoxon_signed_rank(v5 - v4, alternative="greater").p_value == 1.0
    assert hs.wilcoxon_signed_rank([0.0, 0.0]).p_value == 1.0
    with pytest.raises(ValueError):
        hs.wilcoxon_signed_rank([1.0], zero_method="zsplit")
    with pytest.raises(ValueError):
        hs.wilcoxon_signed_rank([1.0, np.nan])
