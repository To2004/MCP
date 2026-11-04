"""RF5 FlagRates: Wilson bounds, floor demotion by established callers only, calibration.py's
floor names, per-era base rates, path activity and cap condition, day compaction and the JSON
round trip. Callers are agent keys (spec 2.1, D5). Synthetic streams only."""

from __future__ import annotations

import json
import random
from dataclasses import replace

import pytest

from mcp_security.behaviour import BehaviourConfig, calibration, clock
from mcp_security.behaviour.engine import replace_config
from mcp_security.behaviour.flag_rates import (
    COPY_FLOOR,
    FIRST_ACCESS_FLOOR,
    LATE_DAYS,
    LOWER,
    OVER,
    UNCLEAR,
    UNKNOWN_ERA,
    UPPER,
    WATCH_FLOOR,
    WITHIN,
    FlagRates,
    Interval,
    RateSettings,
    cap_condition_holds,
    dimension_item,
    flag_item,
    floor_firings,
    floor_item,
    format_report,
    nominal_rates,
    path_activity,
    rate_status,
    split_item,
    wilson_interval,
)

BETA = 0.003  # the first-access floor's budget (spec 2.4)
WINDOW = 30
ALPHA = 0.01
FIRST_ACCESS = floor_item(FIRST_ACCESS_FLOOR)
WATCH = floor_item(WATCH_FLOOR)
OVERSIZED = flag_item("request_too_big")
HANDSHAKE = flag_item("protocol_skip")
FOOTPRINT = ("tool", "asset", "network", "client")
V5 = BehaviourConfig(design="v5")


def _floor_rates(**overrides: object) -> FlagRates:
    return FlagRates(RateSettings(alert_floors={FIRST_ACCESS_FLOOR: BETA}, **overrides))


def _rows(report) -> dict:
    return {r.item: r for r in report.rates}


def _route(
    rates: FlagRates,
    established: int,
    firings: int,
    sybils: int = 0,
    sybil_fires: bool = True,
    days: int = WINDOW,
    item: str = FIRST_ACCESS,
) -> None:
    """``established`` callers active every day, ``firings`` of their agent-days with ``item``
    fired, spread evenly over the days; ``sybils`` new identities active every day, each
    firing ``item`` every day when ``sybil_fires``."""
    per_day, extra = divmod(firings, days)
    for day in range(days):
        fires_today = per_day + (day < extra)
        for i in range(established):
            fire = i < fires_today
            rates.add(day, f"agent{i}", (item,) if fire else (), established=True)
        for i in range(sybils):
            rates.add(day, f"sybil{i}", (item,) if sybil_fires else ())


# ── Wilson and status ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("raised", "days", "lower", "upper"),
    [  # Newcombe (1998), Stat. Med. 17:857-872, Table I, method 3 (Wilson score)
        (81, 263, 0.2553, 0.3662),
        (15, 148, 0.0624, 0.1605),
        (0, 20, 0.0, 0.1611),
        (1, 29, 0.0061, 0.1718),
    ],
)
def test_wilson_matches_the_published_table(
    raised: int, days: int, lower: float, upper: float
) -> None:
    interval = wilson_interval(raised, days)
    assert interval.lower == pytest.approx(lower, abs=5e-5)
    assert interval.upper == pytest.approx(upper, abs=5e-5)


def test_wilson_edges_and_width() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)
    assert wilson_interval(0, 50).lower == 0.0
    assert wilson_interval(50, 50).upper == 1.0
    narrow, wide = wilson_interval(100, 1_000), wilson_interval(10, 100)
    assert wide.lower < narrow.lower < 0.1 < narrow.upper < wide.upper
    assert wilson_interval(10, 100, 0.99).upper > wide.upper
    for bad in ((-1, 5), (6, 5), (1.0, 5), (True, 5)):
        with pytest.raises(ValueError):
            wilson_interval(*bad)
    with pytest.raises(ValueError):
        wilson_interval(1, 5, confidence=1.0)


