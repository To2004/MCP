"""E6 and E8: Missing handshake (legacy only, watch-only) over per-caller started sessions."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from mcp_security.behaviour import engine
from mcp_security.behaviour.engine import v5_switches_off
from mcp_security.behaviour.handshake import (
    HANDSHAKE_STRENGTH,
    LEGACY_ERA,
    MAX_SESSIONS_PER_CALLER,
    NOT_STARTED_NOTE,
    SESSION_TTL_S,
    SESSIONLESS_NOTE,
    HandshakeFinding,
    HandshakeRules,
    HandshakeState,
    check,
    commit,
    is_started,
    normally_initializes,
    session_started,
)
from mcp_security.behaviour.own_session import advance

HOUR_S, DAY_S = 3_600.0, 86_400.0
T0 = 1_780_000_000.0
RULES = HandshakeRules()
MODERN = engine.MODERN_ERA
JUNK_IDS = 1_000


def call(
    state: HandshakeState,
    ts: float,
    session: str | None,
    run_start: float,
    *,
    era: str | None = LEGACY_ERA,
    warm: bool = True,
    rules: HandshakeRules = RULES,
) -> HandshakeFinding:
    """Check then commit one scored call, as the engine's observe does."""
    finding = check(state, era=era, session=session, ts=ts, warm=warm, rules=rules)
    commit(state, era=era, session=session, ts=ts, run_start=run_start, rules=rules)
    return finding


def initialized_runs(state: HandshakeState, runs: int, start: float = T0) -> float:
    """``runs`` own sessions, an hour apart, each opening with an initialized legacy session
    and one call in it; the time after the last one."""
    for k in range(runs):
        ts = start + k * HOUR_S
        session_started(state, f"sid-{k}", ts, RULES)
        call(state, ts + 1, f"sid-{k}", run_start=ts)
    return start + runs * HOUR_S


# ── settings ─────────────────────────────────────────────────────────────────────────────
def test_the_constants_are_the_engines() -> None:
    assert LEGACY_ERA == engine.LEGACY_ERA
    assert MAX_SESSIONS_PER_CALLER == engine.MAX_SESSIONS_PER_CALLER == 64
    assert SESSION_TTL_S == engine.SESSION_TTL_S == 7 * DAY_S


def test_rules_from_a_v5_config_and_from_one_with_every_switch_off() -> None:
    on = HandshakeRules.from_config(engine.BehaviourConfig(design="v5"))
    assert on == HandshakeRules(64, 7 * DAY_S, 3, True)
    off = HandshakeRules.from_config(v5_switches_off())
    assert (off.max_sessions, off.session_ttl_s, off.sessionless_counts) == (None, None, False)


@pytest.mark.parametrize(
    "bad",
    [{"max_sessions": 0}, {"max_sessions": True}, {"session_ttl_s": 0}, {"normally_after": 0}],
)
def test_bad_rules_fail_fast(bad: dict) -> None:
    with pytest.raises(ValueError):
        HandshakeRules(**bad)


# ── E6: who is raised ────────────────────────────────────────────────────────────────────
def test_a_caller_who_always_initializes_is_raised_on_a_sessionless_legacy_call() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    assert normally_initializes(state, RULES)
    finding = call(state, ts, None, run_start=ts)
    assert finding == HandshakeFinding(True, SESSIONLESS_NOTE)
    assert finding.strength == HANDSHAKE_STRENGTH


def test_resuming_a_session_that_was_never_initialized_is_raised() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    assert call(state, ts, "never-initialized", run_start=ts) == HandshakeFinding(
        True, NOT_STARTED_NOTE
    )


def test_a_call_in_a_started_session_is_not_raised() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 5)
    assert not call(state, ts, "sid-0", run_start=ts).raised


def test_the_first_three_own_sessions_never_raise() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 2)
    assert not call(state, ts, None, run_start=ts).raised  # only 2 counted before it
    assert state.seen == 3 and state.initialized == 2


def test_a_caller_on_a_stateless_legacy_server_is_never_raised() -> None:
    state = HandshakeState()
    session = None
    for k in range(20):
        session = advance(session, T0 + k * HOUR_S)
        assert not call(state, session.last_call, None, run_start=session.start).raised
    assert (state.seen, state.initialized) == (20, 0)


