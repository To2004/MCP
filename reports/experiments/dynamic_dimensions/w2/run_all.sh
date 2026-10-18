#!/bin/bash
# Full pipeline: worlds -> feature batch 1 (dims2) -> feature batch 2 (dims3) -> compact prep -> selection.
# Parallelism is capped to stay inside the 32 GB job memory limit.
cd "$(dirname "$0")/.."
D=/home/ovadyat/MCP/runs/dynamic_dimensions/w2
PY=/home/ovadyat/MCP/.venv/bin/python
mkdir -p "$D"
declare -A SRV=([github_M]=github [calendar_M]=calendar [slack_M]=slack [github_S]=github [calendar_L]=calendar
                [slack_churn]=slack [github_bots]=github [calendar_M2]=calendar [slack_M2]=slack)
declare -A ARGS=([github_M]="--agents 50 --days 730 --seed 1" [calendar_M]="--agents 50 --days 730 --seed 1"
                 [slack_M]="--agents 50 --days 730 --seed 1" [github_S]="--agents 12 --days 730 --seed 2"
                 [calendar_L]="--agents 150 --days 365 --seed 3" [slack_churn]="--agents 50 --days 730 --seed 4 --churn 3"
                 [github_bots]="--agents 50 --days 730 --seed 5 --bot-share 2.5"
                 [calendar_M2]="--agents 50 --days 730 --seed 6" [slack_M2]="--agents 50 --days 730 --seed 7")
NAMES="github_M calendar_M slack_M github_S calendar_L slack_churn github_bots calendar_M2 slack_M2"
throttle() { while [ "$(jobs -rp | wc -l)" -ge "$1" ]; do sleep 5; done; }
rm -f "$D"/*.npz
for n in $NAMES; do throttle 5; $PY -W ignore world2.py --server "${SRV[$n]}" --per-kind 30 ${ARGS[$n]} --out "w2/$n.csv.gz" & done; wait
echo WORLDS_DONE
for n in $NAMES; do throttle 3; $PY -W ignore dims2.py --world "w2/$n.csv.gz" --server "${SRV[$n]}" --out "$D/$n.npz" & done; wait
echo DIMS2_DONE
for n in $NAMES; do throttle 3; $PY -W ignore dims3.py --world "w2/$n.csv.gz" --server "${SRV[$n]}" --out "$D/${n}_x.npz" & done; wait
echo DIMS3_DONE
for n in $NAMES; do throttle 4; $PY -W ignore eval2.py --scores-dir "$D" --prep "$D/$n.npz" & done; wait
echo PREP_DONE
$PY -W ignore eval2.py --scores-dir "$D" --scenarios $NAMES --load 2 --steps 16
$PY -W ignore report2.py
echo FULL_DONE
