"""The runtime breadth factor: how an omitted argument is read, and how ramps combine.

``scripts/dynamic_design/dynamic_v2.py`` is the implemented runtime layer. These pin the
decisions that are easy to break silently — an omission rule that quietly changes turns
into either a suppressed signal or a false one, with no error either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "dynamic_design"))

from dynamic_v2 import (  # noqa: E402
    B_MAX,
    B_MIN,
    L_MAX,
    L_MIN,
    MIN_HISTORY,
    BreadthScorer,
    parse_quantity,
    span_of,
)


def _spec(**overrides: object) -> dict:
    # breadth 1 = full weight, so tests of the ramp itself are not confounded by weighting.
    entry = {"name": "x", "kind": "magnitude", "ceiling": None, "parse": None,
             "default": None, "breadth": 5}
    entry.update(overrides)
    return entry


def _scorer(**args: dict) -> BreadthScorer:
    return BreadthScorer({"s": {"t": {name: _spec(name=name, **over)
                                      for name, over in args.items()}}})


def _warm(scorer: BreadthScorer, name: str, values: list[float]) -> None:
    for value in values:
        scorer.observe("s", "t", {name: value})


VARIED = [1, 5, 10, 25, 50, 75, 100] * 6  # 42 observations, Q1=5 Q3=75


# --------------------------------------------------------------------------- omission


def test_declared_default_is_substituted_when_omitted() -> None:
    """The server applies its default, so the call really did request that value."""
    scorer = _scorer(a={}, b={"default": 30})
    _warm(scorer, "a", VARIED)
    _warm(scorer, "b", VARIED)
    _, reasons = scorer.breadth_factor("s", "t", {"a": 10})
    assert any("b=30" in r and "default" in r for r in reasons)


def test_omitted_with_no_default_earns_no_discount_once_the_input_is_in_use() -> None:
    """Nobody bounded it, so the call is treated as the high end of normal: no discount."""
    scorer = _scorer(a={})
    _warm(scorer, "a", VARIED)
    assert scorer.breadth_factor("s", "t", {})[0] == pytest.approx(1.0)
    assert scorer.breadth_factor("s", "t", {"a": 1})[0] < 1.0


def test_omitted_argument_nobody_uses_is_ignored() -> None:
    """With no observations there is no Q3 to impute, and no basis to penalise the call.

    Imputing here would charge every call for an argument this deployment never passes.
    """
    scorer = _scorer(a={}, never={})
    _warm(scorer, "a", VARIED)
    _, reasons = scorer.breadth_factor("s", "t", {"a": 10})
    assert not any("never" in r for r in reasons), "unused and omitted contributes nothing"


def test_imputed_values_never_enter_the_reference() -> None:
    """Otherwise the reference learns from its own assumptions and drifts upward."""
    scorer = _scorer(a={})
    _warm(scorer, "a", VARIED)
    before = list(scorer.history[("s", "t", "a")])
    scorer.breadth_factor("s", "t", {})  # `a` omitted -> imputed
    assert scorer.history[("s", "t", "a")] == before


def test_applied_defaults_do_enter_the_reference() -> None:
    """A call that omits an argument really did request the default, so it is an observation."""
    scorer = _scorer(a={"default": 42})
    _warm(scorer, "a", VARIED)
    before = len(scorer.history[("s", "t", "a")])
    scorer.breadth_factor("s", "t", {})
    assert len(scorer.history[("s", "t", "a")]) == before + 1


# ------------------------------------------------------------------- breadth factor B


def _b(scorer: BreadthScorer, args: dict) -> float:
    return scorer.breadth_factor("s", "t", args)[0]


def test_too_little_history_earns_no_discount() -> None:
    scorer = _scorer(a={})
    _warm(scorer, "a", [10] * (MIN_HISTORY - 1))
    assert _b(scorer, {"a": 1}) == 1.0


def test_a_flat_sample_earns_no_discount() -> None:
    """Every observed value identical: nothing to grade against, so nothing is earned."""
    scorer = _scorer(a={})
    _warm(scorer, "a", [10] * 40)
    assert _b(scorer, {"a": 1}) == 1.0


def test_the_interquartile_range_is_neutral_and_both_tails_move() -> None:
    """Between the quartiles is this deployment's normal; either tail is a departure."""
    scorer = _scorer(a={})
    _warm(scorer, "a", VARIED)                      # Q1 = 5, Q3 = 75, upper fence 180
    assert _b(scorer, {"a": 5}) == pytest.approx(1.0), "at Q1"
    assert _b(scorer, {"a": 50}) == pytest.approx(1.0), "mid-range"
    assert _b(scorer, {"a": 75}) == pytest.approx(1.0), "at Q3"
    assert _b(scorer, {"a": 1}) < 1.0, "below Q1 discounts"
    assert _b(scorer, {"a": 150}) > 1.0, "above Q3 escalates"