def test_a_caller_who_stops_initializing_stops_being_raised() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    runs = [ts + k * HOUR_S for k in range(6)]
    raised = [call(state, run, None, run_start=run).raised for run in runs]
    # raised while at least half of the counted own sessions were started (3 of 6 still is)
    assert raised == [True, True, True, True, False, False]


def test_an_own_session_counts_once_however_many_calls_it_has() -> None:
    state = HandshakeState()
    session_started(state, "sid", T0, RULES)
    for k in range(50):
        call(state, T0 + k * 10.0, "sid", run_start=T0)
    assert (state.seen, state.initialized) == (1, 1)


def test_modern_and_unknown_eras_are_never_checked_or_counted() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    before = state.to_json()
    for era in (MODERN, None):
        assert not call(state, ts, None, run_start=ts, era=era).raised
    assert state.to_json() == before


def test_a_caller_in_warm_up_is_never_raised() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    assert not call(state, ts, None, run_start=ts, warm=False).raised


def test_with_the_switch_off_sessionless_calls_neither_count_nor_raise() -> None:
    rules = replace(RULES, sessionless_counts=False)
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    assert not call(state, ts, None, run_start=ts, rules=rules).raised
    assert state.seen == 3
    assert call(state, ts + 1, "never-initialized", run_start=ts, rules=rules).raised


def test_an_empty_session_id_is_no_id() -> None:
    """'' follows the sessionless path: the sessionless note, and nothing with E6's switch
    off (a presented id would be raised as never initialized)."""
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    assert check(state, era=LEGACY_ERA, session="", ts=ts, warm=True, rules=RULES) == (
        HandshakeFinding(True, SESSIONLESS_NOTE)
    )
    off = replace(RULES, sessionless_counts=False)
    assert not call(state, ts, "", run_start=ts, rules=off).raised
    assert state.seen == 3 and not is_started(state, "", ts, RULES)


def test_check_never_changes_the_state() -> None:
    state = HandshakeState()
    ts = initialized_runs(state, 3)
    before = state.to_json()
    check(state, era=LEGACY_ERA, session=None, ts=ts, warm=True, rules=RULES)
    check(state, era=LEGACY_ERA, session="sid-0", ts=ts + 30 * DAY_S, warm=True, rules=RULES)
    assert state.to_json() == before


# ── E8: started sessions only, per-caller quota, TTL ─────────────────────────────────────
def test_junk_ids_from_one_caller_leave_another_callers_session_intact() -> None:
    """Junk ids store nothing, so they cannot evict anything. Per-caller isolation itself
    (one state per caller) is the engine's, and is tested there."""
    victim, flooder = HandshakeState(), HandshakeState()
    ts = initialized_runs(victim, 3)
    for k in range(JUNK_IDS):
        call(flooder, ts + k, f"junk-{k}", run_start=ts)
    assert len(flooder.sessions) == 0  # an id the caller merely presents leaves no state
    assert is_started(victim, "sid-0", ts + JUNK_IDS, RULES)
    assert not call(victim, ts + JUNK_IDS, "sid-0", run_start=ts + JUNK_IDS).raised


def test_an_unknown_id_leaves_no_session_behind() -> None:
    state = HandshakeState()
    initialized_runs(state, 2)
    sessions = dict(state.sessions)
    call(state, T0 + 10 * HOUR_S, "unknown", run_start=T0 + 10 * HOUR_S)
    assert dict(state.sessions) == sessions


def test_a_server_reply_without_a_session_id_stores_nothing() -> None:
    state = HandshakeState()
    session_started(state, None, T0, RULES)
    session_started(state, "", T0, RULES)
    assert not state.sessions


def test_the_quota_drops_the_least_recently_used_session_of_the_same_caller() -> None:
    state = HandshakeState()
    for k in range(MAX_SESSIONS_PER_CALLER):
        session_started(state, f"sid-{k}", T0 + k, RULES)
    call(state, T0 + 100, "sid-0", run_start=T0)  # a use moves sid-0 to the recent end
    session_started(state, "sid-new", T0 + 101, RULES)
    assert len(state.sessions) == MAX_SESSIONS_PER_CALLER
    assert "sid-0" in state.sessions and "sid-1" not in state.sessions


