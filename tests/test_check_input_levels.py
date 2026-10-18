"""Tests for the v13 run checks: scenario pairs and the real-call screen helpers."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_input_levels as c  # noqa: E402


def test_flatten_reads_list_items_of_objects():
    flat = c.flatten({"repo": "x", "attendees": [{"email": "a@b.c"}], "tags": ["t"]})
    assert flat["repo"] == '"x"' and flat["attendees[].email"] == '"a@b.c"'
    assert "tags[]" not in flat


def test_value_signal_sees_a_value_that_tells_risky_apart_and_not_a_unique_one():
    told = c.value_signal(["a", "a", "a", "b", "b", "b"], [True, True, True, False, False, False])
    assert told == 1.0
    unique = c.value_signal(["a", "b", "c", "d"], [True, False, True, False])
    assert unique == 0.5


def _run(tmp_path: Path) -> Path:
    rule = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
        {"min": 50, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
        {"min": 500, "max": None, "level": 5}]}
    tool = {"tool_name": "list", "arguments": [{"path": "limit", "rule": rule}]}
    (tmp_path / "slack.json").write_text(json.dumps({"tools": [tool]}))
    return tmp_path


def test_a_scenario_passes_when_the_risky_call_scores_higher_and_high_enough(tmp_path):
    run = _run(tmp_path)
    base = {"server": "slack", "tool": "list", "change": "x", "basis": "simple", "why": "w",
            "harmless": {"limit": 20}}
    up, small, missing = c.scenario_results(run, [
        {**base, "risky": {"limit": 1000}, "risky_at_least": 5},
        {**base, "risky": {"limit": 200}, "risky_at_least": 5},
        {**base, "server": "github", "risky": {"limit": 1000}}])
    assert up["passed"] and (up["harmless_level"], up["risky_level"]) == (2, 5)
    assert not small["passed"] and not missing["passed"]