def test_rate_status_boundaries_and_an_exact_zero_nominal() -> None:
    assert rate_status(Interval(0.005, 0.02), 0.005) == UNCLEAR  # lower == nominal: not over
    assert rate_status(Interval(0.0051, 0.02), 0.005) == OVER
    assert rate_status(Interval(0.001, 0.005), 0.005) == WITHIN  # upper == nominal
    assert rate_status(Interval(0.0, 0.2), None) is None
    quiet = wilson_interval(0, 4_500)
    assert quiet.upper > 0  # a Wilson bound alone could never confirm a zero rate
    assert rate_status(quiet, 0.0, 0) == WITHIN
    assert rate_status(quiet, 0.0) == WITHIN
    assert rate_status(wilson_interval(1, 4_500), 0.0, 1) == OVER
    assert rate_status(wilson_interval(1, 4_500), 0.0) == OVER


# ── floor names: calibration.py's ───────────────────────────────────────────────────────
def test_floor_names_are_calibrations_and_the_watch_floor_has_its_own_item() -> None:
    assert (FIRST_ACCESS_FLOOR, COPY_FLOOR) == calibration.FLOOR_ORDER
    assert WATCH_FLOOR not in calibration.FLOOR_ORDER
    settings = RateSettings.from_config(V5)
    assert settings.alert_floors == calibration.floor_budgets(V5.floor_budget)
    no_copy = RateSettings.from_config(replace_config(V5, copy_floor=False))
    assert dict(no_copy.alert_floors) == {FIRST_ACCESS_FLOOR: V5.floor_budget[0]}
    assert floor_item(COPY_FLOOR) not in no_copy.nominal


def test_settings_from_calibrations_floor_budgets_demote_and_feed_apply_floors() -> None:
    budgets = calibration.floor_budgets(V5.floor_budget)
    rates = FlagRates(RateSettings(alert_floors=budgets))
    # 300 established agents, 1% of their agent-days fire the alert floor, every agent-day
    # fires the watch floor (sensitivity 4): only the alert-level firings count
    _route(rates, established=300, firings=90)
    watch_level = floor_firings(watch=(FIRST_ACCESS_FLOOR,))  # what apply_floors got as watch
    for day in range(WINDOW):
        for i in range(300):
            rates.add(day, f"agent{i}", watch_level, established=True)
    report = rates.fold(WINDOW)
    assert rates.demoted_floors == (FIRST_ACCESS_FLOOR,)  # copy: 0 of 9,000, bound < 0.05%
    assert [e.floor for e in report.demotions] == [FIRST_ACCESS_FLOOR]
    rows = _rows(report)
    assert rows[WATCH].raised == 9_000 and rows[WATCH].nominal_rate is None
    assert rows[FIRST_ACCESS].established_raised == 90
    stat = calibration.combine({"tool": 0.5}, {"tool": 1 / 12})
    acting = calibration.apply_floors(stat, alert=(FIRST_ACCESS_FLOOR,))
    demoted = calibration.apply_floors(
        stat, alert=(FIRST_ACCESS_FLOOR,), demoted=rates.demoted_floors
    )
    assert acting.alert_floors == (FIRST_ACCESS_FLOOR,)
    assert demoted.alert_floors == () and demoted.q == calibration.WATCH_FLOOR_RATE


def test_watch_firings_never_demote_the_alert_floor() -> None:
    rates = FlagRates.from_config(V5)
    _route(rates, established=300, firings=9_000, item=WATCH)  # every agent-day
    rates.fold(WINDOW)
    assert rates.demoted_floors == ()


def test_overriding_alert_floors_leaves_no_stale_rows() -> None:
    raised = FlagRates.from_config(V5, alert_floors=calibration.floor_budgets((0.004, 0.0005)))
    assert raised.settings.nominal[FIRST_ACCESS] == 0.004
    floors = {k for k in raised.settings.nominal if split_item(k)[0] == "floor"}
    assert floors == {FIRST_ACCESS, floor_item(COPY_FLOOR), WATCH}
    only_first = RateSettings.from_config(V5, alert_floors={FIRST_ACCESS_FLOOR: BETA})
    assert floor_item(COPY_FLOOR) not in only_first.nominal
    assert only_first.nominal[FIRST_ACCESS] == BETA


