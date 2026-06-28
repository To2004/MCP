"""Head-to-head: grade every risk scorer against the human oracle on one surface.

``evaluate_vs_human.py`` folds the framework baselines into a *consensus* and grades
only the scanner against it. That answers "is the scanner near the panel?" but not
the question a reviewer asks: **how does the Qwen scanner compare, scorer-for-scorer,
to the classical frameworks (CVSS, DREAD, OWASP, NIST, MAESTRO) and a generic LLM?**

This script grades each scorer's per-(asset, tool) bands against the *human* oracle
(``risk_ranking_filesystemMCP.xlsx`` / ``mcp_sqlite_risk_rankings.xlsx``) on the
shared cell surface, reporting not just exact/within-one agreement but chance- and
magnitude-corrected ordinal metrics (quadratic-weighted kappa, MAE, Spearman) with
Wilson confidence intervals, plus each scorer's **over-block rate** (share of cells it
rates high|critical). The story: the classical frameworks over-block; the Qwen scanner
tracks the human oracle more closely. Nothing here calls an LLM — every band is read
from an already-computed artifact, so the comparison is deterministic.

Run:  uv run python scripts/compare_scorers.py
"""

from __future__ import annotations

import json
from pathlib import Path

import eval_metrics as m
from evaluate_vs_human import (
    BASELINES,
    FS_TOOL_MAP,
    HEATMAPS,
    SQLITE_TOOL_MAP,
    _EXCLUDE_RATER_DIRS,
    _RATER_GLOBS,
    _read_heatmap,
    _scanner_cells,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "scorer_comparison.md"
OUT_JSON = REPO_ROOT / "reports" / "evaluation" / "scorer_comparison.json"

SCANNER_LABEL = "scanner (Qwen)"
FS_SCAN_STEMS = ["fs_corp_filesystem", "fs_law_firm_fs", "fs_media_studio_fs", "fs_medical_clinic_fs"]
SQLITE_SCAN_STEMS = ["sqlite_cbg_sqlite"]


def _baseline_label(path: Path) -> str:
    """Short scorer name for a baseline workbook (method dir, +variant if any)."""
    method = path.parent.name
    stem = path.stem.lower()
    for variant in ("plain", "security"):
        if variant in stem:
            return f"{method}:{variant}"
    return method


def _baseline_cells(kind: str) -> dict[str, dict[tuple[str, str], str]]:
    """Every baseline scorer's cells for ``kind``: {label: {(asset, tool): band}}."""
    _, glob = _RATER_GLOBS[kind]
    out: dict[str, dict[tuple[str, str], str]] = {}
    for path in sorted(BASELINES.glob(f"*/{glob}")):
        if path.parent.name in _EXCLUDE_RATER_DIRS:
            continue
        out[_baseline_label(path)] = _read_heatmap(path, key_cols=2)
    return out


def _aligned_ranks(
    scorer: dict[tuple[str, str], str], oracle: dict[tuple[str, str], str]
) -> tuple[list[int], list[int], list[str]]:
    """Aligned 1..4 rank lists over cells both scorer and oracle cover."""
    shared = sorted(set(scorer) & set(oracle))
    sa = [m.BAND_RANK[scorer[k]] for k in shared]
    oa = [m.BAND_RANK[oracle[k]] for k in shared]
    return sa, oa, [scorer[k] for k in shared]


def _score(scorer: dict[tuple[str, str], str], oracle: dict[tuple[str, str], str]) -> dict:
    """All metrics for one scorer vs the oracle on their shared cells."""
    sa, oa, scorer_bands = _aligned_ranks(scorer, oracle)
    n = len(sa)
    exact = sum(1 for x, y in zip(sa, oa) if x == y)
    within1 = sum(1 for x, y in zip(sa, oa) if abs(x - y) <= 1)
    dist = m.band_distribution(scorer_bands)
    return {
        "n": n,
        "exact": exact,
        "within1": within1,
        "exact_pct": exact / n if n else None,
        "within1_pct": within1 / n if n else None,
        "exact_ci": m.wilson_ci(exact, n),
        "within1_ci": m.wilson_ci(within1, n),
        "qwk": m.quadratic_weighted_kappa(sa, oa),
        "mae": m.ordinal_mae(sa, oa),
        "spearman": m.spearman_rho(sa, oa),
        "over_block": dist["over_block"],
    }


def _collect(kind: str) -> tuple[dict[str, dict], dict[str, tuple[list[int], list[int]]]]:
    """Per-scorer metrics for one kind, plus the raw aligned ranks for pooling."""
    primary_name = _RATER_GLOBS[kind][0]
    oracle = _read_heatmap(HEATMAPS / primary_name, key_cols=2)
    if kind == "filesystem":
        scanner = _scanner_cells(FS_SCAN_STEMS, FS_TOOL_MAP, by_table=False)
    else:
        scanner = _scanner_cells(SQLITE_SCAN_STEMS, SQLITE_TOOL_MAP, by_table=True)

    scorers = {SCANNER_LABEL: scanner, **_baseline_cells(kind)}
    metrics: dict[str, dict] = {}
    ranks: dict[str, tuple[list[int], list[int]]] = {}
    for label, cells in scorers.items():
        metrics[label] = _score(cells, oracle)
        sa, oa, _ = _aligned_ranks(cells, oracle)
        ranks[label] = (sa, oa)
    return metrics, ranks


def _fmt(x: float | None, pct: bool = False) -> str:
    if x is None:
        return "—"
    return f"{100 * x:.0f}%" if pct else f"{x:+.2f}"


def _table(title: str, metrics: dict[str, dict]) -> str:
    lines = [f"### {title}", "",
             "| scorer | cells | exact | within-1 | QW-κ | MAE | Spearman | over-block |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    # Scanner first, then baselines by descending QW-kappa (best agreement on top).
    others = sorted(
        (k for k in metrics if k != SCANNER_LABEL),
        key=lambda k: (metrics[k]["qwk"] if metrics[k]["qwk"] is not None else -9),
        reverse=True,
    )
    for label in [SCANNER_LABEL, *others]:
        r = metrics[label]
        lo, hi = r["exact_ci"]
        bold = "**" if label == SCANNER_LABEL else ""
        lines.append(
            f"| {bold}{label}{bold} | {r['n']} | "
            f"{_fmt(r['exact_pct'], pct=True)} "
            f"[{100*lo:.0f}–{100*hi:.0f}] | "
            f"{_fmt(r['within1_pct'], pct=True)} | "
            f"{_fmt(r['qwk'])} | {_fmt(r['mae'])} | {_fmt(r['spearman'])} | "
            f"{_fmt(r['over_block'], pct=True)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    by_kind = {}
    pooled_ranks: dict[str, tuple[list[int], list[int]]] = {}
    for kind in ("filesystem", "sqlite"):
        metrics, ranks = _collect(kind)
        by_kind[kind] = metrics
        for label, (sa, oa) in ranks.items():
            psa, poa = pooled_ranks.setdefault(label, ([], []))
            psa.extend(sa)
            poa.extend(oa)

    # Overall row per scorer from the pooled fs+sqlite rank pairs.
    overall: dict[str, dict] = {}
    for label, (sa, oa) in pooled_ranks.items():
        n = len(sa)
        exact = sum(1 for x, y in zip(sa, oa) if x == y)
        within1 = sum(1 for x, y in zip(sa, oa) if abs(x - y) <= 1)
        bands = [m.BANDS[r - 1] for r in sa]
        overall[label] = {
            "n": n, "exact": exact, "within1": within1,
            "exact_pct": exact / n if n else None,
            "within1_pct": within1 / n if n else None,
            "exact_ci": m.wilson_ci(exact, n),
            "within1_ci": m.wilson_ci(within1, n),
            "qwk": m.quadratic_weighted_kappa(sa, oa),
            "mae": m.ordinal_mae(sa, oa),
            "spearman": m.spearman_rho(sa, oa),
            "over_block": m.band_distribution(bands)["over_block"],
        }

    out = [
        "# Scorer head-to-head vs. the human oracle", "",
        "Each scorer's per-(asset, tool) risk bands are graded against the hand-authored "
        "human heatmap on the shared cell surface (filetype × tool for filesystem, "
        "table × tool for SQLite). Metrics: exact band agreement (Wilson 95% CI), "
        "within-one-band, quadratic-weighted Cohen's κ (chance- and magnitude-corrected), "
        "mean absolute band error (MAE), Spearman ρ, and **over-block** = share of cells the "
        "scorer rates high or critical. Higher κ / lower MAE = closer to the human; a high "
        "over-block with low κ is a scorer that defends by rating almost everything dangerous. "
        "No LLM is called here — every band is read from a precomputed artifact.", "",
        _table("Overall (filesystem + SQLite pooled)", overall),
        _table("Filesystem (filetype × tool)", by_kind["filesystem"]),
        _table("SQLite (table × tool)", by_kind["sqlite"]),
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"overall": overall, "by_kind": by_kind}, indent=2, default=list),
        encoding="utf-8",
    )
    print("\n".join(out))
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)} and {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
