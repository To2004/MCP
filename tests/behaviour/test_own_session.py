"""E4: the caller's own session, a run of his calls ended by a 30-minute idle gap."""

from __future__ import annotations

import json

import pytest

from mcp_security.behaviour import engine
from mcp_security.behaviour.own_session import (
    IDLE_GAP_S,
    MINUTE_S,
    OwnSession,
    advance,
    continues,
)

T0 = 1_780_000_000.0  # a fixed instant; only differences matter
LOOP_STEP_S = 8.0  # a stuck loop: a call every 8 seconds
LOOP_HOURS = 3


def run(times: list[float], gap: float = IDLE_GAP_S) -> list[OwnSession]:
    """The session after each call of a stream."""
    session, out = None, []
    for ts in times:
        session = advance(session, ts, gap)
        out.append(session)
    return out


def test_the_idle_gap_is_the_engines_v5_default() -> None:
    assert IDLE_GAP_S == engine.IDLE_GAP_S == 30 * MINUTE_S
    assert engine.BehaviourConfig(design="v5").idle_gap_s == IDLE_GAP_S


def test_calls_29_minutes_apart_stay_in_one_session_and_31_minutes_apart_start_a_new_one() -> None:
    together = run([T0, T0 + 29 * MINUTE_S, T0 + 58 * MINUTE_S])
    assert {s.start for s in together} == {T0}
    assert together[-1].minutes_at(T0 + 58 * MINUTE_S) == pytest.approx(58.0)
    apart = run([T0, T0 + 31 * MINUTE_S])
    assert apart[1].start == T0 + 31 * MINUTE_S
    assert apart[1].minutes_at(T0 + 31 * MINUTE_S) == 0.0


def test_a_gap_of_exactly_the_idle_gap_continues_the_session() -> None:
    first = advance(None, T0)
    assert continues(first, T0 + IDLE_GAP_S)
    assert not continues(first, T0 + IDLE_GAP_S + 1)
    assert not continues(None, T0)


def test_the_gap_is_measured_from_the_latest_call_not_the_start() -> None:
    times = [T0 + k * 20 * MINUTE_S for k in range(10)]  # 3 hours, never 30 idle minutes
    last = run(times)[-1]
    assert last.start == T0
    assert last.minutes_at(times[-1]) == pytest.approx(180.0)


def test_a_three_hour_stuck_loop_is_one_session_of_180_minutes() -> None:
    steps = int(LOOP_HOURS * 3_600 / LOOP_STEP_S)
    times = [T0 + k * LOOP_STEP_S for k in range(steps + 1)]
    last = run(times)[-1]
    assert last.start == T0
    assert last.minutes_at(times[-1]) == pytest.approx(LOOP_HOURS * 60)


def test_advance_never_changes_its_input_so_scoring_can_leave_state_alone() -> None:
    before = advance(None, T0)
    after = advance(before, T0 + 5 * MINUTE_S)
    assert before == OwnSession(T0, T0)
    assert after == OwnSession(T0, T0 + 5 * MINUTE_S)


def test_a_late_message_stays_in_the_run_and_never_moves_it_back() -> None:
    session = advance(advance(None, T0), T0 + 10 * MINUTE_S)
    late = advance(session, T0 + 4 * MINUTE_S)  # stamped before the latest call
    assert late == session
    early = advance(session, T0 - MINUTE_S)  # stamped before the run began
    assert early.start == T0 and early.minutes_at(T0 - MINUTE_S) == 0.0


def test_a_restart_keeps_the_session_and_a_long_outage_ends_it() -> None:
    session = run([T0, T0 + 10 * MINUTE_S])[-1]
    saved = json.loads(json.dumps(session.to_json()))
    restored = OwnSession.from_json(saved)
    assert restored == session
    inside = advance(restored, T0 + 25 * MINUTE_S)
    assert inside.start == T0  # a restart inside the run does not reset the duration
    outage = advance(restored, T0 + 10 * MINUTE_S + IDLE_GAP_S + 1)
    assert outage.start != T0  # down longer than G: what the server saw was a pause


def test_a_caller_saved_without_a_session_restores_to_none() -> None:
    assert OwnSession.from_json(None) is None


def test_the_gap_parameter_moves_the_boundary() -> None:
    times = [T0, T0 + 15 * MINUTE_S]
    assert run(times, gap=10 * MINUTE_S)[1].start == times[1]
    assert run(times, gap=20 * MINUTE_S)[1].start == T0


@pytest.mark.parametrize("gap", [0, -1.0, float("inf"), float("nan"), True, "1800"])
def test_a_bad_idle_gap_fails_fast(gap: object) -> None:
    with pytest.raises(ValueError, match="idle_gap_s"):
        advance(None, T0, gap)  # type: ignore[arg-type]


def test_a_non_finite_timestamp_fails_fast() -> None:
    with pytest.raises(ValueError, match="finite"):
        advance(None, float("nan"))
