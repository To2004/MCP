#!/bin/bash
#SBATCH --job-name=mcp-policy
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-policy-%x-%j.out

# LLM scan with POLICY-grade org context: the data-classification + acceptable-use
# policy (docs/mcp-tools/server-policies.md) is read by EVERY scoring stage instead
# of the per-asset severity inventory, and the asset-sensitivity primitive is
# removed (score = blast x impact, max 25). Same scoring as scan_desc.sbatch —
# only the description document differs.
#
# Pass the comma-separated output stems as arg 1 (default: all 11 servers —
# 5 fs tenants + github/slack/calendar real & cbg).
#   sbatch --job-name=mcp-policy-2 scripts/scan_policy.sbatch fs_fintech_fs,fs_media_studio_fs
#   sbatch --job-name=mcp-policy-real scripts/scan_policy.sbatch github_real,slack_real,calendar_real
#
# Results land in reports/experiments/staticscanner/no_sens/ -- a NEW directory,
# and the driver skips any target already scanned there, so nothing existing is
# overwritten.

set -u
ONLY="${1:-}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"
OUT="$REPO/reports/experiments/staticscanner/no_sens"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# The org policy rides in every prompt, so the context window must hold the
# rubric + the policy section (up to ~450 words) + the tool/asset JSON.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p "$OUT"
echo "=== node: $(hostname) | mode=five_level_v2_policy | only=${ONLY:-ALL} | port=$PORT | CUDA=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-policy-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=(--out-dir "$OUT")
[ -n "$ONLY" ] && ARGS+=(--only "$ONLY")

echo "=== scanning (LLM-only, strict): org POLICY ON, asset sensitivity OFF ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_policy_no_sens.py "${ARGS[@]}"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (description_source=server-policies.md) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| desc_src',d.get('description_source'),'| assets',len(d.get('asset_ids',[])),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (only=${ONLY:-ALL} rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
