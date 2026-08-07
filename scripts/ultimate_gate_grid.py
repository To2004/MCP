"""Offline gate-variant grid over the ``five_level_v2_ult`` scan artifacts.

The ult scan preserves the model's verbatim blast (``blast_radius_raw``) plus
its alias-twin map, so every floor variant can be re-derived deterministically
without an LLM. Grid: gate_impact_min in {3, 4} x sens4_floor in {2, 3}
(floors = {5: 4, 4: sens4_floor}); each variant reapplies alias unification
first, then the gated floor, then recomputes cells/bands with the pipeline's
own ``band_label_v5`` — no scoring logic is duplicated here.

The report compares each variant's band distribution and its band agreement on
shared cells against two prior experiments: the ``five_level_v2_fs`` baseline
(whose bands used the impact-1-3-calibrated ``band_label`` — the known
miscalibration ult fixes) and ``five_level_v2_desc`` (``band_label_no_sens``).

Run:  python scripts/ultimate_gate_grid.py
      (reads reports/experiments/v2/five_level_v2_ult, writes
       reports/experiments/v2/five_level_v2_ult_grid)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import (
    LIKELIHOOD,
    apply_alias_twins,
    apply_bulk_blast,
    apply_bulk_impact,
    apply_gated_floor,
    band_label_v5,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ULT_DIR = REPO_ROOT / "reports" / "experiments" / "v2" / "five_level_v2_ult"
OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v2" / "five_level_v2_ult_grid"
STEMS = ("calendar_real", "slack_real", "github_real", "fs_corp_filesystem")

# Prior experiments for band-agreement comparison: dir, file pattern, stem map.
BASELINES = {
    "five_level_v2_fs": {
        "dir": "v1/five_level_v2_fs",
        "stem_map": {"fs_corp_filesystem": "fs_corp"},  # older stem naming
    },
    "five_level_v2_desc": {"dir": "v2/five_level_v2_desc", "stem_map": {}},
}

GRID = [{"gate_impact_min": gate, "floors": {5: 4, 4: s4}} for gate in (3, 4) for s4 in (2, 3)]


def variant_name(cfg: dict) -> str:
    return f"g{cfg['gate_impact_min']}_s4f{cfg['floors'][4]}"


def rebuild(table: dict, cfg: dict) -> dict:
    """One grid variant's full table, re-derived from the raw primitives.

    Mirrors the pipeline's v3 assembly order (bulk impact → alias → floors →
    bulk blast); artifacts from pre-v3 scans simply have empty bulk keys and
    reduce to the original chain.
    """
    sens = table["asset_sensitivity"]
    asset_ids = table["asset_ids"]
    bulk_twins = table.get("bulk_twins", {})
    impacts = dict(table.get("tool_impact_raw") or table["tool_impact"])
    impacts, _ = apply_bulk_impact(impacts, bulk_twins)
    blast = dict(table["blast_radius_raw"])
    blast, fixups = apply_alias_twins(blast, table.get("alias_twins", {}), asset_ids)
    blast, raised = apply_gated_floor(
        blast,
        sens,
        impacts,
        floors=cfg["floors"],
        gate_impact_min=cfg["gate_impact_min"],
        impact_floors={
            int(k): v for k, v in table.get("blast_floor", {}).get("impact_floors", {}).items()
        },
    )
    blast, _ = apply_bulk_blast(blast, bulk_twins, asset_ids)
    cells: dict[str, dict[str, float | None]] = {}
    bands: dict[str, dict[str, str]] = {}
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0, "na": 0}
    for asset in asset_ids:
        s = sens[asset]
        crow: dict[str, float | None] = {}
        brow: dict[str, str] = {}
        for tool, i in impacts.items():
            br = blast[f"{tool}|{asset}"]
            if br is None:
                crow[tool], brow[tool] = None, "na"
            else:
                crow[tool] = round(s * br * LIKELIHOOD * i, 2)
                brow[tool] = band_label_v5(s, br, i)
            dist[brow[tool]] += 1
        cells[asset], bands[asset] = crow, brow
    out = dict(table)
    out.update(
        {
            "grid_variant": variant_name(cfg),
            "blast_floor": {
                "gate_impact_min": cfg["gate_impact_min"],
                "floors": {str(k): v for k, v in cfg["floors"].items()},
                "raised_cells": raised,
            },
            "alias_fixups": fixups,
            "blast_radius": blast,
            "cells": cells,
            "bands": bands,
            "band_distribution": dist,
        }
    )
    return out


def band_agreement(bands_a: dict, bands_b: dict) -> tuple[int, int, int]:
    """(shared scored cells, exact band matches, cells where A > B in band order)."""
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    shared = matches = higher = 0
    for asset, row in bands_a.items():
        other = bands_b.get(asset, {})
        for tool, band in row.items():
            band_b = other.get(tool)
            if band in order and band_b in order:
                shared += 1
                matches += band == band_b
                higher += order[band] > order[band_b]
    return shared, matches, higher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ult-dir", type=Path, default=ULT_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Gate-variant grid — `five_level_v2_ult`",
        "",
        "Variants re-derived offline from `blast_radius_raw` (alias pass first, then "
        "the gated floor, then `band_label_v5`). `g<N>` = floor gate impact >= N; "
        "`s4f<M>` = sensitivity-4 floor M (sens-5 floor is always 4). The shipped "
        "scan default is g4_s4f3.",
        "",
    ]
    rc = 0
    for stem in STEMS:
        src = args.ult_dir / f"{stem}.json"
        if not src.exists():
            lines += [f"## {stem}", "", "(scan artifact missing — skipped)", ""]
            rc = 1
            continue
        table = json.loads(src.read_text(encoding="utf-8"))
        lines += [f"## {table['server']}", ""]
        lines.append("| variant | raised | low | medium | high | critical | na |")
        lines.append("|---|---|---|---|---|---|---|")
        variants: dict[str, dict] = {}
        for cfg in GRID:
            v = rebuild(table, cfg)
            variants[v["grid_variant"]] = v
            (args.out_dir / f"{stem}_{v['grid_variant']}.json").write_text(
                json.dumps(v, indent=2), encoding="utf-8"
            )
            d = v["band_distribution"]
            lines.append(
                f"| {v['grid_variant']} | {v['blast_floor']['raised_cells']} | {d['low']} "
                f"| {d['medium']} | {d['high']} | {d['critical']} | {d['na']} |"
            )
        lines.append("")

        # Band agreement vs prior experiments (per variant).
        for label, spec in BASELINES.items():
            prior_stem = spec["stem_map"].get(stem, stem)
            prior_path = REPO_ROOT / "reports" / "experiments" / spec["dir"] / f"{prior_stem}.json"
            if not prior_path.exists():
                continue
            prior = json.loads(prior_path.read_text(encoding="utf-8"))
            lines.append(f"### vs {label} ({prior_stem})")
            lines.append("")
            lines.append("| variant | shared cells | same band | ult higher | ult lower |")
            lines.append("|---|---|---|---|---|")
            for name, v in variants.items():
                shared, same, higher = band_agreement(v["bands"], prior["bands"])
                lines.append(
                    f"| {name} | {shared} | {same} | {higher} | {shared - same - higher} |"
                )
            lines.append("")

        # Tidy per-cell CSV: raw + every variant.
        with (args.out_dir / f"{stem}_grid.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            names = list(variants)
            header = ["asset", "sens", "tool", "impact", "blast_raw"]
            for name in names:
                header += [f"blast_{name}", f"score_{name}", f"band_{name}"]
            writer.writerow(header)
            for asset in table["asset_ids"]:
                for tool, impact in table["tool_impact"].items():
                    key = f"{tool}|{asset}"
                    row = [
                        asset,
                        table["asset_sensitivity"][asset],
                        tool,
                        impact,
                        table["blast_radius_raw"].get(key, ""),
                    ]
                    for name in names:
                        v = variants[name]
                        br = v["blast_radius"][key]
                        row += [
                            br if br is not None else "",
                            v["cells"][asset][tool] or "",
                            v["bands"][asset][tool],
                        ]
                    writer.writerow(row)

    (args.out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[done] wrote {args.out_dir}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
