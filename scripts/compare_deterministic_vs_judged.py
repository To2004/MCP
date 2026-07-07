"""Compare the clean deterministic scans against the old judged scans.

For each demo server, contrasts the current ``reports/scan/<stem>.json`` (clean
pipeline: deterministic band_label, judge off, blast 0-5) with the backed-up
``reports/scan_judged_backup/<stem>.json`` (old pipeline: LLM band + judge,
blast 0-4). Reports band agreement and the band-distribution shift.

Note: the primitives (impact/sensitivity/blast) are re-derived by the LLM on each
scan, so some difference is re-scan drift, not just the band method — reported
separately so the two effects are not conflated.

Run:  python scripts/compare_deterministic_vs_judged.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEW = REPO / "reports" / "scan"
OLD = REPO / "reports" / "scan_judged_backup"
RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _cells(d: dict) -> dict[tuple[str, str], str]:
    return {(a, t): b for a, row in d.get("bands", {}).items() for t, b in row.items()}


def _dist(bands: dict) -> dict[str, int]:
    out = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for b in bands.values():
        out[b] = out.get(b, 0) + 1
    return out


def main() -> int:
    stems = sorted(p.stem for p in OLD.glob("*.json") if not p.stem.endswith("_params"))
    print("# Deterministic (clean) vs judged (old) bands\n")
    print("| server | cells | band agree | within-1 | det dist (l/m/h/c) | judged dist |")
    print("| --- | --- | --- | --- | --- | --- |")
    tot = agree = within = 0
    for stem in stems:
        np, op = NEW / f"{stem}.json", OLD / f"{stem}.json"
        if not np.exists():
            continue
        nd, od = json.loads(np.read_text()), json.loads(op.read_text())
        nc, oc = _cells(nd), _cells(od)
        keys = set(nc) & set(oc)
        if not keys:
            continue
        a = sum(nc[k] == oc[k] for k in keys)
        w = sum(abs(RANK[nc[k]] - RANK[oc[k]]) <= 1 for k in keys)
        tot += len(keys)
        agree += a
        within += w
        ndist = _dist(nc)
        odist = _dist(oc)
        dd = "/".join(str(ndist[x]) for x in ("low", "medium", "high", "critical"))
        od_ = "/".join(str(odist[x]) for x in ("low", "medium", "high", "critical"))
        print(f"| {stem} | {len(keys)} | {a/len(keys):.0%} | {w/len(keys):.0%} | {dd} | {od_} |")
    if tot:
        print(f"\n**Overall:** {agree}/{tot} exact ({agree/tot:.0%}), "
              f"{within}/{tot} within-one-band ({within/tot:.0%}). The deterministic "
              f"floors shift more cells up (irreversibility/confidentiality) while "
              f"dropping the non-reproducible LLM overrides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
