#!/bin/bash
#SBATCH --job-name=mcp-input-types
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/input-types-%j.out  # copied into the run folder at the end

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
# Real catalogs carry large schemas: calendar create-event is ~4.9k tokens of
# prompt+tool, and a 31-argument answer adds ~2k more. 8192 would truncate.
export OLLAMA_CONTEXT_LENGTH=12288
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

# One run folder for all servers, decided once so they cannot disagree. Honour a
# folder pinned by the caller (--export=ALL,MCP_INPUT_TYPES_OUT=...) so a retry
# can land back in the run it belongs to; otherwise take the next free number.
if [ -z "${MCP_INPUT_TYPES_OUT:-}" ]; then
  RUN_DIR=$("$PY" - <<'PYEOF'
from pathlib import Path
v10 = Path("reports/experiments/v10")
used = [int(d.name[3:]) for d in v10.glob("run*") if d.name[3:].isdigit()]
print(v10 / f"run{max(used, default=0) + 1}")
PYEOF
)
  export MCP_INPUT_TYPES_OUT="$REPO/$RUN_DIR"
fi
mkdir -p "$MCP_INPUT_TYPES_OUT/logs"
echo "=== run folder: $MCP_INPUT_TYPES_OUT ==="

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

# Which servers to type; override with --export=ALL,TYPE_SERVERS="calendar"
SERVERS=${TYPE_SERVERS:-$("$PY" -c "from sys import path; path.insert(0,'scripts'); from mcp_catalogs import SERVERS; print(*SERVERS)")}
echo "=== servers: $SERVERS ==="
RC=0; PIDS=(); idx=0
for srv in $SERVERS; do
  port=$((BASE_PORT + (idx % NGPU)))
  echo "  -> $srv on gpu$((idx % NGPU)) (port $port)"
  idx=$((idx + 1))
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" scripts/derive_input_types.py --server "$srv" -v \
      > "$MCP_INPUT_TYPES_OUT/logs/${srv}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
"$PY" scripts/summarize_input_types.py "$MCP_INPUT_TYPES_OUT" || RC=1
cp "$REPO/reports/input-types-${SLURM_JOB_ID}.out" "$MCP_INPUT_TYPES_OUT/logs/" 2>/dev/null
echo "=== DONE rc=$RC ==="; ls -la "$MCP_INPUT_TYPES_OUT"; exit $RC
