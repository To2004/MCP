"""v5's wire log (``gateway/wire_log.py``): B3, the LOG-1 and ARG-1 fields on a v5 route's
lines and never on a v1-v4 route's, the GW-1 verdict line, and the bounded session book (E9,
DEP-5). Every caller, token and session here is synthetic.

B3 follows the author's decision of 2026-10-27 (spec 2.9, D5): history is kept per agent, so
the identity strength says which key a call's history is under, not whose token it is.
"""

from __future__ import annotations

import inspect
import json
import math
from dataclasses import replace
from typing import Any

import pytest

from mcp_security.behaviour.engine import ACCEPTED, LEGACY_ERA, MODERN_ERA, REJECTED
from mcp_security.gateway.config import NO_AUTH as CONFIG_NO_AUTH
from mcp_security.gateway.http_wire import UNPARSED_JSON, unparsed_verdict
from mcp_security.gateway.protocol_era import (
    ISSUE_HEADER_METHOD,
    ISSUE_HEADER_NAME,
    META_CAPABILITIES,
    META_PROTOCOL,
    MODERN_FROM,
    LogicalCalls,
    argument_bytes,
    json_bytes,
)
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import (
    ARG_BYTES_FIELD,
    FROM_GATEWAY,
    IDENTITY_NONE,
    IDENTITY_SERVICE,
    IDENTITY_STRENGTH_FIELD,
    IDENTITY_USER,
    LOG1_FIELDS,
    LOGICAL_CALL_FIELD,
    MAX_SESSION_OWNERS,
    MAX_SESSIONS_PER_CALLER,
    NO_AUTH,
    OUTCOME_FIELD,
    PROTOCOL_ERA_FIELD,
    PROTOCOL_ISSUES_FIELD,
    REFUSED_FIELD,
    REPLY_BYTES_FIELD,
    REPLY_WIRE_BYTES_FIELD,
    SESSION_BOOK_FORMAT,
    SESSION_TTL_S,
    TO_AGENT,
    TO_SERVER,
    UNPARSED,
    UNPARSED_REASON_FIELD,
    V5_CALL_FIELDS,
    WARN,
    BoundedSessionBook,
    Exchange,
    LogPolicy,
    SessionBook,
    build_record,
    decision_record,
    identity_strength,
    notice_record,
    reply_facts,
    unparsed_record,
    with_v5_facts,
)
from mcp_security.gateway.wire_log import META_CLIENT as WIRE_META_CLIENT
from mcp_security.gateway.wire_log import META_PROTOCOL as WIRE_META_PROTOCOL

T0 = 1_780_000_000.0
ARGS = {"owner": "acme", "repo": "repo-a", "path": "README.md"}
CONTENT = [{"type": "text", "text": "hello " * 50}]
V4, V5 = LogPolicy(), LogPolicy(v5=True)
V5_ONLY = {*LOG1_FIELDS, *V5_CALL_FIELDS, IDENTITY_STRENGTH_FIELD}
MODERN_HEADERS = {
    "MCP-Protocol-Version": MODERN_FROM,
    "Mcp-Method": "tools/call",
    "Mcp-Name": "get_file_contents",
}
SESSIONS_FLOOD = 1_000_000
#: Enough callers that their quotas together (128,000) pass the route's default bound.
FLOOD_CALLERS = 2_000
FLOOD_STEP_S = 0.01  # 10^6 sessions over about 2.8 hours


