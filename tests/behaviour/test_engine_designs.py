"""Designs v2, v3 and v4 of the behaviour multiplier (DIMENSION_FORMULAS_v2.md, _v3.md and
DIMENSION_FORMULAS.md). Design v1 keeps its own tests in test_engine.py."""

from __future__ import annotations

import json
import random
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message
from mcp_security.behaviour.engine import (
    ASSET,
    ASSETS_LAST_HOUR,
    BURST,
    CLIENT,
    MANY_ASSETS,
    NETWORK,
    NEW_CLIENT,
    NEW_NETWORK,
    NEW_TOOL,
    REQUEST_SIZE,
    REQUEST_TOO_BIG,
    SAME_CALL_10M,
    SENSITIVE_FIRST_LOOK,
    SEQUENCE,
    TIME_OF_DAY,
    TOOL,
    WRITES_LAST_HOUR,
)

DAY = 86_400.0
MONDAY = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()  # a Monday, 00:00 UTC
TEST_DAY = 63  # a Monday, after 9 weeks of history
SATURDAY = 68
ORDINARY = 1.0 + 1e-9
V2 = BehaviourConfig(design="v2")
V3 = BehaviourConfig(design="v3")
V4 = BehaviourConfig()
TOOLS = ("read", "list", "search")


def call(day, hour, agent="a", tool="read", asset="repo0", sensitivity=2, operation="read", **kw):
    """One tool call at ``hour`` o'clock on ``day`` (days after MONDAY)."""
    defaults = {
        "session": f"{agent}-{day}-{int(hour)}",
        "address": "10.0.0.1",
        "client": "claude-desktop/1.0",
        "size": 200,
    }
    return Message(
        MONDAY + day * DAY + hour * 3600,
        agent,
        "tools/call",
        tool=tool,
        asset=asset,
        sensitivity=sensitivity,
        operation=operation,
        **(defaults | kw),
    )


def session(day, hour, agent="a", n=10, gap=30.0, tools=TOOLS, assets=5, **kw):
    """``initialize``, then ``n`` calls ``gap`` seconds apart, rotating tools and assets."""
    sid = f"{agent}-{day}-{hour}"
    t0 = MONDAY + day * DAY + hour * 3600
    init = Message(
        t0 - 1, agent, "initialize", sid, address="10.0.0.1", client="claude-desktop/1.0"
    )
    calls = [
        call(
            day,
            hour + i * gap / 3600,
            agent,
            tools[i % len(tools)],
            f"repo{i % assets}",
            session=sid,
            **kw,
        )
        for i in range(n)
    ]
    return [init, *calls]


def workday(day, agent="a", start=9.0, **kw):
    return [m for k in range(4) for m in session(day, start + 2 * k, agent, **kw)]


def history(days=60, **kw):
    return [m for d in range(days) if d % 7 < 5 for m in workday(d, **kw)]


def opened(calls):
    """Each session starts with ``initialize``, as an ordinary client does."""
    out, seen = [], set()
    for m in calls:
        if m.session not in seen:
            seen.add(m.session)
            out.append(
                Message(
                    m.ts - 0.5, m.agent, "initialize", m.session, address=m.address, client=m.client
                )
            )
        out.append(m)
    return out


def run(warm, test, config=V4):
    engine = BehaviourEngine(config)
    for m in warm:
        engine.observe(m)
    return [engine.observe(m) for m in test]


def peak(verdicts):
    return max(verdicts, key=lambda v: v.multiplier)


BASE = history()


def test_v4_is_the_default_and_an_unknown_design_is_an_error() -> None:
    assert BehaviourConfig().design == "v4"
    with pytest.raises(ValueError, match="design must be one of"):
        BehaviourConfig(design="v6")


# ── v3: warm-up, learning once a day, onboarding ────────────────────────────────────────────
@pytest.mark.parametrize(
    "config,first_look", [(V3, SENSITIVE_FIRST_LOOK), (V4, ASSET)], ids=["v3", "v4"]
)
def test_the_warm_up_is_the_first_day_and_only_rules_that_need_no_past_take_part(
    config, first_look
) -> None:
    first_day = workday(0, tools=("read", "list", "search", "comment", "label"))
    payroll = call(0, 17, tool="read", asset="payroll", sensitivity=5)
    verdicts = run([], [*first_day, payroll], config)
    ordinary, look = verdicts[:-1], verdicts[-1]
    assert all(v.multiplier == 1.0 and v.learning for v in ordinary)  # no "new tool" all day
    assert look.learning and look.strongest == first_look
    assert look.multiplier == pytest.approx(3.62, abs=0.01)
    next_day = run(first_day, workday(1), config)
    assert not any(v.learning for v in next_day[5:])


