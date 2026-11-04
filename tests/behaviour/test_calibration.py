"""v5 calibration (CAL-1..CAL-7): commonness, record rank, shares, floors, surge guard, clock.

Every rate printed or asserted here is from synthetic traffic, never a paper number. The probe
equivalence test imports ``org_record_rank_probe.py`` (arm O3) and prices its Burst and
Oversized arms through ``RouteClock.price``. The clock's exact prices, reference versions, GWR
and cost guards are in ``test_calibration_clock.py``.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_security.behaviour import engine
from mcp_security.behaviour.calibration import (
    ALERT,
    COPY_FLOOR,
    FIRST_ACCESS_FLOOR,
    GATEWAY,
    OVERFLOW,
    PROTOCOL_SKIP,
    REQUEST_TOO_BIG,
    WATCH,
    WATCH_CAP,
    AgentDay,
    CalibrationSettings,
    CallMeasures,
    DayRings,
    GatewayReference,
    Priced,
    RecordReference,
    ReferenceEntry,
    RouteClock,
    SurgeGuard,
    alert_line,
    apply_floors,
    cap_condition,
    combine,
    curve,
    first_access_floor,
    floor_budgets,
    outputs,
    path_active,
    record_price,
    shares_for,
    value_strength,
)
from mcp_security.behaviour.engine import BehaviourConfig

PROBES = (
    Path(__file__).resolve().parents[2]
    / "reports"
    / "experiments"
    / "dynamic_dimensions"
    / "knowledge_base"
    / "probes"
)
DAY = 86_400.0
HOUR = 3_600.0
PAST = 89  # the window's past days, [t-89, t-1]
UTC_MIDNIGHT = CalibrationSettings(route_zone="UTC", day_start_hour=0.0, route_warmup_days=None)
CALLS, WRITES, REPEATS = "calls_last_hour", "writes_last_hour", "same_call_10m"
TOOL, BURST, SEQUENCE = "tool", "burst", "sequence"
#: the probe's 15 dimensions in its column order (calib_per_dim_conformal.py, dimension index)
PROBE_DIMS = (
    "calls_last_hour",
    "writes_last_hour",
    "assets_last_hour",
    "same_call_10m",
    "session_length",
    "time_of_day",
    "tool",
    "asset",
    "network",
    "client",
    "burst",
    "many_assets",
    "request_too_big",
    "sequence",
    "protocol_skip",
)
STATED_ALPHAS = (0.01, 0.025, 0.05)


def day_ts(day: int, hour: float = 12.0) -> float:
    """A UTC timestamp on ``day`` at ``hour``."""
    return day * DAY + hour * HOUR


def closed(
    took: tuple[str, ...] = (),
    amounts: dict | None = None,
    values: dict | None = None,
    flags: dict | None = None,
    records: tuple[str, ...] = (),
) -> AgentDay:
    """A closed caller-day built by hand."""
    out = AgentDay(
        took=set(took) | set(amounts or {}) | set(values or {}) | set(flags or {}),
        amounts=dict(amounts or {}),
        values={d: set(v) for d, v in (values or {}).items()},
        flags={d: set(v) for d, v in (flags or {}).items()},
        records=set(records),
    )
    return out


# ── constants agree with the engine ─────────────────────────────────────────────────────────
def test_the_engine_keys_and_constants_are_the_engines() -> None:
    assert REQUEST_TOO_BIG == engine.REQUEST_TOO_BIG
    assert PROTOCOL_SKIP == engine.PROTOCOL_SKIP
    assert WATCH_CAP == engine.WATCH_CAP
    assert CalibrationSettings().surge_min == engine.SURGE_MIN
    assert CalibrationSettings().surge_factor == engine.SURGE_FACTOR
    assert CalibrationSettings().route_warmup_days == engine.ROUTE_WARMUP_DAYS
    for i in range(101):
        s = i / 100
        assert curve(s) == engine.multiplier(s)
    for alpha in (0.001, 0.01, 0.025, 0.05, 0.0943, 0.3):
        assert alert_line(alpha) == engine.alert_multiplier(alpha)


def test_settings_follow_a_v5_config_and_fail_fast() -> None:
    cfg = BehaviourConfig(design="v5")
    s = CalibrationSettings.from_config(cfg)
    assert (s.past_days, s.route_zone, s.day_start_hour) == (89, "UTC", 4.0)
    assert (s.max_history_days, s.min_active_days, s.max_values) == (365, 20, 4096)
    with pytest.raises(ValueError):
        CalibrationSettings(record_reference="band")
    with pytest.raises(ValueError):
        CalibrationSettings(route_zone="Mars/Olympus")
    with pytest.raises(ValueError):
        CalibrationSettings(max_history_days=50)
    with pytest.raises(ValueError):
        CallMeasures(amounts={CALLS: 1.0}, values={CALLS: ("x",)})
    with pytest.raises(ValueError):
        CallMeasures(amounts={CALLS: math.inf})


# ── CAL-1: DayRings ─────────────────────────────────────────────────────────────────────────
def test_amount_commonness_counts_past_day_maxima_at_least_as_large() -> None:
    rings = DayRings()
    for day, amount in zip(range(1, 6), (3.0, 7.0, 5.0, 7.0, 2.0), strict=True):
        rings.close_day(day, closed(amounts={CALLS: amount}))
    rings.close_day(6, closed(took=(BURST,)))  # an active day on which Call rate took no part
    assert rings.active_days(7) == 6
    tie = rings.amount(CALLS, 7.0, today=7)
    assert (tie.earlier, tie.days, tie.q) == (2, 5, 3 / 6)  # a tie counts as "at least"
    record = rings.amount(CALLS, 8.0, today=7)
    assert record.record and record.q == 1 / 6
    assert rings.amount(CALLS, 1.0, today=7).q == 1.0


def test_only_the_window_counts_and_today_never_does() -> None:
    rings = DayRings(past_days=89)
    rings.close_day(10, closed(amounts={CALLS: 50.0}))
    rings.close_day(60, closed(amounts={CALLS: 5.0}))
    assert rings.amount(CALLS, 10.0, today=99).earlier == 1  # day 10 is in [10, 98]
    assert rings.amount(CALLS, 10.0, today=100).earlier == 0  # day 10 left the window
    assert rings.amount(CALLS, 10.0, today=60).days == 1  # day 60 is today: not counted


def test_a_never_used_value_is_the_strangest_and_each_day_leaves_itself_out() -> None:
    rings = DayRings()
    for day, used in enumerate(({"a"}, {"a", "b"}, {"a"}, {"a", "c"}), start=1):
        rings.close_day(day, closed(values={TOOL: used}))
    # counts over J: a 4, b 1, c 1; day strangeness (itself left out): 3, 0, 3, 0
    new, rare, usual = (rings.value(TOOL, (v,), today=5) for v in ("z", "b", "a"))
    assert (new.earlier, rare.earlier, usual.earlier) == (2, 2, 4)
    assert new.q <= rare.q <= usual.q
    assert rings.value(TOOL, ("a", "z"), today=5).q == new.q  # the strangest value prices it
    plain = DayRings()
    for day in range(1, 4):
        plain.close_day(day, closed(values={TOOL: {"a"}}))
    assert plain.value(TOOL, ("z",), today=4).record


def test_a_never_used_value_is_never_less_strange_than_a_used_one() -> None:
    rng = random.Random(3)
    for _ in range(200):
        rings = DayRings()
        pool = [f"v{i}" for i in range(rng.randint(1, 8))]
        for day in range(1, rng.randint(2, 40)):
            if rng.random() < 0.8:
                used = set(rng.sample(pool, rng.randint(1, len(pool))))
                rings.close_day(day, closed(values={TOOL: used}))
        today = 41
        new = rings.value(TOOL, ("never",), today).q
        assert all(new <= rings.value(TOOL, (v,), today).q for v in pool)


def test_flags_count_habit_days_per_key_and_rf11_days_do_not_count() -> None:
    rings = DayRings()
    pair = ("repo-a", "repo-b")
    rings.close_day(1, closed(flags={BURST: {None}}))
    rings.close_day(2, closed(flags={SEQUENCE: {pair}}))
    rings.close_day(3, closed(flags={BURST: {None}}))
    assert rings.flag(BURST, None, today=4).earlier == 2
    assert rings.flag(SEQUENCE, pair, today=4).earlier == 1  # repeats of a pair are habit
    assert rings.flag(SEQUENCE, ("repo-a", "repo-c"), today=4).record  # a new pair is a record
    day = AgentDay()
    day.add(CallMeasures(flags={BURST: None}, habit=False), Priced({}))
    assert day.flags == {} and BURST in day.took  # took part, but not a habit day


def test_the_record_hold_keeps_recent_record_days_out_of_d_only() -> None:
    held = DayRings(record_hold_days=30)
    plain = DayRings()
    for rings in (held, plain):
        rings.close_day(50, closed(amounts={CALLS: 9.0}, records=(CALLS,)))
        rings.close_day(80, closed(amounts={CALLS: 9.0}, records=(CALLS,)))
    assert plain.amount(CALLS, 9.0, today=100).earlier == 2
    hold = held.amount(CALLS, 9.0, today=100)
    assert (hold.earlier, hold.days) == (1, 2)  # day 80 (>= 70) is held out; A keeps it


def test_the_record_hold_also_keeps_recent_first_raises_out_of_a_flags_habit() -> None:
    held, plain = DayRings(record_hold_days=30), DayRings()
    for rings in (held, plain):
        rings.close_day(60, closed(flags={BURST: {None}}, records=(BURST,)))  # 40 days ago
        rings.close_day(90, closed(flags={BURST: {None}}, records=(BURST,)))  # 10 days ago
    assert plain.flag(BURST, None, today=100).earlier == 2
    hold = held.flag(BURST, None, today=100)
    assert (hold.earlier, hold.days) == (1, 2)  # day 90's raise is held out of the habit
    recent = DayRings(record_hold_days=30)
    recent.close_day(90, closed(flags={BURST: {None}}, records=(BURST,)))
    assert recent.flag(BURST, None, today=100).record  # a first raise 10 days ago: a record


def test_minimum_history_stretches_the_window_back_until_it_holds_k_days() -> None:
    stretched = DayRings(max_history_days=365, min_active_days=3)
    fixed = DayRings()
    for rings in (stretched, fixed):
        for day in (10, 20, 30):
            rings.close_day(day, closed(amounts={CALLS: 1.0}))
    assert fixed.active_days(201) == 0
    assert stretched.window_start(201) == 10
    assert stretched.active_days(201) == 3
    assert stretched.active_days(400) == 0  # beyond 365 days nothing is kept


def test_a_values_flood_is_bounded_and_priced_as_new() -> None:
    day = AgentDay()
    day.add(CallMeasures(values={TOOL: tuple(f"v{i}" for i in range(1000))}), Priced({}), 4)
    assert len(day.values[TOOL]) == 5 and OVERFLOW in day.values[TOOL]
    rings = DayRings()
    rings.close_day(1, day)
    rings.close_day(2, closed(values={TOOL: {"v0"}}))
    assert rings.value(TOOL, ("v999",), today=3).earlier == 1  # the flood day counts as strange


def test_day_rings_round_trip_through_json() -> None:
    rings = DayRings(record_hold_days=30)
    rings.close_day(
        1, closed(amounts={CALLS: 2.0}, values={TOOL: {("x", 1)}}, flags={SEQUENCE: {("a", "b")}})
    )
    back = DayRings.from_json(
        json.loads(json.dumps(rings.to_json())), CalibrationSettings(record_hold_days=30)
    )
    assert back.value(TOOL, (("x", 1),), today=2) == rings.value(TOOL, (("x", 1),), today=2)
    assert back.flag(SEQUENCE, ("a", "b"), today=2).earlier == 1
    assert back.to_json() == rings.to_json()


# ── CAL-2: the record reference ─────────────────────────────────────────────────────────────
def entry(identity: str, ranked: dict | None = None, took=(BURST,), established=True):
    return ReferenceEntry(identity, established, frozenset(took) | set(ranked or {}), ranked or {})


def test_the_record_rank_is_an_add_one_rank_among_all_agent_days() -> None:
    ref = RecordReference()
    for day in range(10):
        for c in range(9):
            ranked = {BURST: float(c)} if c < 3 else {}
            ref.add(day, f"c{c}|{day}", entry(f"c{c}", ranked))
    ref.rebuild(10)
    assert ref.n(BURST) == 90 and ref.ranked_days(BURST) == 30
    assert ref.rank(BURST, 2.0) == (1 + 10) / 91  # ties count as "at least"
    assert ref.rank(BURST, 5.0) == 1 / 91
    assert ref.rank(BURST, -1.0) == 31 / 91
    assert ref.rank("sweep", 1.0) == 1.0  # nothing in the window: no help from the rank


def test_each_caller_files_one_record_day_per_dimension_per_day_its_strongest() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    clock.advance(day_ts(5))
    for strength in (2.0, 7.0, 3.0):
        clock.commit(
            "ann",
            day_ts(5),
            None,
            CallMeasures(took_part=frozenset({BURST})),
            Priced({}, (BURST,), {BURST: strength}),
        )
    clock.advance(day_ts(6))
    assert clock.reference.ranked_days(BURST) == 1 and clock.reference.n(BURST) == 1
    assert clock.reference.count_at_least(BURST, 7.0) == 1


def test_a_record_is_priced_by_the_min_of_its_personal_part_and_its_rank() -> None:
    assert record_price(9, 0.5) == 0.1
    assert record_price(9, 0.01) == 0.01
    with pytest.raises(ValueError):
        record_price(-1, 0.5)


def test_leave_top_identity_out_drops_the_flooder_from_ranks_and_n() -> None:
    plain, top = RecordReference(), RecordReference(leave_top_identity_out=True)
    for ref in (plain, top):
        for day in range(20):
            ref.add(day, f"flood|{day}", entry("flood", {BURST: 9.0}))
            ref.add(day, f"bea|{day}", entry("bea", {BURST: 1.0} if day < 2 else {}))
            ref.add(day, f"cy|{day}", entry("cy"))
        ref.rebuild(20)
    assert plain.rank(BURST, 5.0) == 21 / 61
    assert top.left_out == {BURST: "flood"}
    assert (top.n(BURST), top.rank(BURST, 5.0)) == (40, 1 / 41)


def test_the_established_reference_keeps_only_established_agent_days() -> None:
    ref = RecordReference(established_only=True)
    ref.add(0, "new|0", entry("new", {BURST: 9.0}, established=False))
    ref.add(0, "old|0", entry("old", {BURST: 1.0}))
    ref.rebuild(1)
    assert (ref.n(BURST), ref.ranked_days(BURST)) == (1, 1)
    assert ref.rank(BURST, 5.0) == 1 / 2


def test_a_gateway_reference_is_shared_by_its_routes() -> None:
    with pytest.raises(ValueError):
        RouteClock(CalibrationSettings(reference_scope=GATEWAY))
    gw = CalibrationSettings(reference_scope=GATEWAY, route_zone="UTC", day_start_hour=0.0)
    shared = GatewayReference(gw)
    github, slack = (
        RouteClock(gw, route="github", gateway=shared),
        RouteClock(gw, route="slack", gateway=shared),
    )
    for clock in (github, slack):
        clock.advance(day_ts(3))
    github.commit("ann", day_ts(3), None, CallMeasures(), Priced({}, (BURST,), {BURST: 4.0}))
    slack.commit("ann", day_ts(3), None, CallMeasures(), Priced({}, (BURST,), {BURST: 2.0}))
    fold = github.advance(day_ts(4))  # the gateway folds both routes at once
    assert fold is not None and (fold.folded, fold.callers) == (2, 2)
    assert slack.advance(day_ts(4)) is None
    assert slack.reference is github.reference is shared.reference
    assert slack.surge is github.surge is shared.surge
    assert shared.reference.n(BURST) == 2  # one agent-day per (route, caller, day)
    assert slack.to_json()["reference"] is None and slack.day == github.day == 4


def test_cap_condition_at_a_90_day_window_the_personal_part_cannot_reach_one_percent() -> None:
    shares = {w for w in shares_for(BehaviourConfig(design="v5")).values() if w is not None}
    assert shares == {1 / 21, 1 / 12}
    for share in shares:
        for alpha in (*STATED_ALPHAS, 0.0943):
            assert cap_condition(share, alpha)
        for active in range(90):  # A_d <= 89
            personal = record_price(active, rank=1.0) / share
            assert personal > 0.01 and personal >= 12 / 90
    assert cap_condition(1 / 12, 12 / 90 - 1e-6)
    assert not cap_condition(1 / 12, 12 / 90)  # the condition fails at alpha >= 13.3%
    assert not cap_condition(1 / 12, 12 / 180 + 1e-9, past_days=179)  # a longer window (W6)


def test_path_activity_needs_n_plus_one_at_least_one_over_w_alpha() -> None:
    for share, need in ((1 / 18, 1800), (1 / 12, 1200), (1 / 21, 2100)):
        assert path_active(need - 1, share, 0.01)
        assert not path_active(need - 2, share, 0.01)
    ref = RecordReference()
    for c in range(30):
        ref.add(0, str(c), entry(str(c)))
    ref.rebuild(1)
    report = ref.path_activity({BURST: 1 / 12, PROTOCOL_SKIP: None}, 0.05)
    assert report == {BURST: False}  # 31 < 240: the path is inactive


# ── CAL-3, CAL-4, CAL-5 ─────────────────────────────────────────────────────────────────────
def test_combine_takes_the_weighted_minimum_and_caps_watch_only_terms() -> None:
    shares = shares_for(BehaviourConfig(design="v5"))
    stat = combine({CALLS: 0.02, BURST: 0.005, PROTOCOL_SKIP: 0.0001}, shares)
    assert stat.dimension == BURST and stat.q == pytest.approx(0.06)
    assert stat.runner_up == PROTOCOL_SKIP and stat.q2 == pytest.approx(WATCH_CAP)
    assert stat.values[CALLS] == pytest.approx(0.42)
    alone = combine({PROTOCOL_SKIP: 0.0}, shares)
    assert alone.q == pytest.approx(WATCH_CAP) and alone.q > max(STATED_ALPHAS)
    assert combine({CALLS: 0.02}, shares).values[CALLS] == stat.values[CALLS]  # no renormalising
    nothing = combine({CALLS: math.inf}, shares)
    assert nothing.dimension is None and nothing.q == math.inf
    with pytest.raises(ValueError):
        combine({"unknown": 0.1}, shares)


def test_ties_go_to_the_dimension_first_in_the_design_order_whatever_the_rates_order() -> None:
    shares = {CALLS: 0.1, TOOL: 0.1, BURST: 0.1}
    for rates in (
        {BURST: 0.01, TOOL: 0.01, CALLS: 0.01},
        {TOOL: 0.01, CALLS: 0.01, BURST: 0.01},
    ):
        stat = combine(rates, shares)
        assert (stat.dimension, stat.runner_up) == (CALLS, TOOL)
    assert combine({BURST: 0.01, TOOL: 0.02}, shares).dimension == BURST  # no tie: the minimum


def test_footprint_watch_only_under_d3_b_never_reaches_a_stated_line() -> None:
    watch = shares_for(BehaviourConfig(design="v5", footprint_alerts=False))
    assert watch[TOOL] is None and watch[CALLS] == 1 / 21
    assert combine({TOOL: 0.0}, watch).q == pytest.approx(WATCH_CAP)
    assert combine({TOOL: 0.0}, shares_for(BehaviourConfig(design="v5"))).q == 0.0


def test_a_floor_wins_only_when_strictly_smaller_and_then_names_itself() -> None:
    stat = combine({CALLS: 0.02, BURST: 0.06}, {CALLS: 1 / 21, BURST: 1 / 12})
    won = apply_floors(stat, alert=[FIRST_ACCESS_FLOOR])
    assert (won.q, won.dimension, won.q2, won.runner_up) == (
        0.01,
        FIRST_ACCESS_FLOOR,
        stat.q,
        CALLS,
    )
    assert won.floors == (FIRST_ACCESS_FLOOR,) and won.alert_floors == (FIRST_ACCESS_FLOOR,)
    low = combine({CALLS: 0.0001}, {CALLS: 1 / 21})
    kept = apply_floors(low, watch=[FIRST_ACCESS_FLOOR])
    assert kept.dimension == CALLS and kept.floors == (FIRST_ACCESS_FLOOR,)
    tie = combine({BURST: 0.01}, {BURST: 1.0})
    assert apply_floors(tie, alert=[COPY_FLOOR]).dimension == BURST  # a tie keeps the statistic
    assert apply_floors(stat).q == stat.q


def test_route_warm_up_and_demotion_turn_alert_floors_into_watch_floors() -> None:
    stat = combine({CALLS: 0.5}, {CALLS: 1 / 21})
    cold = apply_floors(stat, alert=[FIRST_ACCESS_FLOOR], route_warm=False)
    assert cold.q == 0.125 and cold.alert_floors == ()
    demoted = apply_floors(stat, alert=[COPY_FLOOR, FIRST_ACCESS_FLOOR], demoted={COPY_FLOOR})
    assert demoted.q == 0.01 and demoted.dimension == FIRST_ACCESS_FLOOR
    assert demoted.floors == (COPY_FLOOR, FIRST_ACCESS_FLOOR)
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0))
    clock.advance(day_ts(100))
    assert not clock.route_warm
    clock.advance(day_ts(113))
    assert not clock.route_warm
    clock.advance(day_ts(114))
    assert clock.route_warm


def test_first_access_levels_and_floor_budgets() -> None:
    assert first_access_floor(5, touched=False, unique_match=True) == ALERT
    assert first_access_floor(4, touched=False, unique_match=True) == WATCH
    assert first_access_floor(3, touched=False, unique_match=True) is None
    assert first_access_floor(5, touched=True, unique_match=True) is None
    assert first_access_floor(5, touched=False, unique_match=False) is None
    assert floor_budgets(BehaviourConfig(design="v5").floor_budget) == {
        FIRST_ACCESS_FLOOR: 0.003,
        COPY_FLOOR: 0.0005,
    }


def test_the_alert_is_q_at_most_alpha_which_is_m_at_least_the_alert_line() -> None:
    line = alert_line(0.01)
    assert line == pytest.approx(4.69, abs=0.005)
    floor = apply_floors(combine({}, {}), alert=[FIRST_ACCESS_FLOOR])
    out = outputs(floor, 0.01)
    assert out.alert and out.multiplier == line
    watch = outputs(apply_floors(combine({}, {}), watch=[FIRST_ACCESS_FLOOR]), 0.01)
    assert not watch.alert and watch.multiplier == pytest.approx(2.63, abs=0.005)
    rng = random.Random(5)
    for _ in range(2000):
        q = rng.choice([rng.random() * 0.03, rng.random(), math.inf])
        res = outputs(combine({CALLS: q}, {CALLS: 1.0}), 0.01)
        assert res.multiplier >= 1.0
        if abs(q - 0.01) > 1e-9:
            assert res.alert == (res.multiplier >= line)
    assert outputs(combine({}, {}), 0.01).multiplier == 1.0
    assert outputs(combine({CALLS: 0.1}, {CALLS: 1.0}), None, line=3.0).alert is False


# ── CAL-6: surge guard; the min and the guard never lower q ─────────────────────────────────
def test_the_surge_guard_needs_a_surge_and_only_raises_q() -> None:
    ref = RecordReference()
    for day in range(89):
        ref.add(day, f"x|{day}", entry("x", {BURST: 1.0} if day % 3 == 0 else {}))
    ref.rebuild(89)
    guard = SurgeGuard(5, 3.0)
    assert guard.threshold(BURST, ref) == 5  # mean 30/89: max(5, 1.01)
    for c in range(3):
        guard.note(f"c{c}", (BURST,), {BURST: 9.0})
    assert guard.price(BURST, "c9", 1.0, 0.001, ref) == (0.001, False)  # 4 < 5
    guard.note("c3", (BURST,), {BURST: 9.0})
    for c in range(4, 20):
        guard.note(f"c{c}", (BURST,), {})
    q, hot = guard.price(BURST, "c9", 1.0, 0.001, ref)
    assert hot and q == (1 + 4) / (20 + 1)  # c0-c3 are stronger; 20 callers took part today
    assert guard.notice(BURST) and not guard.notice(BURST)
    rng = random.Random(11)
    for _ in range(3000):
        guard.reset()
        for c in range(rng.randint(0, 30)):
            ranked = {BURST: rng.random()} if rng.random() < 0.5 else {}
            guard.note(f"c{c}", (BURST,), ranked)
        q = rng.random() ** 3
        assert guard.price(BURST, f"c{rng.randint(0, 40)}", rng.random(), q, ref)[0] >= q


def test_the_surge_threshold_is_the_factor_times_the_window_mean_when_that_is_larger() -> None:
    def reference(ranked_days: int) -> RecordReference:
        ref = RecordReference()
        for i in range(ranked_days):
            day = i % PAST
            ref.add(day, f"x{i}", entry(f"x{i}", {BURST: 1.0}))
        ref.rebuild(PAST)
        return ref

    ref = reference(445)  # a daily mean of 445 / 89 = 5 ranked days
    guard = SurgeGuard(5, 3.0)
    assert ref.daily_mean(BURST) == 5.0 and guard.threshold(BURST, ref) == 445 * 3 / 89 == 15
    for c in range(13):
        guard.note(f"c{c}", (BURST,), {BURST: 9.0})
    assert guard.price(BURST, "me", 1.0, 0.001, ref) == (0.001, False)  # 13 + me = 14 < 15
    guard.note("c13", (BURST,), {BURST: 9.0})
    q, hot = guard.price(BURST, "me", 1.0, 0.001, ref)  # 14 + me = 15: a surge
    assert hot and q == (1 + 14) / (14 + 1 + 1)
    over = reference(450)  # 3 x 450 / 89 = 15.17: 15 is not a surge (it would be at 450 / 90)
    straddle = SurgeGuard(5, 3.0)
    for c in range(14):
        straddle.note(f"c{c}", (BURST,), {BURST: 9.0})
    assert not straddle.surging(BURST, over, "me")
    straddle.note("c14", (BURST,), {BURST: 9.0})
    assert straddle.surging(BURST, over, "me")


def test_the_online_surge_rank_counts_the_caller_before_he_commits() -> None:
    ref = RecordReference()
    ref.rebuild(PAST)  # an empty window: the threshold is surge_min
    guard = SurgeGuard(2, 3.0)
    guard.note("a", (BURST,), {BURST: 5.0})
    guard.note("b", (BURST,), {})
    q, hot = guard.price(BURST, "me", 1.0, 0.0, ref)  # a + me = 2 ranked: a surge
    assert hot and q == (1 + 1) / (2 + 1 + 1)  # a is stronger; a, b and me took part today
    guard.note("me", (BURST,), {BURST: 1.0})
    assert guard.price(BURST, "me", 1.0, 0.0, ref) == (q, True)  # noted: not counted twice


def test_the_personal_min_never_creates_an_alert_the_rank_alone_would_not() -> None:
    rng = random.Random(13)
    shares = (1 / 21, 1 / 12)
    for _ in range(20_000):
        active, rank = rng.randint(0, 89), rng.random() ** 4
        q = record_price(active, rank)
        assert q <= 1 / (active + 1)  # a record is never priced above a non-record
        for share in shares:
            for alpha in (*STATED_ALPHAS, 0.0943):
                if q / share <= alpha:
                    assert q == rank


# ── CAL-7: the route clock ──────────────────────────────────────────────────────────────────
def burst_record(strength: float) -> tuple[CallMeasures, Priced]:
    return CallMeasures(took_part=frozenset({BURST})), Priced({}, (BURST,), {BURST: strength})


def test_a_dormant_callers_last_day_enters_the_reference_at_the_next_rollover() -> None:
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=4.0))
    clock.advance(day_ts(10, 5))
    clock.commit("dormant", day_ts(10, 22), None, *burst_record(6.0))
    clock.commit(
        "busy", day_ts(10, 23), None, CallMeasures(took_part=frozenset({BURST})), Priced({})
    )
    assert clock.advance(day_ts(11, 3)) is None  # 03:00 still belongs to day 10
    assert clock.reference.n(BURST) == 0
    fold = clock.advance(day_ts(11, 4))
    assert fold is not None and (fold.day, fold.folded, fold.callers) == (11, 2, 2)
    assert clock.reference.ranked_days(BURST) == 1 and clock.reference.n(BURST) == 2
    assert 10 in clock.callers["dormant"].days and "dormant" not in clock.open
    clock.commit(
        "busy", day_ts(11, 9), None, CallMeasures(took_part=frozenset({BURST})), Priced({})
    )
    clock.advance(day_ts(12, 5))
    assert clock.reference.ranked_days(BURST) == 1 and clock.reference.n(BURST) == 3
    assert set(fold.digests) == {BURST} and fold.notice()["day"] == 11


def test_a_caller_dormant_past_every_window_is_forgotten() -> None:
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0))
    clock.advance(day_ts(0))
    clock.commit("gone", day_ts(0), None, *burst_record(1.0))
    clock.advance(day_ts(1))
    assert "gone" in clock.callers
    clock.advance(day_ts(90))
    assert "gone" in clock.callers  # day 0 is still within reach of a local day 89
    clock.advance(day_ts(91))
    assert "gone" not in clock.callers
    b5 = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0, max_history_days=365))
    b5.advance(day_ts(0))
    b5.commit("away", day_ts(0), None, *burst_record(1.0))
    b5.advance(day_ts(200))
    assert "away" in b5.callers  # B5 keeps a long-absent caller's history


def test_a_callers_own_days_reach_his_rings_before_the_route_rolls_over() -> None:
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=4.0))
    tokyo = "Asia/Tokyo"
    clock.advance(day_ts(10, 12))
    m = CallMeasures(amounts={CALLS: 3.0})
    clock.commit("kei", day_ts(10, 12), tokyo, m, clock.price("kei", day_ts(10, 12), tokyo, m))
    later = day_ts(10, 20)  # 05:00 the next day in Tokyo; the route is still on day 10
    priced = clock.price("kei", later, tokyo, CallMeasures(amounts={CALLS: 2.0}))
    assert priced.commonness[CALLS].days == 1  # his day 10 is closed for him already
    assert clock.reference.n(CALLS) == 0  # but the route reference is frozen until 04:00 UTC
    clock.advance(day_ts(11, 5))
    assert clock.reference.n(CALLS) == 1
    la = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=4.0))
    la.advance(day_ts(10, 20))
    la.commit("lou", day_ts(10, 20), "America/Los_Angeles", m, Priced({}))
    la.advance(day_ts(11, 5))  # 21:00 on his day 10 in Los Angeles: not ended
    assert la.reference.n(CALLS) == 0 and "lou" in la.open
    la.advance(day_ts(12, 5))
    assert la.reference.n(CALLS) == 1 and "lou" not in la.open


LAZY_DAYS = 240  # longer than the window, so filed days reach its trailing edge
CALLER_ZONES = {
    "ann": None,
    "bea": "Asia/Tokyo",
    "cy": "America/New_York",
    "dee": "Pacific/Auckland",
}


def test_the_reference_is_the_same_whether_the_clock_ticks_daily_or_only_at_calls() -> None:
    rng = random.Random(17)
    events, day = [], 0
    while day < LAZY_DAYS:
        for caller, zone_name in CALLER_ZONES.items():
            if rng.random() < 0.8:
                hour = rng.uniform(0, 24)
                events.append((day_ts(day, hour), caller, zone_name, rng.random()))
        day += rng.choice((1, 1, 2, 3, 6))  # gaps of up to five days with no calls at all
    events.sort()
    settings = CalibrationSettings(route_zone="Europe/Berlin", day_start_hour=4.0)
    daily, lazy = RouteClock(settings), RouteClock(settings)
    prices = {"daily": [], "lazy": []}
    digests: dict[str, dict[int, dict]] = {"daily": {}, "lazy": {}}
    last = events[0][0]
    for ts, caller, zone_name, amount in events:
        t = last
        while t < ts:  # the daily clock also ticks every hour in between
            daily.advance(t)
            t += HOUR
        last = ts
        for name, clock in (("daily", daily), ("lazy", lazy)):
            clock.advance(ts)
            m = CallMeasures(amounts={CALLS: amount}, strengths={CALLS: amount})
            priced = clock.price(caller, ts, zone_name, m)
            prices[name].append((priced.rates, priced.reference_day))
            clock.commit(caller, ts, zone_name, m, priced)
            for version_day, version in clock.reference.versions.items():
                digests[name][version_day] = version.digests()
    end = events[-1][0] + 5 * DAY
    daily.advance(end)
    lazy.advance(end)
    assert prices["daily"] == prices["lazy"]
    assert len({day for _, day in prices["lazy"]}) > LAZY_DAYS // 5
    for day, seen in digests["lazy"].items():  # every version the lazy clock used is the daily's
        assert seen == digests["daily"][day], day
    assert daily.reference.digests() == lazy.reference.digests()
    assert daily.reference.to_json() == lazy.reference.to_json()
    for (filing, ready), filed in lazy.reference.buckets.items():
        for key in filed:  # filed under its own local day, ready at the rollover after it ended
            local = int(key.rsplit("\x1f", 1)[1])
            assert filing == local and ready in (local + 1, local + 2), (key, filing, ready)


def test_the_clock_refuses_calls_before_it_is_advanced() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    with pytest.raises(ValueError):
        clock.price("ann", day_ts(1), None, CallMeasures())
    clock.advance(day_ts(1))
    with pytest.raises(ValueError):
        clock.commit("ann", day_ts(2), None, CallMeasures(), Priced({}))
    assert clock.advance(day_ts(0)) is None and clock.day == 1  # time never goes back


def test_org_priced_flags_have_no_personal_part() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    clock.advance(day_ts(0))
    for c in range(9):
        org = {REQUEST_TOO_BIG: float(c)} if c < 3 else {}
        m = CallMeasures(org_flags=org, took_part=frozenset({REQUEST_TOO_BIG}))
        clock.commit(f"c{c}", day_ts(0), None, m, clock.price(f"c{c}", day_ts(0), None, m))
    clock.advance(day_ts(1))
    priced = clock.price("c0", day_ts(1), None, CallMeasures(org_flags={REQUEST_TOO_BIG: 1.5}))
    assert priced.rates[REQUEST_TOO_BIG] == (1 + 1) / (9 + 1)
    assert priced.records == () and priced.ranked == {REQUEST_TOO_BIG: 1.5}


def test_a_clock_survives_a_json_round_trip() -> None:
    settings = CalibrationSettings(route_zone="UTC", day_start_hour=4.0, record_hold_days=30)
    clock = RouteClock(settings, route="r")
    rng = random.Random(23)

    def step(c: RouteClock, ts: float, caller: str, amount: float) -> dict:
        c.advance(ts)
        m = CallMeasures(
            amounts={CALLS: amount},
            values={TOOL: (f"t{int(amount * 5)}",)},
            flags={SEQUENCE: ("a", f"b{int(amount * 3)}")} if amount > 0.7 else {},
            strengths={CALLS: amount, SEQUENCE: 1.0},
        )
        p = c.price(caller, ts, None, m)
        c.commit(caller, ts, None, m, p)
        return dict(p.rates)

    stream = sorted(
        (rng.uniform(0, 40 * DAY), f"c{rng.randint(0, 5)}", rng.random()) for _ in range(400)
    )
    for ts, caller, amount in stream[:250]:
        step(clock, ts, caller, amount)
    back = RouteClock.from_json(json.loads(json.dumps(clock.to_json())), settings, route="r")
    assert back.to_json() == clock.to_json()
    for ts, caller, amount in stream[250:]:
        assert step(back, ts, caller, amount) == step(clock, ts, caller, amount)


# ── the probe: arm O3 on a fixed synthetic array ────────────────────────────────────────────
N_SYN_AGENTS, N_SYN_DAYS, P_ACTIVE = 30, 160, 0.6
SURGE_DAYS = (100, 130)
SURGE_MIN_SYN = 5  # the settings' surge_min
BOUNDARY_DAY = 115  # exactly SURGE_MIN Burst record agent-days: a surge (>=, not >)
OVERSIZED_COLUMN = 12


@pytest.fixture(scope="module")
def probe() -> SimpleNamespace:
    np = pytest.importorskip("numpy")
    sys.path.insert(0, str(PROBES))
    try:
        import org_record_rank_probe as orp  # noqa: PLC0415  (a probe script, path set above)
    finally:
        sys.path.remove(str(PROBES))
    return SimpleNamespace(np=np, orp=orp, pdm=orp.pdm, syn=orp.syn)


def synthetic_rows(np, seed: int = 7) -> SimpleNamespace:
    """A fixed array: agent-days with 1-3 calls, a Cadence dimension that takes part on 80%
    of calls, Burst records, raised Oversized requests, and two surge days."""
    rng = np.random.default_rng(seed)
    agent, day, ts = [], [], []
    for d in range(N_SYN_DAYS):
        for a in range(N_SYN_AGENTS):
            if rng.random() < P_ACTIVE:
                for _ in range(int(rng.integers(1, 4))):
                    agent.append(a)
                    day.append(d)
                    ts.append(d * DAY + float(rng.uniform(1.0, DAY - 1.0)))
    agent, day, ts = np.array(agent), np.array(day), np.array(ts)
    n = len(agent)
    surge = np.isin(day, SURGE_DAYS)
    took_c = rng.random(n) < 0.8
    s_c = np.where(took_c, rng.random(n), np.nan)
    rec_c = took_c & (rng.random(n) < np.where(surge, 0.6, 0.04))
    rec_b = rng.random(n) < np.where(surge, 0.5, 0.03)
    boundary = np.flatnonzero(day == BOUNDARY_DAY)
    rec_b[boundary] = False
    first_rows = boundary[np.unique(agent[boundary], return_index=True)[1]]
    rec_b[first_rows[:SURGE_MIN_SYN]] = True
    mag_b = np.where(rec_b, 1.0 + rng.exponential(1.0, n), np.nan)
    raised_o = rng.random(n) < np.where(surge, 0.5, 0.03)
    rho_o = np.where(raised_o, 1.0 + rng.exponential(1.0, n), np.nan)
    return SimpleNamespace(**locals())


def test_record_rank_surge_and_org_flags_equal_the_o3_probe(probe) -> None:
    np, orp, pdm = probe.np, probe.orp, probe.pdm
    x = synthetic_rows(np)
    v = SimpleNamespace(agent=x.agent, day=x.day, magnitude={OVERSIZED_COLUMN: x.rho_o})
    ones = np.ones(x.n, bool)
    s_bins, m_bins = (pdm.S_BINS, pdm.s_bin), (pdm.MAG_BINS, pdm.mag_bin)
    # the probe (offline, whole days)
    q_c, _, n_c = orp.org_rank(v, x.rec_c, x.s_c, x.took_c, s_bins)
    want_c, _ = orp.surge_price(v, x.rec_c, x.s_c, x.took_c, s_bins, q_c)
    mag_b = np.nan_to_num(x.mag_b, nan=0.0)
    q_b, _, n_b = orp.org_rank(v, x.rec_b, mag_b, ones, m_bins)
    a = pdm.active_days_at(x.agent, x.day, x.agent, x.day)
    o_b = q_b.copy()
    o_b[x.rec_b] = np.minimum(1.0 / (a[x.rec_b] + 1.0), q_b[x.rec_b])
    want_b, surge_days = orp.surge_price(v, x.rec_b, mag_b, ones, m_bins, o_b)
    q_o = pdm.org_flag_rate(v, OVERSIZED_COLUMN)
    want_o, _ = orp.surge_price(v, x.raised_o, np.nan_to_num(x.rho_o), ones, m_bins, q_o)
    # this module (online, a whole day noted before it is priced, as the probe does). Burst
    # records and Oversized requests go through RouteClock.price: a Burst record is a flag
    # under a key never raised before (each row its own key, not a habit), with its bin as
    # strength. Call rate's records have no personal part in the probe, so its rank and surge
    # are composed by hand.
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0))
    s_bin = pdm.s_bin(np.nan_to_num(x.s_c))
    m_bin_b, m_bin_o = pdm.mag_bin(x.mag_b), pdm.mag_bin(x.rho_o)
    got = {name: np.full(x.n, np.inf) for name in ("c", "b", "o")}
    by_day = [np.flatnonzero(x.day == d) for d in range(N_SYN_DAYS)]

    def measures(i: int) -> CallMeasures:
        took = {BURST, REQUEST_TOO_BIG} | ({CALLS} if x.took_c[i] else set())
        burst = {BURST: ("row", int(i))} if x.rec_b[i] else {}
        oversized = {REQUEST_TOO_BIG: int(m_bin_o[i])} if x.raised_o[i] else {}
        return CallMeasures(
            flags=burst,
            org_flags=oversized,
            strengths={BURST: int(m_bin_b[i])} if x.rec_b[i] else {},
            took_part=frozenset(took),
            habit=False,
        )

    for d, rows in enumerate(by_day):
        clock.advance(d * DAY)
        for i in rows:
            caller = f"a{x.agent[i]}"
            pre = clock.price(caller, x.ts[i], None, measures(i))
            assert pre.records == ((BURST,) if x.rec_b[i] else ())
            ranked, records = dict(pre.ranked), list(pre.records)
            if x.rec_c[i]:
                ranked[CALLS] = int(s_bin[i])
                records.append(CALLS)
            clock.commit(caller, x.ts[i], None, measures(i), Priced({}, tuple(records), ranked))
        for i in rows:
            caller, ref = f"a{x.agent[i]}", clock.reference
            if x.took_c[i]:
                assert ref.n(CALLS) == n_c[i]
            assert ref.n(BURST) == n_b[i]
            if x.rec_c[i]:
                s = int(s_bin[i])
                got["c"][i] = clock.surge.price(CALLS, caller, s, ref.rank(CALLS, s), ref)[0]
            priced = clock.price(caller, x.ts[i], None, measures(i))
            assert priced.reference_day == d
            if x.rec_b[i]:
                assert priced.commonness[BURST].days == a[i]
                got["b"][i] = priced.rates[BURST]
            if x.raised_o[i]:
                got["o"][i] = priced.rates[REQUEST_TOO_BIG]
    for name, mask, want in (
        ("c", x.rec_c, want_c),
        ("b", x.rec_b, want_b),
        ("o", x.raised_o, want_o),
    ):
        assert np.array_equal(got[name][mask], want[mask]), name
    assert surge_days >= len(SURGE_DAYS) + 1 and np.any(want_b[x.rec_b] > o_b[x.rec_b])
    on_boundary = x.rec_b & (x.day == BOUNDARY_DAY)
    assert on_boundary.sum() == SURGE_MIN_SYN
    assert np.any(want_b[on_boundary] > o_b[on_boundary])  # the guard acted at the threshold


def test_combine_and_floors_equal_the_o3_probe(probe) -> None:
    np, orp, pdm, syn = probe.np, probe.orp, probe.pdm, probe.syn
    rng = np.random.default_rng(29)
    n = 3000
    active = rng.integers(0, 90, (n, len(PROBE_DIMS)))
    q = (1.0 + rng.integers(0, active + 1)) / (active + 1.0)
    org = (1.0 + rng.integers(0, 40, (n, len(PROBE_DIMS)))) / 3001.0
    q = np.where(rng.random(q.shape) < 0.3, org, q)
    q = np.where(rng.random(q.shape) < 0.3, np.inf, q)
    q[:20] = np.inf  # rows where nothing took part
    capped = q.copy()
    hs = len(PROBE_DIMS) - 1
    capped[:, hs] = np.maximum(capped[:, hs], orp.WATCH_CAP * orp.W_O2[hs])
    want_q, want_d, want_q2 = pdm.stage2(capped, orp.W_O2)
    floor = rng.choice([0.0, 0.8, 0.9], n, p=[0.8, 0.1, 0.1])
    fq, _ = syn.floor_q(
        SimpleNamespace(floor=floor, agent=np.zeros(n), day=np.zeros(n, int)), "fixed"
    )
    use = fq < want_q
    shares = {d: float(w) for d, w in zip(PROBE_DIMS[:hs], orp.W_O2[:hs], strict=True)}
    shares[PROTOCOL_SKIP] = None
    for i in range(n):
        rates = {d: float(q[i, j]) for j, d in enumerate(PROBE_DIMS)}
        stat = combine(rates, shares, watch_share=float(orp.W_O2[hs]))
        assert stat.q == want_q[i] and stat.q2 == want_q2[i]
        assert stat.dimension == (PROBE_DIMS[want_d[i]] if want_d[i] >= 0 else None)
        dec = apply_floors(
            stat,
            alert=[FIRST_ACCESS_FLOOR] if floor[i] > 0.85 else [],
            watch=[FIRST_ACCESS_FLOOR] if 0.75 < floor[i] < 0.85 else [],
        )
        assert dec.q == (fq[i] if use[i] else want_q[i])
        assert dec.q2 == (want_q[i] if use[i] else want_q2[i])
        assert (dec.dimension == FIRST_ACCESS_FLOOR) == bool(use[i])
    assert use.sum() > 50


# ── the bound on exchangeable synthetic streams ─────────────────────────────────────────────
#: up to 12%: the cap condition holds below 12/90 = 13.3% at share 1/12
PROPERTY_ALPHAS = (0.01, 0.05, 0.12)
BETA = 0.002  # the alert floor's true firing rate per agent-day in the synthetic stream
WARM_FROM = 90
SLACK_SE = 3.0


CORE_TOOLS = tuple(f"t{i}" for i in range(10))  # each caller keeps three of them
TAIL_TOOLS = tuple(f"x{i}" for i in range(400))  # a rare long tail, drawn on every day
P_TAIL = 0.004  # the chance a call uses a tail tool


def callers_using(users: dict[str, list], day: int) -> int:
    """How many callers used a tool on a past day of the window, [day - 89, day - 1]."""
    return sum(
        1
        for previous, last in users.values()
        if (last < day and last >= day - PAST) or (previous is not None and previous >= day - PAST)
    )


def simulate(seed: int, n_callers: int = 100, n_days: int = 180, p_active: float = 0.7) -> dict:
    """Exchangeable callers: every amount, value, flag and floor is i.i.d. across callers and
    days. Each caller uses three core tools and, rarely, a tail tool; a tail tool new to him on
    a day when his window holds no other one-off tool is a Footprint record, priced by how few
    callers used it (D3 (a)). Returns, over warm agent-days, how many alerted and each
    dimension's spend."""
    rng = random.Random(seed)
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0))
    shares = shares_for(BehaviourConfig(design="v5"))
    core = {f"c{c}": rng.sample(CORE_TOOLS, 3) for c in range(n_callers)}
    users: dict[str, dict[str, list]] = {}  # tool -> caller -> [previous day, last day]
    dims = (CALLS, WRITES, REPEATS, TOOL, BURST, REQUEST_TOO_BIG)
    alerts = dict.fromkeys(PROPERTY_ALPHAS, 0)
    spend = {(a, d): 0 for a in PROPERTY_ALPHAS for d in dims}
    warm_days = records = 0
    for day in range(n_days):
        clock.advance(day * DAY + 1)
        for c in range(n_callers):
            if rng.random() >= p_active:
                continue
            caller, floor_fires = f"c{c}", rng.random() < BETA
            day_q, day_v = math.inf, dict.fromkeys(dims, math.inf)
            for k in range(rng.randint(1, 3)):
                ts = day * DAY + HOUR * (1 + 7 * k) + rng.random() * HOUR
                amounts = {d: rng.expovariate(1.0) for d in (CALLS, WRITES, REPEATS)}
                tail = rng.random() < P_TAIL
                tool = rng.choice(TAIL_TOOLS) if tail else rng.choice(core[caller])
                used_by = callers_using(users.get(tool, {}), day)
                strengths = dict(amounts) | {TOOL: value_strength(used_by)}
                flags, org = {}, {}
                if rng.random() < 0.03:
                    flags[BURST], strengths[BURST] = None, 1.0 + rng.expovariate(1.0)
                if rng.random() < 0.03:
                    org[REQUEST_TOO_BIG] = 1.0 + rng.expovariate(1.0)
                m = CallMeasures(
                    amounts=amounts,
                    values={TOOL: (tool,)},
                    flags=flags,
                    org_flags=org,
                    strengths=strengths,
                    took_part=frozenset({BURST, REQUEST_TOO_BIG}),
                )
                priced = clock.price(caller, ts, None, m)
                stat = combine(priced.rates, shares)
                fired = [FIRST_ACCESS_FLOOR] if floor_fires and k == 0 else []
                dec = apply_floors(stat, alert=fired, route_warm=clock.route_warm)
                day_q = min(day_q, dec.q)
                for d, q in priced.rates.items():
                    day_v[d] = min(day_v[d], q / shares[d])
                records += day >= WARM_FROM and TOOL in priced.records
                clock.commit(caller, ts, None, m, priced)
                seen = users.setdefault(tool, {}).get(caller)
                if seen is None or seen[1] < day:
                    users[tool][caller] = [None if seen is None else seen[1], day]
            if day >= WARM_FROM:
                warm_days += 1
                for a in PROPERTY_ALPHAS:
                    alerts[a] += day_q <= a
                    for d in dims:
                        spend[(a, d)] += day_v[d] <= a
    return {
        "n": warm_days,
        "alerts": alerts,
        "spend": spend,
        "shares": shares,
        "dims": dims,
        "tool_records": records,
    }


