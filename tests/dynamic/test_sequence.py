"""Tests for session-level read-then-send sequence risk."""

from __future__ import annotations

from mcp_security.call_scoring.tables import table_from_dict
from mcp_security.call_scoring.score import score_call
from mcp_security.call_scoring.loader import Call
from mcp_security.dynamic.sequence import score_sequence


def _scan():
    return table_from_dict(
        "fs_fintech_fs",
        {
            "server": "secure-filesystem-server",
            "mcp_kind": "filesystem",
            "tool_impact": {"read_file": 1, "write_file": 3},
            "asset_sensitivity": {".csv": 4, ".md": 1},
            "cells": {
                ".csv": {"read_file": 4.0, "write_file": 24.0},
                ".md": {"read_file": 1.0, "write_file": 3.0},
            },
            "bands": {
                ".csv": {"read_file": "medium", "write_file": "high"},
                ".md": {"read_file": "low", "write_file": "low"},
            },
        },
    )


def _call(index, tool, path):
    return Call(source="fs_fintech_fs", index=str(index), tool=tool, args={"path": path}, run_id="r1")


def test_sensitive_read_then_outbound_call_is_critical():
    table = _scan()
    session = [
        score_call(_call(1, "read_file", "customers.csv"), table),
        score_call(_call(2, "write_file", "export.md"), table),
    ]
    verdicts = score_sequence(session)
    assert verdicts[0].band == "low"
    assert verdicts[1].band == "critical"
    # asset is the resolved table key (an extension, for this extension-keyed scan).
    assert ".csv" in verdicts[1].reason


def test_outbound_call_outside_window_is_not_flagged():
    table = _scan()
    session = [score_call(_call(1, "read_file", "customers.csv"), table)]
    session += [score_call(_call(i, "read_file", "notes.md"), table) for i in range(2, 8)]
    session.append(score_call(_call(8, "write_file", "export.md"), table))
    verdicts = score_sequence(session)
    assert verdicts[-1].band == "low"


def test_no_sensitive_read_no_flag():
    table = _scan()
    session = [
        score_call(_call(1, "read_file", "notes.md"), table),
        score_call(_call(2, "write_file", "export.md"), table),
    ]
    verdicts = score_sequence(session)
    assert all(v.band == "low" for v in verdicts)
