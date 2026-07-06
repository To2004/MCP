"""Unit tests for attack_runner pure functions.

These tests do NOT require a live server or the MCP SDK transport layer.
Only pure helper functions are exercised here.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from tests.testbed.harness.attack_runner import (
    _build_args,
    _check_damage,
    _response_to_text,
)
from tests.testbed.harness import scorer_bridge
from tests.testbed.harness.scorer_bridge import score


# ---------------------------------------------------------------------------
# _check_damage
# ---------------------------------------------------------------------------


def test_check_damage_matches() -> None:
    """damage_indicator regex is found in response_text."""
    assert _check_damage("root:x:0:0:root:/root:/bin/bash", "root:|daemon:") is True


def test_check_damage_no_match() -> None:
    """damage_indicator regex is NOT found in response_text."""
    assert _check_damage("Hello, world!", "root:|daemon:") is False


def test_check_damage_none_indicator() -> None:
    """None damage_indicator always returns False regardless of response."""
    assert _check_damage("root:x:0:0", None) is False


def test_check_damage_case_insensitive() -> None:
    """Regex match is case-insensitive."""
    assert _check_damage("ROOT:x:0:0", "root:") is True


# ---------------------------------------------------------------------------
# _response_to_text
# ---------------------------------------------------------------------------


def test_response_to_text_string() -> None:
    """Non-response objects fall back to str() conversion."""
    assert _response_to_text(42) == "42"
    assert _response_to_text({"key": "val"}) == "{'key': 'val'}"


def test_response_to_text_requests_response() -> None:
    """Objects with a .text attribute return that attribute directly."""
    fake = SimpleNamespace(text="hello from requests")
    assert _response_to_text(fake) == "hello from requests"


def test_response_to_text_mcp_call_tool_result() -> None:
    """Objects with a .content list of text blocks are joined into one string."""
    block1 = SimpleNamespace(text="line one")
    block2 = SimpleNamespace(text="line two")
    fake_result = SimpleNamespace(content=[block1, block2])
    assert _response_to_text(fake_result) == "line one\nline two"


def test_response_to_text_mcp_non_text_blocks() -> None:
    """Content blocks without .text are silently skipped."""
    block_no_text = SimpleNamespace(data=b"\x00\x01")
    fake_result = SimpleNamespace(content=[block_no_text])
    assert _response_to_text(fake_result) == ""


# ---------------------------------------------------------------------------
# _build_args
# ---------------------------------------------------------------------------


def _make_tool(properties: dict[str, Any]) -> Any:
    """Build a minimal fake Tool with the given inputSchema properties."""
    return SimpleNamespace(inputSchema={"type": "object", "properties": properties})


def test_build_args_with_schema() -> None:
    """First property in inputSchema is used as the argument key."""
    tool = _make_tool({"path": {"type": "string"}, "encoding": {"type": "string"}})
    result = _build_args(tool, "../../etc/passwd")
    assert result == {"path": "../../etc/passwd"}


def test_build_args_no_schema() -> None:
    """When inputSchema has no properties, fallback key 'input' is used."""
    tool = _make_tool({})
    result = _build_args(tool, "some value")
    assert result == {"input": "some value"}


def test_build_args_no_input_schema_attr() -> None:
    """When the tool has no inputSchema attribute, fallback key 'input' is used."""
    tool = SimpleNamespace()  # no inputSchema attribute
    result = _build_args(tool, "value")
    assert result == {"input": "value"}


def test_build_args_none_input_schema() -> None:
    """When inputSchema is None, fallback key 'input' is used."""
    tool = SimpleNamespace(inputSchema=None)
    result = _build_args(tool, "value")
    assert result == {"input": "value"}


# ---------------------------------------------------------------------------
# scorer_bridge
# ---------------------------------------------------------------------------


def test_scorer_bridge_static_and_combined_always_none(monkeypatch) -> None:
    """static/combined stay None: no profile-to-scan-artifact mapping exists yet."""
    monkeypatch.setattr(scorer_bridge, "judge_call", lambda tool, args: ("high", "test reason"))
    result = score("read_file", {"path": "foo"}, "Reads a file", "file contents")
    assert result["static"] is None
    assert result["combined"] is None


def test_scorer_bridge_dynamic_reflects_judge_verdict(monkeypatch) -> None:
    """dynamic is the judge's band when the judge returns a verdict."""
    monkeypatch.setattr(scorer_bridge, "judge_call", lambda tool, args: ("critical", "obfuscated payload"))
    result = score("run_command", {"cmd": "..."}, "Runs a command", "")
    assert result["dynamic"] == "critical"
    assert "obfuscated payload" in result["note"]


def test_scorer_bridge_dynamic_none_when_judge_has_no_verdict(monkeypatch) -> None:
    """dynamic is None (not fabricated) when the judge stage has no opinion."""
    monkeypatch.setattr(scorer_bridge, "judge_call", lambda tool, args: None)
    result = score("any_tool", {}, "", "")
    assert result["dynamic"] is None


def test_scorer_bridge_always_has_note_key(monkeypatch) -> None:
    """The bridge always includes a 'note' key explaining the current verdict."""
    monkeypatch.setattr(scorer_bridge, "judge_call", lambda tool, args: None)
    result = score("any_tool", {}, "", "")
    assert "note" in result
    assert isinstance(result["note"], str)
    assert len(result["note"]) > 0
