"""Tests for per-tool atomic-op flagging and input-risk ranking."""

from __future__ import annotations

import mcp_security.scanner.atomic_flags as af
from mcp_security.scanner.atomic_flags import (
    classify_tools_atomic,
    enrich_scan,
    rank_tool_inputs,
)
from mcp_security.static_scoring.registry import ToolSpec


def _tool(name, desc="", schema=None):
    return ToolSpec(name=name, description=desc, input_schema=schema or {})


def test_rule_classifier_flags_destructive_tool():
    flags = classify_tools_atomic([_tool("delete_file", "Delete a file")])
    f = flags["delete_file"]
    assert "DELETE" in f["atomic_ops"]
    assert f["severity"] == 5 and f["severity_label"] == "Critical"
    assert f["source"] == "rules"


def test_hyphenated_name_is_normalised():
    # calendar-style names use hyphens; must still classify.
    flags = classify_tools_atomic([_tool("delete-event", "Delete a calendar event")])
    assert "DELETE" in flags["delete-event"]["atomic_ops"]


def test_verb_fallback_covers_unmatched_tool():
    # A name the rule set misses (no description to help) still gets a verb flag.
    flags = classify_tools_atomic([_tool("channels_me")])
    f = flags["channels_me"]
    assert f["source"] == "verb-fallback"
    assert f["atomic_ops"]  # not left empty


def test_every_tool_gets_flagged():
    tools = [_tool("channels_me"), _tool("get-freebusy"), _tool("usergroups_list")]
    flags = classify_tools_atomic(tools)
    assert all(f["atomic_ops"] for f in flags.values())  # none left empty


_PUSH_SCHEMA = {
    "type": "object",
    "properties": {
        "owner": {"type": "string"},
        "content": {"type": "string"},
        "files": {"type": "array"},
    },
    "required": ["owner"],
}


def test_input_ranking_deterministic_puts_payload_and_arrays_first():
    entry = rank_tool_inputs([_tool("push_files", "Push files", _PUSH_SCHEMA)])["push_files"]
    assert entry["source"] == "rules"
    inputs = entry["inputs"]
    assert {r["name"] for r in inputs[:2]} == {"content", "files"}  # outrank the target id
    assert inputs[-1]["name"] == "owner"


def test_input_ranking_uses_llm_when_available(monkeypatch):
    # Model ranks owner highest (reversing the heuristic) -> proves the LLM path is used.
    monkeypatch.setattr(af, "query_ollama", lambda prompt: {"ranking": [
        {"name": "owner", "risk": 5, "reason": "controls the whole target"},
        {"name": "content", "risk": 2, "reason": "just text"},
        {"name": "files", "risk": 1, "reason": "empty here"},
    ]})
    entry = rank_tool_inputs([_tool("push_files", "Push files", _PUSH_SCHEMA)], use_llm=True)["push_files"]
    assert entry["source"] == "llm"
    assert entry["inputs"][0]["name"] == "owner" and entry["inputs"][0]["risk"] == 5


def test_llm_ranking_falls_back_to_rules_when_unreachable(monkeypatch):
    monkeypatch.setattr(af, "query_ollama", lambda prompt: None)  # Ollama down
    entry = rank_tool_inputs([_tool("push_files", "Push files", _PUSH_SCHEMA)], use_llm=True)["push_files"]
    assert entry["source"] == "rules-fallback"
    assert {r["name"] for r in entry["inputs"][:2]} == {"content", "files"}


def test_llm_ranking_falls_back_when_incomplete(monkeypatch):
    # Model omits a parameter -> untrusted -> fall back to rules.
    monkeypatch.setattr(af, "query_ollama", lambda prompt: {"ranking": [
        {"name": "owner", "risk": 5, "reason": "x"}]})
    entry = rank_tool_inputs([_tool("push_files", "Push files", _PUSH_SCHEMA)], use_llm=True)["push_files"]
    assert entry["source"] == "rules-fallback"


def test_llm_ranking_carries_critical_trigger(monkeypatch):
    monkeypatch.setattr(af, "query_ollama", lambda prompt: {"ranking": [
        {"name": "owner", "risk": 2, "critical_trigger": None, "reason": "target"},
        {"name": "content", "risk": 4, "critical_trigger": None, "reason": "payload"},
        {"name": "files", "risk": 5, "critical_trigger": ">= 20 files", "reason": "bulk"},
    ]})
    inputs = rank_tool_inputs([_tool("push_files", "", _PUSH_SCHEMA)], use_llm=True)["push_files"]["inputs"]
    files = next(r for r in inputs if r["name"] == "files")
    assert files["critical_trigger"] == ">= 20 files"


def test_deterministic_ranking_has_trigger_field():
    inputs = rank_tool_inputs([_tool("read_query", "", {
        "type": "object", "properties": {"query": {"type": "string"}}})])["read_query"]["inputs"]
    assert inputs[0]["name"] == "query"
    assert inputs[0]["critical_trigger"] == "unbounded / no bound on scope"


def test_enrich_scan_attaches_both_fields():
    table = {"tool_impact": {"read_file": 1}}
    enrich_scan(table, [_tool("read_file", "Read a file")])
    assert "tool_atomic_ops" in table and "tool_input_ranking" in table
    assert table["tool_atomic_ops"]["read_file"]["primary_op"] == "READ"
    assert table["tool_input_ranking"]["read_file"]["source"] == "rules"
