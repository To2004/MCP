"""Tests for CIA-as-a-facet-selector (the v6 rule)."""

from __future__ import annotations

import pytest

from mcp_security.static_scoring import cia_facets as cf


def test_loss_axis_orderings():
    assert cf.parse_loss_axis("C>I>A") == {"C": 0, "I": 1, "A": 2}
    assert cf.parse_loss_axis("A>I>C") == {"A": 0, "I": 1, "C": 2}
    # "I≈C>A" — a tie shares a rank, so both keep the asset's full sensitivity.
    assert cf.parse_loss_axis("I≈C>A") == {"I": 0, "C": 0, "A": 1}
    # An unstated axis means no axis leads: every facet keeps the full value.
    assert cf.parse_loss_axis("none") == {"C": 0, "I": 0, "A": 0}
    assert cf.parse_loss_axis("") == {"C": 0, "I": 0, "A": 0}


def test_loss_axis_accepts_profile_letter_grades():
    assert cf.parse_loss_axis("C:H I:M A:L") == {"C": 0, "I": 1, "A": 2}


def test_unreadable_axis_raises():
    with pytest.raises(cf.LossAxisError):
        cf.parse_loss_axis("mostly integrity")


def test_facet_split_is_anchored_at_the_leading_axis():
    assert cf.facet_sensitivity(4, "C>I>A") == {"C": 4, "I": 3, "A": 2}
    assert cf.facet_sensitivity(4, "I>A>C") == {"I": 4, "A": 3, "C": 2}
    # The floor holds at 1 rather than going to zero.
    assert cf.facet_sensitivity(1, "C>I>A") == {"C": 1, "I": 1, "A": 1}


def test_op_to_facet_map():
    assert cf.violated_facets(["READ"]) == ("C",)
    assert cf.violated_facets(["DELETE"]) == ("I", "A")
    assert cf.violated_facets(["BROADCAST"]) == ("C", "I")
    assert cf.violated_facets(["EXECUTE"]) == ("C", "I", "A")
    # Multiple ops union, in canonical C/I/A order.
    assert cf.violated_facets(["WRITE", "READ"]) == ("C", "I")
    # An unknown or missing op must not become harmless.
    assert cf.violated_facets(["FROBNICATE"]) == ("C", "I", "A")
    assert cf.violated_facets([]) == ("C", "I", "A")


def test_selector_never_raises_a_cell():
    """The design property: no (axis, op) combination can exceed the asset's own number."""
    for axis in ("C>I>A", "I>A>C", "A>I>C", "I≈C>A", "none"):
        for ops in (["READ"], ["WRITE"], ["DELETE"], ["BROADCAST"], ["EXECUTE"], []):
            for sensitivity in range(1, 6):
                verdict = cf.effective_sensitivity(sensitivity, axis, ops)
                assert verdict.sensitivity <= sensitivity, (axis, ops, sensitivity)


def test_read_and_write_diverge_on_an_integrity_led_asset():
    read = cf.effective_sensitivity(4, "I>A>C", ["READ"])
    write = cf.effective_sensitivity(4, "I>A>C", ["WRITE"])
    assert (read.sensitivity, read.facet) == (2, "C")
    assert (write.sensitivity, write.facet) == (4, "I")


def test_read_and_write_diverge_the_other_way_on_a_confidentiality_led_asset():
    read = cf.effective_sensitivity(4, "C>I>A", ["READ"])
    write = cf.effective_sensitivity(4, "C>I>A", ["WRITE"])
    assert (read.sensitivity, read.facet) == (4, "C")
    assert (write.sensitivity, write.facet) == (3, "I")


def test_a_tool_violating_nothing_prices_at_the_lowest_facet():
    verdict = cf.effective_sensitivity(4, "C>I>A", ["PING"])
    assert verdict.facet is None
    assert verdict.sensitivity == 2  # the asset's A value
    assert "violates no CIA objective" in verdict.reason
