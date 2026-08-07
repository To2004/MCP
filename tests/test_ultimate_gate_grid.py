"""Tests for the ult gate-variant grid rebuild (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ultimate_gate_grid import GRID, band_agreement, rebuild, variant_name


def _table() -> dict:
    return {
        "server": "t:test",
        "asset_ids": ["cal", "readme"],
        "asset_sensitivity": {"cal": 4, "readme": 1},
        "tool_impact": {"delete": 5, "read": 3, "read_old": 3},
        "alias_twins": {"read_old": "read"},
        "blast_radius_raw": {
            "delete|cal": 1,
            "read|cal": 2,
            "read_old|cal": 1,
            "delete|readme": 1,
            "read|readme": None,
            "read_old|readme": None,
        },
        "blast_radius": {},
        "cells": {},
        "bands": {},
    }


def test_grid_covers_four_variants():
    assert sorted(variant_name(c) for c in GRID) == ["g3_s4f2", "g3_s4f3", "g4_s4f2", "g4_s4f3"]


def test_rebuild_applies_alias_then_floor_per_variant():
    table = _table()
    by_name = {variant_name(c): rebuild(table, c) for c in GRID}
    # Alias pass in every variant: read_old|cal pulled up to read's blast 2.
    for v in by_name.values():
        assert v["blast_radius"]["read_old|cal"] >= 2
        assert v["blast_radius"]["read|readme"] is None  # both-N/A stays N/A
    # g4 floors only the delete (impact 5): sens-4 floor applies.
    assert by_name["g4_s4f3"]["blast_radius"]["delete|cal"] == 3
    assert by_name["g4_s4f2"]["blast_radius"]["delete|cal"] == 2
    assert by_name["g4_s4f3"]["blast_radius"]["read|cal"] == 2  # read not gated at g4
    # g3 also floors the reads (impact 3) on the sens-4 asset.
    assert by_name["g3_s4f3"]["blast_radius"]["read|cal"] == 3
    assert by_name["g3_s4f3"]["blast_radius"]["read_old|cal"] == 3
    # Low-sensitivity asset never floored; raw preserved in the source table.
    for v in by_name.values():
        assert v["blast_radius"]["delete|readme"] == 1
    assert table["blast_radius_raw"]["delete|cal"] == 1
    # Scores/bands recomputed: delete|cal under g4_s4f3 = 4*3*5.
    v = by_name["g4_s4f3"]
    assert v["cells"]["cal"]["delete"] == 60
    assert v["bands"]["cal"]["delete"] == "high"
    assert v["band_distribution"]["na"] == 2


def test_band_agreement_counts():
    a = {"cal": {"delete": "high", "read": "medium"}, "r": {"x": "na"}}
    b = {"cal": {"delete": "medium", "read": "medium"}, "r": {"x": "low"}}
    shared, same, higher = band_agreement(a, b)
    assert (shared, same, higher) == (2, 1, 1)  # na cells excluded
