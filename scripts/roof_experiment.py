"""Offline experiment: try several blast-ROOF rule-sets on an existing pure scan.

Roofs cap blast for low-consequence cells (the mirror of the floors). Because a
wrong roof UNDER-scores a real threat, this harness applies each candidate
rule-set deterministically to a scan's existing floored blast — no GPU, no
re-scan — and reports exactly which cells each rule changes, so a human can
judge before any roof is made the default.

Every rule-set here obeys the safety invariant baked into
:func:`~mcp_security.static_scoring.pipeline.apply_blast_roof`: only impact<=3
cells (reads / metadata / liveness) are ever capped, so no write or delete is
touched. Asset escape flags (hub / population / self-sufficient) exempt a cell
from the read cap, since those assets can legitimately disclose wholesale.

Run:  python scripts/roof_experiment.py [--scan reports/experiments/v3/five_level_v2_pure_v3/calendar_real.json]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import (
    LIKELIHOOD,
    apply_blast_roof,
    band_label_v5,
)
from mcp_security.static_scoring.server_profiles import parse_asset_rows, profile_for

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN = (
    REPO_ROOT / "reports" / "experiments" / "v3" / "five_level_v2_pure_v3" / "calendar_real.json"
)
OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v3" / "roof_experiment"

# Candidate roof rule-sets, from most conservative to most aggressive.
RULESETS = {
    # R0: no roof — the current shipped behaviour, for the diff baseline.
    "none": {},
    # R1 (default candidate): rubric-grounded. A non-escaping read caps at 4; a
    # public (sens-1) asset caps at 4. Only corrects impossible-tier over-scores.
    "conservative": {"read_cap": 4, "sens_caps": {1: 4}},
    # R2 (user's ask): sens-1 caps at 3, metadata/liveness (impact<=2) caps at 3,
    # plus the non-escaping-read cap at 4.
    "user": {"read_cap": 4, "sens_caps": {1: 3}, "combined_cap": (5, 2, 3)},
    # R3 (aggressive): trivial x trivial -> 2; sens<=2 caps at 3; read cap 4.
    "aggressive": {"read_cap": 4, "sens_caps": {1: 3, 2: 3}, "combined_cap": (2, 2, 2)},
}


def load_flags(server: str) -> dict[str, tuple[str, ...]]:
    """{asset_id: flag tuple} from the org profile (roofs are flag-aware)."""
    return {r.asset_id: r.flags for r in parse_asset_rows(profile_for(server).text)}


def recompute(table: dict, blast: dict) -> tuple[dict, dict, dict]:
    """(cells, bands, distribution) for a blast map, via band_label_v5."""
    sens, impacts = table["asset_sensitivity"], table["tool_impact"]
    cells: dict[str, dict] = {}
    bands: dict[str, dict] = {}
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0, "na": 0}
    for a in table["asset_ids"]:
        crow, brow = {}, {}
        for tool, i in impacts.items():
            br = blast[f"{tool}|{a}"]
            if br is None:
                crow[tool], brow[tool] = None, "na"
            else:
                crow[tool] = round(sens[a] * br * LIKELIHOOD * i, 2)
                brow[tool] = band_label_v5(sens[a], br, i)
            dist[brow[tool]] += 1
        cells[a], bands[a] = crow, brow
    return cells, bands, dist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, default=DEFAULT_SCAN)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    table = json.loads(args.scan.read_text(encoding="utf-8"))
    server = table["server"]
    flags = load_flags(server)
    base_blast = table["blast_radius"]  # already floored/aliased/bulk-adjusted
    _, base_bands, base_dist = recompute(table, base_blast)

    lines = [
        f"# Blast-roof experiment — {server}",
        "",
        "Roofs CAP blast for low-consequence cells (mirror of the floors). Applied "
        "offline to the shipped floored blast; only impact<=3 cells are ever capped "
        "(never a write/delete), and assets flagged hub/population/self-sufficient "
        "are exempt from the read cap. Bands are the pure `band_label_v5` of the "
        "resulting score.",
        "",
        "| ruleset | rule | cells capped | low | medium | high | critical |",
        "|---|---|---|---|---|---|---|",
    ]
    all_changes: dict[str, list[dict]] = {}
    for name, cfg in RULESETS.items():
        if not cfg:
            new_blast, fixups = dict(base_blast), []
        else:
            new_blast, fixups = apply_blast_roof(
                base_blast, table["asset_sensitivity"], table["tool_impact"], flags, **cfg
            )
        _, _, dist = recompute(table, new_blast)
        all_changes[name] = fixups
        rule = "—" if not cfg else ", ".join(f"{k}={v}" for k, v in cfg.items())
        lines.append(
            f"| {name} | {rule} | {len(fixups)} | {dist['low']} | {dist['medium']} "
            f"| {dist['high']} | {dist['critical']} |"
        )
    lines.append("")

    # Per-ruleset: the exact cells it changed, and any band drop.
    for name, fixups in all_changes.items():
        if not fixups:
            continue
        lines += [
            f"## {name} — capped cells",
            "",
            "| asset | tool | sens | impact | blast | -> | band before | band after |",
            "|---|---|:-:|:-:|:-:|:-:|---|---|",
        ]
        sens, impacts = table["asset_sensitivity"], table["tool_impact"]
        for f in fixups:
            a, t = f["asset"], f["tool"]
            bb = base_bands[a][t]
            ba = band_label_v5(sens[a], f["to"], impacts[t])
            lines.append(
                f"| `{a}` | `{t}` | {sens[a]} | {impacts[t]} | {f['from']}→{f['to']} "
                f"| | {bb} | {ba} |"
            )
        lines.append("")

    (args.out_dir / f"{Path(args.scan).stem}_roofs.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    # tidy CSV of every cell under every ruleset for spreadsheet review
    with (args.out_dir / f"{Path(args.scan).stem}_roofs.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.writer(fh)
        names = list(RULESETS)
        w.writerow(
            [
                "asset",
                "tool",
                "sens",
                "impact",
                "flags",
                *[f"blast_{n}" for n in names],
                *[f"band_{n}" for n in names],
            ]
        )
        blasts = {}
        for name, cfg in RULESETS.items():
            blasts[name] = (
                dict(base_blast)
                if not cfg
                else apply_blast_roof(
                    base_blast, table["asset_sensitivity"], table["tool_impact"], flags, **cfg
                )[0]
            )
        sens, impacts = table["asset_sensitivity"], table["tool_impact"]
        for a in table["asset_ids"]:
            for t, i in impacts.items():
                if blasts["none"][f"{t}|{a}"] is None:
                    continue
                row = [a, t, sens[a], i, "|".join(flags.get(a, ()))]
                for n in names:
                    row.append(blasts[n][f"{t}|{a}"])
                for n in names:
                    br = blasts[n][f"{t}|{a}"]
                    row.append(band_label_v5(sens[a], br, i))
                w.writerow(row)
    print(f"[done] wrote {args.out_dir}")
    print(f"baseline bands: {base_dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
