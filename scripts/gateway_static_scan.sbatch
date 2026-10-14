#!/bin/bash
#SBATCH --job-name=gw-static-scan
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/gw-static-scan-%j.out
# The static side of the gateway demo, on the catalog the gateway captured:
#   1. static-scan (~/mcp-static-scan): PARTS=scan -> sensitivity, impact, blast radius
#      (levels only); PARTS=inputs -> input importance (which inputs can change the risk)
#   2. scan_breadth.py: which inputs are quantities (the runtime factor's spec)
#   3. static_cells: levels -> cells with the repo's v5 formula
#   Steps 2-3 run only when PARTS includes scan.
# One private Ollama on the allocated GPU serves both scans. Compute nodes have no
# internet; qwen2.5:32b is already in OLLAMA_MODELS.
#
#   sbatch --export=ALL,NAME=github_remote scripts/gateway_static_scan.sbatch
#   sbatch --export=ALL,NAME=github_remote,PARTS=inputs scripts/gateway_static_scan.sbatch
set -u
NAME=${NAME:-github_remote}
PARTS=${PARTS:-scan}
REPO=/home/ovadyat/MCP
SCAN_REPO=/home/ovadyat/mcp-static-scan
DIR=$REPO/reports/experiments/gateway/$NAME
CATALOG=$DIR/$NAME.json
POLICY=$DIR/github_helios_remote.md
OUT=$DIR/${PARTS//,/_}  # scan/ or inputs/: two jobs must not share a log
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11000 + SLURM_JOB_ID % 2000))  # two jobs on one node must not share a port
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CONTEXT_LENGTH=16384  # static-scan asks for 16384; breadth needs less
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== $(hostname) $NAME ==="
nvidia-smi -L
OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/runs/ollama-gw-static-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
trap 'kill $SERVE_PID 2>/dev/null; wait $SERVE_PID 2>/dev/null' EXIT
for _ in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 || { echo "ollama did not start"; exit 1; }
echo "ollama up on :$PORT"

cd "$SCAN_REPO" || exit 1
"$SCAN_REPO/.venv/bin/static-scan" run --catalog "$CATALOG" --policy "$POLICY" --parts "$PARTS" \
    --name "$NAME" --out "$OUT" --host "http://127.0.0.1:$PORT" -v
SCAN_RC=$?
echo "=== static-scan rc=$SCAN_RC ==="

case ",$PARTS," in
  *,scan,*) ;;
  *) echo "=== done static-scan=$SCAN_RC (parts $PARTS) ==="; exit $SCAN_RC ;;
esac

cd "$REPO" || exit 1
OLLAMA_HOST="http://127.0.0.1:$PORT" "$REPO/.venv/bin/python" scripts/scan_breadth.py \
    --catalog "$CATALOG" --model qwen2.5:32b
BREADTH_RC=$?
echo "=== breadth rc=$BREADTH_RC ==="

"$REPO/.venv/bin/python" -m mcp_security.gateway.static_cells \
    --scan "$OUT/$NAME.scan.json" --out "$DIR/$NAME.cells.json"
CELLS_RC=$?
echo "=== done scan=$SCAN_RC breadth=$BREADTH_RC cells=$CELLS_RC ==="
exit $(( SCAN_RC | BREADTH_RC | CELLS_RC ))
