#!/bin/bash
#SBATCH --job-name=mcp-polsens
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-polsens-%x-%j.out

# LLM scan that DERIVES asset sensitivity from the org policy: five_level_v2_na
# scoring (sensitivity stage runs) with docs/mcp-tools/server-policies.md in
# front of every prompt. Compare with scripts/compare_policy_sensitivity.py.
#
# Pass the comma-separated output stems as arg 1 (default: all 11), and the literal
# word `overwrite` as arg 2 to re-scan targets that already have an artifact (needed
# after a prompt change; without it completed targets are skipped).
#   sbatch scripts/scan_policy_sens.sbatch calendar_real
#   sbatch scripts/scan_policy_sens.sbatch calendar_real overwrite
#
# Results land in reports/experiments/staticscanner/; the driver skips
# already-scanned targets, so nothing is overwritten.

set -u
ONLY="${1:-}"
OVERWRITE="${2:-}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/staticscanner"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p "$OUT"
echo "=== node: $(hostname) | mode=staticscanner-policy-sens | only=${ONLY:-ALL} | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-polsens-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=(--out-dir "$OUT")
[ -n "$ONLY" ] && ARGS+=(--only "$ONLY")
[ "$OVERWRITE" = "overwrite" ] && ARGS+=(--overwrite)

echo "=== scanning (LLM-only, strict): org POLICY ON, sensitivity DERIVED from it ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_policy_sens.py "${ARGS[@]}"
RC=$?

if [ "$RC" = 0 ] && [ -n "$ONLY" ]; then
  echo "=== comparison vs no-context baseline and org ground truth ==="
  for stem in ${ONLY//,/ }; do
    "$PY" scripts/compare_policy_sensitivity.py --stem "$stem" || true
  done
fi

echo "=== done (only=${ONLY:-ALL} rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
