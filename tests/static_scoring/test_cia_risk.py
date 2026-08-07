"""Tests for the CIA-native score — additive evidence over the existing score."""

from __future__ import annotations

from mcp_security.static_scoring.cia_risk import (
    SCORE_MAX,
    control_for,
    op_impact,
    score_cell,
)


def _score(sens, axis, ops, blast, base, **kw):
    return score_cell(sens, axis, ops, blast, base, **kw)


def test_na_pair_scores_nothing():
    assert _score(5, "C>I>A", ["READ"], None, 0) is None


def test_the_invariant_a_cell_is_never_lowered():
    """The rule the whole module exists to guarantee."""
    for axis in ("C>I>A", "I>A>C", "A>I>C", "none"):
        for ops in (["READ"], ["WRITE"], ["DELETE"], ["METADATA"], ["PING"], ["BROADCAST"]):
            for sens in range(1, 6):
                for blast in range(1, 6):
                    base = sens * blast * 5  # the harshest base the old scale can give
                    risk = _score(sens, axis, ops, blast, base)
                    assert risk.score >= round(base), (axis, ops, sens, blast)


def test_a_crown_jewel_write_keeps_its_value():
    """The regression that motivated the invariant: executive x create-events."""
    # executive: sensitivity 4, C>I>A, coverage 4, v5 score 64 (4x4x4).
    risk = _score(4, "C>I>A", ["CREATE", "WRITE"], 4, 64)
    assert risk.score == 64
    # The org ranks this asset's loss on confidentiality, so that is what the cell
    # is reported and controlled as -- not integrity, which is merely the verb.
    assert risk.driver == "C"


def test_the_orgs_leading_objective_is_never_zeroed():
    """A write on a confidentiality-led asset still carries a confidentiality reason.

    `create-event` classifies as CREATE, which the op chart scores I-only. But the
    calendar register says an event write reaches `contacts` through its attendee
    fields, and the org rates that asset on confidentiality. Scoring the cell on
    integrity alone would discard the org's stated reason for the asset mattering.
    """
    risk = _score(4, "C>I>A", ["CREATE", "WRITE"], 5, 80)
    assert risk.impact["C"] > 0, "the org's leading objective was zeroed by the op chart"
    assert risk.driver == "C"
    assert control_for(risk).startswith("deny")


def test_a_trailing_objective_is_still_allowed_to_be_zero():
    """The fallback applies to the LEADING objective only, not to all three."""
    risk = _score(4, "C>I>A", ["READ"], 3, 36)
    assert risk.impact["C"] == 5
    assert risk.impact["A"] == 0  # a read cannot deny availability


def test_an_under_priced_read_is_raised():
    # incident-response: sensitivity 5, coverage 5, v5 score 75 (5x5x3).
    risk = _score(5, "C>I>A", ["READ"], 5, 75, flags=("self-sufficient",))
    assert risk.score == 125
    assert risk.driver == "C"
    assert risk.raised is True


def test_a_read_can_outrank_a_write_on_the_same_asset():
    """The ordering the 1-5 action ladder makes unsayable."""
    read = _score(5, "C>I>A", ["READ"], 4, 5 * 4 * 3)  # 5x4x5 = 100
    write = _score(5, "C>I>A", ["WRITE"], 4, 5 * 4 * 4)  # 5x4x4 = 80
    assert read.score > write.score


def test_sensitivity_is_not_split_by_the_loss_axis():
    """A ranking is not a magnitude: the same write scores the same on either axis."""
    c_led = _score(4, "C>I>A", ["WRITE"], 4, 64)
    i_led = _score(4, "I>A>C", ["WRITE"], 4, 64)
    assert c_led.score == i_led.score == 64
    assert c_led.sensitivity == i_led.sensitivity == 4


def test_score_stays_inside_the_scale():
    for ops in (["READ"], ["DELETE"], ["EXECUTE"], ["BROADCAST"]):
        for blast in range(1, 6):
            risk = _score(5, "C>I>A", ops, blast, 125, flags=("hub", "self-sufficient"))
            assert 0 <= risk.score <= SCORE_MAX


def test_a_tool_that_violates_nothing_keeps_its_base_score():
    """A liveness check is not "touching the crown jewel" — no floor applies."""
    risk = _score(5, "C>I>A", ["PING"], 5, 25)
    assert risk.score == 25
    assert risk.raised is False
    assert risk.floored is False
    assert risk.driver is None


def test_sensitivity_floor_keeps_a_crown_jewel_out_of_the_routine_band():
    # A metadata listing on a sensitivity-5 asset: 5 x 4 x 2 = 40 in both scales,
    # which sits below sensitivity-4 cells. The floor lifts it.
    risk = _score(5, "C>I>A", ["LIST"], 4, 40)
    assert risk.score == 50
    assert risk.floored is True
    # Sensitivity 3 and below has no floor: it is not a crown jewel.
    assert _score(3, "C>I>A", ["LIST"], 4, 24).floored is False


def test_the_floor_never_lowers_a_cell_that_already_scores_higher():
    risk = _score(5, "C>I>A", ["DELETE"], 5, 125)
    assert risk.score == 125
    assert risk.floored is False


def test_self_sufficient_lifts_confidentiality_coverage_only():
    plain = _score(4, "C>I>A", ["READ"], 1, 12)
    flagged = _score(4, "C>I>A", ["READ"], 1, 12, flags=("self-sufficient",))
    assert flagged.score > plain.score
    assert flagged.coverage["C"] == 5 and flagged.coverage["I"] == 1


def test_self_sufficient_needs_a_content_returning_operation():
    """A credential leaks by being read — not by being listed, nor by posting."""
    listing = _score(5, "C>I>A", ["METADATA"], 1, 10, flags=("self-sufficient",))
    posting = _score(5, "C>I>A", ["BROADCAST"], 1, 10, flags=("self-sufficient",))
    assert listing.coverage["C"] == 1
    assert posting.coverage["C"] == 1


def test_hub_alone_does_not_lift_coverage():
    hub = _score(4, "I>A>C", ["READ"], 1, 12, flags=("hub",))
    assert hub.coverage["C"] == 1


def test_op_impact_is_the_max_across_a_tool_s_operations():
    assert op_impact(["READ"]) == {"C": 5}
    assert op_impact(["DELETE"]) == {"I": 5, "A": 5}
    assert op_impact(["CREATE", "WRITE"]) == {"I": 4}
    assert op_impact(["READ", "DELETE"]) == {"C": 5, "I": 5, "A": 5}
    # An unclassified op must not become harmless.
    assert op_impact(["FROBNICATE"]) == {"C": 3, "I": 3, "A": 3}
    assert op_impact([]) == {"C": 3, "I": 3, "A": 3}


def test_mutations_never_lose_against_the_old_ladder():
    """Every write/delete op must meet the ladder tier it had before."""
    ladder = {"CREATE": 4, "WRITE": 4, "MODIFY": 4, "MOVE": 4, "OVERWRITE": 5, "DELETE": 5}
    for op, tier in ladder.items():
        assert max(op_impact([op]).values()) >= tier, op


def test_control_follows_the_driver():
    assert control_for(_score(5, "C>I>A", ["READ"], 5, 10)).startswith("deny")
    assert control_for(_score(5, "I>A>C", ["DELETE"], 5, 10)).startswith("require human")
    assert control_for(None).startswith("existing")
