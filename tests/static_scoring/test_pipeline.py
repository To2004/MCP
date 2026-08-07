"""Tests for the static (design-time) misuse-scoring pipeline.

The deterministic path must run fully offline and never under-score a
crown-jewel asset; the LLM path must be used when the model answers and override
the fallback. We stub the model rather than hitting Ollama.
"""

from __future__ import annotations

import pytest

import mcp_security.static_scoring.pipeline as pipeline_mod
from mcp_security.static_scoring import band_label, build_static_table
from mcp_security.static_scoring.fallback import asset_sensitivity, tool_impact
from mcp_security.static_scoring.registry import AssetSpec, ServerRegistry, ToolSpec


def _toy_registry() -> ServerRegistry:
    return ServerRegistry(
        server="toy",
        kind="sqlite",
        tools=[
            ToolSpec("read_query", "Run a SELECT.", read_only_hint=True),
            ToolSpec("write_query", "Run DELETE/UPDATE.", destructive_hint=True),
        ],
        assets=[
            AssetSpec("api_keys", "Table with columns: id, service, key", tags=("column:key",)),
            AssetSpec("publications", "Table with columns: id, title", tags=("column:title",)),
        ],
        apps={"portal": "reads publications"},
    )


# --- deterministic primitives ----------------------------------------------
def test_tool_impact_tiers():
    assert tool_impact(ToolSpec("read_file", "Read", read_only_hint=True))[0] == 1
    assert tool_impact(ToolSpec("edit_file", "Edit lines", destructive_hint=True))[0] == 2
    assert tool_impact(ToolSpec("delete_file", "Delete a file"))[0] == 3
    assert (
        tool_impact(ToolSpec("write_file", "Completely overwrite", destructive_hint=True))[0] == 3
    )


def test_asset_sensitivity_escalates_crown_jewels():
    # 'key' column is not an exact anchor, but the table name escalates it.
    sens, drivers, _ = asset_sensitivity(AssetSpec("api_keys", "service, key", tags=()))
    assert sens == 5
    assert drivers
    # A '.pem' file type is absent from FILETYPE_SENSITIVITY but must hit critical.
    assert asset_sensitivity(AssetSpec(".pem", "key file", tags=("ext:pem",)))[0] == 5


def test_band_label_is_deterministic_and_valid():
    # The band is a coarse label the DYNAMIC scorer consumes as the static floor;
    # its exact calibration is not the product, so we only check it is a valid,
    # reproducible function of the primitives (same inputs -> same band).
    for s in range(1, 6):
        for b in range(0, 6):
            for i in range(1, 4):
                band = band_label(s, b, i)
                assert band in {"low", "medium", "high", "critical"}
                assert band == band_label(s, b, i)


# --- full table (offline) ---------------------------------------------------
def test_offline_table_shape_and_formula():
    table = build_static_table(_toy_registry(), use_llm=False, version="static-test")
    assert table["version"] == "static-test"
    assert table["model_reviewed"] is False
    assert table["inferred_profile"]["needs_human_review"] is True
    for key in ("tool_impact", "asset_sensitivity", "blast_radius", "cells", "bands", "baselines"):
        assert key in table

    # Cells obey score = sensitivity * blast * 1.0 * impact.
    sens = table["asset_sensitivity"]["api_keys"]
    impact = table["tool_impact"]["write_query"]
    blast = table["blast_radius"]["write_query|api_keys"]
    assert table["cells"]["api_keys"]["write_query"] == sens * blast * impact


def test_offline_write_on_secret_is_critical():
    table = build_static_table(_toy_registry(), use_llm=False, version="static-test")
    assert table["bands"]["api_keys"]["write_query"] == "critical"
    # Read-only on a low-sensitivity table stays low.
    assert table["bands"]["publications"]["read_query"] == "low"


def test_bands_are_deterministic_no_judge_by_default():
    # Default pipeline: no judge, no LLM band stage -> bands are band_label(score),
    # so two runs of the same registry produce identical bands (reproducible).
    a = build_static_table(_toy_registry(), use_llm=False, version="static-test")
    b = build_static_table(_toy_registry(), use_llm=False, version="static-test")
    assert a["bands"] == b["bands"]
    assert a["crosscheck_summary"]["judge_ran"] is False


