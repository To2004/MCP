"""Tests for the CIA misuse signal and its qualifier role in the fusion step."""

from __future__ import annotations

from types import SimpleNamespace

from mcp_security.dynamic.cia import (
    OFF_AXIS_BAND,
    ON_AXIS_BAND,
    leading_facets,
    score_cia,
)

# exec-private protects confidentiality; read-markers protects integrity.
AXES = {
    "exec-private": leading_facets("C>I>A"),
    "read-markers": leading_facets("I>A>C"),
    "color-catalog": leading_facets("none"),
}
OPS = {
    "conversations_history": ["READ"],
    "conversations_add_message": ["BROADCAST"],
    "conversations_mark": ["METADATA"],
    "delete_thing": ["DELETE"],
}


def _call(tool: str, asset: str | None):
    return SimpleNamespace(tool=tool, asset=asset)


def test_leading_facets_handles_ties_and_absence():
    assert leading_facets("C>I>A") == frozenset({"C"})
    assert leading_facets("I≈C>A") == frozenset({"I", "C"})
    # "none" states no priority at all — the signal must abstain, not pick one.
    assert leading_facets("none") == frozenset()


def test_reading_a_confidentiality_led_asset_is_on_axis():
    band, reason = score_cia(_call("conversations_history", "exec-private"), AXES, OPS)
    assert band == ON_AXIS_BAND
    assert "violates C" in reason


def test_marking_read_on_an_integrity_led_asset_is_off_axis():
    # METADATA violates C; read-markers protects I -> the deviation does not matter.
    band, _ = score_cia(_call("conversations_mark", "read-markers"), AXES, OPS)
    assert band == OFF_AXIS_BAND


def test_delete_on_an_integrity_led_asset_is_on_axis():
    band, _ = score_cia(_call("delete_thing", "read-markers"), AXES, OPS)
    assert band == ON_AXIS_BAND


def test_signal_abstains_rather_than_guessing():
    # No asset, no axis, no op classification: each abstains with a stated reason.
    assert score_cia(_call("conversations_history", None), AXES, OPS)[0] == OFF_AXIS_BAND
    assert score_cia(_call("conversations_history", "color-catalog"), AXES, OPS)[0] == OFF_AXIS_BAND
    assert score_cia(_call("unknown_tool", "exec-private"), AXES, OPS)[0] == OFF_AXIS_BAND
    _, reason = score_cia(_call("unknown_tool", "exec-private"), AXES, OPS)
    assert "no atomic-op classification" in reason


def test_qualifier_withholds_escalation_off_axis_but_never_lowers_the_static_floor():
    from mcp_security.call_scoring.score import ScoredCall
    from mcp_security.dynamic.combine import score_session

    def call(tool: str, asset: str, static_band: str) -> ScoredCall:
        return ScoredCall(
            source="test", run_id="r1", index="1", tool=tool, category="c",
            persona="assistant", server="slack:real", asset=asset, tool_impact=3,
            sensitivity=4, score=10.0, band=static_band, scorable=True, reason="",
            param_band=None, param_top=None, param_multiplier=1.0,
            final_score=10.0, final_band=static_band, args_raw="{}",
        )

    # No baseline for this persona -> the baseline stage flags a deviation on both
    # calls. Only the on-axis one should be allowed to escalate.
    on_axis = call("conversations_history", "exec-private", "medium")
    off_axis = call("conversations_mark", "read-markers", "medium")
    verdicts = score_session([on_axis, off_axis], {}, asset_axes=AXES, tool_ops=OPS)

    assert verdicts[1].cia_band == OFF_AXIS_BAND
    assert verdicts[1].final_band == "medium"  # held at its static floor, not lowered
    assert verdicts[0].cia_band == ON_AXIS_BAND


def test_signal_is_off_by_default_so_existing_callers_are_unaffected():
    from mcp_security.call_scoring.score import ScoredCall
    from mcp_security.dynamic.combine import score_session

    one = ScoredCall(
        source="test", run_id="r1", index="1", tool="conversations_history", category="c",
        persona="assistant", server="slack:real", asset="exec-private", tool_impact=3,
        sensitivity=4, score=10.0, band="low", scorable=True, reason="",
        param_band=None, param_top=None, param_multiplier=1.0,
        final_score=10.0, final_band="low", args_raw="{}",
    )
    verdict = score_session([one], {})[0]
    assert verdict.cia_band is None
    assert verdict.cia_reason == ""
