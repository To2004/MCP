#!/bin/bash
#SBATCH --job-name=mcp-static-score
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/home/ovadyat/MCP/reports/static-score-%j.out

# Regenerate the static risk tables with the local LLM (Qwen2.5:32b) instead of
# the offline deterministic fallback. Mirrors scripts/rank_on_gpu.sbatch.
# GPU pick per the cluster rule: rtx_4090 first; fall back to rtx_3090/rtx_pro_6000
# by editing --gres if no 4090 slot is free.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11500

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
# Fit 32B-Q4 on one 24GB GPU: cap ctx + shrink KV so all layers offload.
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== node: $(hostname) | CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv 2>/dev/null

echo "=== starting ollama serve on $OLLAMA_HOST ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!

for i in $(seq 1 90); do
  curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; break; }
  sleep 1
done

# The python client needs a scheme-qualified host.
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"
PY="$REPO/.venv/bin/python"
RC=0

echo "=== static scoring: ALL demo servers → one combined file (Qwen2.5:32b) ==="
"$PY" -m mcp_security.static_scoring --all
RC=$(( RC || $? ))

# Determinism check: re-score one server and diff against a second pass. With
# temperature=0 + fixed seed the two JSONs must be byte-identical.
echo "=== determinism check (cbg_sqlite scored twice) ==="
"$PY" -m mcp_security.static_scoring --kind cbg_sqlite --out "$REPO/reports/det_a.json" >/dev/null
"$PY" -m mcp_security.static_scoring --kind cbg_sqlite --out "$REPO/reports/det_b.json" >/dev/null
if diff -q "$REPO/reports/det_a.json" "$REPO/reports/det_b.json" >/dev/null; then
  echo "DETERMINISTIC: two passes are byte-identical"
else
  echo "NON-DETERMINISTIC: passes differ"; diff "$REPO/reports/det_a.json" "$REPO/reports/det_b.json" | head -40
fi
rm -f "$REPO/reports/det_a.json" "$REPO/reports/det_b.json"

echo "=== gpu mem in use ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv 2>/dev/null

kill "$SERVE_PID" 2>/dev/null
echo "=== DONE rc=$RC ==="
exit $RC
