"""Sensitivity analysis of the risk formula's band cut-points.

The static score is multiplicative and fixed: ``score = sensitivity * blast *
impact`` (likelihood pinned to 1.0), and the documented policy
(:func:`mcp_security.static_scoring.pipeline.band_label`) turns it into a band via
fixed cut-points (``medium>=8``, ``high>=24``) plus crown-jewel rules. A fair
question for any such cut-point scheme: **how stable is the band if an input is off
by one?** The LLM estimates sensitivity (1-5), blast (0-4) and impact (1-3); each
is an ordinal judgement that could reasonably move by ±1.

This script re-derives every scanned cell's inputs, then for each cell perturbs one
input at a time by ±1 (within its valid range) and recomputes the policy band. It
reports, per scan and overall:

* **stable** cells — the band is unchanged under every single ±1 perturbation;
* **fragile** cells — at least one ±1 perturbation flips the band (these are the
  cells a gate's behaviour hinges on, and where rater disagreement bites hardest);
* **boundary** cells — whose raw score sits within a margin of a numeric cut-point.

It reads the published scans only; no model and no ground truth are involved.

Run:  python scripts/formula_sensitivity.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import BAND_THRESHOLDS, band_label

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "formula_sensitivity.md"

# Valid ranges for each formula input (see the scoring pipeline).
_RANGES = {"sensitivity": (1, 5), "blast": (0, 4), "impact": (1, 3)}
# A cell is a "boundary" cell if its score is within this margin of a cut-point.
_BOUNDARY_MARGIN = 4


def _scan_files() -> list[Path]:
    return [p for p in sorted(SCAN_DIR.glob("*.json")) if not p.stem.endswith("_params")]


def _perturbations(sens: int, blast: int, impact: int) -> list[tuple[str, int, int, int, int]]:
    """All single-input ±1 perturbations within range: (label, ds, db, di, signed)."""
    out: list[tuple[str, int, int, int, int]] = []
    base = {"sensitivity": sens, "blast": blast, "impact": impact}
    for name, (lo, hi) in _RANGES.items():
        for delta in (-1, 1):
            val = base[name] + delta
            if lo <= val <= hi:
                pert = dict(base)
                pert[name] = val
                out.append((f"{name}{delta:+d}", pert["sensitivity"], pert["blast"],
                            pert["impact"], delta))
    return out


def _is_boundary(score: float) -> bool:
    return any(abs(score - thr) <= _BOUNDARY_MARGIN for thr in BAND_THRESHOLDS.values())


def _analyse_scan(path: Path) -> dict:
    """Per-cell stability of the policy band under ±1 input perturbations."""
    data = json.loads(path.read_text("utf-8"))
    sens, impact, blast = (data["asset_sensitivity"], data["tool_impact"], data["blast_radius"])
    n = stable = fragile = boundary = 0
    fragile_cells: list[dict] = []
    for asset, row in data["cells"].items():
        for tool in row:
            bl = blast.get(f"{tool}|{asset}")
            if bl is None:
                continue
            s, b, i = sens[asset], bl, impact[tool]
            score = s * b * i
            nominal = band_label(s, b, i)
            flips = {
                label: band_label(ps, pb, pi)
                for label, ps, pb, pi, _ in _perturbations(s, b, i)
                if band_label(ps, pb, pi) != nominal
            }
            n += 1
            if _is_boundary(score):
                boundary += 1
            if flips:
                fragile += 1
                fragile_cells.append({"cell": f"{tool} × {asset}", "band": nominal,
                                      "score": score, "flips": flips})
            else:
                stable += 1
    return {"scan": path.stem, "n": n, "stable": stable, "fragile": fragile,
            "boundary": boundary, "fragile_cells": fragile_cells}


def _pct(part: int, whole: int) -> str:
    return f"{part}/{whole} ({100*part/whole:.0f}%)" if whole else "0/0"


def to_markdown(reports: list[dict]) -> str:
    total = {k: sum(r[k] for r in reports) for k in ("n", "stable", "fragile", "boundary")}
    lines = [
        "# Formula sensitivity (band cut-point robustness)",
        "",
        "`score = sensitivity × blast × impact`, banded by fixed cut-points "
        f"(medium ≥ {BAND_THRESHOLDS['medium']}, high ≥ {BAND_THRESHOLDS['high']}) plus "
        "crown-jewel rules. Each scanned cell's inputs are perturbed by ±1 (one at a "
        "time, within range); a cell is **fragile** if any such perturbation flips its "
        "band, **boundary** if its score is within "
        f"{_BOUNDARY_MARGIN} of a cut-point.",
        "",
        f"**Overall:** {total['n']} cells · stable {_pct(total['stable'], total['n'])} · "
        f"fragile {_pct(total['fragile'], total['n'])} · "
        f"boundary {_pct(total['boundary'], total['n'])}",
        "",
        "| Scan | cells | stable | fragile | boundary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in reports:
        lines.append(f"| {r['scan']} | {r['n']} | {_pct(r['stable'], r['n'])} | "
                     f"{_pct(r['fragile'], r['n'])} | {_pct(r['boundary'], r['n'])} |")
    # Show the most fragile cells (those that flip), capped, for inspection.
    flips = [c for r in reports for c in r["fragile_cells"]]
    flips.sort(key=lambda c: (-len(c["flips"]), c["cell"]))
    if flips:
        lines += ["", "## Most fragile cells (band flips under a ±1 input change)", "",
                  "| cell | band | score | flips to |", "| --- | --- | --- | --- |"]
        for c in flips[:25]:
            flip_str = ", ".join(f"{k}→{v}" for k, v in sorted(c["flips"].items()))
            lines.append(f"| `{c['cell']}` | {c['band']} | {c['score']:g} | {flip_str} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-dir", type=Path, default=SCAN_DIR)
    args = parser.parse_args()
    files = [p for p in sorted(args.scan_dir.glob("*.json")) if not p.stem.endswith("_params")]
    reports = [_analyse_scan(p) for p in files]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    md = to_markdown(reports)
    OUT_MD.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
