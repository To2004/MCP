"""Tests for the judge-ranking metrics (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.judge_blast_experiments import is_offender, metrics


def test_metrics_agreement_and_bias():
    rows = [
        {"offender": True, "judged": 3, "exp": 3},  # exact
        {"offender": True, "judged": 3, "exp": 1},  # -2 under
        {"offender": False, "judged": 2, "exp": 3},  # +1 over
        {"offender": False, "judged": None, "exp": 4},  # judge failed — excluded
        {"offender": False, "judged": 2, "exp": None},  # experiment N/A — excluded
    ]
    m = metrics(rows, "exp", lambda r: True)
    assert m["n"] == 3
    assert m["exact"] == 1 / 3
    assert m["within1"] == 2 / 3
    assert m["mae"] == (0 + 2 + 1) / 3
    assert m["bias"] == (0 - 2 + 1) / 3
    off = metrics(rows, "exp", lambda r: r["offender"])
    assert off["n"] == 2 and off["bias"] == -1.0
    assert metrics([], "exp", lambda r: True) is None


def test_is_offender_requires_mutation_sensitive_and_low_blast():
    table = {
        "blast_radius": {"del|cal": 1, "del|readme": 1, "list|cal": 1, "del|na": None},
        "tool_impact": {"del": 5, "list": 2},
        "asset_sensitivity": {"cal": 4, "readme": 1, "na": 5},
    }
    assert is_offender(table, "del", "cal") is True
    assert is_offender(table, "del", "readme") is False  # low sensitivity
    assert is_offender(table, "list", "cal") is False  # not a mutation
    assert not is_offender(table, "del", "na")  # N/A cell