class _Clock:
    """A settable clock for the session book."""

    def __init__(self, now: float = T0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _call(rpc_id: Any = 1, modern: bool = True, args: dict | None = None) -> dict:
    params: dict = {"name": "get_file_contents", "arguments": ARGS if args is None else args}
    if modern:
        params["_meta"] = {META_PROTOCOL: MODERN_FROM, META_CAPABILITIES: {}}
    return {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/call", "params": params}


def _exchange(**fields: Any) -> Exchange:
    who = {
        "agent": "claude-code",
        "agent_id": "agt-0001",
        "user": "user-0001",
        "app": "claude-code",
        "auth": "oauth",
        "issuer": "https://idp.example",
    }
    who.update(fields)
    return Exchange(route="github", session=None, http_method="POST", **who)


def _v5_exchange(
    messages: list[dict], headers: dict | None = None, calls: LogicalCalls | None = None, **f: Any
) -> Exchange:
    base = _exchange(requests={"1": ("tools/call", "get_file_contents")}, received=T0, **f)
    return with_v5_facts(
        base,
        MODERN_HEADERS if headers is None else headers,
        messages,
        LogicalCalls() if calls is None else calls,
    )


def test_the_meta_keys_are_still_exported_by_the_wire_log() -> None:
    assert (WIRE_META_PROTOCOL, WIRE_META_CLIENT) == (
        "io.modelcontextprotocol/protocolVersion",
        "io.modelcontextprotocol/clientInfo",
    )
    assert NO_AUTH == CONFIG_NO_AUTH


def test_a_v4_route_writes_no_v5_field_whatever_the_exchange_carries() -> None:
    """INF-3: v1-v4 lines never change. The exchange carries every v5 fact; the policy is off."""
    exchange = _v5_exchange([_call()], headers={}, baseline_key="bk", zone="Europe/Berlin")
    exchange = replace(exchange, reply_wire_bytes=999)
    reply = {"jsonrpc": "2.0", "id": 1, "result": {"content": CONTENT}}
    lines = [
        build_record(exchange, SessionBook(), TO_SERVER, None, _call(), V4),
        build_record(exchange, SessionBook(), TO_AGENT, 200, reply, V4),
        build_record(exchange, SessionBook(), TO_AGENT, 405, None, V4),
        decision_record(exchange, SessionBook(), _call(), {"risk": 1.0}, None, T0, V4),
        notice_record(exchange, "session_agent_mismatch", V4),
    ]
    plain = replace(exchange, **_V5_EXCHANGE_EMPTY)
    again = [
        build_record(plain, SessionBook(), TO_SERVER, None, _call(), V4),
        build_record(plain, SessionBook(), TO_AGENT, 200, reply, V4),
        build_record(plain, SessionBook(), TO_AGENT, 405, None, V4),
        decision_record(plain, SessionBook(), _call(), {"risk": 1.0}, None, T0, V4),
        notice_record(plain, "session_agent_mismatch", V4),
    ]
    for line, same in zip(lines, again, strict=True):
        assert not V5_ONLY & set(line)
        assert _untimed(line) == _untimed(same)
    assert lines[0]["log.level"] == "info"  # issues never raise a v4 line's level


#: Every v5 field of an exchange, empty: what a v1-v4 route's exchange carries.
_V5_EXCHANGE_EMPTY = {
    "era": None,
    "protocol_issues": (),
    "reply_wire_bytes": None,
    "calls": {},
    "baseline_key": None,
    "zone": None,
}


def _untimed(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in ("ts", "gateway.duration_s")}


def test_v5_facts_for_a_modern_call() -> None:
    exchange = _v5_exchange([_call()])
    assert (exchange.era, exchange.protocol_issues) == (MODERN_ERA, ())
    facts = exchange.call_facts({"id": 1})
    assert facts.arg_bytes == argument_bytes(_call()) == json_bytes(ARGS)
    assert facts.logical_call == f"{exchange.id}/1"
    assert (facts.reply_bytes, facts.outcome) == (None, None)


def test_v5_facts_for_a_legacy_batch_keep_only_scored_requests() -> None:
    notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    listing = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    exchange = _v5_exchange([notification, _call(modern=False), listing], headers={})
    assert (exchange.era, exchange.protocol_issues) == (LEGACY_ERA, ())
    assert set(exchange.calls) == {"1"}


def test_a_retry_of_a_rejected_call_shares_its_logical_call_across_exchanges() -> None:
    calls = LogicalCalls()
    modern = _v5_exchange([_call()], calls=calls, id="ex-1")
    rejected = reply_facts(modern, 400, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602}})
    assert rejected is not None and rejected.outcome == REJECTED
    calls.answered(rejected.logical_call, rejected.outcome, None, T0 + 0.1)
    legacy = with_v5_facts(
        _exchange(received=T0 + 1, id="ex-2"), {}, [_call(rpc_id=7, modern=False)], calls
    )
    assert legacy.era == LEGACY_ERA
    assert legacy.call_facts({"id": 7}).logical_call == "ex-1/1"