def test_a_session_idle_past_the_ttl_is_no_longer_started_and_is_dropped() -> None:
    state = HandshakeState()
    session_started(state, "sid", T0, RULES)
    assert is_started(state, "sid", T0 + SESSION_TTL_S, RULES)
    late = T0 + SESSION_TTL_S + 1
    assert not is_started(state, "sid", late, RULES)
    call(state, late, "sid", run_start=late)
    assert "sid" not in state.sessions


def test_an_idle_session_is_dropped_when_another_one_starts_or_is_used() -> None:
    """E8's TTL sweep runs on every update, not only on the expired session's own use."""
    state = HandshakeState()
    session_started(state, "idle", T0, RULES)
    session_started(state, "new", T0 + SESSION_TTL_S + 1, RULES)
    assert list(state.sessions) == ["new"]
    used = HandshakeState()
    session_started(used, "idle", T0, RULES)
    session_started(used, "current", T0 + SESSION_TTL_S, RULES)  # "idle" is exactly ttl old
    assert list(used.sessions) == ["idle", "current"]
    later = T0 + SESSION_TTL_S + 1
    call(used, later, "current", run_start=later)
    assert list(used.sessions) == ["current"]


def test_a_snapshot_keeps_a_session_exactly_ttl_old() -> None:
    state = HandshakeState()
    session_started(state, "sid", T0, RULES)
    assert [sid for sid, _ in state.to_json(now=T0 + SESSION_TTL_S)["sessions"]] == ["sid"]
    assert state.to_json(now=T0 + SESSION_TTL_S + 1)["sessions"] == []


def test_using_a_session_refreshes_its_ttl() -> None:
    state = HandshakeState()
    session_started(state, "sid", T0, RULES)
    call(state, T0 + 6 * DAY_S, "sid", run_start=T0 + 6 * DAY_S)
    assert is_started(state, "sid", T0 + 12 * DAY_S, RULES)


def test_a_late_message_never_moves_a_sessions_last_use_back() -> None:
    state = HandshakeState()
    session_started(state, "sid", T0, RULES)
    call(state, T0 + 6 * DAY_S, "sid", run_start=T0 + 6 * DAY_S)
    call(state, T0 + DAY_S, "sid", run_start=T0 + 6 * DAY_S)  # stamped 5 days earlier
    assert state.sessions["sid"] == T0 + 6 * DAY_S
    assert is_started(state, "sid", T0 + 12 * DAY_S, RULES)


def test_an_expired_session_behind_a_live_one_is_dropped_when_presented() -> None:
    """A start that reached the state late sits behind a newer session in the LRU order, out
    of reach of the TTL sweep from the front; presenting it after its TTL still drops it."""
    state = HandshakeState()
    session_started(state, "live", T0 + 5 * DAY_S, RULES)
    session_started(state, "late", T0, RULES)
    later = T0 + SESSION_TTL_S + 1
    call(state, later, "late", run_start=later)
    assert list(state.sessions) == ["live"]


def test_a_snapshot_keeps_only_live_sessions_and_a_restart_raises_nothing() -> None:
    state = HandshakeState()
    session_started(state, "old", T0, RULES)
    ts = initialized_runs(state, 3, start=T0 + 7 * DAY_S)
    saved = json.loads(json.dumps(state.to_json(now=ts, ttl=RULES.session_ttl_s)))
    assert [sid for sid, _ in saved["sessions"]] == ["sid-0", "sid-1", "sid-2"]
    restored = HandshakeState.from_json(saved)
    assert not call(restored, ts, "sid-2", run_start=ts).raised  # started before the restart
    assert call(restored, ts + HOUR_S, "old", run_start=ts + HOUR_S).raised


def test_a_caller_saved_without_handshake_state_restores_empty() -> None:
    assert HandshakeState.from_json(None) == HandshakeState()
    assert HandshakeState.from_json({}) == HandshakeState()


def test_without_quota_or_ttl_every_started_session_is_kept() -> None:
    rules = HandshakeRules(max_sessions=None, session_ttl_s=None)
    state = HandshakeState()
    for k in range(MAX_SESSIONS_PER_CALLER + 10):
        session_started(state, f"sid-{k}", T0 + k, rules)
    assert len(state.sessions) == MAX_SESSIONS_PER_CALLER + 10
    assert is_started(state, "sid-0", T0 + 365 * DAY_S, rules)
