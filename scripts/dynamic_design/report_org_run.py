"""Report what the runtime does on a realistic corpus, and how much of it is noise.

Three questions, in the order they have to be answered:

1. Does the corpus have a tail at all? A uniform corpus cannot exercise ``L``, so the
   distribution is reported before any score is.
2. Is the score reproducible? Byte-identical calls scored at different points in the
   stream reveal how much of the range is warm-up drift rather than signal. That spread
   is the noise floor, and no ranking narrower than it means anything.
3. Does the score track anything a reader would call risk? The org model makes rare tools
   mostly administrative, so read/write is an independent label to compare against.
"""

from __future__ import annotations

import argparse
import collections
import csv
import itertools
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dynamic_v2 import BreadthScorer, load_specs  # noqa: E402
from org_traffic import write_tools  # noqa: E402

REPO = Path("/home/ovadyat/MCP")
#: Fraction of the corpus used to warm quartiles and tool counts before scoring begins.
WARM_FRACTION = 0.5


def _load(path: Path) -> list[dict]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def _args(row: dict) -> dict:
    try:
        parsed = json.loads(row["args"] or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _quantile(values: list[float], pct: int) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, pct * len(ordered) // 100)]


def describe_corpus(rows: list[dict], server: str) -> None:
    """The call mix, before anything is scored."""
    tools = collections.Counter(r["tool"] for r in rows)
    total = sum(tools.values())
    ranked = tools.most_common()
    print(f"\n{len(rows):,} calls, {len(tools)} distinct tools")
    print(f"  head {ranked[0][0]} {ranked[0][1] / total:.2%}   "
          f"tail {ranked[-1][0]} {ranked[-1][1] / total:.2%}   "
          f"ratio {ranked[0][1] / ranked[-1][1]:.0f}x")
    writes = sum(c for t, c in tools.items() if t in write_tools(server))
    print(f"  writes {writes / total:.1%} of volume")


def score(rows: list[dict], server: str) -> list[dict]:
    """Warm on the first half, score the second, keeping each call's factors."""
    scorer = BreadthScorer(load_specs())
    split = int(len(rows) * WARM_FRACTION)
    for row in rows[:split]:
        scorer.observe(server, row["tool"], _args(row))

    writes = write_tools(server)
    scored: list[dict] = []
    for row in rows[split:]:
        args = _args(row)
        value, reasons = scorer.score(server, row["tool"], args)
        breadth, _ = scorer.breadth_factor(server, row["tool"], args)
        likelihood, _ = scorer.likelihood_factor(server, row["tool"])
        scorer.observe(server, row["tool"], args)
        scored.append({"tool": row["tool"], "args": row["args"], "D": value,
                       "B": breadth, "L": likelihood,
                       "write": row["tool"] in writes, "why": "; ".join(reasons)})
    return scored


def report_spread(scored: list[dict]) -> float:
    """Overall shape, and the noise floor measured from repeated identical calls."""
    values = [s["D"] for s in scored]
    span = max(values) - min(values)
    print(f"\nD over {len(values):,} scored calls")
    print(f"  min {min(values):.3f}  p25 {_quantile(values, 25):.3f}  "
          f"median {st.median(values):.3f}  p75 {_quantile(values, 75):.3f}  "
          f"max {max(values):.3f}")
    for label, key in (("B", "B"), ("L", "L")):
        column = [s[key] for s in scored]
        moved = sum(abs(v - 1.0) > 1e-9 for v in column)
        print(f"  {label}: min {min(column):.3f}  median {st.median(column):.3f}  "
              f"max {max(column):.3f}   fires on {moved / len(column):.1%} of calls")

    groups = collections.defaultdict(list)
    for s in scored:
        groups[(s["tool"], s["args"])].append(s["D"])
    repeats = {k: v for k, v in groups.items() if len(v) >= 5}
    if not repeats:
        print("  no repeated calls: noise floor not measurable")
        return 0.0
    spreads = [max(v) - min(v) for v in repeats.values()]
    worst_key, worst = max(repeats.items(), key=lambda kv: max(kv[1]) - min(kv[1]))
    # The floor is a p95, not the maximum. A maximum over N groups is an extreme-value
    # statistic that grows with N on its own, so it would report a corpus 100x larger as
    # 17x noisier purely for having more chances to throw an outlier.
    floor = _quantile(spreads, 95)
    print(f"\nnoise floor, from {len(repeats)} byte-identical repeated calls")
    print(f"  median spread {st.median(spreads):.3f}   p95 {floor:.3f}"
          f"   = {floor / span * 100:.0f}% of the whole range")
    print(f"  single worst (an outlier, not the floor): {worst_key[0]} n={len(worst)} "
          f"D {min(worst):.3f}..{max(worst):.3f}")
    return floor


def report_by_tool(scored: list[dict], floor: float) -> None:
    """Per-tool medians, with the rare and the state-changing marked."""
    by_tool = collections.defaultdict(list)
    for s in scored:
        by_tool[s["tool"]].append(s)
    print(f"\n{'tool':32} {'n':>6} {'D med':>7} {'L':>6} {'B med':>7}  kind")
    for tool, group in sorted(by_tool.items(), key=lambda kv: -st.median(
            [s["D"] for s in kv[1]])):
        ds = [s["D"] for s in group]
        mark = "write" if group[0]["write"] else "read"
        print(f"{tool:32} {len(group):6} {st.median(ds):7.3f} {group[0]['L']:6.3f} "
              f"{st.median([s['B'] for s in group]):7.3f}  {mark}")
    print(f"\n(noise floor {floor:.3f}: any two tools closer than this are not "
          f"distinguishable)")


def report_risk_alignment(scored: list[dict], floor: float) -> None:
    """Does the score separate state-changing calls from reads?"""
    writes = [s["D"] for s in scored if s["write"]]
    reads = [s["D"] for s in scored if not s["write"]]
    if not writes:
        print("\nno write calls in the scored half")
        return
    print("\nwrite vs read, on D")
    print(f"  writes n={len(writes):,} median {st.median(writes):.3f}")
    print(f"  reads  n={len(reads):,} median {st.median(reads):.3f}")
    gap = st.median(writes) - st.median(reads)
    verdict = "above the noise floor" if abs(gap) > floor else "INSIDE the noise floor"
    print(f"  gap {gap:+.3f}  ({verdict})")

    pairs = list(itertools.product(writes[:400], reads[:400]))
    higher = sum(w > r for w, r in pairs)
    ties = sum(w == r for w, r in pairs)
    print(f"  P(write scores above read) = {(higher + 0.5 * ties) / len(pairs):.3f}"
          f"   (0.5 = no separation)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--server", default="github")
    args = parser.parse_args(argv)

    rows = _load(args.corpus)
    print("=" * 78)
    print(args.corpus.name)
    print("=" * 78)
    describe_corpus(rows, args.server)
    scored = score(rows, args.server)
    floor = report_spread(scored)
    report_by_tool(scored, floor)
    report_risk_alignment(scored, floor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
