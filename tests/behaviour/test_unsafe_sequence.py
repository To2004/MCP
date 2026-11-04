"""E5, SEQ-1, SEQ-2 and E14: Unsafe sequence over the caller's own windows, keyed by pair."""

from __future__ import annotations

import inspect
import json
from dataclasses import replace

import pytest

from mcp_security.behaviour import engine
from mcp_security.behaviour.engine import Message, v5_switches_off
from mcp_security.behaviour.unsafe_sequence import (
    BLIND_WRITE,
    FOREIGN_OWNER,
    NEW_TARGET,
    NO_READ,
    PUBLIC,
    PUBLIC_TARGET,
    READ,
    READ_THEN_WRITE,
    REQUIRED_STEP,
    REQUIRES_WINDOW_S,
    SEQUENCE_WINDOW_S,
    UNRESOLVED,
    WRITE,
    SensitiveRead,
    SequenceFinding,
    SequenceRules,
    SequenceState,
    WindowReadLedger,
    commit,
    evaluate,
    ledger_reads,
    missing_step_source,
    share_read,
    source_id,
)
from mcp_security.gateway.framework import ReadLedger
from tests.behaviour.golden_stream import POLICY, build_stream

MINUTE_S, HOUR_S, DAY_S = 60.0, 3_600.0, 86_400.0
DAY = 20_000  # the caller's local day number in most tests
T0 = DAY * DAY_S + 10 * HOUR_S  # 10:00 on that day
CALLER = "agent-a"
GUARDS = {"merge_pr": frozenset({"review_pr"})}
RULES = SequenceRules(requires_before=GUARDS)
VAULT, REPORTS, NOTES, WIKI = "repo-vault", "repo-reports", "repo-notes", "repo-wiki"


def msg(
    ts: float,
    tool: str,
    asset: str | None,
    operation: str | None = None,
    sensitivity: int | None = None,
    *,
    exposure: str | None = None,
    owner: str | None = None,
    session: str | None = None,
) -> Message:
    """A scored call as the engine's ``Message`` (the module reads it through a protocol)."""
    return Message(
        ts,
        CALLER,
        "tools/call",
        session=session,
        tool=tool,
        asset=asset,
        sensitivity=sensitivity,
        operation=operation,
        exposure=exposure,
        owner=owner,
    )


def read(ts: float, asset: str, sensitivity: int, owner: str | None = None) -> Message:
    return msg(ts, "get_file", asset, READ, sensitivity, owner=owner)


def write(ts: float, asset: str | None, sensitivity: int | None = 2, **kw: object) -> Message:
    return msg(ts, "write_file", asset, WRITE, sensitivity, **kw)


