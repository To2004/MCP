"""Tests for the per-agent behavioral baseline."""

from __future__ import annotations

from mcp_security.call_scoring.tables import table_from_dict
from mcp_security.call_scoring.score import score_call
from mcp_security.call_scoring.loader import Call
from mcp_security.dynamic.baseline import build_baselines, score_deviation


def _fs_scan():
    return table_from_dict(
        "fs_corp_filesystem",
        {
            "server": "secure-filesystem-server",
            "mcp_kind": "filesystem",
            "tool_impact": {"read_file": 1, "write_file": 3},
            "asset_sensitivity": {".md": 2, ".pem": 5},
            "cells": {
                ".md": {"read_file": 2.0, "write_file": 12.0},
                ".pem": {"read_file": 10.0, "write_file": 60.0},
            },
            "bands": {
                ".md": {"read_file": "low", "write_file": "medium"},
                ".pem": {"read_file": "medium", "write_file": "critical"},
            },
        },
    )


def _call(index, tool, path, persona="Alice", run_id="r1"):
    return Call(
        source="fs_corp_filesystem", index=str(index), tool=tool,
        args={"path": path}, persona=persona, run_id=run_id,
        args_raw=f'{{"path": "{path}"}}',
    )


def test_build_baselines_tracks_tools_and_max_sensitivity():
    table = _fs_scan()
    calls = [
        score_call(_call(1, "read_file", "notes.md"), table),
        score_call(_call(2, "read_file", "notes.md"), table),
    ]
    baselines = build_baselines(calls)
    key = "Alice@fs_corp_filesystem"
    assert key in baselines
    assert baselines[key].known_tools == frozenset({"read_file"})
    assert baselines[key].max_sensitivity == 2


def test_score_deviation_no_baseline_is_honest_non_signal():
    band, reason = score_deviation(score_call(_call(1, "read_file", "notes.md"), _fs_scan()), None)
    assert band == "low"
    assert "no baseline" in reason


def test_score_deviation_flags_unseen_tool():
    table = _fs_scan()
    history = [score_call(_call(1, "read_file", "notes.md"), table)]
    baselines = build_baselines(history)
    baseline = baselines["Alice@fs_corp_filesystem"]

    new_call = score_call(_call(2, "write_file", "notes.md"), table)
    band, reason = score_deviation(new_call, baseline)
    assert band == "high"
    assert "write_file" in reason


def test_score_deviation_flags_higher_sensitivity_than_seen():
    table = _fs_scan()
    history = [score_call(_call(1, "read_file", "notes.md"), table)]
    baselines = build_baselines(history)
    baseline = baselines["Alice@fs_corp_filesystem"]

    new_call = score_call(_call(2, "read_file", "secrets.pem"), table)
    band, reason = score_deviation(new_call, baseline)
    assert band in {"high", "critical"}
    assert "sensitivity" in reason


def test_score_deviation_flags_abnormal_burst():
    table = _fs_scan()
    # Baseline: small sessions varying 2-3 calls, so stdev is nonzero.
    history = []
    sizes = [2, 3, 2, 3, 2]
    for run, size in enumerate(sizes):
        for i in range(size):
            history.append(score_call(_call(i, "read_file", "notes.md", run_id=f"r{run}"), table))
    baselines = build_baselines(history)
    baseline = baselines["Alice@fs_corp_filesystem"]

    new_call = score_call(_call(1, "read_file", "notes.md"), table)
    band, reason = score_deviation(new_call, baseline, session_size=50)
    assert band == "medium"
    assert "std devs" in reason


def test_score_deviation_consistent_call_is_low():
    table = _fs_scan()
    history = [score_call(_call(1, "read_file", "notes.md"), table)]
    baselines = build_baselines(history)
    baseline = baselines["Alice@fs_corp_filesystem"]

    same_call = score_call(_call(2, "read_file", "notes.md"), table)
    band, _reason = score_deviation(same_call, baseline, session_size=1)
    assert band == "low"
