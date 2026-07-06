#!/bin/bash
#SBATCH --job-name=mcp-enrich-llm
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/enrich-llm-%j.out

# LLM-rank every scanned tool's inputs (tool_input_ranking, source=llm) using
# Qwen2.5:32b via a local Ollama. Mirrors scripts/scan_real_on_gpu.sbatch.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11519
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== node: $(hostname) ==="; nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }; sleep 1; done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
echo "=== LLM-ranking tool inputs across all scans ==="
"$REPO/.venv/bin/python" scripts/enrich_scans_atomic.py --llm
RC=$?
kill "$SERVE_PID" 2>/dev/null
exit $RC
