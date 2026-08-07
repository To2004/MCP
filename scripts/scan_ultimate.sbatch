#!/bin/bash
#SBATCH --job-name=mcp-ult
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-ult-%x-%j.out

# Experiment `five_level_v2_ult` (+ ablation arms): org profile in every stage,
# sensitivity from the profile's own per-asset table, gated blast floor +
# alias-twin pass in assembly, band_label_v5. Scans calendar:real, slack:real,
# github:real, fs:corp_filesystem; results land in reports/experiments/<mode>/.
#   sbatch scripts/scan_ultimate.sbatch                              # base arm
#   sbatch --job-name=mcp-ult-tools scripts/scan_ultimate.sbatch five_level_v2_ult_tools
#   sbatch --job-name=mcp-ult-lean  scripts/scan_ultimate.sbatch five_level_v2_ult_leanimp
#   sbatch --job-name=mcp-ult-strct scripts/scan_ultimate.sbatch five_level_v2_ult_struct

set -u
MODE="${1:-five_level_v2_ult}"
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
echo "=== node: $(hostname) | mode=$MODE | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-ult-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_ultimate.py --impact-mode "$MODE" --out-dir "$OUT"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=$MODE) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| sens',d['sensitivity_source'],'| floored',d['blast_floor'].get('raised_cells'),'| fixups',len(d['alias_fixups']),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
