"""Grade the scanner's output against the design-time evaluation ground truth.

The scanner derives its risk matrices live from the scanned tools/assets and must
never read the committed tables. This script closes the loop the other way: it
compares each scan artifact in ``reports/scan/`` to the corresponding ground-truth
table in ``reports/evaluation/raw/all_static_tables.json`` and reports how often
the scanner agrees — per cell band, per tool impact, per asset sensitivity.

It is purely an *evaluator*: it is never imported by the scanner or the ranker.

Run::

    python scripts/evaluate_scanner.py
    python scripts/evaluate_scanner.py --take2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
EVAL_RAW = REPO_ROOT / "reports" / "evaluation" / "raw"
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "scanner_accuracy.md"

# Scan-artifact stem prefixes -> stripped to match a ground-truth table name.
_PREFIXES = ("fs_", "sqlite_", "slack_")


def _gt_name(scan_stem: str) -> str:
    """Map a scan filename stem to its ground-truth table name."""
    for prefix in _PREFIXES:
        if scan_stem.startswith(prefix):
            return scan_stem[len(prefix) :]
    return scan_stem


def _agreement(scan_map: dict, gt_map: dict) -> tuple[int, int]:
    """Count (matches, compared) over the keys present in both maps."""
    shared = set(scan_map) & set(gt_map)
    matches = sum(1 for k in shared if scan_map[k] == gt_map[k])
    return matches, len(shared)


def _band_agreement(scan: dict, gt: dict) -> tuple[int, int]:
    """Count band matches across (asset, tool) cells present in both matrices."""
    matches = compared = 0
    scan_bands, gt_bands = scan.get("bands", {}), gt.get("bands", {})
    for asset in set(scan_bands) & set(gt_bands):
        for tool in set(scan_bands[asset]) & set(gt_bands[asset]):
            compared += 1
            matches += scan_bands[asset][tool] == gt_bands[asset][tool]
    return matches, compared


def _pct(matches: int, total: int) -> str:
    return f"{matches}/{total} ({100 * matches / total:.0f}%)" if total else "—"


def evaluate(scan_dir: Path, gt_path: Path) -> str:
    """Compare every scan against ground truth; return a markdown report."""
    if not scan_dir.exists() or not any(scan_dir.glob("*.json")):
        return (
            "# Scanner accuracy\n\nNo scan artifacts found in "
            f"`{scan_dir.relative_to(REPO_ROOT)}`. Run the scanner first "
            "(it is LLM-only — use `scripts/scan_and_rank_on_gpu.sbatch`).\n"
        )
    gt = json.loads(gt_path.read_text(encoding="utf-8"))["tables"]
    lines = [
        "# Scanner accuracy",
        "",
        f"Scans in `{scan_dir.relative_to(REPO_ROOT)}` vs ground truth "
        f"`{gt_path.relative_to(REPO_ROOT)}`. Higher agreement = the scanner "
        "reproduces the reviewed judgement without ever reading it.",
        "",
        "| Server | Band agreement | Tool-impact agreement | Asset-sensitivity agreement |",
        "| --- | --- | --- | --- |",
    ]
    totals = [0, 0, 0, 0, 0, 0]
    for scan_file in sorted(scan_dir.glob("*.json")):
        scan = json.loads(scan_file.read_text(encoding="utf-8"))
        name = _gt_name(scan_file.stem)
        if name not in gt:
            lines.append(f"| {scan_file.stem} | _no ground truth_ | — | — |")
            continue
        bm, bc = _band_agreement(scan, gt[name])
        tm, tc = _agreement(scan.get("tool_impact", {}), gt[name].get("tool_impact", {}))
        sm, sc = _agreement(scan.get("asset_sensitivity", {}), gt[name].get("asset_sensitivity", {}))
        totals = [totals[0] + bm, totals[1] + bc, totals[2] + tm,
                  totals[3] + tc, totals[4] + sm, totals[5] + sc]
        lines.append(f"| {name} | {_pct(bm, bc)} | {_pct(tm, tc)} | {_pct(sm, sc)} |")
    lines.append(
        f"| **overall** | **{_pct(totals[0], totals[1])}** | "
        f"**{_pct(totals[2], totals[3])}** | **{_pct(totals[4], totals[5])}** |"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-dir", type=Path, default=SCAN_DIR)
    parser.add_argument("--take2", action="store_true", help="grade against the take2 ground truth")
    parser.add_argument("--gt", type=Path, help="explicit ground-truth JSON")
    args = parser.parse_args()

    gt_path = args.gt or EVAL_RAW / (
        "all_static_tables_take2.json" if args.take2 else "all_static_tables.json"
    )
    report = evaluate(args.scan_dir, gt_path)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
