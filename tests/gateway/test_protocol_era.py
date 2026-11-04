"""E3, E7 and ARG-1: the protocol era of a request, its conformance issues, era-free sizes,
the server's outcome and logical-call folding (``gateway/protocol_era.py``).

Every message here is synthetic. The wire names (``_meta`` keys, headers, the SEP-2322 MRTR
fields) and the rejecting error codes are also checked against the MCP Python SDK the repo runs
on (``mcp>=2.3,<3``): its own types build the MRTR messages, and its own validation ladder
(``mcp.shared.inbound``) judges the conformance cases.
"""

from __future__ import annotations

import base64

import httpx
import mcp_types
import pytest
from mcp.shared import inbound as sdk_inbound
from mcp_types import version as sdk_version
from mcp_types.methods import is_input_required
from pydantic import BaseModel
from starlette.datastructures import Headers

from mcp_security.behaviour.engine import ACCEPTED, LEGACY_ERA, MODERN_ERA, REJECTED
from mcp_security.gateway.protocol_era import (
    ASSUMED_VERSION,
    CONTINUED,
    FALLBACK_FOLD_S,
    ISSUE_DUPLICATE_METHOD,
    ISSUE_DUPLICATE_NAME,
    ISSUE_DUPLICATE_VERSION,
    ISSUE_HEADER_METHOD,
    ISSUE_HEADER_NAME,
    ISSUE_HEADER_VERSION,
    ISSUE_LEGACY_BATCH,
    ISSUE_LEGACY_EVENT,
    ISSUE_LEGACY_SESSION,
    ISSUE_META_CAPABILITIES,
    ISSUE_META_VERSION,
    ISSUE_MISMATCH_METHOD,
    ISSUE_MISMATCH_NAME,
    ISSUE_MISMATCH_VERSION,
    META_CAPABILITIES,
    META_CLIENT,
    META_PROTOCOL,
    METHOD_HEADER,
    MODERN_FROM,
    MRTR_INPUT_REQUIRED,
    MRTR_INPUT_RESPONSES_FIELD,
    MRTR_REQUEST_STATE_FIELD,
    MRTR_RESULT_TYPE_FIELD,
    NAME_HEADER,
    NAMED_METHODS,
    PROTOCOL_HEADER,
    REJECTING_HTTP_STATUSES,
    REJECTING_RPC_CODES,
    REQUEST_STATE_TTL_S,
    LogicalCalls,
    argument_bytes,
    call_outcome,
    call_signature,
    classify,
    classify_request,
    conformance_issues,
    is_modern_revision,
    json_bytes,
    minted_request_state,
    reply_payload_bytes,
    request_issues,
    request_state_of,
)

LEGACY_VERSION = "2025-11-25"
CAPABILITIES = {"elicitation": {}}
ARGS = {"owner": "acme", "repo": "repo-a", "path": "README.md"}
T0 = 1_780_000_000.0


def _meta(version: str = MODERN_FROM, capabilities: bool = True) -> dict:
    meta: dict = {META_PROTOCOL: version}
    if capabilities:
        meta[META_CAPABILITIES] = CAPABILITIES
    return meta


def _call(
    meta: dict | None = None, rpc_id: int | None = 1, args: dict | None = None, **params: object
) -> dict:
    body: dict = {"name": "get_file_contents", "arguments": ARGS if args is None else args}
    if meta is not None:
        body["_meta"] = meta
    body.update(params)
    message: dict = {"jsonrpc": "2.0", "method": "tools/call", "params": body}
    if rpc_id is not None:
        message["id"] = rpc_id
    return message


