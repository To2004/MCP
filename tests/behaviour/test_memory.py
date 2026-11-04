"""v5 memory (Batch 1, I2): B5, B7, DEP-7, AI-8 and RF7 in ``behaviour/memory.py``.

The v1-v4 classes (``DailyCounts``, ``DailyMean``, ``SlidingCounts``, ``FirstUses``) are pinned
by the goldens (``test_golden_designs.py``, ``tests/gateway/test_golden_gateway.py``); here
they serve as the reference v5 must equal where the spec says so. Every number is synthetic.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, deque

import numpy as np
import pytest

from mcp_security.behaviour.memory import (
    FIRST_USE_SECONDS,
    MAX_VALUES_PER_KIND,
    ColleagueFirstUses,
    DailyCounts,
    DailyMean,
    FirstUses,
    MinimumHistory,
    OrgFirstSeen,
    SlidingTotal,
    SlotQuantile,
    ValueDays,
    WindowMean,
    is_established,
    org_discount_applies,
    slot_of,
    value_strength,
)

WINDOW, MIN_ACTIVE, HORIZON = 90, 20, 365
HOUR_S, DAY_S = 3_600.0, 86_400.0
FLOOD = 100_000  # the spec's 10^5-value flood
SEEDS = (1, 7, 11)


def json_round_trip(data):
    """What a snapshot file gives back: tuples become lists, keys stay strings."""
    return json.loads(json.dumps(data))


def brute_start(active: list[int], t: int) -> int:
    """B5's start(t) from the formula, over every active day ever noted."""
    before = sorted(d for d in set(active) if d < t)
    start = t - HORIZON + 1
    if len(before) >= MIN_ACTIVE:
        start = max(start, min(t - WINDOW + 1, before[-MIN_ACTIVE]))
    return start


def phased_activity(rng: random.Random, days: int) -> list[bool]:
    """Busy stretches, sparse stretches and long absences (60-180 days)."""
    out: list[bool] = []
    while len(out) < days:
        phase = rng.choice(("busy", "sparse", "away"))
        length = rng.randint(60, 180) if phase == "away" else rng.randint(10, 80)
        rate = {"busy": 0.9, "sparse": 0.2, "away": 0.0}[phase]
        out.extend(rng.random() < rate for _ in range(length))
    return out[:days]


# ── B5: minimum history ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("seed", SEEDS)
def test_the_window_start_never_decreases_and_follows_the_formula(seed: int) -> None:
    rng = random.Random(seed)
    history, noted, previous = MinimumHistory(), [], None
    for t, active in enumerate(phased_activity(rng, 1_200)):
        start = history.roll(t)
        assert start == brute_start(noted, t)
        assert t - HORIZON + 1 <= start <= t - WINDOW + 1
        assert previous is None or start >= previous
        assert history.active_days(t) == sum(1 for d in set(noted) if start <= d < t)
        assert all(day >= start for day in history.to_json()["active"])  # roll forgets them
        previous = start
        if active:
            history.note(t)
            noted.append(t)


def test_a_caller_with_twenty_active_days_in_ninety_sees_v4s_window() -> None:
    """Every other day active: always >= 20 active days in 90, so v5's value-days are exactly
    v4's window (``DailyCounts(90, daily=True)``) counted in days."""
    rng = random.Random(3)
    values = [f"repo-{i}" for i in range(12)]
    history, days, v4 = MinimumHistory(), ValueDays(), DailyCounts(WINDOW, daily=True)
    for t in range(0, 300, 2):
        start = history.roll(t)
        days.roll(t, start)
        v4.expire(t)
        if t >= 2 * WINDOW:
            assert start == t - WINDOW + 1
            past = {d: c for d, c in v4.by_day.items() if d < t}
            for value in values:
                assert days.days_used(value) == sum(1 for c in past.values() if value in c)
            assert days.active_days() == len(past)
        history.note(t)
        for value in rng.sample(values, rng.randint(1, 5)):
            for _ in range(rng.randint(1, 3)):
                days.add(t, value)
                v4.add(t, value, count_as_new=False)


def test_a_long_absence_keeps_the_history_v4_forgets() -> None:
    """N10: 60 active days, then 120 days away. v4's window is empty; v5's reaches back to
    his 20th most recent active day."""
    history, days, v4 = MinimumHistory(), ValueDays(), DailyCounts(WINDOW, daily=True)
    for t in range(60):
        days.roll(t, history.roll(t))
        history.note(t)
        days.add(t, "repo-main")
        v4.add(t, "repo-main", count_as_new=False)
    back = 59 + 121
    start = history.roll(back)
    days.roll(back, start)
    v4.expire(back)
    assert start == 40  # his 20th most recent active day
    assert days.days_used("repo-main") == MIN_ACTIVE and days.active_days() == MIN_ACTIVE
    assert not v4.known("repo-main") and v4.active_days(today=back) == 0


def test_the_window_reaches_back_at_most_a_year() -> None:
    history, days = MinimumHistory(), ValueDays()
    for t in range(10):
        days.roll(t, history.roll(t))
        history.note(t)
        days.add(t, "repo-main")
    assert history.roll(40) == 40 - HORIZON + 1  # fewer than 20 active days: a year back
    later = 9 + 400
    days.roll(later, history.roll(later))
    assert history.active_days(later) == 0
    assert days.days_used("repo-main") == 0 and days.active_days() == 0
    assert len(days) == 0  # a value with no day left in the window is forgotten