def test_floor_firings_take_apply_floors_names() -> None:
    """The engine passes the same names to apply_floors and to floor_firings: a first access
    at the WATCH level never lands on the alert floor's item, and a name calibration.py does
    not know fails at once instead of escaping demotion."""
    every = floor_firings(alert=calibration.FLOOR_ORDER, watch=(FIRST_ACCESS_FLOOR,))
    assert every == (FIRST_ACCESS, floor_item(COPY_FLOOR), WATCH)
    assert floor_firings(watch=(FIRST_ACCESS_FLOOR,)) == (WATCH,)
    assert floor_firings(alert=(COPY_FLOOR, COPY_FLOOR)) == (floor_item(COPY_FLOOR),)
    assert floor_firings() == ()
    with pytest.raises(ValueError, match="one of"):
        floor_firings(alert=("first_access",))  # RF5's old name, once a silent mismatch
    with pytest.raises(ValueError, match="watch level"):
        floor_firings(watch=(COPY_FLOOR,))
    with pytest.raises(ValueError, match="string"):
        floor_firings(alert=FIRST_ACCESS_FLOOR)


# ── floor demotion ──────────────────────────────────────────────────────────────────────
def test_sybils_cannot_force_a_demotion() -> None:
    honest, attacked = _floor_rates(), _floor_rates()
    _route(honest, established=200, firings=3)
    _route(attacked, established=200, firings=3, sybils=500)
    clean, flooded = honest.fold(WINDOW), attacked.fold(WINDOW)
    assert not honest.demoted(FIRST_ACCESS_FLOOR)
    assert not attacked.demoted(FIRST_ACCESS_FLOOR)
    assert flooded.demotions == ()
    row = _rows(flooded)[FIRST_ACCESS]
    assert (row.established_raised, row.established_days) == (3, 6_000)
    assert row.raised == 3 + 500 * WINDOW and row.status == OVER  # every caller: far over
    assert row.established_upper < BETA
    assert _rows(clean)[FIRST_ACCESS].established_upper == pytest.approx(row.established_upper)
    # the same firings counted as established would demote: the guard is what holds
    counted = _floor_rates()
    _route(counted, established=200, firings=3)
    for day in range(WINDOW):
        for i in range(500):
            counted.add(day, f"sybil{i}", (FIRST_ACCESS,), established=True)
    counted.fold(WINDOW)
    assert counted.demoted(FIRST_ACCESS_FLOOR)


def test_sybils_cannot_block_a_demotion_either() -> None:
    plain, diluted = _floor_rates(), _floor_rates()
    _route(plain, established=200, firings=60)
    _route(diluted, established=200, firings=60, sybils=2_000, sybil_fires=False)
    for rates in (plain, diluted):
        report = rates.fold(WINDOW)
        assert rates.demoted(FIRST_ACCESS_FLOOR)
        (event,) = report.demotions
        assert (event.floor, event.day, event.demoted) == (FIRST_ACCESS_FLOOR, WINDOW, True)
        assert (event.raised, event.agent_days, event.beta, event.rule) == (60, 6_000, BETA, UPPER)
        assert event.bound > BETA
        assert report.demoted == (FIRST_ACCESS_FLOOR,)


def test_a_demotion_is_logged_once_and_restored_when_the_rate_falls() -> None:
    rates = _floor_rates()
    _route(rates, established=200, firings=60)
    assert len(rates.fold(WINDOW).demotions) == 1
    for i in range(200):
        rates.add(WINDOW, f"agent{i}", (), established=True)
    assert rates.fold(WINDOW + 1).demotions == ()  # still demoted: nothing new to log
    assert rates.demoted(FIRST_ACCESS_FLOOR)
    restored = ()
    for day in range(WINDOW + 1, 3 * WINDOW):
        for i in range(200):
            rates.add(day, f"agent{i}", (), established=True)
        restored = rates.fold(day + 1).demotions
        if restored:
            break
    assert restored, "the floor was never restored"
    (event,) = restored
    assert not event.demoted and event.bound <= BETA
    assert not rates.demoted(FIRST_ACCESS_FLOOR)
    assert event.fields()["demoted"] is False


def test_a_same_day_refold_logs_nothing_new() -> None:
    rates = _floor_rates()
    _route(rates, established=200, firings=60)
    first, again = rates.fold(WINDOW), rates.fold(WINDOW)
    assert len(first.demotions) == 1 and again.demotions == ()
    assert again.rates == first.rates and again.demoted == (FIRST_ACCESS_FLOOR,)


