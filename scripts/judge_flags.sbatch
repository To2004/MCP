#!/bin/bash
#SBATCH --job-name=judge-flags
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/judge-flags-%j.out

# Anchor-free LLM judge over the 122 cells where the keyflags and noflags arms
# disagree. The judge re-derives blast itself from the organization's full
# register row + the tool declaration; it never sees either arm's answer.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | port=$PORT ==="
OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-judge-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/judge_flag_arms.py
RC=$?
echo "=== done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null; wait "$SERVE_PID" 2>/dev/null
exit $RC
