#!/bin/bash
#SBATCH --job-name=mcp-input-labels
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:2
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=05:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/input-labels-%j.out  # copied into the run folder at the end

# v12, two stages. Stage 1 (docs/standards/tool-input-importance.md, three votes plus
# docs/standards/tool-input-importance-check.md) decides which inputs can change a call's
# risk; stage 2 (docs/standards/tool-input-rules.md) writes one run-time rule, levels 1-5,
# per important input. The script's default is stage 1 only, so the shortlist can be
# reviewed first. Choose with
#   --export=ALL,LABEL_FLAGS="--stage both"
# and run stage 2 on an existing importance file by also pinning its folder:
#   --export=ALL,LABEL_FLAGS="--stage rules",MCP_INPUT_LABELS_OUT=<run folder>
# One ollama per GPU, servers round-robin across them (same shape as
# derive_input_features.sbatch). Override the servers with
#   --export=ALL,LABEL_SERVERS="github"
# and send an empty policy (the ablation) with --export=ALL,LABEL_FLAGS="--no-policy".
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11700
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=20m
export OLLAMA_NUM_PARALLEL=1
# 16384 is the size v11 proved safe on one 24 GB GPU; 32768 pushed the KV cache
# past VRAM and forced silent CPU offload. Do not raise without re-testing.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

if [ -z "${MCP_INPUT_LABELS_OUT:-}" ]; then
  RUN_DIR=$("$PY" - <<'PYEOF'
from pathlib import Path
v12 = Path("reports/experiments/v12")
used = [int(d.name[3:]) for d in v12.glob("run*") if d.name[3:].isdigit()]
print(v12 / f"run{max(used, default=0) + 1}")
PYEOF
)
  export MCP_INPUT_LABELS_OUT="$REPO/$RUN_DIR"
fi
mkdir -p "$MCP_INPUT_LABELS_OUT/logs"
echo "=== run folder: $MCP_INPUT_LABELS_OUT ==="

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="
SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port "$BIN" serve \
    > "$REPO/reports/ollama-labels-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 180); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

SERVERS=${LABEL_SERVERS:-"github slack calendar"}
echo "=== servers: $SERVERS  flags: ${LABEL_FLAGS:-} ==="
RC=0; PIDS=(); idx=0
for srv in $SERVERS; do
  port=$((BASE_PORT + (idx % NGPU)))
  echo "  -> $srv on gpu$((idx % NGPU)) (port $port)"
  idx=$((idx + 1))
  # shellcheck disable=SC2086  # LABEL_FLAGS is intentionally word-split
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" scripts/derive_input_labels.py --server "$srv" -v ${LABEL_FLAGS:-} \
      > "$MCP_INPUT_LABELS_OUT/logs/${srv}-${SLURM_JOB_ID}.log" 2>&1 &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid" || RC=1; done

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
cp "$REPO/reports/input-labels-${SLURM_JOB_ID}.out" "$MCP_INPUT_LABELS_OUT/logs/" 2>/dev/null
echo "=== DONE rc=$RC ==="; ls -la "$MCP_INPUT_LABELS_OUT"; exit $RC
