#!/bin/bash
#SBATCH --job-name=mcp-scan-sqlite
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-sqlite-%j.out

# Scan only the cbg_sqlite server (the one missing from the multi-GPU run because
# its tool catalog did not exist yet). LLM-only, single GPU.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11500
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"

echo "=== node: $(hostname) ==="
# OLLAMA_HOST must be set BEFORE serve so it binds the chosen port, not 11434.
export OLLAMA_HOST=127.0.0.1:$PORT
"$BIN" serve > "$REPO/reports/ollama-serve-sqlite-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for t in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${t}s"; break; }
  sleep 1
done
export OLLAMA_HOST=http://127.0.0.1:$PORT

"$PY" -m mcp_security.scanner --kind sqlite --root demo/cbg_sqlite/cbg.db \
    --server "sqlite:cbg_sqlite" --out reports/scan/sqlite_cbg_sqlite.md
RC=$?
kill "$SERVE_PID" 2>/dev/null
echo "=== DONE rc=$RC ==="
exit $RC
