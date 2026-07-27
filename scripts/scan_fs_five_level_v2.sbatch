#!/bin/bash
#SBATCH --job-name=mcp-fs-five-level-v2
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-fs-flv2-%j.out

# LLM scan of ONLY the corp filesystem MCP (fs:corp) under the five_level_v2_na
# generalized action-type ladder (1 liveness / 2 metadata / 3 read / 4 write+move /
# 5 delete+cancel), coverage blast with population-scale reach, and N/A cells.
# Assets are per-file + per-directory (real names) with gen-assets homing.
# Writes reports/experiments/five_level_v2_fs/{fs_corp.{json,md},scoring-prompts.md}.
#   sbatch scripts/scan_fs_five_level_v2.sbatch

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
echo "=== node: $(hostname) | mode=five_level_v2_na | server=fs:corp | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

# Snapshot the exact prompt set this experiment sends (impact + coverage-blast + N/A).
"$PY" scripts/dump_scoring_prompts.py --impact-mode five_level_v2_na \
  --out "$REPO/reports/experiments/five_level_v2_fs/scoring-prompts.md"

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-fs-flv2-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning fs:corp (LLM-only, strict) under impact_mode=five_level_v2_na ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_fs_five_level_v2.py
RC=$?

if [ "$RC" = 0 ]; then
  OUT="$REPO/reports/experiments/five_level_v2_fs/fs_corp.json"
  echo "=== summary (impact_mode=five_level_v2_na) ==="
  "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  fs_corp.json: score_max',d['score_max'],'| assets',len(d['asset_sensitivity']),'| bands',d['band_distribution']);ti=d['tool_impact'];print('  tool_impact by level:');[print('   ',t,'=',v) for t,v in sorted(ti.items(), key=lambda kv:(-kv[1],kv[0]))]" "$OUT" 2>/dev/null
fi

echo "=== done (rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
