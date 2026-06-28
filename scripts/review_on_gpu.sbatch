#!/bin/bash
#SBATCH --job-name=mcp-review
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --output=/home/ovadyat/MCP/reports/review-%j.out

# Run the full reviewer suite: deterministic correctness verification (no model),
# the methodology audit, the results-quality verdict, and the results advisor.
# verify runs first as a hard gate; the LLM modes need one local Ollama instance.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11550
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="

# Deterministic gate first — needs no model, surfaces any artifact inconsistency.
echo "=== verify (deterministic) ==="
"$PY" -m mcp_security.review verify; VERIFY_RC=$?

CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve \
  > "$REPO/reports/ollama-serve-review-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
for t in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break; sleep 1
done

echo "=== judge + results verdict + advise (LLM) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" -m mcp_security.review all; LLM_RC=$?

kill "$SERVE_PID" 2>/dev/null
RC=$(( VERIFY_RC || LLM_RC ))
echo "=== DONE verify_rc=$VERIFY_RC llm_rc=$LLM_RC rc=$RC ==="; exit $RC