def test_b_is_monotone_and_saturates_at_both_ends() -> None:
    """A one-sided B left 93.6% of real calls on exactly 1.0, so widening was invisible.

    Discount-only rested on blast_radius already pricing the worst one call can do. That
    prices the tool's *capability*, judged from a schema; what this deployment actually
    asks for is a different fact, and only the runtime has it.
    """
    scorer = _scorer(a={})
    _warm(scorer, "a", VARIED)                      # Q1 = 5, Q3 = 75, upper fence 180
    scores = [_b(scorer, {"a": v}) for v in (1, 2, 4, 5, 75, 100, 150, 180, 10**6)]
    assert scores == sorted(scores), "monotone in the quantity"
    assert scores[0] == pytest.approx(B_MIN, abs=0.15), "the narrowest ever seen earns most"
    assert scores[-1] == pytest.approx(B_MAX), "beyond the fence saturates, never runs away"
    assert _b(scorer, {"a": 10**6}) == _b(scorer, {"a": 500}), "bounded above the fence"


def test_the_most_alarming_argument_decides() -> None:
    """One runaway quantity is enough; a call wide in any dimension is not a narrow one."""
    scorer = _scorer(a={}, b={})
    _warm(scorer, "a", VARIED)
    _warm(scorer, "b", VARIED)
    assert _b(scorer, {"a": 1, "b": 1}) < 1.0, "narrow throughout"
    assert _b(scorer, {"a": 1, "b": 50}) == pytest.approx(1.0), "one ordinary cancels it"
    assert _b(scorer, {"a": 1, "b": 150}) > 1.0, "one wide argument escalates the whole call"


def test_a_peripheral_argument_counts_less_than_a_central_one() -> None:
    """Weighting is relative to the most central argument a quantity can be READ from.

    It used to be relative to the most central argument of any kind. That degenerates:
    every tool names its asset, so the reference was breadth 5 on 17 of 17 GitHub tools
    and always an identifier with no readable quantity, while the measurable arguments are
    breadth 3. The ratio was a constant 0.50 almost everywhere -- a flat halving of every
    signal the runtime can read, costing a third of the deviation it was meant to shape.
    """
    def narrow(level: int) -> float:
        scorer = BreadthScorer({"s": {"t": {
            "a": _spec(name="a", breadth=level),
            "other": _spec(name="other", breadth=5)}}})
        _warm(scorer, "a", VARIED)
        _warm(scorer, "other", VARIED)
        # Both narrow: with one ordinary argument, max() would cancel the discount
        # entirely and hide the weighting this test is about.
        return scorer.breadth_factor("s", "t", {"a": 1, "other": 1})[0]

    assert narrow(5) < narrow(3), "the more central the argument, the more its value counts"


