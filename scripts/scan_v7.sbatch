#!/bin/bash
#SBATCH --job-name=mcp-v7
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/home/ovadyat/MCP/reports/scan-v7-%x-%j.out

# v7 — the framework-NATIVE policy arms. Same scanner, same tool catalogs, same
# four organizations as the v5r `nacombo` arm; what changes is the document each
# organization publishes. Instead of one register shape for everyone, each arm
# reads a policy written in its own framework's shape:
#
#   iso   docs/mcp-tools/server-policies-iso.md    A.5.9 inventory + A.8.3 authorization
#   nist  docs/mcp-tools/server-policies-nist.md   SP 800-60 types + AC-3 authorization
#   cis   docs/mcp-tools/server-policies-cis.md    Safeguard 3.2 inventory + 3.3 ACLs
#
# All three drop the register's Flags column (inert in nacombo already: that arm
# runs asset_flags=none, floors=none, and v5r removed the blast roof) and all
# three state, per asset, which of the tools that REACH it the organization
# actually SANCTIONS. Sensitivity is still derived — no register states a number.
#
#   sbatch scripts/scan_v7.sbatch iso                       # one arm, all 4 servers
#   sbatch scripts/scan_v7.sbatch nist github_helios        # one arm, one server
#   sbatch scripts/scan_v7.sbatch cis "" overwrite          # re-scan an arm
#
# Results land in reports/experiments/v7/five_level_v2_policy_v7_<arm>/; the
# driver skips targets that already have an artifact unless `overwrite` is passed.

set -u
ARM="${1:-iso}"
ONLY="${2:-}"
OVERWRITE="${3:-}"
REPO=/home/ovadyat/MCP
BIN=/home/ovadyat/local-llm/ollama
PORT=$((11600 + RANDOM % 300))
PY="$REPO/.venv/bin/python"

case "$ARM" in
  iso|nist|cis) MODE="five_level_v2_v7_${ARM}" ;;
  *) echo "unknown arm '$ARM'; choose iso, nist or cis"; exit 2 ;;
esac
OUT="$REPO/reports/experiments/v7/five_level_v2_policy_v7_${ARM}"
# The four organizations the v7 experiment covers. Same four in every arm, so a
# cross-arm difference is attributable to the policy document alone.
SERVERS="${ONLY:-fs_corp_filesystem,github_helios,slack_vireo,calendar_aurora}"

export OLLAMA_MODELS=/home/ovadyat/local-llm/models
export OLLAMA_KEEP_ALIVE=10m
# A framework-native policy section runs longer than the baseline's — the ISO
# github section alone is ~1400 words once the access-restriction rules are in —
# and it rides in every prompt alongside the rubric and the sibling lists.
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

cd "$REPO"
mkdir -p "$OUT"
echo "=== node: $(hostname) | arm=$ARM | mode=$MODE | servers=$SERVERS | port=$PORT ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>/dev/null

OLLAMA_HOST=127.0.0.1:$PORT "$BIN" serve > "$REPO/reports/ollama-v7-${ARM}-${SLURM_JOB_ID}.log" 2>&1 &
SERVE_PID=$!
up=0
for i in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && { echo "ollama up after ${i}s"; up=1; break; }
  sleep 1
done
[ "$up" = 1 ] || { echo "ollama never came up"; kill "$SERVE_PID" 2>/dev/null; exit 1; }

ARGS=(--impact-mode "$MODE" --only "$SERVERS")
[ "$OVERWRITE" = "overwrite" ] && ARGS+=(--overwrite)

echo "=== scanning (framework-native policy, derived sensitivity, static impact + LLM fallback) ==="
OLLAMA_HOST=http://127.0.0.1:$PORT "$PY" scripts/scan_policy_v5.py "${ARGS[@]}"
RC=$?

if [ "$RC" = 0 ]; then
  echo "=== per-server summary (impact_mode=$MODE) ==="
  for f in "$OUT"/*.json; do
    "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));s=d.get('tool_impact_source',{});print('  '+sys.argv[1].split('/')[-1]+': score_max',d['score_max'],'| sens',d['sensitivity_source'],'| policy',d.get('description_source'),'| impact static',sum(1 for v in s.values() if v=='static_ladder'),'/',len(s),'| bands',d['band_distribution'])" "$f" 2>/dev/null
  done
fi

echo "=== done (arm=$ARM rc=$RC); stopping ollama ==="
kill "$SERVE_PID" 2>/dev/null
wait "$SERVE_PID" 2>/dev/null
exit $RC
