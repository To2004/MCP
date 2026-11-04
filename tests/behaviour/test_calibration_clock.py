"""v5 calibration: the route clock (CAL-7) and what it prices.

Exact ``RouteClock.price`` values (the record min, A_d, the value path, the Oversized surge,
``record_rank`` off), one reference version per agent-day, filing and ready days, the
gateway-wide reference (GWR), snapshots, and the cost guards (DEP-7's value cap, the rollover
rebuild). Every number here is from synthetic traffic, never a paper number.
"""

from __future__ import annotations

import json
import random
import time
from collections import Counter

import pytest

from mcp_security.behaviour.calibration import (
    GATEWAY,
    KEPT_VERSIONS,
    OVERFLOW,
    PROTOCOL_SKIP,
    REQUEST_TOO_BIG,
    AgentDay,
    CalibrationSettings,
    CallMeasures,
    Commonness,
    DayRings,
    GatewayReference,
    Priced,
    RecordReference,
    ReferenceEntry,
    RouteClock,
)

DAY, HOUR = 86_400.0, 3_600.0
PAST = 89  # the window's past days, [t-89, t-1]
CALLS, TOOL, BURST = "calls_last_hour", "tool", "burst"
LOS_ANGELES, TOKYO, AUCKLAND = "America/Los_Angeles", "Asia/Tokyo", "Pacific/Auckland"
UTC_MIDNIGHT = CalibrationSettings(route_zone="UTC", day_start_hour=0.0, route_warmup_days=None)
UTC_FOUR = CalibrationSettings(route_zone="UTC", day_start_hour=4.0, route_warmup_days=None)
GW = CalibrationSettings(
    reference_scope=GATEWAY, route_zone="UTC", day_start_hour=0.0, route_warmup_days=None
)
FLOOD_CAP = 4_096  # DEP-7's max_values_per_kind
FLOOD_SECONDS = 0.05  # a generous bound on one call's value pricing (it was ~0.2-0.3 s)


def day_ts(day: int, hour: float = 12.0) -> float:
    """A UTC timestamp on ``day`` at ``hour``."""
    return day * DAY + hour * HOUR


def took(*dims: str) -> CallMeasures:
    """A call on which ``dims`` took part without being raised."""
    return CallMeasures(took_part=frozenset(dims))


# ── exact prices ────────────────────────────────────────────────────────────────────────────
def call_rate_history(settings: CalibrationSettings = UTC_MIDNIGHT) -> RouteClock:
    """Days 0-4, priced on day 5. Ann is active every day, but Call rate takes part only on
    days 3 and 4 (maxima 4 and 5): A = 5, A_d = 2. Bea takes part every day and sets a Call
    rate record of strength 10 on days 0-2. So N_d = 7 and three ranked days at 10."""
    clock = RouteClock(settings)
    for day in range(5):
        clock.advance(day_ts(day))
        ann = CallMeasures(amounts={CALLS: 1.0 + day}) if day >= 3 else took(BURST)
        clock.commit("ann", day_ts(day), None, ann, Priced({}))
        bea = Priced({}, (CALLS,), {CALLS: 10.0}) if day < 3 else Priced({})
        clock.commit("bea", day_ts(day), None, CallMeasures(amounts={CALLS: 2.0}), bea)
    clock.advance(day_ts(5))
    return clock


def test_an_amount_record_is_priced_min_of_one_over_a_d_plus_one_and_its_rank() -> None:
    clock = call_rate_history()
    assert clock.reference.n(CALLS) == 7 and clock.reference.ranked_days(CALLS) == 3
    rings = clock.rings("ann", 5)
    assert (rings.active_days(5), rings.active_days(5, CALLS)) == (5, 2)
    weak = clock.price("ann", day_ts(5), None, CallMeasures({CALLS: 9.0}, strengths={CALLS: 4.0}))
    assert weak.commonness[CALLS] == Commonness(0, 2)
    assert (weak.records, weak.ranked, weak.surged) == ((CALLS,), {CALLS: 4.0}, ())
    assert weak.rates[CALLS] == 1 / 3  # min(1/(2 + 1), (1 + 3)/(7 + 1)): the personal part
    strong = clock.price(
        "ann", day_ts(5), None, CallMeasures({CALLS: 9.0}, strengths={CALLS: 11.0})
    )
    assert strong.rates[CALLS] == 1 / 8  # min(1/3, (1 + 0)/(7 + 1)): the rank
    usual = clock.price("ann", day_ts(5), None, CallMeasures({CALLS: 4.5}, strengths={CALLS: 11.0}))
    assert usual.rates[CALLS] == 2 / 3 and usual.records == () and usual.ranked == {}


