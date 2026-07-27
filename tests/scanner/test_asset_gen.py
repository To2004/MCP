"""Tests for the standalone tool->asset generator (no LLM required)."""

from __future__ import annotations

from mcp_security.scanner import asset_gen
from mcp_security.scanner.asset_gen import (
    FEW_SHOT,
    GROUND_TRUTH,
    build_prompt,
    evaluate,
    generate_asset,
)


def test_few_shot_and_ground_truth_are_disjoint():
    # The prompt is "trained" on FEW_SHOT and checked on GROUND_TRUTH; a tool in
    # both would leak the answer into the eval.
    shot_names = {name for name, *_ in FEW_SHOT}
    truth_names = {name for name, *_ in GROUND_TRUTH}
    assert not shot_names & truth_names


def test_prompt_has_no_org_context():
    prompt = build_prompt("channels_list", "List channels in the workspace.")
    # The model must be told it knows nothing about the org...
    assert "NOTHING about the organization" in prompt
    # ...and the prompt must not leak the org's real asset/scope names.
    for leaked in ("exec-private", "hr-internal", "infra-config", "payments-service"):
        assert leaked not in prompt


def test_heuristic_maps_listing_tools_to_a_directory_asset():
    gen = generate_asset("channels_list", "List channels in the workspace.", use_llm=False)
    assert gen.asset_id is not None
    assert "channel" in gen.asset_id and "directory" in gen.asset_id
    assert gen.kind == "read-surface"


def test_heuristic_gives_utility_tools_no_asset():
    for name, desc in [
        ("get-current-time", "Get the current time."),
        ("list-colors", "List the available event color palette."),
    ]:
        gen = generate_asset(name, desc, use_llm=False)
        assert gen.asset_id is None, name
        assert gen.kind == "none"
        assert gen.to_asset_spec() is None


def test_heuristic_marks_write_tools_mutable():
    gen = generate_asset("create_event", "Create an event with attendees.", use_llm=False)
    assert gen.asset_id is not None and "event" in gen.asset_id
    assert gen.kind == "mutable-state"
    spec = gen.to_asset_spec()
    assert spec is not None and "source:generated" in spec.tags


def test_close_match_accepts_near_misses_only():
    close = asset_gen.close_match
    assert close("channel-directory", "channels-directory")  # plural variant
    assert close("channel-directory", "channel-catalog")  # catalog ~ directory synonym
    assert not close("channel-directory", "payment-ledger")
    assert close(None, None)
    assert not close(None, "channel-directory")


def test_evaluate_runs_offline_and_reports_every_tool():
    report = evaluate(use_llm=False)
    assert report["n"] == len(GROUND_TRUTH)
    assert {r["tool"] for r in report["results"]} == {name for name, *_ in GROUND_TRUTH}
    # The utility tool must be matched by generating no asset for it.
    colors = next(r for r in report["results"] if r["tool"] == "list-colors")
    assert colors["generated"] is None and colors["match"]


def test_augment_homes_uncovered_tools_without_duplicating_curated_assets():
    from mcp_security.scanner.scan import augment_with_generated_assets
    from mcp_security.static_scoring.registry import load_slack_registry

    registry = load_slack_registry()
    before = {a.asset_id for a in registry.assets}
    added = augment_with_generated_assets(registry, use_llm=False)
    after = {a.asset_id for a in registry.assets}
    # Slack's curated assets already cover every tool (possibly under a close
    # name), so augmentation must not duplicate them wholesale.
    assert added == len(after - before)
    for new_id in after - before:
        assert not any(asset_gen.close_match(new_id, old) for old in before), (
            f"{new_id} duplicates a curated asset"
        )
    # Generated assets are marked so a scan can be audited later.
    generated = [a for a in registry.assets if "source:generated" in a.tags]
    assert len(generated) == added
