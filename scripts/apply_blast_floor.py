"""Experiment `blast_floor`: sensitivity-coupled minimum blast radius.

Motivation: under the coverage rubric a mutation of ONE item is blast 1, so a
destructive call on a sensitive asset (delete-event on a personal calendar,
write_file over an audit log) multiplies down to a low score even though its
tool impact is 4-5. This experiment counters that with a deterministic rule:
the more sensitive the asset, the higher the MINIMUM blast a scored cell may
carry — consequences on a sensitive asset are never "pinpoint".

Two variants are produced from the SAME baseline scan (no LLM re-run):

- ``plain`` — the rule as specified: sensitivity 5 -> min blast 4,
  sensitivity 4 -> min blast 3 (configurable via ``--sens4-floor``).
  Applied to every scored (non-N/A) cell.
- ``gated`` — same floors, but applied ONLY to mutating tools
  (tool_impact >= 4, i.e. write/modify and delete/destroy). Reads and
  metadata listings keep the model's coverage blast, so reconnaissance
  tools are not inflated alongside the mutations the rule targets.

N/A cells stay N/A; floors never LOWER a model blast. Scores and bands are
recomputed with the same formula and ``band_label`` as the baseline scan, so
the outputs are directly comparable.

Run:  python scripts/apply_blast_floor.py
      (reads reports/experiments/v1/five_level_v2_fs, writes
       reports/experiments/v1/five_level_v2_floor)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import LIKELIHOOD, band_label

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_fs"
OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_floor"
SERVERS = ("calendar_real", "slack_real", "fs_corp")

# Mutating tiers on the five_level_v2 ladder: 4 = write/modify, 5 = delete/destroy.
MUTATION_IMPACT_MIN = 4


def floor_table(sens4_floor: int) -> dict[int, int]:
    """Minimum blast per asset sensitivity (sensitivities absent keep model blast)."""
    return {5: 4, 4: sens4_floor}


def floored_blast(
    sensitivity: int, blast: int | None, impact: int, floors: dict[int, int], *, gated: bool
) -> int | None:
    """Blast after the floor rule; ``None`` (N/A) passes through untouched."""
    if blast is None:
        return None
    if gated and impact < MUTATION_IMPACT_MIN:
        return blast
    return max(blast, floors.get(sensitivity, 1))


def apply_floor(table: dict, floors: dict[int, int], *, gated: bool) -> tuple[dict, int]:
    """Return (new scan table, number of cells the floor raised).

    The new table keeps every primitive except blast_radius, which is floored;
    cells and bands are recomputed exactly as the baseline pipeline does.
    """
    sens = table["asset_sensitivity"]
    impacts = table["tool_impact"]
    new_blast: dict[str, int | None] = {}
    raised = 0
    for key, blast in table["blast_radius"].items():
        tool, asset = key.split("|", 1)
        value = floored_blast(sens[asset], blast, impacts[tool], floors, gated=gated)
        new_blast[key] = value
        if blast is not None and value != blast:
            raised += 1

    cells: dict[str, dict[str, float | None]] = {}
    bands: dict[str, dict[str, str]] = {}
    for asset, s in sens.items():
        crow: dict[str, float | None] = {}
        brow: dict[str, str] = {}
        for tool, i in impacts.items():
            br = new_blast[f"{tool}|{asset}"]
            if br is None:
                crow[tool], brow[tool] = None, "na"
            else:
                crow[tool] = round(s * br * LIKELIHOOD * i, 2)
                brow[tool] = band_label(s, br, i)
        cells[asset], bands[asset] = crow, brow

    dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0, "na": 0}
    for row in bands.values():
        for band in row.values():
            dist[band] = dist.get(band, 0) + 1

    new_table = dict(table)
    new_table.update(
        {
            "experiment": "blast_floor",
            "floor_variant": "gated" if gated else "plain",
            "floor_table": {str(k): v for k, v in floors.items()},
            "floor_raised_cells": raised,
            "blast_radius_baseline": table["blast_radius"],
            "blast_radius": new_blast,
            "cells": cells,
            "bands": bands,
            "band_distribution": dist,
        }
    )
    return new_table, raised


def _write_scores_csv(out: Path, stem: str, baseline: dict, plain: dict, gated: dict) -> None:
    """One tidy row per scored cell: baseline vs both floor variants."""
    sens, impacts = baseline["asset_sensitivity"], baseline["tool_impact"]
    rows = []
    for key, blast in baseline["blast_radius"].items():
        tool, asset = key.split("|", 1)
        s, i = sens[asset], impacts[tool]
        row: dict[str, object] = {
            "server": baseline["server"],
            "asset": asset,
            "asset_sensitivity": s,
            "tool": tool,
            "tool_impact": i,
            "blast_baseline": blast if blast is not None else "",
        }
        for name, tbl in (("plain", plain), ("gated", gated)):
            br = tbl["blast_radius"][key]
            row[f"blast_{name}"] = br if br is not None else ""
            row[f"score_{name}"] = tbl["cells"][asset][tool] or ""
            row[f"band_{name}"] = tbl["bands"][asset][tool]
        if blast is not None:
            row["score_baseline"] = round(s * blast * LIKELIHOOD * i, 2)
            row["band_baseline"] = band_label(s, blast, i)
        else:
            row["score_baseline"], row["band_baseline"] = "", "na"
        rows.append(row)
    fields = [
        "server",
        "asset",
        "asset_sensitivity",
        "tool",
        "tool_impact",
        "blast_baseline",
        "score_baseline",
        "band_baseline",
        "blast_plain",
        "score_plain",
        "band_plain",
        "blast_gated",
        "score_gated",
        "band_gated",
    ]
    with (out / f"{stem}_scores.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=BASELINE_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--sens4-floor",
        type=int,
        default=3,
        choices=(2, 3),
        help="minimum blast for sensitivity-4 assets (the rule allows 2 or 3)",
    )
    args = parser.parse_args(argv)
    floors = floor_table(args.sens4_floor)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary: list[str] = [
        "# Experiment `blast_floor` — sensitivity-coupled minimum blast",
        "",
        f"Floors: sensitivity 5 -> blast >= {floors[5]}; sensitivity 4 -> blast >= "
        f"{floors[4]}. `plain` floors every scored cell; `gated` floors only mutating "
        f"tools (impact >= {MUTATION_IMPACT_MIN}). Baseline: `{args.baseline_dir.name}`.",
        "",
        "| server | variant | cells raised | low | medium | high | critical | na |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for stem in SERVERS:
        src = args.baseline_dir / f"{stem}.json"
        if not src.exists():
            print(f"[skip] {src} missing")
            continue
        baseline = json.loads(src.read_text(encoding="utf-8"))
        variants: dict[str, dict] = {}
        for name, gated in (("plain", False), ("gated", True)):
            table, raised = apply_floor(baseline, floors, gated=gated)
            variants[name] = table
            out_json = args.out_dir / f"{stem}_{name}.json"
            out_json.write_text(json.dumps(table, indent=2), encoding="utf-8")
            d = table["band_distribution"]
            summary.append(
                f"| {baseline['server']} | {name} | {raised} | {d['low']} | {d['medium']} "
                f"| {d['high']} | {d['critical']} | {d['na']} |"
            )
            print(f"[ok] {stem} {name}: {raised} cells floored -> {out_json.name}")
        _write_scores_csv(args.out_dir, stem, baseline, variants["plain"], variants["gated"])
    (args.out_dir / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"[done] wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
