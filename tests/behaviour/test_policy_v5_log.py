"""AI-6: a v5 gateway log joined for learning (requests, decisions, outcomes), and the CLI.

The log lines are synthetic: plain dicts with the field names the gateway writes, plus one
check that the gateway's own line builders produce keys the join reads.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mcp_security.behaviour import BehaviourConfig, Message
from mcp_security.behaviour import policy as learner
from mcp_security.behaviour.policy import (
    config_from_json,
    derive_policy,
    derive_policy_v5,
    learned_calls,
    messages_from_log,
)
from mcp_security.gateway import wire_log

DAY = 86_400.0
T0 = 20_602 * DAY + 10 * 3_600.0  # 10:00 UTC
V5 = BehaviourConfig(design="v5")
CALL = "tools/call"


def _line(**fields: object) -> dict:
    """A log line: keys with dots are written as given, None values left out (as the gateway
    does); ``direction`` and the rest are shorthands."""
    renames = {
        "direction": "gateway.direction",
        "exchange": "gateway.exchange_id",
        "rid": "jsonrpc.request.id",
        "method": "mcp.method.name",
        "tool": "gen_ai.tool.name",
        "agent_id": "gateway.agent_id",
        "baseline": "gateway.baseline_key",
        "arg_bytes": "gateway.arg_bytes",
        "zone": "gateway.zone",
        "outcome": "gateway.outcome",
        "decision": "gateway.decision",
    }
    return {renames.get(k, k): v for k, v in fields.items() if v is not None}


def _request(
    ts: float, exchange: str, tool: str = "read", rid: str = "1", **fields: object
) -> dict:
    return _line(
        ts=ts,
        direction="agent->server",
        exchange=exchange,
        rid=rid,
        method=CALL,
        tool=tool,
        **fields,
    )


def _decision(ts: float, exchange: str, **behaviour: object) -> dict:
    decision = {"behaviour": 1.0, **{f"behaviour_{k}": v for k, v in behaviour.items()}}
    return _line(ts=ts, direction="gateway", exchange=exchange, rid="1", decision=decision)


def _reply(ts: float, exchange: str, outcome: str, rid: str | None = "1") -> dict:
    return _line(ts=ts, direction="server->agent", exchange=exchange, rid=rid, outcome=outcome)


def test_the_join_reads_the_gateways_own_field_names() -> None:
    for name in (
        "TO_SERVER",
        "FROM_GATEWAY",
        "BASELINE_KEY_FIELD",
        "ZONE_FIELD",
        "LOGICAL_CALL_FIELD",
        "OUTCOME_FIELD",
        "ARG_BYTES_FIELD",
    ):
        assert getattr(learner, name) == getattr(wire_log, name), name
    exchange = wire_log.Exchange("github", "alice", None, "POST", agent_id="tok-alice")
    call = {"jsonrpc": "2.0", "id": 7, "method": CALL, "params": {"name": "get_file"}}
    book = wire_log.SessionBook()
    request = wire_log.build_record(exchange, book, wire_log.TO_SERVER, None, call)
    decision = wire_log.decision_record(
        exchange, book, call, {"behaviour_asset": "repo-1"}, None, request["ts"]
    )
    (message,) = messages_from_log([request, decision], design="v5")
    assert (message.agent, message.tool, message.asset) == ("tok-alice", "get_file", "repo-1")


def test_a_decision_joins_its_request_by_key_not_by_position() -> None:
    lines = [
        _request(T0, "e1", "get_file", agent_id="tok", baseline="key-a", zone="Europe/Berlin"),
        _request(T0 + 1, "e2", "list_issues", agent_id="tok", baseline="key-a"),
        _decision(T0 + 1, "e2", asset="repo-2", tool="list_issues:all"),  # e2 first
        _decision(
            T0,
            "e1",
            asset="repo-1",
            more_assets=["fork-1"],
            operation="write",
            sensitivity=4,
            tool="get_file",
        ),
        _reply(T0 + 2, "e1", "accepted"),
    ]
    first, second = messages_from_log(lines, design="v5")
    assert first == Message(
        T0,
        "key-a",
        CALL,
        tool="get_file",
        asset="repo-1",
        more_assets=("fork-1",),
        sensitivity=4,
        operation="write",
        zone="Europe/Berlin",
        outcome="accepted",
    )
    assert (second.tool, second.asset, second.outcome) == ("list_issues:all", "repo-2", None)


def test_v1_to_v4_read_the_request_lines_alone_as_before() -> None:
    lines = [
        _request(T0, "e1", agent_id="tok", baseline="key-a", arg_bytes=90),
        _decision(T0, "e1", asset="repo-1"),
    ]
    (message,) = messages_from_log(lines)
    assert (message.agent, message.asset, message.arg_bytes) == ("tok", None, None)
    with pytest.raises(ValueError, match="design must be one of"):
        messages_from_log(lines, design="v6")


def test_a_rejected_call_is_read_and_never_learned() -> None:
    lines = [
        _request(T0, "e1", baseline="k"),
        _reply(T0 + 1, "e1", "rejected"),
        _request(T0 + 2, "e2", baseline="k"),
        _request(T0 + 2, "e2", baseline="k", rid="2"),
        _reply(T0 + 3, "e2", "rejected", rid=None),  # a bodiless 400: every call of e2
        _request(T0 + 4, "e3", baseline="k"),
        _reply(T0 + 5, "e3", "accepted"),
    ]
    messages = messages_from_log(lines, design="v5")
    assert [m.outcome for m in messages] == ["rejected", "rejected", "rejected", "accepted"]
    assert [m.ts - T0 for m in learned_calls(messages, V5)] == [4]


def test_late_decisions_of_the_windows_last_calls_are_still_joined() -> None:
    lines = [
        _request(T0, "e0", baseline="k"),
        _request(T0 + DAY - 1, "e1", baseline="k"),
        _request(T0 + DAY + 10, "e2", baseline="k"),  # past the window: not read
        _decision(T0 + DAY - 1, "e1", asset="repo-late"),  # written after it
        _request(T0 + DAY + 2 * learner.JOIN_GRACE_S, "e3", baseline="k"),  # stops reading
        _decision(T0, "e0", asset="never-read"),
    ]
    messages = messages_from_log(lines, days=1, design="v5")
    assert [(m.ts - T0, m.asset) for m in messages] == [(0, None), (DAY - 1, "repo-late")]


def _traffic() -> list[Message]:
    """10 callers x 25 days of calls cycling 4 repositories (and their forks) in 30 minutes,
    with argument sizes and operations: enough agent-days for every line."""
    out = []
    for a in range(10):
        for d in range(25):
            for i in range(30):
                out.append(
                    Message(
                        T0 + d * DAY + a * 2_000 + i * 60.0,
                        f"key-{a}",
                        CALL,
                        tool="get_file" if i % 3 else "push_files",
                        asset=f"repo{i % 4}",
                        more_assets=(f"fork{i % 4}",),
                        operation="read" if i % 3 else "write",
                        arg_bytes=200 + 37 * ((a + d + i) % 11),
                        size=900,
                    )
                )
    return out


def _v5_log_of(messages: list[Message]) -> list[dict]:
    """``messages`` as a v5 gateway would log them, each decision written after the next
    request (background scoring)."""
    lines: list[dict] = []
    for i, m in enumerate(messages):
        lines.append(
            _request(
                m.ts,
                f"e{i}",
                m.tool,
                agent_id=f"token-{i % 3}",
                baseline=m.agent,
                arg_bytes=m.arg_bytes,
                **{"gateway.message_bytes": m.size},
            )
        )
        if i:
            prev = messages[i - 1]
            lines.append(
                _decision(
                    prev.ts,
                    f"e{i - 1}",
                    tool=prev.tool,
                    asset=prev.asset,
                    more_assets=list(prev.more_assets),
                    operation=prev.operation,
                )
            )
    last = messages[-1]
    lines.append(
        _decision(
            last.ts,
            f"e{len(messages) - 1}",
            tool=last.tool,
            asset=last.asset,
            more_assets=list(last.more_assets),
            operation=last.operation,
        )
    )
    return lines


def test_sweep_learned_from_a_v5_log_equals_sweep_from_the_same_calls() -> None:
    traffic = sorted(_traffic(), key=lambda m: m.ts)
    from_log = derive_policy_v5(messages_from_log(_v5_log_of(traffic), design="v5"), V5)
    assert from_log == derive_policy_v5(traffic, V5)
    assert from_log.many_assets_per_hour == 8  # 4 repositories and their 4 forks (AI-12)
    v4_driver = [  # a v4 gateway's decisions carry no behaviour_* inputs: sweep stays off
        {k: v for k, v in line.items() if k != "gateway.decision"} for line in _v5_log_of(traffic)
    ]
    assert (
        derive_policy_v5(messages_from_log(v4_driver, design="v5"), V5).many_assets_per_hour is None
    )


def _write_log(path: Path, lines: list[dict]) -> None:
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


def test_the_cli_learns_a_v5_policy_and_keeps_v4s(tmp_path, monkeypatch, capsys) -> None:
    traffic = sorted(_traffic(), key=lambda m: m.ts)
    log = tmp_path / "route.jsonl"
    _write_log(log, _v5_log_of(traffic))
    for design in ("v5", "v4"):
        out = tmp_path / f"{design}.json"
        argv = ["policy", "--log", str(log), "--out", str(out), "--design", design]
        monkeypatch.setattr(sys, "argv", argv)
        learner.main()
        written = config_from_json(json.loads(out.read_text(encoding="utf-8")))
        messages = messages_from_log(_v5_log_of(traffic), design=design)
        assert written == derive_policy(messages, base=BehaviourConfig(design=design))
    v5 = config_from_json(json.loads((tmp_path / "v5.json").read_text(encoding="utf-8")))
    v4 = config_from_json(json.loads((tmp_path / "v4.json").read_text(encoding="utf-8")))
    assert (v5.design, v5.many_assets_per_hour) == ("v5", 8)
    assert (v4.design, v4.many_assets_per_hour) == ("v4", None)  # a log alone: no assets
    assert "design v5" in capsys.readouterr().out
