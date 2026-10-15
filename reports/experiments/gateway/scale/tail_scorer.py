"""Semi-runtime scoring in its own process: follow the gateway's log, score each call.

The gateway only forwards and logs (``scoring: off``); this process reads the log as it
grows, scores every ``tools/call`` request with the same ``RouteScorer`` (per-caller
history) and appends a decision line, plus how long after the request it was decided.
Because the log is the record, a restart can resume from a byte offset or replay it.

    python tail_scorer.py --log logs/github.jsonl --out decisions.jsonl --seconds 60
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.proxy import load_config

ROUTES = Path("src/mcp_security/gateway/routes.example.json")
POLL_S = 0.005


def follow(path: Path, deadline: float):
    """Yield complete lines appended to ``path`` until ``deadline``."""
    while not path.exists() and time.time() < deadline:
        time.sleep(POLL_S)
    with path.open(encoding="utf-8") as handle:
        partial = ""
        while time.time() < deadline:
            chunk = handle.readline()
            if not chunk:
                time.sleep(POLL_S)
                continue
            partial += chunk
            if partial.endswith("\n"):
                yield partial
                partial = ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    up = load_config(ROUTES).upstreams["github"]
    scorer = RouteScorer("github", load_artifacts("github", up.scan, up.breadth, up.rules, up.kind),
                         history="caller")
    lags, deadline = [], time.time() + args.seconds
    with args.out.open("w", encoding="utf-8") as out:
        for line in follow(args.log, deadline):
            record = json.loads(line)
            message = record.get("message") or {}
            if record.get("gateway.direction") != "agent->server" or message.get("method") != "tools/call":
                continue
            params = message.get("params") or {}
            decision = scorer.score(params.get("name"), params.get("arguments") or {},
                                    record["ts"], caller=record.get("gateway.agent"))
            lag = time.time() - record["ts"]
            lags.append(lag)
            out.write(json.dumps({"ts": record["ts"], "lag_s": round(lag, 4),
                                  "jsonrpc.request.id": message.get("id"),
                                  "gateway.decision": decision}) + "\n")
    lags.sort()
    q = lambda p: round(lags[min(len(lags) - 1, int(p * len(lags)))] * 1000, 2) if lags else None  # noqa: E731
    print(json.dumps({"decisions": len(lags), "lag_p50_ms": q(0.5), "lag_p95_ms": q(0.95),
                      "lag_p99_ms": q(0.99), "lag_max_ms": q(1.0)}))


if __name__ == "__main__":
    main()