def test_a_v5_request_line_carries_era_issues_sizes_and_logical_call() -> None:
    headers = {"MCP-Protocol-Version": MODERN_FROM}  # no Mcp-Method, no Mcp-Name
    exchange = _v5_exchange([_call()], headers=headers, baseline_key="bk-1", zone="Asia/Jerusalem")
    line = build_record(exchange, SessionBook(), TO_SERVER, None, _call(), V5)
    assert line[PROTOCOL_ERA_FIELD] == MODERN_ERA
    assert line[PROTOCOL_ISSUES_FIELD] == [ISSUE_HEADER_METHOD, ISSUE_HEADER_NAME]
    assert line["log.level"] == WARN
    assert line[ARG_BYTES_FIELD] == json_bytes(ARGS)
    assert line[LOGICAL_CALL_FIELD] == exchange.call_facts({"id": 1}).logical_call
    assert (line["gateway.baseline_key"], line["gateway.zone"]) == ("bk-1", "Asia/Jerusalem")
    assert line[IDENTITY_STRENGTH_FIELD] == IDENTITY_USER  # "bk-1" is not the agent's key
    assert line["gateway.message_bytes"] > line[ARG_BYTES_FIELD]  # the envelope is not counted


def test_a_conforming_v5_request_line_stays_info_with_no_issue_field() -> None:
    exchange = _v5_exchange([_call()])
    line = build_record(exchange, SessionBook(), TO_SERVER, None, _call(), V5)
    assert line["log.level"] == "info" and PROTOCOL_ISSUES_FIELD not in line


@pytest.mark.parametrize(
    ("status", "reply", "outcome", "reply_bytes"),
    [
        (200, {"jsonrpc": "2.0", "id": 1, "result": {"content": CONTENT}}, ACCEPTED, True),
        (200, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602}}, REJECTED, False),
        (400, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32022}}, REJECTED, False),
        # The status rejects though the body alone would not: a reply line reads both.
        (404, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603}}, REJECTED, False),
        (405, {"jsonrpc": "2.0", "id": 1, "result": {"content": CONTENT}}, REJECTED, True),
    ],
)
def test_a_v5_reply_line_carries_its_size_logical_call_and_outcome(
    status: int, reply: dict, outcome: str, reply_bytes: bool
) -> None:
    exchange = _v5_exchange([_call()])
    exchange = replace(exchange, reply_wire_bytes=4_321)
    line = build_record(exchange, SessionBook(), TO_AGENT, status, reply, V5)
    assert line[OUTCOME_FIELD] == outcome
    assert line[LOGICAL_CALL_FIELD] == exchange.call_facts({"id": 1}).logical_call
    assert line[REPLY_WIRE_BYTES_FIELD] == 4_321
    assert line.get(REPLY_BYTES_FIELD) == (json_bytes(CONTENT) if reply_bytes else None)
    assert ARG_BYTES_FIELD not in line and PROTOCOL_ISSUES_FIELD not in line