def feed(
    state: SequenceState,
    calls: list[Message],
    rules: SequenceRules = RULES,
    *,
    day: int | None = None,
    habit: bool = True,
) -> list[SequenceFinding]:
    """Score then commit each call, as the engine's observe does; the findings."""
    out = []
    for call in calls:
        today = int(call.ts // DAY_S) if day is None else day
        finding = evaluate(state, call, today, rules)
        commit(state, call, today, finding, rules, habit=habit)
        out.append(finding)
    return out


# ── settings ─────────────────────────────────────────────────────────────────────────────
def test_the_literals_and_windows_are_the_engines() -> None:
    assert (READ, WRITE, PUBLIC) == (engine.READ, engine.WRITE, engine.PUBLIC)
    assert SEQUENCE_WINDOW_S == engine.SEQUENCE_WINDOW_S == 10 * MINUTE_S
    assert REQUIRES_WINDOW_S == engine.REQUIRES_WINDOW_S == DAY_S


def test_rules_from_a_v5_config_and_from_one_with_every_switch_off() -> None:
    on = SequenceRules.from_config(engine.BehaviourConfig(design="v5", requires_before=GUARDS))
    assert (on.read_window_s, on.step_window_s, on.same_asset) == (600.0, DAY_S, True)
    assert on.track_pairs and on.copy_floor and on.step_tools == {"review_pr"}
    off = SequenceRules.from_config(v5_switches_off())
    assert (off.read_window_s, off.step_window_s) == (None, None)
    assert not (off.same_asset or off.track_pairs or off.copy_floor)


def test_the_rules_are_immutable_and_hashable() -> None:
    guards = {"merge_pr": {"review_pr"}}
    rules = SequenceRules(requires_before=guards)
    guards["merge_pr"].add("approve")  # the caller's dict is copied, not shared
    assert rules.requires_before["merge_pr"] == {"review_pr"} == rules.step_tools
    with pytest.raises(TypeError):
        rules.requires_before["deploy"] = frozenset({"approve"})  # type: ignore[index]
    assert hash(rules) == hash(SequenceRules(requires_before=GUARDS)) and rules == RULES
    assert replace(rules, copy_floor=False).requires_before == GUARDS


@pytest.mark.parametrize(
    "bad",
    [
        {"read_window_s": 0},
        {"step_window_s": -1.0},
        {"read_memory_days": 0},
        {"history_days": True},
        {"max_entries": 0},
        {"sensitive_level": 6},
        {"copy_source_level": 0},
    ],
)
def test_bad_rules_fail_fast(bad: dict) -> None:
    with pytest.raises(ValueError):
        SequenceRules(**bad)


# ── E5 (B): read then write within 10 minutes ────────────────────────────────────────────
def test_a_write_9_minutes_after_a_sensitive_read_is_raised_and_at_11_minutes_is_not() -> None:
    """Part A: ts - r.ts <= 10 min, so a write exactly 10 minutes after is still a copy."""
    for gap_s, raised in ((9 * MINUTE_S, True), (SEQUENCE_WINDOW_S, True), (11 * MINUTE_S, False)):
        state = SequenceState()
        feed(state, [read(T0, VAULT, 5)])
        finding = evaluate(state, write(T0 + gap_s, NOTES), DAY, RULES)
        assert (READ_THEN_WRITE in finding.parts) is raised, gap_s


def test_writing_the_asset_just_read_or_after_a_low_sensitivity_read_is_not_a_copy() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), read(T0 + 1, WIKI, 3)])
    # the asset just read: not a copy (B needs a different source), not blind (C: read today)
    assert evaluate(state, write(T0 + MINUTE_S, VAULT, 5), DAY, RULES).parts == ()
    only_low = SequenceState()
    feed(only_low, [read(T0, WIKI, 3)])
    assert not evaluate(only_low, write(T0 + MINUTE_S, NOTES), DAY, RULES).raised


def test_session_ids_change_nothing() -> None:
    """E5 reads no session: the same stream with and without session ids, or with a new
    session per call, gives the same findings (v4's session split hid the copy)."""
    stream = [read(T0, VAULT, 5), write(T0 + 2 * MINUTE_S, NOTES), write(T0 + 3 * MINUTE_S, WIKI)]
    variants = [
        stream,
        [replace(m, session="s1") for m in stream],
        [replace(m, session=f"s{i}") for i, m in enumerate(stream)],
    ]
    results = [feed(SequenceState(), calls) for calls in variants]
    assert results[0] == results[1] == results[2]
    assert results[0][1].parts == (READ_THEN_WRITE,)


# ── SEQ-1: pair keys, strength, record and habit ─────────────────────────────────────────
def test_the_pair_is_source_then_target_with_the_sensitivity_drop_as_strength() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5)])
    (pair,) = evaluate(state, write(T0 + MINUTE_S, NOTES, 2), DAY, RULES).pairs
    assert (pair.key, pair.part, pair.strength) == ((VAULT, NOTES), READ_THEN_WRITE, 3)


