#!/bin/bash
#SBATCH --job-name=mcp-input-features
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:2
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/input-features-%j.out  # copied into the run folder at the end

# v11: type every server's tool inputs with the local model, using
# docs/standards/tool-input-features.md verbatim as the prompt (with
# tool-context and structural-fact placeholders filled in by the runner).
# One ollama per GPU, servers round-robin across them -- same pattern as
# derive_input_types.sbatch, sized for all 5 catalogs in mcp_catalogs.py.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11700
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=20m
export OLLAMA_NUM_PARALLEL=1
# Proven working size (see git history / v11 README pilot log): 32768 caused
# severe VRAM/KV-cache pressure and CPU-offload slowdowns on a single
# rtx_4090. Two tools (calendar create-events/update-event) still overflow
# this and are a known, documented limitation -- do not "fix" by raising
# this without re-testing for the same regression.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

if [ -z "${MCP_INPUT_FEATURES_OUT:-}" ]; then
  RUN_DIR=$("$PY" - <<'PYEOF'
from pathlib import Path
v11 = Path("reports/experiments/v11")
used = [int(d.name[3:]) for d in v11.glob("run*") if d.name[3:].isdigit()]
print(v11 / f"run{max(used, default=0) + 1}")
PYEOF
)
  export MCP_INPUT_FEATURES_OUT="$REPO/$RUN_DIR"
fi
mkdir -p "$MCP_INPUT_FEATURES_OUT/logs"
echo "=== run folder: $MCP_INPUT_FEATURES_OUT ==="

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="
SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port "$BIN" serve \
    > "$REPO/reports/ollama-features-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 180); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

# Which servers to type; override with --export=ALL,FEATURE_SERVERS="calendar"
SERVERS=${FEATURE_SERVERS:-$("$PY" -c "from sys import path; path.insert(0,'scripts'); from mcp_catalogs import SERVERS; print(*SERVERS)")}
echo "=== servers: $SERVERS ==="
RC=0; PIDS=(); idx=0
for srv in $SERVERS; do
  port=$((BASE_PORT + (idx % NGPU)))
  echo "  -> $srv on gpu$((idx % NGPU)) (port $port)"
  idx=$((idx + 1))
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" scripts/derive_input_features.py --server "$srv" -v \
      > "$MCP_INPUT_FEATURES_OUT/logs/${srv}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
cp "$REPO/reports/input-features-${SLURM_JOB_ID}.out" "$MCP_INPUT_FEATURES_OUT/logs/" 2>/dev/null
echo "=== DONE rc=$RC ==="; ls -la "$MCP_INPUT_FEATURES_OUT"; exit $RC
