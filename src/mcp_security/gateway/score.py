"""Score a gateway log offline: pair each ``tools/call`` with its result, then ``cell × B × L``.

Nothing here touches the network or the running gateway, so it can be re-run at any time —
after a new scan, or a change to the runtime factor — and gives the same numbers for the
same log. Routes without a scan are listed with their calls but no score.

    uv run python -m mcp_security.gateway.score --config src/mcp_security/gateway/routes.json \
        --route github
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from types import ModuleType

from mcp_security.binding.scoring import MatrixScorer
from mcp_security.gateway.proxy import TO_AGENT, TO_SERVER, load_config

REPO_ROOT = Path(__file__).resolve().parents[3]
DYNAMIC_DIR = REPO_ROOT / "scripts" / "dynamic_design"
DEFAULT_SCORE_MAX = 125.0
GATEWAY_ORG = "gateway"
COLUMNS = [
    "ts",
    "agent",
    "session",
    "tool",
    "args",
    "outcome",
    "latency_s",
    "cell",
    "asset",
    "basis",
    "factor",
    "risk",
    "reasons",
]
TOP_N = 10


def read_log(path: Path) -> list[dict]:
    """Every record in a gateway JSONL log, in the order it was written."""
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def pair_calls(records: list[dict]) -> list[dict]:
    """One row per ``tools/call``, in request order, with how the server answered it."""
    calls: list[dict] = []
    pending: dict[tuple, dict] = {}
    for record in records:
        message = record.get("message") or {}
        key = (record["agent"], record["session"], message.get("id"))
        if record["direction"] == TO_SERVER and message.get("method") == "tools/call":
            params = message.get("params") or {}
            call = {
                "ts": record["ts"],
                "agent": record["agent"],
                "session": record["session"],
                "tool": params.get("name"),
                "args": params.get("arguments") or {},
                "outcome": "no_response",
                "latency_s": None,
            }
            calls.append(call)
            pending[key] = call
        elif record["direction"] == TO_AGENT and key in pending:
            call = pending.pop(key)
            call["outcome"] = _outcome(message)
            call["latency_s"] = round(record["ts"] - call["ts"], 3)
    return calls


def _outcome(message: dict) -> str:
    if "error" in message:
        return "rpc_error"
    return "tool_error" if (message.get("result") or {}).get("isError") else "ok"


def score_calls(
    calls: list[dict], *, scan: dict | None, specs: dict, route: str, kind: str | None
) -> list[dict]:
    """Add ``cell``, ``factor`` (B × L) and ``risk`` to each call, replayed in order."""
    if scan is None:
        return [
            {
                **call,
                "cell": None,
                "asset": None,
                "basis": None,
                "factor": None,
                "risk": None,
                "reasons": "route not scanned",
            }
            for call in calls
        ]

    gate_runtime = _gate_runtime()
    matrix = MatrixScorer(scan["cells"], scan["bands"])
    gate = gate_runtime.GateScorer(specs)
    connection = gate_runtime.Connection(org_id=GATEWAY_ORG, server_id=route, kind=kind or route)
    score_max = float(scan.get("score_max", DEFAULT_SCORE_MAX))
    rows = []
    for call in calls:
        cell = matrix.score(call["tool"], call["args"])
        factor, reasons = gate.score(connection, call["tool"], call["args"])
        known = cell.basis != "no-cells"
        rows.append(
            {
                **call,
                "cell": cell.severity if known else None,
                "asset": cell.driver,
                "basis": cell.basis,
                "factor": round(factor, 3),
                "risk": round(min(score_max, cell.severity * factor), 3) if known else None,
                "reasons": "; ".join(reasons) if known else "tool not in scan",
            }
        )
    return rows


def _gate_runtime() -> ModuleType:
    """The runtime factor lives in ``scripts/dynamic_design`` (stdlib-only scripts)."""
    if str(DYNAMIC_DIR) not in sys.path:
        sys.path.insert(0, str(DYNAMIC_DIR))
    import gate_runtime  # noqa: PLC0415 — path is only valid after the insert above

    return gate_runtime


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
    scan = json.loads(Path(upstream.scan).read_text(encoding="utf-8")) if upstream.scan else None
    specs = _gate_runtime().load_gate_specs() if scan else {}
    rows = score_calls(calls, scan=scan, specs=specs, route=args.route, kind=upstream.kind)

    out = log_path.with_name(f"{args.route}_scored.csv")
    write_csv(rows, out)
    print(f"{len(rows)} tool calls from {log_path} -> {out}")
    ranked = sorted((r for r in rows if r["risk"] is not None), key=lambda r: -r["risk"])
    for row in ranked[:TOP_N]:
        print(
            f"  R={row['risk']:>7.2f}  cell={row['cell']:>5.1f}  x{row['factor']:.2f}  "
            f"{row['tool']}  {json.dumps(row['args'])[:60]}"
        )


if __name__ == "__main__":
    main()