def test_upper_rule_demotes_a_small_route_without_firings_lower_rule_does_not() -> None:
    upper, lower = _floor_rates(), _floor_rates(demote_on=LOWER)
    for rates in (upper, lower):
        _route(rates, established=30, firings=0)  # 900 established agent-days, no firing
        rates.fold(WINDOW)
    assert wilson_interval(0, 900).upper > BETA
    assert upper.demoted(FIRST_ACCESS_FLOOR)
    assert not lower.demoted(FIRST_ACCESS_FLOOR)


def test_lower_rule_demotes_when_the_lower_bound_exceeds_beta() -> None:
    over, under = _floor_rates(demote_on=LOWER), _floor_rates(demote_on=LOWER)
    _route(over, established=200, firings=60)  # 1% of 6,000: lower bound about 0.78%
    _route(under, established=200, firings=18)  # 0.3%: lower bound below beta
    (event,) = over.fold(WINDOW).demotions
    assert event.rule == LOWER and event.bound == pytest.approx(wilson_interval(60, 6_000).lower)
    assert event.bound > BETA and over.demoted(FIRST_ACCESS_FLOOR)
    assert under.fold(WINDOW).demotions == () and not under.demoted(FIRST_ACCESS_FLOOR)


def test_a_bound_equal_to_beta_does_not_demote() -> None:
    """The spec demotes when the bound *exceeds* beta."""
    beta = wilson_interval(60, 6_000).upper
    at, below = (
        FlagRates(RateSettings(alert_floors={FIRST_ACCESS_FLOOR: b})) for b in (beta, beta * 0.999)
    )
    for rates in (at, below):
        _route(rates, established=200, firings=60)
        rates.fold(WINDOW)
    assert not at.demoted(FIRST_ACCESS_FLOOR)
    assert below.demoted(FIRST_ACCESS_FLOOR)


def test_upper_rule_on_a_route_with_no_established_callers() -> None:
    """Pins the spec's rule as written (escalated to the author): no evidence demotes."""
    rates = _floor_rates()
    _route(rates, established=0, firings=0, sybils=50, sybil_fires=False)
    (event,) = rates.fold(WINDOW).demotions
    assert (event.agent_days, event.raised, event.bound) == (0, 0, 1.0)
    assert rates.demoted(FIRST_ACCESS_FLOOR)


def test_an_agent_day_is_established_if_any_call_says_so_and_counts_once() -> None:
    rates = _floor_rates()
    rates.add(0, "a", (FIRST_ACCESS,))
    rates.add(0, "a", (FIRST_ACCESS,), established=True)
    rates.add(0, "a", (FIRST_ACCESS, OVERSIZED))
    rows = _rows(rates.report(1))
    assert (rows[FIRST_ACCESS].raised, rows[FIRST_ACCESS].agent_days) == (1, 1)
    assert rows[FIRST_ACCESS].established_raised == 1
    assert rows[OVERSIZED].raised == 1


# ── report, window, compaction, eras ────────────────────────────────────────────────────
def test_report_status_against_nominal_and_the_window() -> None:
    nominal = {OVERSIZED: 0.005, flag_item("burst"): 0.005, HANDSHAKE: None}
    rates = FlagRates(RateSettings(nominal=nominal))
    for day in range(40):
        for i in range(100):
            raised = (OVERSIZED,) if i < 5 else ()
            raised += (flag_item("burst"),) if day >= 39 and i == 0 else ()
            rates.add(day, f"c{i}", raised + ((HANDSHAKE,) if i % 2 else ()))
    report = rates.report(39)  # days 9..38: day 39's burst is outside
    rows = _rows(report)
    assert report.agent_days == 3_000
    assert rows[OVERSIZED].rate == pytest.approx(0.05) and rows[OVERSIZED].status == OVER
    assert rows[flag_item("burst")].raised == 0 and rows[flag_item("burst")].status == WITHIN
    assert rows[HANDSHAKE].status is None and rows[HANDSHAKE].rate == pytest.approx(0.5)
    small = FlagRates(RateSettings(nominal=nominal))
    small.add(0, "c", ())
    assert _rows(small.report(1))[OVERSIZED].status == UNCLEAR
    assert "request_too_big" in format_report(report)


def test_folds_go_forward_and_forget_days_outside_the_window() -> None:
    rates = FlagRates()
    rates.add(0, "a", (OVERSIZED,))
    rates.add(100, "a", ())
    rates.fold(100)
    with pytest.raises(ValueError):
        rates.fold(99)
    snapshot = rates.to_json()
    assert "0" not in snapshot["open"] and "0" not in snapshot["closed"]
    assert rates.report(31).agent_days == 0  # forgotten, not only hidden