def test_a_bodiless_rejection_gives_the_exchanges_calls_their_outcome() -> None:
    exchange = _v5_exchange([_call()])
    line = build_record(exchange, SessionBook(), TO_AGENT, 405, None, V5)
    assert line[OUTCOME_FIELD] == REJECTED
    listing = _v5_exchange([{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
    assert OUTCOME_FIELD not in build_record(listing, SessionBook(), TO_AGENT, 202, None, V5)


def test_reply_facts_skip_what_is_not_a_reply_to_a_scored_call() -> None:
    exchange = _v5_exchange([_call()])
    server_request = {"jsonrpc": "2.0", "id": 1, "method": "sampling/createMessage"}
    assert reply_facts(exchange, 200, server_request) is None
    assert reply_facts(exchange, 200, {"jsonrpc": "2.0", "id": 9, "result": {}}) is None
    assert reply_facts(exchange, 200, None) is None


#: A per-person key (the opt-in ``baseline_key = "user"``) and a reported one (no sign-in).
PERSON_KEY, REPORTED_KEY = "a1b2c3d4e5f6", "0f9e8d7c6b5a"


@pytest.mark.parametrize(
    ("fields", "strength"),
    [
        # Signed in, history per agent (D5's default): service, whatever the token's shape.
        ({}, IDENTITY_SERVICE),  # a token naming a person, before the scorer sets the key
        ({"baseline_key": "agt-0001"}, IDENTITY_SERVICE),  # the agent key, Identity.id
        ({"agent_id": None, "baseline_key": "claude-code"}, IDENTITY_SERVICE),  # no id: name
        ({"user": "ci-bot", "app": "ci-bot", "agent": "ci-bot"}, IDENTITY_SERVICE),  # Okta cc
        ({"user": "ci-bot@clients", "app": "ci-bot", "agent": "ci-bot"}, IDENTITY_SERVICE),  # Auth0
        ({"user": "5f0c7d1e-sp-object-id", "app": "ci-bot"}, IDENTITY_SERVICE),  # Entra app-only
        ({"user": None}, IDENTITY_SERVICE),
        # Signed in, on a route that keys history per person (opt-in): user.
        ({"baseline_key": PERSON_KEY}, IDENTITY_USER),
        # No sign-in: the key is the reported client name and address.
        (
            {"agent": "anonymous", "auth": NO_AUTH, "user": None, "agent_id": None, "app": None},
            IDENTITY_NONE,
        ),
        (
            {"agent": "anonymous", "auth": NO_AUTH, "agent_id": None, "baseline_key": REPORTED_KEY},
            IDENTITY_NONE,
        ),
        ({"agent": None, "auth": None}, IDENTITY_NONE),  # a refused request
    ],
)
def test_identity_strength(fields: dict, strength: str) -> None:
    exchange = _exchange(**fields)
    assert identity_strength(exchange) == strength
    line = build_record(exchange, SessionBook(), TO_SERVER, None, _call(), V5)
    assert line[IDENTITY_STRENGTH_FIELD] == strength


def test_v5_decision_and_notice_lines_carry_the_callers_fields() -> None:
    exchange = _v5_exchange([_call()], baseline_key="bk-1")
    decision = decision_record(exchange, SessionBook(), _call(), {"risk": 2.0}, None, T0, V5)
    assert decision[PROTOCOL_ERA_FIELD] == MODERN_ERA
    assert decision[LOGICAL_CALL_FIELD] == exchange.call_facts({"id": 1}).logical_call
    assert decision[ARG_BYTES_FIELD] == json_bytes(ARGS)
    assert decision[IDENTITY_STRENGTH_FIELD] == IDENTITY_USER
    assert decision["gateway.baseline_key"] == "bk-1"
    notice = notice_record(exchange, "session_agent_mismatch", V5)
    assert (notice[PROTOCOL_ERA_FIELD], notice[IDENTITY_STRENGTH_FIELD]) == (
        MODERN_ERA,
        IDENTITY_USER,
    )


def test_an_unparsed_body_gets_a_warn_verdict_line() -> None:
    verdict = unparsed_verdict(b"{not json", None, fail_closed=True)
    assert verdict is not None
    line = unparsed_record(_exchange(), verdict, V5)
    assert (line["gateway.notice"], line["log.level"]) == (UNPARSED, WARN)
    assert (line[UNPARSED_REASON_FIELD], line[REFUSED_FIELD]) == (UNPARSED_JSON, True)
    assert line["gateway.direction"] == FROM_GATEWAY
    forwarded = unparsed_verdict(b"{not json", None, fail_closed=False)
    assert forwarded is not None
    assert unparsed_record(_exchange(), forwarded, V4)[REFUSED_FIELD] is False


# ── the bounded session book (E9, DEP-5) ────────────────────────────────────────────────────


def test_the_bounded_book_has_the_session_books_interface() -> None:
    for name, method in inspect.getmembers(SessionBook, inspect.isfunction):
        if name.startswith("_"):
            continue
        bounded = getattr(BoundedSessionBook, name)
        assert inspect.signature(bounded).parameters.keys() == (
            inspect.signature(method).parameters.keys()
        ), name


@pytest.mark.parametrize("book", [SessionBook, BoundedSessionBook])
def test_request_seq_counts_only_the_agents_messages_in_either_book(book: type) -> None:
    exchange = Exchange("github", "alice", "s", "POST", requests={"2": ("tools/call", "t")})
    reply = {"jsonrpc": "2.0", "id": 2, "result": {"content": []}}
    sessions = book()
    lines = [
        build_record(exchange, sessions, TO_SERVER, None, _call(2)),
        build_record(exchange, sessions, TO_AGENT, 200, reply),
        build_record(exchange, sessions, TO_SERVER, None, _call(3)),
    ]
    assert [line["gateway.seq"] for line in lines] == [1, 2, 3]
    assert [line.get("gateway.request_seq") for line in lines] == [1, None, 2]


def test_v4s_book_binds_on_first_sight_and_v5s_only_on_accept() -> None:
    old, new = SessionBook(), BoundedSessionBook(clock=_Clock())
    assert old.claim("s", "alice") is None and old.claim("s", "bob") == "alice"
    assert new.claim("s", "alice") is None and new.claim("s", "bob") is None  # nobody bound yet
    assert new.accept("s", "alice", 200) is True
    assert new.claim("s", "bob") == "alice"
    assert new.accept("s", "bob", 200) is False  # an owned session keeps its owner
    assert new.accept("s", "alice", 404) is True  # still the owner after the server ended it


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 502, None])
def test_an_id_the_server_did_not_take_is_not_claimed(status: int | None) -> None:
    book = BoundedSessionBook(clock=_Clock())
    assert book.claim("junk", "mallory") is None
    assert book.accept("junk", "mallory", status) is False
    assert book.claim("junk", "alice") is None
    assert book.accept("junk", "alice", 200) is True  # the server later mints it for alice
    assert book.claim("junk", "mallory") == "alice"


def test_junk_ids_evict_only_their_own_callers_sessions() -> None:
    book = BoundedSessionBook(clock=_Clock())
    book.claim("victim", "alice")
    book.accept("victim", "alice", 200)
    for i in range(2_000):
        book.claim(f"junk-{i}", "mallory")
        book.accept(f"junk-{i}", "mallory", 404)
    assert book.claim("victim", "mallory") == "alice"
    assert book.sessions == 1 + MAX_SESSIONS_PER_CALLER and book.callers == 2


def test_a_caller_over_its_quota_loses_its_least_recently_seen_session() -> None:
    clock = _Clock()
    book = BoundedSessionBook(max_per_caller=3, clock=clock)
    for name in ("a", "b", "c"):
        clock.now += 1
        book.claim(name, "alice")
        book.accept(name, "alice", 200)
    clock.now += 1
    book.next_seq("a")  # a is used again: b is now the least recently seen
    book.claim("d", "alice")
    assert book.claim("b", "bob") is None  # b was forgotten
    assert book.claim("a", "bob") == "alice" and book.claim("d", "alice") is None


def test_an_idle_session_is_forgotten_with_every_map() -> None:
    clock = _Clock()
    book = BoundedSessionBook(clock=clock)
    book.claim("s", "alice")
    book.accept("s", "alice", 200)
    book.start("s", "client/1.0")
    book.saw_tools("s", [{"name": "get_file_contents"}], "digest")
    book.next_seq("s")
    clock.now += SESSION_TTL_S - 1
    assert (book.client("s"), book.catalog("s"), book.listed("s", "get_file_contents")) == (
        "client/1.0",
        "digest",
        True,
    )
    book.next_request("s")  # in use: the idle time starts again
    clock.now += SESSION_TTL_S + 1
    assert (book.client("s"), book.catalog("s"), book.listed("s", "x")) == (None, None, None)
    assert book.sessions == 0 and book.callers == 0
    assert book.claim("s", "bob") is None


def test_a_session_seen_before_its_caller_counts_against_that_callers_quota() -> None:
    """A reply line (``next_seq``) can create a session's record before anyone presents it;
    the first caller to present it then owns its quota slot, so its own sessions evict it."""
    book = BoundedSessionBook(max_per_caller=1, clock=_Clock())
    book.next_seq("s")
    assert book.claim("s", "alice") is None
    book.claim("t", "alice")
    assert (book.sessions, book.callers) == (1, 1)
    assert book.next_seq("s") == 1  # "s" was evicted by alice's "t": it starts again


def test_the_route_bound_evicts_the_routes_least_recently_seen_session() -> None:
    clock = _Clock()
    book = BoundedSessionBook(max_sessions=4, clock=clock)
    for name, caller in [("a", "alice"), ("b", "bob"), ("c", "carol"), ("d", "alice")]:
        clock.now += 1
        book.claim(name, caller)
        book.accept(name, caller, 200)
        book.start(name, f"{caller}-client/1")
    clock.now += 1
    book.next_seq("a")  # "b" is now the route's least recently seen session
    book.claim("e", "dave")
    assert book.sessions == 4
    kept = [book.client(name) for name in "abcd"]  # a read that moves nothing
    assert kept == ["alice-client/1", None, "carol-client/1", "alice-client/1"]


def test_ending_a_session_keeps_its_owner_and_forgets_the_rest() -> None:
    book = BoundedSessionBook(clock=_Clock())
    book.claim("s", "alice")
    book.accept("s", "alice", 200)
    book.start("s", "client/1.0")
    assert book.next_seq("s") == 1
    book.end("s")
    assert book.ended("s") and book.client("s") is None and book.next_seq("s") == 1
    assert book.claim("s", "bob") == "alice"
    book.claim("unowned", "bob")
    book.end("unowned")
    assert not book.ended("unowned") and book.claim("unowned", "carol") is None
    book.end(None)
    assert not book.ended(None)


def test_save_and_restore_keep_live_owners_and_clients_without_raw_ids() -> None:
    clock = _Clock()
    pseudonyms = Pseudonymizer(b"route-key")
    book = BoundedSessionBook(key=pseudonyms.of, clock=clock)
    for session, caller in (("sess-secret-1", "alice"), ("sess-secret-2", "bob")):
        book.claim(session, caller)
        book.accept(session, caller, 200)
        book.start(session, f"{caller}-client/1")
    clock.now += SESSION_TTL_S - 10
    book.next_seq("sess-secret-2")
    saved = json.loads(json.dumps(book.snapshot()))
    assert "sess-secret" not in json.dumps(saved)
    clock.now += 20  # sess-secret-1 is now idle past the TTL; sess-secret-2 is not
    restored = BoundedSessionBook(key=pseudonyms.of, clock=clock)
    restored.restore(saved)
    assert restored.sessions == 1
    assert restored.claim("sess-secret-2", "mallory") == "bob"
    assert restored.client("sess-secret-2") == "bob-client/1"
    assert restored.claim("sess-secret-1", "mallory") is None


def _row(key: str, caller: str, owner: str | None, seen: object) -> list:
    return [key, caller, owner, seen, None, False]


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"format": "session-book/0", "sessions": []},
        {"format": SESSION_BOOK_FORMAT, "sessions": [["k", "c", None, "late", None, False]]},
        {"format": SESSION_BOOK_FORMAT, "sessions": "all"},
        # One key twice: its record would sit in two callers' quotas (a KeyError later).
        {
            "format": SESSION_BOOK_FORMAT,
            "sessions": [_row("k", "alice", "alice", T0 - 2), _row("k", "bob", "bob", T0 - 1)],
        },
        {"format": SESSION_BOOK_FORMAT, "sessions": [_row("k", "alice", "bob", T0)]},
        {"format": SESSION_BOOK_FORMAT, "sessions": [_row("k", "alice", None, math.nan)]},
        {"format": SESSION_BOOK_FORMAT, "sessions": [_row("k", "alice", None, math.inf)]},
        {"format": SESSION_BOOK_FORMAT, "sessions": [_row("k", "alice", None, True)]},
    ],
    ids=["empty", "format", "time-type", "rows", "twice", "owner", "nan", "inf", "bool"],
)
def test_a_bad_snapshot_fails_loudly_and_changes_nothing(bad: dict) -> None:
    book = BoundedSessionBook(clock=_Clock())
    book.claim("s", "alice")
    book.accept("s", "alice", 200)
    with pytest.raises(ValueError):
        book.restore(bad)
    assert book.sessions == 1 and book.claim("s", "bob") == "alice"


