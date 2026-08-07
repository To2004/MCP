#!/bin/bash
#SBATCH --job-name=mcp-flv2ctx
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-flv2ctx-%x-%j.out

# Experiment `five_level_v2_ctx`: same 1-5 action ladder + coverage blast + N/A as
# five_level_v2_na, but a per-tool UNDERSTANDING stage (role, single-call reach,
# consequence carriers, worst realistic misuse) runs first and its profile is
# injected into every blast decision for that tool. Scans calendar + slack (real
# catalogs) and the corp filesystem; results land in
# reports/experiments/five_level_v2_ctx/.
#   sbatch scripts/scan_flv2ctx.sbatch

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/five_level_v2_ctx"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | mode=five_level_v2_ctx | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-flv2ctx-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

RC=0
echo "=== scanning calendar,slack (LLM-only, strict) under impact_mode=five_level_v2_ctx ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_real_catalogs.py \
  --impact-mode five_level_v2_ctx --gen-assets --kinds calendar,slack \
  --version-tag scan-flv2ctx --out-dir "$OUT" || RC=1

echo "=== scanning fs:corp (by-file assets) under impact_mode=five_level_v2_ctx ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_fs_five_level_v2.py \
  --impact-mode five_level_v2_ctx --out-dir "$OUT" || RC=1

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=five_level_v2_ctx) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| assets',len(d['asset_sensitivity']),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
