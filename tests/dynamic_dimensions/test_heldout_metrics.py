"""Known-answer tests for the held-out metrics (heldout/heldout_metrics.py).

Every fixture is synthetic: hand-computed pAUC areas, review lists and credits, deployment-day
keys on simulator-style timestamps, harm counts and gate curves. The general statistics are
tested in test_heldout_stats.py.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import numpy as np
import pytest

from mcp_security.behaviour import clock
from reports.experiments.dynamic_dimensions.heldout import heldout_metrics as hm
from reports.experiments.dynamic_dimensions.heldout import heldout_stats as hs
from reports.experiments.dynamic_dimensions.heldout import heldout_world_spec as ws
from reports.experiments.dynamic_dimensions.heldout import outside_baselines as ob
from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

HOUR_S = 3_600.0
ZONE_OFFSET_H = {"UTC": 0, "Asia/Tokyo": 9}  # neither zone has daylight saving since 1951


# ── pAUC ─────────────────────────────────────────────────────────────────────────────────────
def test_partial_auc_of_a_perfect_ranking_is_one() -> None:
    assert hm.partial_auc(np.arange(100.0), [200.0, 300.0]) == pytest.approx(1.0)


def test_partial_auc_of_all_ties_is_the_diagonal() -> None:
    neg, pos = np.zeros(50), np.zeros(5)
    assert hm.partial_auc(neg, pos, normalise=False) == pytest.approx(0.03**2 / 2)
    assert hm.partial_auc(neg, pos) == pytest.approx(0.015)


def test_partial_auc_hand_example() -> None:
    # 100 benign days scored 0..99; episodes at 99.5, 98.5 and 50. Over FPR [0, 0.01] recall is
    # 1/3, over [0.01, 0.03] it is 2/3: area 0.01/3 + 0.02 * 2/3 = 0.05/3, normalised 5/9.
    pauc = hm.partial_auc(np.arange(100.0), [99.5, 98.5, 50.0])
    assert pauc == pytest.approx(5 / 9)


def test_partial_auc_interpolates_a_tied_segment() -> None:
    # pos 2 alone first (tpr 0.5 at fpr 0), then pos 1 tied with 10 negatives: a diagonal from
    # (0, 0.5) to (1, 1); at fpr 0.03 recall is 0.515.
    pauc = hm.partial_auc(np.ones(10), [2.0, 1.0], normalise=False)
    assert pauc == pytest.approx(0.03 * (0.5 + 0.515) / 2)


def test_full_auc_equals_the_mann_whitney_probability() -> None:
    rng = np.random.default_rng(3)
    neg, pos = rng.integers(0, 6, 40).astype(float), rng.integers(0, 8, 25).astype(float)
    wins = (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
    assert hm.partial_auc(neg, pos, max_fpr=1.0) == pytest.approx(wins)


def test_partial_auc_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        hm.partial_auc([], [1.0])
    with pytest.raises(ValueError):
        hm.partial_auc([np.nan], [1.0])
    with pytest.raises(ValueError):
        hm.partial_auc([0.0], [1.0], max_fpr=0.0)


# ── agent-days, credit ───────────────────────────────────────────────────────────────────────
def test_group_agent_days_and_the_top_call_is_the_first_at_the_maximum() -> None:
    agent = np.array(["b", "a", "a", "a", "b"])
    day = np.array([1, 1, 1, 2, 1])
    score = np.array([0.2, 0.9, 0.9, 0.1, 0.3])
    days = hm.group_agent_days(agent, day)
    assert days.n_days == 3
    assert list(days.agent) == ["a", "a", "b"]
    assert list(days.day) == [1, 2, 1]
    dm = hm.day_max(days, score, secondary=np.arange(5.0))
    assert list(dm.score) == [0.9, 0.1, 0.3]
    assert list(dm.top) == [1, 3, 4]  # call 1 precedes call 2 in the stream
    assert list(dm.secondary) == [1.0, 3.0, 4.0]


def test_credited_episode_scores() -> None:
    out = hm.credited_episode_scores([5.0, 7.0, 3.0, 9.0], [0, 0, 1, -1], 3)
    assert list(out) == [7.0, 3.0, -np.inf]


def test_credit_needs_the_top_call_to_belong_to_the_episode() -> None:
    # One agent-day: a benign call and an episode call tie at the maximum; the benign one is
    # first in the stream, so the day credits nobody and the episode is never caught (EV-18).
    days = hm.group_agent_days(["a", "a"], [100, 100])
    dm = hm.day_max(days, [0.9, 0.9])
    episode = np.array([-1, 0])
    top_ep = episode[dm.top]
    caught = hm.credited_caught(np.ones(days.n_days, bool), top_ep, 1)
    assert not caught[0]
    assert hm.credited_episode_scores(dm.score, top_ep, 1)[0] == -np.inf


def test_credited_pauc_on_a_small_world() -> None:
    # 100 benign agent-days scored 0..99 and two gray agent-days whose top calls belong to
    # episodes 0 and 1 (scores 99.5 and 50); a third episode only appears off-top.
    n = 100
    agent = [f"x{i}" for i in range(n)] + ["g0", "g1", "g1"]
    day = [100] * n + [100, 101, 101]
    score = list(np.arange(float(n))) + [99.5, 50.0, 10.0]
    episode = [-1] * n + [0, 1, 2]
    days = hm.group_agent_days(agent, day)
    dm = hm.day_max(days, score)
    expected = hm.partial_auc(np.arange(float(n)), [99.5, 50.0, -np.inf])
    assert hm.credited_pauc(days, dm, episode) == pytest.approx(expected)
    assert expected == pytest.approx((0.03 / 3) / 0.03)


def test_credited_pauc_respects_the_window() -> None:
    days = hm.group_agent_days(["a", "b", "c"], [10, 100, 100])
    dm = hm.day_max(days, [5.0, 1.0, 2.0])
    with pytest.raises(ValueError, match="no gray episode"):
        hm.credited_pauc(days, dm, [0, -1, -1], window=(90, 180))


def _gray_world(gray: list[tuple[int, float, int]]) -> tuple[hm.AgentDays, hm.DayMax, list]:
    """100 benign agent-days on day 100 scored 0..99, plus one agent-day per (day, score,
    episode) for the gray agent "g", each topped by its episode's call."""
    agent = [f"x{i}" for i in range(100)] + ["g"] * len(gray)
    day = [100] * 100 + [d for d, _, _ in gray]
    score = list(np.arange(100.0)) + [s for _, s, _ in gray]
    episode = [-1] * 100 + [e for _, _, e in gray]
    days = hm.group_agent_days(agent, day)
    return days, hm.day_max(days, score), episode


