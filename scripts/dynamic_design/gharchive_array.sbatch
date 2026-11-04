#!/bin/bash
#SBATCH --job-name=gharchive
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=runs/gharchive/logs/%x-%A_%a.out
#
# GH Archive extraction for the v5 real-data checks: EV-26 request sizes (Hyp5) and X2
# per-actor cadence. CPU only (no GPU). Every number it produces is "real public activity,
# not MCP traffic".
#
# Modules (read their docstrings for the formulas and the privacy rules):
#   reports/experiments/dynamic_dimensions/heldout/gharchive_request_sizes.py
#   reports/experiments/dynamic_dimensions/heldout/gharchive_actor_cadence.py
#
# Run everything from the repository root. One script, the first argument picks the step.
# Steps marked LOGIN run with bash on the login node; the others are submitted with sbatch.
# Compute nodes here have no internet (see breadth_llm.sbatch), so downloading is its own
# step and the array tasks read local files only. One run uses one GHA_ROOT and one key.
#
#   1. LOGIN  bash scripts/dynamic_design/gharchive_array.sbatch key
#             One pseudonym key for the whole run (mode 600, never committed or printed).
#             Refuses while GHA_ROOT holds a selection or parts of an earlier key: start a new
#             run in a fresh GHA_ROOT (or move the old files away).
#   2. LOGIN  bash scripts/dynamic_design/gharchive_array.sbatch download 2024-12-01 2024-12-30
#             Hourly files into $GHA_ROOT/raw/<day>/, plus the day before's 23:00 hour in
#             raw/<day>/lookback/. About 2 GB a day; the full 2024-12-01..2025-08-27 window is
#             about 0.55-0.9 TB (Part A), so download and extract it in chunks (step 9).
#             Hours that are missing or fail `gzip -t` are listed in raw/<day>/MISSING (the
#             lookback hour in raw/<day>/lookback/MISSING). A task refuses a day with any hour
#             missing, so a partial day is never read as a whole one: download it again.
#   3. sbatch --array=0-29%30 scripts/dynamic_design/gharchive_array.sbatch orgs 2024-12-01
#             People per organisation on the learning month (task i = first day + i).
#   4. sbatch scripts/dynamic_design/gharchive_array.sbatch select
#             The top 20 organisations by distinct people plus 20 drawn at random with
#             20-200 people -> $GHA_ROOT/selection.json. The draw depends on the key as well
#             as the seed (the pool is ordered by keyed pseudonyms), so selection.json is the
#             only record of it once the key is gone: keep it frozen.
#   5. sbatch --array=0-269%50 scripts/dynamic_design/gharchive_array.sbatch extract 2024-12-01
#             Per UTC day: request sizes and actor day parts of the selected organisations.
#   6. EV-14 size bank (organisations and a month outside the evaluated ones), with the same
#      key, before step 8: LOGIN download 2024-11-01 2024-11-30, then
#      sbatch --array=0-29%30 ... bank 2024-11-01, then sbatch ... bank-reduce -> size_bank.json.
#   7. sbatch --mem=64G --time=04:00:00 scripts/dynamic_design/gharchive_array.sbatch reduce
#             Publishable aggregates: sizes_summary.json (quantiles; v4 and v5 limits learned
#             on the 30 days from GHA_LEARN_FROM; realised rates; routes and cells under 10
#             actors suppressed) and cadence_summary.json (v5 days; streamed). The sizes
#             summary holds every extract part in memory, hence --mem=64G (cpu nodes have 128
#             GB or more). Check the counts on one month first: run steps 5 and 7 on 30 days and
#             read the parts and actor_days counts before the full window. UTC days whose
#             extract is missing are listed in both summaries ("utc_days": "missing").
#   8. LOGIN  bash scripts/dynamic_design/gharchive_array.sbatch forget
#             Deletes the key and the per-organisation people lists once every extract task
#             (the bank's included) has succeeded: the pseudonyms then link to no login.
#             selection.json stays, as the record of the draw. Re-extracting after this needs
#             a new key and a new run from step 1 in a fresh GHA_ROOT.
#   9. LOGIN  bash scripts/dynamic_design/gharchive_array.sbatch clean 2024-12-01 2024-12-30
#             Deletes downloaded days (after their extract tasks succeeded).
#
# Chain steps with --dependency=afterok:<jobid>. A day that fails (an hour missing from the
# archive itself) blocks afterok; after re-downloading what can be, submit reduce with
# --dependency=afterany to report the day as missing instead. Environment (all optional):
#   GHA_ROOT        work folder (default runs/gharchive); raw downloads, parts and outputs
#   GHA_KEY_FILE    the pseudonym key file (default $GHA_ROOT/pseudonym.key)
#   GHA_LEARN_FROM  first learning day for reduce (default 2024-12-01, Part A's window start)
#   GHA_AGENTS      file of coding-agent logins, one per line (default: the module's list)
#   PY              the Python to run (default .venv/bin/python)
#
# Python runs from the repository root without -I: the extractors import each other as
# `reports.experiments...`, which needs the root on sys.path. Downloads never sit in the
# working directory or next to code; they are only ever passed as file arguments.
set -euo pipefail
shopt -s nullglob

