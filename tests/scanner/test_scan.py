"""Tests for the static scanner: registry assembly and LLM-only scanning."""

from __future__ import annotations

import json

import pytest

import mcp_security.static_scoring.pipeline as pipeline_mod
from mcp_security.scanner import build_registry, scan_server, write_scan
from mcp_security.static_scoring.pipeline import LLMUnavailableError


def _fake_model(prompt: str, **_):
    """Route on each stage's distinctive task header (mirrors pipeline tests)."""
    if "bootstrapping a misuse" in prompt:
        return {"mcp_kind": "filesystem", "confidence": 0.95, "needs_human_review": False}
    if "Assign TOOL IMPACT" in prompt:
        return {"tool_impact": 3, "confidence": 0.9}
    if "Assign ASSET SENSITIVITY" in prompt:
        return {"sensitivity": 5, "confidence": 0.9}
    if "Assign BLAST RADIUS" in prompt:
        return {"blast_radius": 4, "confidence": 0.9}
    if "behavioral baseline" in prompt:
        return {"expected_tools": ["read_text_file"], "confidence": 0.9}
    if "Assign a RISK BAND" in prompt:
        import re

        names = re.findall(r'"tool_name":\s*"([^"]+)"', prompt)
        return {"asset_id": "a", "bands": {n: "high" for n in names}, "reasoning": "x"}
    return None


def test_build_registry_tools_from_excel_assets_from_disk():
    reg = build_registry("filesystem", by_file=False)
    assert reg.kind == "filesystem"
    # Tools come from the Excel catalog; assets from the on-disk demo store.
    assert {t.name for t in reg.tools} >= {"read_text_file", "write_file"}
    assert any(a.asset_id == ".pem" for a in reg.assets)


def test_scan_is_llm_only_and_raises_without_model(monkeypatch):
    monkeypatch.setattr(pipeline_mod, "query_ollama", lambda *a, **k: None)
    with pytest.raises(LLMUnavailableError):
        scan_server("filesystem", use_llm=True, version="scan-test")


def test_scan_with_model_produces_full_matrix(monkeypatch):
    monkeypatch.setattr(pipeline_mod, "query_ollama", _fake_model)
    result = scan_server("filesystem", use_llm=True, version="scan-test")
    table = result.table
    assert table["model_reviewed"] is True
    assert table["provenance"] == "llm-scan"
    for key in ("tool_impact", "asset_sensitivity", "blast_radius", "cells", "bands"):
        assert key in table
    assert result.n_tools == len(table["tool_impact"]) > 0
    assert result.n_assets == len(table["asset_sensitivity"]) > 0


def test_write_scan_roundtrips(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline_mod, "query_ollama", _fake_model)
    result = scan_server("filesystem", server="fs:test", use_llm=True, version="scan-test")
    path = write_scan(result, tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["tool_impact"] == result.table["tool_impact"]