def test_the_history_learns_once_a_day_so_a_new_thing_stays_new_all_day() -> None:
    q4 = [call(TEST_DAY, 10 + i / 30, asset="q4-plan", session="q4") for i in range(12)]
    first_day = [v.multiplier for v in run(BASE, q4)]
    assert min(first_day) == pytest.approx(max(first_day)) and first_day[0] > 4.0
    next_day = peak(run(BASE + q4, [call(TEST_DAY + 1, 10, asset="q4-plan")]))
    assert next_day.multiplier < 2.0
    learning_per_call = [v.multiplier for v in run(BASE, q4, V2)]
    assert learning_per_call[-1] < learning_per_call[0] - 1.0  # v2: trained within the day


def test_what_a_new_hire_explores_during_onboarding_does_not_hide_a_later_first_look() -> None:
    explore = [
        call(d, 9 + i / 4, agent="h", asset=f"repo{(3 * d + i) % 30}", session=f"h-{d}")
        for d in range(14)
        if d % 7 < 5
        for i in range(20)
    ]
    later = [m for d in range(14, 73) if d % 7 < 5 for m in workday(d, "h")]
    new_folder = opened([call(73, 11, agent="h", asset="new-folder")])
    v3 = peak(run(explore + later, new_folder, V3))
    v2 = peak(run(explore + later, new_folder, V2))
    assert v3.strongest == ASSET and v3.multiplier > 4.0
    assert v2.multiplier < 1.5  # the exploring counted as "starting new things"


# ── v3: the new counts ──────────────────────────────────────────────────────────────────────
def test_the_same_call_in_ten_minutes_flags_a_stuck_loop_under_the_burst_limit() -> None:
    loop = [
        call(TEST_DAY, 10 + i * 8 / 3600, tool="read", asset="repo1", session="loop")
        for i in range(60)
    ]  # 7.5 a minute, under the burst limit of 20
    worst = peak(run(BASE, loop, V3))
    assert worst.strongest == SAME_CALL_10M and worst.multiplier > 3.0
    assert BURST not in worst.scores


def test_writes_in_the_last_hour_count_against_his_usual() -> None:
    usual = history(tools=("read", "list", "edit"))
    cleanup = [
        call(
            TEST_DAY,
            10 + i / 60,
            tool="edit",
            asset=f"repo{i % 5}",
            operation="write",
            session="cleanup",
        )
        for i in range(40)
    ]
    worst = peak(run(usual, cleanup, V3))
    assert worst.scores[WRITES_LAST_HOUR] > 0.8


def test_distinct_assets_in_an_hour_are_a_count_with_a_learned_rule_as_backstop() -> None:
    sweep = [
        call(
            TEST_DAY, 10 + i / 120, asset=f"repo{i % 5}" if i < 10 else f"other{i}", session="sweep"
        )
        for i in range(20)
    ]
    with_limit = run(BASE, sweep, replace(V3, many_assets_per_hour=10))
    assert all(MANY_ASSETS not in v.scores for v in with_limit[:10])
    assert with_limit[-1].scores[MANY_ASSETS] == pytest.approx(0.9)
    assert with_limit[-1].scores[ASSETS_LAST_HOUR] > 0.6  # 4x his usual hour
    assert all(MANY_ASSETS not in v.scores for v in run(BASE, sweep, V3))  # no limit: off


# ── v3: policy rules ────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "sensitivity,operation,value",
    [(5, "read", 0.9), (5, "write", 0.9), (4, "read", 0.8), (4, "write", 0.8)],
)
def test_a_first_look_at_a_sensitive_asset_is_graded_by_the_asset(
    sensitivity, operation, value
) -> None:
    look = call(TEST_DAY, 11, asset="secrets", sensitivity=sensitivity, operation=operation)
    [verdict] = run(BASE, [look], V3)
    assert verdict.scores[SENSITIVE_FIRST_LOOK] == pytest.approx(value)
    if operation == "write":
        assert SEQUENCE in verdict.scores  # a first write is also a blind write


