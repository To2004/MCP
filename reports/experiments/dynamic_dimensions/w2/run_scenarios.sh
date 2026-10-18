#!/bin/bash
# Generate each scenario's world, then score it with the 43-dimension pool.
cd "$(dirname "$0")/.."
PY=/home/ovadyat/MCP/.venv/bin/python
OUT=/home/ovadyat/MCP/runs/dynamic_dimensions/w2
mkdir -p "$OUT"
run() {  # name server args...
  name=$1; server=$2; shift 2
  $PY -W ignore world2.py --server "$server" --per-kind 30 "$@" --out "w2/$name.csv.gz" > "$OUT/$name.log" 2>&1 &&
  $PY -W ignore dims2.py --world "w2/$name.csv.gz" --server "$server" --out "$OUT/$name.npz" >> "$OUT/$name.log" 2>&1
}
run github_M    github   --agents 50  --days 730 --seed 1 &
run calendar_M  calendar --agents 50  --days 730 --seed 1 &
run slack_M     slack    --agents 50  --days 730 --seed 1 &
run github_S    github   --agents 12  --days 730 --seed 2 &
run calendar_L  calendar --agents 150 --days 365 --seed 3 &
run slack_churn slack    --agents 50  --days 730 --seed 4 --churn 3 &
run github_bots github   --agents 50  --days 730 --seed 5 --bot-share 2.5 &
run calendar_M2 calendar --agents 50  --days 730 --seed 6 &
wait
run slack_M2    slack    --agents 50  --days 730 --seed 7
echo ALL_DONE