def test_a_snapshot_from_a_clock_ahead_restores_as_seen_now() -> None:
    """Clock skew between save and restore: the record counts as seen now, so it expires a TTL
    from now and the book stays in least-recently-seen order."""
    clock = _Clock()
    book = BoundedSessionBook(clock=clock)
    rows = [_row("past", "alice", "alice", T0 - 10), _row("ahead", "alice", "alice", T0 + 500)]
    book.restore({"format": SESSION_BOOK_FORMAT, "sessions": rows})
    assert book.sessions == 2
    clock.now += SESSION_TTL_S + 1
    assert book.client("ahead") is None and book.sessions == 0


def test_bad_book_bounds_fail_loudly() -> None:
    with pytest.raises(ValueError):
        BoundedSessionBook(ttl_s=0)
    with pytest.raises(ValueError):
        BoundedSessionBook(max_per_caller=0)


def test_a_million_never_deleted_sessions_keep_the_book_bounded() -> None:
    """DEP-5: 10^6 sessions from 2,000 callers, none ever ended, with the default bounds. Each
    caller holds at most its quota, the route at most its bound, and every map shrinks with the
    records."""
    clock = _Clock()
    bound = MAX_SESSION_OWNERS
    book = BoundedSessionBook(clock=clock)
    largest = 0
    for i in range(SESSIONS_FLOOD):
        clock.now += FLOOD_STEP_S
        session, caller = f"s{i}", f"c{i % FLOOD_CALLERS}"
        book.claim(session, caller)
        book.accept(session, caller, 200 if i % 3 else 404)
        largest = max(largest, book.sessions)
    assert largest <= bound
    assert book.sessions <= min(bound, FLOOD_CALLERS * MAX_SESSIONS_PER_CALLER)
    assert book.callers <= FLOOD_CALLERS
    assert sum(len(own) for own in book._by_caller.values()) == book.sessions
    clock.now += SESSION_TTL_S + 1
    book.claim("late", "c0")
    assert (book.sessions, book.callers) == (1, 1)
