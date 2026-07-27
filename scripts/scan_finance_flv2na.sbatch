#!/bin/bash
#SBATCH --job-name=mcp-fin-flv2na
#SBATCH --partition=rtx4090
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-fin-flv2na-%x-%j.out

# LLM scan of ONE captured finance MCP under the five_level_v2_na rubric (parity
# with the github/fs/calendar five_level_v2_fs run). Pass the finance kind as arg 1;
# results land in reports/experiments/five_level_v2_finance/.
#   sbatch scripts/scan_finance_flv2na.sbatch finance_tools

set -u
KIND="${1:-finance_tools}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/five_level_v2_finance"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | mode=five_level_v2_na | kind=$KIND | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-fin-flv2na-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning finance:$KIND (LLM-only, strict) under impact_mode=five_level_v2_na ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_finance_five_level_v2.py \
  --kind "$KIND" --version-tag scan-fin-flv2na --out-dir "$OUT"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== summary (impact_mode=five_level_v2_na) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d.get('score_max'),'| assets',len(d.get('asset_sensitivity',{})),'| bands',d.get('band_distribution'))" "$f" 2>/dev/null
  done
fi

echo "=== done (kind=$KIND rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