# --- LLM path ---------------------------------------------------------------
def test_llm_answers_override_fallback(monkeypatch):
    def fake_query(prompt, **_):
        # Route on each stage's distinctive task header — proposer prompts all
        # embed the domain profile, so matching on field names is ambiguous.
        if "bootstrapping a misuse" in prompt:  # domain inference system prompt
            return {"mcp_kind": "SQL database", "confidence": 0.95, "needs_human_review": False}
        if "Assign TOOL IMPACT" in prompt:
            return {"tool_impact": 3, "confidence": 0.9}
        if "Assign ASSET SENSITIVITY" in prompt:
            return {"sensitivity": 2, "confidence": 0.9}
        if "Assign BLAST RADIUS" in prompt:
            return {"blast_radius": 1, "confidence": 0.9}
        if "behavioral baseline" in prompt:
            return {"expected_tools": ["read_query"], "confidence": 0.9}
        if "Assign a RISK BAND" in prompt:
            import re

            names = re.findall(r'"tool_name":\s*"([^"]+)"', prompt)
            return {"asset_id": "a", "bands": {n: "high" for n in names}, "reasoning": "x"}
        return None

    monkeypatch.setattr(pipeline_mod, "query_ollama", fake_query)
    table = build_static_table(_toy_registry(), use_llm=True, version="static-test")
    assert table["model_reviewed"] is True
    # The model said every tool is impact 3 and every asset sensitivity 2.
    assert set(table["tool_impact"].values()) == {3}
    assert set(table["asset_sensitivity"].values()) == {2}


def test_llm_down_degrades_to_fallback(monkeypatch):
    monkeypatch.setattr(pipeline_mod, "query_ollama", lambda *a, **k: None)
    table = build_static_table(_toy_registry(), use_llm=True, version="static-test")
    assert table["model_reviewed"] is False  # every call returned None → fallback
    assert table["crosscheck_summary"]["judge_ran"] is False


def test_strict_mode_raises_instead_of_fabricating(monkeypatch):
    """LLM-only (strict) mode must abort, never fall back to a heuristic score."""
    from mcp_security.static_scoring.pipeline import LLMUnavailableError

    monkeypatch.setattr(pipeline_mod, "query_ollama", lambda *a, **k: None)
    with __import__("pytest").raises(LLMUnavailableError):
        build_static_table(_toy_registry(), use_llm=True, strict=True, version="static-test")


def test_strict_requires_llm():
    with __import__("pytest").raises(ValueError):
        from mcp_security.static_scoring.pipeline import StaticScorer

        StaticScorer(_toy_registry(), use_llm=False, strict=True)


def test_blast_radius_is_the_models_own_value():
    """Blast is LLM-only (coverage): cells use the model's blast_radius verbatim."""
    import mcp_security.static_scoring.pipeline as pipeline_mod

    def fake_query(prompt: str, *a, **k):
        if "BLAST RADIUS" in prompt or "coverage" in prompt.lower():
            return {"blast_radius": 4, "coverage_reasoning": "whole asset"}
        if "TOOL IMPACT" in prompt:
            return {"tool_impact": 1, "reasoning": "read"}
        if "ASSET SENSITIVITY" in prompt:
            return {"sensitivity": 5, "reasoning": "secrets"}
        if "mcp_kind" in prompt or "domain" in prompt.lower():
            return {"mcp_kind": "test", "confidence": 0.9, "needs_human_review": False}
        return {"expected_tools": [], "reasoning": "x", "confidence": 0.8}

    import pytest

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(pipeline_mod, "query_ollama", fake_query)
    try:
        table = build_static_table(_toy_registry(), use_llm=True, version="static-test")
    finally:
        monkeypatch.undo()
    # every blast is the model's 4; a single-item read of a crown jewel is now high.
    assert set(table["blast_radius"].values()) == {4}
    assert "blast_llm" not in table and "blast_consistency" not in table