def test_late_adds_reach_open_days_only() -> None:
    rates = _floor_rates()
    rates.add(0, "a", ())
    rates.fold(10)
    rates.add(10 - LATE_DAYS, "late", (FIRST_ACCESS,), established=True)  # a lagging caller
    with pytest.raises(ValueError, match="closed"):
        rates.add(10 - LATE_DAYS - 1, "later", ())
    row = _rows(rates.report(11))[FIRST_ACCESS]
    assert (row.raised, row.established_raised, row.agent_days) == (1, 1, 2)
    rates.add(10 - LATE_DAYS, "late", (FIRST_ACCESS,))  # the same agent-day: counts once
    rates.fold(11)  # day 8 is closed now: kept as counts, still in the window
    assert _rows(rates.report(12))[FIRST_ACCESS].raised == 1
    with pytest.raises(ValueError):
        rates.add(10 - LATE_DAYS, "late", ())


def test_late_days_cover_the_widest_zone_gap() -> None:
    """At a UTC+14 route's rollover to day t, an agent at UTC-12 is still in its local day
    t - 2 for two more hours (B9: 04:00 rollover, 26 hours behind), so its adds to day t - 2
    must still count after the fold."""
    route_zone, agent_zone = "Etc/GMT-14", "Etc/GMT+12"  # POSIX signs: UTC+14, UTC-12
    t = 20_000
    offset = clock.local_seconds(0.0, route_zone)  # a fixed zone: its UTC offset
    rollover = t * clock.DAY_S + clock.DAY_START_HOUR * clock.HOUR_S - offset
    assert clock.local_day(rollover - 1, route_zone) == t - 1
    assert clock.local_day(rollover, route_zone) == t
    lagging = clock.local_day(rollover, agent_zone)
    assert lagging == t - LATE_DAYS  # no zone pair lags further
    rates = _floor_rates()
    rates.fold(t)
    rates.add(lagging, "agent-west", (FIRST_ACCESS,), established=True)
    row = _rows(rates.report(t + 1))[FIRST_ACCESS]
    assert (row.raised, row.established_raised) == (1, 1)


def test_a_window_shorter_than_the_late_slack_keeps_its_open_days() -> None:
    rates = FlagRates(RateSettings(window_days=LATE_DAYS))
    rates.add(10 - LATE_DAYS, "a", (OVERSIZED,))
    rates.fold(10)  # day 8: still open for late adds, and the first day of [8, 9]
    assert _rows(rates.report(10))[OVERSIZED].raised == 1
    rates.fold(11)  # outside [9, 10] now: forgotten
    assert rates.report(10).agent_days == 0


def test_compacted_days_report_as_the_full_record() -> None:
    settings = RateSettings(alert_floors={FIRST_ACCESS_FLOOR: BETA}, nominal={HANDSHAKE: None})
    folded, kept = FlagRates(settings), FlagRates(settings)
    items = (OVERSIZED, HANDSHAKE, FIRST_ACCESS, WATCH)
    rng = random.Random(11)
    for day in range(70):
        calls = [(day, f"c{rng.randrange(40)}") for _ in range(rng.randrange(30, 60))]
        if day >= LATE_DAYS:  # callers whose local day lags the route's
            calls += [(day - rng.randrange(1, LATE_DAYS + 1), f"w{rng.randrange(10)}")]
        for d, caller in calls:
            raised = tuple(i for i in items if rng.random() < 0.1)
            era = rng.choice(("legacy", "modern", None))
            for rates in (folded, kept):
                rates.add(d, caller, raised, established=caller < "c2", era=era)
        report = folded.fold(day + 1)
        full = kept.report(day + 1)
        assert (report.rates, report.eras, report.agent_days) == (
            full.rates,
            full.eras,
            full.agent_days,
        )
        assert folded.report(day + 1) == replace(report, demotions=())  # nothing lost
    snapshot = folded.to_json()
    assert set(map(int, snapshot["open"])) <= set(range(70 - LATE_DAYS, 71))
    assert len(snapshot["closed"]) == WINDOW - LATE_DAYS
    assert all("callers" not in c for c in snapshot["closed"].values())


