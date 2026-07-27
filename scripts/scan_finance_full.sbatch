#!/bin/bash
#SBATCH --job-name=mcp-scan-finance
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-finance-%x-%j.out

# Full LLM static scan of ONE finance MCP (asset x tool matrix), revised prompts.
# Usage: sbatch --job-name=mcp-scan-<server> scripts/scan_finance_full.sbatch <server>
#   <server> in {finance_tools, maverick}
# GPU pick per the cluster rule: rtx_4090 (top-ranked, had free slots at submit).

set -u
SERVER="${1:?usage: sbatch scan_finance_full.sbatch <finance_tools|maverick>}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11500 + RANDOM % 400))
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# 16K ctx (q8_0 KV still fully offloads on 24GB) — headroom for large tool sets
# like maverick's whole-registry domain-inference prompt.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p reports/scan reports/exports
echo "=== node: $(hostname) | server=$SERVER | port=$PORT ==="
nvidia-smi --query-gpu=index,name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "reports/ollama-finance-${SERVER}-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for t in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${t}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning finance:$SERVER (strict, LLM-only) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT \
  "$PY" scripts/scan_finance_full.py --server "$SERVER"
RC=$?

if [ "$RC" = 0 ]; then
  STEM="finance_${SERVER}"
  DIR="reports/scan_finance_full"
  echo "=== sensitivity + impact ==="
  "$PY" -c "import json;d=json.load(open('${DIR}/${STEM}.json'));print('sensitivity:',d['asset_sensitivity']);print('band_distribution:',d['band_distribution']);f=d.get('blast_consistency',{}).get('flagged',[]);print('model-vs-derived blast mismatches:',len(f))"
  echo "=== risk matrix (s x b x i in place) ==="
  sed -n '/## Risk matrix/,/## Tool atomic/p' "${DIR}/${STEM}.md"
fi

echo "=== shutting down ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
echo "=== DONE (server=$SERVER rc=$RC) ==="
exit $RC
