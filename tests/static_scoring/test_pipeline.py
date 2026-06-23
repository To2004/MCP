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


def test_band_label_reserves_critical_for_crown_jewels():
    # critical ONLY for irreversible (impact 3) destruction of a sensitivity-5
    # asset at departmental+ reach — the ops a gate must hard-block.
    assert band_label(5, 4, 3) == "critical"  # secret/PII, destroy, wide
    assert band_label(4, 4, 3) == "high"  # restricted business data, not crown-jewel
    assert band_label(5, 2, 3) == "high"  # crown-jewel but narrow reach
    # Confidentiality floor: reading a crown-jewel is never "low".
    assert band_label(5, 1, 1) == "medium"  # narrow read of a secret = leak
    assert band_label(5, 3, 1) == "high"  # broad read of a secret = mass exfiltration
    assert band_label(4, 1, 1) == "low"  # narrow read of restricted data = routine
    assert band_label(4, 3, 1) == "high"  # broad read of restricted data = exfiltration
    assert band_label(3, 2, 2) == "medium"
    assert band_label(2, 1, 1) == "low"


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


def test_crosscheck_counts_every_judged_primitive():
    table = build_static_table(_toy_registry(), use_llm=False, version="static-test")
    summary = table["crosscheck_summary"]
    # 2 tools + 2 assets + 4 blast cells = 8 judged primitives (domain isn't one).
    assert summary["total_records"] == 8
    assert summary["judge_ran"] is False  # no model offline → confidence-threshold flagging
    assert 0 <= summary["flagged_for_review"] <= summary["total_records"]


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


def test_judge_overrides_proposer_and_flags_disagreement(monkeypatch):
    # Proposer rates every tool impact 1; the judge independently says 3 and wins.
    def fake_query(prompt, **_):
        if "bootstrapping a misuse" in prompt:
            return {"mcp_kind": "SQL database", "confidence": 0.95, "needs_human_review": False}
        if "independent security reviewer" in prompt:  # JUDGE_SYSTEM
            if "tool_impact" in prompt:
                return {
                    "agree": False,
                    "judged_value": 3,
                    "reasoning": "destructive",
                    "confidence": 0.9,
                }
            return {"agree": True, "judged_value": None, "reasoning": "ok", "confidence": 0.8}
        if "Assign TOOL IMPACT" in prompt:
            return {"tool_impact": 1, "confidence": 0.6}
        if "Assign ASSET SENSITIVITY" in prompt:
            return {"sensitivity": 3, "confidence": 0.9}
        if "Assign BLAST RADIUS" in prompt:
            return {"blast_radius": 2, "confidence": 0.9}
        if "behavioral baseline" in prompt:
            return {"expected_tools": ["read_query"], "confidence": 0.9}
        return None

    monkeypatch.setattr(pipeline_mod, "query_ollama", fake_query)
    table = build_static_table(_toy_registry(), use_llm=True, version="static-test")
    summary = table["crosscheck_summary"]
    assert summary["judge_ran"] is True
    # The judge disagreed on both tools and overrode 1 → 3.
    assert set(table["tool_impact"].values()) == {3}
    assert summary["overridden"] == 2
    assert summary["flagged_for_review"] == 2
    assert any(d["proposed"] == 1 and d["judged"] == 3 for d in summary["disagreements"])
