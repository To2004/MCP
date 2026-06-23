#!/bin/bash
# Waits for a SLURM job to finish (polls every 5 min), checks result,
# submits one retry if LLM timed out. Stops after 3 attempts total.
# Usage: nohup bash wait_and_run.sh <JOB_ID> &

JOB_ID=${1:-18039560}
LOG="/home/ovadyat/MCP/local_llm/wait_and_run.log"
RANK_SCRIPT="/home/ovadyat/MCP/local_llm/run_llm_ranking.sh"
INTERVAL=300   # 5 minutes
MAX_ATTEMPTS=3
ATTEMPT=${2:-1}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "Attempt $ATTEMPT/$MAX_ATTEMPTS — watching job $JOB_ID"

# Poll until job disappears from queue (covers PENDING / RUNNING / COMPLETING)
while true; do
    STATUS=$(squeue -j "$JOB_ID" -h -o "%T" 2>/dev/null)
    [[ -z "$STATUS" ]] && break
    log "Job $JOB_ID: $STATUS — checking again in 5 min."
    sleep $INTERVAL
done

log "Job $JOB_ID finished."

# Give SLURM a moment to flush the output file
sleep 10

OUT_LOG="/home/ovadyat/MCP/local_llm/run_llm_ranking-${JOB_ID}.out"

if [[ ! -f "$OUT_LOG" ]]; then
    log "ERROR: output log not found at $OUT_LOG — cannot determine result."
    exit 1
fi

if grep -q "Ollama response received" "$OUT_LOG"; then
    log "SUCCESS — LLM was used. Excel and MD updated with Qwen2.5 scores."
    log "Report: /home/ovadyat/MCP/local_llm/scoring_notes_local_llm_filesystem.md"
    exit 0
fi

if [[ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]]; then
    log "Max attempts ($MAX_ATTEMPTS) reached — LLM inference kept failing. Claude scores remain in Excel."
    exit 1
fi

log "LLM did not respond — submitting retry (attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS)."
NEW_JOB=$(sbatch "$RANK_SCRIPT" | awk '{print $NF}')
log "New job submitted: $NEW_JOB"

# Restart this script for the new job (exec replaces process, no fork bomb)
exec bash "$0" "$NEW_JOB" "$((ATTEMPT + 1))"
