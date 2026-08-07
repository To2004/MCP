#!/bin/bash
#SBATCH --job-name=mcp-v7-judge
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/judge-v7-%j.out

# Independent sensitivity judge for the v7 framework arms.
#
# Answers the question the raw disagreement rate cannot: when a v7 arm scores an
# asset differently from the nacombo baseline, is that because the framework
# document genuinely says something different (justified), or because the scanner
# misread its own policy (scanner error)?
#
# The judge re-derives each asset's tier from ONE policy document at a time and is
# never shown a scanner's number, so it cannot anchor. The verdict is then
# arithmetic on four values. See the script docstring.
#
#   sbatch scripts/judge_v7.sbatch                 # all arms, all servers
#   sbatch scripts/judge_v7.sbatch 3               # 3 assets per (arm, server)
#
# Results land in reports/experiments/v7/JUDGE_SENSITIVITY.md.

set -u
LIMIT="${1:-}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11900 + RANDOM % 300))
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# A whole policy section rides in every judge prompt, and the framework-native
# sections are longer than the baseline's.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | port=$PORT | limit=${LIMIT:-none} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-v7judge-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=()
[ -n "$LIMIT" ] && ARGS+=(--limit "$LIMIT")

echo "=== judging (blind re-derivation from policy text) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/judge_v7_sensitivity.py "${ARGS[@]}"
RC=$?

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
