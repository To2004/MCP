"""CLI: score one captured session against its scan, with the dynamic signal fused in.

Usage::

    uv run python -m mcp_security.dynamic --session logs/proxy/sessions/<name>/calls.csv \\
        --server <scan-stem> [--corpus logs/proxy/sessions] [-v]

``--corpus`` points at the directory of sessions used to build the per-persona
behavioral baseline (defaults to the session's own parent's parent, i.e. every
session under ``logs/proxy/sessions/``). The LLM judge stage is off by default
(needs a reachable Ollama instance); pass ``--judge`` to enable it.
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter, defaultdict
from pathlib import Path

from mcp_security.call_scoring.loader import load_calls
from mcp_security.call_scoring.score import score_call
from mcp_security.call_scoring.tables import SCAN_DIR, load_scan

from .baseline import build_baselines
from .combine import score_session
from .judge import judge_call

DEFAULT_CORPUS = Path("logs/proxy/sessions")


def _group_by_run(calls) -> dict[str, list]:
    sessions = defaultdict(list)
    for call in calls:
        sessions[call.run_id or call.source].append(call)
    return sessions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score one session with static + dynamic fusion.")
    parser.add_argument("--session", type=Path, required=True, help="Path to a session's calls.csv.")
    parser.add_argument("--server", required=True, help="Scan artifact stem under reports/scan/.")
    parser.add_argument(
        "--corpus", type=Path, default=DEFAULT_CORPUS,
        help=f"Root of session directories for baseline-building (default: {DEFAULT_CORPUS}).",
    )
    parser.add_argument("--scan-dir", type=Path, default=SCAN_DIR, help="Directory of scan artifacts.")
    parser.add_argument("--judge", action="store_true", help="Enable the LLM judge escalation stage.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable info logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    table = load_scan(args.scan_dir / f"{args.server}.json")

    baseline_calls = []
    for csv_path in sorted(args.corpus.glob("*/calls.csv")):
        baseline_calls.extend(score_call(c, table) for c in load_calls(csv_path) if c.tool)
    baselines = build_baselines(baseline_calls)

    target_calls = [score_call(c, table) for c in load_calls(args.session)]
    judge_fn = judge_call if args.judge else None

    final_band_counts: Counter[str] = Counter()
    for run_id, session_calls in _group_by_run(target_calls).items():
        verdicts = score_session(session_calls, baselines, judge_fn=judge_fn)
        for verdict in verdicts:
            final_band_counts[verdict.final_band] += 1
            if args.verbose:
                print(
                    f"[{run_id}] {verdict.call.tool} static={verdict.static_band} "
                    f"baseline={verdict.baseline_band} sequence={verdict.sequence_band} "
                    f"-> final={verdict.final_band}"
                )

    print(f"Scored {sum(final_band_counts.values())} calls from {args.session}")
    for band, count in sorted(final_band_counts.items()):
        print(f"  {band}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
