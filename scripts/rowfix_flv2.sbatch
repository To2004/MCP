#!/bin/bash
#SBATCH --job-name=mcp-rowfix
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/home/ovadyat/MCP/reports/rowfix-%x-%j.out

# Experiment `rowfix`: per-asset row-consistency repair over the five_level_v2_fs
# baseline scans (calendar/slack/fs). One LLM audit call per asset row; results
# land in reports/experiments/five_level_v2_rowfix/.
#   sbatch scripts/rowfix_flv2.sbatch

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
echo "=== node: $(hostname) | experiment=rowfix | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-rowfix-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/row_consistency_repair.py
RC=$?

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
