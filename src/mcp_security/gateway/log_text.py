"""Formatting shared by the two log views: sizes, times, outcomes, levels, the summary."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

from mcp_security.gateway.wire_log import (
    CALL_METHOD,
    FROM_GATEWAY,
    INFO,
    LIST_METHOD,
    NOTICE_LEVELS,
    TO_AGENT,
    TO_SERVER,
)

MAX_VALUE_CHARS = 48
SHORT_ID = 8  # session, request and digest ids are shown by their first characters
KILOBYTE = 1024
SECONDS_PER_DAY = 86_400
RUN_NOTICES = ("gateway_started", "gateway_stopped")
REASONS = {"unknown_token": "token matches no agent", "no_bearer_token": "no bearer token"}


def exchange_key(record: dict, number: int) -> str:
    """The exchange a record belongs to. Logs before gateway-log/3 have no exchange id, so
    a request and its reply are matched by session and JSON-RPC id instead."""
    if record.get("gateway.exchange_id"):
        return str(record["gateway.exchange_id"])
    rpc_id = record.get("jsonrpc.request.id")
    if rpc_id is None:
        rpc_id = (record.get("message") or {}).get("id")
    if rpc_id is None:
        return f"line-{number}"
    return f"rpc:{record.get('mcp.session.id')}:{rpc_id}"


def overview(records: list[dict], chain: str) -> list[str]:
    """Two header lines: route, format, size and chain status; then the time span."""
    times = timestamps(records)
    schemas = sorted({r.get("schema", "v1") for r in records})
    route = next((r["gateway.route"] for r in records if r.get("gateway.route")), "?")
    lines = [f"route {route}  ·  {', '.join(schemas)}  ·  {len(records)} records  ·  {chain}"]
    if times:
        start, end = (datetime.fromtimestamp(t, timezone.utc) for t in (min(times), max(times)))
        seconds = max(times) - min(times)
        lines.append(f"{start:%Y-%m-%d %H:%M:%S} – {end:%H:%M:%S} UTC  ·  {seconds:.1f} s")
    return lines


def timestamps(records: list[dict]) -> list[float]:
    return [r["ts"] for r in records if isinstance(r.get("ts"), (int, float))]


def level_of(record: dict) -> str:
    """The line's severity: its ``log.level``, or — in logs from before it — the notice's."""
    return str(record.get("log.level") or NOTICE_LEVELS.get(record.get("gateway.notice", ""), INFO))


def outcome(record: dict) -> str:
    """How a reply ended, in words: ok, tool error, a JSON-RPC code, or what was listed."""
    method, message = record.get("mcp.method.name"), record.get("message")
    if record.get("rpc.response.status_code"):
        return f"JSON-RPC error {record['rpc.response.status_code']}"
    if record.get("error.type"):
        kind = record["error.type"]
        return "tool error" if kind == "tool_error" else f"error {kind}"
    if method == CALL_METHOD:
        return "ok"
    if method == LIST_METHOD and isinstance(message, dict):
        return f"{len((message.get('result') or {}).get('tools') or [])} tools"
    return ""


def clock(record: dict, with_date: bool = False) -> str:
    """``HH:MM:SS.mmm`` in UTC, with the date in front when ``with_date``."""
    ts = record.get("ts")
    if not isinstance(ts, (int, float)):
        return ""
    moment = datetime.fromtimestamp(ts, timezone.utc)
    stamp = f"{moment:%H:%M:%S}.{moment.microsecond // 1000:03d}"
    return f"{moment:%Y-%m-%d} {stamp}" if with_date else stamp


def spans_days(records: list[dict]) -> bool:
    times = timestamps(records)
    return bool(times) and int(min(times) // SECONDS_PER_DAY) != int(max(times) // SECONDS_PER_DAY)


def value_text(value: object) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= MAX_VALUE_CHARS else text[: MAX_VALUE_CHARS - 1] + "…"


def size_text(count: object) -> str:
    if not isinstance(count, int) or count <= 0:
        return ""
    return f"{count} B" if count < KILOBYTE else f"{count / KILOBYTE:.1f} KB"


def pad(text: str, width: int) -> str:
    return text if len(text) >= width else text + " " * (width - len(text))


def call_arguments(record: dict) -> dict | None:
    """A tool call's arguments, if the request body was kept."""
    args = ((record.get("message") or {}).get("params") or {}).get("arguments")
    return args if isinstance(args, dict) else None


def summary_lines(records: list[dict], exchanges: int) -> list[str]:
    """Counts at the end of a view: calls and how they ended, by agent, notices, top risk."""
    calls = [
        r
        for r in records
        if r.get("gateway.direction") == TO_SERVER and r.get("mcp.method.name") == CALL_METHOD
    ]
    replies = Counter(
        outcome(r)
        for r in records
        if r.get("gateway.direction") == TO_AGENT and r.get("mcp.method.name") == CALL_METHOD
    )
    agents = Counter(
        f"{r.get('gateway.agent')} ({r['gateway.agent_id']})"
        if r.get("gateway.agent_id")
        else str(r.get("gateway.agent"))
        for r in calls
    )
    notices = Counter(
        r["gateway.notice"]
        for r in records
        if r.get("gateway.notice") and r["gateway.notice"] not in RUN_NOTICES
    )
    verdicts = [
        r for r in records if r.get("gateway.direction") == FROM_GATEWAY and "gateway.decision" in r
    ]
    top = max(verdicts, key=lambda r: r["gateway.decision"].get("risk") or -1, default=None)
    ended = ", ".join(f"{n} {k}" for k, n in replies.most_common())
    lines = [
        "== Summary " + "=" * 72,
        f"   exchanges {exchanges}  ·  tool calls {len(calls)}" + (f" ({ended})" if ended else ""),
        "   calls by agent  " + ", ".join(f"{a} {n}" for a, n in agents.most_common()),
        "   notices  " + (", ".join(f"{k} {n}" for k, n in notices.most_common()) or "none"),
    ]
    if top and top["gateway.decision"].get("risk") is not None:
        d = top["gateway.decision"]
        tool = top.get("gen_ai.tool.name")
        lines.append(f"   highest risk  {d['risk']:.1f} {d.get('band', '')}  {tool}")
    return lines
