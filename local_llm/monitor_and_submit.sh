#!/bin/bash
# Polls SLURM every 5 minutes for the model-download job.
# When it finishes, submits the LLM ranking job automatically.
# Run on login node: nohup bash monitor_and_submit.sh &

DOWNLOAD_JOB=18039233
RANK_SCRIPT="/home/ovadyat/MCP/local_llm/run_llm_ranking.sh"
LOG="/home/ovadyat/MCP/local_llm/monitor.log"
INTERVAL=300   # 5 minutes

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Monitor started. Watching job $DOWNLOAD_JOB." | tee -a "$LOG"

while true; do
    if squeue -j "$DOWNLOAD_JOB" 2>/dev/null | grep -q "$DOWNLOAD_JOB"; then
        STATE=$(squeue -j "$DOWNLOAD_JOB" -h -o "%T" 2>/dev/null)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Job $DOWNLOAD_JOB still running (state: $STATE). Checking again in 5 min." | tee -a "$LOG"
        sleep $INTERVAL
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Job $DOWNLOAD_JOB finished." | tee -a "$LOG"

        # Verify model file exists
        MODEL_DIR="/home/ovadyat/local-llm/models"
        if ls "$MODEL_DIR"/blobs/ 2>/dev/null | grep -q .; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Model files found. Submitting ranking job..." | tee -a "$LOG"
            RANK_JOB=$(sbatch "$RANK_SCRIPT" | awk '{print $NF}')
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Ranking job submitted: $RANK_JOB" | tee -a "$LOG"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Model files not found in $MODEL_DIR — check pull job output." | tee -a "$LOG"
        fi
        break
    fi
done