def _initialize(version: str = LEGACY_VERSION) -> dict:
    params = {"protocolVersion": version, "clientInfo": {"name": "c", "version": "1"}}
    return {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": params}


def _modern_headers(**extra: str) -> dict[str, str]:
    """Every header 2026-07-28 requires on a tools/call, as a client capitalises them."""
    headers = {
        "MCP-Protocol-Version": MODERN_FROM,
        "Mcp-Method": "tools/call",
        "Mcp-Name": "get_file_contents",
    }
    headers.update(extra)
    return headers


#: The 7-case era table (Part A E3): (row, HTTP method, headers, message) -> (era, version).
ERA_TABLE = [
    ("1a-initialize", "POST", {}, _initialize(), LEGACY_ERA, LEGACY_VERSION),
    (
        "1b-session-id",
        "POST",
        {"Mcp-Session-Id": "s-1", "MCP-Protocol-Version": LEGACY_VERSION},
        _call(),
        LEGACY_ERA,
        LEGACY_VERSION,
    ),
    (
        "2-legacy-header-no-meta",
        "POST",
        {"MCP-Protocol-Version": LEGACY_VERSION},
        _call(),
        LEGACY_ERA,
        LEGACY_VERSION,
    ),
    ("3-no-header-no-meta", "POST", {}, _call(), LEGACY_ERA, ASSUMED_VERSION),
    ("4-meta-modern", "POST", _modern_headers(), _call(_meta()), MODERN_ERA, MODERN_FROM),
    (
        "5-modern-header-no-meta",
        "POST",
        {"MCP-Protocol-Version": MODERN_FROM},
        _call(),
        MODERN_ERA,
        MODERN_FROM,
    ),
    (
        "6-meta-modern-legacy-header",
        "POST",
        _modern_headers(**{"MCP-Protocol-Version": LEGACY_VERSION}),
        _call(_meta()),
        MODERN_ERA,
        MODERN_FROM,
    ),
    ("7a-GET", "GET", {"MCP-Protocol-Version": MODERN_FROM}, None, LEGACY_ERA, MODERN_FROM),
    ("7b-DELETE", "DELETE", {"Mcp-Session-Id": "s-1"}, None, LEGACY_ERA, ASSUMED_VERSION),
]
#: The issues each modern row carries; legacy rows carry none.
ROW_ISSUES = {
    "4-meta-modern": (),
    "5-modern-header-no-meta": (
        ISSUE_META_VERSION,
        ISSUE_META_CAPABILITIES,
        ISSUE_HEADER_METHOD,
        ISSUE_HEADER_NAME,
    ),
    "6-meta-modern-legacy-header": (ISSUE_MISMATCH_VERSION,),
}


@pytest.mark.parametrize(
    ("row", "http_method", "headers", "message", "era", "version"),
    ERA_TABLE,
    ids=[row[0] for row in ERA_TABLE],
)
def test_the_era_table(
    row: str, http_method: str, headers: dict, message: dict | None, era: str, version: str
) -> None:
    view = classify(http_method, headers, message)
    assert (view.era, view.version) == (era, version)
    issues = conformance_issues(view, headers, message)
    assert issues == ROW_ISSUES.get(row, ())
    messages = [message] if message else []
    assert request_issues(http_method, headers, messages) == issues
    assert classify_request(http_method, headers, messages).era == era


def test_the_eras_are_the_engines_values() -> None:
    assert {view[4] for view in ERA_TABLE} == {LEGACY_ERA, MODERN_ERA} == {"legacy", "modern"}


def test_only_revision_dates_compare_with_the_modern_revision() -> None:
    assert is_modern_revision(MODERN_FROM) and is_modern_revision("2027-01-01")
    assert not is_modern_revision(LEGACY_VERSION)
    assert not is_modern_revision("garbage")  # sorts above "2026-07-28" as a plain string
    assert not is_modern_revision(None)
    view = classify("POST", {"MCP-Protocol-Version": "zzz"}, _call())
    assert (view.era, view.version) == (LEGACY_ERA, "zzz")


def test_a_non_string_meta_version_does_not_make_a_request_modern() -> None:
    view = classify("POST", {}, _call({META_PROTOCOL: 20260728}))
    assert (view.era, view.version_body, view.version) == (LEGACY_ERA, None, ASSUMED_VERSION)


def test_header_names_are_case_insensitive() -> None:
    lower = {k.lower(): v for k, v in _modern_headers().items()}
    view = classify("post", lower, _call(_meta()))
    assert view.era == MODERN_ERA
    assert conformance_issues(view, lower, _call(_meta())) == ()


def test_a_batch_is_modern_only_when_every_message_is() -> None:
    headers = _modern_headers()
    assert classify_request("POST", headers, [_call(_meta()), _call(_meta())]).era == MODERN_ERA
    mixed = classify_request("POST", headers, [_call(_meta()), _initialize()])
    assert mixed.era == LEGACY_ERA
    assert request_issues("POST", headers, [_call(_meta()), _initialize()]) == ()
    assert classify_request("POST", {"MCP-Protocol-Version": MODERN_FROM}, []).era == MODERN_ERA


def test_a_modern_batch_is_a_conformance_issue() -> None:
    """No revision since 2025-06-18 has batches, so a modern batch is logged as one."""
    headers = _modern_headers()
    batch = [_call(_meta()), _call(_meta(), rpc_id=2)]
    assert request_issues("POST", headers, batch) == (ISSUE_LEGACY_BATCH,)
    assert request_issues("POST", headers, batch[:1]) == ()
    legacy = [_call(), _call(rpc_id=2)]
    assert request_issues("POST", {"MCP-Protocol-Version": LEGACY_VERSION}, legacy) == ()


def test_an_empty_meta_version_is_no_version() -> None:
    view = classify("POST", {}, _call({META_PROTOCOL: "", META_CAPABILITIES: CAPABILITIES}))
    assert (view.era, view.version_body, view.version) == (LEGACY_ERA, None, ASSUMED_VERSION)


#: One case per E7 issue: (headers, message) -> the single issue it raises.
ISSUE_CASES = [
    (_modern_headers(), _call({META_CAPABILITIES: CAPABILITIES}), ISSUE_META_VERSION),
    (_modern_headers(), _call(_meta(capabilities=False)), ISSUE_META_CAPABILITIES),
    (
        _modern_headers(),
        _call({META_PROTOCOL: MODERN_FROM, META_CAPABILITIES: ["elicitation"]}),
        ISSUE_META_CAPABILITIES,
    ),
    (_modern_headers(), _call({META_PROTOCOL: "", META_CAPABILITIES: {}}), ISSUE_META_VERSION),
    (
        {"Mcp-Method": "tools/call", "Mcp-Name": "get_file_contents"},
        _call(_meta()),
        ISSUE_HEADER_VERSION,
    ),
    (
        {"MCP-Protocol-Version": MODERN_FROM, "Mcp-Name": "get_file_contents"},
        _call(_meta()),
        ISSUE_HEADER_METHOD,
    ),
    (
        {"MCP-Protocol-Version": MODERN_FROM, "Mcp-Method": "tools/call"},
        _call(_meta()),
        ISSUE_HEADER_NAME,
    ),
    (
        _modern_headers(**{"MCP-Protocol-Version": "2027-01-01"}),
        _call(_meta()),
        ISSUE_MISMATCH_VERSION,
    ),
    (_modern_headers(**{"Mcp-Method": "tools/list"}), _call(_meta()), ISSUE_MISMATCH_METHOD),
    (_modern_headers(**{"Mcp-Name": "delete_repository"}), _call(_meta()), ISSUE_MISMATCH_NAME),
    (_modern_headers(**{"Mcp-Session-Id": "s-1"}), _call(_meta()), ISSUE_LEGACY_SESSION),
    (_modern_headers(**{"Last-Event-ID": "e-9"}), _call(_meta()), ISSUE_LEGACY_EVENT),
]


@pytest.mark.parametrize(
    ("headers", "message", "issue"),
    ISSUE_CASES,
    ids=[f"{i}-{case[2]}" for i, case in enumerate(ISSUE_CASES)],
)
def test_each_conformance_issue(headers: dict, message: dict, issue: str) -> None:
    view = classify("POST", headers, message)
    assert view.era == MODERN_ERA
    assert conformance_issues(view, headers, message) == (issue,)


def test_a_conforming_call_a_notification_and_a_legacy_request_have_no_issues() -> None:
    conforming, headers = _call(_meta()), _modern_headers()
    assert conformance_issues(classify("POST", headers, conforming), headers, conforming) == ()
    assert request_issues("POST", headers, [conforming]) == ()
    notification = {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}
    view = classify("POST", {"MCP-Protocol-Version": MODERN_FROM}, notification)
    assert view.era == MODERN_ERA
    assert conformance_issues(view, {}, notification) == ()  # not checked: no id
    legacy = _call(rpc_id=7)
    assert conformance_issues(classify("POST", {}, legacy), {}, legacy) == ()  # not checked


def test_header_rules_apply_on_http_only() -> None:
    message = _call(_meta())
    view = classify("POST", {}, message)
    assert conformance_issues(view, {}, message, http=False) == ()
    assert ISSUE_HEADER_VERSION in conformance_issues(view, {}, message)


def test_a_base64_mcp_name_is_compared_decoded() -> None:
    name = "ציון"
    message = _call(_meta(), name=name)
    encoded = "=?base64?" + base64.b64encode(name.encode()).decode() + "?="
    headers = _modern_headers(**{"Mcp-Name": encoded})
    assert conformance_issues(classify("POST", headers, message), headers, message) == ()


def test_a_resource_read_is_named_by_its_uri() -> None:
    message = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "resources/read",
        "params": {"uri": "repo://acme/repo-a", "_meta": _meta()},
    }
    headers = {"MCP-Protocol-Version": MODERN_FROM, "Mcp-Method": "resources/read"}
    view = classify("POST", headers, message)
    assert conformance_issues(view, headers, message) == (ISSUE_HEADER_NAME,)
    headers["Mcp-Name"] = "repo://acme/repo-b"
    assert conformance_issues(view, headers, message) == (ISSUE_MISMATCH_NAME,)