REPO=${REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}
GHA_ROOT=${GHA_ROOT:-$REPO/runs/gharchive}
RAW=$GHA_ROOT/raw
KEY_FILE=${GHA_KEY_FILE:-$GHA_ROOT/pseudonym.key}
SELECTION=$GHA_ROOT/selection.json
PART_DIRS=(orgs sizes cadence bank_parts)
LEARN_FROM=${GHA_LEARN_FROM:-2024-12-01}
PY=${PY:-$REPO/.venv/bin/python}
URL=https://data.gharchive.org
HOURS_PER_DAY=24
LAST_HOUR=23
KEY_BYTES=32
CURL_RETRIES=3
SIZES=reports.experiments.dynamic_dimensions.heldout.gharchive_request_sizes
CADENCE=reports.experiments.dynamic_dimensions.heldout.gharchive_actor_cadence
AGENT_ARGS=()
if [ -n "${GHA_AGENTS:-}" ]; then AGENT_ARGS=(--agents "$GHA_AGENTS"); fi

die() { echo "gharchive: $*" >&2; exit 1; }

[ -f "$REPO/pyproject.toml" ] && [ -d "$REPO/reports/experiments/dynamic_dimensions/heldout" ] \
  || die "run from the repository root (or set REPO)"
cd "$REPO"

task_day() {  # the array task's day: $1 (first day) + SLURM_ARRAY_TASK_ID
  [ -n "${SLURM_ARRAY_TASK_ID:-}" ] || die "submit this step as an array (--array=0-N)"
  date -u -d "$1 + ${SLURM_ARRAY_TASK_ID} days" +%F
}