def test_a_day_number_that_goes_back_never_moves_the_start_back() -> None:
    """A late commit can carry an earlier day than the last roll's (a slow reply across the
    rollover): the window keeps the start it reached."""
    history = MinimumHistory()
    for t in range(0, 200, 2):
        history.roll(t)
        history.note(t)
    start = history.roll(200)
    assert start == 200 - WINDOW + 1
    assert history.window_start(150) == start  # the formula alone would give 150 - 89


def test_a_caller_away_longer_than_the_horizon_is_no_longer_established() -> None:
    """Established counts active days inside the B5 window only, so 30 active days followed
    by 400 days away leave nothing: he counts as new again (RF7, RF11 and the floors)."""
    history = MinimumHistory()
    for t in range(30):
        history.roll(t)
        history.note(t)
    assert history.is_established(30, first_day=0)
    assert history.active_days(430) == 0
    assert not history.is_established(430, first_day=0)


def test_established_needs_twenty_active_days_and_fourteen_days() -> None:
    assert is_established(20, first_day=0, today=14)
    assert not is_established(19, first_day=0, today=100)
    assert not is_established(40, first_day=90, today=103)  # a bootstrapped caller, 13 days
    history = MinimumHistory()
    for t in range(20):
        history.roll(t)
        history.note(t)
    assert not history.is_established(19, first_day=0)  # day 19 itself does not count yet
    assert history.is_established(20, first_day=0)


def test_minimum_history_round_trips() -> None:
    history = MinimumHistory()
    for t in range(0, 400, 3):
        history.roll(t)
        history.note(t)
    back = MinimumHistory.from_json(json_round_trip(history.to_json()))
    for t in (400, 450, 700):
        assert back.roll(t) == history.roll(t)
        assert back.active_days(t) == history.active_days(t)


def test_minimum_history_rejects_a_window_longer_than_the_horizon() -> None:
    with pytest.raises(ValueError):
        MinimumHistory(window_days=400, max_days=365)


# ── value-days, count-of-counts, value cap (CAL-1, DEP-7) ──────────────────────────────────
def test_a_never_used_value_is_the_strangest() -> None:
    history, days = MinimumHistory(), ValueDays()
    rng = random.Random(5)
    used = [f"repo-{i}" for i in range(8)]
    for t in range(40):
        days.roll(t, history.roll(t))
        history.note(t)
        days.add(t, rng.choice(used))
        days.add(t, "repo-0")
    days.roll(40, history.roll(40))
    counts = {v: days.days_used(v) for v in used if not days.is_new(v)}
    assert counts and min(counts.values()) >= 1
    assert days.days_used("never-seen") == 0 < min(counts.values())
    assert days.is_new("never-seen")


@pytest.mark.parametrize("seed", SEEDS)
def test_value_days_and_count_of_counts_match_a_brute_force_model(seed: int) -> None:
    rng = random.Random(seed)
    universe = [f"v{i}" for i in range(30)]
    history, days = MinimumHistory(), ValueDays()
    log: list[tuple[int, str]] = []
    for t, active in enumerate(phased_activity(rng, 500)):
        start = history.roll(t)
        days.roll(t, start)
        past = [(d, v) for d, v in log if start <= d < t]
        expected = {v: len({d for d, w in past if w == v}) for v in universe}
        assert {v: days.days_used(v) for v in universe} == expected
        cc = Counter(n for n in expected.values() if n)
        assert days.count_of_counts() == dict(cc)
        assert days.distinct() == sum(cc.values())
        assert days.active_days() == len({d for d, _ in past})
        for k in (1, 3, 10, 50):
            assert days.values_at_most(k) == sum(n for c, n in cc.items() if c <= k)
            assert days.value_days_at_most(k) == sum(c * n for c, n in cc.items() if c <= k)
        if past:
            d, v = rng.choice(past)
            assert days.used_on(v, d)
        if active:
            history.note(t)
            for value in rng.sample(universe, rng.randint(1, 6)):
                days.add(t, value)
                log.append((t, value))


def test_each_day_counts_once_and_today_waits_for_the_day_to_end() -> None:
    days = ValueDays()
    days.roll(10, 0)
    for _ in range(5):
        days.add(10, "repo-a")
    assert days.days_used("repo-a") == 0 and days.used_today("repo-a")
    assert not days.is_new("repo-a")
    days.roll(11, 0)
    assert days.days_used("repo-a") == 1 and not days.used_today("repo-a")
    assert days.used_on("repo-a", 10) and not days.used_on("repo-a", 9)