def test_with_record_rank_off_a_record_keeps_its_personal_price() -> None:
    clock = call_rate_history(
        CalibrationSettings(
            route_zone="UTC", day_start_hour=0.0, route_warmup_days=None, record_rank=False
        )
    )
    off = clock.price("ann", day_ts(5), None, CallMeasures({CALLS: 9.0}, strengths={CALLS: 11.0}))
    assert off.rates[CALLS] == 1 / 3 and off.records == (CALLS,)
    assert off.ranked == {CALLS: 11.0}  # still filed for the reference


def test_a_never_used_value_is_a_record_ranked_by_its_strength() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    for day in range(4):
        clock.advance(day_ts(day))
        clock.commit("ann", day_ts(day), None, CallMeasures(values={TOOL: ("read",)}), Priced({}))
        cy = Priced({}, (TOOL,), {TOOL: 0.5 / (1 + day)}) if day < 2 else Priced({})
        clock.commit("cy", day_ts(day), None, CallMeasures(values={TOOL: ("search",)}), cy)
        dan = ("read", "rare") if day == 1 else ("read",)  # one day with a one-off value
        clock.commit("dan", day_ts(day), None, CallMeasures(values={TOOL: dan}), Priced({}))
    clock.advance(day_ts(4))
    assert clock.reference.n(TOOL) == 12 and clock.reference.ranked_days(TOOL) == 2

    def tool(caller: str, value: str, strength: float) -> Priced:
        m = CallMeasures(values={TOOL: (value,)}, strengths={TOOL: strength})
        return clock.price(caller, day_ts(4), None, m)

    new = tool("ann", "deploy", 1.0)  # ann used 'read' on all four days: no one-off day
    assert new.commonness[TOOL] == Commonness(0, 4) and new.records == (TOOL,)
    assert new.ranked == {TOOL: 1.0} and new.rates[TOOL] == 1 / 13  # min(1/5, 1/(12 + 1))
    assert tool("ann", "deploy", 0.5).rates[TOOL] == 2 / 13  # cy's 0.5 ties: "at least"
    assert tool("ann", "deploy", 0.1).rates[TOOL] == 1 / 5  # 3/13 is above 1/(A_d + 1)
    usual = tool("ann", "read", 0.1)
    assert usual.rates[TOOL] == 1.0 and usual.records == ()
    one_off = tool("dan", "deploy", 1.0)  # dan's day 1 held a value used on no other day
    assert one_off.commonness[TOOL] == Commonness(1, 4) and one_off.records == ()
    assert one_off.rates[TOOL] == 2 / 5


def test_an_oversized_request_is_surge_priced_and_a_missing_handshake_never_is() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    clock.advance(day_ts(0))
    for c in range(10):  # day 0: ten agent-days took part; two raised both flags (1 and 2)
        org = {REQUEST_TOO_BIG: float(c), PROTOCOL_SKIP: float(c)} if c in (1, 2) else {}
        m = CallMeasures(org_flags=org, took_part=frozenset({REQUEST_TOO_BIG, PROTOCOL_SKIP}))
        clock.commit(f"o{c}", day_ts(0), None, m, clock.price(f"o{c}", day_ts(0), None, m))
    clock.advance(day_ts(1))
    for c in range(4):  # day 1: four callers raise both at strength 8 before "me"
        m = CallMeasures(org_flags={REQUEST_TOO_BIG: 8.0, PROTOCOL_SKIP: 8.0})
        clock.commit(f"s{c}", day_ts(1), None, m, clock.price(f"s{c}", day_ts(1), None, m))
    m = CallMeasures(org_flags={REQUEST_TOO_BIG: 3.0, PROTOCOL_SKIP: 3.0})
    me = clock.price("me", day_ts(1), None, m)
    # window rank (1 + 0)/(10 + 1); today 4 + me = 5 ranked agent-days reach surge_min, and
    # today's rank is (1 + 4 stronger)/(4 + me + 1)
    assert me.rates == {REQUEST_TOO_BIG: 5 / 6, PROTOCOL_SKIP: 1 / 11}
    assert me.surged == (REQUEST_TOO_BIG,) and me.records == ()
    assert me.ranked == {REQUEST_TOO_BIG: 3.0, PROTOCOL_SKIP: 3.0}


