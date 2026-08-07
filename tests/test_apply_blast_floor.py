"""Tests for the blast_floor experiment's floor rule and table rebuild."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.apply_blast_floor import apply_floor, floor_table, floored_blast

FLOORS = floor_table(3)  # sens 5 -> min 4, sens 4 -> min 3


def test_floor_raises_pinpoint_mutation_on_sensitive_asset():
    # delete-event style cell: sens 4, impact 5, model blast 1 -> floored to 3.
    assert floored_blast(4, 1, 5, FLOORS, gated=False) == 3
    assert floored_blast(5, 1, 5, FLOORS, gated=False) == 4


def test_floor_never_lowers_and_ignores_low_sensitivity():
    assert floored_blast(4, 5, 5, FLOORS, gated=False) == 5  # already above the floor
    assert floored_blast(3, 1, 5, FLOORS, gated=False) == 1  # no floor below sens 4
    assert floored_blast(1, 1, 5, FLOORS, gated=False) == 1


def test_gated_variant_spares_reads_and_metadata():
    # Gated: impact <= 3 (liveness/metadata/read) keeps the model's blast...
    assert floored_blast(4, 1, 2, FLOORS, gated=True) == 1
    assert floored_blast(5, 2, 3, FLOORS, gated=True) == 2
    # ...while mutations (impact >= 4) are floored.
    assert floored_blast(4, 1, 4, FLOORS, gated=True) == 3


def test_na_cells_pass_through():
    assert floored_blast(5, None, 5, FLOORS, gated=False) is None


def _tiny_table() -> dict:
    return {
        "server": "t:test",
        "asset_sensitivity": {"cal": 4, "readme": 1},
        "tool_impact": {"delete": 5, "list": 2},
        "blast_radius": {
            "delete|cal": 1, "list|cal": 1, "delete|readme": 1, "list|readme": None,
        },
    }


def test_apply_floor_rebuilds_cells_bands_and_counts():
    table, raised = apply_floor(_tiny_table(), FLOORS, gated=False)
    assert raised == 2  # plain floors both sens-4 cells: delete|cal AND list|cal
    assert table["blast_radius"]["delete|cal"] == 3
    assert table["blast_radius"]["list|cal"] == 3

    gated_table, gated_raised = apply_floor(_tiny_table(), FLOORS, gated=True)
    assert gated_raised == 1  # gated spares the metadata tool
    assert gated_table["blast_radius"]["list|cal"] == 1
    assert table["cells"]["cal"]["delete"] == 4 * 3 * 5
    assert table["blast_radius_baseline"]["delete|cal"] == 1  # baseline preserved
    assert table["cells"]["readme"]["list"] is None
    assert table["bands"]["readme"]["list"] == "na"
    assert table["band_distribution"]["na"] == 1
