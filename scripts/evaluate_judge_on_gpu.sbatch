#!/bin/bash
#SBATCH --job-name=mcp-judge-eval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/judge-eval-%j.out

# Run the evaluation-only judge over the committed scans and report per-primitive
# agreement (how well an independent reviewer concurs with the scores I produced).
# BLAST_SAMPLE bounds the per-server blast cells judged (0 = all).

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
BLAST_SAMPLE="${BLAST_SAMPLE:-30}"

echo "=== node $(hostname) | blast_sample=$BLAST_SAMPLE ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }; sleep 1; done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
"$REPO/.venv/bin/python" scripts/evaluate_judge_agreement.py --blast-sample "$BLAST_SAMPLE"
RC=$?
echo "=== judge eval done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null
exit $RC
