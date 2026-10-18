"""Tests for static+dynamic fusion via escalation."""

from __future__ import annotations

from mcp_security.call_scoring.tables import table_from_dict
from mcp_security.call_scoring.score import score_call
from mcp_security.call_scoring.loader import Call
from mcp_security.dynamic.baseline import build_baselines
from mcp_security.dynamic.combine import score_session


def _scan():
    return table_from_dict(
        "fs_corp_filesystem",
        {
            "server": "secure-filesystem-server",
            "mcp_kind": "filesystem",
            "tool_impact": {"read_file": 1, "write_file": 3},
            "asset_sensitivity": {".md": 1, ".pem": 5},
            "cells": {
                ".md": {"read_file": 1.0, "write_file": 3.0},
                ".pem": {"read_file": 5.0, "write_file": 75.0},
            },
            "bands": {
                ".md": {"read_file": "low", "write_file": "low"},
                ".pem": {"read_file": "low", "write_file": "critical"},
            },
        },
    )


def _call(index, tool, path, persona="Alice", run_id="r1"):
    return Call(
        source="fs_corp_filesystem", index=str(index), tool=tool,
        args={"path": path}, persona=persona, run_id=run_id,
        args_raw=f'{{"path": "{path}"}}',
    )


def test_dynamic_signal_escalates_low_static_band():
    table = _scan()
    history = [score_call(_call(1, "read_file", "notes.md"), table)]
    baselines = build_baselines(history)

    # Static band for read_file on .md is "low", but Alice has never used
    # write_file before -- baseline should escalate it, never lower it.
    session = [score_call(_call(2, "write_file", "notes.md"), table)]
    verdicts = score_session(session, baselines)

    assert verdicts[0].static_band == "low"
    assert verdicts[0].baseline_band == "high"
    assert verdicts[0].final_band == "high"


def test_never_lowers_a_critical_static_band():
    table = _scan()
    history = [score_call(_call(1, "write_file", "secrets.pem"), table)]
    baselines = build_baselines(history)

    # Consistent with baseline, but static band is already critical.
    session = [score_call(_call(2, "write_file", "secrets.pem"), table)]
    verdicts = score_session(session, baselines)

    assert verdicts[0].static_band == "critical"
    assert verdicts[0].final_band == "critical"


def test_judge_fn_can_escalate_further():
    table = _scan()
    session = [score_call(_call(1, "read_file", "notes.md"), table)]

    def fake_judge(tool, args):
        return "critical", "decoded payload is a reverse shell"

    verdicts = score_session(session, {}, judge_fn=fake_judge)
    assert verdicts[0].judge_band == "critical"
    assert verdicts[0].final_band == "critical"


def test_no_judge_fn_leaves_judge_band_none():
    table = _scan()
    session = [score_call(_call(1, "read_file", "notes.md"), table)]
    verdicts = score_session(session, {})
    assert verdicts[0].judge_band is None
