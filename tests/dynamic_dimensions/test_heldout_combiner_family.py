"""Tests for the EV-20 combiner family (heldout/combiner_family.py), on synthetic evidence."""

from __future__ import annotations

import math

import numpy as np
import pytest

from mcp_security.behaviour.engine import (
    BURST,
    PROTOCOL_SKIP,
    READ_VOLUME,
    TOOL,
    BehaviourConfig,
)
from reports.experiments.dynamic_dimensions.heldout import combiner_family as cf
from reports.experiments.dynamic_dimensions.heldout import heldout_metrics as hm

NAN = math.nan


def _evidence(scores, rates, groups=("A", "B"), shares=(0.5, 0.5)) -> cf.CallEvidence:
    names = tuple(f"d{i}" for i in range(len(groups)))
    return cf.CallEvidence(
        np.array(scores, float), np.array(rates, float), names, tuple(groups), np.array(shares)
    )


def test_v5_layout_has_sixteen_dimensions_and_the_decided_shares() -> None:
    names, groups, shares = cf.layout(BehaviourConfig(design="v5"))
    assert len(names) == 16 and READ_VOLUME in names
    share = dict(zip(names, shares, strict=True))
    assert share[READ_VOLUME] == pytest.approx(1 / 21)
    assert share[TOOL] == pytest.approx(1 / 12)  # D3 (a): Footprint alerts
    assert share[BURST] == pytest.approx(1 / 12)
    assert math.isnan(share[PROTOCOL_SKIP])  # watch-only


def test_layout_refuses_a_design_without_shares_and_follows_read_volume() -> None:
    with pytest.raises(ValueError, match="budget shares"):
        cf.layout(BehaviourConfig(design="v4"))
    names, _, shares = cf.layout(BehaviourConfig(design="v5", reply_volume=False))
    assert READ_VOLUME not in names and len(names) == 15
    assert dict(zip(names, shares, strict=True))["calls_last_hour"] == pytest.approx(1 / 18)


def test_v5_statistic_prices_watch_only_terms_at_the_cap() -> None:
    ev = _evidence([[0.9, 0.9]], [[0.01, 0.001]], shares=(0.5, NAN))
    # alerting: 0.01 / 0.5 = 0.02; watch-only: max(12 x 0.001, 2/15) = 2/15
    assert cf.v5_statistic(ev)[0] == pytest.approx(0.02)
    ev = _evidence([[0.9, 0.9]], [[0.5, 0.001]], shares=(0.5, NAN))
    assert cf.v5_statistic(ev)[0] == pytest.approx(2 / 15)


def test_a_watch_only_term_costs_twelve_times_its_rate_above_the_cap() -> None:
    ev = _evidence([[0.9, 0.9]], [[0.9, 0.05]], shares=(0.5, NAN))
    assert cf.v5_statistic(ev)[0] == pytest.approx(0.6)  # max(12 x 0.05, 2/15)


def test_v5_statistic_drops_without_renormalising() -> None:
    ev = _evidence([[0.9, 0.8]], [[0.01, 0.02]], shares=(0.25, 0.5))
    assert cf.v5_statistic(ev)[0] == pytest.approx(0.04)  # min(0.04, 0.04)
    assert cf.v5_statistic(ev, drop=("d0",))[0] == pytest.approx(0.04)  # still 0.02 / 0.5
    nothing = _evidence([[NAN, NAN]], [[NAN, NAN]])
    assert np.isinf(cf.v5_statistic(nothing)[0])
    assert cf.s1_of(cf.v5_statistic(nothing))[0] == -np.inf
    with pytest.raises(ValueError):
        cf.v5_statistic(ev, drop=("d0", "d1"))


def test_score_arms_known_values() -> None:
    ev = _evidence([[0.75, 0.9]], [[0.01, 0.5]])
    arms = cf.arm_scores(ev, ablations=False)
    assert arms[cf.ARM_MEAN][0] == pytest.approx(0.825)
    assert arms[cf.ARM_NOISY_OR][0] == pytest.approx(1 - 0.5 * 0.2)
    assert arms["soft_or_0.5"][0] == pytest.approx(0.9 + 0.5 * 0.75 * 0.1)
    assert arms[cf.ARM_TOP2][0] == pytest.approx(0.825)
    assert arms[cf.ARM_THRESH][0] == pytest.approx(0.25 + 0.4)
    assert arms[cf.ARM_GROUP_AOM][0] == pytest.approx(0.825)  # one dimension per group
    same_group = _evidence([[0.75, 0.9]], [[0.01, 0.5]], groups=("A", "A"))
    assert cf.group_aom_arm(same_group)[0] == pytest.approx(0.9)


