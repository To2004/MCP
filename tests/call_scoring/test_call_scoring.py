"""Tests for the call-scoring module: tables, resolution, scoring, and corpus."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_security.call_scoring import load_tables, score_call
from mcp_security.call_scoring.corpus import SOURCES, score_corpus, summarize
from mcp_security.call_scoring.loader import Call, load_calls
from mcp_security.call_scoring.resolve import resolve_asset
from mcp_security.call_scoring.tables import band_for_score

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def tables():
    return load_tables()


def test_tables_load_expected_servers(tables):
    assert {"cbg_sqlite", "corp_filesystem", "law_firm_fs", "slack"} <= set(tables)
    cbg = tables["cbg_sqlite"]
    assert cbg.mcp_kind == "SQL database"
    assert "api_keys" in cbg.asset_sensitivity


def test_band_for_score_thresholds():
    thresholds = {"low": 6, "medium": 18, "high": 36}
    assert band_for_score(2, thresholds) == "low"
    assert band_for_score(6, thresholds) == "medium"
    assert band_for_score(18, thresholds) == "high"
    assert band_for_score(40, thresholds) == "critical"


def test_resolve_filesystem_extension(tables):
    table = tables["corp_filesystem"]
    call = Call(source="t", index="1", tool="read_file", args={"path": "/data/secrets.pem"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved
    assert resolved.asset == ".pem"
    assert resolved.sensitivity == table.asset_sensitivity[".pem"]


def test_resolve_filesystem_unknown_extension(tables):
    table = tables["corp_filesystem"]
    call = Call(source="t", index="1", tool="read_file", args={"path": "/src/app.py"})
    resolved = resolve_asset(call, table)
    assert not resolved.resolved


def test_resolve_sql_from_query(tables):
    table = tables["cbg_sqlite"]
    call = Call(source="t", index="1", tool="read_query", args={"query": "SELECT * FROM employees"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved
    assert resolved.asset == "employees"


def test_score_critical_cell_matches_table(tables):
    """A known critical cell (api_keys x write_query) must score as critical."""
    table = tables["cbg_sqlite"]
    call = Call(
        source="t",
        index="1",
        tool="write_query",
        args={"query": "UPDATE api_keys SET v='x'"},
    )
    scored = score_call(call, table)
    assert scored.scorable
    assert scored.asset == "api_keys"
    assert scored.band == "critical"


def test_score_unknown_tool_is_unscorable(tables):
    table = tables["corp_filesystem"]
    call = Call(source="t", index="1", tool="readFile", args={"path": "/x.md"})
    scored = score_call(call, table)
    assert not scored.scorable
    assert scored.band == "invalid"
    assert "misconfiguration" in scored.reason


def test_score_read_below_write_on_same_asset(tables):
    """Reading an asset must never out-score writing it (impact ordering holds)."""
    table = tables["cbg_sqlite"]
    read = score_call(Call("t", "1", "read_query", {"query": "SELECT * FROM employees"}), table)
    write = score_call(Call("t", "2", "write_query", {"query": "UPDATE employees SET x=1"}), table)
    assert read.score is not None and write.score is not None
    assert read.score <= write.score


def test_loader_reads_raw_session_schema():
    path = REPO_ROOT / "logs/proxy/sessions/cbg_sqlite_sim/calls.csv"
    calls = load_calls(path)
    assert calls
    assert all(isinstance(c, Call) and c.tool for c in calls)


def test_score_corpus_runs_and_summarizes():
    scored = score_corpus()
    assert scored, "corpus should produce scored calls"
    # Sorted descending by score (unscorable sink to the bottom as -1).
    scores = [s.score if s.score is not None else -1.0 for s in scored]
    assert scores == sorted(scores, reverse=True)
    assert "Scored" in summarize(scored)


@pytest.mark.parametrize("rel_path, table_name", SOURCES)
def test_each_source_exists(rel_path, table_name):
    assert (REPO_ROOT / "logs/proxy" / rel_path).exists()
