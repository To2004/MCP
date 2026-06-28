#!/bin/bash
#SBATCH --job-name=mcp-newsims
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/newsims-%j.out

# Scan the five NEW simulations across the big MCPs (scripts/make_simulations.py),
# derive their parameter rubrics, then re-rank the WHOLE corpus (old + new) and
# re-grade. Calendar/github/slack are declarative (few assets -> fast scans); the
# fintech filesystem is the only slow one. One Ollama instance per GPU.
set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
BASE_PORT=11500
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
cd "$REPO"; PY="$REPO/.venv/bin/python"; mkdir -p reports/scan; RC=0

NGPU=$(nvidia-smi -L 2>/dev/null | wc -l); [ "${NGPU:-0}" -ge 1 ] || { echo "no GPUs"; exit 1; }
echo "=== $(hostname): $NGPU GPU(s) ==="
SERVE_PIDS=()
for i in $(seq 0 $((NGPU - 1))); do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST=127.0.0.1:$port "$BIN" serve \
    > "$REPO/reports/ollama-serve-${SLURM_JOB_ID}-gpu${i}.log" 2>&1 &
  SERVE_PIDS+=($!)
done
for i in $(seq 0 $((NGPU - 1))); do
  for t in $(seq 1 120); do
    curl -s "http://127.0.0.1:$((BASE_PORT + i))/api/tags" >/dev/null 2>&1 && break; sleep 1
  done
done

# (kind|root|server) — root is '-' for declarative kinds (assets from the registry).
JOBS=(
  "calendar|-|calendar:cbg"
  "github|-|github:cbg"
  "slack|-|slack:cbg"
  "sqlite|demo/devops_sqlite/devops.db|sqlite:devops_sqlite"
  "filesystem|demo/fintech_fs|fs:fintech_fs"
)

echo "=== ensure simulations exist ==="
"$PY" scripts/make_simulations.py; RC=$(( RC || $? ))

echo "=== scanning ${#JOBS[@]} new servers (strict, LLM-only) ==="
SCAN_PIDS=(); idx=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind root name <<< "$job"
  port=$((BASE_PORT + (idx % NGPU))); stem=$(echo "$name" | tr ':' '_')
  rootarg=(); [ "$root" != "-" ] && rootarg=(--root "$root")
  byfile=(); [ "$kind" = "filesystem" ] && byfile=(--by-file)
  echo "  -> $name ($kind) on gpu$((idx % NGPU))"
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" -m mcp_security.scanner --kind "$kind" "${rootarg[@]}" --server "$name" \
      "${byfile[@]}" --out "reports/scan/${stem}.md" \
      > "$REPO/reports/scan-${stem}-${SLURM_JOB_ID}.log" 2>&1 &
  SCAN_PIDS+=($!); idx=$((idx + 1))
done
for pid in "${SCAN_PIDS[@]}"; do wait "$pid" || RC=1; done
echo "=== scans done (rc=$RC) ==="; ls -1 reports/scan/*.json 2>/dev/null

echo "=== deriving parameter rubrics (calendar attendees, sqlite LIMIT, etc.) ==="
PARAM_PIDS=(); idx=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind root name <<< "$job"
  port=$((BASE_PORT + (idx % NGPU)))
  OLLAMA_HOST=http://127.0.0.1:$port \
    "$PY" -m mcp_security.param_scoring --kind "$kind" --server "$name" \
      > "$REPO/reports/param-$(echo "$name" | tr ':' '_')-${SLURM_JOB_ID}.log" 2>&1 &
  PARAM_PIDS+=($!); idx=$((idx + 1))
done
for pid in "${PARAM_PIDS[@]}"; do wait "$pid" || RC=1; done

echo "=== rank the whole corpus (old + new) ==="
"$PY" -m mcp_security.call_scoring -v; RC=$(( RC || $? ))
echo "=== grade scanner (LLM tables + oracle panel) + formula sensitivity ==="
"$PY" scripts/evaluate_scanner.py; RC=$(( RC || $? ))
"$PY" scripts/evaluate_vs_human.py; RC=$(( RC || $? ))
"$PY" scripts/formula_sensitivity.py; RC=$(( RC || $? ))
echo "=== deterministic verification gate ==="
"$PY" -m mcp_security.review verify; RC=$(( RC || $? ))

for pid in "${SERVE_PIDS[@]}"; do kill "$pid" 2>/dev/null; done
echo "=== DONE rc=$RC ==="; exit $RC
