"""Design v5 in Batch 0: its config, its interfaces, the legacy fixes, and score / commit.

Every test runs on the INF-1 stream (``golden_stream.py``), which already pins v1-v4.
"""

from __future__ import annotations

import copy
import functools
import json
import pickle
from dataclasses import fields, replace

import pytest

from mcp_security.behaviour import (
    DESIGNS,
    LEGACY_DESIGNS,
    BehaviourConfig,
    BehaviourEngine,
    Message,
    Reply,
    Verdict,
    alerting_dimensions,
    budget_share,
    dimension_groups,
    multiplier,
    replace_config,
    v5_switches_off,
    with_alert_alpha,
)
from mcp_security.behaviour import engine as engine_module
from mcp_security.behaviour.engine import (
    ALERT_LINE,
    ALL_DESIGN_FIELDS,
    APP_CLIENT,
    ASSET,
    BURST,
    CALLS_LAST_HOUR,
    CLIENT_INFO,
    DERIVED,
    DERIVED_FIELDS,
    DESIGN_VALUES,
    MANY_ASSETS,
    MAX_MULTIPLIER,
    MIN_MULTIPLIER,
    MODERN_ERA,
    PROTOCOL_SKIP,
    PUBLIC,
    READ_VOLUME,
    REJECTED,
    RED_FLAGS,
    REQUEST_TOO_BIG,
    SEQUENCE,
    SPEC_ALTERNATIVES,
    TOOL,
    TYPICAL_CADENCE,
    TYPICAL_FOOTPRINT,
    WATCH_ONLY,
    alert_multiplier,
)
from mcp_security.behaviour.memory import FirstUses
from mcp_security.behaviour.policy import (
    MAX_GROWTH,
    RELEARN_DAYS,
    config_from_json,
    config_to_json,
)
from tests.behaviour.golden_stream import DAY_S, POLICY, build_stream, golden_config

V5_ALERT_LINE = 4.69  # the 1% line, x4.69 (spec 2.4)
LINE_TOLERANCE = 0.005
CADENCE_SHARE_V5 = 1 / 21  # a third split over 7 Cadence dimensions (decision D1)
CADENCE_SHARE_NO_READ_VOLUME = 1 / 18  # ... over 6 without Read volume
SHARE_1_12 = 1 / 12  # Footprint (4 dimensions) and Red Flags (4 that can alert)
V5_DIMENSIONS, V4_DIMENSIONS = 16, 15
CHECK_EVERY = 61  # messages between the checks that score must not learn
ORG_DISCOUNT_DAYS = 7
SWEEP_ALPHAS = {0.025: 4.29, 0.05: 3.73}  # EV-21's lines (spec 2.4)
PLATFORM = (("github-actions", "4.148.0.0/14"), ("copilot", "2a01:111::/32"))


@pytest.fixture(scope="module")
def stream() -> list[Message]:
    return build_stream()


def _v5(**overrides: object) -> BehaviourConfig:
    return BehaviourConfig(design="v5", **(POLICY | overrides))


def _v5_off(**overrides: object) -> BehaviourConfig:
    return v5_switches_off(**(POLICY | overrides))


def _config(design: str) -> BehaviourConfig:
    return _v5() if design == "v5" else golden_config(design)


def _verdicts(config: BehaviourConfig, messages: list[Message]) -> list[Verdict]:
    engine = BehaviourEngine(config)
    return [engine.observe(m) for m in messages]


RUNS = {
    **{design: functools.partial(_config, design) for design in DESIGNS},
    "v5_off": _v5_off,
    "v5_floor": functools.partial(_v5_off, min_multiplier=1.0),  # PS8 alone
}


@functools.cache
def _run(name: str) -> tuple[list[Verdict], BehaviourEngine]:
    """The verdicts of one ``RUNS`` config over the whole stream, and the engine after it
    (shared by the tests: read it, never feed it)."""
    engine = BehaviourEngine(RUNS[name]())
    return [engine.observe(m) for m in build_stream()], engine


def _state(engine: BehaviourEngine) -> str:
    """Everything the engine learned, open sessions included, as comparable text."""
    sessions = {k: repr(v) for k, v in engine.sessions.items()}
    return json.dumps([engine.snapshot(), list(sessions.items())], sort_keys=True, default=str)