def test_an_unreadable_identifier_does_not_set_the_reference() -> None:
    """An argument no quantity can be read from can never carry a deviation, so it must
    not decide how much the ones that can are worth."""
    scorer = BreadthScorer({"s": {"t": {
        "a": _spec(name="a", breadth=3),
        "names_it": _spec(name="names_it", kind="none", breadth=5)}}})
    _warm(scorer, "a", VARIED)
    assert scorer.breadth_factor("s", "t", {"a": 1})[0] == pytest.approx(B_MIN)


# ---------------------------------------------------------------- likelihood factor L


def test_an_unused_tool_raises_risk_and_a_dominant_one_lowers_it() -> None:
    scorer = BreadthScorer({"s": {"t": {"a": _spec(name="a")}, "b": {}, "c": {},
                                  "rare": {}}})
    for _ in range(400):
        scorer.observe("s", "t", {"a": 10})
    for _ in range(40):
        scorer.observe("s", "b", {})
        scorer.observe("s", "c", {})
    dominant, _ = scorer.likelihood_factor("s", "t")
    unused, _ = scorer.likelihood_factor("s", "rare")
    assert dominant < 1.0 < unused
    assert dominant >= L_MIN and unused <= L_MAX


def test_a_typical_tool_sits_at_one() -> None:
    """The neutral point is the median tool this deployment calls, so ordinary is 1.0.

    Anchoring on an even split over the whole catalog made every tool a deployment
    actually uses look common, so no call could ever score 1.0.
    """
    scorer = BreadthScorer({"s": {f"t{i}": {} for i in range(6)}})
    for i in range(6):
        for _ in range(50):
            scorer.observe("s", f"t{i}", {})
    factor, _ = scorer.likelihood_factor("s", "t3")
    assert factor == pytest.approx(1.0, abs=0.02)


def test_the_discount_side_is_tighter_than_the_escalation_side() -> None:
    """Commonness exonerating is the failure mode with history behind it."""
    assert (1.0 - L_MIN) < (L_MAX - 1.0)


# ------------------------------------------------------------------------ extraction


def test_quantity_is_read_from_the_value_shape_not_the_label() -> None:
    """A label disagreement must not silently discard a quantity."""
    assert parse_quantity([1, 2, 3], "magnitude", None) == 3.0
    assert parse_quantity(50, "count", None) == 50.0
    assert parse_quantity("30d", "magnitude", None) == 30.0
    assert parse_quantity("a,b,c", "count", "split:,") == 3.0


def test_an_identifier_like_value_yields_nothing() -> None:
    assert parse_quantity("primary", "magnitude", None) is None
    assert parse_quantity(True, "magnitude", None) is None


def test_a_span_needs_both_endpoints() -> None:
    args = {"timeMin": "2026-01-01T00:00:00Z", "timeMax": "2026-01-08T00:00:00Z"}
    assert span_of(args, ["timeMin", "timeMax"]) == pytest.approx(7.0)
    assert span_of({"timeMin": args["timeMin"]}, ["timeMin", "timeMax"]) is None


def test_the_two_factors_are_independent() -> None:
    """B never reads tool counts and L never reads argument values."""
    scorer = _scorer(a={})
    _warm(scorer, "a", VARIED)
    before = scorer.breadth_factor("s", "t", {"a": 1})[0]
    for _ in range(500):
        scorer.tool_calls["s"]["t"] += 1
    assert scorer.breadth_factor("s", "t", {"a": 1})[0] == pytest.approx(before)


def test_an_argument_that_cannot_be_narrow_does_not_pin_the_whole_call() -> None:
    """A page number is 1 in most calls, so its Q1 sits on its own minimum.

    Such an argument can never fall below Q1, so it can never signal narrowness. Because
    B takes the LEAST discount any argument justifies, counting it as "ordinary" pinned B
    to 1.0 for every call on the tool, silently disabling the factor on real traffic.
    """
    scorer = _scorer(page={}, per_page={})
    _warm(scorer, "page", [1] * 34 + [2] * 6 + [3] * 2)   # Q1 == min == 1
    _warm(scorer, "per_page", VARIED)                      # Q1 = 5, Q3 = 75
    assert _b(scorer, {"page": 1, "per_page": 1}) < 1.0, "per_page=1 must still be earned"
    _, reasons = scorer.breadth_factor("s", "t", {"page": 1, "per_page": 1})
    assert not any(r.startswith("page=") for r in reasons), "page contributes nothing"


