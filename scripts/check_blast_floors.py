"""Verify the blast floors hold in a finished scan, and report who set each cell.

The floors are stated twice on purpose: in the blast prompt (so the model's own
number already respects them) and in the deterministic assembly (so a scan cannot
ship a cell below them). This checks the artifact for both:

* **Violations** — any scored cell below its floor. Should be zero; a non-zero
  count means the assembly did not run or ran with a different configuration.
* **Corrections** — cells the assembly had to raise, i.e. where the model
  ignored a floor it was told. This is the number that says whether stating the
  floors in the prompt is working: it should fall toward zero as the prompt
  lands, and every remaining one is a disagreement worth reading.

Floors checked (read from the artifact, not hardcoded, so this cannot silently
disagree with the scan it is auditing):

    asset sensitivity 5  ->  blast >= 4
    asset sensitivity 4  ->  blast >= 3
    tool impact       5  ->  blast >= 3

Run:  uv run python scripts/check_blast_floors.py [--dir <results dir>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r"


def floor_for(sensitivity: int, impact: int, floors: dict[int, int], impact_floors: dict[int, int]) -> int:
    """The binding floor for one cell — the higher of the two keyed rules."""
    return max(floors.get(sensitivity, 1), impact_floors.get(impact, 1))


def audit(table: dict) -> dict:
    """Violations and corrections for one scan artifact."""
    config = table.get("blast_floor") or {}
    floors = {int(k): v for k, v in (config.get("floors") or {}).items()}
    impact_floors = {int(k): v for k, v in (config.get("impact_floors") or {}).items()}
    gate = config.get("gate_impact_min", 1)
    sens = table.get("asset_sensitivity") or {}
    impacts = table["tool_impact"]
    final = table["blast_radius"]
    raw = table.get("blast_radius_raw") or {}

    violations, corrections = [], []
    for key, value in final.items():
        if value is None:
            continue
        tool, asset = key.split("|", 1)
        if asset not in sens or impacts.get(tool) is None:
            continue
        if impacts[tool] < gate:  # outside the floor's gate; not eligible
            continue
        needed = floor_for(sens[asset], impacts[tool], floors, impact_floors)
        if value < needed:
            violations.append(
                {"cell": key, "blast": value, "floor": needed,
                 "sens": sens[asset], "impact": impacts[tool]}
            )
        before = raw.get(key)
        if before is not None and before < needed:
            corrections.append(
                {"cell": key, "model_said": before, "raised_to": value,
                 "floor": needed, "sens": sens[asset], "impact": impacts[tool]}
            )
    scored = sum(1 for v in final.values() if v is not None)
    return {
        "config": {"gate_impact_min": gate, "floors": floors, "impact_floors": impact_floors},
        "roof": table.get("blast_roof") or {},
        "scored_cells": scored,
        "violations": violations,
        "corrections": corrections,
        "reported_raised": config.get("raised_cells"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--stem", default=None, help="check one artifact only")
    args = parser.parse_args(argv)

    paths = sorted(
        p for p in args.dir.glob("*.json")
        if p.stem not in {"evaluation"} and (args.stem is None or p.stem == args.stem)
    )
    if not paths:
        print(f"[FAIL] no scan artifacts in {args.dir}")
        return 1

    rc = 0
    for path in paths:
        table = json.loads(path.read_text(encoding="utf-8"))
        if "blast_radius" not in table:
            continue
        result = audit(table)
        cfg = result["config"]
        roof = "none" if not result["roof"] else f"read_cap {result['roof'].get('read_cap')}"
        label = "ok" if not result["violations"] else "FAIL"
        if result["violations"]:
            rc = 1
        print(
            f"[{label}] {path.stem}: {result['scored_cells']} scored cells | "
            f"floors {cfg['floors']} + impact {cfg['impact_floors']} "
            f"(gate {cfg['gate_impact_min']}) | roof {roof}"
        )
        print(
            f"        violations {len(result['violations'])} | "
            f"model needed correcting on {len(result['corrections'])} cell(s)"
            + (
                f" (artifact reports {result['reported_raised']} raised)"
                if result["reported_raised"] is not None
                else ""
            )
        )
        for item in result["violations"][:10]:
            print(
                f"          BELOW FLOOR {item['cell']}: blast {item['blast']} < {item['floor']} "
                f"(sens {item['sens']}, impact {item['impact']})"
            )
        for item in result["corrections"][:10]:
            print(
                f"          raised {item['cell']}: model said {item['model_said']} -> "
                f"{item['raised_to']} (sens {item['sens']}, impact {item['impact']})"
            )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