def test_rank_arms_known_values() -> None:
    ev = _evidence([[0.9, 0.6]], [[0.01, 0.5]])
    assert cf.tippett_arm(ev)[0] == pytest.approx(-math.log(1 - 0.99**2))
    assert cf.harmonic_mean_arm(ev)[0] == pytest.approx(math.log(0.5 / 0.01 + 0.5 / 0.5))
    even = _evidence([[0.5, 0.5]], [[0.5, 0.5]])
    assert cf.cauchy_arm(even)[0] == pytest.approx(0.0, abs=1e-12)
    assert cf.cauchy_arm(ev)[0] > 0


def test_tippett_counts_only_the_dimensions_that_took_part() -> None:
    ev = _evidence([[0.9, NAN]], [[0.01, NAN]])
    assert cf.tippett_arm(ev)[0] == pytest.approx(-math.log(0.01))  # k = 1, p = 0.01


def test_cauchy_weights_and_caps_known_values() -> None:
    # Weights 1/4 and 3/4, two dimensions taking part: the cap is 2/3.
    ev = _evidence([[0.9, 0.6]], [[0.1, 0.3]], shares=(0.25, 0.75))
    want = 0.25 / math.tan(0.1 * math.pi) + 0.75 / math.tan(0.3 * math.pi)
    assert cf.cauchy_arm(ev)[0] == pytest.approx(want)
    both_at_one = _evidence([[0.5, 0.5]], [[1.0, 1.0]])
    assert cf.cauchy_arm(both_at_one)[0] == pytest.approx(-1 / math.sqrt(3))  # cot(2 pi / 3)
    tiny = _evidence([[0.99, NAN]], [[1e-20, NAN]])
    assert cf.cauchy_arm(tiny)[0] == pytest.approx(1 / (math.pi * 1e-20), rel=1e-12)


def test_a_strong_record_outranks_an_ordinary_call_despite_a_dimension_at_one() -> None:
    # Call A: a 1-in-9000 record on d0, and d1 at q = 1 (every past day as strange: the usual
    # value of an ordinary dimension under add-one commonness). Call B: nothing strange.
    ev = _evidence([[0.99, 0.4], [0.5, 0.5]], [[1 / 9000, 1.0], [0.6, 0.6]])
    arms = cf.arm_scores(ev, ablations=False)
    for arm in (cf.ARM_V5, cf.ARM_TIPPETT, cf.ARM_HARMONIC, cf.ARM_CAUCHY):
        assert arms[arm][0] > arms[arm][1], arm
    assert np.isfinite(arms[cf.ARM_CAUCHY]).all()


def test_footprint_enters_the_rank_arms_as_a_rank() -> None:
    ref = np.array([1.0, 2.0, 3.0, 4.0])
    assert list(cf.rank_transform([4.0, 2.5, 0.0, 5.0], ref)) == pytest.approx(
        [2 / 5, 3 / 5, 5 / 5, 1 / 5]
    )
    names = (TOOL, BURST)
    ev = cf.CallEvidence(
        np.array([[5.0, 0.6]]),
        np.array([[NAN, 0.5]]),  # Footprint scored but carries no rate (D3 (b) / v4 vectors)
        names,
        ("Typical Footprint", "Red Flags"),
        np.array([1 / 12, 1 / 12]),
    )
    assert cf.footprint_dimensions(ev) == (TOOL,)
    filled = cf.with_rank_fallback(ev, {TOOL: ref})
    assert filled.rates[0, 0] == pytest.approx(1 / 5)
    assert cf.v5_statistic(filled)[0] == pytest.approx((1 / 5) * 12)


def test_footprint_enters_the_rank_arms_under_d3_b() -> None:
    # D3 (b): Footprint is watch-only for v5, but the rank arms still take its rank, with its
    # unspent third split equally (1/12 each). Missing handshake stays out of them.
    names, groups, shares = cf.layout(BehaviourConfig(design="v5", footprint_alerts=False))
    footprint = [i for i, g in enumerate(groups) if g == "Typical Footprint"]
    skip = names.index(PROTOCOL_SKIP)
    assert len(footprint) == 4 and all(math.isnan(shares[i]) for i in footprint)
    rates = np.full((3, len(names)), 0.6)
    rates[0, names.index(TOOL)] = 0.001  # a new tool, rare across the organisation
    rates[2, skip] = 0.001  # a missing handshake only
    ev = cf.CallEvidence(np.full_like(rates, 0.5), rates, names, groups, shares)
    weights = ev.rank_weights
    assert all(weights[i] == pytest.approx(1 / 12) for i in footprint)
    assert math.isnan(weights[skip]) and np.nansum(weights) == pytest.approx(1.0)
    for arm in (cf.tippett_arm, cf.harmonic_mean_arm, cf.cauchy_arm):
        out = arm(ev)
        assert out[0] > out[1], arm.__name__
        assert out[2] == pytest.approx(out[1]), arm.__name__
    assert cf.v5_statistic(ev)[0] == pytest.approx(cf.WATCH_CAP)  # v5 itself: watch-only
    names_a, groups_a, shares_a = cf.layout(BehaviourConfig(design="v5"))  # D3 (a)
    under_a = cf.CallEvidence(ev.scores, ev.rates, names_a, groups_a, shares_a)
    np.testing.assert_array_equal(under_a.rank_weights, shares_a)  # the shares themselves
    no_budget = cf.CallEvidence(
        np.ones((1, 2)),
        np.full((1, 2), 0.5),
        ("tool", "burst"),
        ("Typical Footprint", "B"),
        np.array([NAN, 1.0]),
    )
    with pytest.raises(ValueError, match="no budget"):
        cf.tippett_arm(no_budget)


