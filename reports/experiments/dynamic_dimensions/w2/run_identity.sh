#!/bin/bash
# Identity test: rescore the identity variants (variant CSVs already written by identity_variants.py),
# then prepare them. Per-session variants (~500k identities each) run one at a time for memory.
cd "$(dirname "$0")/.."
D=/home/ovadyat/MCP/runs/dynamic_dimensions/w2id
PY=/home/ovadyat/MCP/.venv/bin/python
mkdir -p "$D"
declare -A SRV=([calendar_M]=calendar [slack_M]=slack [github_M]=github)
throttle() { while [ "$(jobs -rp | wc -l)" -ge "$1" ]; do sleep 5; done; }
rm -f "$D"/*.npz
for n in calendar_M slack_M github_M; do
  throttle 3
  v=${n}__shared10
  ( $PY -W ignore dims2.py --world "w2/$v.csv.gz" --server "${SRV[$n]}" --out "$D/$v.npz" &&
    $PY -W ignore dims3.py --world "w2/$v.csv.gz" --server "${SRV[$n]}" --out "$D/${v}_x.npz" ) &
done
wait
echo SHARED_DONE
for n in calendar_M slack_M github_M; do
  v=${n}__session
  $PY -W ignore dims2.py --world "w2/$v.csv.gz" --server "${SRV[$n]}" --out "$D/$v.npz" &&
  $PY -W ignore dims3.py --world "w2/$v.csv.gz" --server "${SRV[$n]}" --out "$D/${v}_x.npz"
done
echo SESSION_DONE
for f in "$D"/*__*.npz; do
  case "$f" in *_x.npz|*compact*) continue;; esac
  throttle 3
  $PY -W ignore eval2.py --scores-dir "$D" --prep "$f" &
done
wait
echo IDENTITY_DONE