# ── the design and its config ──────────────────────────────────────────────────────────────
def test_v5_is_a_design_that_builds_on_v4() -> None:
    assert DESIGNS == (*LEGACY_DESIGNS, "v5")
    v5, v4 = BehaviourEngine(_v5()), BehaviourEngine(golden_config("v4"))
    assert (v5.v2, v5.v3, v5.v4, v5.v5) == (True, True, True, True)
    assert (v4.v4, v4.v5) == (True, False)


def test_a_v5_config_takes_the_spec_defaults() -> None:
    config = BehaviourConfig(design="v5")
    for name, (_, v5_value) in DESIGN_VALUES.items():
        if v5_value != DERIVED:
            assert getattr(config, name) == v5_value, name
    assert config.alert_floor_rate == config.alert_alpha == pytest.approx(0.01)
    assert config.alert_line == pytest.approx(V5_ALERT_LINE, abs=LINE_TOLERANCE)
    assert (config.legacy_fixes, config.min_multiplier, config.footprint_alerts) == (
        True,
        1.0,
        True,
    )
    assert config.reply_volume and config.calibration == "commonness"


@pytest.mark.parametrize("design", LEGACY_DESIGNS)
def test_a_v1_to_v4_config_keeps_todays_values(design: str) -> None:
    config = BehaviourConfig(design=design)
    for name, (legacy, _) in DESIGN_VALUES.items():
        assert getattr(config, name) == legacy, name
    assert config.alert_line == ALERT_LINE and config.min_multiplier == MIN_MULTIPLIER


def test_a_switch_set_off_on_v5_stays_off() -> None:
    config = _v5(usual_quantile=None, surge_min=None, legacy_fixes=False, min_multiplier=0.7)
    assert (config.usual_quantile, config.surge_min, config.legacy_fixes) == (None, None, False)
    assert config.min_multiplier == MIN_MULTIPLIER
    assert all(getattr(_v5_off(), name) == legacy for name, (legacy, _) in DESIGN_VALUES.items())


def test_a_v5_switch_on_a_v4_config_is_an_error_but_the_legacy_fixes_are_allowed() -> None:
    with pytest.raises(ValueError, match="calibration is a v5 switch"):
        BehaviourConfig(design="v4", calibration="commonness")
    assert BehaviourConfig(design="v4", legacy_fixes=True).legacy_fixes  # "v4.1"


@pytest.mark.parametrize(
    "bad",
    [
        {"calibration": "median"},
        {"record_reference": "everyone"},
        {"route_zone": "Mars/Olympus_Mons"},
        {"day_start_hour": 24.0},
        {"budget_shares": (0.5, 0.5, 0.5)},
        {"floor_budget": (0.003,)},
        {"min_multiplier": 1.5},
        {"alert_alpha": 0.0},
        {"weekend_days": (7,)},
        {"scored_methods": ()},
        {"scored_methods": ("bogus/method",)},
        {"alert_line": -1.0},
        {"alert_line": 3.0},  # not the line at alpha = 1%
        {"alert_floor_rate": 0.05},  # not alpha
        {"alert_alpha": -0.5},
        {"reply_unit_bytes": 0},
        {"usual_quantile": 7.0},
        {"watch_cap": -3},
        {"watch_floor_rate": 1.5},
        {"surge_min": -2},
        {"surge_factor": 0.5},
        {"idle_gap_s": -1},
        {"session_ttl_s": -1},
        {"score_budget_ms": 0},
        {"max_values_per_kind": 0},
        {"max_sessions_per_caller": 2.5},
        {"route_warmup_days": -5},
        {"org_discount_max_static": 9},
        {"floor_budget": (0.003, 2.0)},
        {"footprint_alerts": "no"},
        {"legacy_fixes": "yes"},
        {"client_source": "token"},
        {"shared_networks": (("github-actions", "not-a-cidr"),)},
        {"shared_networks": (("only-a-label",),)},
    ],
)
def test_a_v5_field_out_of_range_fails_fast(bad: dict) -> None:
    with pytest.raises(ValueError):
        BehaviourConfig(design="v5", **bad)