def test_blast_escape_route_recorded_verbatim():
    """The model's own escape route is recorded as-is (no coercion): blast is the
    model's decision, the pipeline only captures it."""
    import mcp_security.static_scoring.pipeline as pipeline_mod

    def fake_query(prompt: str, *a, **k):
        if "BLAST RADIUS" in prompt or "coverage" in prompt.lower():
            return {"blast_radius": 5, "escape": "b", "coverage_reasoning": "reads the key"}
        if "TOOL IMPACT" in prompt:
            return {"tool_impact": 3, "reasoning": "read"}
        if "ASSET SENSITIVITY" in prompt:
            return {"sensitivity": 5, "reasoning": "secrets"}
        if "mcp_kind" in prompt or "domain" in prompt.lower():
            return {"mcp_kind": "test", "confidence": 0.9, "needs_human_review": False}
        return {"expected_tools": [], "reasoning": "x", "confidence": 0.8}

    import pytest

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(pipeline_mod, "query_ollama", fake_query)
    try:
        table = build_static_table(
            _toy_registry(), use_llm=True, version="static-test", impact_mode="five_level_v2_na"
        )
    finally:
        monkeypatch.undo()
    # Blast and its route are the model's verbatim: 5 with escape "b", uncoerced.
    assert set(table["blast_radius"].values()) == {5}
    assert set(table["blast_escape"].values()) == {"b"}


def test_ctx_mode_builds_profiles_and_injects_into_blast(monkeypatch):
    """five_level_v2_ctx: a per-tool understanding stage runs first and its
    profile rides along in every blast prompt for that tool."""
    seen_blast_prompts: list[str] = []

    def fake_query(prompt, **_):
        if "bootstrapping a misuse" in prompt:
            return {"mcp_kind": "SQL database", "confidence": 0.95, "needs_human_review": False}
        if "UNDERSTANDING of ONE tool" in prompt:
            return {
                "tool_name": "x",
                "role": "the only destructive op",
                "single_call_reach": "one row",
                "consequence_carriers": "users",
                "worst_realistic_misuse": "silent row loss",
                "importance": "high",
                "confidence": 0.9,
            }
        if "Assign TOOL IMPACT" in prompt:
            return {"tool_impact": 4, "confidence": 0.9}
        if "Assign ASSET SENSITIVITY" in prompt:
            return {"sensitivity": 4, "confidence": 0.9}
        if "Assign BLAST RADIUS" in prompt:
            seen_blast_prompts.append(prompt)
            return {"affects_asset": True, "blast_radius": 3, "escape": "none", "confidence": 0.9}
        if "behavioral baseline" in prompt:
            return {"expected_tools": ["read_query"], "confidence": 0.9}
        return None

    monkeypatch.setattr(pipeline_mod, "query_ollama", fake_query)
    table = build_static_table(
        _toy_registry(), use_llm=True, version="static-test", impact_mode="five_level_v2_ctx"
    )
    assert set(table["tool_profiles"]) == {"read_query", "write_query"}
    assert seen_blast_prompts and all("TOOL UNDERSTANDING" in p for p in seen_blast_prompts)
    assert all('"single_call_reach": "one row"' in p for p in seen_blast_prompts)
    # N/A plumbing intact: scored cells present, bands recomputed as usual.
    assert table["blast_radius"]["write_query|api_keys"] == 3


# --- five_level_v2_desc: org description in, asset sensitivity out ------------
_ORG_DESCRIPTION = (
    "**Company.** A toy research group. **Expected organizational use.** Analysts "
    "query experiment results. `api_keys` is credential material; `publications` is "
    "already public. **CIA in general.** C > I > A."
)


def _desc_registry() -> ServerRegistry:
    registry = _toy_registry()
    registry.description = _ORG_DESCRIPTION
    return registry


