"""Tests for per-tool atomic-op flagging and input-risk ranking."""

from __future__ import annotations

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


def test_input_ranking_puts_payload_and_arrays_first():
    schema = {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "content": {"type": "string"},
            "files": {"type": "array"},
        },
        "required": ["owner"],
    }
    ranking = rank_tool_inputs([_tool("push_files", "Push files", schema)])["push_files"]
    top_two = {r["name"] for r in ranking[:2]}
    assert top_two == {"content", "files"}  # payload + array outrank the target id
    assert ranking[-1]["name"] == "owner"


def test_enrich_scan_attaches_both_fields():
    table = {"tool_impact": {"read_file": 1}}
    enrich_scan(table, [_tool("read_file", "Read a file")])
    assert "tool_atomic_ops" in table and "tool_input_ranking" in table
    assert table["tool_atomic_ops"]["read_file"]["primary_op"] == "READ"
