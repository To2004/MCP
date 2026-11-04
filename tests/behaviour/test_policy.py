"""The behaviour policy learned from traffic: limits per agent-day, required earlier steps."""

from __future__ import annotations

import json

import pytest

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message
from mcp_security.behaviour.engine import SEQUENCE
from mcp_security.behaviour.policy import (
    config_from_json,
    config_to_json,
    derive_policy,
    messages_from_log,
)

T0 = 1_780_000_000.0
DAY = 86_400.0


def _calls(agent: str, day: int, n: int, gap: float, size: int = 200, tool: str = "read"):
    return [
        Message(
            T0 + day * DAY + i * gap, agent, "tools/call", f"{agent}-{day}", tool=tool, size=size
        )
        for i in range(n)
    ]


def test_limits_come_from_each_agent_days_busiest_moment_not_from_single_calls() -> None:
    # 200 agent-days with a busiest minute of 6 calls; one day with 60 in a minute
    traffic = [m for d in range(200) for m in _calls("a", d, 6, 5.0)] + _calls("a", 300, 60, 1.0)
    policy = derive_policy(traffic)
    assert policy.burst_per_minute == 6  # the 99.5th percentile of agent-days, not 60
    assert policy.request_limit_bytes == 1_000  # 200 bytes, rounded up to the next KB


def test_a_step_that_always_comes_first_becomes_required() -> None:
    traffic = []
    for s in range(100):
        tools = ["review", "merge"] if s % 2 else ["review", "comment"]
        traffic += [
            Message(T0 + s * 600 + i, "a", "tools/call", f"s{s}", tool=t)
            for i, t in enumerate(tools)
        ]
    policy = derive_policy(traffic, min_sessions=20)
    assert policy.requires_before == {
        "merge": frozenset({"review"}),
        "comment": frozenset({"review"}),
    }


def test_too_few_sessions_or_a_skipped_step_learns_nothing() -> None:
    traffic = []
    for s in range(100):
        tools = ["merge"] if s == 0 else ["review", "merge"]  # once without the review
        traffic += [
            Message(T0 + s * 600 + i, "a", "tools/call", f"s{s}", tool=t)
            for i, t in enumerate(tools)
        ]
    assert derive_policy(traffic, sequence_share=0.995).requires_before == {}
    assert derive_policy(traffic[:20], min_sessions=50).requires_before == {}


def test_a_learned_required_step_makes_the_engine_flag_a_session_without_it() -> None:
    policy = BehaviourConfig(requires_before={"merge": frozenset({"review"})}, warmup_calls=0)
    engine = BehaviourEngine(policy)
    engine.observe(Message(T0, "a", "tools/call", "s1", tool="review"))
    assert (
        SEQUENCE
        not in engine.observe(Message(T0 + 1, "a", "tools/call", "s1", tool="merge")).scores
    )
    assert SEQUENCE in engine.observe(Message(T0 + 9, "a", "tools/call", "s2", tool="merge")).scores


def test_a_policy_survives_json_and_rejects_unknown_keys() -> None:
    policy = BehaviourConfig(burst_per_minute=33, requires_before={"b": frozenset({"a", "c"})})
    assert config_from_json(json.loads(json.dumps(config_to_json(policy)))) == policy
    with pytest.raises(ValueError, match="unknown behaviour policy keys"):
        config_from_json({"burst_limit": 5})


def test_a_gateway_log_becomes_messages_and_only_the_first_days_are_read() -> None:
    def line(ts: float, method: str, direction: str = "agent->server", **extra) -> dict:
        return {
            "ts": ts,
            "gateway.direction": direction,
            "mcp.method.name": method,
            "gateway.agent_id": "alice",
            "mcp.session.id": "s1",
            "gateway.message_bytes": 90,
            **extra,
        }

    records = [
        line(T0, "initialize", **{"gateway.client": "cursor/1.4", "client.address": "10.0.0.1"}),
        line(T0 + 1, "tools/call", **{"gen_ai.tool.name": "read"}),
        line(T0 + 2, "tools/call", "server->agent"),  # a reply: not a request
        line(T0 + 3 * DAY, "tools/call", **{"gen_ai.tool.name": "write"}),
    ]
    messages = messages_from_log(records, days=1)
    assert [(m.method, m.tool) for m in messages] == [("initialize", None), ("tools/call", "read")]
    assert (messages[0].agent, messages[0].client, messages[0].size) == ("alice", "cursor/1.4", 90)


def test_request_limits_are_also_learned_per_tool_from_agent_days() -> None:
    comments = [m for d in range(100) for m in _calls("a", d, 3, 60.0, 900, "comment")]
    files = [m for d in range(100) for m in _calls("b", d, 3, 60.0, 80_000, "write_file")]
    rare = _calls("c", 0, 5, 60.0, 400, "rare_tool")  # one agent-day: no limit of its own
    policy = derive_policy(sorted(comments + files + rare, key=lambda m: m.ts))
    assert policy.request_limit_by_tool == {"comment": 1_000, "write_file": 80_000}
    assert policy.request_limit_bytes == 80_000  # one limit is set by the biggest tool


def test_the_many_assets_limit_comes_from_each_agent_days_busiest_hour() -> None:
    def day_of(agent: str, day: int, assets: int) -> list[Message]:
        return [
            Message(
                T0 + day * DAY + i * 60.0,
                agent,
                "tools/call",
                "s",
                tool="read",
                asset=f"repo{i % assets}",
            )
            for i in range(30)
        ]

    traffic = [m for d in range(200) for m in day_of("a", d, 4)] + day_of("a", 300, 30)
    assert derive_policy(traffic).many_assets_per_hour == 4  # not the one 30-asset hour
    assert derive_policy(_calls("a", 0, 5, 60.0)).many_assets_per_hour is None  # no assets


def test_written_required_steps_stay_and_learned_ones_are_added() -> None:
    written = BehaviourConfig(requires_before={"merge": frozenset({"review"})})
    traffic = []
    for s in range(100):
        traffic += [
            Message(T0 + s * 600 + i, "a", "tools/call", f"s{s}", tool=t)
            for i, t in enumerate(["plan", "deploy"])
        ]
    policy = derive_policy(traffic, base=written, min_sessions=20)
    assert policy.requires_before == {
        "merge": frozenset({"review"}),
        "deploy": frozenset({"plan"}),
    }


@pytest.mark.parametrize("design", ["v1", "v2", "v3"])
def test_the_design_and_the_per_tool_limits_survive_json(design) -> None:
    policy = BehaviourConfig(
        design=design, request_limit_by_tool={"comment": 15_000}, many_assets_per_hour=12
    )
    assert config_from_json(json.loads(json.dumps(config_to_json(policy)))) == policy
