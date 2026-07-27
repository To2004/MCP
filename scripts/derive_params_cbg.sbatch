#!/bin/bash
#SBATCH --job-name=mcp-params-cbg
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/derive-params-%j.out

# Derive per-tool input-parameter rubrics (magnitude cutoffs) for every server,
# LLM-only, sharded across the allocated GPUs. Reuses the existing scans; the
# ranker is re-run afterwards so reports/ranked_calls.* reflect parameter risk.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11500
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="
SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port "$BIN" serve \
    > "$REPO/reports/ollama-serve-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 120); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

JOBS=(
  "calendar|calendar:cbg"
  "github|github:cbg"
  "slack|slack:cbg"
)
RC=0; PIDS=(); idx=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind name <<< "$job"
  port=$((BASE_PORT + (idx % NGPU))); stem=$(echo "$name" | tr ':' '_')
  echo "  -> params for $name on gpu$((idx % NGPU))"
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" -m mcp_security.param_scoring --kind "$kind" --server "$name" -v \
      > "$REPO/reports/param-${stem}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!); idx=$((idx + 1))
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

echo "=== re-rank with parameter escalation ==="
"$PY" -m mcp_security.call_scoring -v; RC=$(( RC || $? ))

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
echo "=== DONE rc=$RC ==="; exit $RC
