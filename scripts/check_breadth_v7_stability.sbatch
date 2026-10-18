#!/bin/bash
#SBATCH --job-name=mcp-breadth-v7-stab
#SBATCH --partition=main
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/breadth-v7-%x-%j.out

# One of the three v7 ablations (context|fields|window), each exp2 + one added
# tie-breaker rule diagnosed from exp2's own regressions. Pass the variant as the first
# sbatch argument: sbatch --job-name=mcp-breadth-v7-context scripts/check_breadth_v7_stability.sbatch context
set -u
VARIANT="${1:?usage: sbatch check_breadth_v7_stability.sbatch <context|fields|window>}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11000 + SLURM_JOB_ID % 2000))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO" || exit 1
mkdir -p runs

echo "=== $(hostname) variant=$VARIANT ==="
nvidia-smi -L

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/runs/ollama-breadth-v7-${VARIANT}-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
for _ in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 || { echo "ollama did not start"; kill $SERVE_PID; exit 1; }
echo "ollama up on :$PORT"

OLLAMA_HOST="http://127.0.0.1:$PORT" "$REPO/.venv/bin/python" \
    "$REPO/scripts/check_breadth_v7_stability.py" "$VARIANT" --model qwen2.5:32b
RC=$?

kill $SERVE_PID 2>/dev/null
wait $SERVE_PID 2>/dev/null
echo "=== done rc=$RC ==="
exit $RC
