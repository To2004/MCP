"""Score a gateway log offline: pair each ``tools/call`` with its result, then score it.

The scoring is ``framework.RouteScorer``, the same object the gateway runs live before
forwarding, fed the calls in the same order — so re-scoring a log gives the numbers the
gateway logged, and re-scoring it after a new scan shows what that scan changes. Nothing
here touches the network. Routes without a scan are listed with their calls but no score.

    uv run python -m mcp_security.gateway.score --config src/mcp_security/gateway/routes.json \
        --route github
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.proxy import load_config
from mcp_security.gateway.log_file import read_log
from mcp_security.gateway.wire_log import CALL_METHOD, TO_AGENT, TO_SERVER, TOOL_ERROR

COLUMNS = [
    "ts",
    "agent",
    "session",
    "tool",
    "args",
    "outcome",
    "latency_s",
    "asset",
    "basis",
    "sensitivity",
    "impact",
    "blast",
    "band",
    "cell",
    "factor",
    "risk",
    "input_level",
    "input_set_by",
    "score_us",
    "reasons",
]
TOP_N = 10
ARGS_NOT_LOGGED = "arguments not logged (log_bodies: none)"


def pair_calls(records: list[dict]) -> list[dict]:
    """One row per ``tools/call``, in request order, with how the server answered it.

    Works from the line's own fields, so a log kept without reply bodies still pairs; a
    call whose request body was not kept (``log_bodies: none``) has ``args`` None.
    """
    calls: list[dict] = []
    pending: dict[tuple, dict] = {}
    for record in records:
        message = record.get("message")
        key = (record.get("gateway.agent"), record.get("mcp.session.id"), _request_id(record))
        direction = record["gateway.direction"]
        if direction == TO_SERVER and _method(record) == CALL_METHOD:
            params = (message or {}).get("params") or {}
            call = {
                "ts": record["ts"],
                "agent": record.get("gateway.agent"),
                "session": record.get("mcp.session.id"),
                "tool": params.get("name") or record.get("gen_ai.tool.name"),
                "args": (params.get("arguments") or {}) if message is not None else None,
                "outcome": "no_response",
                "latency_s": None,
            }
            calls.append(call)
            pending[key] = call
        elif direction == TO_AGENT and key in pending:
            call = pending.pop(key)
            call["outcome"] = _outcome(record)
            call["latency_s"] = round(record["ts"] - call["ts"], 3)
    return calls


def _request_id(record: dict) -> object:
    """The JSON-RPC id: the line's field (v2, v3), else the message's own (v1)."""
    if "jsonrpc.request.id" in record:
        return record["jsonrpc.request.id"]
    return (record.get("message") or {}).get("id")


def _method(record: dict) -> str | None:
    return record.get("mcp.method.name") or (record.get("message") or {}).get("method")


def _outcome(record: dict) -> str:
    message = record.get("message")
    if message is None:  # body not kept: the line's fields say how it ended
        if "rpc.response.status_code" in record:
            return "rpc_error"
        return TOOL_ERROR if record.get("error.type") == TOOL_ERROR else "ok"
    if "error" in message:
        return "rpc_error"
    return TOOL_ERROR if (message.get("result") or {}).get("isError") else "ok"


def score_calls(calls: list[dict], scorer: RouteScorer | None) -> list[dict]:
    """Each call with its score, in order; a route without a scan gets no score, and nor
    does a call whose arguments were not logged (the live decision line still has it)."""
    if scorer is None:
        return [{**call, "reasons": "route not scanned"} for call in calls]
    return [
        {**call, **scorer.score(call["tool"], call["args"], call["ts"])}
        if call["args"] is not None
        else {**call, "reasons": ARGS_NOT_LOGGED}
        for call in calls
    ]


def write_csv(rows: list[dict], path: Path) -> None:
    """The scored calls, one row each; ``args`` as JSON."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            args = None if row["args"] is None else json.dumps(row["args"], ensure_ascii=False)
            writer.writerow({**row, "args": args})


def main() -> None:
    """Score one route's log: ``--config routes.json --route github``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--route", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    upstream = config.upstreams[args.route]
    log_path = config.log_dir / f"{args.route}.jsonl"
    calls = pair_calls(read_log(log_path))
    artifacts = load_artifacts(
        args.route, upstream.scan, upstream.breadth, upstream.rules, upstream.kind
    )
    rows = score_calls(calls, RouteScorer(args.route, artifacts) if artifacts else None)

    out = log_path.with_name(f"{args.route}_scored.csv")
    write_csv(rows, out)
    print(f"{len(rows)} tool calls from {log_path} -> {out}")
    timed = sorted(row["score_us"] for row in rows if "score_us" in row)
    if timed:
        print(f"scoring time per call: median {timed[len(timed) // 2]} us, max {timed[-1]} us")
    ranked = sorted((r for r in rows if r.get("risk") is not None), key=lambda r: -r["risk"])
    for row in ranked[:TOP_N]:
        print(
            f"  R={row['risk']:>7.2f}  cell={row['cell']:>5.1f}  x{row['factor']:.2f}  "
            f"{row['tool']}  {json.dumps(row['args'])[:60]}"
        )


if __name__ == "__main__":
    main()
