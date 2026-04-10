"""Unit tests for pure helpers in attack_fs_chains.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attack_fs_chains import CANARY, classify_hit, clean_text, truncate


def test_classify_canary_is_critical():
    pinned = "some bytes including ATTACKER_CANARY_12345 in the middle"
    latest = "Error: outside allowed directories"
    sev, reason, regression = classify_hit(
        input_path="/tmp/mcp_attack_328/link",
        pinned=pinned,
        latest=latest,
        pinned_elapsed_ms=20,
        latest_elapsed_ms=20,
    )
    assert sev == "CRITICAL"
    assert "canary" in reason.lower()
    assert regression is True


def test_classify_etc_passwd_marker_is_critical():
    response = "root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/bin:/sbin/nologin\n"
    sev, _, _ = classify_hit("", response, response, 10, 10)
    assert sev == "CRITICAL"


def test_classify_ssh_key_is_critical():
    response = "-----BEGIN OPENSSH PRIVATE KEY-----\nbase64blob\n-----END-----"
    sev, _, _ = classify_hit("", response, response, 10, 10)
    assert sev == "CRITICAL"


def test_classify_timeout_is_high():
    sev, reason, _ = classify_hit("", "", "", 16000, 16000)
    assert sev == "HIGH"
    assert "timeout" in reason.lower() or "hang" in reason.lower()


def test_classify_huge_response_is_high():
    blob = "x" * (6 * 1024 * 1024)
    sev, reason, _ = classify_hit("", blob, blob, 100, 100)
    assert sev == "HIGH"
    assert "mb" in reason.lower() or "dos" in reason.lower()


def test_classify_host_path_leak_is_medium():
    response = "ENOENT: no such file at /home/alice/secret_project/node_modules/foo"
    sev, _, _ = classify_hit("bar.txt", response, response, 10, 10)
    assert sev == "MEDIUM"


def test_classify_regression_low_when_content_flip():
    sev, _, regression = classify_hit(
        input_path="some/path",
        pinned="Error: outside allowed directories",
        latest="file contents returned ok and nothing sensitive",
        pinned_elapsed_ms=10,
        latest_elapsed_ms=10,
    )
    assert regression is True
    assert sev == "LOW"


def test_classify_clean_is_info():
    sev, _, regression = classify_hit("ok.txt", "hello", "hello", 10, 10)
    assert sev == "INFO"
    assert regression is False


def test_clean_text_strips_control_chars():
    assert clean_text("ok\x00bad") == "ok<0x00>bad"
    assert clean_text("tab\there") == "tab\there"


def test_truncate_keeps_short_strings():
    assert truncate("short", 100) == "short"


def test_truncate_marks_long_strings():
    s = "a" * 500
    result = truncate(s, 100)
    assert len(result) < len(s)
    assert "500" in result
