"""Turn MCPHunt agent traces into gateway logs, one per MCP server, for offline scoring.

MCPHunt (https://huggingface.co/datasets/mcphunt-benchmark/mcphunt-agent-traces, CC-BY-4.0)
recorded every tool call five models made against eight real MCP servers in one simulated
team workspace. Each call becomes the two lines the gateway writes for it (the request, then
the reply) in ``gateway-log/3`` shape, so ``mcp_security.gateway.score`` scores it as if the
gateway had stood in front of the server. Each model is one agent (``gateway.agent_id``); each
run is one session per server it used, opened by an ``initialize`` exchange. Reply bodies are
not kept (as with ``log_bodies: requests``): a failed call carries ``error.type: tool_error``.

Two clocks:

* ``real``: the recorded times. Each model's runs fall within one to three days, in blocks
  (all risky variants, then benign, then hard negatives).
* ``spread``: each model's runs in a seeded random order, spread over ``--days`` days from
  ``SPREAD_START``, a few per day in office hours; the timing inside a run is kept.

Writes ``<out>/<server>.jsonl``, ``<out>/calls.csv`` (one row per call with MCPHunt's labels;
joins the scored CSV on ``session`` + ``ts``) and ``<out>/meta.json``.

    uv run python scripts/mcphunt_to_gateway_log.py --traces external/mcphunt/traces \\
        --out external/mcphunt/gateway_logs/real --clock real
    uv run python scripts/mcphunt_to_gateway_log.py --traces external/mcphunt/traces \\
        --out external/mcphunt/gateway_logs/spread90 --clock spread --days 90
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mcp_security.gateway.wire_log import (
    CALL_METHOD,
    EXECUTE_TOOL,
    INIT_METHOD,
    SCHEMA,
    TO_AGENT,
    TO_SERVER,
    TOOL_ERROR,
)

CLOCKS = ("real", "spread")
DEFAULT_DAYS = 90
DEFAULT_SEED = 0
#: Day one of the spread clock: a Monday, midnight UTC.
SPREAD_START = datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp()
OFFICE_START_S = 9 * 3600  # the first run of a day starts at 09:00 UTC
RUN_GAP_S = 50 * 60  # between two runs of one agent on one day
AGENT_OFFSET_S = 7 * 60  # between agents, so their runs interleave
DAY_S = 86_400
INIT_LEAD_S = 0.05  # the initialize exchange just before a session's first call
PROTOCOL_VERSION = "2025-06-18"
CLIENT = "mcphunt-agent"
UNKNOWN_SERVER = "unknown"  # MCPHunt's label for a call to a tool no server has
LABEL_COLUMNS = [
    "route", "agent", "session", "ts", "trace_id", "task_id", "task_category",
    "risk_mechanism", "env_type", "outcome", "turn", "tool", "success",
    "canary_in_args", "canary_in_result",
]


@dataclass(frozen=True)
class Call:
    """One recorded tool call, placed on the chosen clock."""

    route: str
    agent: str
    session: str
    request_id: str
    start: float
    end: float
    tool: str
    args: dict
    success: bool
    labels: dict


def load_traces(traces_dir: Path) -> dict[str, list[dict]]:
    """Every model's runs, keyed by the model's file stem, each list in recorded order."""
    files = sorted(traces_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no MCPHunt trace files (*.json) in {traces_dir}")
    runs = {}
    for path in files:
        traces = json.loads(path.read_text(encoding="utf-8"))["traces"]
        runs[path.stem] = sorted(traces, key=lambda t: t["collection_timestamp"])
    return runs


def session_id(agent: str, trace_id: str, route: str) -> str:
    """A stable pseudonym for one run's session on one server."""
    return hashlib.sha256(f"{agent}|{trace_id}|{route}".encode()).hexdigest()[:16]


