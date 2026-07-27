#!/bin/bash
#SBATCH --job-name=mcp-scan-exp
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-exp-%x-%j.out

# Full LLM scan of the REAL catalogs (GitHub 26 / Calendar 13 / Slack 16) under ONE
# tool-impact experiment. Usage:
#   sbatch --job-name=mcp-exp-<mode> scripts/scan_experiment.sbatch <mode>
#   <mode> in {baseline, five_level, cia}
# Writes to reports/experiments/<mode>/<kind>_real.{json,md} so experiments never
# overwrite each other or the committed baseline in reports/scan/.

set -u
MODE="${1:?usage: sbatch scan_experiment.sbatch <baseline|five_level|cia>}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/$MODE"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p "$OUT"
echo "=== node: $(hostname) | mode=$MODE | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-exp-${MODE}-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning (LLM-only, strict) under impact_mode=$MODE, extra args: ${*:2} ==="
OLLAMA_HOST=http://127.0.0.1:$PORT \
  "$PY" scripts/scan_real_catalogs.py --impact-mode "$MODE" --out-dir "$OUT" \
    --version-tag "scan-exp-$MODE" "${@:2}"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=$MODE) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (mode=$MODE rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