def test_request_issues_are_listed_once_in_first_seen_order() -> None:
    headers = {"MCP-Protocol-Version": MODERN_FROM}
    twice = [_call(_meta()), _call(_meta(), rpc_id=2)]
    expected = (ISSUE_HEADER_METHOD, ISSUE_HEADER_NAME, ISSUE_LEGACY_BATCH)
    assert request_issues("POST", headers, twice) == expected


def _raw_headers(pairs: list[tuple[str, str]]) -> Headers:
    """Request headers as the proxy sees them (Starlette), repeats kept."""
    return Headers(raw=[(name.lower().encode(), value.encode()) for name, value in pairs])


@pytest.mark.parametrize("repeated", ["MCP-Protocol-Version", "Mcp-Method", "Mcp-Name"])
@pytest.mark.parametrize("make", [_raw_headers, httpx.Headers], ids=["starlette", "httpx"])
def test_a_routing_header_sent_twice_is_read_first_and_logged(repeated: str, make) -> None:
    """The proxy reads a header with Starlette's ``Headers.get`` (the first copy), so the era
    and the comparisons use the first copy too; a second copy is an issue (the SDK rejects
    it), whatever it says."""
    pairs = [*_modern_headers().items(), (repeated, "2025-11-25")]
    headers, message = make(pairs), _call(_meta())
    duplicate = {
        "MCP-Protocol-Version": ISSUE_DUPLICATE_VERSION,
        "Mcp-Method": ISSUE_DUPLICATE_METHOD,
        "Mcp-Name": ISSUE_DUPLICATE_NAME,
    }[repeated]
    view = classify("POST", headers, message)
    assert (view.era, view.version_header) == (MODERN_ERA, MODERN_FROM)
    assert conformance_issues(view, headers, message) == (duplicate,)
    raw = [(name.lower(), value) for name, value in pairs]
    assert sdk_inbound.find_duplicated_routing_header(raw) == repeated.lower()