def test_a_v1_to_v4_config_needs_no_time_zone_database(monkeypatch) -> None:
    def no_database(name: str) -> None:
        raise ValueError(f"unknown time zone {name!r}")

    monkeypatch.setattr(engine_module, "zone", no_database)
    for design in LEGACY_DESIGNS:
        assert BehaviourConfig(design=design).route_zone == "UTC"
    with pytest.raises(ValueError, match="time zone"):
        BehaviourConfig(design="v5")


def test_the_alert_line_is_the_multiplier_at_the_alert_alpha() -> None:
    assert _v5().alert_line == pytest.approx(V5_ALERT_LINE, abs=LINE_TOLERANCE)
    assert _v5(alert_alpha=0.025).alert_line == pytest.approx(4.29, abs=LINE_TOLERANCE)
    assert alert_multiplier(0.01) == _v5().alert_line
    assert golden_config("v4").alert_line == _v5_off().alert_line == ALERT_LINE


# ── the alert line follows alpha (CAL-5) ─────────────────────────────────────────────────
def test_replace_cannot_leave_the_alert_line_stale() -> None:
    v5 = _v5()
    with pytest.raises(ValueError, match="follows alert_alpha"):
        replace(v5, alert_alpha=0.025)
    with pytest.raises(ValueError, match="follows alert_alpha"):
        replace(v5, max_multiplier=4.0)
    assert replace(v5, reply_volume=False).alert_line == v5.alert_line  # alpha unchanged


@pytest.mark.parametrize(("alpha", "line"), SWEEP_ALPHAS.items())
def test_with_alert_alpha_moves_the_line_and_the_floor_rate(alpha: float, line: float) -> None:
    swept = with_alert_alpha(_v5(), alpha)
    assert swept.alert_line == pytest.approx(line, abs=LINE_TOLERANCE)
    assert swept.alert_floor_rate == swept.alert_alpha == alpha
    bounded = replace_config(_v5(), max_multiplier=4.0)
    assert bounded.alert_line == alert_multiplier(0.01, 4.0)
    assert replace_config(golden_config("v4"), alert_line=3.5).alert_line == 3.5


def test_switches_off_with_alpha_on_takes_the_derived_line() -> None:
    assert (_v5_off().alert_line, _v5_off().alert_floor_rate) == (ALERT_LINE, None)
    on = _v5_off(alert_alpha=0.01)
    assert on.alert_line == alert_multiplier(0.01) == _v5().alert_line
    assert on.alert_floor_rate == 0.01


def test_an_explicit_alert_line_must_match_alpha_and_is_free_without_one() -> None:
    assert BehaviourConfig(design="v5", alert_line=alert_multiplier(0.01)) == BehaviourConfig(
        design="v5"
    )
    free = BehaviourConfig(design="v5", alert_alpha=None, alert_line=3.5)
    assert (free.alert_line, free.alert_floor_rate) == (3.5, None)


def test_a_v5_policy_file_stores_alpha_and_editing_it_moves_the_line() -> None:
    data = config_to_json(_v5())
    assert not DERIVED_FIELDS & set(data)
    data["alert_alpha"] = 0.025
    edited = config_from_json(data)
    assert edited.alert_line == pytest.approx(SWEEP_ALPHAS[0.025], abs=LINE_TOLERANCE)
    assert edited.alert_floor_rate == 0.025
    free = BehaviourConfig(design="v5", alert_alpha=None, alert_line=3.5)
    assert config_to_json(free)["alert_line"] == 3.5
    assert config_from_json(json.loads(json.dumps(config_to_json(free)))) == free


# ── dimensions, budget shares (CAL-3) and the other v5 switches ───────────────────────────
def test_read_volume_is_the_16th_dimension_in_v5_cadence_only() -> None:
    v4, v5 = dimension_groups("v4"), dimension_groups("v5")
    assert v5[TYPICAL_CADENCE] == (*v4[TYPICAL_CADENCE], READ_VOLUME)
    assert (v5[TYPICAL_FOOTPRINT], v5[RED_FLAGS]) == (v4[TYPICAL_FOOTPRINT], v4[RED_FLAGS])
    assert sum(map(len, v5.values())) == V5_DIMENSIONS
    assert sum(map(len, v4.values())) == V4_DIMENSIONS
    assert (1 / 3) / len(v5[TYPICAL_CADENCE]) == pytest.approx(CADENCE_SHARE_V5)
    for design in LEGACY_DESIGNS:
        assert READ_VOLUME not in {d for group in dimension_groups(design).values() for d in group}


