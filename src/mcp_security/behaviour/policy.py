"""The behaviour layer's policy, learned from traffic for now: limits and required steps.

Until an organisation writes these down, they are read from its own ordinary traffic (no
labels needed), at the level of an *agent-day*: a busy agent makes hundreds of calls a day,
so a limit set on calls would still fire for him every day. Each limit is set so the rule
fires on at most ``1 - quantile`` of ordinary agent-days:

- ``burst_per_minute``: the agent-days' busiest minute (most tool calls in 60 s), at the
  quantile, rounded up;
- ``request_limit_bytes``: the agent-days' largest tool-call request, at the quantile,
  rounded up to the next KB;
- ``requires_before``: tool B requires tool A when, in at least ``sequence_share`` of the
  sessions where B was called, A was called earlier in the same session (and B was called in
  at least ``min_sessions`` sessions). B's required tools are "any one of".

The rule values themselves (0.9 -> x3.6, protocol skip 0.7 -> x1.9) stay as designed.

    uv run python -m mcp_security.behaviour.policy --log runs/gateway/github.jsonl \\
        --out runs/gateway/github.behaviour.json --days 30
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from collections.abc import Iterable
from dataclasses import asdict, fields, replace
from pathlib import Path

from mcp_security.behaviour.engine import CALL_METHOD, DAY_S, MINUTE_S, BehaviourConfig, Message

QUANTILE = 0.995  # a learned rule fires on at most 0.5% of ordinary agent-days
SEQUENCE_SHARE = 0.995
MIN_SESSIONS = 50
KB = 1_000
TO_SERVER = "agent->server"


def derive_policy(
    messages: Iterable[Message],
    base: BehaviourConfig | None = None,
    quantile: float = QUANTILE,
    sequence_share: float = SEQUENCE_SHARE,
    min_sessions: int = MIN_SESSIONS,
) -> BehaviourConfig:
    """``base`` with its limits and required steps read from ``messages`` (arrival order)."""
    base = base or BehaviourConfig()
    burst: dict[tuple[str, int], int] = defaultdict(int)  # agent-day -> busiest minute
    biggest: dict[tuple[str, int], int] = defaultdict(int)  # agent-day -> largest request
    recent: dict[str, deque] = defaultdict(deque)
    earlier: dict[tuple[str, str], set] = defaultdict(set)  # session -> tools so far
    sessions_with: Counter = Counter()  # tool -> sessions it was called in
    preceded: Counter = Counter()  # (tool, earlier tool) -> sessions
    for m in messages:
        if m.method != CALL_METHOD or not m.tool:
            continue
        day = (m.agent, int(m.ts // DAY_S))
        q = recent[m.agent]
        q.append(m.ts)
        while q and q[0] <= m.ts - MINUTE_S:
            q.popleft()
        burst[day] = max(burst[day], len(q))
        biggest[day] = max(biggest[day], m.size)
        if m.session:
            seen = earlier[(m.agent, m.session)]
            if m.tool not in seen:  # B's first call in this session
                sessions_with[m.tool] += 1
                for before in seen:
                    preceded[(m.tool, before)] += 1
            seen.add(m.tool)
    if not burst:
        return base
    requires: dict[str, set[str]] = defaultdict(set)
    for (tool, before), n in preceded.items():
        total = sessions_with[tool]
        if total >= min_sessions and n >= sequence_share * total:
            requires[tool].add(before)
    return replace(
        base,
        burst_per_minute=_quantile(list(burst.values()), quantile),
        request_limit_bytes=math.ceil(_quantile(list(biggest.values()), quantile) / KB) * KB,
        requires_before={tool: frozenset(before) for tool, before in requires.items()},
    )


def _quantile(values: list[int], q: float) -> int:
    values = sorted(values)
    return int(values[min(len(values) - 1, math.ceil(q * len(values)) - 1)])


def config_to_json(config: BehaviourConfig) -> dict:
    """A config as JSON-safe data (``requires_before`` sets become sorted lists)."""
    data = asdict(config)
    data["requires_before"] = {t: sorted(b) for t, b in config.requires_before.items()}
    return data


def config_from_json(data: dict) -> BehaviourConfig:
    """``config_to_json`` output back; unknown keys are an error, missing ones the default."""
    known = {f.name for f in fields(BehaviourConfig)}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"unknown behaviour policy keys: {sorted(unknown)}")
    data = dict(data)
    if "requires_before" in data:
        data["requires_before"] = {t: frozenset(b) for t, b in data["requires_before"].items()}
    return BehaviourConfig(**data)


def load_policy(path: str | Path) -> BehaviourConfig:
    return config_from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def messages_from_log(records: Iterable[dict], days: float | None = None) -> list[Message]:
    """The agent-to-server requests of a gateway log (gateway-log/2 or /3), as messages;
    ``days``: only the first ``days`` days of the log."""
    out: list[Message] = []
    start = None
    for record in records:
        if record.get("gateway.direction") != TO_SERVER:
            continue
        ts = record["ts"]
        start = ts if start is None else start
        if days is not None and ts - start > days * DAY_S:
            break
        message = record.get("message") or {}
        out.append(
            Message(
                ts=ts,
                agent=record.get("gateway.agent_id") or record.get("gateway.agent") or "gateway",
                method=record.get("mcp.method.name") or message.get("method") or "",
                session=record.get("mcp.session.id"),
                tool=record.get("gen_ai.tool.name"),
                address=record.get("client.address"),
                client=record.get("gateway.client"),
                size=record.get("gateway.message_bytes", 0),
            )
        )
    return out


def main() -> None:
    """Learn a route's behaviour policy from its gateway log and write it as JSON."""
    from mcp_security.gateway.log_file import read_log  # noqa: PLC0415 — CLI only

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", type=Path, required=True, help="the route's gateway log")
    parser.add_argument("--out", type=Path, required=True, help="where to write the policy")
    parser.add_argument("--days", type=float, default=None, help="learn from the first N days")
    args = parser.parse_args()
    messages = messages_from_log(read_log(args.log), args.days)
    policy = derive_policy(messages)
    args.out.write_text(json.dumps(config_to_json(policy), indent=1), encoding="utf-8")
    calls = sum(1 for m in messages if m.method == CALL_METHOD)
    print(
        f"{calls} tool calls -> {args.out}: burst > {policy.burst_per_minute}/min, "
        f"request > {policy.request_limit_bytes} B, "
        f"{len(policy.requires_before)} tools with a required earlier step"
    )


if __name__ == "__main__":
    main()
