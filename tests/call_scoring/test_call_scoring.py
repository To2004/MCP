"""Tests for the call-scoring module: scan loading, resolution, scoring, corpus.

Calls are scored against the scanner's matrices (``reports/scan/``), never the
committed design-time tables. These tests build small synthetic scan matrices in
memory so they do not depend on a real (LLM-only) scan having been run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_security.call_scoring import load_scan, score_call
from mcp_security.call_scoring.corpus import SOURCES, score_corpus, summarize
from mcp_security.call_scoring.loader import Call, load_calls
from mcp_security.call_scoring.resolve import resolve_asset
from mcp_security.call_scoring.tables import STATUS_INVALID, STATUS_UNRESOLVED, table_from_dict

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fs_scan():
    """A tiny filesystem scan matrix: .pem is a crown-jewel, .md is ordinary."""
    return table_from_dict(
        "fs_corp_filesystem",
        {
            "server": "secure-filesystem-server",
            "mcp_kind": "filesystem",
            "tool_impact": {"read_file": 1, "write_file": 3, "edit_file": 3},
            "asset_sensitivity": {".pem": 5, ".md": 2},
            "cells": {
                ".pem": {"read_file": 10.0, "write_file": 60.0, "edit_file": 60.0},
                ".md": {"read_file": 2.0, "write_file": 12.0, "edit_file": 12.0},
            },
            "bands": {
                ".pem": {"read_file": "medium", "write_file": "critical", "edit_file": "critical"},
                ".md": {"read_file": "low", "write_file": "medium", "edit_file": "medium"},
            },
        },
    )


def _sqlite_scan():
    """A tiny sqlite scan matrix: api_keys is a crown-jewel table."""
    return table_from_dict(
        "sqlite_cbg_sqlite",
        {
            "server": "cbg-sqlite-server",
            "mcp_kind": "SQL database",
            "tool_impact": {"read_query": 1, "write_query": 3},
            "asset_sensitivity": {"api_keys": 5, "employees": 4},
            "cells": {
                "api_keys": {"read_query": 15.0, "write_query": 60.0},
                "employees": {"read_query": 8.0, "write_query": 48.0},
            },
            "bands": {
                "api_keys": {"read_query": "high", "write_query": "critical"},
                "employees": {"read_query": "medium", "write_query": "high"},
            },
        },
    )


# --- resolution -------------------------------------------------------------
def test_resolve_filesystem_extension():
    table = _fs_scan()
    call = Call(source="t", index="1", tool="read_file", args={"path": "/data/secrets.pem"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved and resolved.asset == ".pem"
    assert resolved.sensitivity == table.asset_sensitivity[".pem"]


def _fs_scan_by_file():
    """A per-file (take2) scan: assets are relative paths, not extensions."""
    return table_from_dict(
        "fs_corp_filesystem",
        {
            "server": "secure-filesystem-server", "mcp_kind": "filesystem",
            "tool_impact": {"read_text_file": 1, "write_file": 3},
            "asset_sensitivity": {"sensitive/security/private_key.pem": 5,
                                  "projects/known_defects.csv": 3},
            "cells": {"sensitive/security/private_key.pem": {"read_text_file": 5.0, "write_file": 60.0},
                      "projects/known_defects.csv": {"read_text_file": 3.0, "write_file": 36.0}},
            "bands": {"sensitive/security/private_key.pem": {"read_text_file": "medium", "write_file": "critical"},
                      "projects/known_defects.csv": {"read_text_file": "low", "write_file": "high"}},
        },
    )


def test_resolve_per_file_by_path_suffix():
    """take2: a Windows call path resolves to the matching scanned file."""
    table = _fs_scan_by_file()
    call = Call("t", "1", "read_text_file",
                {"path": r"C:\Users\u\GitHub\MCP\demo\corp_filesystem_sim\sensitive\security\private_key.pem"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved and resolved.asset == "sensitive/security/private_key.pem"
    assert resolved.sensitivity == 5


def test_resolve_per_file_unmatched_is_unresolved():
    table = _fs_scan_by_file()
    resolved = resolve_asset(Call("t", "1", "read_text_file", {"path": "/tmp/not_scanned.txt"}), table)
    assert not resolved.resolved


def _fs_scan_with_dirs():
    """A take2 scan that also carries directory-scope assets (trailing slash)."""
    return table_from_dict(
        "fs_corp_filesystem",
        {
            "server": "secure-filesystem-server", "mcp_kind": "filesystem",
            "tool_impact": {"read_text_file": 1, "list_directory": 1, "directory_tree": 1},
            "asset_sensitivity": {
                "onboarding/org_chart.png": 2,
                "onboarding/": 2, "sensitive/security/": 5, "/": 4,
            },
            "cells": {a: {t: 1.0 for t in ("read_text_file", "list_directory", "directory_tree")}
                      for a in ("onboarding/org_chart.png", "onboarding/", "sensitive/security/", "/")},
            "bands": {
                "onboarding/org_chart.png": {"read_text_file": "low", "list_directory": "low",
                                             "directory_tree": "low"},
                "onboarding/": {"read_text_file": "low", "list_directory": "medium",
                                "directory_tree": "medium"},
                "sensitive/security/": {"read_text_file": "high", "list_directory": "high",
                                        "directory_tree": "high"},
                "/": {"read_text_file": "medium", "list_directory": "high", "directory_tree": "high"},
            },
        },
    )


def test_resolve_directory_call_to_scope():
    """A folder-targeted enumeration resolves to the directory-scope asset."""
    table = _fs_scan_with_dirs()
    call = Call("t", "1", "list_directory",
                {"path": r"C:\Users\u\demo\corp_filesystem_sim\sensitive\security"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved and resolved.asset == "sensitive/security/"
    assert resolved.sensitivity == 5


def test_resolve_unenumerated_file_falls_back_to_ancestor_scope():
    """A file the scan never enumerated resolves to its nearest scanned folder."""
    table = _fs_scan_with_dirs()
    call = Call("t", "1", "read_text_file",
                {"path": r"C:\Users\u\demo\corp_filesystem_sim\onboarding\policies.pdf"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved and resolved.asset == "onboarding/"
    assert "ancestor" in resolved.basis


def test_resolve_store_root_scope_is_last_resort():
    """An op on the store root (no nearer folder) resolves to the root scope."""
    table = _fs_scan_with_dirs()
    call = Call("t", "1", "directory_tree", {"path": r"C:\Users\u\demo\corp_filesystem_sim"})
    resolved = resolve_asset(call, table)
    assert resolved.resolved and resolved.asset == "/"


def _declarative_scan(kind: str, assets: dict[str, int], tools: list[str]):
    """A minimal scan for a declarative kind (slack/calendar/github)."""
    return table_from_dict(
        f"{kind}_cbg",
        {
            "server": f"{kind}:cbg", "mcp_kind": "inferred free text", "server_kind": kind,
            "tool_impact": {t: 1 for t in tools},
            "asset_sensitivity": assets,
            "cells": {a: {t: 1.0 for t in tools} for a in assets},
            "bands": {a: {t: "low" for t in tools} for a in assets},
        },
    )


def test_resolve_calendar_by_arg_and_default_scope():
    table = _declarative_scan("calendar", {"personal": 2, "executive": 4, "contacts": 4},
                              ["list_events", "create_event", "access_contacts"])
    # named calendar
    r = resolve_asset(Call("t", "1", "list_events", {"calendar": "executive"}), table)
    assert r.resolved and r.asset == "executive"
    # no calendar arg -> personal default scope (still scorable)
    r = resolve_asset(Call("t", "2", "create_event", {"title": "x", "attendees": ["a"]}), table)
    assert r.resolved and r.asset == "personal"
    # access_contacts pins the directory scope regardless of args
    r = resolve_asset(Call("t", "3", "access_contacts", {}), table)
    assert r.resolved and r.asset == "contacts"


def test_resolve_github_by_repo_arg():
    table = _declarative_scan("github", {"backend-api": 4, "infra-config": 5},
                              ["get_file_contents", "push_files"])
    r = resolve_asset(Call("t", "1", "get_file_contents", {"repo": "org/infra-config"}), table)
    assert r.resolved and r.asset == "infra-config"
    r = resolve_asset(Call("t", "2", "push_files", {"repo": "unknown-repo"}), table)
    assert not r.resolved


def test_server_kind_dispatch_beats_freetext_mcp_kind():
    """server_kind drives dispatch even when mcp_kind is unrelated free text."""
    table = _declarative_scan("slack", {"exec-private": 5}, ["slack_get_channel_history"])
    # mcp_kind is "inferred free text" (no 'slack'); server_kind='slack' must win.
    r = resolve_asset(Call("t", "1", "slack_get_channel_history", {"channel": "exec-private"}),
                      table)
    assert r.resolved and r.asset == "exec-private"


def test_resolve_filesystem_unknown_extension():
    resolved = resolve_asset(
        Call(source="t", index="1", tool="read_file", args={"path": "/src/app.py"}), _fs_scan()
    )
    assert not resolved.resolved


def test_resolve_sql_from_query():
    resolved = resolve_asset(
        Call(source="t", index="1", tool="read_query", args={"query": "SELECT * FROM employees"}),
        _sqlite_scan(),
    )
    assert resolved.resolved and resolved.asset == "employees"


# --- scoring ----------------------------------------------------------------
def test_resolved_score_and_band_match_scan_exactly():
    """A resolved cell returns the scan's verbatim score and band."""
    table = _sqlite_scan()
    scored = score_call(Call("t", "1", "write_query", {"query": "UPDATE api_keys SET v='x'"}), table)
    assert scored.score == table.cells["api_keys"]["write_query"]
    assert scored.band == table.bands["api_keys"]["write_query"] == "critical"
    assert scored.scorable and scored.asset == "api_keys"