def test_credited_pauc_counts_only_episodes_and_days_in_the_window() -> None:
    window = (90, 180)
    # Episode 0 tops day 100 at 99.5: a perfect ranking. Episode 1 lives only on day 10,
    # outside the window: it is no positive at all (else a -inf positive halves the area).
    days, dm, episode = _gray_world([(100, 99.5, 0), (10, 99.9, 1)])
    assert hm.credited_pauc(days, dm, episode, window=window) == pytest.approx(1.0)
    # Episode 0 tops day 100 at only 50, and a day-10 agent-day at 99.9: day 10 is outside the
    # window, so it cannot credit episode 0, whose credited score stays 50.
    days, dm, episode = _gray_world([(100, 50.0, 0), (10, 99.9, 0)])
    assert hm.credited_pauc(days, dm, episode, window=window) == pytest.approx(0.0)


# ── local days and deployment days ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("zone", ["America/New_York", "Australia/Lord_Howe", "Asia/Kolkata"])
def test_local_day_keys_equal_the_engine_clock_across_dst(zone: str) -> None:
    start = datetime(2026, 3, 1, tzinfo=UTC).timestamp()
    ts = start + np.sort(np.random.default_rng(5).uniform(0, 60 * clock.DAY_S, 3_000))
    keys = hm.local_day_keys(ts, zone)
    hours = hm.local_hours(ts, zone)
    assert list(keys) == [clock.local_day(float(t), zone) for t in ts]
    assert list(hours) == [clock.local_hour(float(t), zone) for t in ts]
    shifted = hm.local_day_keys(ts, zone, base_day=int(keys.min()))
    assert list(shifted) == list(keys - keys.min())