@pytest.mark.parametrize(
    ("source", "target", "exposure", "strength"),
    [
        (5, 2, None, 3),
        (5, 2, PUBLIC, 4),  # a public target adds one
        (4, 5, None, 0),  # no drop: never negative
        (4, 5, PUBLIC, 1),
        (5, None, None, 4),  # an unknown target sensitivity counts as the lowest level
    ],
)
def test_strength(source: int, target: int | None, exposure: str | None, strength: int) -> None:
    """The copy's own pair, checked directly: a sensitivity-5 target is also a blind write,
    whose pair could otherwise lead the finding."""
    state = SequenceState()
    feed(state, [read(T0, VAULT, source)])
    finding = evaluate(state, write(T0 + MINUTE_S, NOTES, target, exposure=exposure), DAY, RULES)
    (copy,) = [pair for pair in finding.pairs if pair.part == READ_THEN_WRITE]
    assert copy.strength == finding.strength == strength


def test_a_new_pair_is_a_record_and_a_repeated_pair_is_habit() -> None:
    state = SequenceState()
    day1 = feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], day=DAY)[1]
    assert day1.record and day1.lead.past_days == 0
    feed(state, [read(T0 + DAY_S, VAULT, 5)], day=DAY + 1)
    again = evaluate(state, write(T0 + DAY_S + MINUTE_S, NOTES), DAY + 1, RULES)
    assert not again.record and again.lead.past_days == 1  # habit: priced by its past days
    other = evaluate(state, write(T0 + DAY_S + MINUTE_S, WIKI), DAY + 1, RULES)
    assert other.record  # the same source into a new target is a new pair


def test_today_never_counts_as_a_past_day() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], day=DAY)
    same_day = evaluate(state, write(T0 + 2 * MINUTE_S, NOTES), DAY, RULES)
    assert same_day.record and same_day.lead.past_days == 0


def test_a_pair_leaves_the_window_after_90_days() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], day=DAY)
    assert state.past_days((VAULT, NOTES), DAY + 89) == 1
    assert state.past_days((VAULT, NOTES), DAY + 90) == 0
    for offset in (50, 100):  # raised again: a day that left the window leaves the list
        ts = T0 + offset * DAY_S
        feed(state, [read(ts, VAULT, 5), write(ts + MINUTE_S, NOTES)], day=DAY + offset)
    assert state.pair_days[(VAULT, NOTES)] == [DAY + 50, DAY + 100]


def test_the_lead_pair_is_the_strangest_then_the_strongest() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], day=DAY)  # a habit pair
    tomorrow = T0 + DAY_S
    feed(state, [read(tomorrow, VAULT, 5), read(tomorrow + 1, REPORTS, 4)], day=DAY + 1)
    finding = evaluate(state, write(tomorrow + MINUTE_S, NOTES), DAY + 1, RULES)
    assert {p.key for p in finding.pairs} == {(VAULT, NOTES), (REPORTS, NOTES)}
    assert finding.lead.key == (REPORTS, NOTES) and finding.record  # new beats stronger habit
    fresh = evaluate(SequenceState(), write(T0, NOTES), DAY, RULES)
    assert fresh.lead is None and fresh.strength is None and not fresh.record


def test_among_new_pairs_the_strongest_leads() -> None:
    """Two records (strengths 2 and 3): the stronger one sets the record rank's strength."""
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), read(T0 + 1, REPORTS, 4)])
    finding = evaluate(state, write(T0 + MINUTE_S, NOTES, 2), DAY, RULES)
    assert sorted(p.strength for p in finding.pairs) == [2, 3]
    assert all(p.record for p in finding.pairs)
    assert (finding.lead.key, finding.strength) == ((VAULT, NOTES), 3)


def test_habit_days_are_kept_out_until_the_engine_says_so() -> None:
    """RF11: commit(habit=False) learns the read but not the pair day."""
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], day=DAY, habit=False)
    assert state.past_days((VAULT, NOTES), DAY + 1) == 0 and VAULT in state.last_read


def test_with_pairs_off_nothing_is_counted() -> None:
    rules = replace(RULES, track_pairs=False)
    state = SequenceState()
    finding = feed(state, [read(T0, VAULT, 5), write(T0 + MINUTE_S, NOTES)], rules)[1]
    assert finding.raised and finding.lead.past_days is None and not finding.record
    assert not state.pair_days