def test_the_first_copy_decides_the_era_as_in_the_proxy() -> None:
    """A legacy first copy and a modern second: legacy, as ``mcp.protocol.version`` says."""
    headers = _raw_headers([("MCP-Protocol-Version", LEGACY_VERSION), *_modern_headers().items()])
    assert headers.get(PROTOCOL_HEADER) == LEGACY_VERSION
    view = classify("POST", headers, _call())
    assert (view.era, view.version) == (LEGACY_ERA, LEGACY_VERSION)


@pytest.mark.parametrize(
    ("status", "reply", "outcome"),
    [
        (400, None, REJECTED),
        (404, None, REJECTED),
        (405, None, REJECTED),
        (200, {"id": 1, "error": {"code": -32602}}, REJECTED),
        (200, {"id": 1, "error": {"code": -32601}}, REJECTED),
        (200, {"id": 1, "error": {"code": -32020}}, REJECTED),
        (200, {"id": 1, "error": {"code": -32021}}, REJECTED),
        (200, {"id": 1, "error": {"code": -32022}}, REJECTED),
        (400, {"id": 1, "result": {MRTR_RESULT_TYPE_FIELD: MRTR_INPUT_REQUIRED}}, REJECTED),
        (200, {"id": 1, "result": {"content": [], "isError": True}}, ACCEPTED),
        (200, {"id": 1, "result": {"content": []}}, ACCEPTED),
        (202, None, ACCEPTED),
        (200, {"id": 1, "result": {MRTR_RESULT_TYPE_FIELD: MRTR_INPUT_REQUIRED}}, CONTINUED),
        # Not in spec 2.1's list, so accepted until the author decides otherwise (I6 finding 5).
        (200, {"id": 1, "error": {"code": -32603}}, ACCEPTED),
        (200, {"id": 1, "error": {"code": -32600}}, ACCEPTED),
        (401, None, ACCEPTED),
        (403, None, ACCEPTED),
        (429, None, ACCEPTED),
        (502, None, ACCEPTED),
    ],
)
def test_the_outcome_of_a_call(status: int, reply: dict | None, outcome: str) -> None:
    assert call_outcome(status, reply) == outcome