def spread_starts(agent_index: int, traces: list[dict], days: int, seed: int) -> dict[str, float]:
    """When each run starts on the spread clock: a seeded shuffle, then a few runs a day."""
    order = list(traces)
    random.Random(f"{seed}:{agent_index}").shuffle(order)
    starts, per_day = {}, Counter()
    for index, trace in enumerate(order):
        day = index * days // len(order)
        slot = per_day[day]
        per_day[day] += 1
        starts[trace["trace_id"]] = (
            SPREAD_START + day * DAY_S + OFFICE_START_S + agent_index * AGENT_OFFSET_S
            + slot * RUN_GAP_S
        )
    return starts


def _event_times(event: dict) -> tuple[float, float]:
    """(start, end) as recorded: MCPHunt stamps a call when it returns."""
    end = event.get("timestamp")
    if not isinstance(end, (int, float)):
        raise ValueError(f"event without a numeric timestamp: {event.get('tool')!r}")
    return end - (event.get("latency_ms") or 0) / 1000, end


def run_calls(agent: str, trace: dict, run_start: float | None) -> tuple[list[Call], Counter]:
    """The run's calls on the clock (``run_start`` None: the recorded clock), and what was
    skipped: calls MCPHunt could not route to a server."""
    skipped: Counter = Counter()
    events = [e for e in trace["events"] if e.get("server") != UNKNOWN_SERVER]
    skipped["unknown_server"] = len(trace["events"]) - len(events)
    if not events:
        return [], skipped
    first_start = _event_times(events[0])[0]
    shift = 0.0 if run_start is None else run_start - first_start
    labels = {key: trace.get(key) for key in (
        "trace_id", "task_id", "task_category", "risk_mechanism", "env_type", "outcome")}
    counters: Counter = Counter()
    calls = []
    for event in events:
        route = event["server"]
        start, end = _event_times(event)
        args = event.get("args")
        if not isinstance(args, dict):
            skipped["args_not_object"] += 1
            args = {}
        counters[route] += 1
        calls.append(Call(
            route=route,
            agent=agent,
            session=session_id(agent, trace["trace_id"], route),
            request_id=str(counters[route]),
            start=round(start + shift, 6),
            end=round(end + shift, 6),
            tool=event["tool"],
            args=args,
            success=bool(event.get("success")),
            labels={**labels, "turn": event.get("turn"),
                    "canary_in_args": bool(event.get("canary_in_args")),
                    "canary_in_result": bool(event.get("canary_in_result"))},
        ))
    return calls, skipped


def _line(route: str, agent: str, ts: float, direction: str, **fields: object) -> dict:
    """The fields every line of an imported log carries."""
    return {
        "schema": SCHEMA,
        "ts": ts,
        "log.level": "info",
        "gateway.route": route,
        "gateway.direction": direction,
        "gateway.agent_id": agent,
        "gateway.agent": agent,
        "gateway.client": f"{CLIENT}/{agent}",
        **fields,
    }


def initialize_lines(call: Call) -> list[dict]:
    """The initialize request and reply that open a call's session."""
    request = {"jsonrpc": "2.0", "id": "0", "method": INIT_METHOD, "params": {
        "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
        "clientInfo": {"name": CLIENT, "version": call.agent}}}
    reply = {"jsonrpc": "2.0", "id": "0", "result": {"protocolVersion": PROTOCOL_VERSION}}
    ts = round(call.start - INIT_LEAD_S, 6)
    return [
        _line(call.route, call.agent, ts, TO_SERVER, **{
            "mcp.method.name": INIT_METHOD, "jsonrpc.request.id": "0",
            "gateway.message_bytes": len(json.dumps(request).encode()), "message": request}),
        _line(call.route, call.agent, ts, TO_AGENT, **{
            "mcp.session.id": call.session, "mcp.method.name": INIT_METHOD,
            "jsonrpc.request.id": "0", "message": reply}),
    ]