def _desc_fake_query(seen: dict[str, list[str]]):
    """Model stub for the desc mode; records every prompt it is shown, by stage."""

    def fake_query(prompt, **_):
        if "bootstrapping a misuse" in prompt:
            seen.setdefault("domain", []).append(prompt)
            return {"mcp_kind": "SQL database", "confidence": 0.95, "needs_human_review": False}
        if "Assign TOOL IMPACT" in prompt:
            seen.setdefault("impact", []).append(prompt)
            return {"tool_impact": 5, "confidence": 0.9}
        if "Assign ASSET SENSITIVITY" in prompt:
            seen.setdefault("sensitivity", []).append(prompt)
            return {"sensitivity": 5, "confidence": 0.9}
        if "Assign BLAST RADIUS" in prompt:
            seen.setdefault("blast", []).append(prompt)
            return {"affects_asset": True, "blast_radius": 4, "escape": "none", "confidence": 0.9}
        if "behavioral baseline" in prompt:
            seen.setdefault("baseline", []).append(prompt)
            return {"expected_tools": ["read_query"], "confidence": 0.9}
        return None

    return fake_query


def test_desc_mode_skips_sensitivity_and_scores_blast_times_impact(monkeypatch):
    """No sensitivity stage runs; the cell is blast x impact on a 25-point scale."""
    seen: dict[str, list[str]] = {}
    monkeypatch.setattr(pipeline_mod, "query_ollama", _desc_fake_query(seen))
    table = build_static_table(
        _desc_registry(),
        use_llm=True,
        version="static-test",
        impact_mode="five_level_v2_desc",
    )
    assert "sensitivity" not in seen  # the stage never ran
    assert table["asset_sensitivity"] == {}
    assert table["sensitivity_scored"] is False
    assert table["asset_ids"] == ["api_keys", "publications"]
    assert table["formula"] == pipeline_mod.FORMULA_NO_SENS
    assert table["score_max"] == 25
    # blast 4 x impact 5 = 20 for every cell, and no sensitivity leaked into it.
    assert set(table["cells"]["api_keys"].values()) == {20}
    assert set(table["cells"]["publications"].values()) == {20}


def test_desc_mode_puts_the_org_description_in_every_stage(monkeypatch):
    """Domain inference, tool impact, blast and baselines all see the description."""
    seen: dict[str, list[str]] = {}
    monkeypatch.setattr(pipeline_mod, "query_ollama", _desc_fake_query(seen))
    table = build_static_table(
        _desc_registry(),
        use_llm=True,
        version="static-test",
        impact_mode="five_level_v2_desc",
    )
    assert table["org_description_used"] is True
    for stage in ("domain", "impact", "blast", "baseline"):
        assert seen[stage], f"{stage} stage never ran"
        assert all("A toy research group" in p for p in seen[stage]), stage
    # The blast rubric must say sensitivity is gone, or the model reconciles a
    # rubric that prices value with a primitive nobody scores.
    assert all("NO SEPARATE SENSITIVITY SCORE IN THIS RUN" in p for p in seen["blast"])


def test_desc_mode_requires_a_description():
    """A desc scan without the org profile would be indistinguishable from a normal
    scan in the artifact, so it must fail loudly instead."""
    import pytest

    from mcp_security.static_scoring.pipeline import StaticScorer

    with pytest.raises(ValueError, match="requires registry.description"):
        StaticScorer(_toy_registry(), use_llm=False, impact_mode="five_level_v2_desc")


def test_band_label_no_sens_floors():
    """Bands without sensitivity: irreversibility and total coverage keep their floors."""
    from mcp_security.static_scoring.pipeline import band_label_no_sens as band

    assert band(5, 5) == "critical"  # destroy the whole asset
    assert band(4, 5) == "critical"  # destroy all of it, contained
    assert band(1, 5) == "high"  # any destructive op floors at high
    assert band(4, 4) == "high"  # total-coverage write
    assert band(5, 1) == "high"  # systemic reach, even for a no-op read
    assert band(4, 3) == "high"  # whole-asset read = mass disclosure
    assert band(2, 4) == "medium"  # narrow write
    assert band(3, 3) == "medium"  # partial read
    assert band(1, 3) == "low"  # pinpoint read
    assert band(1, 2) == "low"  # metadata


# --- five_level_v2_ult: profile sensitivity + deterministic assembly ----------
_ULT_PROFILE = """**Tier: M** · `toy` · toy profile for tests. C > I > A.

| Asset | Sens. | C | I | A | Why |
|---|---|---|---|---|---|
| `api_keys` | 5 | H | H | M | Live credentials. |
| `publications` | 1 | L | L | L | Public. |
"""


