#!/bin/bash
#SBATCH --job-name=mcp-scan-rank
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-rank-%j.out

# Run the full pipeline on a GPU node with the local LLM (Qwen2.5:32b):
#   1. statically scan each demo server (tools from Excel, assets from disk) and
#      derive its risk matrix with the LLM in strict (LLM-only) mode;
#   2. rank every captured session's calls against those fresh scans.
# Mirrors scripts/static_score_on_gpu.sbatch. GPU pick per the cluster rule:
# rtx_4090 first; edit --gres to rtx_3090 / rtx_pro_6000 if no 4090 slot is free.

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

# 1. Scan each server the sessions touch. Tools come from the Excel catalog and
#    assets from the on-disk demo store; the LLM derives every risk primitive.
echo "=== scan: filesystem demos + sqlite (LLM-only) ==="
"$PY" -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem \
    --server "fs:corp_filesystem" --out reports/scan/fs_corp_filesystem.md
RC=$(( RC || $? ))
"$PY" -m mcp_security.scanner --kind filesystem --root demo/medical_clinic_fs \
    --server "fs:medical_clinic_fs" --out reports/scan/fs_medical_clinic_fs.md
RC=$(( RC || $? ))
"$PY" -m mcp_security.scanner --kind filesystem --root demo/law_firm_fs \
    --server "fs:law_firm_fs" --out reports/scan/fs_law_firm_fs.md
RC=$(( RC || $? ))
"$PY" -m mcp_security.scanner --kind filesystem --root demo/media_studio_fs \
    --server "fs:media_studio_fs" --out reports/scan/fs_media_studio_fs.md
RC=$(( RC || $? ))
"$PY" -m mcp_security.scanner --kind sqlite --root demo/cbg_sqlite/cbg.db \
    --server "sqlite:cbg_sqlite" --out reports/scan/sqlite_cbg_sqlite.md
RC=$(( RC || $? ))

# 2. Rank every captured session's calls against the fresh scans.
echo "=== rank captured calls against the scans ==="
"$PY" -m mcp_security.call_scoring -v
RC=$(( RC || $? ))

# 3. Grade the scans against the design-time evaluation ground truth.
echo "=== evaluate scanner vs ground truth ==="
"$PY" scripts/evaluate_scanner.py
RC=$(( RC || $? ))

echo "=== gpu mem in use ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv 2>/dev/null

kill "$SERVE_PID" 2>/dev/null
echo "=== DONE rc=$RC ==="
exit $RC