# ── E5 (A): the required step within 24 hours, on the same asset ─────────────────────────
def review(ts: float, asset: str | None, session: str | None = None) -> Message:
    return msg(ts, "review_pr", asset, READ, 2, session=session)


def merge(ts: float, asset: str | None, session: str | None = None) -> Message:
    return msg(ts, "merge_pr", asset, WRITE, 2, session=session)


def test_a_merge_after_a_review_of_the_same_repository_3_hours_earlier_is_clear() -> None:
    state = SequenceState()
    feed(state, [review(T0, WIKI, "s1")])
    finding = evaluate(state, merge(T0 + 3 * HOUR_S, WIKI, "s2"), DAY, RULES)
    assert REQUIRED_STEP not in finding.parts


def test_a_review_of_one_repository_then_a_merge_of_another_is_raised() -> None:
    state = SequenceState()
    feed(state, [review(T0, WIKI)])
    finding = evaluate(state, merge(T0 + HOUR_S, NOTES), DAY, RULES)
    assert finding.parts == (REQUIRED_STEP,)
    assert finding.lead.key == (missing_step_source("merge_pr"), NOTES)


def test_a_review_older_than_24_hours_does_not_count() -> None:
    state = SequenceState()
    feed(state, [review(T0, WIKI)])
    assert evaluate(state, merge(T0 + DAY_S, WIKI), DAY + 1, RULES).parts == ()
    assert evaluate(state, merge(T0 + DAY_S + 1, WIKI), DAY + 1, RULES).parts == (REQUIRED_STEP,)


def test_an_unresolved_asset_on_either_side_falls_back_to_the_tool() -> None:
    unresolved_review = SequenceState()
    feed(unresolved_review, [review(T0, None)])
    assert not evaluate(unresolved_review, merge(T0 + HOUR_S, NOTES), DAY, RULES).raised
    resolved_review = SequenceState()
    feed(resolved_review, [review(T0, WIKI)])
    assert not evaluate(resolved_review, merge(T0 + HOUR_S, None), DAY, RULES).raised
    nothing = evaluate(SequenceState(), merge(T0, None), DAY, RULES)
    assert nothing.lead.target == UNRESOLVED


def test_a_review_at_the_same_second_as_the_merge_counts() -> None:
    """The window is closed at both ends, [ts - 24 h, ts] (the module docstring)."""
    state = SequenceState()
    feed(state, [review(T0, WIKI)])
    assert not evaluate(state, merge(T0, WIKI), DAY, RULES).raised


def test_each_guarded_tool_needs_its_own_step() -> None:
    """A review clears a merge but not a deploy, which needs an approval; with the deploy's
    asset unresolved the check falls back to the tool, and still no approval was made."""
    rules = SequenceRules(requires_before={**GUARDS, "deploy": frozenset({"approve"})})
    state = SequenceState()
    feed(state, [review(T0, WIKI)], rules)
    assert not evaluate(state, merge(T0 + HOUR_S, WIKI), DAY, rules).raised
    deploy = msg(T0 + HOUR_S, "deploy", None, WRITE, 2)
    finding = evaluate(state, deploy, DAY, rules)
    assert finding.parts == (REQUIRED_STEP,)
    assert finding.lead.key == (missing_step_source("deploy"), UNRESOLVED)
    feed(state, [msg(T0 + 2 * HOUR_S, "approve", WIKI, READ, 2)], rules)
    assert not evaluate(state, replace(deploy, ts=T0 + 3 * HOUR_S), DAY, rules).raised


def test_a_late_older_review_does_not_hide_a_newer_one() -> None:
    """A review stamped 25 hours earlier that arrives late must not replace today's."""
    state = SequenceState()
    feed(state, [review(T0, WIKI), review(T0 - 25 * HOUR_S, WIKI)])
    assert not evaluate(state, merge(T0 + HOUR_S, WIKI), DAY, RULES).raised
    assert state.steps[("review_pr", WIKI)] == T0


