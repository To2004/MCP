"""Design v1 of the behaviour multiplier, kept runnable: ordinary stays at or below x1, strong
things flare, nothing leaves [0.7, 5]. The cases are v1's stress-tested edge cases
(DIMENSION_FORMULAS_v1.md); v2 and v3 are in test_engine_designs.py."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone

import pytest

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message, multiplier
from mcp_security.behaviour.engine import (
    ASSET,
    NEW_CLIENT,
    NEW_NETWORK,
    PROTOCOL_SKIP,
    REQUEST_TOO_BIG,
    SEQUENCE,
    SESSION_LENGTH,
    TIME_OF_DAY,
    TOOL,
)

DAY = 86_400.0
MONDAY = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()  # a Monday, 00:00 UTC
ORDINARY = 1.0 + 1e-9
V1 = BehaviourConfig(design="v1")


def session(
    t0,
    sid,
    agent="a",
    tools=("read", "list", "search"),
    n=10,
    gap=30.0,
    init=True,
    assets=5,
    address="10.0.0.1",
    client="claude-desktop/1.0",
    size=200,
    **kw,
):
    """One session: initialize, then n tool calls gap seconds apart."""
    out = (
        [Message(t0 - 1, agent, "initialize", sid, address=address, client=client)] if init else []
    )
    for i in range(n):
        out.append(
            Message(
                t0 + i * gap,
                agent,
                "tools/call",
                sid,
                tool=tools[i % len(tools)],
                asset=f"repo{i % assets}" if assets else None,
                sensitivity=2,
                operation="read",
                address=address,
                client=client,
                size=size,
                **kw,
            )
        )
    return out


def workday(day, agent="a", sessions=4, start_h=9.0, hours=8.0, one_session=False, **kw):
    """Short sessions spread over the working hours of ``day`` (days after MONDAY)."""
    t0 = MONDAY + day * DAY
    if one_session:
        return session(
            t0 + start_h * 3600,
            f"{agent}-{day}",
            agent,
            n=sessions * 10,
            gap=hours * 3600 / (sessions * 10),
            **kw,
        )
    return [
        m
        for k in range(sessions)
        for m in session(
            t0 + (start_h + k * hours / sessions) * 3600, f"{agent}-{day}-{k}", agent, **kw
        )
    ]


def history(days=60, **kw):
    return [m for d in range(days) if d % 7 < 5 for m in workday(d, **kw)]


def run(warm, test, config=V1):
    engine = BehaviourEngine(config)
    for m in warm:
        engine.observe(m)
    return [engine.observe(m) for m in test]


def peak(verdicts):
    return max(verdicts, key=lambda v: v.multiplier)


BASE = history()
TEST_DAY = 63  # a Monday, after 9 weeks of history


def at(hours: float) -> float:
    return MONDAY + TEST_DAY * DAY + hours * 3600


def test_the_curve_is_one_at_the_edge_of_ordinary_and_stays_in_bounds() -> None:
    assert multiplier(0.5) == 1.0
    assert multiplier(0.0) == pytest.approx(0.7)
    assert multiplier(1.0) == pytest.approx(5.0)
    assert multiplier(0.9) == pytest.approx(3.62, abs=0.01)
    assert all(0.7 <= multiplier(s / 100) <= 5.0 for s in range(101))


def test_warm_up_leaves_a_new_agent_at_one() -> None:
    verdicts = run([], workday(0, sessions=1))
    tool_calls = [v for v in verdicts if v.scores or v.learning]
    assert all(v.multiplier == 1.0 for v in verdicts[:6])
    assert tool_calls[0].learning


@pytest.mark.parametrize(
    "name,warm,test",
    [
        ("ordinary day", BASE, workday(TEST_DAY)),
        ("night-shift worker", history(start_h=22), workday(TEST_DAY, start_h=22)),
        (
            "desktop client: one session all day",
            history(one_session=True),
            workday(TEST_DAY, one_session=True),
        ),
        (
            "new address in the same /16 on every call",
            [
                m.__class__(**{**m.__dict__, "address": f"100.64.{i % 256}.{i % 250 + 1}"})
                for i, m in enumerate(BASE)
            ],
            [
                m.__class__(
                    **{**m.__dict__, "address": f"100.64.{(i * 7) % 256}.{(i * 3) % 250 + 1}"}
                )
                for i, m in enumerate(workday(TEST_DAY))
            ],
        ),
        ("a client upgrade (same family)", BASE, workday(TEST_DAY, client="claude-desktop/2.0")),
        ("requests always 0 bytes", history(size=0), workday(TEST_DAY, size=0)),
        ("0 bytes, then one of 50 bytes", history(size=0), session(at(10), "s", size=50, n=1)),
        (
            "agent using 26 tools evenly",
            history(tools=tuple(f"t{i}" for i in range(26))),
            workday(TEST_DAY, tools=tuple(f"t{i}" for i in range(26))),
        ),
        (
            "stateless client that never initializes",
            history(init=False),
            workday(TEST_DAY, init=False),
        ),
    ],
)
def test_ordinary_does_not_flare(name, warm, test) -> None:
    worst = peak(run(warm, test))
    assert worst.multiplier <= ORDINARY, (name, worst)


@pytest.mark.parametrize(
    "name,test,dimension,low,high",
    [
        ("first-time tool", session(at(10), "s", tools=("delete_repo",), n=1), TOOL, 3.0, 3.7),
        ("new /16 network", workday(TEST_DAY, address="203.0.113.5"), NEW_NETWORK, 3.6, 3.7),
        ("new client program", workday(TEST_DAY, client="python-httpx/0.27"), NEW_CLIENT, 3.6, 3.7),
        (
            "a never-touched asset",
            [
                Message(
                    at(10),
                    "a",
                    "tools/call",
                    "s1",
                    tool="read",
                    asset="new-repo",
                    sensitivity=2,
                    operation="read",
                    address="10.0.0.1",
                    client="claude-desktop/1.0",
                )
            ],
            ASSET,
            4.0,
            5.0,
        ),
        ("a 20 KB request", session(at(10), "s", n=1, size=20_000), REQUEST_TOO_BIG, 3.6, 3.7),
        ("a call at 3 am", session(at(3), "s", n=2), TIME_OF_DAY, 4.0, 5.0),
        (
            "a stuck session (usually minutes, open 3 hours)",
            session(at(9), "s", n=40, gap=270),
            SESSION_LENGTH,
            3.0,
            5.0,
        ),
        (
            "tool call without initialize",
            session(at(10), "s", n=3, init=False),
            PROTOCOL_SKIP,
            1.8,
            2.0,
        ),
    ],
)
def test_strong_signals_flare(name, test, dimension, low, high) -> None:
    worst = peak(run(BASE, test))
    assert low <= worst.multiplier <= high, (name, worst)
    assert worst.strongest == dimension, (name, worst)


def test_a_write_to_a_sensitive_asset_never_read_is_a_problematic_sequence() -> None:
    write = Message(
        at(11),
        "a",
        "tools/call",
        "s1",
        tool="update",
        asset="secrets",
        sensitivity=5,
        operation="write",
        address="10.0.0.1",
        client="claude-desktop/1.0",
    )
    verdict = run(
        BASE,
        [
            Message(
                at(11) - 1, "a", "initialize", "s1", address="10.0.0.1", client="claude-desktop/1.0"
            ),
            write,
        ],
    )[-1]
    assert SEQUENCE in verdict.scores and verdict.multiplier >= 3.6


def test_a_tool_that_needs_a_step_before_it_flares_without_that_step() -> None:
    config = BehaviourConfig(design="v1", requires_before={"merge": frozenset({"review"})})
    reviewed = session(at(10), "s1", tools=("review", "merge"), n=2)
    unreviewed = session(at(11), "s2", tools=("merge",), n=1)
    assert SEQUENCE not in run(BASE + reviewed[:-1], reviewed[-1:], config)[-1].scores
    assert SEQUENCE in run(BASE + reviewed, unreviewed, config)[-1].scores


def test_travel_flares_on_the_first_day_and_settles_within_the_week() -> None:
    travel = [m for d in range(TEST_DAY, TEST_DAY + 5) for m in workday(d, start_h=1)]
    per_day = len(travel) // 5
    first = peak(run(BASE, travel[:per_day]))
    fifth = peak(run(BASE + travel[:-per_day], travel[-per_day:]))
    assert first.multiplier > 4.0 and first.strongest == TIME_OF_DAY
    assert fifth.multiplier <= 1.1


def test_a_huge_request_approaches_five_but_never_passes_it() -> None:
    worst = peak(run(BASE, session(at(10), "s", n=1, size=10**9)))
    assert 4.9 <= worst.multiplier <= 5.0


def test_any_stream_stays_between_point_seven_and_five() -> None:
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
    verdicts = run([], stream)
    assert all(0.7 <= v.multiplier <= 5.0 for v in verdicts)


def test_a_restored_engine_continues_exactly_where_the_saved_one_stopped() -> None:
    first, rest = BASE[: len(BASE) // 2], BASE[len(BASE) // 2 :] + workday(TEST_DAY)
    straight = run(first, rest)
    saved = BehaviourEngine(V1)
    for m in first:
        saved.observe(m)
    restored = BehaviourEngine(V1)
    restored.restore(json.loads(json.dumps(saved.snapshot())))
    # open sessions are not saved; the continuation starts new sessions on new days anyway
    resumed = [restored.observe(m) for m in rest]
    assert [round(v.multiplier, 9) for v in resumed] == [round(v.multiplier, 9) for v in straight]
