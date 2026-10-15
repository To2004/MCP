#!/bin/bash
#SBATCH --job-name=gw-loadtest
#SBATCH --partition=main
#SBATCH --cpus-per-task=48
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/gw-loadtest-%j.out
# Load test of the gateway on a dedicated CPU node: modes x concurrency x shards against
# local fake MCP servers (no network beyond the node). See loadtest.py.
#   sbatch reports/experiments/gateway/scale/loadtest.sbatch
#   sbatch --export=ALL,GATEWAY=aiohttp,MODES=off,inline,background reports/.../loadtest.sbatch
set -u
GATEWAY=${GATEWAY:-httpx}
MODES=${MODES:-direct,off,inline,background}
LEVELS=${LEVELS:-1,16,64,256,1024}
SHARDS=${SHARDS:-1,2,4,8}
REPO=/home/ovadyat/MCP
PY=$REPO/.venv/bin/python
OUT=$REPO/reports/experiments/gateway/scale/results_load${SUFFIX:-}.jsonl
cd "$REPO" || exit 1
echo "=== $(hostname) $(nproc) cpus, gateway=$GATEWAY modes=$MODES levels=$LEVELS shards=$SHARDS ==="
: > "$OUT"
"$PY" reports/experiments/gateway/scale/loadtest.py --gateway "$GATEWAY" \
    --levels "$LEVELS" --shards "$SHARDS" --modes "$MODES" \
    --seconds "${SECONDS_PER_CELL:-20}" --procs 16 --history caller --port-offset "${PORT_OFFSET:-0}" \
    --upstream-delay-ms "${UPSTREAM_DELAY_MS:-0}" --out "$OUT"
echo "=== done rc=$? ==="