def test_with_the_same_asset_tie_off_any_review_counts() -> None:
    rules = replace(RULES, same_asset=False)
    state = SequenceState()
    feed(state, [review(T0, WIKI)], rules)
    assert not evaluate(state, merge(T0 + HOUR_S, NOTES), DAY, rules).raised


# ── E1 cannot recur: a missing session is never evidence of a missing step ───────────────
def test_a_sessionless_merge_after_a_sessionless_review_is_clear() -> None:
    """E1's bug: v4 raised every sessionless guarded call, review or not. v5's check takes
    no session, so the review counts whatever the session ids."""
    state = SequenceState()
    feed(state, [review(T0, WIKI, session=None)])
    finding = evaluate(state, merge(T0 + 5 * MINUTE_S, WIKI, session=None), DAY, RULES)
    assert not finding.raised


def test_a_merge_with_no_review_is_raised_with_or_without_a_session() -> None:
    """E5 (A) is session-free: no review in the 24 h window raises the merge whatever its
    session id, and a session id never stands in for the review."""
    for session in (None, "s1"):
        finding = evaluate(SequenceState(), merge(T0, WIKI, session=session), DAY, RULES)
        assert finding.parts == (REQUIRED_STEP,)


def _golden_findings(stream: list[Message]) -> list[SequenceFinding]:
    """Each tool call of the INF-1 stream through E5, one state per caller (UTC days)."""
    rules = SequenceRules(requires_before=POLICY["requires_before"])
    states: dict[str, SequenceState] = {}
    out = []
    for m in stream:
        if m.method != "tools/call":
            continue
        state = states.setdefault(m.agent, SequenceState())
        today = int(m.ts // DAY_S)
        finding = evaluate(state, m, today, rules)
        commit(state, m, today, finding, rules)
        out.append(finding)
    return out


def test_on_the_golden_stream_e5_is_its_formula_and_ignores_session_ids() -> None:
    """The INF-1 stream through E5 (A): a guarded call is raised exactly when no required
    step of his, on the same asset or with either unresolved, lies in [ts - 24 h, ts].
    Carol's sessionless merges: day 10 (repo-app, last reviewed 25 h earlier) is raised;
    day 11 (repo-docs, reviewed in a session an hour earlier) and day 25 (after her
    sessionless review) are clear. The bot's nightly sessionless merge never follows a
    review, so it is raised every night. Stripping every session id, or giving every call
    its own, changes nothing."""
    stream = build_stream()
    calls = [m for m in stream if m.method == "tools/call"]
    guards = POLICY["requires_before"]

    def oracle(i: int) -> bool:
        m = calls[i]
        return not any(
            c.agent == m.agent
            and c.tool in guards[m.tool]
            and 0 <= m.ts - c.ts <= REQUIRES_WINDOW_S
            and (c.asset is None or m.asset is None or c.asset == m.asset)
            for c in calls[:i]
        )

    findings = _golden_findings(stream)
    guarded = [i for i, m in enumerate(calls) if m.tool in guards]
    assert [REQUIRED_STEP in findings[i].parts for i in guarded] == [oracle(i) for i in guarded]
    carol = [i for i in guarded if calls[i].agent == "carol" and calls[i].session is None]
    assert [REQUIRED_STEP in findings[i].parts for i in carol] == [True, False, False]
    bot = [i for i in guarded if calls[i].agent == "ci-bot"]
    assert len(bot) == 30 and all(REQUIRED_STEP in findings[i].parts for i in bot)
    sessionless = [replace(m, session=None) for m in stream]
    one_each = [replace(m, session=f"s{k}") for k, m in enumerate(stream)]
    assert _golden_findings(sessionless) == findings == _golden_findings(one_each)


# ── E5 (C): a blind write, v4's 7-day rule ───────────────────────────────────────────────
def test_a_write_to_a_sensitive_asset_not_read_in_7_days_is_blind() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5)], day=DAY)
    assert BLIND_WRITE not in evaluate(state, write(T0 + 7 * DAY_S, VAULT, 5), DAY + 7, RULES).parts
    blind = evaluate(state, write(T0 + 8 * DAY_S, VAULT, 5), DAY + 8, RULES)
    assert blind.parts == (BLIND_WRITE,) and blind.lead.key == (NO_READ, VAULT)
    assert BLIND_WRITE not in evaluate(state, write(T0, NOTES, 3), DAY, RULES).parts