def test_a_flood_of_distinct_values_stays_bounded_and_prices_the_rest_as_new() -> None:
    history, days = MinimumHistory(), ValueDays()
    legit = [f"repo-{i}" for i in range(10)]
    for t in range(30):
        days.roll(t, history.roll(t))
        history.note(t)
        for value in legit:
            days.add(t, value)
    flood_days = 3
    for k, t in enumerate(range(30, 30 + flood_days)):
        days.roll(t, history.roll(t))
        history.note(t)
        for i in range(FLOOD):
            days.add(t, f"junk-{k}-{i}")
            if i % 10_000 == 0:
                assert len(days) <= MAX_VALUES_PER_KIND
        assert len(days) <= MAX_VALUES_PER_KIND
    days.roll(30 + flood_days, history.roll(30 + flood_days))
    assert len(days) <= MAX_VALUES_PER_KIND
    assert days.stored_entries() <= (30 + flood_days) * MAX_VALUES_PER_KIND
    assert days.overflowed == flood_days * FLOOD + len(legit) - MAX_VALUES_PER_KIND
    for value in legit:  # folded into the overflow: priced as new, the strangest
        assert days.days_used(value) == 0 and days.is_new(value)
    assert days.active_days() == 30 + flood_days  # the days still happened
    assert days.distinct() == MAX_VALUES_PER_KIND


def test_an_evicted_values_old_days_never_count_again() -> None:
    """x is used on day 0, folded into the overflow on day 1 and used again on day 2: it is a
    new value with one day, and day 0's dead entry does not count for it (Hour of day's
    leave-one-out reads ``used_on``)."""
    days = ValueDays(max_values=2)
    days.roll(0, 0)
    days.add(0, "x")
    days.add(0, "y")
    days.roll(1, 0)
    days.add(1, "a")  # folds x into the overflow
    days.add(1, "b")  # and y
    days.roll(2, 0)
    days.add(2, "x")  # x again: it folds a
    days.roll(3, 0)
    assert days.days_used("x") == 1 and days.used_on("x", 2)
    assert not days.used_on("x", 0) and not days.used_on("y", 0)
    assert days.overflowed == 3 and days.active_days() == 3
    back = ValueDays.from_json(json_round_trip(days.to_json()), max_values=2)
    assert not back.used_on("x", 0) and back.days_used("x") == 1 and back.active_days() == 3


def test_rolling_early_or_late_gives_the_same_state() -> None:
    rng = random.Random(9)
    universe = [f"v{i}" for i in range(15)]
    early, late, history = ValueDays(), ValueDays(), MinimumHistory()
    for t, active in enumerate(phased_activity(rng, 300)):
        early.roll(t, history.roll(t))
        if active:
            history.note(t)
            for value in rng.sample(universe, 3):
                early.add(t, value)
                late.add(t, value)
    end = 300
    start = history.roll(end)
    early.roll(end, start)
    late.roll(end, start)
    assert early.to_json() == late.to_json()


def test_value_days_round_trip_and_keep_their_eviction_order() -> None:
    rng = random.Random(4)
    days, history = ValueDays(max_values=50), MinimumHistory()
    universe = [f"v{i}" for i in range(80)] + [("weekend", h) for h in range(24)]
    for t in range(60):
        days.roll(t, history.roll(t))
        history.note(t)
        for value in rng.sample(universe, 20):
            days.add(t, value)
    back = ValueDays.from_json(json_round_trip(days.to_json()), max_values=50)
    assert back.to_json() == days.to_json()
    for t in range(60, 90):
        start = history.roll(t)
        for store in (days, back):
            store.roll(t, start)
        history.note(t)
        for value in rng.sample(universe, 20):
            days.add(t, value)
            back.add(t, value)
        assert [days.days_used(v) for v in universe] == [back.days_used(v) for v in universe]
        assert back.overflowed == days.overflowed and back.to_json() == days.to_json()


