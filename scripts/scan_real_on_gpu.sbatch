#!/bin/bash
#SBATCH --job-name=mcp-scan-real
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-real-%j.out

# LLM-scan the REAL captured MCP tool catalogs (GitHub 26 / Calendar 13 / Slack 16)
# into risk matrices, using Qwen2.5:32b via a local Ollama on the GPU node.
# Mirrors scripts/scan_and_rank_on_gpu.sbatch. GPU rule: rtx_4090 first.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11517

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== node: $(hostname) | CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv 2>/dev/null

echo "=== starting ollama serve on $OLLAMA_HOST ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do
  curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; break; }
  sleep 1
done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
PY="$REPO/.venv/bin/python"

echo "=== scanning real catalogs (LLM-only, strict) ==="
"$PY" scripts/scan_real_catalogs.py --version-tag "scan-real-$(date +%Y-%m-%d 2>/dev/null || echo 2026-07-06)"
RC=$?

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
exit $RC
