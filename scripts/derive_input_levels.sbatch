#!/bin/bash
#SBATCH --job-name=mcp-input-levels
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/input-levels-%j.out  # copied into the run folder at the end

# v13, one step (docs/standards/tool-input-levels.md): per input, a rule reaching all
# five levels 1-5, or null. Writes reports/experiments/v13/runN/<server>.json.
# One ollama per GPU, servers round-robin across them. Override the servers with
#   --export=ALL,LEVEL_SERVERS="github slack"
# and pin the run folder with --export=ALL,MCP_INPUT_LEVELS_OUT=<folder>.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
# ports from the job id: two jobs on one node must not share an ollama server
BASE_PORT=$((11000 + (SLURM_JOB_ID % 400) * 4))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=20m
export OLLAMA_NUM_PARALLEL=1
# 16384 is the size proved safe on one 24 GB GPU; do not raise without re-testing.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

if [ -z "${MCP_INPUT_LEVELS_OUT:-}" ]; then
  RUN_DIR=$("$PY" - <<'PYEOF'
from pathlib import Path
v13 = Path("reports/experiments/v13")
used = [int(d.name[3:]) for d in v13.glob("run*") if d.name[3:].isdigit()]
print(v13 / f"run{max(used, default=0) + 1}")
PYEOF
)
  export MCP_INPUT_LEVELS_OUT="$REPO/$RUN_DIR"
fi
mkdir -p "$MCP_INPUT_LEVELS_OUT/logs"
echo "=== run folder: $MCP_INPUT_LEVELS_OUT ==="

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="
SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port "$BIN" serve \
    > "$MCP_INPUT_LEVELS_OUT/logs/ollama-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 180); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

SERVERS=${LEVEL_SERVERS:-"github slack calendar filesystem sqlite"}
echo "=== servers: $SERVERS ==="
RC=0; PIDS=(); idx=0
for srv in $SERVERS; do
  port=$((BASE_PORT + (idx % NGPU)))
  echo "  -> $srv on gpu$((idx % NGPU)) (port $port)"
  idx=$((idx + 1))
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" scripts/derive_input_levels.py --server "$srv" -v \
      > "$MCP_INPUT_LEVELS_OUT/logs/${srv}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
cp "$REPO/reports/input-levels-${SLURM_JOB_ID}.out" "$MCP_INPUT_LEVELS_OUT/logs/" 2>/dev/null
echo "=== DONE rc=$RC ==="; ls -la "$MCP_INPUT_LEVELS_OUT"; exit $RC
