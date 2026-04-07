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
# scorer_bridge stub
# ---------------------------------------------------------------------------


def test_scorer_bridge_stub_returns_none_scores() -> None:
    """Stub scorer returns None for static, dynamic, and combined scores."""
    result = score("read_file", {"path": "foo"}, "Reads a file", "file contents")
    assert result["static"] is None
    assert result["dynamic"] is None
    assert result["combined"] is None


def test_scorer_bridge_stub_has_note_key() -> None:
    """Stub scorer always includes a 'note' key explaining the placeholder."""
    result = score("any_tool", {}, "", "")
    assert "note" in result
    assert isinstance(result["note"], str)
    assert len(result["note"]) > 0
