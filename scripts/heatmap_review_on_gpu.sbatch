#!/bin/bash
#SBATCH --job-name=mcp-heatmap-rev
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/heatmap-rev-%j.out

# Framework-grounded, LLM-only, leakage-free holistic review of the risk heatmap
# for the two focus servers. SERVERS env selects which (default: both).

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
SERVERS="${SERVERS:-fs_corp_filesystem github_cbg}"
OUTNAME="${OUTNAME:-heatmap_review.md}"

echo "=== node $(hostname) | servers=$SERVERS ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }; sleep 1; done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
"$REPO/.venv/bin/python" scripts/evaluate_heatmap_review.py \
  --servers $SERVERS --out "reports/evaluation/$OUTNAME"
RC=$?
echo "=== heatmap review done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null
exit $RC
