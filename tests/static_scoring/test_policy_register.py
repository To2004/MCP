"""Tests for the policy asset register and the v5 static/LLM impact hand-off."""

from __future__ import annotations

import pytest

from mcp_security.static_scoring import server_policies as sp
from mcp_security.static_scoring.pipeline import (
    STATIC_IMPACT_MIN_CONFIDENCE,
    StaticScorer,
)
from mcp_security.static_scoring.registry import AssetSpec, ServerRegistry, ToolSpec

REGISTER = """### demo

**Tier: M** · `demo:server` · 2 tools · policy-only disclosure

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `secrets` | The credential store | `read_file`, `write_file` | `hub`, `self-sufficient` | C>I>A |
| `listing` | Names only | `list_dir` | `metadata-only` | C>I>A |
| `orphan` | Nothing reaches it | — | — | I>A>C |

**Asset recognition rules.** **Default: Confidential.**
"""


def test_register_parses_ids_tools_and_flags():
    rows = sp.parse_asset_register(REGISTER)
    assert [row.asset_id for row in rows] == ["secrets", "listing", "orphan"]
    assert rows[0].tools == ("read_file", "write_file")
    assert rows[0].flags == ("hub", "self-sufficient")  # cell order is preserved
    assert rows[0].cia == "C>I>A"
    # An em-dash Tools cell is a statement, not a parse error: nothing reaches it.
    assert rows[2].tools == ()
    assert rows[2].flags == ()


def test_register_rejects_an_unknown_flag():
    broken = REGISTER.replace("`hub`, `self-sufficient`", "`crown-jewel`")
    with pytest.raises(sp.PolicyRegisterError, match="unknown flag"):
        sp.parse_asset_register(broken)


def test_register_rejects_a_duplicate_asset():
    dupe = REGISTER.replace("| `orphan` |", "| `secrets` |")
    with pytest.raises(sp.PolicyRegisterError, match="duplicate"):
        sp.parse_asset_register(dupe)


def test_missing_register_raises():
    with pytest.raises(sp.PolicyRegisterError, match="no '\\| Asset \\| Description"):
        sp.parse_asset_register("### demo\n\nprose only, no table\n")


def test_a_sensitivity_table_in_a_policy_is_refused():
    leaked = REGISTER + "\n| Asset | Sens. | Why |\n|---|---|---|\n| `secrets` | 5 | key |\n"
    with pytest.raises(sp.PolicyNumbersError, match="states adverse impact"):
        sp.assert_no_sensitivity_numbers(leaked, server="demo:server")


def test_tool_coverage_helpers():
    rows = sp.parse_asset_register(REGISTER)
    assert sp.unmapped_tools(rows, ["read_file", "write_file", "list_dir", "ping"]) == ["ping"]
    assert sp.unknown_register_tools(rows, ["read_file", "write_file"]) == ["list_dir"]


# --- the v5 impact hand-off -------------------------------------------------


def _scorer(tools: list[ToolSpec]) -> StaticScorer:
    """A v5 scorer over a minimal registry, with the LLM disabled."""
    registry = ServerRegistry(
        server="demo:server",
        kind="demo",
        tools=tools,
        assets=[AssetSpec("secrets", "the credential store")],
        description="**Data classification policy.** Restricted: credentials.",
    )
    return StaticScorer(registry, use_llm=False, impact_mode="five_level_v2_v5")


def test_ladder_answers_when_a_verb_fired():
    tool = ToolSpec("delete_file", "Delete a file from the store.")
    scorer = _scorer([tool])
    impacts = scorer.score_tools()
    assert impacts["delete_file"] == 5
    assert scorer._impact_source["delete_file"] == "static_ladder"
    assert scorer._static_impacts["delete_file"]["source"] == "static_ladder"


def test_ladder_abstains_when_no_verb_matched():
    # A declaration with no ladder verb at all: the rules do not know, so v5 hands
    # the tool to the model instead of scoring it from a default.
    tool = ToolSpec("frobnicate", "Applies the configured transformation.")
    verdict_confidence = 0.35  # what static_impact reports for the no-evidence branch
    assert verdict_confidence < STATIC_IMPACT_MIN_CONFIDENCE
    scorer = _scorer([tool])
    scorer.score_tools()
    assert scorer._impact_source["frobnicate"] == "llm_fallback"
    record = scorer._static_impacts["frobnicate"]
    assert record["abstained"] is True
    assert record["static_would_have_said"] == 3  # the default it declined to use