def test_a_sensitive_asset_he_already_reads_is_not_a_first_look() -> None:
    reads = [call(d, 12, asset="deploy", sensitivity=4) for d in range(0, 60, 7)]
    habit = sorted(BASE + reads, key=lambda m: m.ts)
    [verdict] = run(habit, [call(TEST_DAY, 12, asset="deploy", sensitivity=4)], V3)
    assert SENSITIVE_FIRST_LOOK not in verdict.scores


def test_request_size_is_a_rule_with_a_limit_per_tool_and_nothing_else() -> None:
    config = replace(V3, request_limit_by_tool={"comment": 5_000})
    usual = history(tools=("read", "list", "comment"))
    sizes = [("comment", 6_000, True), ("read", 6_000, False), ("read", 12_000, True)]
    for tool, size, fires in sizes:
        [verdict] = run(usual, [call(TEST_DAY, 10, tool=tool, size=size)], config)
        assert (REQUEST_TOO_BIG in verdict.scores) == fires, (tool, size)
        assert REQUEST_SIZE not in verdict.scores


def test_a_habit_rule_counts_less_the_more_often_he_breaks_it() -> None:
    def burst(day, agent):
        return [call(day, 15 + i / 3600, agent, session=f"{agent}-{day}-b") for i in range(25)]

    daily_bursts = [m for d in range(60) if d % 7 < 5 for m in workday(d, "b") + burst(d, "b")]
    first_time = peak(run(BASE, burst(TEST_DAY, "a"), V3))
    habit = peak(run(daily_bursts, burst(TEST_DAY, "b"), V3))
    assert first_time.scores[BURST] == pytest.approx(0.9)
    assert habit.scores.get(BURST, 0.0) < 0.5


def test_something_new_for_many_agents_at_once_is_an_org_wide_change() -> None:
    others = [
        m
        for agent in ("b", "c", "d")
        for m in (
            call(TEST_DAY - 1, 10, agent, tool="release"),
            call(TEST_DAY - 1, 11, agent, asset="secrets", sensitivity=5),
        )
    ]
    rollout, peek = (
        call(TEST_DAY, 10, tool="release"),
        call(TEST_DAY, 11, asset="secrets", sensitivity=5),
    )
    alone = run(BASE, [rollout, peek], V3)
    together = run(BASE + others, [rollout, peek], V3)
    assert alone[0].scores[NEW_TOOL] == pytest.approx(0.9)
    assert together[0].scores[NEW_TOOL] <= 0.5  # a release: 3 others started it this week
    assert together[1].scores[SENSITIVE_FIRST_LOOK] == pytest.approx(0.9)  # never discounted


# ── v3: time of day ─────────────────────────────────────────────────────────────────────────
def test_a_weekend_call_is_compared_with_his_weekends_blended_with_all_his_days() -> None:
    night, morning = session(SATURDAY, 2, n=5), session(SATURDAY, 10, n=5)
    v3_night, v2_night = peak(run(BASE, night, V3)), peak(run(BASE, night, V2))
    assert v3_night.strongest == TIME_OF_DAY and v3_night.multiplier > 4.0
    assert v2_night.multiplier <= ORDINARY  # v2 judged it only against his (no) weekends
    assert peak(run(BASE, morning, V3)).multiplier <= ORDINARY


# ── v4: every "new for him" check in Typical Footprint ─────────────────────────────────────
def roaming(days=60):
    """A worker on a phone: a different /16 network every day."""
    return [m for d in range(days) if d % 7 < 5 for m in workday(d, address=f"100.{d}.0.1")]


def test_v4_has_no_new_network_app_tool_or_first_look_rules() -> None:
    stream = [
        call(TEST_DAY, 10, address="203.0.113.5"),
        call(TEST_DAY, 11, client="python-httpx/0.27"),
        call(TEST_DAY, 12, tool="delete_repo"),
        call(TEST_DAY, 13, asset="payroll", sensitivity=5),
    ]
    gone = {NEW_NETWORK, NEW_CLIENT, NEW_TOOL, SENSITIVE_FIRST_LOOK}
    assert not any(gone & set(v.scores) for v in run(BASE, stream))