# ── one reference version per agent-day ────────────────────────────────────────────────────
def test_an_agent_day_is_priced_against_one_reference_version_all_day() -> None:
    clock = RouteClock(UTC_FOUR)
    clock.advance(day_ts(9, 5))
    for c in range(20):  # twenty UTC agent-days on day 9, one with a weak Burst record
        record = Priced({}, (BURST,), {BURST: 1.0}) if c == 0 else Priced({})
        clock.commit(f"u{c}", day_ts(9, 6), None, took(BURST), record)
    m = CallMeasures(flags={BURST: "k"}, strengths={BURST: 5.0}, habit=False)
    clock.advance(day_ts(10, 2))  # 02:00 UTC: still route day 9
    before = clock.price("lou", day_ts(10, 2), LOS_ANGELES, m)
    clock.advance(day_ts(10, 5))  # the route rolled over at 04:00 UTC
    after = clock.price("lou", day_ts(10, 5), LOS_ANGELES, m)
    assert clock.caller_day(day_ts(10, 2), LOS_ANGELES) == 9
    assert clock.caller_day(day_ts(10, 5), LOS_ANGELES) == 9
    assert before.reference_day == after.reference_day == 9  # his day began 12:00 UTC, day 9
    assert before.rates == after.rates == {BURST: 1.0}
    una = clock.price("una", day_ts(10, 5), None, m)  # a UTC day 10 began at the rollover
    assert una.reference_day == 10 and una.rates == {BURST: 1 / 21}
    clock.advance(day_ts(10, 13))  # 05:00 in Los Angeles: his day 10 began at 12:00 UTC
    assert clock.price("lou", day_ts(10, 13), LOS_ANGELES, m).reference_day == 10
    clock.advance(day_ts(10, 20))  # 05:00 in Tokyo on her day 11, which began 19:00 UTC
    kei = clock.price("kei", day_ts(10, 20), TOKYO, m)
    clock.advance(day_ts(11, 5))  # the route rolled over again; her day 11 goes on
    assert kei.reference_day == 10
    assert clock.price("kei", day_ts(11, 5), TOKYO, m).rates == kei.rates
    assert clock.price("kei", day_ts(11, 5), TOKYO, m).reference_day == 10
    assert sorted(clock.reference.versions) == [9, 10, 11]


def test_every_call_of_an_agent_day_names_the_same_reference_version() -> None:
    rng = random.Random(31)
    clock = RouteClock(UTC_FOUR)
    zones = (None, TOKYO, LOS_ANGELES, AUCKLAND, "Asia/Kolkata", "America/St_Johns")
    seen: dict[tuple[str, int], set[int]] = {}
    for ts in sorted(rng.uniform(0, 40 * DAY) for _ in range(3000)):
        caller = f"c{rng.randrange(12)}"
        zone_name = zones[int(caller[1:]) % len(zones)]
        clock.advance(ts)
        m = CallMeasures(amounts={CALLS: rng.random()}, strengths={CALLS: rng.random()})
        priced = clock.price(caller, ts, zone_name, m)
        clock.commit(caller, ts, zone_name, m, priced)
        seen.setdefault((caller, clock.caller_day(ts, zone_name)), set()).add(priced.reference_day)
    assert all(len(days) == 1 for days in seen.values())
    assert len(clock.reference.versions) == KEPT_VERSIONS


