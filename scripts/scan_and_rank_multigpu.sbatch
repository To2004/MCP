#!/bin/bash
#SBATCH --job-name=mcp-scan-rank-mg
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-rank-mg-%j.out

# Full pipeline on MULTIPLE GPUs (one local-LLM instance per GPU):
#   1. statically scan each demo server (tools from Excel, assets from disk) and
#      derive its risk matrix with Qwen2.5:32b in strict (LLM-only) mode — scans
#      run in PARALLEL, sharded across the allocated GPUs;
#   2. rank every captured session's calls against those fresh scans;
#   3. grade the scans against the design-time evaluation ground truth.
#
# GPU pick per the cluster rule: rtx_4090 first (it currently has free, idle
# slots). If no 4090 is schedulable, change --gres to rtx_pro_6000 / rtx_3090.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11500

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# Fit 32B-Q4 on one 24GB GPU: cap ctx + shrink KV so all layers offload.
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
PY="$REPO/.venv/bin/python"
mkdir -p reports/scan
RC=0

echo "=== node: $(hostname) | CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv 2>/dev/null
NGPU=$(nvidia-smi -L 2>/dev/null | wc -l)
[ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs visible"; exit 1; }
echo "=== starting $NGPU ollama instance(s), one per GPU ==="

SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  # Pin this instance to GPU i and give it its own port + runtime home.
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port OLLAMA_MODELS=/home/ovadyat/local-llm/models \
    "$BIN" serve > "$REPO/reports/ollama-serve-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done

# Wait for every instance to answer.
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  for t in $(seq 1 120); do
    curl -s "http://127.0.0.1:$port/api/tags" >/dev/null 2>&1 && { echo "gpu$i (port $port) up after ${t}s"; break; }
    sleep 1
  done
done

# Scan jobs: kind|root|server-name. The artifact stem is derived from the name
# (fs:corp_filesystem -> fs_corp_filesystem) and matches call_scoring's SOURCES.
JOBS=(
  "filesystem|demo/corp_filesystem|fs:corp_filesystem"
  "filesystem|demo/medical_clinic_fs|fs:medical_clinic_fs"
  "filesystem|demo/law_firm_fs|fs:law_firm_fs"
  "filesystem|demo/media_studio_fs|fs:media_studio_fs"
  "sqlite|demo/cbg_sqlite/cbg.db|sqlite:cbg_sqlite"
)

# Save each MCP's own tools/list (authoritative tool inventory + input schemas).
echo "=== saving each MCP's tools/list ==="
"$PY" scripts/save_tool_lists.py
RC=$(( RC || $? ))

echo "=== scanning ${#JOBS[@]} servers across $NGPU GPU(s) (strict, LLM-only) ==="
SCAN_PIDS=()
idx=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind root name <<< "$job"
  port=$((BASE_PORT + (idx % NGPU)))
  stem=$(echo "$name" | tr ':' '_')
  echo "  -> $name on gpu$((idx % NGPU)) (port $port)"
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" -m mcp_security.scanner --kind "$kind" --root "$root" --server "$name" \
      --by-file --out "reports/scan/${stem}.md" \
      > "$REPO/reports/scan-${stem}-${SLURM_JOB_ID}.log" 2>&1 &
  SCAN_PIDS+=($!)
  idx=$((idx + 1))
done

for pid in "${SCAN_PIDS[@]}"; do
  wait "$pid" || RC=1
done
echo "=== scans done (rc=$RC); artifacts: ==="
ls -1 reports/scan/*.json 2>/dev/null

# Derive per-tool input-parameter rubrics (magnitude cutoffs) per server.
echo "=== deriving input-parameter rubrics across $NGPU GPU(s) ==="
PARAM_PIDS=()
idx=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind root name <<< "$job"
  port=$((BASE_PORT + (idx % NGPU)))
  stem=$(echo "$name" | tr ':' '_')
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" -m mcp_security.param_scoring --kind "$kind" --server "$name" \
      > "$REPO/reports/param-${stem}-${SLURM_JOB_ID}.log" 2>&1 &
  PARAM_PIDS+=($!)
  idx=$((idx + 1))
done
for pid in "${PARAM_PIDS[@]}"; do wait "$pid" || RC=1; done

# Rank captured calls against the fresh scans, escalated by parameter risk.
echo "=== ranking captured calls (with parameter escalation) ==="
"$PY" -m mcp_security.call_scoring -v
RC=$(( RC || $? ))

# Grade the scans: vs the LLM-generated tables AND vs the independent human heatmaps.
echo "=== grading scanner vs LLM ground truth ==="
"$PY" scripts/evaluate_scanner.py
RC=$(( RC || $? ))
echo "=== grading scanner vs INDEPENDENT oracle panel (multi-rater + inter-rater) ==="
"$PY" scripts/evaluate_vs_human.py
RC=$(( RC || $? ))
echo "=== scorer head-to-head (scanner vs classical + generic-LLM baselines) ==="
"$PY" scripts/compare_scorers.py
RC=$(( RC || $? ))
echo "=== dynamic evaluation (request-time detection on captured calls) ==="
"$PY" scripts/evaluate_calls.py
RC=$(( RC || $? ))
echo "=== formula sensitivity (band cut-point robustness, no model) ==="
"$PY" scripts/formula_sensitivity.py
RC=$(( RC || $? ))

# Deterministic correctness gate (no model). The LLM reviewers (methodology judge,
# results verdict, advisor) need a larger context window than this scan job uses,
# so run them afterwards via scripts/review_on_gpu.sbatch.
echo "=== deterministic verification gate ==="
"$PY" -m mcp_security.review verify
RC=$(( RC || $? ))

echo "=== gpu mem in use ==="
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv 2>/dev/null

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
echo "=== DONE rc=$RC ==="
exit $RC
