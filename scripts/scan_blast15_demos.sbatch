#!/bin/bash
#SBATCH --job-name=mcp-scan-b15
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-b15-%j.out

# Re-scan the 10 demo servers with the CURRENT pipeline (judge removed, deterministic
# bands, blast 1-5, hardened proposer prompts) into a DEDICATED output dir so the
# comparison against reports/all_scans.zip is clean and nothing existing is clobbered.
# Pick the server group with --export=GROUP=fs|rest.

set -u
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
OUT=/home/ovadyat/MCP/reports/scan_blast15
PORT=$((11600 + RANDOM % 300))
export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

mkdir -p "$OUT"
GROUP="${GROUP:-fs}"
# kind|root|server-name|extra-flags  (root "-" for declarative kinds)
FS_JOBS=(
  "filesystem|demo/corp_filesystem|fs:corp_filesystem|--by-file"
  "filesystem|demo/fintech_fs|fs:fintech_fs|--by-file"
  "filesystem|demo/law_firm_fs|fs:law_firm_fs|--by-file"
  "filesystem|demo/media_studio_fs|fs:media_studio_fs|--by-file"
  "filesystem|demo/medical_clinic_fs|fs:medical_clinic_fs|--by-file"
)
REST_JOBS=(
  "sqlite|demo/cbg_sqlite/cbg.db|sqlite:cbg_sqlite|"
  "sqlite|demo/devops_sqlite/devops.db|sqlite:devops_sqlite|"
  "github|-|github:cbg|"
  "slack|-|slack:cbg|"
  "calendar|-|calendar:cbg|"
)
if [ "$GROUP" = "fs" ]; then JOBS=("${FS_JOBS[@]}"); else JOBS=("${REST_JOBS[@]}"); fi

echo "=== node $(hostname) | group=$GROUP | ${#JOBS[@]} servers -> $OUT ==="
"$BIN" serve > "$REPO/reports/ollama-serve-$SLURM_JOB_ID.log" 2>&1 &
SERVE_PID=$!
for i in $(seq 1 120); do curl -s "http://$OLLAMA_HOST/api/tags" >/dev/null 2>&1 && { echo "ollama up (${i}s)"; break; }; sleep 1; done
export OLLAMA_HOST=http://127.0.0.1:$PORT

cd "$REPO"; PY="$REPO/.venv/bin/python"; RC=0
for job in "${JOBS[@]}"; do
  IFS='|' read -r kind root name extra <<< "$job"
  stem=$(echo "$name" | tr ':' '_' | tr -c 'A-Za-z0-9_-' '_')
  echo "=== scan $name ($kind) ==="
  if [ "$root" = "-" ]; then
    "$PY" -m mcp_security.scanner --kind "$kind" --server "$name" \
      --out "$OUT/${stem}.md" --version-tag "scan-blast15" || RC=1
  else
    "$PY" -m mcp_security.scanner --kind "$kind" --root "$root" --server "$name" $extra \
      --out "$OUT/${stem}.md" --version-tag "scan-blast15" || RC=1
  fi
done
echo "=== group $GROUP done (rc=$RC) ==="
kill "$SERVE_PID" 2>/dev/null
exit $RC
