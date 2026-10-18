#!/bin/bash
#SBATCH --job-name=mcp-input-types
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/input-types-%j.out

# Type the tool inputs of github / slack / calendar with the local model, using
# docs/standards/input-typing.md verbatim as the prompt. One ollama per GPU;
# with one GPU the three servers queue through a single ollama instance.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11600
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=20m
export OLLAMA_NUM_PARALLEL=1
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
    > "$REPO/reports/ollama-types-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 180); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

# server|shard|gpu
JOBS=("github|0/1|0" "slack|0/1|1" "calendar|0/1|0")
RC=0; PIDS=()
for job in "${JOBS[@]}"; do
  IFS='|' read -r srv shard gpu <<< "$job"
  port=$((BASE_PORT + (gpu % NGPU)))
  echo "  -> $srv shard $shard on gpu$gpu (port $port)"
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" scripts/derive_input_types.py --server "$srv" --shard "$shard" -v \
      > "$REPO/reports/input-types-${srv}-${shard//\//_}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
echo "=== DONE rc=$RC ==="; ls -la "$REPO/reports/input_types/"; exit $RC
