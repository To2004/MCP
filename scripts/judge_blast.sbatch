#!/bin/bash
#SBATCH --job-name=mcp-judge-blast
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:30:00
#SBATCH --output=/home/ovadyat/MCP/reports/judge-blast-%x-%j.out

# LLM-as-judge ranking of the blast experiments: a blinded judge re-derives blast
# for every scored baseline cell (~380 calls), then each experiment (baseline/ctx/
# floor-plain/floor-gated/rowfix) is graded by agreement. Results land in
# reports/experiments/five_level_v2_judge/ + blast_experiments_judged.md.
#   sbatch scripts/judge_blast.sbatch

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
echo "=== node: $(hostname) | experiment=judge-blast | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-judge-blast-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/judge_blast_experiments.py
RC=$?

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