def test_a_never_read_write_at_the_sensitive_level_is_blind_and_below_it_is_not() -> None:
    assert evaluate(SequenceState(), write(T0, REPORTS, 4), DAY, RULES).parts == (BLIND_WRITE,)
    assert evaluate(SequenceState(), write(T0, REPORTS, 3), DAY, RULES).parts == ()


# ── SEQ-2: the copy floor ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("target_kw", "target_new", "reasons"),
    [
        ({"exposure": PUBLIC}, False, (PUBLIC_TARGET,)),
        ({"owner": "owner-b"}, False, (FOREIGN_OWNER,)),
        ({}, True, (NEW_TARGET,)),
        (
            {"exposure": PUBLIC, "owner": "owner-b"},
            True,
            (PUBLIC_TARGET, FOREIGN_OWNER, NEW_TARGET),
        ),
    ],
)
def test_a_sensitivity_5_copy_into_a_public_foreign_or_new_target_fires_the_floor(
    target_kw: dict, target_new: bool, reasons: tuple[str, ...]
) -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5, owner="owner-a")])
    call = write(T0 + MINUTE_S, NOTES, **target_kw)
    (floor,) = evaluate(state, call, DAY, RULES, target_new=target_new).copy_floors
    assert (floor.source, floor.target, floor.reasons) == (VAULT, NOTES, reasons)


def test_the_copy_floor_does_not_fire_without_its_trigger() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5, owner="owner-a"), read(T0, REPORTS, 4, owner="owner-a")])
    plain = evaluate(state, write(T0 + MINUTE_S, NOTES, owner="owner-a"), DAY, RULES)
    assert plain.raised and not plain.copy_floors  # same owner, private, known target
    unknown_owner = evaluate(state, write(T0 + MINUTE_S, NOTES), DAY, RULES)
    assert not unknown_owner.copy_floors  # an unknown owner is never foreign
    no_source_owner = SequenceState()
    feed(no_source_owner, [read(T0, VAULT, 5)])  # the source's owner is unknown
    into_known = evaluate(no_source_owner, write(T0 + MINUTE_S, NOTES, owner="o-b"), DAY, RULES)
    assert into_known.raised and not into_known.copy_floors
    only_4 = SequenceState()
    feed(only_4, [read(T0, REPORTS, 4)])
    public = write(T0 + MINUTE_S, NOTES, exposure=PUBLIC)
    assert not evaluate(only_4, public, DAY, RULES, target_new=True).copy_floors
    off = replace(RULES, copy_floor=False)
    assert not evaluate(state, public, DAY, off, target_new=True).copy_floors


# ── E14: the cross-route read ledger ─────────────────────────────────────────────────────
def test_a_read_on_one_route_and_a_write_on_another_make_a_sequence() -> None:
    ledger = WindowReadLedger()
    source = read(T0, VAULT, 5, owner="owner-a")
    assert share_read(ledger, CALLER, "github", source)
    ts = T0 + 5 * MINUTE_S
    cross = ledger_reads(ledger, CALLER, "slack", ts)
    assert [(r.asset, r.route) for r in cross] == [(VAULT, "github")]
    post = write(ts, "channel-general", 2, exposure=PUBLIC)
    finding = evaluate(SequenceState(), post, DAY, RULES, cross_reads=cross)
    assert finding.parts == (READ_THEN_WRITE,)
    assert finding.copy_floors[0].route == "github"
    assert not evaluate(SequenceState(), post, DAY, RULES).raised  # without the ledger