def test_the_outcomes_are_the_engines_values() -> None:
    assert (ACCEPTED, REJECTED) == ("accepted", "rejected")


def test_argument_bytes_are_the_same_in_both_eras() -> None:
    legacy = _call(args={"q": "שלום", "n": 1})
    modern = _call(_meta(), rpc_id="abc", args={"n": 1, "q": "שלום"})
    assert argument_bytes(legacy) == argument_bytes(modern) == len('{"q":"שלום","n":1}'.encode())
    assert argument_bytes(_call(args={"q": "x" * 1000})) > argument_bytes(_call(args={"q": "x"}))
    no_arguments = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "t"}}
    assert argument_bytes(no_arguments) == argument_bytes(_call(args={})) == json_bytes({})


def test_reply_bytes_count_the_payload_and_never_the_envelope() -> None:
    content = [{"type": "text", "text": "x" * 500}]
    legacy = {"jsonrpc": "2.0", "id": 1, "result": {"content": content}}
    modern = {
        "jsonrpc": "2.0",
        "id": "abc",
        "result": {"content": content, "_meta": {"io.modelcontextprotocol/serverInfo": {}}},
    }
    size = reply_payload_bytes("tools/call", legacy)
    assert size == reply_payload_bytes("tools/call", modern) == json_bytes(content)
    contents = {"jsonrpc": "2.0", "id": 2, "result": {"contents": content}}
    assert reply_payload_bytes("resources/read", contents) == size
    messages = {"jsonrpc": "2.0", "id": 3, "result": {"messages": content}}
    assert reply_payload_bytes("prompts/get", messages) == size
    assert reply_payload_bytes("tools/call", {"id": 1, "error": {"code": -1}}) is None
    asking = {"id": 1, "result": {MRTR_RESULT_TYPE_FIELD: MRTR_INPUT_REQUIRED}}
    assert reply_payload_bytes("tools/call", asking) is None
    assert reply_payload_bytes("tools/list", legacy) is None


