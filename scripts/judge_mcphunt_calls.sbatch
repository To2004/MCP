#!/bin/bash
#SBATCH --job-name=mcphunt-judge
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=/home/ovadyat/MCP/runs/mcphunt-judge-%j.out
# The judge step of scripts/judge_mcphunt_calls.py on one GPU: a private Ollama serves the
# judge model (another family than the scanner's qwen2.5:32b) and the sampled MCPHunt calls
# are rated one by one. Resumable: calls already in the verdicts file are skipped. Compute
# nodes have no internet; pull the model on the login node first (ollama pull gemma3:27b).
#
#   sbatch scripts/judge_mcphunt_calls.sbatch
#   sbatch --export=ALL,MODEL=gemma3:27b,SAMPLE=<sample.jsonl>,OUT=<verdicts.jsonl> \
#       scripts/judge_mcphunt_calls.sbatch
set -u
REPO=/home/ovadyat/MCP
JUDGE_DIR=$REPO/reports/experiments/gateway/mcphunt/judge
MODEL=${MODEL:-gemma3:27b}
SAMPLE=${SAMPLE:-$JUDGE_DIR/sample.jsonl}
OUT=${OUT:-$JUDGE_DIR/verdicts.jsonl}
BIN=/home/ovadyat/local-llm/ollama
PORT=$((13000 + SLURM_JOB_ID % 2000))  # two jobs on one node must not share a port
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CONTEXT_LENGTH=16384  # policy + tool + earlier calls + a cut file body
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== $(hostname) judge $MODEL ==="
nvidia-smi -L
mkdir -p "$REPO/runs"
OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/runs/ollama-judge-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
trap 'kill $SERVE_PID 2>/dev/null; wait $SERVE_PID 2>/dev/null' EXIT
for _ in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 || { echo "ollama did not start"; exit 1; }
echo "ollama up on :$PORT"

cd "$REPO" || exit 1
"$REPO/.venv/bin/python" scripts/judge_mcphunt_calls.py judge --sample "$SAMPLE" --out "$OUT" \
    --model "$MODEL" --host "http://127.0.0.1:$PORT"
RC=$?
echo "=== done judge rc=$RC ==="
exit $RC