def call_lines(call: Call) -> list[dict]:
    """The request line and the reply line the gateway writes for one tool call."""
    request = {"jsonrpc": "2.0", "id": call.request_id, "method": CALL_METHOD,
               "params": {"name": call.tool, "arguments": call.args}}
    common = {"mcp.session.id": call.session, "mcp.method.name": CALL_METHOD,
              "jsonrpc.request.id": call.request_id}
    reply = {**common, "gateway.duration_s": round(call.end - call.start, 6)}
    if not call.success:
        reply["error.type"] = TOOL_ERROR
    return [
        _line(call.route, call.agent, call.start, TO_SERVER, **common, **{
            "gen_ai.operation.name": EXECUTE_TOOL, "gen_ai.tool.name": call.tool,
            "gateway.message_bytes": len(json.dumps(request).encode()), "message": request}),
        _line(call.route, call.agent, call.end, TO_AGENT, **reply),
    ]


def route_lines(calls: list[Call]) -> list[dict]:
    """One server's log lines in time order: each session opens before its first call."""
    keyed: list[tuple[float, int, int, dict]] = []
    opened: set[str] = set()
    for order, call in enumerate(calls):
        if call.session not in opened:
            opened.add(call.session)
            keyed += [(line["ts"], 0, order, line) for line in initialize_lines(call)]
        request, reply = call_lines(call)
        keyed.append((request["ts"], 1, order, request))
        keyed.append((reply["ts"], 2, order, reply))
    keyed.sort(key=lambda item: item[:3])
    return [line for *_, line in keyed]


def convert(traces_dir: Path, out_dir: Path, clock: str, days: int, seed: int) -> dict:
    """Write one gateway log per server, the label table and a summary; return the summary."""
    if clock not in CLOCKS:
        raise ValueError(f"clock must be one of {CLOCKS}, not {clock!r}")
    if days < 1:
        raise ValueError("days must be at least 1")
    by_route: dict[str, list[Call]] = {}
    skipped: Counter = Counter()
    runs = load_traces(traces_dir)
    for agent_index, (agent, traces) in enumerate(runs.items()):
        starts = spread_starts(agent_index, traces, days, seed) if clock == "spread" else {}
        for trace in traces:
            calls, dropped = run_calls(agent, trace, starts.get(trace["trace_id"]))
            skipped.update(dropped)
            for call in calls:
                by_route.setdefault(call.route, []).append(call)

    out_dir.mkdir(parents=True, exist_ok=True)
    for route, calls in sorted(by_route.items()):
        with (out_dir / f"{route}.jsonl").open("w", encoding="utf-8") as handle:
            for line in route_lines(calls):
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    write_labels(by_route, out_dir / "calls.csv")
    summary = {
        "source": str(traces_dir),
        "source_sha256": {p.name: _sha256(p) for p in sorted(traces_dir.glob("*.json"))},
        "clock": clock,
        "days": days if clock == "spread" else None,
        "seed": seed if clock == "spread" else None,
        "agents": {agent: len(traces) for agent, traces in runs.items()},
        "calls": {route: len(calls) for route, calls in sorted(by_route.items())},
        "skipped": dict(skipped),
    }
    (out_dir / "meta.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    return summary


def write_labels(by_route: dict[str, list[Call]], path: Path) -> None:
    """One row per call with MCPHunt's labels, keyed like the scored CSV (session, ts)."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_COLUMNS)
        writer.writeheader()
        for route, calls in sorted(by_route.items()):
            for call in calls:
                writer.writerow({"route": route, "agent": call.agent, "session": call.session,
                                 "ts": call.start, "tool": call.tool, "success": call.success,
                                 **call.labels})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> None:
    """Convert MCPHunt traces: ``--traces DIR --out DIR --clock real|spread [--days N]``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--traces", type=Path, required=True, help="MCPHunt main/ trace files")
    parser.add_argument("--out", type=Path, required=True, help="where to write the logs")
    parser.add_argument("--clock", choices=CLOCKS, default="real")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="spread clock only")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="spread clock only")
    args = parser.parse_args()
    summary = convert(args.traces, args.out, args.clock, args.days, args.seed)
    print(json.dumps({k: summary[k] for k in ("clock", "agents", "calls", "skipped")}, indent=1))


if __name__ == "__main__":
    main()
