#!/bin/bash
#SBATCH --job-name=mcp-blast-stab
#SBATCH --partition=main
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/blast-stab-%j.out

# Whether blast_radius flips when a server's peer_tools/peer_assets lists (embedded in
# every blast prompt by the production nacombo arm) are presented in reverse order.
# Starts a private Ollama on the allocated GPU, runs scripts/check_blast_stability.py,
# stops it. Compute nodes have no internet, so the model must already be in
# OLLAMA_MODELS (qwen2.5:32b is).
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
# Derived from the job id: two jobs sharing a node must not share a port.
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

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/runs/ollama-blast-stab-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
for _ in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 || { echo "ollama did not start"; kill $SERVE_PID; exit 1; }
echo "ollama up on :$PORT"

OLLAMA_HOST="http://127.0.0.1:$PORT" "$REPO/.venv/bin/python" \
    "$REPO/scripts/check_blast_stability.py" --pairs-per-server 24
RC=$?

kill $SERVE_PID 2>/dev/null
wait $SERVE_PID 2>/dev/null
echo "=== done rc=$RC ==="
exit $RC