def _asking(state: str) -> dict:
    """An MRTR input_required answer that mints ``state``."""
    result = {
        MRTR_RESULT_TYPE_FIELD: MRTR_INPUT_REQUIRED,
        "inputRequests": {"confirm": {"type": "elicitation", "message": "Delete 3 files?"}},
        MRTR_REQUEST_STATE_FIELD: state,
    }
    return {"jsonrpc": "2.0", "id": 1, "result": result}


def _continuation(state: str, args: dict | None = None) -> dict:
    """The retried call echoing ``state``: a new JSON-RPC id, the answers and the state in
    ``params`` (verified, spec 2.1)."""
    echoed = {MRTR_REQUEST_STATE_FIELD: state, MRTR_INPUT_RESPONSES_FIELD: {}}
    return _call(_meta(), rpc_id=2, args=args, **echoed)


def test_the_mrtr_field_names() -> None:
    assert (MRTR_RESULT_TYPE_FIELD, MRTR_INPUT_REQUIRED) == ("resultType", "input_required")
    assert (MRTR_REQUEST_STATE_FIELD, MRTR_INPUT_RESPONSES_FIELD) == (
        "requestState",
        "inputResponses",
    )
    assert request_state_of(_continuation("st-1")) == "st-1"
    assert minted_request_state(_asking("st-1")) == "st-1"
    assert request_state_of(_call(_meta())) is None
    assert minted_request_state({"id": 1, "result": {MRTR_REQUEST_STATE_FIELD: "x"}}) is None


def test_an_mrtr_continuation_folds_into_the_call_it_continues() -> None:
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(_meta()), T0, "x/1")
    calls.answered(first, call_outcome(200, _asking("st-1")), _asking("st-1"), T0 + 1)
    later = T0 + 120.0  # the user took two minutes to answer the elicitation
    assert calls.key_for("alice", _continuation("st-1"), later, "y/1") == first
    assert calls.key_for("alice", _continuation("st-1"), later + 1, "z/1") == "z/1"  # used up


@pytest.mark.parametrize(
    ("caller", "message", "why"),
    [
        ("mallory", _continuation("st-1"), "another caller"),
        ("alice", _continuation("st-1", args={**ARGS, "repo": "repo-b"}), "other arguments"),
        ("alice", _continuation("st-2"), "a state never minted"),
        ("alice", _call(_meta(), requeststate="st-1"), "the state in another field"),
    ],
)
def test_what_is_not_a_continuation_is_a_new_call(caller: str, message: dict, why: str) -> None:
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(_meta()), T0, "x/1")
    calls.answered(first, CONTINUED, _asking("st-1"), T0 + 1)
    assert calls.key_for(caller, message, T0 + 2, "y/1") == "y/1", why


def test_a_request_state_expires() -> None:
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(_meta()), T0, "x/1")
    calls.answered(first, CONTINUED, _asking("st-1"), T0)
    late = T0 + REQUEST_STATE_TTL_S + 1
    assert calls.key_for("alice", _continuation("st-1"), late, "y/1") == "y/1"


def test_a_retry_of_a_rejected_call_folds_within_the_window_only() -> None:
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(_meta()), T0, "x/1")
    calls.answered(first, call_outcome(400, None), None, T0 + 0.2)
    assert calls.key_for("alice", _call(), T0 + 1.0, "y/1") == first  # fallback to legacy
    calls.answered(first, REJECTED, None, T0 + 1.1)
    late = T0 + 1.0 + FALLBACK_FOLD_S + 0.1
    assert calls.key_for("alice", _call(), late, "z/1") == "z/1"


def test_repeats_of_an_accepted_call_never_fold() -> None:
    """A burst of identical calls stays a burst: Call rate, Burst and Repetition see each."""
    calls = LogicalCalls()
    keys = []
    for i in range(20):
        key = calls.key_for("alice", _call(), T0 + 0.1 * i, f"x/{i}")
        calls.answered(key, ACCEPTED, {"id": 1, "result": {"content": []}}, T0 + 0.1 * i)
        keys.append(key)
    assert len(set(keys)) == 20
    unanswered = [calls.key_for("bob", _call(), T0 + 0.1 * i, f"b/{i}") for i in range(5)]
    assert len(set(unanswered)) == 5