def test_the_budget_shares_follow_the_alerting_dimensions() -> None:
    v5 = BehaviourConfig(design="v5")
    assert WATCH_ONLY == {PROTOCOL_SKIP}
    alerting = alerting_dimensions(v5)
    assert PROTOCOL_SKIP not in alerting[RED_FLAGS] and len(alerting[RED_FLAGS]) == 4
    assert budget_share(v5, CALLS_LAST_HOUR) == pytest.approx(CADENCE_SHARE_V5)
    assert budget_share(v5, READ_VOLUME) == pytest.approx(CADENCE_SHARE_V5)
    assert budget_share(v5, TOOL) == pytest.approx(SHARE_1_12)
    for flag in (BURST, MANY_ASSETS, REQUEST_TOO_BIG, SEQUENCE):
        assert budget_share(v5, flag) == pytest.approx(SHARE_1_12)
    assert budget_share(v5, PROTOCOL_SKIP) is None
    no_read_volume = replace(v5, reply_volume=False)
    assert budget_share(no_read_volume, CALLS_LAST_HOUR) == pytest.approx(
        CADENCE_SHARE_NO_READ_VOLUME
    )
    with pytest.raises(ValueError, match="does not score"):
        budget_share(no_read_volume, READ_VOLUME)
    watch_footprint = replace(v5, footprint_alerts=False)  # FP-1, D3 (b)
    assert alerting_dimensions(watch_footprint)[TYPICAL_FOOTPRINT] == ()
    assert budget_share(watch_footprint, TOOL) is None
    with pytest.raises(ValueError, match="no shares"):
        budget_share(golden_config("v4"), TOOL)


def test_the_revision_1_switches_are_v5_only_and_shared_networks_any_design() -> None:
    v5, v4 = BehaviourConfig(design="v5"), BehaviourConfig(design="v4")
    assert (v5.client_source, v4.client_source) == (APP_CLIENT, CLIENT_INFO)
    assert v5.multi_asset_breadth and v5.missing_client_counts
    assert not (v4.multi_asset_breadth or v4.missing_client_counts)
    with pytest.raises(ValueError, match="v5 switch"):
        BehaviourConfig(design="v4", multi_asset_breadth=True)
    assert "shared_networks" in ALL_DESIGN_FIELDS
    platform = BehaviourConfig(design="v4", shared_networks=PLATFORM)  # B10 on a v4 route
    assert config_to_json(platform)["shared_networks"] == PLATFORM
    read_back = config_from_json(json.loads(json.dumps(config_to_json(platform))))
    assert read_back == platform and read_back.shared_networks == PLATFORM
    assert "shared_networks" not in config_to_json(v4)  # INF-4: empty, so omitted


def test_the_spec_alternatives_are_valid_and_never_the_off_values() -> None:
    off = _v5_off()
    for name, value in SPEC_ALTERNATIVES.items():
        assert value != DESIGN_VALUES[name][0] and getattr(off, name) != value
        assert getattr(BehaviourConfig(design="v5", **{name: value}), name) == value


def test_the_deferred_relearn_switches_are_policy_constants() -> None:
    assert (RELEARN_DAYS, MAX_GROWTH) == (30, 1.25)
    assert not {"relearn_days", "max_growth"} & {f.name for f in fields(BehaviourConfig)}


# ── v5 with every switch off is v4 ────────────────────────────────────────────────────────
def test_v5_with_every_switch_off_gives_exactly_v4s_verdicts() -> None:
    (v4, v4_engine), (v5, v5_engine) = _run("v4"), _run("v5_off")
    assert v5 == v4
    assert {**v5_engine.snapshot(), "design": "v4"} == v4_engine.snapshot()


# ── the legacy fixes: v4 unchanged (INF-1), v5 fixed ──────────────────────────────────────
def test_e1_a_sessionless_guarded_call_is_raised_by_v4_and_not_evaluable_in_v5(stream) -> None:
    guarded = [
        i for i, m in enumerate(stream) if m.session is None and m.tool in POLICY["requires_before"]
    ]
    (v4, _), (v5, _) = _run("v4"), _run("v5")
    assert any(SEQUENCE in v4[i].scores for i in guarded)
    assert not any(SEQUENCE in v5[i].scores for i in guarded)