day_files() {  # set FILES to the 24 hourly files of day $1, or fail when any is missing
  local day=$1 hour file
  if [ -s "$RAW/$day/MISSING" ]; then
    die "$RAW/$day/MISSING lists hours that failed to download: $(tr '\n' ' ' \
      < "$RAW/$day/MISSING")(download the day again)"
  fi
  FILES=()
  for hour in $(seq 0 $LAST_HOUR); do
    file=$RAW/$day/$day-$hour.json.gz
    [ -s "$file" ] || die "missing $file: a partial day is never read (run the download step)"
    FILES+=("$file")
  done
  [ ${#FILES[@]} -eq $HOURS_PER_DAY ] || die "expected $HOURS_PER_DAY hourly files for $day"
}

lookback_file() {  # set LOOKBACK to day $1's lookback hour (the day before's 23:00), or fail
  local day=$1 prev
  prev=$(date -u -d "$day - 1 day" +%F)
  LOOKBACK=$RAW/$day/lookback/$prev-$LAST_HOUR.json.gz
  if [ -s "$RAW/$day/lookback/MISSING" ]; then
    die "the lookback hour of $day failed to download (download the day again)"
  fi
  [ -s "$LOOKBACK" ] || die "missing lookback $LOOKBACK (run the download step)"
}

load_key() {
  [ -s "$KEY_FILE" ] || die "no pseudonym key at $KEY_FILE (run the key step first)"
  GHARCHIVE_PSEUDONYM_KEY=$(<"$KEY_FILE")
  export GHARCHIVE_PSEUDONYM_KEY
}

fetch() {  # fetch $1 (a file name on data.gharchive.org) to $2; list it in $3 when missing
  local name=$1 dest=$2 missing=$3
  if [ -s "$dest" ] && gzip -t "$dest" 2>/dev/null; then return 0; fi
  if curl -sfL --retry "$CURL_RETRIES" -o "$dest.part" "$URL/$name" \
      && gzip -t "$dest.part" 2>/dev/null; then
    mv "$dest.part" "$dest"
  else
    rm -f "$dest.part"
    echo "$name" >> "$missing"
    echo "gharchive: missing or corrupt: $name" >&2
  fi
}

download_day() {  # the 24 hours of day $1 and the day before's last hour
  local day=$1 prev dir=$RAW/$1 hour
  prev=$(date -u -d "$day - 1 day" +%F)
  mkdir -p "$dir/lookback"
  rm -f "$dir/MISSING" "$dir/lookback/MISSING"
  for hour in $(seq 0 $LAST_HOUR); do
    fetch "$day-$hour.json.gz" "$dir/$day-$hour.json.gz" "$dir/MISSING"
  done
  if [ -s "$RAW/$prev/$prev-$LAST_HOUR.json.gz" ]; then
    cp "$RAW/$prev/$prev-$LAST_HOUR.json.gz" "$dir/lookback/"
  else
    fetch "$prev-$LAST_HOUR.json.gz" "$dir/lookback/$prev-$LAST_HOUR.json.gz" \
      "$dir/lookback/MISSING"
  fi
}

each_day() {  # run $1 for every day from $2 to $3 inclusive
  local step=$1 day=$2 last=$3
  [ "$(date -u -d "$day" +%s)" -le "$(date -u -d "$last" +%s)" ] || die "$2 is after $3"
  while [ "$(date -u -d "$day" +%s)" -le "$(date -u -d "$last" +%s)" ]; do
    "$step" "$day"
    day=$(date -u -d "$day + 1 day" +%F)
  done
}

clean_day() { rm -rf "${RAW:?}/$1"; }

STEP=${1:-}
case "$STEP" in
  key)
    mkdir -p "$GHA_ROOT" "$REPO/runs/gharchive/logs"
    if [ -e "$KEY_FILE" ]; then die "a key already exists at $KEY_FILE (forget it first)"; fi
    if [ -e "$SELECTION" ]; then
      die "$SELECTION was made under an earlier key and records that run's draw:" \
        "start the new run in a fresh GHA_ROOT (or move it away)"
    fi
    for dir in "${PART_DIRS[@]}"; do
      old=("$GHA_ROOT/$dir"/*)
      if [ ${#old[@]} -gt 0 ]; then
        die "$GHA_ROOT/$dir holds parts of an earlier key: use a fresh GHA_ROOT"
      fi
    done
    (umask 077 && "$PY" -c "import secrets; print(secrets.token_hex($KEY_BYTES))" > "$KEY_FILE")
    echo "pseudonym key written to $KEY_FILE (mode 600)"
    ;;
  download)
    [ $# -eq 3 ] || die "usage: download FIRST_DAY LAST_DAY (YYYY-MM-DD)"
    each_day download_day "$2" "$3"
    ;;
  orgs)
    [ $# -eq 2 ] || die "usage: orgs FIRST_DAY"
    day=$(task_day "$2")
    day_files "$day"
    load_key
    "$PY" -m "$SIZES" orgs "${AGENT_ARGS[@]}" --out "$GHA_ROOT/orgs/$day.json.gz" "${FILES[@]}"
    ;;
  select)
    parts=("$GHA_ROOT"/orgs/*.json.gz)
    [ ${#parts[@]} -gt 0 ] || die "no orgs parts in $GHA_ROOT/orgs"
    "$PY" -m "$SIZES" select-orgs --out "$SELECTION" "${parts[@]}"
    ;;
  extract)
    [ $# -eq 2 ] || die "usage: extract FIRST_DAY"
    [ -s "$SELECTION" ] || die "no $SELECTION (run the select step first)"
    day=$(task_day "$2")
    day_files "$day"
    lookback_file "$day"
    load_key
    "$PY" -m "$SIZES" extract --day "$day" --orgs "$SELECTION" "${AGENT_ARGS[@]}" \
      --out "$GHA_ROOT/sizes/$day.json.gz" "${FILES[@]}"
    "$PY" -m "$CADENCE" extract --day "$day" --orgs "$SELECTION" "${AGENT_ARGS[@]}" \
      --lookback "$LOOKBACK" --out "$GHA_ROOT/cadence/$day.json.gz" "${FILES[@]}"
    ;;
  reduce)
    sizes=("$GHA_ROOT"/sizes/*.json.gz)
    cadence=("$GHA_ROOT"/cadence/*.json.gz)
    [ ${#sizes[@]} -gt 0 ] && [ ${#cadence[@]} -gt 0 ] || die "no extract parts to reduce"
    "$PY" -m "$SIZES" summarise --learn-from "$LEARN_FROM" \
      --out "$GHA_ROOT/sizes_summary.json" "${sizes[@]}"
    "$PY" -m "$CADENCE" summarise --out "$GHA_ROOT/cadence_summary.json" "${cadence[@]}"
    if [ -e "$KEY_FILE" ]; then echo "reminder: run forget once every extract succeeded"; fi
    ;;
  bank)
    [ $# -eq 2 ] || die "usage: bank FIRST_DAY (a month outside the evaluated window)"
    [ -s "$SELECTION" ] || die "no $SELECTION: the bank excludes the evaluated organisations"
    day=$(task_day "$2")
    day_files "$day"
    load_key
    "$PY" -m "$SIZES" extract --day "$day" --exclude-orgs "$SELECTION" --histograms-only \
      "${AGENT_ARGS[@]}" --out "$GHA_ROOT/bank_parts/$day.json.gz" "${FILES[@]}"
    ;;
  bank-reduce)
    parts=("$GHA_ROOT"/bank_parts/*.json.gz)
    [ ${#parts[@]} -gt 0 ] || die "no bank parts in $GHA_ROOT/bank_parts"
    "$PY" -m "$SIZES" summarise --bank "$GHA_ROOT/size_bank.json" \
      --out "$GHA_ROOT/bank_summary.json" "${parts[@]}"
    ;;
  forget)
    rm -f "$KEY_FILE"
    rm -rf "${GHA_ROOT:?}/orgs"
    echo "pseudonym key and people lists deleted; the pseudonyms now link to no login"
    ;;
  clean)
    [ $# -eq 3 ] || die "usage: clean FIRST_DAY LAST_DAY (YYYY-MM-DD)"
    each_day clean_day "$2" "$3"
    ;;
  *)
    die "usage: key | download F L | orgs F | select | extract F | bank F | bank-reduce |" \
      "reduce | forget | clean F L (see the header)"
    ;;
esac