def test_malformed_inputs_fail_fast_and_leave_no_trace() -> None:
    rates = FlagRates()
    for bad in ("burst", "rule:burst", "flag:", 7):
        with pytest.raises(ValueError):
            rates.add(0, "a", (bad,))
    with pytest.raises(ValueError, match="string"):
        rates.add(0, "a", "flag:burst")
    with pytest.raises(ValueError):
        rates.add(0, "a", ("flag:burst", 7))
    with pytest.raises(ValueError):
        rates.add(0, "", ())
    with pytest.raises(ValueError):
        rates.add(0, "a", (), established=1)
    assert rates.report(1).agent_days == 0
    with pytest.raises(ValueError):
        RateSettings(demote_on="median")
    with pytest.raises(ValueError):
        RateSettings(nominal={FIRST_ACCESS: 0.01}, alert_floors={FIRST_ACCESS_FLOOR: BETA})
    for beta in (0.0, 1.0, -0.001, True):
        with pytest.raises(ValueError):
            RateSettings(alert_floors={FIRST_ACCESS_FLOOR: beta})
    assert split_item(dimension_item("asset")) == ("dimension", "asset")


def test_settings_mappings_are_read_only() -> None:
    settings = RateSettings.from_config(V5)
    for mapping in (settings.nominal, settings.alert_floors, settings.shares):
        with pytest.raises(TypeError):
            mapping["x"] = 0.1  # type: ignore[index]


def test_per_era_base_rates() -> None:
    rates = FlagRates(RateSettings(nominal={HANDSHAKE: None}))
    for day in range(10):
        for i in range(20):
            rates.add(day, f"legacy{i}", (HANDSHAKE,) if i < 4 else (), era="legacy")
            rates.add(day, f"modern{i}", (), era="modern")
        rates.add(day, "both", (), era="legacy")
        rates.add(day, "both", (HANDSHAKE,), era="modern")
        rates.add(day, "anon", ())
    eras = {(e.era, e.item): e for e in rates.report(10).eras}
    assert eras["legacy", HANDSHAKE].agent_days == 210  # "both" counts in each era it used
    assert eras["legacy", HANDSHAKE].raised == 40
    assert eras["modern", HANDSHAKE].raised == 10 and eras["modern", HANDSHAKE].agent_days == 210
    assert eras[UNKNOWN_ERA, HANDSHAKE].agent_days == 10
    assert eras["legacy", HANDSHAKE].rate == pytest.approx(40 / 210)
    assert _rows(rates.report(10))[HANDSHAKE].raised == 50
    rates.fold(10)  # compacted days keep their era counts
    assert {(e.era, e.item): e for e in rates.report(10).eras} == eras


# ── nominal rates, path activity, cap condition ─────────────────────────────────────────
def test_nominal_rates_follow_the_v5_config() -> None:
    v5 = nominal_rates(V5)
    assert v5[dimension_item("calls_last_hour")] == pytest.approx(ALPHA / 21)
    assert v5[dimension_item("read_volume")] == pytest.approx(ALPHA / 21)
    assert v5[dimension_item("asset")] == pytest.approx(ALPHA / 12)
    assert v5[dimension_item("burst")] == pytest.approx(ALPHA / 12)
    assert v5[dimension_item("protocol_skip")] == 0.0  # watch-only: never alerts alone
    assert v5[OVERSIZED] == 0.005 and v5[flag_item("sequence")] is None
    assert v5[FIRST_ACCESS] == 0.003 and v5[floor_item(COPY_FLOOR)] == 0.0005
    assert v5[WATCH] is None
    settings = RateSettings.from_config(V5)
    assert settings.alert_floors == {FIRST_ACCESS_FLOOR: 0.003, COPY_FLOOR: 0.0005}
    assert settings.alpha == ALPHA and dict(settings.nominal) == v5
    v4 = RateSettings.from_config(BehaviourConfig())
    assert set(v4.nominal) == {
        flag_item(f) for f in ("burst", "many_assets", "request_too_big")
    } | {
        flag_item("sequence"),
        HANDSHAKE,
    }
    assert v4.alert_floors == {} and v4.shares == {} and v4.alpha is None


def test_nominal_rates_without_read_volume() -> None:
    """D1 off: Cadence's third splits six ways and Read volume has no item."""
    nominal = nominal_rates(replace_config(V5, reply_volume=False))
    assert dimension_item("read_volume") not in nominal
    assert nominal[dimension_item("calls_last_hour")] == pytest.approx(ALPHA / 18)
    assert nominal[dimension_item("asset")] == pytest.approx(ALPHA / 12)