def test_score_unknown_tool_is_invalid():
    scored = score_call(Call("t", "1", "readFile", {"path": "/x.md"}), _fs_scan())
    assert not scored.scorable and scored.score is None
    assert scored.band == STATUS_INVALID and "misconfiguration" in scored.reason


def test_unresolved_asset_is_not_fabricated():
    scored = score_call(Call("t", "1", "read_file", {"path": "/src/app.py"}), _fs_scan())
    assert not scored.scorable and scored.score is None
    assert scored.band == STATUS_UNRESOLVED


def test_score_read_below_write_on_same_asset():
    table = _sqlite_scan()
    read = score_call(Call("t", "1", "read_query", {"query": "SELECT * FROM employees"}), table)
    write = score_call(Call("t", "2", "write_query", {"query": "UPDATE employees SET x=1"}), table)
    assert read.score is not None and write.score is not None
    assert read.score <= write.score


def _limit_rubric():
    """A read_query rubric where a large/unbounded row limit is high risk."""
    from mcp_security.param_scoring import ToolRubric
    from mcp_security.param_scoring.rubric import Cutoff, ParamRubric

    return ToolRubric(
        "read_query",
        (ParamRubric("query", "medium", "parsed_limit",
                     (Cutoff(100, "medium"), Cutoff(1000, "high"))),),
    )


