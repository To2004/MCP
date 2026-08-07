#!/usr/bin/env python3
"""Score a live sweep with the stateless MatrixScorer, and grade the over-scoring.

Each swept call carries the asset it actually touched (labelled from the server's
own listing, not by hand). The scorer never reads that column: it sees the tool
and the arguments, looks the tool up in the scanned ``(tool, asset)`` matrix, and
takes the worst cell it cannot rule out. This measures what a gate would really
act on, against the true cell, across the full severity range the sweep exercised
— including the high-severity write cells the read-only corpus could not reach.

Reported per server:

``sole``        share of calls a single-candidate tool answered outright
``named``       share where an argument value spelled out an asset
``unresolved``  share where nothing narrowed — worst cell taken
``mean over``   assigned severity minus true severity (0-100 matrix scale)
``exact``       assigned == true
``under``       assigned < true — a safety failure, expected 0

Usage::

    uv run python scripts/evaluate_matrix_scoring.py --sweep reports/experiments/v8/sweep/scale_calls.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.binding.scoring import MatrixScorer  # noqa: E402

CORPUS = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"
V8_DIR = REPO_ROOT / "reports" / "experiments" / "v8"


def load_matrix(server: str) -> tuple[dict, dict]:
    artifact = json.loads((CORPUS / f"{server}.json").read_text(encoding="utf-8"))
    return artifact["cells"], artifact["bands"]


def evaluate(sweep_rows: list[dict], server: str) -> dict:
    cells, bands = load_matrix(server)
    scorer = MatrixScorer(cells, bands)
    calls = [r for r in sweep_rows if r["org"] == server and r["status"] == "OK"]

    basis: Counter[str] = Counter()
    over: list[float] = []
    covered_cells: set[tuple[str, str]] = set()
    for row in calls:
        args = json.loads(row["args"] or "{}")
        result = scorer.score(row["tool"], args)
        basis[result.basis] += 1
        covered_cells.add((row["tool"], row["asset"]))
        true_band = bands.get(row["asset"], {}).get(row["tool"])
        true_cell = cells.get(row["asset"], {}).get(row["tool"])
        if true_cell is None or true_band == MatrixScorer.UNSCORED_BAND:
            continue
        over.append(result.severity - true_cell)

    n = max(len(calls), 1)
    graded = over or [0.0]
    return {
        "server": server,
        "calls": len(calls),
        "cells_touched": len(covered_cells),
        "gradable": len(over),
        "sole": basis["sole-candidate"] / n,
        "named": basis["named"] / n,
        "unresolved": basis["unresolved"] / n,
        "mean_over": statistics.mean(graded),
        "exact": sum(1 for d in over if d == 0) / len(graded),
        "under": sum(1 for d in over if d < 0) / len(graded),
        "worst_over": max(graded),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", type=Path,
                        default=V8_DIR / "sweep" / "scale_calls.csv")
    parser.add_argument("--json", type=Path, default=V8_DIR / "matrix_scoring_results.json")
    options = parser.parse_args()

    with options.sweep.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    servers = sorted({r["org"] for r in rows})
    results = [evaluate(rows, s) for s in servers]

    header = (f"{'server':16s} {'calls':>6s} {'cells':>6s} {'sole':>6s} {'named':>6s} "
              f"{'unres':>6s} {'over':>7s} {'exact':>6s} {'under':>6s} {'wOver':>6s}")
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['server']:16s} {r['calls']:6d} {r['cells_touched']:6d} {r['sole']:6.1%} "
              f"{r['named']:6.1%} {r['unresolved']:6.1%} {r['mean_over']:7.1f} "
              f"{r['exact']:6.1%} {r['under']:6.1%} {r['worst_over']:6.0f}")
    options.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {options.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