def test_footprint_watch_only_under_d3_b() -> None:
    config = replace_config(V5, footprint_alerts=False)
    nominal = nominal_rates(config)
    assert all(nominal[dimension_item(d)] == 0.0 for d in FOOTPRINT)
    rates = FlagRates.from_config(config)
    report = rates.fold(10, agent_days=dict.fromkeys(FOOTPRINT, 5_000))
    paths = {p.dimension for p in report.paths}
    assert not paths & set(FOOTPRINT) and "calls_last_hour" in paths


def test_a_group_switched_off_is_watch_only() -> None:
    """The engine accepts a share of 0, which calibration.combine reads as watch-only."""
    config = replace_config(V5, budget_shares=(0.5, 0.0, 0.5))
    settings = RateSettings.from_config(config)
    assert all(settings.shares[d] is None for d in FOOTPRINT)
    assert all(settings.nominal[dimension_item(d)] == 0.0 for d in FOOTPRINT)
    assert settings.shares["burst"] == pytest.approx(0.5 / 4)  # Missing handshake: watch-only
    report = FlagRates(settings).fold(10, agent_days=dict.fromkeys(FOOTPRINT, 5_000))
    assert not {p.dimension for p in report.paths} & set(FOOTPRINT)
    assert not set(report.broken_caps) & set(FOOTPRINT)
    assert path_activity({"d": 9}, {"d": 0.0}, ALPHA) == ()


def test_a_watch_only_dimension_is_within_until_it_alerts_alone() -> None:
    rates = FlagRates.from_config(V5)
    for day in range(WINDOW):
        for i in range(150):
            rates.add(day, f"c{i}", ())
    item = dimension_item("protocol_skip")
    assert _rows(rates.report(WINDOW))[item].status == WITHIN
    rates.add(WINDOW - 1, "c0", (item,))
    assert _rows(rates.report(WINDOW))[item].status == OVER


@pytest.mark.parametrize(
    ("share", "alpha", "needed"),
    [  # spec 2.3's table: N_d + 1 needed at each line
        (1 / 18, 0.01, 1_800),
        (1 / 12, 0.01, 1_200),
        (1 / 21, 0.01, 2_100),
        (1 / 18, 0.025, 720),
        (1 / 12, 0.025, 480),
        (1 / 18, 0.0943, 191),
        (1 / 12, 0.0943, 128),
        ((1 / 3) / 4, 0.03, 400),  # 1 / (w alpha) is 400.00000000000006 in floats
    ],
)
def test_path_activity_lines(share: float, alpha: float, needed: int) -> None:
    (low,) = path_activity({"d": needed - 2}, {"d": share}, alpha)
    (high,) = path_activity({"d": needed - 1}, {"d": share}, alpha)
    assert low.needed == high.needed == needed
    assert not low.active and high.active


def test_path_report_on_a_v5_route() -> None:
    rates = FlagRates.from_config(V5)
    report = rates.fold(10, agent_days={"read_volume": 2_099, "asset": 1_198})
    paths = {p.dimension: p for p in report.paths}
    assert "protocol_skip" not in paths  # watch-only: no path
    assert paths["read_volume"].active and not paths["asset"].active
    assert paths["asset"].message == ("asset: path inactive at the 1% line (N_d + 1 = 1199 < 1200)")
    assert not paths["calls_last_hour"].active  # missing: N_d = 0
    assert all(p.cap_holds for p in report.paths)
    assert {p.dimension for p in report.inactive_paths} >= {"asset", "calls_last_hour"}
    assert rates.report(10).paths == ()  # no N_d given: no path report
    assert rates.report(10).broken_caps == ()


def test_cap_condition_breaks_at_the_spec_line() -> None:
    assert cap_condition_holds(1 / 12, 0.01)
    assert cap_condition_holds(1 / 12, 0.133)
    assert not cap_condition_holds(1 / 12, 12 / 90)  # (A_d + 1) w alpha = 1: can reach
    assert not cap_condition_holds(1 / 12, 0.01, history_days=1_200)
    for share, alpha in ((1 / 12, 0.01), (1 / 12, 12 / 90), (1 / 21, 0.2)):
        assert cap_condition_holds(share, alpha) == calibration.cap_condition(share, alpha)


