"""Tests for the optional LLM judge stage: normalization and graceful degradation."""

from __future__ import annotations

import base64

from mcp_security.dynamic import judge as judge_module
from mcp_security.dynamic.judge import judge_call, normalize_args, normalize_value


def test_normalize_value_decodes_base64():
    token = base64.b64encode(b"rm -rf /tmp/data").decode()
    result = normalize_value(f"echo {token} | base64 -d | bash")
    assert "rm -rf /tmp/data" in result


def test_normalize_value_decodes_hex():
    token = "726d202d7266202f746d702f64617461"  # "rm -rf /tmp/data"
    result = normalize_value(f"echo {token} | xxd -r -p")
    assert "rm -rf /tmp/data" in result


def test_normalize_value_expands_shell_assignment():
    result = normalize_value("CMD=rm; ARGS='-rf /'; $CMD $ARGS")
    assert "rm -rf /" in result or ("rm" in result and "-rf /" in result)


def test_normalize_args_only_touches_string_values():
    args = {"limit": 5, "path": "notes.md"}
    assert normalize_args(args) == {"limit": 5, "path": "notes.md"}


def test_judge_call_returns_none_when_ollama_unreachable(monkeypatch):
    monkeypatch.setattr(judge_module, "query_ollama", lambda prompt: None)
    assert judge_call("read_file", {"path": "notes.md"}) is None


def test_judge_call_returns_none_on_invalid_band(monkeypatch):
    monkeypatch.setattr(judge_module, "query_ollama", lambda prompt: {"band": "extreme", "reason": "x"})
    assert judge_call("read_file", {"path": "notes.md"}) is None


def test_judge_call_returns_band_and_reason(monkeypatch):
    monkeypatch.setattr(
        judge_module, "query_ollama",
        lambda prompt: {"band": "critical", "reason": "obfuscated reverse shell"},
    )
    result = judge_call("run_command", {"cmd": "..."})
    assert result == ("critical", "obfuscated reverse shell")
