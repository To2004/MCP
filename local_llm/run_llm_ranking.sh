#!/bin/bash
# SLURM job: start Ollama on 4090, run the ranking script, save results.

#SBATCH --partition rtx4090
#SBATCH --time 0-02:00:00
#SBATCH --job-name llm-rank-fs
#SBATCH --output /home/ovadyat/MCP/local_llm/run_llm_ranking-%J.out
#SBATCH --gpus=rtx_4090:1
#SBATCH --constraint=rtx_4090
#SBATCH --mail-user=ovadyat@post.bgu.ac.il
#SBATCH --mail-type=ALL

OLLAMA_BIN="/home/ovadyat/local-llm/bin/ollama"
MODELS_DIR="/home/ovadyat/local-llm/models"
SCRIPT="/home/ovadyat/MCP/local_llm/rank_with_llm.py"

export OLLAMA_MODELS="$MODELS_DIR"
export OLLAMA_HOST="http://127.0.0.1:11434"
export OLLAMA_CONTEXT_LENGTH=8192   # prompt is ~2k tokens; 8k gives plenty of room

source /storage/modules/packages/anaconda/etc/profile.d/conda.sh
conda activate base

echo "[1/4] Starting Ollama server..."
"$OLLAMA_BIN" serve &
OLLAMA_PID=$!

echo "[2/4] Waiting for server to be ready..."
until curl -sf http://127.0.0.1:11434/ > /dev/null 2>&1; do
    sleep 2
done
echo "       Server ready (PID $OLLAMA_PID)"

echo "[3/4] Running ranking script..."
python3 "$SCRIPT"

echo "[4/4] Shutting down Ollama..."
kill $OLLAMA_PID
echo "Done."
