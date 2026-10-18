#!/bin/bash
#SBATCH --job-name=mcp-breadth-finance
#SBATCH --partition=main
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/breadth-finance-%j.out

# The scanner's breadth pass over the 5 live-captured finance catalogs (yahoo_finance,
# finance_tools, maverick, sec_edgar, openbb). Same shape as scan_breadth.sbatch, which
# only covers github/slack/calendar; the finance _scan.json artifacts on disk predate a
# working Ollama connection and are 100% "unclassified" — this replaces them for real.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11000 + SLURM_JOB_ID % 2000))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO" || exit 1
mkdir -p runs

echo "=== $(hostname) ==="
nvidia-smi -L

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/runs/ollama-breadth-finance-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
for _ in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 || { echo "ollama did not start"; kill $SERVE_PID; exit 1; }
echo "ollama up on :$PORT"

OLLAMA_HOST="http://127.0.0.1:$PORT" "$REPO/.venv/bin/python" \
    "$REPO/scripts/scan_breadth.py" --model qwen2.5:32b \
    --catalog reports/scan_finance/tool_lists/yahoo_finance.json \
    --catalog reports/scan_finance/tool_lists/finance_tools.json \
    --catalog reports/scan_finance/tool_lists/maverick.json \
    --catalog reports/scan_finance/tool_lists/sec_edgar.json \
    --catalog reports/scan_finance/tool_lists/openbb.json
RC=$?

kill $SERVE_PID 2>/dev/null
wait $SERVE_PID 2>/dev/null
echo "=== done rc=$RC ==="
exit $RC
