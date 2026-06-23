#!/bin/bash
#SBATCH --job-name=mcp-asset-rank
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --output=/home/ovadyat/MCP/reports/rank-%j.out

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11500

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
# Fit 32B-Q4 on one 24GB GPU: cap ctx + shrink KV so all layers offload.
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== node: $(hostname) | CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv 2>/dev/null

echo "=== starting ollama serve on $OLLAMA_HOST ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!

for i in $(seq 1 90); do
  curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; break; }
  sleep 1
done

# The python client needs a scheme-qualified host.
export OLLAMA_HOST=http://127.0.0.1:$PORT

echo "=== ranking assets with the rubric (Qwen2.5:32b) ==="
cd "$REPO"
"$REPO/.venv/bin/python" "$REPO/scripts/rank_assets_with_rubric.py"
RC=$?

echo "=== gpu mem in use ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv 2>/dev/null

kill "$SERVE_PID" 2>/dev/null
echo "=== DONE rc=$RC ==="
exit $RC