def test_v5r_drops_the_behavioral_baseline():
    # The baseline is a runtime primitive — no static cell multiplies it, and a
    # deviation is only measurable against an observed call.
    registry = ServerRegistry(
        server="demo:server",
        kind="demo",
        tools=[ToolSpec("read_file", "Read a file.")],
        assets=[AssetSpec("secrets", "the credential store")],
        apps={"expected-use": "read one file at a time"},
        description="**Data classification policy.** Restricted: credentials.",
    )
    v5r = StaticScorer(registry, use_llm=False, impact_mode="five_level_v2_v5r")
    assert v5r.build_baselines() == {}
    # ...while the arm it was branched from still builds one.
    v5 = StaticScorer(registry, use_llm=False, impact_mode="five_level_v2_v5")
    assert set(v5.build_baselines()) == {"expected-use"}


def test_v4_static_mode_never_abstains():
    # The v4 arm has no fallback: the ladder answers every tool, default included.
    # It is a profile-sensitivity mode, so its description carries the org's table.
    registry = ServerRegistry(
        server="demo:server",
        kind="demo",
        tools=[ToolSpec("frobnicate", "Applies the configured transformation.")],
        assets=[AssetSpec("secrets", "the credential store")],
        description="| Asset | Sens. | Why |\n|---|---|---|\n| `secrets` | 5 | key material |\n",
    )
    scorer = StaticScorer(registry, use_llm=False, impact_mode="five_level_v2_v4_static")
    assert scorer.score_tools()["frobnicate"] == 3
    assert scorer._impact_source["frobnicate"] == "static_ladder"


# --- the v5r prompt set must be complete ------------------------------------


def test_every_prompt_the_v5r_path_references_exists():
    """A missing template only surfaces mid-scan, so assert the set up front.

    Regression guard: a slice-based edit to `prompts.py` once deleted
    `ASSET_TASK_POLICY_V5R` while rewriting a neighbouring constant. Nothing in
    the suite touched the sensitivity prompt, so 507 tests passed and the failure
    waited for the next GPU run.
    """
    from mcp_security.static_scoring import prompts

    required = (
        "DOMAIN_INFERENCE_SYSTEM_V5R",
        "DOMAIN_INFERENCE_USER_V5R",
        "TOOL_IMPACT_TASK_V5R",
        "ASSET_TASK_POLICY_V5R",
        "ASSET_USER_POLICY",
        "BLAST_TASK_V5R",
        "BLAST_TASK_V5R_FLOORED",
        "BLAST_USER_V5R",
        "_PROPOSER_BASE_DESC",
    )
    missing = [name for name in required if not hasattr(prompts, name)]
    assert not missing, f"v5r references prompts that do not exist: {missing}"


def test_v5r_prompt_templates_have_the_placeholders_their_callers_format():
    from mcp_security.static_scoring import prompts

    assert "{tools_json}" in prompts.DOMAIN_INFERENCE_USER_V5R
    assert "{tool_json}" in prompts.TOOL_IMPACT_TASK_V5R
    assert "{asset_json}" in prompts.ASSET_USER_POLICY
    for field in ("{tool_json}", "{asset_json}", "{tool_impact}", "{asset_sensitivity}",
                  "{peer_tools}", "{peer_assets}"):
        assert field in prompts.BLAST_USER_V5R, field


def test_escape_routes_live_in_blast_not_in_tool_impact():
    """The register's flags are a REACH question, so they belong to blast alone."""
    from mcp_security.static_scoring import prompts

    impact = prompts.TOOL_IMPACT_TASK_V5R.lower()
    for term in ("hub", "population", "self-sufficient", "flag", "register"):
        assert term not in impact, f"tool impact must not mention {term!r}"
    blast = prompts.BLAST_TASK_V5R.lower()
    for term in ("hub", "population", "self-sufficient", "register"):
        assert term in blast, f"blast should sanction tier 5 via {term!r}"


def test_blast_grants_self_sufficient_its_own_route():
    """`self-sufficient` is a CONTENT property; `population` is a COVERAGE one.

    Sharing one route let a single post on a `self-sufficient` asset claim tier 5.
    """
    from mcp_security.static_scoring import prompts

    blast = prompts.BLAST_TASK_V5R
    self_sufficient_line = next(
        line for line in blast.splitlines() if "self-sufficient" in line and "(b)" in line
    )
    population_line = next(
        line for line in blast.splitlines() if "population" in line and "(c)" in line
    )
    assert "population" not in self_sufficient_line
    assert "self-sufficient" not in population_line


def test_every_blast_escape_route_is_reportable():
    """A route the model cannot name in its answer is a route it cannot use.

    Regression guard: adding a fourth route (`irreversible-total`) without widening
    the return schema left `escape` accepting only `a|b|c|none`.
    """
    import re

    from mcp_security.static_scoring import prompts

    routes = {letter for letter, _ in re.findall(r"\((\w)\) (\w[\w-]*)", prompts.BLAST_TASK_V5R)}
    allowed = set(re.search(r'"escape": "([^"]+)"', prompts.BLAST_USER_V5R).group(1).split("|"))
    assert routes <= allowed, f"routes {sorted(routes - allowed)} cannot be reported"
    assert "none" in allowed
