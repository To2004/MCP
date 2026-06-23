#!/bin/bash
#SBATCH --job-name=mcp-score-1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --output=/home/ovadyat/MCP/reports/score-%x-%j.out

# Score ONE server (model-reviewed, judge on) to reports/samples/parts*/<name>.json.
# Designed to fan out across GPUs: launch one of these per server, then combine
# the parts on the login node with `--combine`. Args: $1 = server name,
# $2 = "take2" (optional) for per-file full-path filesystem assets.
#
# GPU pick per the cluster rule: rtx_4090 first.

set -u
SERVER="${1:?usage: sbatch static_score_one.sbatch <server_name> [take2]}"
VARIANT="${2:-take1}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
# Unique port per job so co-located jobs on a 3-GPU node don't collide.
PORT=$(( 11000 + SLURM_JOB_ID % 2000 ))

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== $SERVER on $(hostname) | port $PORT | gpu ${CUDA_VISIBLE_DEVICES:-?} ==="
"$BIN" serve > "$REPO/reports/ollama-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 90); do
  curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }
  sleep 1
done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
if [ "$VARIANT" = "take2" ]; then
  OUTDIR=reports/samples/parts_take2; TAKE2_FLAG=--take2
else
  OUTDIR=reports/samples/parts; TAKE2_FLAG=
fi
mkdir -p "$OUTDIR"
"$REPO/.venv/bin/python" -m mcp_security.static_scoring \
  --kind "$SERVER" $TAKE2_FLAG --out "$OUTDIR/$SERVER.json"
RC=$?

kill "$SERVE_PID" 2>/dev/null
echo "=== DONE $SERVER rc=$RC ==="
exit $RC