def test_param_risk_amplifies_score_numerically():
    table = _sqlite_scan()
    # Bulk read of employees: cell score 8.0, param risk high -> x2.0 -> final 16.0.
    call = Call("t", "1", "read_query", {"query": "SELECT * FROM employees LIMIT 5000"})
    scored = score_call(call, table, _limit_rubric())
    assert scored.score == 8.0            # raw cell number unchanged
    assert scored.band == "medium"        # cell band unchanged (cosmetic)
    assert scored.param_band == "high"
    assert scored.param_multiplier == 2.0
    assert scored.final_score == 16.0     # 8.0 * 2.0 — the number ranking uses


def test_ranking_is_by_number_not_band():
    from mcp_security.call_scoring.corpus import _rank_key

    table = _sqlite_scan()
    # Plain read of api_keys: score 15, band 'high', no param -> final 15.
    plain = score_call(Call("t", "1", "read_query", {"query": "SELECT * FROM api_keys LIMIT 1"}),
                       table, None)
    # Bulk read of employees: score 8, band 'medium', param x2 -> final 16.
    bulk = score_call(Call("t", "2", "read_query", {"query": "SELECT * FROM employees LIMIT 5000"}),
                      table, _limit_rubric())
    ranked = sorted([plain, bulk], key=_rank_key, reverse=True)
    # By the NUMBER, the bulk read (16.0) outranks api_keys (15.0) even though its
    # band ('medium') is lower than the plain call's ('high').
    assert ranked[0] is bulk
    assert bulk.final_score > plain.final_score
    assert bulk.band == "medium" and plain.band == "high"


def test_persona_is_carried_through():
    call = Call("t", "1", "read_file", {"path": "/k.pem"}, persona="Mallory (Attacker)")
    scored = score_call(call, _fs_scan())
    assert scored.persona == "Mallory (Attacker)"


# --- loader -----------------------------------------------------------------
def test_loader_captures_run_id():
    calls = load_calls(REPO_ROOT / "logs/proxy/sessions/law_firm_sim/calls.csv")
    assert any(c.run_id for c in calls), "run_id must be captured for traceability"


def test_loader_reads_raw_session_schema():
    calls = load_calls(REPO_ROOT / "logs/proxy/sessions/cbg_sqlite_sim/calls.csv")
    assert calls and all(isinstance(c, Call) and c.tool for c in calls)


# --- scan loading + corpus --------------------------------------------------
def test_load_scan_roundtrip(tmp_path):
    import json

    path = tmp_path / "fs_corp_filesystem.json"
    path.write_text(json.dumps({
        "server": "secure-filesystem-server", "mcp_kind": "filesystem",
        "tool_impact": {"read_file": 1}, "asset_sensitivity": {".pem": 5},
        "cells": {".pem": {"read_file": 10.0}}, "bands": {".pem": {"read_file": "medium"}},
    }), encoding="utf-8")
    table = load_scan(path)
    assert table.mcp_kind == "filesystem" and table.cell("read_file", ".pem") == (10.0, "medium")


def test_score_corpus_ranks_and_segregates_statuses():
    scans = {"fs_corp_filesystem": _fs_scan(), "sqlite_cbg_sqlite": _sqlite_scan()}
    # rubrics={} isolates this test from any parameter rubrics on disk.
    scored = score_corpus(scans=scans, rubrics={})
    assert scored, "corpus should produce scored calls"
    last_scored = max(i for i, s in enumerate(scored) if s.score is not None)
    first_unscored = min((i for i, s in enumerate(scored) if s.score is None), default=len(scored))
    assert last_scored < first_unscored
    block = [s.score for s in scored[: last_scored + 1]]
    assert block == sorted(block, reverse=True)
    assert "Resolved to a scanned cell" in summarize(scored)


@pytest.mark.parametrize("rel_path, scan_name", SOURCES)
def test_each_source_exists(rel_path, scan_name):
    assert (REPO_ROOT / "logs/proxy" / rel_path).exists()