def test_evidence_from_verdict_dicts() -> None:
    ev = cf.evidence_from_verdicts(
        [{"d0": 0.7}, {"d1": 0.9, "other": 1.0}],
        [{"d0": 0.2}, {"d1": 0.05}],
        ("d0", "d1"),
        ("A", "B"),
        [0.5, 0.5],
    )
    assert ev.scores[0, 0] == 0.7 and math.isnan(ev.scores[0, 1])
    assert ev.rates[1, 1] == 0.05
    with pytest.raises(ValueError):
        _evidence([[0.5, 0.5]], [[0.0, 0.5]])  # a commonness is never 0


def _single_dimension_world(n_days: int = 2_000, calls: int = 3, seed: int = 0):
    """One dimension takes part per call (the others are NaN), so every arm is a monotone
    function of the same score: at a matched budget they must alert on the same days."""
    rng = np.random.default_rng(seed)
    n = n_days * calls
    s = rng.random(n)
    q = cf.rank_transform(s, s)
    which = rng.integers(0, 3, n)
    scores = np.full((n, 3), NAN)
    rates = np.full((n, 3), NAN)
    scores[np.arange(n), which] = s
    rates[np.arange(n), which] = q
    ev = cf.CallEvidence(scores, rates, ("a", "b", "c"), ("G1", "G2", "G3"), np.full(3, 1 / 3))
    days = hm.group_agent_days(np.repeat(np.arange(n_days), calls), np.full(n, 100))
    return ev, days


def test_monotone_arms_give_the_same_alarm_set_at_a_matched_budget() -> None:
    ev, days = _single_dimension_world()
    arms = cf.arm_scores(ev, ablations=False)
    day_scores = {arm: hm.day_max(days, s).score for arm, s in arms.items()}
    fits = cf.fit_arms(day_scores, (0.01,))
    alarms = {
        arm: frozenset(np.flatnonzero(hm.at_or_above(day_scores[arm], fits[arm][0.01])))
        for arm in arms
    }
    assert len(set(alarms.values())) == 1
    assert len(alarms[cf.ARM_V5]) == 20


def test_realised_alpha_on_the_calibration_pool_is_within_one_agent_day() -> None:
    ev, days = _single_dimension_world(n_days=1_537, seed=4)
    v5 = hm.day_max(days, cf.arm_scores(ev, ablations=False)[cf.ARM_V5]).score
    for alpha, fit in cf.fit_arms({cf.ARM_V5: v5})[cf.ARM_V5].items():
        realised = hm.at_or_above(v5, fit).mean()
        assert realised <= alpha and alpha - realised < 1 / len(v5)


def test_leave_one_out_arms_are_named_and_change_the_statistic() -> None:
    ev = _evidence([[0.9, 0.8], [0.6, 0.95]], [[0.01, 0.3], [0.4, 0.002]])
    arms = cf.arm_scores(ev)
    assert {"lodo:d0", "lodo:d1", "logo:A", "logo:B"} <= set(arms)
    assert arms["lodo:d0"][0] == pytest.approx(cf.s1_of(np.array([0.6]))[0])
    assert arms[cf.ARM_V5][0] == pytest.approx(cf.s1_of(np.array([0.02]))[0])


