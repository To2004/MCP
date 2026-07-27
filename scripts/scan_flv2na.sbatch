#!/bin/bash
#SBATCH --job-name=mcp-flv2na
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-flv2na-%x-%j.out

# LLM scan of one or more MCP servers under the five_level_v2_na rubric (generalized
# 1-5 action ladder + coverage blast with N/A cells + gen-assets homing). Pass the
# comma-separated kinds as arg 1; results land in reports/experiments/five_level_v2_fs/.
#   sbatch --job-name=mcp-flv2na-github scripts/scan_flv2na.sbatch github
#   sbatch --job-name=mcp-flv2na-sql    scripts/scan_flv2na.sbatch sqlite

set -u
KINDS="${1:?usage: sbatch scan_flv2na.sbatch <kinds e.g. github,slack,calendar,sqlite>}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/five_level_v2_fs"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | mode=five_level_v2_na | kinds=$KINDS | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-flv2na-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning kinds=$KINDS (LLM-only, strict) under impact_mode=five_level_v2_na ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_real_catalogs.py \
  --impact-mode five_level_v2_na --gen-assets --kinds "$KINDS" \
  --version-tag scan-flv2na --out-dir "$OUT"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=five_level_v2_na) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| assets',len(d['asset_sensitivity']),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (kinds=$KINDS rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