def slack(rate: float, n: int) -> float:
    return SLACK_SE * math.sqrt(max(rate, 1 / n) * (1 - rate) / n)


def test_on_exchangeable_streams_the_alert_rate_stays_within_alpha_plus_beta() -> None:
    res = simulate(seed=41)
    n = res["n"]
    assert n > 6000
    for alpha in PROPERTY_ALPHAS:
        bound = alpha + BETA
        realised = res["alerts"][alpha] / n
        assert realised <= bound + slack(bound, n), (alpha, realised)
        for d in res["dims"]:  # the per-dimension spend check (each within w_d alpha)
            share_bound = res["shares"][d] * alpha
            spent = res["spend"][(alpha, d)] / n
            assert spent <= share_bound + slack(share_bound, n), (alpha, d, spent)
    # the statistic can alert (it is not vacuous): at 12% the records and ranks do fire, and
    # so does Footprint's value path (D3 (a)), whose records are ranked like any other
    top = max(PROPERTY_ALPHAS)
    assert res["alerts"][top] / n > 0.25 * (top * sum(res["shares"][d] for d in res["dims"]))
    assert res["tool_records"] > 10 and res["spend"][(top, TOOL)] > 0


def test_a_value_strength_is_largest_for_a_value_new_to_the_organisation() -> None:
    assert value_strength(0) == 1.0 > value_strength(1) > value_strength(10)
    with pytest.raises(ValueError):
        value_strength(-1)