def _ult_registry(description: str = _ULT_PROFILE) -> ServerRegistry:
    return ServerRegistry(
        server="toy",
        kind="sqlite",
        tools=[
            ToolSpec("read_query", "Run a SELECT.", read_only_hint=True),
            ToolSpec(
                "read_query_old",
                "Run a SELECT. DEPRECATED: Use read_query instead.",
                read_only_hint=True,
            ),
            ToolSpec("write_query", "Run DELETE/UPDATE.", destructive_hint=True),
        ],
        assets=[
            AssetSpec("api_keys", "Table with columns: id, service, key", tags=("column:key",)),
            AssetSpec("publications", "Table with columns: id, title", tags=("column:title",)),
        ],
        apps={"portal": "reads publications"},
        description=description,
    )


def _ult_fake_query(seen: list[str]):
    """Stub model: write_query = destroy(5), reads = 3; blast 1 everywhere except
    read_query gets blast 3 on publications (so its deprecated twin, at 1, must be
    pulled up by the alias pass)."""

    def fake_query(prompt, **_):
        seen.append(prompt)
        if "bootstrapping a misuse" in prompt:
            return {"mcp_kind": "SQL database", "confidence": 0.95, "needs_human_review": False}
        if "Assign TOOL IMPACT" in prompt:
            impact = 5 if "write_query" in prompt else 3
            return {"tool_impact": impact, "confidence": 0.9}
        if "Assign ASSET SENSITIVITY" in prompt:
            raise AssertionError("ult mode must not run the LLM sensitivity stage")
        if "Assign BLAST RADIUS" in prompt:
            # NOTE: match on the JSON payloads, not bare words — the org profile
            # (which names every asset) is injected into every prompt's preamble.
            blast = 3 if ('"read_query"' in prompt and '"publications"' in prompt) else 1
            return {
                "affects_asset": True,
                "blast_radius": blast,
                "escape": "none",
                "confidence": 0.9,
            }
        if "behavioral baseline" in prompt:
            return {"expected_tools": ["read_query"], "confidence": 0.9}
        return None

    return fake_query


def test_ult_requires_description_and_full_coverage():
    with pytest.raises(ValueError, match="requires registry.description"):
        build_static_table(
            _ult_registry(description=""), use_llm=False, impact_mode="five_level_v2_ult"
        )
    partial = _ULT_PROFILE.replace("| `publications` | 1 | L | L | L | Public. |\n", "")
    with pytest.raises(pipeline_mod.ProfileCoverageError, match="publications"):
        build_static_table(
            _ult_registry(description=partial), use_llm=False, impact_mode="five_level_v2_ult"
        )