def test_fast_leave_one_out_equals_dropping_directly() -> None:
    rng = np.random.default_rng(9)
    n, names = 400, ("a", "b", "c", "d", "e")
    groups = ("G1", "G1", "G2", "G3", "G3")
    scores = np.where(rng.random((n, 5)) < 0.6, rng.random((n, 5)), NAN)
    rates = np.where(np.isnan(scores), NAN, np.clip(rng.random((n, 5)), 1e-3, 1.0))
    shares = np.array([1 / 6, 1 / 6, 1 / 3, 1 / 6, NAN])
    ev = cf.CallEvidence(scores, rates, names, groups, shares)
    arms = cf.arm_scores(ev)
    for name in names:
        direct = cf.s1_of(cf.v5_statistic(ev, drop=(name,)))
        assert np.array_equal(arms[f"lodo:{name}"], direct)
    for group in set(groups):
        dims = [nm for nm, g in zip(names, groups, strict=True) if g == group]
        assert np.array_equal(arms[f"logo:{group}"], cf.s1_of(cf.v5_statistic(ev, drop=dims)))


def test_red_flags_statistic_reads_only_red_flags() -> None:
    names = (TOOL, BURST)
    ev = cf.CallEvidence(
        np.array([[0.99, 0.6]]),
        np.array([[0.001, 0.5]]),
        names,
        ("Typical Footprint", "Red Flags"),
        np.array([1 / 12, 1 / 12]),
    )
    assert cf.red_flags_statistic(ev)[0] == pytest.approx(cf.s1_of(np.array([6.0]))[0])


def test_evaluate_and_pool_points() -> None:
    # Agent-days: two benign (scores 1, 5), one gray day credited to episode 0 (score 9).
    days = hm.group_agent_days(["a", "b", "c"], [100, 100, 100])
    dm = hm.day_max(days, [1.0, 5.0, 9.0])
    fit = hm.Threshold(0.01, True, 5.0, None, 0.0, None, 1, 3)
    point = cf.evaluate_arm(cf.ARM_V5, fit, days, dm, [-1, -1, 0])
    assert (point.benign_days, point.benign_alerts, point.episodes, point.caught) == (2, 1, 1, 1)
    pooled = cf.pool_points([point, point])
    assert pooled.benign_rate == pytest.approx(0.5) and pooled.recall == 1.0
    assert pooled.transfer_ratio == pytest.approx(50.0)
    with pytest.raises(ValueError):
        cf.pool_points([point, cf.ArmPoint("mean", 0.01, 1, 0, 1, 0)])


def test_evaluate_arm_counts_only_the_window() -> None:
    # Benign a (day 10, outside), b and c (day 100); gray g (day 100, episode 0) and h (day 10,
    # episode 1, outside). Above the threshold: a, c, g and h; only c and g are in the window.
    days = hm.group_agent_days(["a", "b", "c", "g", "h"], [10, 100, 100, 100, 10])
    dm = hm.day_max(days, [9.0, 1.0, 5.0, 9.0, 9.0])
    fit = hm.Threshold(0.01, True, 5.0, None, 0.0, None, 1, 5)
    point = cf.evaluate_arm(cf.ARM_V5, fit, days, dm, [-1, -1, -1, 0, 1], window=(90, 180))
    assert (point.benign_days, point.benign_alerts, point.episodes, point.caught) == (2, 1, 1, 1)


def test_hyp4_rejects_only_arms_that_cannot_beat_v5_by_delta() -> None:
    rng = np.random.default_rng(7)
    v5 = 0.6 + 0.02 * rng.normal(size=30)
    per_world = {
        cf.ARM_V5: v5,
        cf.ARM_MEAN: v5 - 0.05 + 0.01 * rng.normal(size=30),  # clearly worse
        cf.ARM_TIPPETT: v5 + 0.10,  # clearly better
    }
    out = cf.hyp4_noninferiority(per_world, delta_c=0.02, b=2_000)
    assert out[cf.ARM_MEAN].rejected
    assert not out[cf.ARM_TIPPETT].rejected
    assert out[cf.ARM_MEAN].level == pytest.approx(1 - 0.05 / 2)
    with pytest.raises(ValueError):
        cf.hyp4_noninferiority({cf.ARM_MEAN: v5}, delta_c=0.02)


def test_hyp4_decides_on_the_bound_not_the_estimate() -> None:
    # The arm beats v5 by about 0.010 on average, below delta_c = 0.012, but the worlds spread
    # its upper bound above delta_c: the null "arm - v5 >= delta_c" is not rejected.
    rng = np.random.default_rng(7)
    v5 = 0.6 + 0.02 * rng.normal(size=30)
    signs = np.where(np.arange(30) % 2 == 0, 1.0, -1.0)
    arm = v5 + 0.01 + 0.03 * signs * rng.random(30)
    out = cf.hyp4_noninferiority({cf.ARM_V5: v5, cf.ARM_MEAN: arm}, delta_c=0.012, b=2_000)
    result = out[cf.ARM_MEAN]
    assert result.difference < 0.012 < result.upper
    assert not result.rejected
