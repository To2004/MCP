"""Cold-start to warm-start sweep for the weight-by-rank runtime factor (dynamic_v2.py).

`dynamic_v2.BreadthScorer` weights each argument's deviation by `BREADTH_WEIGHT`, the
scan's 1-5 breadth/centrality RANK for that argument, relative to its tool's most
central measurable argument (`_relative_weight`). Below `MIN_HISTORY` (20) observations
of an argument, `B` abstains at exactly 1.0 -- "no history" -- rather than grading
against a reference that does not exist yet. This script asks: how much warm-up does
that rank-weighted reference actually need before it stops abstaining and settles down?

Same idea as `reports/experiments/dynamic_layer/v3/warmup_curve.txt` (which measured
`L`'s cold-start behaviour), extended to `B` -- the factor `BREADTH_WEIGHT` actually
feeds -- and swept over a wider range of warm-up sizes using the 100k-row synthetic
org corpora already on disk (`reports/experiments/real_benign/*_org_100k.csv`).

Methodology: reserve a FIXED test tail (the corpus's last `--test-size` rows, same rows
scored at every warm-up length, so what changes between rows is only how much history
the scorer had, never which calls it was asked to judge). Warm the scorer on the first
N rows of what remains for each N in `--warmup-sizes`, then score the fixed tail and
report the D distribution and, critically, `scorer.sources` -- what FRACTION of scored
quantities were still abstaining ("no history"/"no floor") vs actually graded
("ordinary"/"narrow"/"wide") at each warm-up size. That fraction, not the D distribution
alone, is the honest cold-start signature: a scorer that abstains on 95% of quantities
and one that grades 95% of them can show a similar-looking median D of ~1.0.

    python3 scripts/dynamic_design/warmup_sweep.py --server github_helios
    python3 scripts/dynamic_design/warmup_sweep.py --server calendar_aurora --warmup-sizes 0 50 500 5000 50000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dynamic_v2 import ORG_TO_SERVER, MIN_HISTORY, BreadthScorer, load_specs  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO / "reports" / "experiments" / "real_benign"
DEFAULT_WARMUP_SIZES = (0, 20, 100, 500, 2_000, 10_000, 50_000, 94_000)
DEFAULT_TEST_SIZE = 5_000


def _read_rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open()))


def _parse_args(row: dict) -> dict | None:
    try:
        parsed = json.loads(row.get("args") or "{}")
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _feed(scorer: BreadthScorer, server: str, rows: list[dict]) -> None:
    for row in rows:
        args = _parse_args(row)
        if args is not None:
            scorer.observe(server, row["tool"], args)


def _score(scorer: BreadthScorer, server: str, rows: list[dict]) -> list[float]:
    out = []
    for row in rows:
        args = _parse_args(row)
        if args is None:
            continue
        d, _reasons = scorer.score(server, row["tool"], args)
        out.append(d)
    return out


def summarise(label: str, values: list[float]) -> str:
    if not values:
        return f"{label:<10}  (no scored rows)"
    v = sorted(values)
    n = len(v)
    return (f"{label:<10}{n:>7}{v[0]:>7.2f}{v[n // 4]:>7.2f}{v[n // 2]:>8.2f}"
            f"{v[3 * n // 4]:>7.2f}{v[-1]:>7.2f}"
            f"{sum(1 for x in v if x < 0.999) / n:>7.0%}"
            f"{sum(1 for x in v if x > 1.001) / n:>7.0%}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, choices=sorted(ORG_TO_SERVER))
    parser.add_argument("--corpus", type=Path, default=None,
                        help=f"default: {CORPUS_DIR}/<server>_org_100k.csv")
    parser.add_argument("--warmup-sizes", type=int, nargs="*", default=list(DEFAULT_WARMUP_SIZES))
    parser.add_argument("--test-size", type=int, default=DEFAULT_TEST_SIZE)
    args = parser.parse_args(argv)

    corpus_path = args.corpus or CORPUS_DIR / f"{args.server}_org_100k.csv"
    if not corpus_path.exists():
        print(f"[FAIL] no corpus at {corpus_path}")
        return 1
    server_key = ORG_TO_SERVER[args.server]
    specs = load_specs()
    if server_key not in specs:
        print(f"[FAIL] no tool_breadth spec for server {server_key!r} -- "
              f"scan artifact missing from {REPO}/reports/experiments/breadth_spec/")
        return 1

    rows = _read_rows(corpus_path)
    if len(rows) <= args.test_size:
        print(f"[FAIL] corpus has {len(rows)} rows, need more than --test-size={args.test_size}")
        return 1
    test_rows = rows[-args.test_size:]
    pool = rows[:-args.test_size]  # warm-up is drawn from here, in arrival order

    print(f"server={args.server}  corpus={corpus_path.name}  "
          f"pool={len(pool)} rows  fixed test tail={len(test_rows)} rows\n")
    print(f"{'warmup':<10}{'n':>7}{'min':>7}{'p25':>7}{'median':>8}{'p75':>7}{'max':>7}"
          f"{'<1.0':>8}{'>1.0':>8}   sources (no_hist/no_floor/ordinary/narrow/wide)")

    for n in sorted(args.warmup_sizes):
        if n > len(pool):
            print(f"{n:<10}  (skipped -- pool only has {len(pool)} rows)")
            continue
        scorer = BreadthScorer(specs)
        _feed(scorer, server_key, pool[:n])
        values = _score(scorer, server_key, test_rows)
        src = scorer.sources
        total_src = sum(src.values()) or 1
        src_str = "/".join(
            f"{src.get(k, 0)}" for k in
            ("no history", "no floor", "ordinary", "narrow", "wide")
        )
        abstain_pct = (src.get("no history", 0) + src.get("no floor", 0)) / total_src
        print(summarise(str(n), values) + f"   {src_str}   (abstain {abstain_pct:.0%})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