def test_a_retry_by_another_caller_does_not_fold() -> None:
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(), T0, "x/1")
    calls.answered(first, REJECTED, None, T0)
    assert calls.key_for("bob", _call(), T0 + 1, "y/1") == "y/1"


def test_unknown_answers_are_ignored() -> None:
    calls = LogicalCalls()
    calls.answered(None, ACCEPTED, None, T0)
    calls.answered("never-asked", CONTINUED, _asking("st-1"), T0)
    assert calls.entries == 0


def test_the_logical_call_maps_stay_bounded() -> None:
    bound = 1_000
    calls = LogicalCalls(max_entries=bound)
    for i in range(20 * bound):
        ts = T0 + i * 0.001  # 20,000 distinct calls within 20 s
        key = calls.key_for("alice", _call(args={"i": i}), ts, f"k/{i}")
        if i % 2:
            calls.answered(key, CONTINUED, _asking(f"st-{i}"), ts)
        assert calls.entries <= 3 * bound
    assert calls.entries <= 3 * bound


def test_the_same_call_is_told_apart_by_argument_type_and_name_type() -> None:
    """Absent arguments are ``{}``, as in ``argument_bytes``; ``[]``, ``""`` and ``0`` are not,
    and a ``null`` name is not the name ``"None"``."""
    params = {"name": "get_file_contents"}
    bare = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}
    with_args = [_call(args=value) for value in ({}, [], "", 0)]
    signatures = [call_signature("alice", m) for m in with_args]
    assert call_signature("alice", bare) == signatures[0]
    assert len(set(signatures)) == len(signatures)
    unnamed = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": None}}
    named = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "None"}}
    assert call_signature("alice", unnamed) != call_signature("alice", named)


def test_a_lone_surrogate_is_sized_and_signed_not_raised() -> None:
    """``json.loads`` lets an escaped ``\\ud800`` through; a strict UTF-8 encode would raise."""
    message = _call(args={"q": "\ud800"})
    assert argument_bytes(message) == json_bytes({"q": "\ud800"}) == len('{"q":""}') + 3
    assert call_signature("alice", message) != call_signature("alice", _call(args={"q": ""}))
    reply = {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"text": "\udfff"}]}}
    assert reply_payload_bytes("tools/call", reply) == json_bytes([{"text": ""}]) + 3


def test_bad_bounds_fail_loudly() -> None:
    with pytest.raises(ValueError):
        LogicalCalls(max_entries=0)
    with pytest.raises(ValueError):
        LogicalCalls(fold_window_s=-1.0)


# ── the MCP Python SDK the repo runs on (mcp>=2.3,<3) ───────────────────────────────────────


def test_the_wire_names_are_the_sdks() -> None:
    """The ``_meta`` keys, the routing headers, the version a header-less request is assumed to
    speak and the first modern revision, as SDK 2.x names them."""
    assert (META_PROTOCOL, META_CAPABILITIES, META_CLIENT) == (
        mcp_types.PROTOCOL_VERSION_META_KEY,
        mcp_types.CLIENT_CAPABILITIES_META_KEY,
        mcp_types.CLIENT_INFO_META_KEY,
    )
    assert (PROTOCOL_HEADER, METHOD_HEADER, NAME_HEADER) == (
        sdk_inbound.MCP_PROTOCOL_VERSION_HEADER,
        sdk_inbound.MCP_METHOD_HEADER,
        sdk_inbound.MCP_NAME_HEADER,
    )
    assert NAMED_METHODS == frozenset(sdk_inbound.NAME_BEARING_METHODS)
    assert ASSUMED_VERSION == mcp_types.DEFAULT_NEGOTIATED_VERSION
    assert MODERN_FROM == sdk_version.MODERN_PROTOCOL_VERSIONS[0]
    assert all(is_modern_revision(v) for v in sdk_version.MODERN_PROTOCOL_VERSIONS)
    assert not any(is_modern_revision(v) for v in sdk_version.HANDSHAKE_PROTOCOL_VERSIONS)


