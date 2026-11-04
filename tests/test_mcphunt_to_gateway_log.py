"""Tests for scripts/mcphunt_to_gateway_log.py: MCPHunt traces -> gateway-log/3."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mcphunt_to_gateway_log as m  # noqa: E402

from mcp_security.gateway.log_file import read_log  # noqa: E402
from mcp_security.gateway.score import pair_calls  # noqa: E402

T0 = 1_777_000_000.0


def _event(server: str, tool: str, args: object, end: float, success: bool = True) -> dict:
    return {"turn": 1, "server": server, "tool": tool, "args": args, "success": success,
            "latency_ms": 500, "timestamp": end, "canary_in_args": tool == "write_file",
            "canary_in_result": False}


def _trace(trace_id: str, env: str, stamp: str, events: list[dict]) -> dict:
    return {"trace_id": trace_id, "task_id": f"task_{trace_id}", "task_category": "devops",
            "risk_mechanism": "file_to_file", "env_type": env, "outcome": "safe_success",
            "collection_timestamp": stamp, "events": events}


@pytest.fixture
def traces_dir(tmp_path: Path) -> Path:
    """Two agents; agent a has two runs over two servers, one failed call, one unroutable."""
    root = tmp_path / "traces"
    root.mkdir()
    run1 = _trace("r1", "risky_v1", "2026-04-25T06:00:00Z", [
        _event("filesystem", "read_file", {"path": "/ws/project_alpha/.env"}, T0 + 1),
        _event("filesystem", "write_file", {"path": "/ws/notes/x.md", "content": "k"}, T0 + 3),
        _event("sqlite", "read_query", {"query": "SELECT * FROM users"}, T0 + 5, success=False),
        _event("unknown", "file_write", {"path": "/ws/y"}, T0 + 6),
    ])
    run2 = _trace("r2", "benign", "2026-04-25T07:00:00Z", [
        _event("filesystem", "list_directory", {"path": "/ws"}, T0 + 3600),
        _event("filesystem", "read_file", "not-an-object", T0 + 3602),
    ])
    (root / "agent_a.json").write_text(json.dumps({"traces": [run2, run1]}))
    run3 = _trace("r3", "hard_neg_v1", "2026-04-26T06:00:00Z", [
        _event("filesystem", "read_file", {"path": "/ws/README.md"}, T0 + 10),
    ])
    (root / "agent_b.json").write_text(json.dumps({"traces": [run3]}))
    return root


def test_real_clock_logs_pair_back_into_the_recorded_calls(traces_dir: Path, tmp_path: Path):
    out = tmp_path / "real"
    summary = m.convert(traces_dir, out, "real", m.DEFAULT_DAYS, m.DEFAULT_SEED)
    assert summary["calls"] == {"filesystem": 5, "sqlite": 1}
    assert summary["skipped"] == {"unknown_server": 1, "args_not_object": 1}

    calls = pair_calls(read_log(out / "filesystem.jsonl"))
    assert [c["tool"] for c in calls] == [
        "read_file", "write_file", "read_file", "list_directory", "read_file"]
    assert {c["agent"] for c in calls} == {"agent_a", "agent_b"}
    assert all(c["outcome"] == "ok" for c in calls)
    assert calls[0]["args"] == {"path": "/ws/project_alpha/.env"}
    assert calls[0]["ts"] == pytest.approx(T0 + 0.5)  # stamped on return, minus latency
    assert calls[-1]["args"] == {}  # an argument that was not an object

    failed = pair_calls(read_log(out / "sqlite.jsonl"))
    assert [c["outcome"] for c in failed] == ["tool_error"]


def test_each_session_opens_with_initialize_before_its_first_call(traces_dir: Path,
                                                                  tmp_path: Path):
    out = tmp_path / "real"
    m.convert(traces_dir, out, "real", m.DEFAULT_DAYS, m.DEFAULT_SEED)
    records = read_log(out / "filesystem.jsonl")
    assert [r["ts"] for r in records] == sorted(r["ts"] for r in records)
    first_seen: dict[str, str] = {}
    for record in records:
        session = record.get("mcp.session.id")
        if session and session not in first_seen:
            first_seen[session] = record["mcp.method.name"]
    assert set(first_seen.values()) == {"initialize"}
    assert all(r["schema"] == "gateway-log/3" for r in records)


def test_spread_clock_is_seeded_keeps_run_timing_and_stays_in_the_window(traces_dir: Path,
                                                                         tmp_path: Path):
    days = 10
    m.convert(traces_dir, tmp_path / "s1", "spread", days, seed=3)
    m.convert(traces_dir, tmp_path / "s2", "spread", days, seed=3)
    first = (tmp_path / "s1" / "filesystem.jsonl").read_text()
    assert first == (tmp_path / "s2" / "filesystem.jsonl").read_text()

    calls = pair_calls(read_log(tmp_path / "s1" / "filesystem.jsonl"))
    assert all(m.SPREAD_START <= c["ts"] < m.SPREAD_START + days * m.DAY_S for c in calls)
    run1 = [c for c in calls if c["tool"] in ("read_file", "write_file")
            and c["agent"] == "agent_a" and c["args"] != {}]
    assert run1[1]["ts"] - run1[0]["ts"] == pytest.approx(2.0)  # timing inside a run kept


def test_label_rows_share_session_and_ts_with_the_log(traces_dir: Path, tmp_path: Path):
    out = tmp_path / "real"
    m.convert(traces_dir, out, "real", m.DEFAULT_DAYS, m.DEFAULT_SEED)
    with (out / "calls.csv").open(newline="") as handle:
        labels = {(r["session"], float(r["ts"])): r for r in csv.DictReader(handle)
                  if r["route"] == "filesystem"}
    calls = pair_calls(read_log(out / "filesystem.jsonl"))
    joined = [labels[(c["session"], c["ts"])] for c in calls]
    assert [row["env_type"] for row in joined] == [
        "risky_v1", "risky_v1", "hard_neg_v1", "benign", "benign"]
    assert joined[1]["canary_in_args"] == "True"


def test_bad_inputs_fail_loudly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        m.load_traces(tmp_path)
    with pytest.raises(ValueError):
        m.convert(tmp_path, tmp_path / "o", "lunar", 1, 0)
