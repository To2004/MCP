#!/bin/bash
# Coarse dimensions for the 9 scenarios, then re-prepare each scenario with all feature batches.
cd "$(dirname "$0")/.."
D=/home/ovadyat/MCP/runs/dynamic_dimensions/w2
PY=/home/ovadyat/MCP/.venv/bin/python
declare -A SRV=([github_M]=github [calendar_M]=calendar [slack_M]=slack [github_S]=github [calendar_L]=calendar
                [slack_churn]=slack [github_bots]=github [calendar_M2]=calendar [slack_M2]=slack)
NAMES="github_M calendar_M slack_M github_S calendar_L slack_churn github_bots calendar_M2 slack_M2"
throttle() { while [ "$(jobs -rp | wc -l)" -ge "$1" ]; do sleep 5; done; }
for n in $NAMES; do throttle 4; $PY -W ignore dims4.py --world "w2/$n.csv.gz" --server "${SRV[$n]}" --out "$D/${n}_h.npz" & done; wait
echo DIMS4_DONE
for n in $NAMES; do throttle 4; $PY -W ignore eval2.py --scores-dir "$D" --prep "$D/$n.npz" & done; wait
echo COARSE_PREP_DONE
