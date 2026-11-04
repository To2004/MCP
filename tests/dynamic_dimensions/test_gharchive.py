"""Tests for the EV-26 GH Archive request-size extractor and the shared reader.

Every event here is synthetic: invented logins, organisations and repositories, written to
temporary files. Nothing is downloaded. The X2 cadence tests are in
``test_gharchive_cadence.py``.
"""

from __future__ import annotations

import gzip
import json
import os
import random
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from mcp_security.behaviour import policy
from mcp_security.behaviour.clock import DAY_S, local_day
from mcp_security.behaviour.engine import ACCEPTED, CALL_METHOD, WRITE, BehaviourConfig, Message
from mcp_security.gateway.protocol_era import argument_bytes
from mcp_security.gateway.pseudonym import Pseudonymizer
from reports.experiments.dynamic_dimensions.heldout import gharchive_actor_cadence as cad
from reports.experiments.dynamic_dimensions.heldout import gharchive_request_sizes as gs
from tests.dynamic_dimensions.gharchive_support import (
    AGENT_A,
    AGENTS,
    BOT_A,
    DAY,
    HOUR,
    KEY,
    MONDAY,
    ORG_A,
    ORG_B,
    ORG_C,
    OTHER_KEY,
    PERSON_A,
    PERSON_B,
    assert_no_identities,
    comment,
    event,
    issue,
    pseudo,
    review,
    write_gz,
)

LEARN_FROM = MONDAY
COMMENT, ISSUE = gs.ADD_ISSUE_COMMENT, gs.CREATE_ISSUE
PULL, REVIEW = gs.CREATE_PULL_REQUEST, gs.CREATE_PULL_REQUEST_REVIEW
CALLS_PER_SIZE_BANK = 3000
SIZE_TAIL, MAX_REQUEST_KB, ABOVE_KB = 1.5, 200, 20  # the limit fixture's request sizes
REPO_ROOT = Path(__file__).resolve().parents[2]
SBATCH = REPO_ROOT / "scripts" / "dynamic_design" / "gharchive_array.sbatch"


# ── mapping and sizes ──────────────────────────────────────────────────────────────────────


def test_events_map_to_tools_and_their_arguments() -> None:
    assert gs.mapped_tool(issue("t", "b")) == ISSUE
    assert gs.mapped_tool(issue("t", "b", action="closed")) is None
    assert gs.mapped_tool(event("PushEvent", {})) is None
    assert gs.call_arguments(issue("Title", "Body"), ISSUE) == {
        "owner": ORG_A,
        "repo": "widgets",
        "title": "Title",
        "body": "Body",
    }
    # A null body is left out, as a client leaves out an unset optional argument; a title
    # alone is still a request (only a payload without both is trimmed).
    assert gs.call_arguments(issue("Title", None), ISSUE) == {
        "owner": ORG_A,
        "repo": "widgets",
        "title": "Title",
    }
    assert gs.call_arguments(comment("Hi", number=41), COMMENT) == {
        "owner": ORG_A,
        "repo": "widgets",
        "issue_number": 41,
        "body": "Hi",
    }
    expected_review = {"owner": ORG_A, "repo": "widgets", "pullNumber": 12, "body": "ok"}
    for state, verdict in (
        ("approved", "APPROVE"),
        ("changes_requested", "REQUEST_CHANGES"),
        ("commented", "COMMENT"),
    ):
        made = review("ok", state)
        assert gs.mapped_tool(made) == REVIEW
        assert gs.call_arguments(made, REVIEW) == expected_review | {"event": verdict}
    pull = event(
        "PullRequestEvent",
        {
            "action": "opened",
            "pull_request": {
                "title": "T",
                "body": None,
                "head": {"ref": "f"},
                "base": {"ref": "main"},
            },
        },
    )
    assert gs.call_arguments(pull, PULL) == {
        "owner": ORG_A,
        "repo": "widgets",
        "title": "T",
        "head": "f",
        "base": "main",
    }
    trimmed = event("PullRequestEvent", {"action": "opened", "pull_request": {"number": 3}})
    assert gs.call_arguments(trimmed, PULL) is None
    title_only = event("IssuesEvent", {"action": "opened", "issue": {"title": "T"}})
    assert gs.call_arguments(title_only, ISSUE) == {"owner": ORG_A, "repo": "widgets", "title": "T"}
    with pytest.raises(ValueError):
        gs.call_arguments(comment("x"), "merge_pull_request")


def test_sizes_are_the_gateway_measures_in_utf8_bytes() -> None:
    arguments = {"owner": "o", "repo": "r", "title": "t", "body": "é✓"}
    size = gs.request_size(ISSUE, arguments)
    # Compact UTF-8 bytes of params.arguments: "é" is 2 bytes and "✓" 3, not 1 character each.
    assert size.arg_bytes == len('{"owner":"o","repo":"r","title":"t","body":"é✓"}'.encode())
    message = gs.request_message(ISSUE, arguments)
    assert "_meta" not in message["params"]  # the legacy-era rendering
    assert size.arg_bytes == argument_bytes(message)
    assert size.message_bytes == len(json.dumps(message, ensure_ascii=False).encode())
    assert size.message_bytes > size.arg_bytes


def test_iter_events_streams_gzip_and_skips_bad_lines(tmp_path: Path) -> None:
    lines = [json.dumps(comment("a")), "not json", "[1, 2]", "", json.dumps(comment("b"))]
    path = write_gz(tmp_path / "2025-01-04-0.json.gz", lines)
    stats: Counter = Counter()
    events = list(gs.iter_events([path], stats))
    assert [e["payload"]["comment"]["body"] for e in events] == ["a", "b"]
    assert stats["parse_errors"] == 2