@pytest.mark.parametrize(
    "name,message,dimension",
    [
        ("new /16 network", call(TEST_DAY, 10, address="203.0.113.5"), NETWORK),
        ("new client app", call(TEST_DAY, 10, client="python-httpx/0.27"), CLIENT),
        ("tool not used in 90 days", call(TEST_DAY, 10, tool="delete_repo"), TOOL),
    ],
)
def test_v4_something_new_for_a_focused_agent_is_rare_in_typical_footprint(
    name, message, dimension
) -> None:
    [verdict] = run(BASE, [message])
    # never seen, and he rarely starts new things: e = 1 / (44 active days + 1)
    assert verdict.strongest == dimension, name
    assert verdict.score == pytest.approx(0.9 / (1 + 2 / 45))
    assert verdict.multiplier == pytest.approx(3.20, abs=0.01)


def test_v4_a_new_network_is_ordinary_for_someone_who_roams() -> None:
    tomorrow = workday(TEST_DAY, address="100.250.0.1")
    assert peak(run(roaming(), tomorrow)).multiplier <= ORDINARY


def test_v4_something_new_for_many_agents_at_once_is_an_org_wide_change() -> None:
    others = [
        m
        for agent in ("b", "c", "d")
        for m in (
            call(TEST_DAY - 1, 10, agent, tool="release", address="172.20.0.1"),
            call(TEST_DAY - 1, 11, agent, asset="secrets", sensitivity=5),
        )
    ]
    vpn_and_release = call(TEST_DAY, 10, tool="release", address="172.20.0.9")
    peek = call(TEST_DAY, 11, asset="secrets", sensitivity=5)
    alone = run(BASE, [vpn_and_release, peek])
    together = run(BASE + others, [vpn_and_release, peek])
    assert alone[0].scores[TOOL] > 0.85 and alone[0].scores[NETWORK] > 0.85
    assert together[0].scores[TOOL] <= 0.5 and together[0].scores[NETWORK] <= 0.5
    assert together[1].scores[ASSET] == pytest.approx(0.9)  # the first-look floor: no discount


@pytest.mark.parametrize("sensitivity,floor", [(5, 0.9), (4, 0.8), (3, None)])
def test_v4_a_first_look_at_a_sensitive_asset_is_a_floor_on_the_asset_score(
    sensitivity, floor
) -> None:
    look = call(TEST_DAY, 11, asset="secrets", sensitivity=sensitivity)
    [v4] = run(BASE, [look])
    [v3] = run(BASE, [look], V3)
    assert v4.multiplier == pytest.approx(v3.multiplier)  # the same M, now inside Footprint
    rarity = 1 / (1 + 2 / 45)  # a never-touched asset for a focused agent
    assert v4.scores[ASSET] == pytest.approx(max(rarity, floor or 0.0))


def test_v4_explorers_still_flare_on_a_first_look_at_payroll() -> None:
    explorer = [
        call(d, 9 + i / 4, asset=f"folder{(7 * d + i) % 400}", session=f"x-{d}")
        for d in range(60)
        if d % 7 < 5
        for i in range(20)
    ]
    folder, payroll = run(
        explorer,
        [
            call(TEST_DAY, 10, asset="folder-new"),
            call(TEST_DAY, 11, asset="payroll", sensitivity=5),
        ],
    )
    assert folder.multiplier < 1.5  # new folders are ordinary for him
    assert payroll.strongest == ASSET and payroll.multiplier == pytest.approx(3.62, abs=0.01)


def test_v4_network_and_app_wait_for_their_own_history_after_a_v3_snapshot() -> None:
    saved = BehaviourEngine(V3)
    for m in BASE:
        saved.observe(m)
    restored = BehaviourEngine(V4)
    restored.restore(json.loads(json.dumps(saved.snapshot())))
    first = [restored.observe(m) for m in workday(TEST_DAY)]
    assert not any({NETWORK, CLIENT} & set(v.scores) for v in first)  # no history for them yet
    assert peak(first).multiplier <= ORDINARY
    second = [restored.observe(m) for m in workday(TEST_DAY + 1)]
    assert all(NETWORK in v.scores for v in second)
    assert peak(second).multiplier <= ORDINARY


