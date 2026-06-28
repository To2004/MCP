#!/bin/bash
#SBATCH --job-name=mcp-exteval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/home/ovadyat/MCP/reports/exteval-%j.out

# External-benchmark comparison (GPU half): score every labeled benchmark call
# (MCPSecBench / MCP-SafetyBench / MSB) with the Qwen LLM-as-judge baseline, then
# regenerate the detection report + positioning matrix. The deterministic baselines
# (CVSS, AIVSS, keyword, floors) need no GPU and are computed inside evaluate_external.
#
# GPU rule: rtx_4090 first. The judge is one short classification per call, so one
# 4090 is plenty for the ~150-call set.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11500

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
PY="$REPO/.venv/bin/python"
RC=0

echo "=== node: $(hostname) | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=index,name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-exteval-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
for t in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${t}s"; break; }
  sleep 1
done

echo "=== LLM-judge over the external benchmark calls ==="
"$PY" scripts/llm_judge_bench.py;     RC=$(( RC || $? ))

echo "=== detection report (ours-to-come + LLM-judge + CVSS/AIVSS/keyword/floors) ==="
"$PY" scripts/evaluate_external.py;   RC=$(( RC || $? ))

echo "=== positioning matrix ==="
"$PY" scripts/framework_matrix.py;    RC=$(( RC || $? ))

kill "$SERVE_PID" 2>/dev/null
echo "=== DONE rc=$RC ==="
exit $RC