def test_the_same_asset_id_on_another_route_is_a_different_source() -> None:
    """A sensitive read of 'general' on one route then a public write to 'general' on this
    route is a copy; and the two routes' 'general' are two sources, with two pairs."""
    ledger = WindowReadLedger()
    share_read(ledger, CALLER, "github", read(T0, "general", 5))
    cross = ledger_reads(ledger, CALLER, "slack", T0 + MINUTE_S)
    assert [source_id(r) for r in cross] == ["github:general"]
    post = write(T0 + MINUTE_S, "general", 1, exposure=PUBLIC)
    finding = evaluate(SequenceState(), post, DAY, RULES, cross_reads=cross)
    assert finding.parts == (READ_THEN_WRITE,)
    assert finding.lead.key == ("github:general", "general")
    (floor,) = finding.copy_floors
    assert (floor.source, floor.route) == ("github:general", "github")
    own = SequenceState()
    feed(own, [read(T0, "general", 5)])
    both = evaluate(own, write(T0 + MINUTE_S, NOTES), DAY, RULES, cross_reads=cross)
    assert [p.key for p in both.pairs] == [("general", NOTES), ("github:general", NOTES)]
    look_alike = write(T0 + MINUTE_S, "github:general", 1)  # this route's asset, same text
    assert evaluate(SequenceState(), look_alike, DAY, RULES, cross_reads=cross).raised


def test_the_latest_read_of_a_source_is_the_one_that_counts() -> None:
    """Two reads of one asset on another route, re-labelled from 5 to 4 in between: the later
    read sets the drop and the copy floor, as this route's own reads do."""
    ledger = WindowReadLedger()
    ledger.note_read(CALLER, "github", VAULT, 5, T0)
    ledger.note_read(CALLER, "github", VAULT, 4, T0 + MINUTE_S)
    cross = ledger_reads(ledger, CALLER, "slack", T0 + 2 * MINUTE_S)
    post = write(T0 + 2 * MINUTE_S, NOTES, 2, exposure=PUBLIC)
    finding = evaluate(SequenceState(), post, DAY, RULES, cross_reads=cross)
    (pair,) = finding.pairs
    assert pair.strength == (4 - 2) + 1 and not finding.copy_floors


def test_a_read_below_the_sensitive_level_is_never_a_source() -> None:
    """(B) checks the level itself: for reads the engine passes in, and for reads kept under
    a lower level before the rules changed."""
    post = write(T0 + MINUTE_S, NOTES)
    low = SensitiveRead(T0, WIKI, 3, route="github")
    assert not evaluate(SequenceState(), post, DAY, RULES, cross_reads=[low]).raised
    level_3 = replace(RULES, sensitive_level=3)
    kept = SequenceState()
    feed(kept, [read(T0, WIKI, 3)], level_3)
    assert evaluate(kept, post, DAY, level_3).parts == (READ_THEN_WRITE,)
    assert not evaluate(kept, post, DAY, RULES).raised


def test_the_ledger_leaves_out_this_routes_old_and_low_reads() -> None:
    ledger = WindowReadLedger()
    share_read(ledger, CALLER, "github", read(T0, VAULT, 5))
    assert ledger_reads(ledger, CALLER, "github", T0 + MINUTE_S) == ()  # this route's own
    assert ledger_reads(ledger, CALLER, "slack", T0 + 11 * MINUTE_S) == ()  # out of window
    assert ledger_reads(ledger, CALLER, "slack", T0 - MINUTE_S) == ()  # after the call
    assert ledger_reads(ledger, "agent-b", "slack", T0 + MINUTE_S) == ()  # another caller
    assert ledger_reads(None, CALLER, "slack", T0) == ()
    ledger.note_read(CALLER, "github", WIKI, 3, T0)  # noted by another component, below level
    assert [r.asset for r in ledger_reads(ledger, CALLER, "slack", T0 + MINUTE_S)] == [VAULT]
    assert not share_read(ledger, CALLER, "github", read(T0, WIKI, 3))
    assert not share_read(ledger, CALLER, "github", write(T0, VAULT, 5))
    assert not share_read(None, CALLER, "github", read(T0, VAULT, 5))