def test_e2_sessionless_calls_add_no_zero_minute_sessions_in_v5(stream) -> None:
    (_, v4), (_, v5) = _run("v4"), _run("v5")
    for agent in ("alice", "ci-bot", "dave"):
        calls = [m for m in stream if m.agent == agent and m.method == "tools/call"]
        assert v4.agents[agent].session_minutes.n == len(calls)
        assert v5.agents[agent].session_minutes.n == sum(1 for m in calls if m.session)


def test_rf9_one_agent_recorded_twice_counts_twice_in_v4_and_once_in_v5(stream) -> None:
    uses = FirstUses(ORG_DISCOUNT_DAYS * DAY_S)
    for ts, agent in ((1.0, "dave"), (2.0, "dave"), (3.0, "carol")):
        uses.add(("asset", "repo-shared"), ts, agent)
    assert uses.others(("asset", "repo-shared"), 9.0, "alice") == 3
    assert uses.others(("asset", "repo-shared"), 9.0, "alice", distinct=True) == 2
    # in the stream: alice is the third agent to start on repo-shared that week only in v4
    index = next(i for i, m in enumerate(stream) if m.agent == "alice" and m.asset == "repo-shared")
    v4, v5 = _run("v4")[0][index], _run("v5")[0][index]
    assert v4.scores[ASSET] == 0.5  # the org discount
    assert v5.scores[ASSET] > 0.5


# ── score and commit ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("design", DESIGNS)
def test_score_learns_nothing_and_agrees_with_observe(stream, design: str) -> None:
    engine = BehaviourEngine(_config(design))
    for index, message in enumerate(stream):
        if index % CHECK_EVERY == 0:
            before = _state(engine)
            first, second = engine.score(message), engine.score(message)
            assert first == second
            assert _state(engine) == before
            assert engine.observe(message) == first
        else:
            engine.observe(message)


@pytest.mark.parametrize("design", DESIGNS)
def test_score_then_commit_is_observe(stream, design: str) -> None:
    observed, engine = _run(design)
    split = BehaviourEngine(_config(design))
    for message, expected in zip(stream, observed):
        verdict = split.score(message)
        split.commit(message, verdict)
        assert verdict == expected
    assert _state(split) == _state(engine)


# ── the trace hook (EV-03) ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("design", ["v4", "v5"])
def test_a_trace_sees_each_message_once_and_changes_no_verdict(stream, design: str) -> None:
    seen: list[tuple[Message, Verdict]] = []
    traced = BehaviourEngine(_config(design), trace=lambda m, v: seen.append((m, v)))
    got = [traced.observe(m) for m in stream]
    assert got == _run(design)[0]
    assert seen == list(zip(stream, got))


def test_commit_traces_the_verdict_it_is_given(stream) -> None:
    seen: list[tuple[Message, Verdict]] = []
    engine = BehaviourEngine(golden_config("v4"), trace=lambda m, v: seen.append((m, v)))
    verdict = engine.score(stream[0])
    engine.commit(stream[0], verdict)
    assert seen == [(stream[0], verdict)]


@pytest.mark.parametrize("design", ["v4", "v5"])
def test_commit_without_a_verdict_is_traced_once_with_the_one_it_learned(
    stream, design: str
) -> None:
    seen: list[tuple[Message, Verdict]] = []
    traced = BehaviourEngine(_config(design), trace=lambda m, v: seen.append((m, v)))
    for message in stream[:400]:
        traced.commit(message)
    assert seen == list(zip(stream[:400], _run(design)[0][:400], strict=True))


@pytest.mark.parametrize("design", ["v4", "v5"])
def test_a_trace_sees_each_reply_once_and_changes_no_verdict(stream, design: str) -> None:
    seen: list[tuple[Message | Reply, Verdict]] = []
    traced = BehaviourEngine(_config(design), trace=lambda m, v: seen.append((m, v)))
    replies = []
    for message in stream[:400]:
        traced.observe(message)
        if message.method == "tools/call":
            reply = Reply(message.ts + 1, message.agent, message.method, message.tool, 2_000)
            replies.append((reply, traced.reply(reply)))
    assert [v for m, v in seen if isinstance(m, Message)] == _run(design)[0][:400]
    assert [(m, v) for m, v in seen if isinstance(m, Reply)] == replies
    assert len(seen) == 400 + len(replies)


