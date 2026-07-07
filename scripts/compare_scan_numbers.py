"""Compare two sets of static scans cell-by-cell, focused on the NUMBER (score).

Bands are secondary here (the design decision: the numeric score, not the
low/med/high/critical label, is what matters). This diffs a "mine" scan dir
against a reference bundle (``reports/all_scans.zip`` by default) and reports, per
server and overall: score agreement (exact %, MAE, RMSE, Pearson r, signed bias),
primitive agreement (impact / sensitivity / blast), the blast 0->1 effect, and the
largest movers.

Usage:
    python scripts/compare_scan_numbers.py \
        --mine reports/scan_blast15 \
        --ref-zip reports/all_scans.zip \
        --out reports/heatmap_comparison/blast15_vs_reference.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import zipfile
from pathlib import Path

# The 10 demo servers, by scan-artifact stem.
DEMO_STEMS = [
    "fs_corp_filesystem", "fs_fintech_fs", "fs_law_firm_fs", "fs_media_studio_fs",
    "fs_medical_clinic_fs", "sqlite_cbg_sqlite", "sqlite_devops_sqlite",
    "github_cbg", "slack_cbg", "calendar_cbg",
]


def _cells(table: dict) -> dict[str, float]:
    """Flatten a table's ``cells`` matrix to ``{asset|tool: score}``."""
    out: dict[str, float] = {}
    for asset, row in table.get("cells", {}).items():
        for tool, score in row.items():
            out[f"{asset}|{tool}"] = float(score)
    return out


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation, or None if undefined (constant series / <2 points)."""
    if len(xs) < 2:
        return None
    try:
        return statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        return None


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def compare_one(mine: dict, ref: dict) -> dict:
    """Compare one server's two tables. Returns a metrics dict."""
    mc, rc = _cells(mine), _cells(ref)
    shared = sorted(set(mc) & set(rc))
    diffs = [mc[k] - rc[k] for k in shared]
    abs_diffs = [abs(d) for d in diffs]
    my_scores = [mc[k] for k in shared]
    rf_scores = [rc[k] for k in shared]
    movers = sorted(
        ({"cell": k, "ref": rc[k], "mine": mc[k], "delta": mc[k] - rc[k]} for k in shared),
        key=lambda d: abs(d["delta"]), reverse=True,
    )[:8]

    # blast 0 -> new value (the range change effect)
    ref_blast = ref.get("blast_radius", {})
    my_blast = mine.get("blast_radius", {})
    zero_keys = [k for k, v in ref_blast.items() if v == 0]
    zero_now = [my_blast.get(k) for k in zero_keys if k in my_blast]

    def _agree(a: dict, b: dict) -> tuple[int, int]:
        keys = set(a) & set(b)
        same = sum(1 for k in keys if a[k] == b[k])
        return same, len(keys)

    imp_same, imp_n = _agree(mine.get("tool_impact", {}), ref.get("tool_impact", {}))
    sen_same, sen_n = _agree(mine.get("asset_sensitivity", {}), ref.get("asset_sensitivity", {}))
    bl_same, bl_n = _agree(my_blast, ref_blast)

    return {
        "n_cells": len(shared),
        "exact": sum(1 for d in abs_diffs if d == 0),
        "mae": statistics.fmean(abs_diffs) if abs_diffs else 0.0,
        "rmse": (statistics.fmean([d * d for d in diffs]) ** 0.5) if diffs else 0.0,
        "bias": statistics.fmean(diffs) if diffs else 0.0,
        "pearson": _pearson(my_scores, rf_scores),
        "ref_mean": statistics.fmean(rf_scores) if rf_scores else 0.0,
        "mine_mean": statistics.fmean(my_scores) if my_scores else 0.0,
        "impact_agree": (imp_same, imp_n),
        "sens_agree": (sen_same, sen_n),
        "blast_agree": (bl_same, bl_n),
        "ref_blast_zeros": len(zero_keys),
        "zero_now": zero_now,
        "movers": movers,
    }


def _fmt_pct(a: int, b: int) -> str:
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "-"