# ── B7: the robust usual ────────────────────────────────────────────────────────────────────
def inverted_cdf(values: list[float], q: float) -> float:
    """The smallest value that at least q of the values stay at or below (q n exact)."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(q * len(ordered))) - 1]


@pytest.mark.parametrize("seed", SEEDS)
def test_the_usual_is_the_inverted_cdf_quantile_of_his_active_slots(seed: int) -> None:
    rng = random.Random(seed)
    history, usual = MinimumHistory(), SlotQuantile()
    median = SlotQuantile(quantile=0.5)
    slots: dict[int, dict[int, int]] = {}
    for t, active in enumerate(phased_activity(rng, 260)):
        start = history.roll(t)
        usual.roll(t, start)
        median.roll(t, start)
        past = [v for d, s in slots.items() if start <= d < t for v in s.values()]
        if not past:
            assert usual.usual() is None
        elif len(past) < 4:
            assert usual.usual() == max(past)
        else:
            assert usual.usual() == np.quantile(past, 0.75, method="inverted_cdf")
            assert usual.usual() == inverted_cdf(past, 0.75)
            assert median.usual() == np.quantile(past, 0.5, method="inverted_cdf")
        assert usual.slots() == len(past)
        if not active:
            continue
        history.note(t)
        today = slots.setdefault(t, {})
        for hour in rng.sample(range(24), rng.randint(1, 10)):
            for _ in range(rng.randint(1, 3)):  # a slot keeps its largest value
                value = int(rng.expovariate(1 / 12))
                usual.observe(t, hour, value)
                median.observe(t, hour, value)
                today[hour] = max(today.get(hour, value), value)


def test_one_extreme_hour_moves_v4s_usual_but_not_the_robust_one() -> None:
    """N5: one 600-call hour. v4's usual (the call-weighted mean of the trailing-hour count)
    jumps; the 0.75 quantile of his active hours stays at 10."""
    v4, v5 = DailyMean(WINDOW, daily=True), SlotQuantile()
    hours = (9, 10, 11, 13, 14, 15, 16, 17)
    for t in range(30):
        v5.roll(t, 0)
        for hour in hours:
            for k in range(1, 11):  # 10 calls an hour: trailing counts 1..10
                v4.mean_then_add(t, float(k))
            v5.observe(t, hour, 10)
    v5.roll(30, 0)
    before = (v4.mean(30), v5.usual())
    for k in range(1, 601):
        v4.mean_then_add(30, float(k))
    v5.observe(30, 12, 600)
    v5.roll(31, 0)
    assert before[1] == v5.usual() == 10
    assert v4.mean(31) > 5 * before[0]


def test_few_slots_use_their_maximum_and_none_gives_none() -> None:
    usual = SlotQuantile()
    assert usual.usual() is None
    for hour, value in ((1, 1), (2, 5), (3, 2)):
        usual.observe(0, hour, value)
    usual.roll(1, 0)
    assert usual.usual() == 5
    usual.observe(1, 4, 10)
    usual.roll(2, 0)
    assert usual.usual() == 5  # [1, 2, 5, 10]: the third of four


def test_the_usual_leaves_today_out_and_forgets_days_before_the_start() -> None:
    usual = SlotQuantile()
    for t, value in ((0, 50), (1, 4), (2, 4), (3, 4)):
        usual.roll(t, 0)
        usual.observe(t, 9, value)
    assert usual.usual() == 50 and usual.slots() == 3  # days 0-2; today's slot waits
    usual.roll(4, 1)
    assert usual.usual() == 4 and usual.slots() == 3  # day 0 left, day 3 came in


def test_slot_of_gives_clock_hours_and_ten_minute_slots() -> None:
    assert slot_of(3 * HOUR_S + 59 * 60) == 3
    assert slot_of(3 * HOUR_S + 59 * 60, 600.0) == 23


def test_the_slot_quantile_round_trips() -> None:
    rng = random.Random(2)
    usual = SlotQuantile()
    for t in range(40):
        usual.roll(t, max(0, t - WINDOW + 1))
        for hour in rng.sample(range(24), 6):
            usual.observe(t, hour, rng.randint(0, 40))
    back = SlotQuantile.from_json(json_round_trip(usual.to_json()))
    for t in range(40, 140, 7):
        usual.roll(t, t - WINDOW + 1)
        back.roll(t, t - WINDOW + 1)
        assert back.usual() == usual.usual() and back.slots() == usual.slots()


# ── B5's mean and AI-8's read-only DailyMean.mean ───────────────────────────────────────────
def test_the_window_mean_leaves_today_out_and_restores_bit_for_bit() -> None:
    rng = random.Random(6)
    mean = WindowMean()
    assert mean.mean() is None
    mean.roll(0, 0)
    mean.add(0, 3.0)
    assert mean.mean() is None  # today waits for the day to end
    for t in range(1, 120):
        mean.roll(t, max(0, t - WINDOW + 1))
        for _ in range(rng.randint(0, 4)):
            mean.add(t, rng.uniform(0, 30))
    back = WindowMean.from_json(json_round_trip(mean.to_json()))
    for t in range(120, 400, 13):
        mean.roll(t, t - WINDOW + 1)
        back.roll(t, t - WINDOW + 1)
        assert back.mean() == mean.mean()
    mean.roll(1_000, 1_000)
    assert mean.mean() is None


@pytest.mark.parametrize("daily", [False, True])
def test_daily_mean_mean_is_what_mean_then_add_returns_without_adding(daily: bool) -> None:
    rng = random.Random(8)
    usual = DailyMean(WINDOW, daily=daily)
    for t in sorted(rng.choices(range(400), k=600)):
        saved = usual.to_json()
        expected = usual.mean(t)
        assert usual.to_json() == saved  # reading changed nothing
        assert usual.mean_then_add(t, rng.uniform(0, 50)) == expected


# ── AI-8: Read volume's sliding total ────────────────────────────────────────────────────────
def test_the_sliding_total_counts_the_last_hour() -> None:
    total = SlidingTotal(HOUR_S, resolution_s=None)
    total.add(0.0, 100)
    total.add(1_800.0, 200)
    assert total.total_at(3_599.9) == 300
    assert total.total_at(3_600.0) == 200  # (t - 3600, t]: the reply at 0 has left
    total.add(3_600.0, 300)
    total.expire(3_600.0)
    assert total.total() == 500 and len(total) == 2


def test_total_at_reads_without_dropping() -> None:
    total = SlidingTotal(HOUR_S)
    total.add(0.0, 10)
    assert total.total_at(10 * HOUR_S) == 0
    assert total.total() == 10 and len(total) == 1


def test_a_reply_flood_stays_bounded_and_exact() -> None:
    rng = random.Random(1)
    total = SlidingTotal(HOUR_S)
    amounts = [rng.randint(0, 50_000) for _ in range(FLOOD)]
    step = (HOUR_S - 1.0) / FLOOD
    for i, amount in enumerate(amounts):
        total.add(i * step, amount)
    total.expire((FLOOD - 1) * step)
    assert len(total) <= HOUR_S + 1
    assert total.total() == sum(amounts)
    total.expire(3 * HOUR_S)
    assert total.total() == 0 and len(total) == 0


def test_a_bucket_leaves_with_its_newest_reply() -> None:
    """Bounded mode: bytes stay at most one resolution step longer than exact mode."""
    bucketed, exact = SlidingTotal(HOUR_S), SlidingTotal(HOUR_S, resolution_s=None)
    for store in (bucketed, exact):
        store.add(0.2, 10)
        store.add(0.9, 20)
    assert exact.total_at(HOUR_S + 0.5) == 20
    assert bucketed.total_at(HOUR_S + 0.5) == 30
    assert bucketed.total_at(HOUR_S + 0.9) == 0


@pytest.mark.parametrize("exact", [False, True])
def test_adding_alone_keeps_the_sliding_total_bounded(exact: bool) -> None:
    """The score path reads with the pure ``total_at`` and replies only add, so nothing calls
    ``expire``. Five days of replies (a few seconds apart) must still hold one window's worth
    of entries, and every read must equal a recount of the window."""
    rng = random.Random(12)
    resolution = None if exact else 1.0
    total = SlidingTotal(HOUR_S, resolution_s=resolution)
    window: deque[tuple[float, int]] = deque()  # the replies of the last hour
    spill: deque[tuple[float, int]] = deque()  # replies that left it less than 1 s ago
    window_sum = spill_sum = 0
    ts, sent, most = 0.0, 0, 0
    while ts < 5 * DAY_S:
        ts += rng.choice((0.3, 2.0, 7.0))
        amount = rng.randint(0, 20_000)
        total.add(ts, amount)
        sent += 1
        most = max(most, len(total))
        window.append((ts, amount))
        window_sum += amount
        while window[0][0] <= ts - HOUR_S:
            left = window.popleft()
            window_sum -= left[1]
            spill.append(left)
            spill_sum += left[1]
        while spill and spill[0][0] <= ts - HOUR_S - 1.0:
            spill_sum -= spill.popleft()[1]
        assert len(total) <= len(window)
        if sent % 997 == 0:
            read = total.total_at(ts)
            assert read == total.total()
            if exact:
                assert read == window_sum
            else:  # a bucket's bytes may stay up to one resolution step longer
                assert window_sum <= read <= window_sum + spill_sum
    assert sent > 100_000
    assert most <= HOUR_S / 0.3 + 1 if exact else most <= HOUR_S + 1


def test_the_sliding_total_takes_only_non_negative_integers() -> None:
    total = SlidingTotal(HOUR_S)
    with pytest.raises(ValueError):
        total.add(0.0, -1)
    with pytest.raises(TypeError):
        total.add(0.0, 1.5)
    with pytest.raises(TypeError):
        total.add(0.0, True)
    with pytest.raises(TypeError):
        total.add(0.0, np.float64(3.0))
    with pytest.raises(TypeError):
        total.add(0.0, np.bool_(True))
    with pytest.raises(ValueError):
        total.add(0.0, np.int64(-1))


def test_the_sliding_total_takes_numpy_integers_as_ints() -> None:
    """Reply sizes read from a pandas or CSV column are numpy integers."""
    total = SlidingTotal(HOUR_S)
    total.add(0.0, np.int64(5))
    total.add(1.5, np.uint32(7))
    assert total.total() == 12 and type(total.total()) is int
    assert json.loads(json.dumps(total.to_json())) == [[0.0, 5], [1.5, 7]]


def test_the_sliding_total_round_trips() -> None:
    total = SlidingTotal(HOUR_S)
    for i in range(500):
        total.add(i * 13.7, i)
    back = SlidingTotal.from_json(HOUR_S, json_round_trip(total.to_json()))
    for now in (6_000.0, 6_500.0, 9_000.0):
        total.expire(now)
        back.expire(now)
        assert back.total() == total.total() and len(back) == len(total)


# ── RF7: new to the organisation, colleagues, Footprint strength ────────────────────────────
def test_a_value_is_new_to_the_org_for_thirty_days_after_its_run_begins() -> None:
    org = OrgFirstSeen(observed_since=0)
    for day in range(40, 101, 10):  # someone used it 60 days ago, and since
        org.note("tool", "old", "bob", day)
    org.note("tool", "fresh", "alice", 100)
    assert not org.is_new_to_org("tool", "old", 100)
    assert org.is_new_to_org("tool", "fresh", 100) and org.is_new_to_org("tool", "fresh", 129)
    assert not org.is_new_to_org("tool", "fresh", 130)
    assert not org.is_new_to_org("tool", "never-seen", 100)


def test_a_value_first_seen_before_the_store_saw_a_whole_window_is_not_new_to_the_org() -> None:
    """A store that began on day 0 cannot tell a value first seen on day 20 from one used
    the week before it began (a DEP-6 bootstrap, or a gateway put in front of a server in
    use). Only a run whose 90 days before it the store saw can be new."""
    org = OrgFirstSeen()
    assert org.observed_since is None and not org.is_new_to_org("asset", "repo-x", 0)
    org.note("asset", "repo-main", "alice", 0)  # the store begins on day 0
    org.note("asset", "repo-common", "bob", 20)
    assert org.observed_since == 0
    assert not org.is_new_to_org("asset", "repo-common", 21)
    org.note("asset", "repo-88", "bob", WINDOW - 2)  # it saw days 0-87 of 89 before it
    org.note("asset", "repo-89", "bob", WINDOW - 1)  # it saw all of days 0-88
    assert not org.is_new_to_org("asset", "repo-88", WINDOW)
    assert org.is_new_to_org("asset", "repo-89", WINDOW)
    back = OrgFirstSeen.from_json(json_round_trip(org.to_json()))
    assert back.observed_since == 0 and not back.is_new_to_org("asset", "repo-common", 21)
    assert back.is_new_to_org("asset", "repo-89", WINDOW)


def test_a_route_with_no_calls_before_its_first_day_can_pass_that_on() -> None:
    """A brand-new server: no use can hide before day 0, so the engine may say so."""
    org = OrgFirstSeen(observed_since=-WINDOW + 1)
    org.note("asset", "repo-common", "bob", 20)
    assert org.is_new_to_org("asset", "repo-common", 21)


def test_a_late_note_does_not_keep_an_old_run_alive() -> None:
    """A slow reply's commit can carry an earlier day than calls already noted. The value
    then sits behind newer ones, and its next use after a 90-day gap still starts a new run;
    a late use from the day before a run began moves its start back."""
    org = OrgFirstSeen()
    org.note("asset", "repo-a", "alice", 11)
    org.note("asset", "repo-b", "bob", 10)  # committed late: behind repo-a, not before it
    org.note("asset", "repo-b", "bob", 10 + WINDOW)  # last use 10 <= 100 - 90: a new run
    assert org.run_start("asset", "repo-b") == 10 + WINDOW
    org.note("asset", "repo-c", "carol", 120)
    org.note("asset", "repo-c", "dave", 119)  # a late commit from the day before
    assert org.run_start("asset", "repo-c") == 119
    assert org.callers("asset", "repo-c", 120) == 1  # dave's day 119 counts; carol's is today
    org.note("asset", "repo-d", "erin", 130)  # erin's first use of repo-d is today ...
    org.note("asset", "repo-d", "erin", 129)  # ... and her slow reply from yesterday follows
    assert org.callers("asset", "repo-d", 130) == 1  # yesterday's use counts


def test_a_value_unused_for_ninety_days_starts_a_new_run() -> None:
    org = OrgFirstSeen()
    org.note("asset", "repo-a", "alice", 10)
    org.note("asset", "repo-b", "alice", 11)
    org.note("asset", "repo-a", "bob", 100)  # last use 10 <= 100 - 90: a gap
    org.note("asset", "repo-b", "bob", 100)  # last use 11: within the window, same run
    assert org.run_start("asset", "repo-a") == 100
    assert org.run_start("asset", "repo-b") == 11


def test_callers_count_the_windows_past_days_only() -> None:
    org = OrgFirstSeen()
    for caller in ("alice", "bob"):
        org.note("asset", "repo-a", caller, 50)
    org.note("asset", "repo-a", "carol", 100)
    assert org.callers("asset", "repo-a", 100) == 2  # carol's use is today's
    assert org.callers("asset", "repo-a", 100, exclude="alice") == 1
    assert org.callers("asset", "repo-a", 140) == 1  # day 50 has left [51, 139]
    org.note("asset", "repo-a", "dave", 120)
    org.note("asset", "repo-a", "dave", 140)
    assert org.callers("asset", "repo-a", 140) == 2  # dave's day 120 counts, not today


def test_a_value_new_to_the_org_is_the_strongest_record() -> None:
    org = OrgFirstSeen()
    for i in range(12):
        org.note("client", ("app-1", "cursor"), f"caller-{i}", 30)
    common = value_strength(org.callers("client", ("app-1", "cursor"), 31))
    fresh = value_strength(org.callers("client", ("app-9", "unknown"), 31))
    assert fresh == 1.0 > common


def test_a_tool_is_new_only_if_it_entered_the_listing_recently() -> None:
    org = OrgFirstSeen()
    org.note_listing("tool", {"list_issues", "get_file"}, 10)  # the baseline
    org.note("tool", "list_issues", "alice", 12)
    assert not org.is_new_to_org("tool", "list_issues", 12)
    org.note_listing("tool", {"list_issues", "get_file", "export_all"}, 20)
    assert org.is_new_to_org("tool", "export_all", 25)
    assert not org.is_new_to_org("tool", "export_all", 50)
    org.note_listing("tool", {"list_issues", "export_all"}, 30)
    assert org.is_new_to_org("tool", "export_all", 31)  # it keeps the day it entered
    org.note("tool", "undeclared", "bob", 31)  # used, but in no listing
    assert not org.is_new_to_org("tool", "undeclared", 31)
    assert not org.is_new_to_org("tool", "get_file", 31)  # it left the listing
    org.note_listing("tool", {"list_issues", "export_all", "get_file"}, 60)
    assert org.is_new_to_org("tool", "get_file", 61)  # listed again: it entered again


def test_a_tool_key_with_its_operation_reads_the_listing_by_tool_name() -> None:
    """A listing carries bare tool names, and the Footprint value is AI-7's key (``tool``,
    ``tool:operation`` or ``tool:?``): both forms find the tool."""
    org = OrgFirstSeen()
    org.note_listing("tool", {"issue_read", "list_issues"}, 10)  # the baseline
    org.note_listing("tool", {"issue_read", "list_issues", "issue_write", "ns:tool"}, 20)
    for key in ("issue_write", "issue_write:create", "issue_write:?", "issue_write:a:b"):
        assert org.is_new_to_org("tool", key, 25), key
    assert org.is_new_to_org("tool", "ns:tool:get", 25)  # the longest listed prefix
    for key in ("issue_read:get", "list_issues", "export_all:get", "resource:repo", ":x"):
        assert not org.is_new_to_org("tool", key, 25), key


def test_an_org_flood_stays_bounded_and_buys_no_discount() -> None:
    cap = 4_096
    org = OrgFirstSeen(max_values=cap, observed_since=0)
    for caller in ("alice", "bob", "carol"):
        org.note("client", "new-sdk", caller, 150)
    assert org.is_new_to_org("client", "new-sdk", 150)
    for i in range(FLOOD):
        org.note("client", f"junk-{i}", "mallory", 160)
    assert len(org) <= cap
    assert org.callers("client", "new-sdk", 161) == 0  # evicted: no callers, strongest
    org.note("client", "new-sdk", "dave", 161)
    assert org.run_start("client", "new-sdk") == 161
    assert not org.is_new_to_org("client", "new-sdk", 161)  # an eviction may hide a use


def test_an_eviction_guards_the_runs_it_could_hide_for_two_windows() -> None:
    """Day 60's eviction may hide a use of v from days 51-60, so v's run that begins on day
    140 is never new to the org, even after a later eviction on day 151."""
    org = OrgFirstSeen(max_values=4)
    for value in ("a", "b", "c", "d"):
        org.note("asset", value, "alice", 0)
    org.note("asset", "e", "alice", 60)  # evicts a
    org.note("asset", "v", "bob", 140)  # b, c and d left the window: room, no eviction
    assert list(org.evictions["asset"]) == [60]
    assert not org.is_new_to_org("asset", "v", 141)  # day 60 lies in [51, 140]
    for value in ("f", "g", "h"):
        org.note("asset", value, "carol", 151)
    org.note("asset", "v", "bob", 151)  # v is now the most recent ...
    org.note("asset", "i", "carol", 151)  # ... so f is evicted
    assert org.run_start("asset", "v") == 140 and org.run_start("asset", "f") is None
    assert list(org.evictions["asset"]) == [60, 151]
    assert not org.is_new_to_org("asset", "v", 151)


@pytest.mark.parametrize("seed", SEEDS)
def test_callers_match_a_recount_of_every_use(seed: int) -> None:
    """``callers`` keeps two days per caller and a per-day memo; it must equal a recount of
    every logged use, with now and then a late commit for the day before."""
    rng = random.Random(seed)
    org, log = OrgFirstSeen(), []
    values = [f"repo-{i}" for i in range(6)]
    agents = [f"agent-{i}" for i in range(80)]

    def recount(value: str, today: int, exclude: str | None = None) -> int:
        low = today - WINDOW + 1
        return len({c for v, c, d in log if v == value and c != exclude and low <= d < today})

    for today in range(0, 300, 3):
        for _ in range(rng.randint(0, 25)):
            day = today - 1 if rng.random() < 0.05 else today
            value, caller = rng.choice(values), rng.choice(agents)
            org.note("asset", value, caller, day)
            log.append((value, caller, day))
            if day == today and rng.random() < 0.1:  # the same caller's slow reply from yesterday
                org.note("asset", value, caller, today - 1)
                log.append((value, caller, today - 1))
            probe, who = rng.choice(values), rng.choice(agents)
            assert org.callers("asset", probe, today) == recount(probe, today)
            assert org.callers("asset", probe, today, exclude=who) == recount(probe, today, who)


def test_values_with_no_use_left_in_the_window_are_dropped() -> None:
    org = OrgFirstSeen()
    for i in range(100):
        org.note("asset", f"repo-{i}", "alice", 0)
    org.note("asset", "repo-new", "alice", WINDOW)
    assert len(org) == 1


def test_org_first_seen_round_trips() -> None:
    org = OrgFirstSeen()
    org.note_listing("tool", {"a", "b"}, 1)
    org.note_listing("tool", {"a", "b", "c"}, 5)
    for day in range(0, 120, 3):
        org.note("client", ("app", f"family-{day % 4}"), f"caller-{day % 7}", day)
    org.note("client", ("app", "family-new"), "caller-1", 110)
    back = OrgFirstSeen.from_json(json_round_trip(org.to_json()))
    assert back.to_json() == org.to_json()
    for family in ("0", "1", "2", "3", "new"):
        value = ("app", f"family-{family}")
        assert back.callers("client", value, 120) == org.callers("client", value, 120)
        assert back.is_new_to_org("client", value, 120) == org.is_new_to_org("client", value, 120)
    assert back.is_new_to_org("client", ("app", "family-new"), 120)
    assert back.is_new_to_org("tool", "c", 10)


def test_three_first_day_identities_never_count_as_colleagues() -> None:
    """E7: three Sybils start a value; none was established, so nothing is discounted."""
    uses = ColleagueFirstUses()
    for i, sybil in enumerate(("sybil-1", "sybil-2", "sybil-3")):
        uses.add(("tool", "export_all"), 10.0 + i, sybil, established=False)
    colleagues = uses.colleagues(("tool", "export_all"), 100.0, "mallory")
    assert colleagues == 0 and len(uses) == 0
    assert not org_discount_applies("tool", colleagues, True, "read", 2)


def test_three_established_colleagues_count_once_each_within_seven_days() -> None:
    uses, key = ColleagueFirstUses(), ("asset", "repo-new")
    uses.add(key, 10.0, "alice", established=True)
    uses.add(key, 11.0, "bob", established=True)
    assert uses.colleagues(key, 11.0, "dave") == 1  # only uses before the call count
    uses.add(key, 12.0, "carol", established=True)
    uses.add(key, 13.0, "alice", established=True)
    assert uses.colleagues(key, 20.0, "dave") == 3  # alice once
    assert uses.colleagues(key, 20.0, "alice") == 2
    assert uses.colleagues(key, 13.0 + FIRST_USE_SECONDS, "dave") == 1  # [13, 13 + 7 d)
    assert uses.colleagues(key, 14.0 + FIRST_USE_SECONDS, "dave") == 0


@pytest.mark.parametrize("seed", SEEDS)
def test_colleagues_equal_distinct_first_uses_when_everyone_is_established(seed: int) -> None:
    rng = random.Random(seed)
    v5, v4 = ColleagueFirstUses(), FirstUses(FIRST_USE_SECONDS)
    keys = [("tool", f"t{i}") for i in range(5)]
    agents = [f"agent-{i}" for i in range(8)]
    ts = 0.0
    for _ in range(2_000):
        ts += rng.expovariate(1 / 3_000)
        key, agent = rng.choice(keys), rng.choice(agents)
        assert v5.colleagues(key, ts, agent) == v4.others(key, ts, agent, distinct=True)
        v5.add(key, ts, agent, established=True)
        v4.add(key, ts, agent)


def test_colleague_first_uses_stay_bounded_under_a_flood() -> None:
    uses = ColleagueFirstUses(max_keys=4_096)
    for caller in ("alice", "bob", "carol"):
        uses.add(("client", "new-sdk"), 1.0, caller, established=True)
    for i in range(FLOOD):
        uses.add(("client", f"junk-{i}"), 2.0 + i * 1e-3, "mallory", established=True)
    assert len(uses) <= 4_096 and uses.dropped == FLOOD + 1 - 4_096
    assert uses.colleagues(("client", "new-sdk"), 200.0, "dave") == 0  # dropped: no discount
    back = ColleagueFirstUses.from_json(json_round_trip(uses.to_json()), max_keys=4_096)
    assert back.dropped == uses.dropped and back.to_json() == uses.to_json()


def test_colleague_first_uses_subset_and_round_trip() -> None:
    uses = ColleagueFirstUses()
    for i in range(30):
        uses.add(("client", ("app", f"f{i % 5}")), float(i), f"c{i % 4}", established=True)
    keys = [("client", ("app", "f1")), ("client", ("app", "f9"))]
    part = uses.subset(keys)
    assert len(part) == 1
    assert part.colleagues(keys[0], 40.0, "x") == uses.colleagues(keys[0], 40.0, "x")
    back = ColleagueFirstUses.from_json(json_round_trip(uses.to_json()))
    assert back.to_json() == uses.to_json()
    assert back.colleagues(keys[0], 40.0, "x") == uses.colleagues(keys[0], 40.0, "x")


@pytest.mark.parametrize(
    ("kind", "colleagues", "new_to_org", "operation", "static", "applies"),
    [
        ("tool", 3, True, "read", 2, True),
        ("tool", 3, True, "read", 3, True),  # the highest level still discounted
        ("tool", 2, True, "read", 2, False),  # fewer than 3 established colleagues
        ("tool", 3, False, "read", 2, False),  # someone used it 60 days ago
        ("tool", 3, True, "write", 2, False),  # a write tool, even after a catalog change
        ("tool", 3, True, "read", 4, False),  # a high-impact tool
        ("tool", 3, True, None, 2, False),  # not labelled read yet: fails closed
        ("tool", 3, True, "read", None, False),  # no static level yet: fails closed
        ("tool", 3, True, None, None, False),  # new to the catalog and not scanned yet
        ("network", 3, True, "write", 5, True),  # network and client: discounted on writes
        ("client", 3, True, "write", 5, True),
        ("asset", 3, True, "write", 5, True),
        ("asset", 3, True, None, None, True),  # the tool's labels bind the tool only
    ],
)
def test_the_org_discount_condition(
    kind: str,
    colleagues: int,
    new_to_org: bool,
    operation: str | None,
    static: int | None,
    applies: bool,
) -> None:
    assert org_discount_applies(kind, colleagues, new_to_org, operation, static) is applies


def test_the_org_discount_with_v4s_values_needs_only_the_colleagues() -> None:
    assert org_discount_applies("tool", 3, True, "write", 5, reads_only=False, max_static=None)
    assert org_discount_applies("tool", 3, True, None, None, reads_only=False, max_static=None)


def test_each_tool_exclusion_fails_closed_only_while_it_is_on() -> None:
    assert org_discount_applies("tool", 3, True, None, 2, reads_only=False)
    assert not org_discount_applies("tool", 3, True, None, 2, reads_only=True)
    assert org_discount_applies("tool", 3, True, "read", None, max_static=None)
    assert not org_discount_applies("tool", 3, True, "read", None, max_static=3)