# ── v3 and v4 stay ordinary on ordinary days ────────────────────────────────────────────────
@pytest.mark.parametrize("config", [V3, V4], ids=["v3", "v4"])
@pytest.mark.parametrize(
    "name,warm,test",
    [
        ("ordinary day", BASE, workday(TEST_DAY)),
        ("night-shift worker", history(start=22.0), workday(TEST_DAY, start=22.0)),
        (
            "agent using 26 tools evenly",
            history(tools=tuple(f"t{i}" for i in range(26))),
            workday(TEST_DAY, tools=tuple(f"t{i}" for i in range(26))),
        ),
        ("requests always 0 bytes", history(size=0), workday(TEST_DAY, size=0)),
        ("a client upgrade", BASE, workday(TEST_DAY, client="claude-desktop/2.0")),
    ],
)
def test_ordinary_does_not_flare(config, name, warm, test) -> None:
    worst = peak(run(warm, test, config))
    assert worst.multiplier <= ORDINARY, (name, worst)


# ── v2 ──────────────────────────────────────────────────────────────────────────────────────
def test_v2_checks_request_size_and_new_tools_only_as_rules() -> None:
    huge = peak(run(BASE, [call(TEST_DAY, 10, size=10**9)], V2))
    first_tool = peak(run(BASE, [call(TEST_DAY, 10, tool="delete_repo")], V2))
    assert huge.strongest == REQUEST_TOO_BIG and huge.multiplier == pytest.approx(3.62, abs=0.01)
    assert first_tool.strongest == NEW_TOOL
    assert first_tool.multiplier == pytest.approx(3.62, abs=0.01)


# ── every design ────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("config", [V2, V3, V4], ids=["v2", "v3", "v4"])
def test_any_stream_stays_between_point_seven_and_five(config) -> None:
    rnd = random.Random(7)
    stream, t = [], MONDAY
    for _ in range(5_000):
        t += rnd.expovariate(1 / 120)
        stream.append(
            Message(
                t,
                rnd.choice("abc"),
                rnd.choice(["tools/call"] * 8 + ["initialize", "tools/list"]),
                f"s{rnd.randrange(50)}",
                tool=f"t{rnd.randrange(30)}",
                asset=f"x{rnd.randrange(200)}",
                sensitivity=rnd.randrange(1, 6),
                operation=rnd.choice(["read", "write"]),
                address=f"{rnd.randrange(1, 255)}.{rnd.randrange(256)}.0.1",
                client=rnd.choice(["cursor/1", "claude-desktop/2", "python-httpx/0.27"]),
                size=rnd.choice([0, 100, 5_000, 50_000, 10**8]),
            )
        )
    assert all(0.7 <= v.multiplier <= 5.0 for v in run([], stream, config))


@pytest.mark.parametrize("config", [V2, V3, V4], ids=["v2", "v3", "v4"])
def test_a_restored_engine_continues_exactly_where_the_saved_one_stopped(config) -> None:
    others = [m for d in range(30) if d % 7 < 5 for m in workday(d, "b", start=10.5)]
    stream = sorted(BASE + others, key=lambda m: m.ts)
    first, rest = stream[: len(stream) // 2], stream[len(stream) // 2 :] + workday(TEST_DAY)
    straight = run(first, rest, config)
    saved = BehaviourEngine(config)
    for m in first:
        saved.observe(m)
    restored = BehaviourEngine(config)
    restored.restore(json.loads(json.dumps(saved.snapshot())))
    resumed = [restored.observe(m) for m in rest]
    assert [round(v.multiplier, 9) for v in resumed] == [round(v.multiplier, 9) for v in straight]


@pytest.mark.parametrize("config", [V3, V4], ids=["v3", "v4"])
def test_state_saved_by_v1_loads_without_a_new_warm_up(config) -> None:
    saved = BehaviourEngine(BehaviourConfig(design="v1"))
    for m in BASE:
        saved.observe(m)
    restored = BehaviourEngine(config)
    restored.restore(json.loads(json.dumps(saved.snapshot())))
    verdicts = [restored.observe(m) for m in workday(TEST_DAY)]
    assert not any(v.learning for v in verdicts)
    assert peak(verdicts).multiplier <= ORDINARY
