#!/bin/bash
#SBATCH --job-name=mcp-scan-calendar
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:40:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-calendar-%j.out

# Single-GPU static scan of the Google Calendar MCP with the revised prompts
# (realistic+domain-grounded tool impact, characteristic-content sensitivity,
# completed blast decision procedure, reason-before-score schemas). Strict
# LLM-only mode: aborts rather than fabricate if the model is unreachable.
# GPU pick per the cluster rule: rtx_4090 (top-ranked, had idle slots at submit).

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=11500
PY="$REPO/.venv/bin/python"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# Fit 32B-Q4 on one 24GB GPU: cap ctx + shrink KV so all layers offload.
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p reports/scan reports/exports
RC=0

echo "=== node: $(hostname) | CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} ==="
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "reports/ollama-calendar-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!

up=0
for t in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${t}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

echo "=== scanning calendar:real (strict, LLM-only) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT \
  "$PY" -m mcp_security.scanner --kind calendar --server "calendar:real" \
    --out "reports/scan/calendar_real.md" --version-tag "scan-stage3"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== exporting json + csv + md (deterministic, no LLM) ==="
  "$PY" scripts/export_scan.py reports/scan/calendar_real.json --out-dir reports/exports
  echo "=== band distribution ==="
  "$PY" -c "import json;d=json.load(open('reports/scan/calendar_real.json'));print(d['band_distribution'])"
  echo "=== blast consistency (drift flagged by the new deterministic check) ==="
  "$PY" -c "import json;d=json.load(open('reports/scan/calendar_real.json'));f=d.get('blast_consistency',{}).get('flagged',[]);print('no drift' if not f else json.dumps(f,indent=2))"
  echo "=== risk matrix (with s x b x i in place) ==="
  sed -n '/## Risk matrix/,/## Tool atomic/p' reports/scan/calendar_real.md
fi

echo "=== shutting down ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
echo "=== DONE (rc=$RC) ==="
exit $RC