def test_a_truncated_download_fails_loudly(tmp_path: Path) -> None:
    whole = write_gz(tmp_path / "whole.json.gz", [json.dumps(comment("x" * 5000))] * 50)
    cut = tmp_path / "cut.json.gz"
    cut.write_bytes(whole.read_bytes()[: whole.stat().st_size // 2])
    with pytest.raises((EOFError, OSError)):
        list(gs.iter_events([cut]))


def test_actor_classes_and_agent_login_files(tmp_path: Path) -> None:
    assert gs.actor_class(PERSON_A, AGENTS) == gs.PERSON
    assert gs.actor_class(BOT_A, AGENTS) == gs.BOT
    assert gs.actor_class(AGENT_A, AGENTS) == gs.AGENT  # matched without case
    assert gs.actor_class(AGENT_A, ()) == gs.BOT
    listing = tmp_path / "agents.txt"
    listing.write_text("# coding agents\n  # an indented note\n\n  Agent-X[bot]  \nbuilder\n")
    assert gs.load_agent_logins(listing) == frozenset({"agent-x[bot]", "builder"})
    assert gs.load_agent_logins(None) == gs.AGENT_LOGINS


# ── pseudonyms and the key check ───────────────────────────────────────────────────────────


def test_extraction_refuses_to_run_without_a_key() -> None:
    with pytest.raises(gs.PseudonymKeyError):
        gs.keyed_pseudonymizer(environ={})
    for short in ("short", "x" * 31):
        with pytest.raises(gs.PseudonymKeyError):
            gs.keyed_pseudonymizer(environ={gs.KEY_ENV: short})
    assert gs.keyed_pseudonymizer(environ={gs.KEY_ENV: "x" * gs.MIN_KEY_CHARS}).keyed
    with pytest.raises(ValueError):
        gs.pseudonym(Pseudonymizer(), gs.ACTOR_ROLE, PERSON_A)
    with pytest.raises(ValueError):
        gs.key_check(Pseudonymizer())


def test_pseudonyms_are_stable_within_a_run_and_keyed() -> None:
    events = [comment("hello", login=PERSON_A), comment("hi", login=PERSON_B, org=ORG_B)]
    first = gs.extract_requests(events, pseudo()).to_json()
    again = gs.extract_requests(events, pseudo()).to_json()
    other = gs.extract_requests(events, pseudo(OTHER_KEY)).to_json()
    assert first == again
    assert {d["actor"] for d in first["parts"]}.isdisjoint({d["actor"] for d in other["parts"]})
    # Roles are separate domains: a login equal to an organisation name gets another pseudonym.
    p = pseudo()
    assert gs.pseudonym(p, gs.ACTOR_ROLE, ORG_A) != gs.pseudonym(p, gs.ORG_ROLE, ORG_A)
    # The key check names the key, not a login, and differs across keys.
    assert first["key_check"] == gs.key_check(p) != gs.key_check(pseudo(OTHER_KEY))
    assert first["key_check"] not in {gs.pseudonym(p, gs.ACTOR_ROLE, PERSON_A), p.of(KEY)}
    assert_no_identities(json.dumps(first))


# ── extraction ─────────────────────────────────────────────────────────────────────────────


def test_extract_keeps_each_part_largest_request_and_the_histograms() -> None:
    events = [
        comment("short", seconds=100),
        comment("a much longer comment body", seconds=200),
        comment("after the split", seconds=gs.SPLIT_S),
        comment("other day", day=DAY + 1),
        comment("personal repository", org=None),
        event("IssueCommentEvent", {"action": "created", "issue": {}, "comment": {}}),
        comment("bot", login=BOT_A),
        issue("no time", "b") | {"created_at": None},
    ]
    out = gs.extract_requests(events, pseudo(), agent_logins=AGENTS)
    assert out.stats["mapped:add_issue_comment"] == 5
    assert out.stats["text_missing:add_issue_comment"] == 1
    assert out.stats["no_org"] == 1
    assert out.stats["bad_events"] == 1
    p = pseudo()
    org, actor = gs.pseudonym(p, gs.ORG_ROLE, ORG_A), gs.pseudonym(p, gs.ACTOR_ROLE, PERSON_A)
    early = out.parts[(org, actor, DAY, gs.EARLY)]
    longest = gs.call_arguments(comment("a much longer comment body"), COMMENT)
    assert early.calls == {COMMENT: 2}  # 00:01:40 and 00:03:20
    assert early.largest_args[COMMENT] == gs.request_size(COMMENT, longest).arg_bytes
    late = out.parts[(org, actor, DAY, gs.LATE)]
    assert late.calls == {COMMENT: 1}  # 04:00:00 opens the late part
    assert set(out.parts) == {
        (org, actor, DAY, gs.EARLY),
        (org, actor, DAY, gs.LATE),
        (org, actor, DAY + 1, gs.EARLY),
        (org, gs.pseudonym(p, gs.ACTOR_ROLE, BOT_A), DAY, gs.EARLY),
    }
    # Each histogram holds its own measure of every mapped call.
    person_calls = [e for e in events[:4]]
    for measure in gs.MEASURES:
        want = Counter(
            getattr(gs.request_size(COMMENT, gs.call_arguments(e, COMMENT)), measure)
            for e in person_calls
        )
        assert out.histograms[measure][gs.PERSON][COMMENT] == want


def test_a_declared_day_drops_events_outside_it() -> None:
    events = [comment("in", seconds=10), comment("before", day=DAY - 1, seconds=DAY_S - 1)]
    out = gs.extract_requests(events, pseudo(), day=DAY)
    assert out.utc_days == {DAY}
    assert out.stats["outside_day"] == 1
    assert {key[2] for key in out.parts} == {DAY}


def test_extract_filters_organisations_round_trips_and_merges() -> None:
    p = pseudo()
    events = [comment("a", org=ORG_A), comment("b", org=ORG_B), comment("c", org=ORG_C)]
    keep = frozenset({gs.pseudonym(p, gs.ORG_ROLE, ORG_A), gs.pseudonym(p, gs.ORG_ROLE, ORG_B)})
    drop = {gs.pseudonym(p, gs.ORG_ROLE, ORG_B)}
    out = gs.extract_requests(events, p, orgs=keep, exclude_orgs=drop)
    assert {d.org for d in out.parts.values()} == {gs.pseudonym(p, gs.ORG_ROLE, ORG_A)}
    assert out.stats["other_org"] == 2
    back = gs.RequestExtract.from_json(json.loads(json.dumps(out.to_json())))
    assert back.to_json() == out.to_json()
    merged = gs.merge_extracts([out, back])
    only = next(iter(merged.parts.values()))
    assert only.calls == {COMMENT: 2}
    assert merged.histograms[gs.ARG_BYTES][gs.PERSON][COMMENT].total() == 2
    assert merged.key_check == gs.key_check(p)


def test_merging_refuses_other_keys_and_days_read_twice() -> None:
    one = gs.extract_requests([comment("a")], pseudo(), day=DAY)
    other_key = gs.extract_requests([comment("a")], pseudo(OTHER_KEY), day=DAY + 1)
    with pytest.raises(ValueError, match="keys"):
        gs.merge_extracts([one, other_key])
    with pytest.raises(ValueError, match="twice"):
        gs.merge_extracts([one, gs.extract_requests([comment("b")], pseudo(), day=DAY)])
    both = gs.merge_extracts([one, gs.extract_requests([comment("b")], pseudo(), day=DAY + 1)])
    assert both.utc_days == {DAY, DAY + 1}


# ── day parts and conventions ──────────────────────────────────────────────────────────────


def test_parts_rebuild_each_designs_day_key() -> None:
    cfg4, cfg5 = BehaviourConfig(), BehaviourConfig(design="v5")
    rng = random.Random(1)
    edges = (0, 1, gs.SPLIT_S - 1, gs.SPLIT_S, DAY_S - 1)
    stamps = [DAY * DAY_S + s for s in edges]
    stamps += [DAY * DAY_S + rng.randrange(3 * int(DAY_S)) for _ in range(500)]
    for ts in stamps:
        day, part = gs.utc_day(ts), gs.part_of(ts)
        assert gs.convention_day(day, part, gs.V4_DAYS) == policy.learning_day(ts, None, cfg4)
        assert gs.convention_day(day, part, gs.V5_DAYS) == policy.learning_day(ts, "UTC", cfg5)
        assert policy.learning_day(ts, "UTC", cfg5) == local_day(ts, "UTC", 4.0)
    assert gs.part_of(DAY * DAY_S + gs.SPLIT_S - 1) == gs.EARLY
    assert gs.part_of(DAY * DAY_S + gs.SPLIT_S) == gs.LATE
    assert gs.utc_days_of(DAY, gs.V5_DAYS) == (DAY, DAY + 1)
    with pytest.raises(ValueError):
        gs.convention_day(DAY, gs.EARLY, "utc")


def _part(
    org: str,
    actor: str,
    day: int,
    sizes: dict[str, int],
    cls: str = gs.PERSON,
    part: int = gs.LATE,
    gap: int = 100,
) -> gs.RequestDay:
    """A part whose argument bytes are ``gap`` below its message bytes."""
    row = gs.RequestDay(org, actor, cls, day, part)
    for tool, size in sizes.items():
        row.add(gs.RequestSize(tool, size - gap, size))
    return row


def test_actor_days_merge_parts_by_convention_and_drop_incomplete_days() -> None:
    early = _part("o", "a", DAY, {COMMENT: 1_000}, part=gs.EARLY)
    early.add(gs.RequestSize(COMMENT, 400, 500), calls=2)
    parts = [
        early,
        _part("o", "a", DAY, {COMMENT: 3_000}, part=gs.LATE),
        _part("o", "a", DAY + 1, {COMMENT: 2_000, ISSUE: 500}, part=gs.EARLY),
        _part("o", "a", DAY + 1, {COMMENT: 900}, part=gs.LATE),
        _part("p", "a", DAY + 1, {COMMENT: 7_000}, part=gs.LATE),
    ]
    v4 = gs.actor_days(parts, gs.V4_DAYS)
    assert {k: d.largest_message for k, d in v4.items()} == {
        ("o", "a", DAY): {COMMENT: 3_000},
        ("o", "a", DAY + 1): {COMMENT: 2_000, ISSUE: 500},
        ("p", "a", DAY + 1): {COMMENT: 7_000},
    }
    assert v4[("o", "a", DAY)].calls == {COMMENT: 4}  # 3 early calls and 1 late
    assert all(d.part is None for d in v4.values())
    # v5: 00:00-04:00 belongs to the day before. Of the range DAY..DAY+1 only DAY is whole.
    v5 = gs.actor_days(parts, gs.V5_DAYS)
    assert {k: d.largest_message for k, d in v5.items()} == {
        ("o", "a", DAY): {COMMENT: 3_000, ISSUE: 500}
    }
    wider = gs.actor_days(parts, gs.V5_DAYS, utc_days=range(DAY - 1, DAY + 3))
    whole_v5 = {("o", "a", DAY - 1), ("o", "a", DAY), ("o", "a", DAY + 1), ("p", "a", DAY + 1)}
    assert set(wider) == whole_v5
    holed = gs.actor_days(parts, gs.V5_DAYS, utc_days={DAY - 1, DAY, DAY + 2})
    assert set(holed) == {("o", "a", DAY - 1)}  # DAY and DAY + 1 touch the unread DAY + 1
    pooled = gs.actor_days(parts, gs.V4_DAYS, pooled=True)
    assert pooled[(gs.POOLED, "a", DAY + 1)].largest_message == {COMMENT: 7_000, ISSUE: 500}
    with pytest.raises(ValueError, match="parts"):
        gs.actor_days(list(v4.values()), gs.V4_DAYS)


# ── an event stream through the extractor equals derive_policy on every call ───────────────


def _sized(make: Callable[[str], dict], tool: str, target: int) -> dict:
    """The event ``make(body)`` whose message bytes are exactly ``target``."""
    base = gs.request_size(tool, gs.call_arguments(make(""), tool)).message_bytes
    made = make("x" * (target - base))
    assert gs.request_size(tool, gs.call_arguments(made, tool)).message_bytes == target
    return made


def _limit_events(seed: int = 7) -> list[dict]:
    """40 people of ORG_A and 6 of ORG_B over 40 days, each active on about half of them with
    1-4 calls, a quarter of the calls before 04:00 UTC. Sizes have a heavy tail (Pareto), so
    the quantiles depend on how calls fall into days. Every request's message bytes sit 20
    above a whole KB, so its argument bytes (about 90 fewer) sit below one: the two measures
    round to different KB. Pull requests are rare (under 50 agent-days: the fallback) and
    reviews come from one person (a borrowed v5 reference)."""
    rng = random.Random(seed)
    events = []
    for org, people in ((ORG_A, 40), (ORG_B, 6)):
        for i in range(people):
            login = f"{org}-dev-{i}"
            for day in range(LEARN_FROM, LEARN_FROM + 40):
                if rng.random() >= 0.5:
                    continue
                for _ in range(rng.randint(1, 4)):
                    early = rng.random() < 0.25
                    seconds = (
                        rng.randrange(int(gs.SPLIT_S))
                        if early
                        else rng.randrange(int(gs.SPLIT_S), int(DAY_S))
                    )
                    at = {"login": login, "org": org, "day": day, "seconds": seconds}
                    kb = min(MAX_REQUEST_KB, int(rng.paretovariate(SIZE_TAIL)))
                    target = kb * gs.KB + ABOVE_KB
                    kind = rng.random()
                    if kind < 0.02:
                        events.append(_sized(lambda b, at=at: _pull(b, **at), PULL, target))
                    elif kind < 0.35:
                        events.append(_sized(lambda b, at=at: issue("t", b, **at), ISSUE, target))
                    else:
                        events.append(_sized(lambda b, at=at: comment(b, **at), COMMENT, target))
                if i == 0 and org == ORG_A and day < LEARN_FROM + 20:
                    at = {"login": login, "org": org, "day": day, "seconds": 9 * HOUR}
                    events.append(
                        _sized(
                            lambda b, at=at: review(b, "approved", **at),
                            REVIEW,
                            5 * gs.KB + ABOVE_KB,
                        )
                    )
    return sorted(events, key=lambda e: e["created_at"])


def _pull(body: str, **kw) -> dict:
    payload = {
        "action": "opened",
        "pull_request": {"title": "p", "body": body, "head": {"ref": "f"}, "base": {"ref": "main"}},
    }
    return event("PullRequestEvent", payload, **kw)


def _raw_messages(events: list[dict], p: Pseudonymizer) -> dict[str, list[Message]]:
    """Organisation pseudonym -> one engine message per mapped call, as a gateway logs it."""
    out: dict[str, list[Message]] = defaultdict(list)
    for e in events:
        tool = gs.mapped_tool(e)
        size = gs.request_size(tool, gs.call_arguments(e, tool))
        out[gs.pseudonym(p, gs.ORG_ROLE, e["org"]["login"])].append(
            Message(
                ts=gs.event_time(e),
                agent=gs.pseudonym(p, gs.ACTOR_ROLE, e["actor"]["login"]),
                method=CALL_METHOD,
                tool=tool,
                operation=WRITE,
                size=size.message_bytes,
                arg_bytes=size.arg_bytes,
                outcome=ACCEPTED,
                zone="UTC",
            )
        )
    return out


def _learning(messages: list[Message], config: BehaviourConfig) -> list[Message]:
    window = range(LEARN_FROM, LEARN_FROM + gs.LEARN_DAYS)
    return [m for m in messages if policy.learning_day(m.ts, m.zone, config) in window]


@pytest.fixture(scope="module")
def limit_world() -> tuple[list[gs.RequestDay], dict[str, list[Message]]]:
    p = pseudo()
    events = _limit_events()
    return list(gs.extract_requests(events, p).parts.values()), _raw_messages(events, p)


def test_v4_limits_equal_derive_policy_on_every_call(limit_world) -> None:
    parts, raw = limit_world
    cfg4 = BehaviourConfig()
    learned = gs.learn_v4_limits(parts, LEARN_FROM)
    big = gs.pseudonym(pseudo(), gs.ORG_ROLE, ORG_A)
    assert learned[big].learning_days >= 500  # q0.995 is not the sample maximum
    assert set(learned[big].by_tool) == {COMMENT, ISSUE}  # pulls and reviews: the fallback
    for org, messages in raw.items():
        want = policy.derive_policy(_learning(messages, cfg4), cfg4)
        assert dict(learned[org].by_tool) == want.request_limit_by_tool
        assert learned[org].fallback == want.request_limit_bytes
        assert (learned[org].design, learned[org].actors) == (gs.V4, 40 if org == big else 6)
    # The fixture tells the measures and the day conventions apart.
    on_args = [replace(m, size=m.arg_bytes) for m in raw[big]]
    assert policy.derive_policy(_learning(on_args, cfg4), cfg4).request_limit_by_tool != dict(
        learned[big].by_tool
    )
    v5_days = gs.actor_days(parts, gs.V5_DAYS).values()
    v5_rows = [d for d in v5_days if d.org == big and d.day < LEARN_FROM + gs.LEARN_DAYS]
    other = policy.derive_policy(gs.policy_messages(v5_rows), cfg4)
    assert other.request_limit_by_tool != dict(learned[big].by_tool)


def test_v5_lines_equal_derive_policy_on_every_call_with_v5_days(limit_world) -> None:
    parts, raw = limit_world
    cfg5 = BehaviourConfig(design="v5")
    learned = gs.learn_v5_limits(parts, LEARN_FROM)
    big, small = (gs.pseudonym(pseudo(), gs.ORG_ROLE, org) for org in (ORG_A, ORG_B))
    want = policy.derive_policy(_learning(raw[big], cfg5), cfg5)
    lines = learned.limits[big]
    assert dict(lines.by_tool) == want.request_limit_by_tool
    assert lines.fallback == want.request_limit_bytes
    assert lines.design == gs.V5
    calls = policy.learned_calls(_learning(raw[big], cfg5), cfg5)
    direct = policy.request_lines(policy.agent_days(calls, cfg5), policy.operation_classes(calls))
    assert lines.learning_days == direct.days
    # The small organisation cannot learn a line: it is reported, not given the default.
    assert small not in learned.limits
    small_calls = policy.learned_calls(_learning(raw[small], cfg5), cfg5)
    assert learned.not_learned == {small: len(policy.agent_days(small_calls, cfg5))}
    # UTC-midnight days (v4's key) give another line on this fixture.
    midnight = BehaviourConfig(design="v5", day_start_hour=0.0)
    utc_line = policy.derive_policy(_learning(raw[big], midnight), midnight)
    assert utc_line.request_limit_by_tool != dict(lines.by_tool)
    with pytest.raises(ValueError):
        gs.learn_v5_limits(parts, LEARN_FROM, base=midnight)
    with pytest.raises(ValueError):
        gs.learn_v5_limits(parts, LEARN_FROM, base=BehaviourConfig())


def test_rates_count_each_designs_agent_days_against_its_measure(limit_world) -> None:
    parts, raw = limit_world
    big = gs.pseudonym(pseudo(), gs.ORG_ROLE, ORG_A)
    eval_from = LEARN_FROM + gs.LEARN_DAYS
    for design, limits in (
        (gs.V4, gs.learn_v4_limits(parts, LEARN_FROM)),
        (gs.V5, gs.learn_v5_limits(parts, LEARN_FROM).limits),
    ):
        config = BehaviourConfig(design=design)
        over: dict[tuple[str, int], bool] = {}
        for m in raw[big]:
            day = policy.learning_day(m.ts, m.zone, config)
            if day < eval_from or (design == gs.V5 and day == LEARN_FROM + 39):
                continue  # v5's last day lacks its next morning: incomplete
            size = m.size if design == gs.V4 else m.arg_bytes
            key = (m.agent, day)
            over[key] = over.get(key, False) or size > limits[big].limit(m.tool)
        rate = gs.oversized_rates(parts, limits, eval_from)[big][gs.ALL_CLASSES]
        assert (rate.raised, rate.active, rate.actors) == (
            sum(over.values()),
            len(over),
            len({who for who, _ in over}),
        )


# ── v4 limits: boundaries ──────────────────────────────────────────────────────────────────


def test_v4_learning_window_and_tool_minimum_boundaries() -> None:
    rows = [_part("o", f"a{i}", LEARN_FROM + i % 29, {COMMENT: 1_500}) for i in range(60)]
    rows.append(_part("o", "late", LEARN_FROM + gs.LEARN_DAYS - 1, {COMMENT: 9_500}))
    rows.append(_part("o", "later", LEARN_FROM + gs.LEARN_DAYS, {COMMENT: 50_000}))
    rows += [
        _part("o", f"i{i}", LEARN_FROM + i % 29, {ISSUE: 700}) for i in range(gs.MIN_TOOL_DAYS)
    ]
    rows += [_part("o", f"p{i}", LEARN_FROM, {PULL: 300}) for i in range(gs.MIN_TOOL_DAYS - 1)]
    (limits,) = gs.learn_v4_limits(rows, LEARN_FROM).values()
    # Day learn_from + 29 is learned (its 9.5 KB is the maximum), learn_from + 30 is not.
    assert limits.by_tool[COMMENT] == 10_000
    assert limits.by_tool[ISSUE] == 1_000  # 50 agent-days: its own limit
    assert PULL not in limits.by_tool  # 49: the fallback
    assert limits.limit(PULL) == limits.fallback == 10_000


def test_v4_fallback_is_the_quantile_of_each_days_largest_request() -> None:
    # Day i holds a comment of (i + 1) KB + 1 and a 100-byte issue. The days' largest requests
    # put the fallback at the 199th of 200 comments; all 400 values would put it one lower.
    rows = [
        _part("o", f"a{i}", LEARN_FROM + i % 30, {COMMENT: (i + 1) * gs.KB + 1, ISSUE: 100})
        for i in range(200)
    ]
    (limits,) = gs.learn_v4_limits(rows, LEARN_FROM).values()
    assert limits.fallback == 200 * gs.KB
    every_value = [v for r in rows for v in r.largest_message.values()]
    assert gs.whole_kb(gs.nearest_rank(every_value, gs.QUANTILE)) == 199 * gs.KB


def test_pooled_limits_merge_an_actor_across_organisations() -> None:
    rows = [_part("o1", f"a{i}", LEARN_FROM + i % 30, {COMMENT: 1_000 + i}) for i in range(60)]
    rows += [_part("o2", f"a{i}", LEARN_FROM + i % 30, {COMMENT: 30_000}) for i in range(60)]
    pooled = gs.learn_v4_limits(rows, LEARN_FROM, pooled=True)[gs.POOLED]
    assert pooled.learning_days == 60  # each actor's two organisations make one agent-day
    assert pooled.by_tool[COMMENT] == 30_000
    per_org = gs.learn_v4_limits(rows, LEARN_FROM)
    assert per_org["o1"].by_tool[COMMENT] == 2_000 and per_org["o1"].learning_days == 60


def test_oversized_rate_rule_and_evaluation_boundary() -> None:
    limit = gs.RouteLimits({COMMENT: 2_000}, fallback=1_000, learning_days=60)
    eval_day = LEARN_FROM + gs.LEARN_DAYS
    rows = [
        _part("o", "a", eval_day, {COMMENT: 2_001}),  # over its tool's limit
        _part("o", "b", eval_day, {COMMENT: 2_000}),  # at the limit: not over
        _part("o", "c", eval_day, {ISSUE: 1_001}),  # over the fallback
        _part("o", "d", eval_day, {ISSUE: 50_000}, cls=gs.BOT),
        _part("o", "e", eval_day - 1, {ISSUE: 50_000}),  # a learning day
        _part("unlearned", "f", eval_day, {ISSUE: 50_000}),
    ]
    rates = gs.oversized_rates(rows, {"o": limit}, eval_day)
    assert set(rates) == {"o"}
    assert rates["o"][gs.ALL_CLASSES] == gs.OversizedRate(3, 4, 4)
    assert rates["o"][gs.PERSON] == gs.OversizedRate(2, 3, 3)
    assert rates["o"][gs.BOT].rate == 1.0
    # v5 limits hold argument bytes (100 fewer here): only the bot's day is over.
    v5 = gs.RouteLimits({COMMENT: 2_000}, 1_000, 60, design=gs.V5)
    by_args = gs.oversized_rates(rows, {"o": v5}, eval_day, utc_days=range(DAY, eval_day + 2))
    assert by_args["o"][gs.ALL_CLASSES] == gs.OversizedRate(1, 4, 4)
    with pytest.raises(ValueError):
        gs.oversized_rates(rows, {"o": limit, "p": v5}, eval_day)


def test_policy_messages_take_whole_days_at_noon() -> None:
    whole = gs.actor_days([_part("o", "a", DAY, {ISSUE: 900})], gs.V4_DAYS).values()
    (message,) = gs.policy_messages(whole)
    assert message.ts == DAY * DAY_S + DAY_S / 2
    assert int(message.ts // DAY_S) == DAY == local_day(message.ts, message.zone, 4.0)
    assert (message.size, message.arg_bytes, message.outcome) == (900, 800, ACCEPTED)
    with pytest.raises(ValueError, match="whole days"):
        gs.policy_messages([_part("o", "a", DAY, {ISSUE: 900})])


def test_v5_learns_only_with_enough_agent_days() -> None:
    def rows(org: str, actors: int, days: int) -> list[gs.RequestDay]:
        return [
            _part(org, f"{org}-{a}", LEARN_FROM + d, {COMMENT: 1_000 + 37 * a + 11 * d})
            for a in range(actors)
            for d in range(days)
        ]

    parts = rows("small", 10, 15) + rows("big", 30, 10)
    read = range(LEARN_FROM, LEARN_FROM + gs.LEARN_DAYS + 1)
    learned = gs.learn_v5_limits(parts, LEARN_FROM, utc_days=read)
    assert learned.not_learned == {"small": 150}  # under policy.MIN_LINE_DAYS
    assert set(learned.limits) == {"big"}
    cfg5 = BehaviourConfig(design="v5")
    days = [d for d in gs.actor_days(parts, gs.V5_DAYS, utc_days=read).values() if d.org == "big"]
    calls = policy.learned_calls(gs.policy_messages(days), cfg5)
    direct = policy.request_lines(policy.agent_days(calls, cfg5), policy.operation_classes(calls))
    assert learned.limits["big"].learning_days == direct.days < 300  # the top identity left out
    assert learned.limits["big"].by_tool == direct.limits
    assert learned.limits["big"].fallback == direct.fallback


# ── the summary ────────────────────────────────────────────────────────────────────────────


def test_summarise_suppresses_routes_and_cells_of_few_actors() -> None:
    rows = []
    for org, people, bots in (("ten", 10, 0), ("nine", 8, 1)):
        for i in range(people + bots):
            cls = gs.BOT if i >= people else gs.PERSON
            actor = f"{org}-{i}"
            rows += [_part(org, actor, LEARN_FROM + d, {COMMENT: 2_000}, cls) for d in (0, 1)]
            rows.append(_part(org, actor, LEARN_FROM + gs.LEARN_DAYS, {COMMENT: 50_000}, cls))
    extract = gs.RequestExtract(utc_days=set(range(LEARN_FROM, LEARN_FROM + gs.LEARN_DAYS + 1)))
    extract.parts = {r.key: r for r in rows}
    summary = gs.summarise(extract, LEARN_FROM)
    v4 = summary[gs.V4]
    assert v4["limits"]["nine"] == {"suppressed": True}  # 8 people and a bot
    assert v4["limits"]["ten"] == {"by_tool": {}, "fallback": 2_000, "learning_days": 20}
    assert v4["rates"]["ten"][gs.PERSON] == {"raised": 10, "active": 10, "rate": 1.0}
    suppressed = {"suppressed": True}
    assert v4["rates"]["nine"] == {c: suppressed for c in (gs.ALL_CLASSES, gs.BOT, gs.PERSON)}
    assert v4["total"][gs.PERSON] == {"raised": 18, "active": 18, "rate": 1.0}
    assert v4["total"][gs.BOT] == suppressed
    assert v4["total"][gs.ALL_CLASSES]["active"] == 19
    assert v4["procedure"] == gs.PROCEDURES[gs.V4] and v4["measure"] == gs.MESSAGE_BYTES
    # v5: neither route has the agent-days for a line: they are counted, not named, and no v5
    # rate is measured against a written default.
    assert summary[gs.V5]["not_learned"] == {"routes": 2, "agent_days": 38}
    assert summary[gs.V5]["limits"] == {} and summary[gs.V5]["rates"] == {}
    assert summary["caller_key"] == gs.CALLER_KEY and summary["label"] == gs.LABEL
    assert summary["utc_days"]["missing"] == []
    holed = gs.RequestExtract(utc_days={LEARN_FROM, LEARN_FROM + 2})
    assert gs.summarise(holed)["utc_days"]["missing"] == [gs.iso_day(LEARN_FROM + 1)]


# ── organisation selection ─────────────────────────────────────────────────────────────────


def test_select_orgs_takes_the_top_and_a_seeded_draw_in_range() -> None:
    people = {f"big-{i}": 1_000 - i for i in range(3)} | {"tie-ba": 500, "tie-ab": 500}
    people |= {f"mid-{i:02d}": 20 + i * 10 for i in range(20)} | {"tiny": 3, "huge": 5_000}
    people |= {"edge-low": 20, "edge-high": 200, "edge-out": 201, "edge-under": 19}
    picked = gs.select_orgs(people, top=4, drawn=5, seed=1)
    assert picked.top == ("huge", "big-0", "big-1", "big-2")
    assert picked == gs.select_orgs(people, top=4, drawn=5, seed=1)
    assert len(picked.drawn) == 5
    assert all(20 <= people[o] <= 200 for o in picked.drawn)
    assert gs.select_orgs(people, top=4, drawn=5, seed=2).drawn != picked.drawn
    ties = gs.select_orgs(people, top=6, drawn=0)
    assert ties.top[-2:] == ("tie-ab", "tie-ba")  # ties: the smaller pseudonym first
    everyone = gs.select_orgs(people, top=6, drawn=100)
    assert {"edge-low", "edge-high"} <= set(everyone.drawn)  # 20 and 200 are in range
    assert not {"edge-out", "edge-under", "tiny"} & set(everyone.drawn)
    excluded = gs.select_orgs(people, top=1, drawn=50, exclude={"huge", "mid-00"})
    assert excluded.top == ("big-0",)
    assert "mid-00" not in excluded.drawn and len(excluded.drawn) == 20  # 18 mids + 2 edges


def test_a_selection_is_tied_to_its_key(tmp_path: Path) -> None:
    selection = gs.select_orgs({"org-x": 50}, top=1, drawn=0)
    path = tmp_path / "selection.json"
    gs.write_json(path, selection.to_json(gs.key_check(pseudo())))
    assert gs.load_org_selection(path, pseudo()) == frozenset({"org-x"})
    with pytest.raises(gs.SelectionKeyError):
        gs.load_org_selection(path, pseudo(OTHER_KEY))


# ── quantiles and the size bank (EV-14) ────────────────────────────────────────────────────


def test_size_quantiles_are_nearest_rank_and_small_cells_are_suppressed() -> None:
    rng = random.Random(11)
    sizes = [rng.randint(100, 9_000) for _ in range(500)]
    hist = gs._histograms()
    hist[gs.ARG_BYTES][gs.PERSON][ISSUE].update(sizes)
    hist[gs.ARG_BYTES][gs.BOT][ISSUE].update([5] * (gs.MIN_PUBLISH_CALLS - 1))
    hist[gs.ARG_BYTES][gs.AGENT][ISSUE].update([6] * gs.MIN_PUBLISH_CALLS)
    table = gs.size_quantiles(hist)[gs.ARG_BYTES]
    cell = table[gs.PERSON][ISSUE]
    for q in gs.QUANTILES:
        # Nearest rank, by definition: the smallest size with at least q of the calls at or below.
        expected = min(v for v in sizes if sum(x <= v for x in sizes) >= q * len(sizes))
        assert cell[f"q{q}"] == gs.nearest_rank(sizes, q) == expected
    assert table[gs.BOT][ISSUE] == {"calls": gs.MIN_PUBLISH_CALLS - 1, "suppressed": True}
    assert table[gs.AGENT][ISSUE]["q0.5"] == 6
    assert table[gs.ALL_CLASSES][ISSUE]["calls"] == 500 + 2 * gs.MIN_PUBLISH_CALLS - 1


def test_quantiles_need_q_in_the_unit_interval() -> None:
    assert gs.nearest_rank([3, 1, 2], 1.0) == gs.histogram_quantile({1: 1, 2: 1, 3: 1}, 1.0) == 3
    assert gs.nearest_rank([3, 1, 2], 0.01) == gs.histogram_quantile({1: 1, 2: 1, 3: 1}, 0.01)
    for q in (0.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            gs.nearest_rank([1, 2], q)
        with pytest.raises(ValueError):
            gs.histogram_quantile({1: 2}, q)


def test_size_bank_is_the_histogram_and_sampling_is_deterministic() -> None:
    rng = random.Random(13)
    sizes = [int(250 + rng.lognormvariate(6.4, 1.0)) for _ in range(CALLS_PER_SIZE_BANK)]
    hist = gs._histograms()
    hist[gs.ARG_BYTES][gs.PERSON][COMMENT].update(sizes)
    bank = gs.SizeBank.from_histograms(hist)
    total = bank.total(COMMENT)
    # The inverse distribution function at evenly spaced points gives back the bank exactly.
    exact = [bank.size_at(COMMENT, (i + 0.5) / total) for i in range(total)]
    assert sorted(exact) == sorted(sizes)
    for q in (0.5, 0.9, 0.99):
        assert bank.quantile(COMMENT, q) == gs.nearest_rank(sizes, q)
    draws = [bank.sample(COMMENT, random.Random(7)) for _ in range(3)]
    assert len(set(draws)) == 1  # the same seed, the same draw
    stream = random.Random(21)
    many = [bank.sample(COMMENT, stream) for _ in range(20_000)]
    for q in (0.5, 0.9, 0.99):  # within 1% of the bank's own quantile levels
        line = bank.quantile(COMMENT, q)
        assert abs(sum(s <= line for s in many) / len(many) - q) <= 0.01
    saved = bank.to_json()
    assert saved["measure_note"] == gs.MEASURE_NOTES[gs.ARG_BYTES]
    assert gs.SizeBank.from_json(json.loads(json.dumps(saved))) == bank
    with pytest.raises(ValueError):
        bank.size_at(COMMENT, 1.0)


# ── the command line, end to end ───────────────────────────────────────────────────────────


def test_command_line_stages_end_to_end(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    events = [comment(f"c{i}", login=f"{PERSON_A}{i}", seconds=60 * i) for i in range(30)]
    events += [comment("bot says", login=BOT_A), comment("b", login=PERSON_B, org=ORG_B)]
    hour = write_gz(raw / "2025-01-04-0.json.gz", [json.dumps(e) for e in events])
    before = write_gz(
        raw / "2025-01-03-23.json.gz",
        [json.dumps(comment("prev", day=DAY - 1, seconds=DAY_S - 600))],
    )
    out = tmp_path / "out"
    module_args = [str(hour)]
    day_args = ["--day", "2025-01-04"]

    monkeypatch.delenv(gs.KEY_ENV, raising=False)
    with pytest.raises(gs.PseudonymKeyError):
        gs.main(["extract", *day_args, "--out", str(out / "x.json.gz"), *module_args])
    assert not (out / "x.json.gz").exists()

    monkeypatch.setenv(gs.KEY_ENV, KEY)
    gs.main(["orgs", "--out", str(out / "orgs.json.gz"), *module_args])
    select = ["select-orgs", "--top", "1", "--random", "0", "--out", str(out / "sel.json")]
    gs.main([*select, str(out / "orgs.json.gz")])
    gs.main(
        [
            "extract",
            *day_args,
            "--orgs",
            str(out / "sel.json"),
            "--out",
            str(out / "sizes.json.gz"),
            *module_args,
        ]
    )
    gs.main(
        [
            "summarise",
            "--learn-from",
            "2025-01-04",
            "--bank",
            str(out / "bank.json"),
            "--out",
            str(out / "summary.json"),
            str(out / "sizes.json.gz"),
        ]
    )
    cad.main(
        [
            "extract",
            *day_args,
            "--orgs",
            str(out / "sel.json"),
            "--lookback",
            str(before),
            "--out",
            str(out / "cadence.json.gz"),
            *module_args,
        ]
    )
    cad.main(
        ["summarise", "--out", str(out / "cadence_summary.json"), str(out / "cadence.json.gz")]
    )
    cad.main(
        [
            "summarise",
            "--days",
            gs.V4_DAYS,
            "--out",
            str(out / "cadence_v4.json"),
            str(out / "cadence.json.gz"),
        ]
    )

    selection = gs.read_json(out / "sel.json")
    assert len(selection["top"]) == 1 and selection["people"] == {selection["top"][0]: 30}
    assert selection["key_check"] == gs.key_check(pseudo())
    summary = gs.read_json(out / "summary.json")
    assert summary["quantiles"][gs.ARG_BYTES][gs.PERSON][COMMENT]["calls"] == 30
    assert summary["stats"]["other_org"] == 1
    assert summary["utc_days"] == {"first": "2025-01-04", "last": "2025-01-04", "missing": []}
    bank = gs.SizeBank.from_json(gs.read_json(out / "bank.json"))
    assert bank.total(COMMENT) == 31
    cadence = gs.read_json(out / "cadence.json.gz")
    assert len(cadence["parts"]) == 31
    assert cadence["files_read"] == sorted([hour.name, before.name])
    # A single UTC day holds no whole v5 day, but one whole v4 day.
    v5_cells = gs.read_json(out / "cadence_summary.json")["cells"]
    assert v5_cells[gs.PERSON][cad.ALL_DAYS] == {"suppressed": True}
    v4_summary = gs.read_json(out / "cadence_v4.json")
    assert v4_summary["cells"][gs.PERSON][cad.ALL_DAYS]["actors"] == 30
    assert v4_summary["convention"] == gs.V4_DAYS
    assert v4_summary["utc_days"] == {"first": "2025-01-04", "last": "2025-01-04", "missing": []}
    for path in sorted(out.iterdir()):
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        assert_no_identities(data.decode())
        assert not path.name.endswith(".part")

    # The same selection under a new key matches nothing: extraction refuses it.
    monkeypatch.setenv(gs.KEY_ENV, OTHER_KEY)
    refused = ["extract", *day_args, "--orgs", str(out / "sel.json"), "--out"]
    with pytest.raises(gs.SelectionKeyError):
        gs.main([*refused, str(tmp_path / "refused.json.gz"), *module_args])
    with pytest.raises(gs.SelectionKeyError):
        cad.main([*refused, str(tmp_path / "refused.json.gz"), *module_args])
    assert not (tmp_path / "refused.json.gz").exists()
    gs.main(["orgs", "--out", str(out / "orgs2.json.gz"), *module_args])
    with pytest.raises(gs.SelectionKeyError):
        gs.main([*select, str(out / "orgs.json.gz"), str(out / "orgs2.json.gz")])
    with pytest.raises(gs.SelectionKeyError):
        gs.main([*select, "--exclude", str(out / "sel.json"), str(out / "orgs2.json.gz")])


# ── the SLURM script's refusals (bash only, before any Python step runs) ───────────────────


def _run_sbatch(tmp_path: Path, *args: str, task: int | None = None) -> subprocess.CompletedProcess:
    """Run the script with bash against a stand-in repository and work folder in tmp_path."""
    repo = tmp_path / "repo"
    heldout = repo / "reports" / "experiments" / "dynamic_dimensions" / "heldout"
    heldout.mkdir(parents=True, exist_ok=True)
    (repo / "pyproject.toml").touch()
    env = {
        "PATH": os.environ.get("PATH", ""),
        "REPO": str(repo),
        "GHA_ROOT": str(tmp_path / "gha"),
        "PY": sys.executable,
    }
    if task is not None:
        env["SLURM_ARRAY_TASK_ID"] = str(task)
    return subprocess.run(
        ["bash", str(SBATCH), *args], env=env, capture_output=True, text=True, check=False
    )


def _download_stand_in(gha: Path, day: str, previous: str) -> Path:
    """24 hourly files of ``day`` and its lookback hour, as the download step leaves them."""
    folder = gha / "raw" / day
    (folder / "lookback").mkdir(parents=True)
    for hour in range(24):
        write_gz(folder / f"{day}-{hour}.json.gz", [json.dumps(comment("x"))])
    write_gz(folder / "lookback" / f"{previous}-23.json.gz", [json.dumps(comment("y"))])
    (gha / "pseudonym.key").write_text("k" * 64)
    (gha / "selection.json").write_text("{}")
    return folder


needs_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


@needs_bash
def test_sbatch_refuses_partial_days(tmp_path: Path) -> None:
    day, previous = "2025-01-06", "2025-01-05"
    folder = _download_stand_in(tmp_path / "gha", day, previous)
    (folder / "MISSING").write_text(f"{day}-13.json.gz\n")
    done = _run_sbatch(tmp_path, "orgs", day, task=0)
    assert done.returncode == 1 and "MISSING" in done.stderr
    (folder / "MISSING").unlink()
    (folder / f"{day}-13.json.gz").unlink()
    done = _run_sbatch(tmp_path, "extract", day, task=0)
    assert done.returncode == 1 and f"{day}-13.json.gz" in done.stderr
    write_gz(folder / f"{day}-13.json.gz", [json.dumps(comment("x"))])
    (folder / "lookback" / f"{previous}-23.json.gz").unlink()
    done = _run_sbatch(tmp_path, "extract", day, task=0)
    assert done.returncode == 1 and "lookback" in done.stderr


@needs_bash
def test_sbatch_key_refuses_an_earlier_runs_files(tmp_path: Path) -> None:
    gha = tmp_path / "gha"
    gha.mkdir()
    (gha / "selection.json").write_text("{}")
    done = _run_sbatch(tmp_path, "key")
    assert done.returncode == 1 and "earlier key" in done.stderr
    (gha / "selection.json").unlink()
    (gha / "sizes").mkdir()
    (gha / "sizes" / "2025-01-06.json.gz").write_bytes(b"")
    done = _run_sbatch(tmp_path, "key")
    assert done.returncode == 1 and "earlier key" in done.stderr
    shutil.rmtree(gha / "sizes")
    done = _run_sbatch(tmp_path, "key")
    assert done.returncode == 0, done.stderr
    key = gha / "pseudonym.key"
    assert len(key.read_text().strip()) == 64 and key.stat().st_mode & 0o777 == 0o600
    done = _run_sbatch(tmp_path, "key")
    assert done.returncode == 1 and "already exists" in done.stderr