def test_an_agent_day_is_filed_under_its_local_day_and_ready_after_it_ends() -> None:
    clock = RouteClock(UTC_FOUR)
    clock.advance(day_ts(10, 5))
    for caller, zone_name in (("una", None), ("kei", TOKYO), ("lou", LOS_ANGELES)):
        clock.commit(caller, day_ts(10, 6), zone_name, took(BURST), Priced({}))
    clock.advance(day_ts(13, 5))
    filed = {
        key.split("\x1f")[1]: bucket
        for bucket, keys in clock.reference.buckets.items()
        for key in keys
    }
    # una's day 10 ends at 04:00 UTC on day 11; kei's (Tokyo) at 19:00 UTC on day 10; lou's
    # day 9 (Los Angeles, 22:00 local) at 12:00 UTC on day 10: each is ready at rollover 11
    assert filed == {"una": (10, 11), "kei": (10, 11), "lou": (9, 11)}
    assert sorted(clock.reference.versions) == [11, 12, 13]  # built at the jump from day 10


def test_a_late_call_reaches_the_callers_rings_but_not_a_filed_agent_day() -> None:
    clock = RouteClock(UTC_MIDNIGHT)
    clock.advance(day_ts(3))
    first = Priced({}, (CALLS,), {CALLS: 1.0})
    clock.commit("ann", day_ts(3), None, CallMeasures(amounts={CALLS: 1.0}), first)
    clock.advance(day_ts(4))  # day 3 is filed
    late = Priced({}, (CALLS,), {CALLS: 7.0})
    clock.commit("ann", day_ts(3, 23), None, CallMeasures(amounts={CALLS: 7.0}), late)
    clock.advance(day_ts(5))
    assert clock.reference.ranked_days(CALLS) == 1
    assert clock.reference.count_at_least(CALLS, 7.0) == 0  # versions never change
    assert clock.rings("ann", 5).amount(CALLS, 7.0, 5).earlier == 1  # his day 3 maximum is 7


# ── GWR: one reference for several routes ──────────────────────────────────────────────────
def gwr_prices(first: str, second: str) -> tuple[list, dict]:
    """Two routes on one gateway reference; the routes advance past day 4 in the given order
    and github prices one call after each advance."""
    gateway = GatewayReference(GW)
    clocks = {r: RouteClock(GW, route=r, gateway=gateway) for r in ("github", "slack")}
    for clock in clocks.values():
        clock.advance(day_ts(3, 1))
    for i in range(10):
        clocks["slack"].commit(f"s{i}", day_ts(3, 2), None, took(BURST), Priced({}))
    record = Priced({}, (BURST,), {BURST: 1.0})
    clocks["github"].commit("g0", day_ts(3, 2), None, took(BURST), record)
    m = CallMeasures(flags={BURST: "x"}, strengths={BURST: 3.0}, habit=False)
    clocks[first].advance(day_ts(4, 1))
    clocks["github"].advance(day_ts(4, 1))
    prices = [clocks["github"].price("g1", day_ts(4, 1), None, m).rates]
    clocks[second].advance(day_ts(4, 2))
    prices.append(clocks["github"].price("g1", day_ts(4, 2), None, m).rates)
    return prices, gateway.reference.digests()


def test_gwr_prices_do_not_depend_on_which_route_advances_first() -> None:
    github_first, slack_first = gwr_prices("github", "slack"), gwr_prices("slack", "github")
    assert github_first == slack_first
    assert github_first[0] == [{BURST: 1 / 12}] * 2  # N = 11 agent-days over both routes


def test_gwr_members_share_the_gateways_clock_settings_and_one_surge_guard() -> None:
    gateway = GatewayReference(GW)
    RouteClock(GW, route="github", gateway=gateway)
    with pytest.raises(ValueError):
        RouteClock(GW, route="github", gateway=gateway)  # one clock per route
    berlin = CalibrationSettings(
        reference_scope=GATEWAY, route_zone="Europe/Berlin", day_start_hour=0.0
    )
    with pytest.raises(ValueError):
        RouteClock(berlin, route="slack", gateway=gateway)  # one gateway clock
    with pytest.raises(ValueError):
        GatewayReference(UTC_MIDNIGHT)
    slack = RouteClock(GW, route="slack", gateway=gateway)
    github = gateway.members["github"]
    slack.advance(day_ts(2))
    for clock in (github, slack):  # the same agent on two routes: two agent-days today
        clock.commit("ann", day_ts(2), None, took(BURST), Priced({}, (BURST,), {BURST: 2.0}))
    assert gateway.surge.ranked[BURST] == {"github\x1fann": 2.0, "slack\x1fann": 2.0}
    assert github.surge is slack.surge is gateway.surge