def test_the_in_memory_ledger_has_the_gateways_read_ledger_signature() -> None:
    for name in ("note_read", "reads_since"):
        ours = inspect.signature(getattr(WindowReadLedger, name)).parameters
        theirs = inspect.signature(getattr(ReadLedger, name)).parameters
        assert list(ours) == list(theirs)


def test_the_ledger_forgets_quiet_callers_and_caps_each_one() -> None:
    ledger = WindowReadLedger(window_s=SEQUENCE_WINDOW_S, max_reads=3)
    for k in range(10):
        ledger.note_read("agent-b", "github", f"repo-{k}", 5, T0 + k)
    assert len(ledger) == 3
    ledger.note_read(CALLER, "github", VAULT, 5, T0 + HOUR_S)  # agent-b is long quiet
    assert len(ledger) == 1 and ledger.reads_since("agent-b", 0.0) == []
    with pytest.raises(ValueError):
        WindowReadLedger(window_s=0)


# ── score/commit, snapshots, bounds ──────────────────────────────────────────────────────
def test_evaluate_never_changes_the_state() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), review(T0, WIKI), write(T0 + MINUTE_S, NOTES)])
    before = json.dumps(state.to_json())
    for call in (write(T0 + 2 * MINUTE_S, WIKI), merge(T0, NOTES), read(T0 + 3, REPORTS, 5)):
        evaluate(state, call, DAY, RULES, target_new=True)
    assert json.dumps(state.to_json()) == before


def test_a_late_older_read_does_not_hide_a_newer_one() -> None:
    """A read of the vault stamped 20 minutes earlier that arrives late must not replace
    the read just made: a write 2 minutes after that read is still a copy."""
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), read(T0 - 20 * MINUTE_S, VAULT, 5)])
    assert state.reads[VAULT].ts == T0
    finding = evaluate(state, write(T0 + 2 * MINUTE_S, NOTES), DAY, RULES)
    assert finding.parts == (READ_THEN_WRITE,)
    week = SequenceState()  # (C): a late read stamped 8 days back keeps the newer read day
    feed(week, [read(T0 + 8 * DAY_S, VAULT, 5), read(T0, VAULT, 5)])
    assert week.last_read[VAULT] == DAY + 8
    assert not evaluate(week, write(T0 + 8 * DAY_S + MINUTE_S, VAULT, 5), DAY + 8, RULES).raised


def test_a_snapshot_round_trip_gives_the_same_findings() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5, owner="o"), review(T0, WIKI), write(T0 + MINUTE_S, NOTES)])
    restored = SequenceState.from_json(json.loads(json.dumps(state.to_json())))
    assert restored.to_json() == state.to_json()
    for call in (write(T0 + 2 * MINUTE_S, REPORTS), merge(T0 + HOUR_S, WIKI)):
        assert evaluate(restored, call, DAY, RULES) == evaluate(state, call, DAY, RULES)
    assert SequenceState.from_json(None).to_json() == SequenceState().to_json()


def test_old_entries_are_pruned_by_time() -> None:
    state = SequenceState()
    feed(state, [read(T0, VAULT, 5), review(T0, WIKI)], day=DAY)
    feed(state, [read(T0 + 2 * DAY_S, REPORTS, 4)], day=DAY + 2)
    assert list(state.reads) == [REPORTS] and not state.steps
    feed(state, [read(T0 + 10 * DAY_S, NOTES, 4)], day=DAY + 10)
    assert list(state.last_read) == [NOTES]


def test_a_flood_of_sensitive_reads_and_pairs_stays_bounded() -> None:
    rules = replace(RULES, max_entries=128)
    state = SequenceState()
    calls = [read(T0 + k * 0.01, f"repo-{k}", 5) for k in range(10_000)]
    feed(state, calls, rules, day=DAY)
    assert len(state.reads) == len(state.last_read) == 128
    finding = feed(state, [write(T0 + 200.0, NOTES)], rules, day=DAY)[0]
    assert len(finding.pairs) == 128  # one pair per remembered source
    for k in range(300):
        feed(state, [write(T0 + 201.0 + k, f"target-{k}")], rules, day=DAY)
    assert len(state.pair_days) <= 128
