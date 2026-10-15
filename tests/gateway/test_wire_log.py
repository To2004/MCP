"""One log line per message: what gateway-log/3 adds over v2, record by record."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_security.gateway.effects import EffectMap
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import (
    SCHEMA,
    TO_AGENT,
    TO_SERVER,
    Exchange,
    LogPolicy,
    SessionBook,
    build_record,
    client_info_of,
    protocol_of,
)

TRACE_ID, SPAN_ID = "4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7"


def _call(args: dict, rpc_id: int = 2, meta: dict | None = None) -> dict:
    params: dict = {"name": "list_commits", "arguments": args}
    if meta is not None:
        params["_meta"] = meta
    return {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/call", "params": params}


def _exchange(**fields: Any) -> Exchange:
    return Exchange("github", "alice", "s", "POST", **fields)


def _sent(message: dict, policy: LogPolicy | None = None, **fields: Any) -> dict:
    return build_record(
        _exchange(**fields), SessionBook(), TO_SERVER, None, message, policy or LogPolicy()
    )


def test_a_tool_call_carries_its_argument_names_and_a_pseudonym_of_its_arguments() -> None:
    first = _sent(_call({"repo": "api", "perPage": 10}))
    reordered = _sent(_call({"perPage": 10, "repo": "api"}))
    other = _sent(_call({"repo": "web", "perPage": 10}))

    assert first["schema"] == SCHEMA
    assert first["gateway.arg_keys"] == ["perPage", "repo"]
    assert (
        first["gateway.args_hash"] == reordered["gateway.args_hash"] != other["gateway.args_hash"]
    )
    assert first["gen_ai.operation.name"] == "execute_tool"
    assert first["jsonrpc.request.id"] == "2"


def test_keyed_pseudonyms_differ_from_unkeyed_ones() -> None:
    plain = _sent(_call({"repo": "api"}))
    keyed = _sent(_call({"repo": "api"}), LogPolicy(pseudonyms=Pseudonymizer(b"secret")))

    assert plain["mcp.session.id"] == Pseudonymizer().of("s")
    assert keyed["mcp.session.id"] != plain["mcp.session.id"]
    assert keyed["gateway.args_hash"] != plain["gateway.args_hash"]


def test_request_seq_counts_only_the_agents_messages() -> None:
    book, exchange = SessionBook(), _exchange(requests={"2": ("tools/call", "list_commits")})
    reply = {"jsonrpc": "2.0", "id": 2, "result": {"content": []}}
    lines = [
        build_record(exchange, book, TO_SERVER, None, _call({})),
        build_record(exchange, book, TO_AGENT, 200, reply),
        build_record(exchange, book, TO_SERVER, None, _call({}, rpc_id=3)),
    ]
    assert [line["gateway.seq"] for line in lines] == [1, 2, 3]
    assert [line.get("gateway.request_seq") for line in lines] == [1, None, 2]


def test_trace_context_from_meta_is_logged_and_garbage_is_not() -> None:
    good = _sent(_call({}, meta={"traceparent": f"00-{TRACE_ID}-{SPAN_ID}-01"}))
    bad = _sent(_call({}, meta={"traceparent": "not-a-trace"}))

    assert (good["trace_id"], good["span_id"]) == (TRACE_ID, SPAN_ID)
    assert "trace_id" not in bad


@pytest.mark.parametrize(
    ("bodies", "request_kept", "reply_kept"),
    [("all", True, True), ("requests", True, False), ("none", False, False)],
)
def test_body_policy_drops_bodies_but_keeps_what_the_dimensions_need(
    bodies: str, request_kept: bool, reply_kept: bool
) -> None:
    policy = LogPolicy(bodies=bodies)
    exchange = _exchange(requests={"2": ("tools/call", "list_commits"), "3": ("tools/list", None)})
    reply = {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"text": "private"}]}}
    listing = {"jsonrpc": "2.0", "id": 3, "result": {"tools": [{"name": "list_commits"}]}}

    request = build_record(exchange, SessionBook(), TO_SERVER, None, _call({"repo": "x"}), policy)
    answer = build_record(exchange, SessionBook(), TO_AGENT, 200, reply, policy)
    catalog = build_record(exchange, SessionBook(), TO_AGENT, 200, listing, policy)

    assert ("message" in request, "message" in answer) == (request_kept, reply_kept)
    assert request["gateway.arg_keys"] == ["repo"] and request["gateway.message_bytes"] > 0
    assert "message" in catalog  # the public tool list is always kept, for catalog.py


def test_an_unknown_body_policy_is_refused() -> None:
    with pytest.raises(ValueError, match="log bodies"):
        LogPolicy(bodies="some")


def test_message_size_is_in_bytes_not_characters() -> None:
    record = _sent(_call({"q": "שלום"}))
    assert record["gateway.message_bytes"] == len(
        json.dumps(_call({"q": "שלום"}), ensure_ascii=False).encode()
    )


def test_typed_effects_ride_on_the_call_line(tmp_path: Path) -> None:
    importance = {
        "tools": [
            {
                "tool_name": "list_commits",
                "arguments": [
                    {"path": "repo", "effect": "which", "important": True},
                    {"path": "perPage", "effect": "how_much", "important": True},
                ],
            }
        ]
    }
    path = tmp_path / "x.importance.json"
    path.write_text(json.dumps(importance))
    policy = LogPolicy(bodies="none", effects=EffectMap.load(path))

    record = _sent(_call({"repo": "api", "perPage": 100}), policy)

    assert record["gateway.effects"] == {"which": {"repo": "api"}, "how_much": {"perPage": 100}}
    assert "message" not in record


def test_headers_that_name_another_call_than_the_body_are_flagged() -> None:
    matching = _sent(_call({}), method_header="tools/call", name_header="list_commits")
    smuggled = _sent(_call({}), method_header="tools/call", name_header="delete_repo")

    assert "gateway.header_mismatch" not in matching
    assert smuggled["gateway.header_mismatch"] == ["Mcp-Name"]


def test_identity_and_wire_fields_are_on_every_line() -> None:
    record = _sent(
        _call({}),
        user="u-0417",
        app="ci",
        agent_id="agt-17",
        client_address="203.0.113.9",
        peer_address="127.0.0.1",
        origin="https://evil.example",
    )
    assert (record["gateway.agent_id"], record["user.id"], record["gateway.app"]) == (
        "agt-17",
        "u-0417",
        "ci",
    )
    assert record["log.level"] == "info"
    assert record["network.peer.address"] == "127.0.0.1"
    assert record["http.request.header.origin"] == ["https://evil.example"]
    assert len(record["gateway.exchange_id"]) == 32


def test_client_and_version_are_read_from_meta_in_2026_requests() -> None:
    meta = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientInfo": {"name": "ExampleClient", "version": "1.0.0"},
    }
    messages = [_call({}, meta=meta)]

    assert client_info_of(messages) == "ExampleClient/1.0.0"
    assert protocol_of(messages) == "2026-07-28"