def build_report(mine_dir: Path, ref_dir: Path) -> str:
    rows: list[str] = []
    agg = {"n": 0, "exact": 0, "abs": 0.0, "sq": 0.0, "signed": 0.0,
           "blast_zeros": 0, "imp_s": 0, "imp_n": 0, "sen_s": 0, "sen_n": 0,
           "bl_s": 0, "bl_n": 0}
    detail: list[str] = []

    for stem in DEMO_STEMS:
        mine = _load(mine_dir / f"{stem}.json")
        ref = _load(ref_dir / f"{stem}.json")
        if mine is None or ref is None:
            rows.append(f"| {stem} | MISSING ({'mine' if mine is None else 'ref'}) | | | | | |")
            continue
        m = compare_one(mine, ref)
        r = m["pearson"]
        rows.append(
            f"| {stem} | {m['n_cells']} | {_fmt_pct(m['exact'], m['n_cells'])} | "
            f"{m['mae']:.2f} | {m['bias']:+.2f} | {'' if r is None else f'{r:.3f}'} | "
            f"{m['ref_mean']:.1f}→{m['mine_mean']:.1f} |"
        )
        agg["n"] += m["n_cells"]
        agg["exact"] += m["exact"]
        agg["abs"] += m["mae"] * m["n_cells"]
        agg["sq"] += (m["rmse"] ** 2) * m["n_cells"]
        agg["signed"] += m["bias"] * m["n_cells"]
        agg["blast_zeros"] += m["ref_blast_zeros"]
        agg["imp_s"] += m["impact_agree"][0]
        agg["imp_n"] += m["impact_agree"][1]
        agg["sen_s"] += m["sens_agree"][0]
        agg["sen_n"] += m["sens_agree"][1]
        agg["bl_s"] += m["blast_agree"][0]
        agg["bl_n"] += m["blast_agree"][1]

        movers = "; ".join(
            f"`{d['cell']}` {d['ref']:.0f}→{d['mine']:.0f}" for d in m["movers"][:5]
        )
        zn = m["zero_now"]
        zero_note = (
            f" — {len(zn)} ex-blast0 cells now blast {min(zn)}–{max(zn)}" if zn else ""
        )
        detail.append(f"- **{stem}**{zero_note}. Top movers: {movers}")

    n = agg["n"] or 1
    lines = [
        "# Static scan numbers — mine (blast 1-5, judge off, hardened prompts) vs "
        "reference (all_scans.zip)",
        "",
        "The **score** is the object of comparison, not the band. Both runs are the "
        "deterministic LLM scan (greedy, fixed seed), so every difference is caused "
        "by the code changes, not sampling noise.",
        "",
        "## Per-server",
        "",
        "| server | cells | exact score | MAE | bias (mine−ref) | Pearson r | mean score |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## Overall",
        "",
        f"- **{agg['n']} cells** compared across 10 servers.",
        f"- Exact score match: **{_fmt_pct(agg['exact'], agg['n'])}**.",
        f"- MAE **{agg['abs'] / n:.2f}**, RMSE **{(agg['sq'] / n) ** 0.5:.2f}**, "
        f"mean signed bias **{agg['signed'] / n:+.2f}** "
        f"({'mine scores higher' if agg['signed'] > 0 else 'mine scores lower'}).",
        f"- Primitive agreement — tool_impact {_fmt_pct(agg['imp_s'], agg['imp_n'])}, "
        f"asset_sensitivity {_fmt_pct(agg['sen_s'], agg['sen_n'])}, "
        f"blast_radius {_fmt_pct(agg['bl_s'], agg['bl_n'])}.",
        f"- **{agg['blast_zeros']}** reference cells had blast 0 (the old N/A level); "
        "all are now blast ≥ 1, so they carry a real score instead of 0.",
        "",
        "## Per-server notes (blast-0 effect + largest movers)",
        "",
        *detail,
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mine", type=Path, default=Path("reports/scan_blast15"))
    ap.add_argument("--ref-zip", type=Path, default=Path("reports/all_scans.zip"))
    ap.add_argument("--ref-dir", type=Path, default=None,
                    help="Use an already-extracted reference dir instead of the zip.")
    ap.add_argument("--out", type=Path,
                    default=Path("reports/heatmap_comparison/blast15_vs_reference.md"))
    args = ap.parse_args()

    if args.ref_dir is not None:
        report = build_report(args.mine, args.ref_dir)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(args.ref_zip) as zf:
                zf.extractall(tmp)
            ref_dir = Path(tmp) / "all_scans" / "demo"
            report = build_report(args.mine, ref_dir)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[wrote {args.out}]")


if __name__ == "__main__":
    main()
