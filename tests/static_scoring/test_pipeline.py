"""Tests for the static (design-time) misuse-scoring pipeline.

The deterministic path must run fully offline and never under-score a
crown-jewel asset; the LLM path must be used when the model answers and override
the fallback. We stub the model rather than hitting Ollama.
"""

from __future__ import annotations

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

