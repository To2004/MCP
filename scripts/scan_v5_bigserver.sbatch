#!/bin/bash
#SBATCH --job-name=v5-big
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=48:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-v5-big-%x-%j.out

# Identical to scripts/scan_v5.sbatch except FLASH ATTENTION IS OFF.
#
# maverick (119 tools) crashed the model server on the first call:
#   ggml_abort in launch_fattn / ggml_cuda_flash_attn_ext_mma_f16
#   -> "llama-server terminated, signal: aborted (core dumped)"
# The flash-attention kernel aborts on this prompt length with a quantised KV
# cache. Turning FA off avoids that code path. The MODEL, the PROMPTS and the
# decoding parameters are unchanged, so a scan produced here is comparable with
# every other arm — only the attention implementation differs.
#
#   sbatch --export=ALL,MODE=five_level_v2_v5r_nacombo scripts/scan_v5_bigserver.sbatch maverick overwrite

set -u
ONLY="${1:-}"
OVERWRITE="${2:-}"
MODE="${MODE:-five_level_v2_v5r_nacombo}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11900 + RANDOM % 300))
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=0      # <- the fix
export OLLAMA_KV_CACHE_TYPE=f16      # q8_0 KV cache needs FA; use f16 without it

cd "$REPO"
echo "=== node: $(hostname) | mode=$MODE | only=${ONLY:-ALL} | FA=off | port=$PORT ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-v5big-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=(--impact-mode "$MODE")
[ -n "$ONLY" ] && ARGS+=(--only "$ONLY")
[ "$OVERWRITE" = "overwrite" ] && ARGS+=(--overwrite)

OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_policy_v5.py "${ARGS[@]}"
RC=$?
echo "=== done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null; wait "$SERVE_PID" 2>/dev/null
exit $RC