def test_local_day_rolls_over_at_four_and_mixes_zones() -> None:
    midnight = datetime(2026, 1, 5, tzinfo=UTC).timestamp()
    ts = np.array([midnight + 3.99 * 3600, midnight + 4 * 3600, midnight + 4 * 3600])
    keys = hm.local_day_keys(ts, np.array(["UTC", "UTC", "Asia/Tokyo"]))
    day = int(midnight // clock.DAY_S)
    assert list(keys) == [day - 1, day, day]  # 13:00 in Tokyo is the same local day


def _simulator_stream(n_agents: int = 12, n_days: int = 181) -> dict[str, np.ndarray]:
    """Calls placed like normal_org_world places them: (BASE_DAY + d) * DAY + (local hour -
    zone offset) * HOUR, three per agent-day at local hours 9-17, in two zones; one gray
    episode, the strangest call of its agent-day, on day 150."""
    rng = np.random.default_rng(11)
    rows = []
    for a in range(n_agents):
        zone = "UTC" if a % 2 else "Asia/Tokyo"
        for d in range(n_days):
            for _ in range(3):
                local = rng.uniform(9, 17)
                ts = (W.BASE_DAY + d) * clock.DAY_S + (local - ZONE_OFFSET_H[zone]) * HOUR_S
                rows.append((f"agent{a}", zone, ts, d, float(rng.random()), -1))
    agent, zone, ts, day, score, episode = (np.array(c) for c in zip(*rows, strict=True))
    gray = np.flatnonzero((agent == "agent1") & (day == 150))[0]
    score[gray], episode[gray] = 2.0, 0
    return {"agent": agent, "zone": zone, "ts": ts, "day": day, "score": score, "ep": episode}


def test_deployment_days_run_through_every_default_window() -> None:
    calls = _simulator_stream()
    keys = hm.local_day_keys(calls["ts"], calls["zone"], base_day=W.BASE_DAY)
    assert np.array_equal(keys, calls["day"])  # deployment day d, in both zones
    days = hm.group_agent_days(calls["agent"], keys)
    dm = hm.day_max(days, calls["score"])
    assert hm.credited_pauc(days, dm, calls["ep"], window=ws.SELECT_WINDOW) == pytest.approx(1.0)
    features = np.random.default_rng(2).random((days.n_days, 3))
    forest = ob.isolation_forest(days, features, n_estimators=10, max_samples=32)
    assert forest.shape == (days.n_days,)
    tools = np.full(len(keys), "list_issues")
    unseen = ob.praetor_unseen(days, calls["agent"], tools, np.full(len(keys), "repo"))
    assert not unseen.any()  # the one edge and context were learned on days 0-29
    assert set(hm.period_index(days.day)) == {-1, 0, 1, 2, 3}
    assert hm.in_window(days.day, hm.ROUTE_WARMUP_WINDOW).sum() == 12 * 90


def test_1970_day_keys_are_refused_by_every_window() -> None:
    calls = _simulator_stream(n_agents=2)
    keys = hm.local_day_keys(calls["ts"], calls["zone"])  # base_day forgotten
    days = hm.group_agent_days(calls["agent"], keys)
    dm = hm.day_max(days, calls["score"])
    tools = np.full(len(keys), "list_issues")
    features = np.ones((days.n_days, 2))
    for run in (
        lambda: hm.credited_pauc(days, dm, calls["ep"], window=ws.SELECT_WINDOW),
        lambda: ob.isolation_forest(days, features, n_estimators=5, max_samples=8),
        lambda: ob.praetor_unseen(days, calls["agent"], tools, tools),
        lambda: ob.role_peer_group(days, features, np.full(days.n_days, "dev")),
        lambda: hm.period_index(days.day),
    ):
        with pytest.raises(ValueError, match="1970-based"):
            run()


def test_active_days_before_counts_the_callers_past_window() -> None:
    days = hm.group_agent_days(
        ["a"] * 6 + ["b"] * 2, [0, 1, 5, 100, 189, 190, 1, 5], seq=np.arange(8)
    )
    a_days = hm.active_days_before(days)
    # a: 0, 1, 2 (days 0, 1 in [t-89, t-1]), 0 (day 100: nothing in 11-99), 1, 1; b: 0, 1
    assert a_days.tolist() == [0, 1, 2, 0, 1, 1, 0, 1]
    assert hm.active_days_before(days, window=200).tolist() == [0, 1, 2, 3, 4, 5, 0, 1]
    assert hm.tenure_band(a_days).tolist() == [0] * 8


# ── thresholds ───────────────────────────────────────────────────────────────────────────────
def test_fit_threshold_meets_alpha_within_one_agent_day() -> None:
    scores = np.random.default_rng(1).normal(size=1_234)
    for alpha in hm.STATED_ALPHAS:
        t = hm.fit_threshold(scores, alpha)
        realised = hm.at_or_above(scores, t).mean()
        assert realised <= alpha
        assert alpha - realised < 1 / len(scores)


def test_fit_threshold_moves_up_past_a_tie_and_can_be_infeasible() -> None:
    scores = np.r_[np.zeros(95), np.ones(5)]
    assert not hm.fit_threshold(scores, 0.01).feasible  # the top tie alone is 5% > 1%
    t = hm.fit_threshold(scores, 0.05)
    assert t.value == 1.0 and t.fit_rate == pytest.approx(0.05) and t.ties == 5
    assert not hm.at_or_above(scores, hm.fit_threshold(scores, 0.01)).any()


# ── the review list ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(("active", "length"), [(150, 4), (100, 3), (60, 2), (20, 1), (10, 1)])
def test_list_lengths_round_half_up(active: int, length: int) -> None:
    assert set(hm.list_lengths(np.zeros(active, int))) == {length}


def test_review_list_credits_only_the_listed_top_call() -> None:
    day = [7, 7, 7, 7]
    score = [0.9, 0.5, 0.4, 0.3]
    top = [-1, 0, 1, -1]
    one = hm.review_list(day, score, np.zeros(4), top, [0, 1], length=1)
    assert one.recall == 0.0  # the benign day takes the only slot
    assert one.random_recall == pytest.approx(0.25)
    assert one.lift == 0.0
    two = hm.review_list(day, score, np.zeros(4), top, [0, 1], length=2)
    assert two.recall == pytest.approx(0.5)
    assert list(two.per_episode) == [1.0, 0.0]


def test_review_list_breaks_ties_at_random_in_expectation() -> None:
    day, score, second = [1, 1, 1], [0.8, 0.8, 0.1], [0.2, 0.2, 0.0]
    res = hm.review_list(day, score, second, [0, 1, -1], [0, 1], length=1)
    assert list(res.per_episode) == pytest.approx([0.5, 0.5])
    by_second = hm.review_list(day, score, [0.3, 0.2, 0.0], [0, 1, -1], [0, 1], length=1)
    assert list(by_second.per_episode) == [1.0, 0.0]  # s2 decides the tie


def test_review_list_over_two_days_with_their_own_lengths() -> None:
    # Day 1 has 80 active agents (L = 2), day 2 has 40 (L = 1). Each day ranks on its own:
    # day 1 lists episodes 0 and 1, not 2; day 2 lists episode 3, not 4.
    day = np.r_[np.full(80, 1), np.full(40, 2)]
    score = np.r_[np.linspace(0, 1, 80), np.linspace(0, 1, 40)]
    top = np.full(120, -1)
    top[[79, 78, 77]] = [0, 1, 2]
    top[[119, 118]] = [3, 4]
    res = hm.review_list(day, score, np.zeros(120), top, np.arange(5))
    assert res.per_episode.tolist() == [1.0, 1.0, 0.0, 1.0, 0.0]
    assert res.slots == 3
    # the random list draws L of that day's agent-days: 2/80 on day 1, 1/40 on day 2
    assert res.random_per_episode.tolist() == pytest.approx([2 / 80] * 3 + [1 / 40] * 2)
    unequal = hm.review_list(day[:100], score[:100], np.zeros(100), top[:100], [0, 1, 2])
    assert unequal.random_per_episode[:3].tolist() == pytest.approx([2 / 80] * 3)


def test_review_list_credit_over_several_days_is_one_minus_the_misses() -> None:
    # Episode 0 tops one agent-day on each of two days; each day lists one of two tied
    # agent-days, so P(listed) = 1/2 per day and P(caught) = 1 - (1/2)(1/2) = 3/4.
    day = [1, 1, 2, 2]
    score = [0.9, 0.9, 0.8, 0.8]
    res = hm.review_list(day, score, np.zeros(4), [0, -1, 0, -1], [0], length=1)
    assert res.per_episode.tolist() == pytest.approx([0.75])
    assert res.caught == pytest.approx(0.75)


def test_recall_at_lengths_grows_with_the_list() -> None:
    rng = np.random.default_rng(2)
    day = np.repeat(np.arange(5), 20)
    score = rng.random(100)
    top = np.where(rng.random(100) < 0.2, rng.integers(0, 10, 100), -1)
    rec = hm.recall_at_lengths(day, score, np.zeros(100), top, np.arange(10), lengths=(1, 4, 16))
    assert rec[1] <= rec[4] <= rec[16]


# ── per-dimension spend ──────────────────────────────────────────────────────────────────────
def test_dimension_fired_uses_shares_and_skips_watch_only() -> None:
    # 0.0004 x 21 = 0.84% fires at 1%; 0.02 x 12 = 24% does not; watch-only never fires.
    rates = np.array([[0.0004, 0.02, 0.001], [np.nan, 0.0001, 0.0001]])
    fired = hm.dimension_fired(rates, [1 / 21, 1 / 12, np.nan], alpha=0.01)
    assert fired.tolist() == [[True, False, False], [False, True, False]]


def test_per_dimension_spend_flags_an_overrun_under_holm() -> None:
    rng = np.random.default_rng(11)
    shares = np.array([1 / 12, 1 / 12, np.nan])
    worlds = np.repeat(np.arange(10), 2_000)
    nominal = shares[0] * 0.01
    fired = np.stack(
        [
            rng.random(len(worlds)) < 5 * nominal,  # overruns its share five-fold
            rng.random(len(worlds)) < 0.5 * nominal,  # within its share
            rng.random(len(worlds)) < 0.2,  # watch-only: never tested
        ],
        axis=1,
    )
    rows = hm.per_dimension_spend(
        fired, shares, ["burst", "sweep", "protocol_skip"], world=worlds, b=2_000
    )
    assert [r.overrun for r in rows] == [True, False, False]
    assert rows[2].p_value is None and rows[2].nominal is None
    assert rows[0].nominal == pytest.approx(nominal)


def test_per_dimension_spend_decides_on_the_holm_adjusted_p() -> None:
    # 5 firings in 2,000 days against a nominal 0.0833% gives p = 0.0275 on its own: an overrun.
    # Three such dimensions: Holm adjusts each to 3 x 0.0275 = 0.0825 > 0.05, so none overruns.
    n, k, share = 2_000, 5, 1 / 12
    raw = hs.binomial_upper_tail(k, n, share * 0.01)
    assert 0.05 / 3 < raw <= 0.05
    fired = np.zeros((n, 3), dtype=bool)
    fired[:k, :] = True
    rows = hm.per_dimension_spend(fired, np.full(3, share), ["burst", "sweep", "sequence"])
    assert [r.p_value for r in rows] == pytest.approx([raw] * 3)
    assert [r.adjusted_p for r in rows] == pytest.approx([3 * raw] * 3)
    assert not any(r.overrun for r in rows)
    alone = hm.per_dimension_spend(fired[:, :1], [share], ["burst"])
    assert alone[0].overrun


def test_per_dimension_spend_with_one_world_uses_the_binomial() -> None:
    fired = np.zeros((1_000, 1), bool)
    fired[:20, 0] = True  # 2% against a nominal 0.1%
    rows = hm.per_dimension_spend(fired, [0.1], ["asset"], alpha=0.01)
    assert rows[0].p_value == pytest.approx(hs.binomial_upper_tail(20, 1_000, 0.001))
    assert rows[0].overrun


# ── strata, periods, precision ───────────────────────────────────────────────────────────────
def test_tenure_bands_and_periods() -> None:
    assert list(hm.tenure_band([0, 19, 20, 44, 45, 90])) == [0, 0, 1, 1, 2, 2]
    assert list(hm.period_index([0, 89, 90, 119, 120, 180])) == [-1, -1, 0, 0, 1, 3]
    assert list(hm.in_window([0, 89, 90], hm.ROUTE_WARMUP_WINDOW)) == [True, True, False]


def test_rates_by_group_and_the_share_of_groups_above_a_bound() -> None:
    alerts = np.array([1, 0, 0, 0, 1, 1, 0, 0], bool)
    group = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    rates = hm.rate_by_group(alerts, group)
    assert rates[0].rate == 0.25 and rates[1].rate == 0.5
    assert hm.share_of_groups_above(alerts, group, 0.3) == 0.5


def test_quiet_check_against_alpha_plus_beta() -> None:
    days = np.full(30, 4_000)
    interval, holds = hm.quiet_check(np.full(30, 20), days, b=1_000)
    assert interval.estimate == pytest.approx(0.005) and holds
    _, fails = hm.quiet_check(np.full(30, 80), days, b=1_000)
    assert not fails


def test_quiet_check_reads_the_one_sided_95_percent_bound() -> None:
    # Worlds with spread (0.2% to 2%, pooled 1.1%): put alpha + beta between the one-sided 95%
    # bound and the two-sided 97.5% one. Only the one-sided bound passes.
    days = np.full(20, 10_000)
    alerts = np.round(np.linspace(0.002, 0.02, 20) * days)
    interval = hs.world_bootstrap(alerts, days, b=1_000, seed=7)
    assert interval.upper_one_sided < interval.upper
    bar = (interval.upper_one_sided + interval.upper) / 2
    checked, holds = hm.quiet_check(alerts, days, 0.01, bar - 0.01, b=1_000, seed=7)
    assert checked.upper_one_sided == interval.upper_one_sided and holds
    below = interval.upper_one_sided - 1e-6
    assert not hm.quiet_check(alerts, days, 0.01, below - 0.01, b=1_000, seed=7)[1]


def test_ppv_and_transfer_ratio() -> None:
    assert hm.ppv(0.5, 0.01, 1e-3) == pytest.approx(0.5e-3 / (0.5e-3 + 0.01 * 0.999))
    curve = hm.ppv_by_prevalence(0.5, 0.01)
    assert list(curve) == list(hm.PREVALENCES)
    assert curve[1e-3] > curve[1e-4] > curve[1e-5]
    assert hm.transfer_ratio(0.015, 0.01) == pytest.approx(1.5)
    with pytest.raises(ValueError):
        hm.transfer_ratio(0.01, 0.0)


# ── harm before the first alert (EV-19) ──────────────────────────────────────────────────────
def test_harm_counts_what_an_episode_delivered_before_its_first_alert() -> None:
    # Episode 0: ten calls one second apart; its first alert is the 7th call (Part A's fixture),
    # so harm counts the 6 calls before it. Episode 1 never alerts: all 3 calls are harm.
    # Benign calls (-1) interleave, and the input order is reversed to test the stream order.
    episode = [0] * 10 + [1] * 3 + [-1] * 4
    ts = list(range(10)) + [100, 101, 102] + [0.5, 3.5, 6.5, 50.0]
    alert = [False] * 6 + [True, False, True, False] + [False] * 3 + [True] * 4
    asset = ["a", "b", "a", "c", "", "b", "d", "e", "f", "g", "x", "x", "y", "z", "z", "z", "z"]
    request = [10.0] * 17
    reply = [100.0] * 17
    rev = slice(None, None, -1)
    harm = hm.harm_before_first_alert(
        np.array(episode)[rev],
        np.array(ts)[rev],
        np.array(alert)[rev],
        asset=np.array(asset)[rev],
        request_bytes=np.array(request)[rev],
        reply_bytes=np.array(reply)[rev],
    )
    assert harm.caught.tolist() == [True, False]
    assert harm.calls.tolist() == [6.0, 3.0]
    assert harm.assets.tolist() == [3.0, 2.0]  # {a, b, c}; {x, y}
    assert harm.request_bytes.tolist() == [60.0, 30.0]
    assert harm.reply_bytes.tolist() == [600.0, 300.0]
    assert harm.delay_s[0] == pytest.approx(6.0) and math.isnan(harm.delay_s[1])
    assert harm.first_alert[0] == 16 - 6 and harm.first_alert[1] == -1  # index after reversal


def test_harm_breaks_equal_timestamps_by_stream_order() -> None:
    harm = hm.harm_before_first_alert(
        [0, 0, 0], [5.0, 5.0, 5.0], [False, True, False], seq=[2, 1, 0], n_episodes=2
    )
    # stream order: call 2, call 1 (the alert), call 0: one call came before the alert
    assert harm.calls.tolist() == [1.0, 0.0] and harm.first_alert.tolist() == [1, -1]
    assert harm.caught.tolist() == [True, False]


# ── the gate curve (EV-24) ───────────────────────────────────────────────────────────────────
def test_gate_curve_hand_example() -> None:
    # Benign agent-days A (R = 1, 4) and B (2, 3); gray agent-days of episode 0 (peak R 3.5,
    # weight 2) and episode 1 (peak 1.5, weight 1).
    agent = ["A", "A", "B", "B", "G0", "G0", "G1"]
    days = hm.group_agent_days(agent, [100] * 7)
    risk = [1.0, 4.0, 2.0, 3.0, 3.5, 0.5, 1.5]
    episode = [-1, -1, -1, -1, 0, 0, 1]
    curve = hm.gate_curve(days, risk, episode, weights=hm.consequence_weight([1, 1], [True, False]))
    assert curve.threshold.tolist() == [4.0, 3.5, 3.0, 2.0, 1.5, 1.0]
    assert curve.benign_call_rate.tolist() == pytest.approx([0.25, 0.25, 0.5, 0.75, 0.75, 1.0])
    assert curve.benign_day_rate.tolist() == pytest.approx([0.5, 0.5, 1.0, 1.0, 1.0, 1.0])
    assert curve.recall.tolist() == pytest.approx([0.0, 2 / 3, 2 / 3, 2 / 3, 1.0, 1.0])


def test_consequence_weight_doubles_writes() -> None:
    assert hm.consequence_weight([5, 3, 0], [True, False, True]).tolist() == [10.0, 3.0, 0.0]
    with pytest.raises(ValueError):
        hm.consequence_weight([-1], [False])
