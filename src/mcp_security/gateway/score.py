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
from mcp_security.gateway.wire_log import TO_AGENT, TO_SERVER, read_log

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


def pair_calls(records: list[dict]) -> list[dict]:
    """One row per ``tools/call``, in request order, with how the server answered it."""
    calls: list[dict] = []
    pending: dict[tuple, dict] = {}
    for record in records:
        message = record.get("message") or {}
        key = (record["gateway.agent"], record.get("mcp.session.id"), message.get("id"))
        direction = record["gateway.direction"]
        if direction == TO_SERVER and message.get("method") == "tools/call":
            params = message.get("params") or {}
            call = {
                "ts": record["ts"],
                "agent": record["gateway.agent"],
                "session": record.get("mcp.session.id"),
                "tool": params.get("name"),
                "args": params.get("arguments") or {},
                "outcome": "no_response",
                "latency_s": None,
            }
            calls.append(call)
            pending[key] = call
        elif direction == TO_AGENT and key in pending:
            call = pending.pop(key)
            call["outcome"] = _outcome(message)
            call["latency_s"] = round(record["ts"] - call["ts"], 3)
    return calls


def _outcome(message: dict) -> str:
    if "error" in message:
        return "rpc_error"
    return "tool_error" if (message.get("result") or {}).get("isError") else "ok"


def score_calls(calls: list[dict], scorer: RouteScorer | None) -> list[dict]:
    """Each call with its score, in order; a route without a scan gets no score."""
    if scorer is None:
        return [{**call, "reasons": "route not scanned"} for call in calls]
    return [{**call, **scorer.score(call["tool"], call["args"], call["ts"])} for call in calls]


def write_csv(rows: list[dict], path: Path) -> None:
    """The scored calls, one row each; ``args`` as JSON."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "args": json.dumps(row["args"], ensure_ascii=False)})


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
