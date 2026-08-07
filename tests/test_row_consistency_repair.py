"""Tests for the rowfix experiment's guardrails and table rebuild (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.row_consistency_repair import apply_repairs, build_row, rebuild_cells


def _table() -> dict:
    return {
        "asset_sensitivity": {"cal": 4},
        "tool_impact": {"delete": 5, "list": 3, "ping": 1},
        "blast_radius": {"delete|cal": 1, "list|cal": 2, "ping|cal": None},
    }


def test_build_row_skips_na_and_carries_scores():
    row = build_row(_table(), "cal")
    assert [r["tool_name"] for r in row] == ["delete", "list"]  # ping is N/A
    assert row[0]["score"] == 4 * 1 * 5


def test_apply_repairs_guardrails():
    table = _table()
    applied = apply_repairs(
        table,
        "cal",
        [
            {"tool_name": "delete", "blast_radius": 9, "reason": "P1"},  # clamped to 5
            {"tool_name": "ping", "blast_radius": 3},  # N/A cell — dropped
            {"tool_name": "ghost", "blast_radius": 3},  # unknown tool — dropped
            {"tool_name": "list", "blast_radius": 2},  # no-op — dropped
            {"tool_name": "list", "blast_radius": "bad"},  # unparsable — dropped
        ],
    )
    assert [(c["tool"], c["old"], c["new"]) for c in applied] == [("delete", 1, 5)]
    assert table["blast_radius"]["delete|cal"] == 5
    assert table["blast_radius"]["ping|cal"] is None
    assert table["blast_radius"]["list|cal"] == 2


def test_rebuild_cells_recomputes_scores_bands_and_na():
    table = _table()
    apply_repairs(table, "cal", [{"tool_name": "delete", "blast_radius": 3, "reason": "P1"}])
    rebuild_cells(table)
    assert table["cells"]["cal"]["delete"] == 4 * 3 * 5
    assert table["cells"]["cal"]["ping"] is None
    assert table["bands"]["cal"]["ping"] == "na"
    assert table["band_distribution"]["na"] == 1