# ── PS6 and EV-21 ─────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("design", ["v4", "v5"])
def test_a_verdict_carries_its_alert_and_runner_up(stream, design: str) -> None:
    config = _config(design)
    for verdict in _run(design)[0]:
        assert verdict.alert == (verdict.multiplier >= config.alert_line)
        if len(verdict.scores) < 2:
            assert (verdict.runner_up, verdict.runner_up_dimension) == (None, None)
            continue
        assert verdict.runner_up_dimension != verdict.strongest
        assert verdict.runner_up == verdict.scores[verdict.runner_up_dimension]
        assert verdict.runner_up == sorted(verdict.scores.values())[-2]


def test_the_module_curve_is_unchanged_for_its_callers() -> None:
    assert (multiplier(0.5), multiplier(1.0), multiplier(0.0)) == (1.0, 5.0, 0.7)
    for score in (0.0, 0.13, 0.49, 0.5, 0.77, 0.9, 1.0):
        top, bottom = MAX_MULTIPLIER ** (2 * score - 1), MIN_MULTIPLIER ** (1 - 2 * score)
        assert multiplier(score) == (top if score >= 0.5 else bottom)


def test_the_configured_bounds_set_the_curve(stream) -> None:
    bounded = replace(golden_config("v4"), max_multiplier=4.0, min_multiplier=0.8)
    for verdict in _verdicts(bounded, stream[:600]):
        if verdict.score is not None:
            assert verdict.multiplier == multiplier(verdict.score, 4.0, 0.8)


def test_v5_never_goes_below_one_and_matches_v4_at_or_above_one(stream) -> None:
    (v4, _), (floored, _) = _run("v4"), _run("v5_floor")
    assert [v.multiplier for v in floored] == [max(1.0, v.multiplier) for v in v4]
    assert min(v.multiplier for v in _run("v5")[0]) >= 1.0


# ── the Read volume stub and the inert message fields ─────────────────────────────────────
@pytest.mark.parametrize("design", DESIGNS)
def test_a_reply_is_a_neutral_no_op_that_never_raises(stream, design: str) -> None:
    engine = BehaviourEngine(_config(design))
    for message in stream[:300]:
        engine.observe(message)
    before = _state(engine)
    for reply in (
        Reply(stream[300].ts, "alice", "tools/call", "get_file", 6_000_000),
        Reply(-1.0, "", None, None, -5),
    ):
        verdict = engine.reply(reply)
        assert (verdict.multiplier, verdict.strongest, verdict.scores) == (1.0, None, {})
    assert _state(engine) == before


@pytest.mark.parametrize("design", DESIGNS)
def test_fold_is_a_stub_that_learns_nothing(stream, design: str) -> None:
    engine = BehaviourEngine(_config(design))
    for message in stream[:300]:
        engine.observe(message)
    before = _state(engine)
    assert engine.fold(stream[300].ts) is None and engine.fold(-1.0) is None
    assert _state(engine) == before


@pytest.mark.parametrize("design", LEGACY_DESIGNS)
def test_the_v5_message_fields_change_nothing_for_v1_to_v4(stream, design: str) -> None:
    extra = {
        "era": MODERN_ERA,
        "app": "claude-code",
        "client_family": "(none)",
        "zone": "Asia/Tokyo",
        "more_assets": ("repo-x99",),
        "exposure": PUBLIC,
        "static": 4.2,
        "arg_bytes": 77,
        "logical_call": "k1",
        "outcome": REJECTED,
        "owner": "someone-else",
    }
    assert set(extra) == {f.name for f in fields(Message)} - {
        "ts",
        "agent",
        "method",
        "session",
        "tool",
        "asset",
        "sensitivity",
        "operation",
        "address",
        "client",
        "size",
    }
    loaded = [replace(m, **extra) for m in stream]
    assert _verdicts(golden_config(design), loaded) == _run(design)[0]


def test_a_v5_config_survives_deepcopy_and_pickle() -> None:
    config = _v5(shared_networks=PLATFORM)
    assert copy.deepcopy(config) == config
    assert pickle.loads(pickle.dumps(config)) == config  # score() copies state by pickle
    assert {f.name for f in fields(config)} >= set(DESIGN_VALUES)