def test_the_rejecting_codes_are_the_sdks() -> None:
    """Spec 2.1's rejecting codes are the SDK's constants, and its server answers each with a
    rejecting HTTP status, so a JSON reply and a status agree."""
    sdk_codes = {
        mcp_types.INVALID_PARAMS,
        mcp_types.METHOD_NOT_FOUND,
        mcp_types.HEADER_MISMATCH,
        mcp_types.MISSING_REQUIRED_CLIENT_CAPABILITY,
        mcp_types.UNSUPPORTED_PROTOCOL_VERSION,
    }
    assert REJECTING_RPC_CODES == sdk_codes
    assert {
        sdk_inbound.ERROR_CODE_HTTP_STATUS[code] for code in sdk_codes
    } <= REJECTING_HTTP_STATUSES
    assert mcp_types.INTERNAL_ERROR not in REJECTING_RPC_CODES  # unmapped there too (HTTP 200)


def _wire(model: BaseModel) -> dict:
    """An SDK model as it goes on the wire."""
    return model.model_dump(by_alias=True, mode="json", exclude_none=True)


def test_mrtr_messages_built_by_the_sdk_fold_into_one_call() -> None:
    asking = mcp_types.InputRequiredResult(
        input_requests={
            "confirm": mcp_types.ElicitRequest(
                params=mcp_types.ElicitRequestFormParams(
                    message="Delete 3 files?", requested_schema={"type": "object", "properties": {}}
                )
            )
        },
        request_state="st-1",
    )
    interim = {"jsonrpc": "2.0", "id": 1, "result": _wire(asking)}
    assert is_input_required(interim["result"])
    assert call_outcome(200, interim) == CONTINUED
    assert minted_request_state(interim) == "st-1"
    assert reply_payload_bytes("tools/call", interim) is None
    retry_params = mcp_types.CallToolRequestParams(
        name="get_file_contents",
        arguments=ARGS,
        input_responses={"confirm": mcp_types.ElicitResult(action="accept", content={})},
        request_state="st-1",
    )
    retry = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": _wire(retry_params)}
    assert request_state_of(retry) == "st-1"
    assert argument_bytes(retry) == argument_bytes(_call())
    calls = LogicalCalls()
    first = calls.key_for("alice", _call(), T0, "x/1")
    calls.answered(first, call_outcome(200, interim), interim, T0 + 1)
    assert calls.key_for("alice", retry, T0 + 30, "y/2") == first


def _sdk_route(headers: dict, message: dict) -> object:
    """The SDK server's verdict on a modern request (``mcp.shared.inbound``)."""
    lowered = {name.lower(): value for name, value in headers.items()}
    return sdk_inbound.classify_inbound_request(message, headers=lowered)


@pytest.mark.parametrize(
    ("headers", "message"),
    [(headers, message) for headers, message, _ in ISSUE_CASES]
    + [(_modern_headers(), _call(_meta()))],
)
def test_a_request_the_sdk_server_rejects_carries_an_issue(headers: dict, message: dict) -> None:
    """E7 is at least as strict as the SDK's validation ladder: what it rejects carries an
    issue, and a request with no issue passes it. (E7 also logs what the ladder does not check:
    the shape of the capabilities and the legacy headers.)"""
    view = classify("POST", headers, message)
    issues = conformance_issues(view, headers, message)
    route = _sdk_route(headers, message)
    if isinstance(route, sdk_inbound.InboundLadderRejection):
        assert issues, route.message
    if not issues:
        assert isinstance(route, sdk_inbound.InboundModernRoute)


def test_an_mcp_name_the_sdk_encodes_is_compared_decoded() -> None:
    for name in ("get_file_contents", "ציון", " padded ", "=?base64?xx?="):
        message = _call(_meta(), name=name)
        headers = _modern_headers(**{"Mcp-Name": sdk_inbound.encode_header_value(name)})
        assert conformance_issues(classify("POST", headers, message), headers, message) == ()
