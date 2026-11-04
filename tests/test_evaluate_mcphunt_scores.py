"""Tests for scripts/evaluate_mcphunt_scores.py: joining scores to MCPHunt labels."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evaluate_mcphunt_scores as ev  # noqa: E402


def _label(session: str, ts: float, tool: str, env: str = "benign", trace: str = "t1",
           outcome: str = "safe_success", canary: bool = False) -> dict:
    return {"route": "filesystem", "agent": "a", "session": session, "ts": str(ts),
            "trace_id": trace, "env_type": env, "outcome": outcome, "tool": tool,
            "canary_in_args": str(canary)}


def _scored(session: str, tool: str, cell: float) -> dict:
    return {"session": session, "tool": tool, "cell": str(cell), "risk": str(cell),
            "dynamic_risk": str(cell / 5), "basis": "named", "band": "low"}


def test_join_pairs_each_session_in_time_order_with_ties_in_recorded_order():
    labels = [_label("s1", 2.0, "write_file"), _label("s1", 1.0, "read_file"),
              _label("s1", 2.0, "list_directory")]
    scored = [_scored("s1", "read_file", 10), _scored("s1", "write_file", 20),
              _scored("s1", "list_directory", 5)]
    joined = ev.join_route(labels, scored)
    assert [(r["tool"], r["cell"]) for r in joined] == [
        ("read_file", "10"), ("write_file", "20"), ("list_directory", "5")]


def test_join_refuses_a_mismatch():
    with pytest.raises(ValueError):
        ev.join_route([_label("s1", 1.0, "read_file")], [_scored("s1", "write_file", 1)])
    with pytest.raises(ValueError):
        ev.join_route([_label("s1", 1.0, "read_file")], [])


def test_run_level_takes_each_runs_highest_score():
    rows = [
        {**_label("s1", 1, "read_file", "risky_v1", "r1", "unsafe_success"),
         **_scored("s1", "read_file", 100)},
        {**_label("s1", 2, "list_directory", "risky_v1", "r1", "unsafe_success"),
         **_scored("s1", "list_directory", 5)},
        {**_label("s2", 1, "read_file", "benign", "r2"), **_scored("s2", "read_file", 20)},
        {**_label("s3", 1, "read_file", "hard_neg_v2", "r3"), **_scored("s3", "read_file", 100)},
    ]
    result = ev.run_level(rows)
    assert result["runs"] == 3 and result["unsafe_runs"] == 1
    assert result["cell"]["risky_vs_benign"] == 1.0
    assert result["cell"]["risky_vs_hard_neg"] == 0.5  # a tie


def test_groups_and_auc_edges():
    assert ev.env_group("hard_neg_v3") == "hard_neg"
    assert ev.env_group("risky_v2") == "risky"
    with pytest.raises(ValueError):
        ev.env_group("calm")
    assert ev.auc([], [1.0]) is None
