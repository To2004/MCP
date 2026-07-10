#!/bin/bash
#SBATCH --job-name=mcp-improve2
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/improve2-%j.out

# Validate the improved rules on TWO servers only (fs:corp_filesystem, github:cbg):
#  1) re-scan them with the refined BLAST/ASSET prompts (version scan-rules-v6)
#  2) re-run the judge-agreement eval on just those two, with the now-fair judge
#     (same scoring rules as the proposer).

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
OUT=/home/ovadyat/MCP/reports/scan
PORT=$((11600 + RANDOM % 300))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

echo "=== node $(hostname) ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }; sleep 1; done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"; PY="$REPO/.venv/bin/python"; RC=0

echo "=== 1/3 re-scan fs:corp_filesystem (improved rules) ==="
"$PY" -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem \
  --server fs:corp_filesystem --by-file --scan-dir "$OUT" \
  --out "$OUT/fs_corp_filesystem.md" --version-tag "scan-rules-v6" || RC=1

echo "=== 2/3 re-scan github:cbg (improved rules) ==="
"$PY" -m mcp_security.scanner --kind github --server github:cbg --scan-dir "$OUT" \
  --out "$OUT/github_cbg.md" --version-tag "scan-rules-v6" || RC=1

echo "=== 3/4 holistic heatmap coherence review (primary validator) ==="
"$PY" scripts/evaluate_heatmap_review.py \
  --servers fs_corp_filesystem github_cbg \
  --out reports/evaluation/heatmap_review_v6.md || RC=1

echo "=== 4/4 per-primitive judge-agreement (secondary) ==="
"$PY" scripts/evaluate_judge_agreement.py \
  --servers fs_corp_filesystem github_cbg --blast-sample 40 \
  --out reports/evaluation/judge_agreement_v6.md || RC=1

echo "=== done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null
exit $RC
