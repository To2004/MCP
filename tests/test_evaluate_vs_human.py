"""Tests for the multi-rater oracle logic in scripts/evaluate_vs_human.py."""

from __future__ import annotations

from scripts.evaluate_vs_human import _consensus, _interrater


def test_consensus_median_is_robust_to_a_maximalist_rater():
    """One all-critical rater must not drag the consensus to critical."""
    cell = ("csv", "read_file")
    raters = [
        {cell: "low"}, {cell: "medium"}, {cell: "medium"},
        {cell: "high"}, {cell: "critical"},  # the DREAD-style outlier
    ]
    # Ranks sorted: [low, medium, medium, high, critical] -> median = medium.
    assert _consensus(raters)[cell] == "medium"


def test_consensus_upper_median_leans_conservative_on_even_panels():
    cell = ("a", "t")
    raters = [{cell: "low"}, {cell: "high"}]  # two middles -> take the higher
    assert _consensus(raters)[cell] == "high"


def test_interrater_counts_exact_and_within_one():
    cell = ("a", "t")
    raters = [{cell: "low"}, {cell: "medium"}, {cell: "critical"}]
    exact, adj, total = _interrater(raters)
    # 3 pairs by rank low=1,medium=2,critical=4: (1,2) within-one; (1,4) no; (2,4) no.
    assert total == 3
    assert exact == 0
    assert adj == 1


def test_interrater_perfect_agreement():
    cell = ("a", "t")
    raters = [{cell: "high"}, {cell: "high"}, {cell: "high"}]
    exact, adj, total = _interrater(raters)
    assert exact == total == 3 and adj == 3
