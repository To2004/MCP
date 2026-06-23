"""Tests for the call-scoring module: tables, resolution, scoring, and corpus."""

from __future__ import annotations

from pathlib import Path

import pytest

import json

from mcp_security.call_scoring import load_tables, score_call
from mcp_security.call_scoring.corpus import SOURCES, score_corpus, summarize
from mcp_security.call_scoring.loader import Call, load_calls
from mcp_security.call_scoring.resolve import resolve_asset
from mcp_security.call_scoring.tables import STATUS_INVALID, STATUS_UNRESOLVED, TABLES_BUNDLE

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def tables():
    return load_tables()


def test_tables_load_expected_servers(tables):
    assert {"cbg_sqlite", "corp_filesystem", "law_firm_fs", "slack"} <= set(tables)
    cbg = tables["cbg_sqlite"]
    assert cbg.mcp_kind == "SQL database"
    assert "api_keys" in cbg.asset_sensitivity


def test_resolved_score_and_band_match_table_exactly(tables):
    """A resolved cell must return the table's verbatim score and band."""
    raw = json.loads(TABLES_BUNDLE.read_text())["tables"]["cbg_sqlite"]
    table = tables["cbg_sqlite"]
    call = Call("t", "1", "write_query", {"query": "UPDATE api_keys SET v='x'"})
    scored = score_call(call, table)
    assert scored.score == raw["cells"]["api_keys"]["write_query"]
    assert scored.band == raw["bands"]["api_keys"]["write_query"]


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


def test_score_unknown_tool_is_invalid(tables):
    table = tables["corp_filesystem"]
    call = Call(source="t", index="1", tool="readFile", args={"path": "/x.md"})
    scored = score_call(call, table)
    assert not scored.scorable
    assert scored.score is None
    assert scored.band == STATUS_INVALID
    assert "misconfiguration" in scored.reason


def test_unresolved_asset_is_not_fabricated(tables):
    """A known tool on an asset the table lacks must be unresolved, not invented."""
    table = tables["corp_filesystem"]
    scored = score_call(Call("t", "1", "read_file", {"path": "/src/app.py"}), table)
    assert not scored.scorable
    assert scored.score is None
    assert scored.band == STATUS_UNRESOLVED


def test_loader_captures_run_id():
    path = REPO_ROOT / "logs/proxy/sessions/law_firm_sim/calls.csv"
    calls = load_calls(path)
    assert any(c.run_id for c in calls), "run_id must be captured for traceability"


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


def test_score_corpus_ranks_and_segregates_statuses():
    scored = score_corpus()
    assert scored, "corpus should produce scored calls"
    # Scored calls (with a numeric score) must all rank above unscored statuses.
    last_scored = max(i for i, s in enumerate(scored) if s.score is not None)
    first_unscored = min(
        (i for i, s in enumerate(scored) if s.score is None), default=len(scored)
    )
    assert last_scored < first_unscored
    # Within the scored block, scores are non-increasing.
    block = [s.score for s in scored[: last_scored + 1]]
    assert block == sorted(block, reverse=True)
    assert "Resolved to a real table cell" in summarize(scored)


@pytest.mark.parametrize("rel_path, table_name", SOURCES)
def test_each_source_exists(rel_path, table_name):
    assert (REPO_ROOT / "logs/proxy" / rel_path).exists()