def test_a_gwr_gateway_and_its_members_survive_a_json_round_trip() -> None:
    gateway = GatewayReference(GW)
    clocks = {r: RouteClock(GW, route=r, gateway=gateway) for r in ("github", "slack")}
    rng = random.Random(37)
    stream = sorted(
        (rng.uniform(0, 30 * DAY), rng.choice(("github", "slack")), f"c{rng.randrange(6)}")
        for _ in range(500)
    )

    def step(routes: dict[str, RouteClock], ts: float, route: str, caller: str) -> dict:
        clock = routes[route]
        clock.advance(ts)
        m = CallMeasures(amounts={CALLS: ts % 7}, strengths={CALLS: ts % 5})
        priced = clock.price(caller, ts, None, m)
        clock.commit(caller, ts, None, m, priced)
        return dict(priced.rates)

    for event in stream[:300]:
        step(clocks, *event)
    snapshot = json.loads(
        json.dumps({"gw": gateway.to_json()} | {r: c.to_json() for r, c in clocks.items()})
    )
    back_gateway = GatewayReference.from_json(snapshot["gw"], GW)
    back = {r: RouteClock.from_json(snapshot[r], GW, route=r, gateway=back_gateway) for r in clocks}
    assert back_gateway.to_json() == gateway.to_json()
    for event in stream[300:]:
        assert step(back, *event) == step(clocks, *event)


def test_snapshots_refuse_a_reference_they_cannot_keep() -> None:
    gateway = GatewayReference(GW)
    with pytest.raises(ValueError):
        RouteClock(UTC_MIDNIGHT, gateway=gateway)  # a route-scope clock has its own reference
    member = RouteClock(GW, route="github", gateway=gateway)
    member.advance(day_ts(1))
    with pytest.raises(ValueError):
        RouteClock.from_json(member.to_json(), GW)  # no gateway: the reference would be lost
    own = RouteClock(UTC_MIDNIGHT)
    own.advance(day_ts(1))
    forged = own.to_json() | {"reference": None}
    with pytest.raises(ValueError):
        RouteClock.from_json(forged, UTC_MIDNIGHT)  # never an empty reference in silence
    with pytest.raises(ValueError):
        RouteClock.from_json(own.to_json(), GW, route="slack", gateway=gateway)
    assert set(gateway.members) == {"github"}  # a refused restore never joins


# ── cost guards ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fresh", [True, False], ids=["new-values-daily", "same-values-daily"])
def test_a_value_flood_keeps_max_values_keys_and_one_call_prices_in_milliseconds(
    fresh: bool,
) -> None:
    rings = DayRings(max_history_days=365, max_values=FLOOD_CAP)
    for day in range(100):
        used = {f"v{day}_{i}" if fresh else f"v{i}" for i in range(FLOOD_CAP)}
        rings.close_day(day, AgentDay(took={TOOL}, values={TOOL: used}))
        assert rings.stored_keys() <= FLOOD_CAP
    start = time.perf_counter()
    new = rings.value(TOOL, ("never",), 100)
    assert time.perf_counter() - start < FLOOD_SECONDS
    assert new.days == PAST
    if fresh:  # every older day held a value now folded away: a new value is common for him
        assert new == Commonness(PAST, PAST)
        assert rings.value(TOOL, ("v0_0",), 100) == new  # a forgotten value is priced as new
    else:  # each value was used on every day: a new one is a record
        assert new == Commonness(0, PAST)
        assert rings.value(TOOL, ("v0",), 100) == Commonness(PAST, PAST)


