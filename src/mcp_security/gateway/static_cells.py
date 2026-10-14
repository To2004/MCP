"""Turn a ``static-scan`` result (three separate 1–5 levels) into the cells the runtime reads.

``static-scan`` reports asset sensitivity, tool impact and blast radius on their own and
combines nothing. The runtime scorer needs one number per (asset, tool) cell, so this is
the single place they are combined, with the repo's v5 formula and bands
(``static_scoring.pipeline``): ``sensitivity × blast × impact``, at most 125. A pair the
tool does not reach, or that the scan left unanswered, has no cell.

    uv run python -m mcp_security.gateway.static_cells --scan X.scan.json --out X.cells.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import FORMULA, LIKELIHOOD, band_label_v5

LEVEL_MAX = 5
SCORE_MAX = float(LEVEL_MAX**3)
NOT_APPLICABLE = "na"


def cells_from_levels(scan: dict) -> dict:
    """The cell matrix (``cells``, ``bands``, ``score_max``) for one static-scan result."""
    sensitivity = {row["asset"]: row["sensitivity"] for row in scan["assets"]}
    impact = {row["tool"]: row["impact"] for row in scan["tools"]}
    cells: dict[str, dict] = {asset: {} for asset in sensitivity}
    bands: dict[str, dict] = {asset: {} for asset in sensitivity}
    unanswered = []
    for pair in scan["reach"]:
        asset, tool = pair["asset"], pair["tool"]
        levels = (sensitivity.get(asset), pair["blast"], impact.get(tool))
        reaches = pair["reaches"]
        if reaches is None or (reaches and None in levels):
            unanswered.append(f"{tool}|{asset}")
        if reaches and None not in levels:
            s, b, i = levels
            cells[asset][tool] = round(s * b * LIKELIHOOD * i, 2)
            bands[asset][tool] = band_label_v5(s, b, i)
        else:
            cells[asset][tool] = None
            bands[asset][tool] = NOT_APPLICABLE
    return {
        "server": scan.get("server"),
        "formula": FORMULA,
        "score_max": SCORE_MAX,
        "catalog": scan.get("catalog"),
        "policy": scan.get("policy"),
        "unanswered": unanswered,
        # The levels themselves, keyed as in a v5 scan, so every score can be decomposed.
        "asset_sensitivity": sensitivity,
        "tool_impact": impact,
        "blast_radius": {f"{p['tool']}|{p['asset']}": p["blast"] for p in scan["reach"]},
        "cells": cells,
        "bands": bands,
    }


def main() -> None:
    """Write the cell matrix for ``--scan`` to ``--out``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    matrix = cells_from_levels(json.loads(args.scan.read_text(encoding="utf-8")))
    args.out.write_text(json.dumps(matrix, indent=1) + "\n", encoding="utf-8")
    scored = sum(value is not None for row in matrix["cells"].values() for value in row.values())
    print(f"{scored} cells, {len(matrix['unanswered'])} unanswered pairs -> {args.out}")


if __name__ == "__main__":
    main()