def test_a_dominant_default_does_not_disqualify_an_argument() -> None:
    """Q3 must not gate B: a popular value collapses the IQR without removing variation.

    ``per_page`` is the API default in most calls, so Q1 and Q3 both land on it while the
    sample still spans its whole legal range. An earlier Q3 <= Q1 test read that as "no
    variation" and dropped the argument, then re-admitted it as soon as Q3 crossed --
    identical calls scored 0.771 or 0.908 depending only on when they arrived.
    """
    scorer = _scorer(per_page={})
    _warm(scorer, "per_page", [1] * 4 + [5] * 5 + [10] * 9 + [30] * 58 + [50] * 10)
    assert _b(scorer, {"per_page": 1}) < 1.0, "below Q1 must still be earned"
    assert _b(scorer, {"per_page": 30}) == pytest.approx(1.0), "at Q1 is ordinary"


# ------------------------------------------------------------------------- cold start


def test_an_empty_deployment_scores_exactly_one() -> None:
    """With no history the runtime must abstain, leaving the static cell untouched.

    R = cell x B x L, so D = 1.0 means "the design-time score stands". Inventing a runtime
    adjustment from no evidence is the one answer that cannot be right.
    """
    assert _scorer(a={}).score("s", "t", {"a": 500})[0] == pytest.approx(1.0)
    assert _scorer(a={}).score("s", "never_seen", {})[0] == pytest.approx(1.0)

    # Scoring a call also registers it, so the next call is no longer on an empty
    # deployment. It must still be indistinguishable from 1.0 rather than exactly it.
    scorer = _scorer(a={})
    for _ in range(5):
        assert abs(scorer.score("s", "t", {"a": 500})[0] - 1.0) < 0.01


def test_likelihood_is_held_back_until_there_is_a_distribution() -> None:
    """Rarity is a claim about a distribution, and a handful of calls is not one.

    Unshrunk, a fresh deployment called a tool "0.79x the median" and escalated 6.4% on
    the evidence of nine calls. B already refuses to grade an argument below MIN_HISTORY;
    this is the same guard for L.
    """
    scorer = BreadthScorer({"s": {f"t{i}": {} for i in range(10)}})
    for _ in range(3):
        scorer.observe("s", "t0", {})
    early, why = scorer.likelihood_factor("s", "t9")
    assert abs(early - 1.0) < 0.05, "a handful of calls must not move the score"
    assert "held back" in why

    for _ in range(4_000):
        scorer.observe("s", "t0", {})
    late, _ = scorer.likelihood_factor("s", "t9")
    assert late > 1.2, "with real history an unused tool must still escalate"


def test_a_dominant_default_still_permits_escalation() -> None:
    """Q1 == Q3 collapses the Tukey fence onto Q3, leaving nothing above it to escalate at.

    per_page is the API default in 58% of real calls and page is 1 in 79%, so this is the
    common case, not the corner one. Before the fallback anchor these two arguments were
    the only widening deviations still invisible after B was made two-sided.
    """
    scorer = _scorer(a={})
    _warm(scorer, "a", [1] * 4 + [5] * 5 + [10] * 9 + [30] * 58 + [100] * 14)
    assert _b(scorer, {"a": 30}) == pytest.approx(1.0), "the default is ordinary"
    assert _b(scorer, {"a": 100}) == pytest.approx(1.0), "the largest value ever used is too"
    assert _b(scorer, {"a": 10_000}) > 1.0, "beyond anything ever asked for escalates"
    assert _b(scorer, {"a": 10**6}) == pytest.approx(B_MAX), "and saturates"