def test_a_flooding_caller_stays_bounded_through_the_clock() -> None:
    cap = 256
    clock = RouteClock(CalibrationSettings(route_zone="UTC", day_start_hour=0.0, max_values=cap))
    worst = 0.0
    for day in range(100):
        clock.advance(day_ts(day))
        m = CallMeasures(values={TOOL: tuple(f"v{day}_{i}" for i in range(3 * cap))})
        start = time.perf_counter()
        priced = clock.price("flood", day_ts(day), None, m)
        worst = max(worst, time.perf_counter() - start)
        clock.commit("flood", day_ts(day), None, m, priced)
        assert len(clock.open["flood"].days[day].values[TOOL]) == cap + 1  # and the overflow
        assert OVERFLOW in clock.open["flood"].days[day].values[TOOL]
    assert clock.callers["flood"].stored_keys() <= cap
    assert worst < FLOOD_SECONDS


def test_a_rollover_summarises_only_the_new_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    summarised: list[int] = []
    original = RecordReference._summarise

    def counting(self: RecordReference, entries) -> object:
        entries = list(entries)
        summarised.append(len(entries))
        return original(self, entries)

    monkeypatch.setattr(RecordReference, "_summarise", counting)
    ref = RecordReference()
    for day in range(150):
        for c in range(5):
            strength = {BURST: float(c)} if c < 2 else {}
            ref.add(day, f"c{c}|{day}", ReferenceEntry(f"c{c}", True, frozenset({BURST}), strength))
        before = len(summarised)
        ref.rebuild(day + 1)
        assert len(summarised) - before == 1  # one new bucket; the others' runs are reused
    assert ref.n(BURST) == 5 * PAST and ref.ranked_days(BURST) == 2 * PAST
    assert len(ref.buckets) == PAST + KEPT_VERSIONS - 1  # older buckets are forgotten
    back = RecordReference.from_json(json.loads(json.dumps(ref.to_json())), CalibrationSettings())
    assert back.digests() == ref.digests() and sorted(back.versions) == sorted(ref.versions)


# ── DayRings against a brute-force count ────────────────────────────────────────────────────
def brute(days: dict[int, AgentDay], today: int, hold: int | None) -> tuple:
    """Leave-one-out value commonness and flag habit, counted day by day (uncapped)."""
    took = [d for d in sorted(days) if today - PAST <= d < today and TOOL in days[d].took]
    counted = [
        d for d in took if hold is None or not (TOOL in days[d].records and d >= today - hold)
    ]
    counts = Counter(v for d in took for v in days[d].values.get(TOOL, ()))

    def strangeness(d: int) -> int:
        return min(0 if v == OVERFLOW else counts[v] - 1 for v in days[d].values[TOOL])

    def value(v: object) -> Commonness:
        used = 0 if v == OVERFLOW else counts.get(v, 0)
        hits = [d for d in counted if days[d].values.get(TOOL) and strangeness(d) <= used]
        return Commonness(len(hits), len(took))

    def flag(key: object) -> Commonness:
        return Commonness(sum(1 for d in counted if key in days[d].flags.get(TOOL, ())), len(took))

    return value, flag


def test_day_rings_equal_a_brute_force_count_with_late_days_and_overflow() -> None:
    rng = random.Random(43)
    pool = ["a", "b", "c", ("pair", 1), None]
    for trial in range(150):
        hold = rng.choice((None, 10))
        rings = DayRings(record_hold_days=hold)
        truth: dict[int, AgentDay] = {}
        latest = 0
        for _ in range(rng.randint(1, 60)):
            day = max(0, latest + rng.choice((1, 1, 2, 5, -3)))  # sometimes an earlier day again
            latest = max(latest, day)
            used = set(rng.sample(pool, rng.randint(1, 3))) | (
                {OVERFLOW} if rng.random() < 0.05 else set()
            )
            keys = {rng.choice(pool)} if rng.random() < 0.5 else set()
            closed = AgentDay(
                took={TOOL},
                values={TOOL: used},
                flags={TOOL: keys} if keys else {},
                records={TOOL} if rng.random() < 0.3 else set(),
            )
            rings.close_day(day, closed)
            truth.setdefault(day, AgentDay()).merge(closed)
            today = latest + rng.randint(1, 20)
            value, flag = brute(truth, today, hold)
            for probe in [*pool, "new", OVERFLOW]:
                assert rings.value(TOOL, (probe,), today) == value(probe), (trial, day, probe)
                assert rings.flag(TOOL, probe, today) == flag(probe), (trial, day, probe)
