#!/bin/bash
#SBATCH --job-name=mcp-v5
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-v5-%x-%j.out

# v5 — the final static arm. Inputs per server are exactly two documents:
#   1. the captured tool catalog (reports/tool_lists/<stem>.json), and
#   2. the org POLICY section (docs/mcp-tools/server-policies.md) — a
#      classification table, an asset register and recognition rules, with NO
#      sensitivity numbers anywhere.
# Sensitivity is DERIVED (LLM classify -> map against the policy); tool impact is
# the deterministic ladder with the v4 impact prompt only where the ladder
# abstains; blast is the v4 rubric with the full context and the sibling lists.
#
#   sbatch scripts/scan_v5.sbatch                                  # all servers, v5
#   sbatch scripts/scan_v5.sbatch calendar_real                    # one server
#   sbatch --export=ALL,MODE=five_level_v2_v5r scripts/scan_v5.sbatch github_helios
#   sbatch scripts/scan_v5.sbatch github_real overwrite            # re-scan one
#
# Results land in reports/experiments/v5/five_level_v2_policy_v5/; the driver
# skips targets that already have an artifact unless `overwrite` is passed.

set -u
ONLY="${1:-}"
OVERWRITE="${2:-}"
MODE="${MODE:-five_level_v2_v5}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
case "$MODE" in
  five_level_v2_v5r) OUT="$REPO/reports/experiments/v5/five_level_v2_policy_v5r" ;;
  *)                 OUT="$REPO/reports/experiments/v5/five_level_v2_policy_v5" ;;
esac

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# The policy rides in every prompt (up to ~900 words on github) alongside the
# rubric, the tool/asset JSON and the sibling lists.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p "$OUT"
echo "=== node: $(hostname) | mode=$MODE | only=${ONLY:-ALL} | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-v5-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=(--impact-mode "$MODE")
[ -n "$ONLY" ] && ARGS+=(--only "$ONLY")
[ "$OVERWRITE" = "overwrite" ] && ARGS+=(--overwrite)

echo "=== scanning (policy-derived sensitivity, static tool impact + LLM fallback) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_policy_v5.py "${ARGS[@]}"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=$MODE) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));s=d.get('tool_impact_source',{});print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| sens',d['sensitivity_source'],'| impact static',sum(1 for v in s.values() if v=='static_ladder'),'/',len(s),'| floored',d['blast_floor'].get('raised_cells'),'| capped',d['blast_roof'].get('capped_cells'),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (only=${ONLY:-ALL} rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
