#!/bin/bash
# Regenerate the full evaluation report set from already-published artifacts.
#
# This is the NO-GPU half of the pipeline: it grades the committed scans
# (reports/scan/) and scored calls (reports/ranked_calls.csv) against the
# reference tables and the human-oracle panel, then runs the scorer head-to-head
# and the dynamic detection evaluation. No model is contacted, so it is fast and
# deterministic and can be run anytime to refresh the reports/evaluation/ tables.
#
# To regenerate the underlying scans/rankings with Qwen first (needs a GPU), run
# scripts/scan_and_rank_multigpu.sbatch on the cluster; it ends by calling the
# same four graders below.
#
# Usage:  bash scripts/run_eval.sh
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
PY=(uv run python)
RC=0

echo "=== scanner vs design-time reference tables ==="
"${PY[@]}" scripts/evaluate_scanner.py;      RC=$(( RC || $? ))
echo "=== scanner vs independent oracle panel (multi-rater + inter-rater) ==="
"${PY[@]}" scripts/evaluate_vs_human.py;     RC=$(( RC || $? ))
echo "=== scorer head-to-head vs human oracle (calibration + over-block) ==="
"${PY[@]}" scripts/compare_scorers.py;       RC=$(( RC || $? ))
echo "=== dynamic evaluation: request-time detection on captured calls ==="
"${PY[@]}" scripts/evaluate_calls.py;        RC=$(( RC || $? ))

echo "=== DONE rc=$RC; reports in reports/evaluation/ ==="
exit $RC