def test_ult_profile_sens_floor_alias_and_output_keys(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(pipeline_mod, "query_ollama", _ult_fake_query(seen))
    table = build_static_table(
        _ult_registry(), use_llm=True, version="static-test", impact_mode="five_level_v2_ult"
    )
    # Sensitivity is the org's own table, logged, never LLM-scored.
    assert table["asset_sensitivity"] == {"api_keys": 5, "publications": 1}
    assert table["sensitivity_source"] == "org_profile"
    assert table["sensitivity_scored"] is True
    assert table["score_max"] == 125
    import hashlib

    assert (
        table["profile_sha256"] == hashlib.sha256(_ULT_PROFILE.strip().encode("utf-8")).hexdigest()
    )
    # The blast note rode along on every blast prompt.
    blast_prompts = [p for p in seen if "Assign BLAST RADIUS" in p]
    assert blast_prompts and all("SENSITIVITY IS SUPPLIED SEPARATELY" in p for p in blast_prompts)
    # Alias pass: deprecated twin inherits read_query's higher blast on publications.
    assert table["blast_radius_raw"]["read_query_old|publications"] == 1
    assert table["blast_radius"]["read_query_old|publications"] == 3
    assert any(
        f["tool"] == "read_query_old" and f["asset"] == "publications" and f["to"] == 3
        for f in table["alias_fixups"]
    )
    # Gated floor: write_query (impact 5) on api_keys (sens 5) floors blast 1 -> 4;
    # reads (impact 3) stay at the model's blast.
    assert table["blast_radius"]["write_query|api_keys"] == 4
    assert table["blast_radius_raw"]["write_query|api_keys"] == 1
    assert table["blast_radius"]["read_query|api_keys"] == 1
    assert table["blast_floor"]["raised_cells"] >= 1
    # Bands come from band_label_v5: floored destroy on the crown jewel = critical.
    assert table["bands"]["api_keys"]["write_query"] == "critical"
    assert table["cells"]["api_keys"]["write_query"] == 5 * 4 * 5


def test_band_label_v5_is_pure_score_thresholds():
    # The band is a pure threshold on score = sens*blast*impact (max 125):
    # low < 17 <= medium < 50 <= high < 100 <= critical.
    bl = pipeline_mod.band_label_v5
    assert bl(5, 5, 5) == "critical"  # 125
    assert bl(4, 5, 5) == "critical"  # 100 — the critical cutoff
    assert bl(4, 4, 5) == "high"  # 80
    assert bl(4, 3, 5) == "high"  # 60
    assert bl(4, 3, 4) == "medium"  # 48 — just under high
    assert bl(3, 3, 5) == "medium"  # 45 (the cell the user flagged) -> medium
    assert bl(3, 2, 3) == "medium"  # 18 — just over medium cutoff
    assert bl(2, 2, 4) == "low"  # 16 — just under medium cutoff
    assert bl(3, 1, 5) == "low"  # 15 — a pinpoint delete of internal data
    assert bl(1, 1, 1) == "low"
    for s in range(1, 6):
        for b in range(1, 6):
            for i in range(1, 6):
                sc = s * b * i
                want = (
                    "critical"
                    if sc >= 100
                    else "high"
                    if sc >= 50
                    else "medium"
                    if sc >= 17
                    else "low"
                )
                assert bl(s, b, i) == want


def test_ult_ablation_variants_prompt_levers(monkeypatch):
    """Each ult ablation arm moves exactly its one prompt-context lever."""
    # _tools: the full registry block rides in impact AND blast prompts.
    seen: list[str] = []
    monkeypatch.setattr(pipeline_mod, "query_ollama", _ult_fake_query(seen))
    build_static_table(
        _ult_registry(), use_llm=True, version="t", impact_mode="five_level_v2_ult_tools"
    )
    impact_prompts = [p for p in seen if "Assign TOOL IMPACT" in p]
    blast_prompts = [p for p in seen if "Assign BLAST RADIUS" in p]
    assert all("Full tool registry of this server" in p for p in impact_prompts)
    assert all("Full tool registry of this server" in p for p in blast_prompts)

    # _leanimp: the org description is absent from impact prompts only.
    seen.clear()
    build_static_table(
        _ult_registry(), use_llm=True, version="t", impact_mode="five_level_v2_ult_leanimp"
    )
    impact_prompts = [p for p in seen if "Assign TOOL IMPACT" in p]
    blast_prompts = [p for p in seen if "Assign BLAST RADIUS" in p]
    assert all("ORGANIZATION'S DESCRIPTION" not in p for p in impact_prompts)
    assert all("ORGANIZATION'S DESCRIPTION" in p for p in blast_prompts)

    # _struct: prompts carry only the structured statements — prose is gone,
    # the table survives, and sensitivity parsing still works.
    seen.clear()
    table = build_static_table(
        _ult_registry(description=_ULT_PROFILE + "\nSome very identifiable prose sentence."),
        use_llm=True,
        version="t",
        impact_mode="five_level_v2_ult_struct",
    )
    assert table["asset_sensitivity"] == {"api_keys": 5, "publications": 1}
    assert table["ult_variant_options"] == {"desc_scheme": "struct"}
    blast_prompts = [p for p in seen if "Assign BLAST RADIUS" in p]
    assert all("very identifiable prose sentence" not in p for p in blast_prompts)
    assert all("| `api_keys` | 5 |" in p for p in blast_prompts)


# --- v3: bulk twins + impact-keyed floor --------------------------------------
def test_bulk_twin_map_detects_plural_and_bulk_tokens():
    from mcp_security.static_scoring.pipeline import bulk_twin_map

    tools = [
        ToolSpec("create-event", "Create one event."),
        ToolSpec("create-events", "Create multiple events in bulk."),
        ToolSpec("read_file", "Read one file."),
        ToolSpec("read_multiple_files", "Read several files at once."),
        ToolSpec("list-colors", "Static palette."),  # plural with no singular twin
        ToolSpec("update-event", "Update one event."),
    ]
    twins = bulk_twin_map(tools)
    assert twins == {"create-events": "create-event", "read_multiple_files": "read_file"}


def test_bulk_dominance_impact_and_blast():
    from mcp_security.static_scoring.pipeline import apply_bulk_blast, apply_bulk_impact

    twins = {"create-events": "create-event"}
    impacts, ifix = apply_bulk_impact({"create-event": 5, "create-events": 4}, twins)
    assert impacts["create-events"] == 5 and ifix[0]["field"] == "impact"

    # blast: bulk below singular -> singular+1; tie -> +1; above -> untouched; N/A safe.
    blast = {
        "create-event|a": 3,
        "create-events|a": 1,
        "create-event|b": 3,
        "create-events|b": 3,
        "create-event|c": 2,
        "create-events|c": 5,
        "create-event|d": None,
        "create-events|d": 2,
    }
    out, bfix = apply_bulk_blast(blast, twins, ["a", "b", "c", "d"])
    assert out["create-events|a"] == 4  # raised above the singular
    assert out["create-events|b"] == 4  # tie-bump (+1) after floors
    assert out["create-events|c"] == 5  # already above — untouched
    assert out["create-events|d"] == 2  # singular N/A — no comparison
    assert all(f["field"] == "blast" for f in bfix) and len(bfix) == 2


def test_impact_keyed_floors():
    from mcp_security.static_scoring.pipeline import apply_gated_floor

    blast = {"destroy|low_asset": 1, "write|low_asset": 1, "read|low_asset": 1}
    out, raised = apply_gated_floor(
        blast,
        {"low_asset": 1},
        {"destroy": 5, "write": 4, "read": 3},
        floors={5: 4, 4: 3},
        gate_impact_min=4,
        impact_floors={5: 3, 4: 2},
    )
    assert out["destroy|low_asset"] == 3  # impact-5 floor, sens irrelevant
    assert out["write|low_asset"] == 2  # impact-4 floor (one tier lower)
    assert out["read|low_asset"] == 1  # below the gate — untouched
    assert raised == 2


def test_blast_roof_never_caps_mutations_and_respects_escape_flags():
    from mcp_security.static_scoring.pipeline import apply_blast_roof

    blast = {
        "read|public": 5,  # impact 3, sens 1 -> capped
        "read|hub": 5,  # impact 3 but escape flag -> exempt
        "read|exec": 5,  # impact 3, sens 4, no flag -> read_cap 4
        "delete|public": 5,  # impact 5 -> NEVER capped
        "meta|routine": 5,  # impact 2, sens 2 -> combined cap
    }
    sens = {"public": 1, "hub": 5, "exec": 4, "routine": 2}
    impacts = {"read": 3, "delete": 5, "meta": 2}
    # map cells to assets via the key; supply flags
    flags = {"hub": ("hub",), "public": (), "exec": (), "routine": ()}
    out, fixups = apply_blast_roof(
        blast,
        sens,
        impacts,
        flags,
        read_cap=4,
        sens_caps={1: 3},
        combined_cap=(2, 2, 2),
    )
    assert out["read|public"] == 3  # sens-1 cap (min of read_cap 4 and sens 3)
    assert out["read|hub"] == 5  # escape flag exempts from read_cap
    assert out["read|exec"] == 4  # read_cap 4, no flag
    assert out["delete|public"] == 5  # mutation NEVER capped (safety invariant)
    assert out["meta|routine"] == 2  # combined trivial x trivial cap
    # never raises, never touches N/A
    assert all(f["field"] == "blast_roof" and f["to"] < f["from"] for f in fixups)