@pytest.mark.parametrize("alpha", [0.005, 0.01, 0.025, 0.03, 0.05, 0.0943, 0.12, 12 / 90])
def test_path_activity_and_cap_agree_with_calibration(alpha: float) -> None:
    """RF5 reports the paths and caps that calibration.py's reference acts on."""
    for share in (1 / 21, 1 / 18, 1 / 12, 1 / 24, 1 / 6):
        (edge,) = path_activity({"d": 0}, {"d": share}, alpha)
        for n in range(max(0, edge.needed - 3), edge.needed + 2):
            (path,) = path_activity({"d": n}, {"d": share}, alpha)
            assert path.active == calibration.path_active(n, share, alpha), (share, n)
        assert cap_condition_holds(share, alpha) == calibration.cap_condition(share, alpha)


def test_the_cap_condition_follows_the_configs_history() -> None:
    """A longer history (W6, the EV-21 sweep) breaks the cap condition at a lower line: at 8%,
    180 days x 1/12 x 8% = 1.2 reaches it, 90 days (0.6) and Cadence's 1/21 (0.69) do not."""
    alpha = 0.08
    longer = RateSettings.from_config(replace_config(V5, history_days=180, alert_alpha=alpha))
    usual = RateSettings.from_config(replace_config(V5, alert_alpha=alpha))
    assert (longer.history_days, usual.history_days) == (180, 90)
    alerting_twelfths = {*FOOTPRINT, "burst", "many_assets", "request_too_big", "sequence"}
    assert set(FlagRates(longer).report(1).broken_caps) == alerting_twelfths
    assert FlagRates(usual).report(1).broken_caps == ()


def test_a_broken_cap_condition_is_reported_without_n_d() -> None:
    settings = RateSettings(shares={"tool": 1 / 12, "calls": 1 / 21, "skip": None}, alpha=0.14)
    report = FlagRates(settings).report(1)
    assert report.broken_caps == ("tool",)  # 90 x 1/21 x 0.14 = 0.6 < 1 still holds
    assert "tool: cap condition broken" in format_report(report)
    assert "calls" not in format_report(report)
    assert json.loads(json.dumps(report.to_json()))["broken_caps"] == ["tool"]


# ── snapshot ────────────────────────────────────────────────────────────────────────────
def _stream(rates: FlagRates, days: range, seed: int) -> None:
    rng = random.Random(seed)
    items = (OVERSIZED, HANDSHAKE, FIRST_ACCESS, dimension_item("tool"), flag_item("burst"))
    for day in days:
        for _ in range(rng.randrange(40, 80)):
            raised = tuple(i for i in items if rng.random() < 0.06)
            caller = f"c{rng.randrange(60)}"
            era = rng.choice(("legacy", "modern", None))
            rates.add(day, caller, raised, established=caller < "c4", era=era)


def test_a_snapshot_round_trips_through_json() -> None:
    live = FlagRates.from_config(V5)
    _stream(live, range(35), seed=3)
    live.fold(35, agent_days={"tool": 500})
    restored = FlagRates.from_json(json.loads(json.dumps(live.to_json(), sort_keys=True)))
    assert restored.to_json() == live.to_json()
    assert restored.settings == live.settings
    for rates in (live, restored):
        _stream(rates, range(35, 50), seed=5)
    assert restored.to_json() == live.to_json()
    for day in (50, 51):
        assert restored.fold(day, {"tool": 900}) == live.fold(day, {"tool": 900})
    report = live.report(52, {"tool": 900})
    assert json.loads(json.dumps(report.to_json()))["day"] == 52
    with pytest.raises(ValueError):
        FlagRates.from_json({"schema": "flag-rates/0"})


def test_a_mid_day_snapshot_keeps_the_days_callers() -> None:
    rates = _floor_rates()
    rates.add(0, "a", (FIRST_ACCESS,), established=True)
    restored = FlagRates.from_json(json.loads(json.dumps(rates.to_json())))
    for r in (rates, restored):
        r.add(0, "a", (FIRST_ACCESS,))  # the same agent-day: counts once after a restore too
    assert restored.report(1) == rates.report(1)
    assert _rows(restored.report(1))[FIRST_ACCESS].raised == 1
