"""The static side of the gateway demo: catalog from the log, remote names, levels -> cells."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_security.gateway.catalog import extract_catalog
from mcp_security.gateway.github_remote import remote_policy, translate_call
from mcp_security.gateway.framework import load_breadth
from mcp_security.gateway.static_cells import NOT_APPLICABLE, cells_from_levels
from mcp_security.gateway.wire_log import (
    TO_AGENT,
    TO_SERVER,
    Exchange,
    SessionBook,
    build_record,
    catalog_digest,
)


def _line(session: str, direction: str, message: dict) -> dict:
    return {"mcp.session.id": session, "gateway.direction": direction, "message": message}


def _list_exchange(session: str, rpc_id: int, tools: list[str]) -> list[dict]:
    request = {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/list"}
    reply = {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": [{"name": t} for t in tools]}}
    return [_line(session, TO_SERVER, request), _line(session, TO_AGENT, reply)]


def test_catalog_is_the_latest_session_with_all_its_pages() -> None:
    log = (
        _list_exchange("old", 1, ["stale_tool"])
        + _list_exchange("new", 1, ["a", "b"])
        + _list_exchange("new", 2, ["c"])  # nextCursor page: a separate request and reply
    )
    assert [t["name"] for t in extract_catalog(log)["tools"]] == ["a", "b", "c"]


def test_catalog_digest_changes_when_a_tool_changes() -> None:
    before = {"tools": [{"name": "a", "description": "reads"}]}
    after = {"tools": [{"name": "a", "description": "reads and deletes"}]}
    assert catalog_digest(before) != catalog_digest(after)


def test_log_without_a_tool_list_is_an_error() -> None:
    with pytest.raises(ValueError, match="no tools/list"):
        extract_catalog([_line("s", TO_SERVER, {"method": "initialize", "id": 0})])


def test_merged_tool_gets_its_method_and_renamed_arguments() -> None:
    tool, args = translate_call(
        "get_pull_request_status", {"owner": "o", "repo": "r", "pull_number": 7}
    )
    assert tool == "pull_request_read"
    assert args == {"method": "get_status", "owner": "o", "repo": "r", "pullNumber": 7}


def test_list_issues_drops_page_and_speaks_the_remote_state_enum() -> None:
    assert translate_call("list_issues", {"page": 2, "per_page": 30, "state": "open"}) == (
        "list_issues",
        {"perPage": 30, "state": "OPEN"},
    )
    assert "state" not in translate_call("list_issues", {"state": "all"})[1]


def test_unchanged_tool_passes_through() -> None:
    assert translate_call("get_file_contents", {"path": "a"}) == (
        "get_file_contents",
        {"path": "a"},
    )


POLICY = """# org

## Classification policy

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `prs` | Pull requests | `get_pull_request`, `get_pull_request_files`, `merge_pull_request` | — | I>C>A |

- `get_pull_request` returns null mergeability.

## Input policy

| Asset | Description | Tools |
|---|---|---|
| `prs` | Pull requests | `get_pull_request`, `get_pull_request_status` |

| Tool | Argument | Constraint | Which asset it gates |
|---|---|---|---|
| `search_code` | `q` + `per_page` | a path like `.env`, `get_issue` named here | `prs` |
"""


def test_remote_policy_renames_register_tools_once_and_keeps_the_wording() -> None:
    out = remote_policy(POLICY)
    assert "| `pull_request_read`, `merge_pull_request` |" in out
    assert "- `pull_request_read` returns null mergeability." in out


def test_remote_policy_keeps_the_input_section_with_remote_names() -> None:
    out = remote_policy(POLICY)
    assert "| `prs` | Pull requests | `pull_request_read` |" in out  # Table 2, merged once
    # Input rules: arguments renamed in place, constraint text kept whole.
    assert "| `search_code` | `query` + `perPage` | a path like `.env`, `issue_read` named" in out


def _scan(reach: list[dict]) -> dict:
    return {
        "assets": [{"asset": "repo", "sensitivity": 4}],
        "tools": [{"tool": "read", "impact": 2}, {"tool": "push", "impact": 4}],
        "reach": reach,
    }


def test_cell_is_sensitivity_times_blast_times_impact_with_v5_band() -> None:
    matrix = cells_from_levels(
        _scan([{"tool": "push", "asset": "repo", "reaches": True, "blast": 5}])
    )
    assert matrix["cells"]["repo"]["push"] == 80.0  # 4 x 5 x 4
    assert matrix["bands"]["repo"]["push"] == "high"
    assert matrix["score_max"] == 125.0


def test_unreached_and_unanswered_pairs_have_no_cell() -> None:
    matrix = cells_from_levels(
        _scan(
            [
                {"tool": "read", "asset": "repo", "reaches": False, "blast": None},
                {"tool": "push", "asset": "repo", "reaches": None, "blast": None},
            ]
        )
    )
    assert matrix["cells"]["repo"] == {"read": None, "push": None}
    assert set(matrix["bands"]["repo"].values()) == {NOT_APPLICABLE}
    assert matrix["unanswered"] == ["push|repo"]


def test_breadth_file_is_keyed_by_tool_then_input(tmp_path: Path) -> None:
    spec = {"tools": {"list_commits": {"inputs": [{"name": "perPage", "kind": "count"}]}}}
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    assert load_breadth(path) == {"list_commits": {"perPage": {"name": "perPage", "kind": "count"}}}


def test_a_call_to_a_tool_the_session_never_saw_listed_is_flagged() -> None:
    book = SessionBook()
    listing = Exchange("github", "alice", "s", "POST", requests={"1": ("tools/list", None)})
    reply = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "read"}]}}
    listed = build_record(listing, book, TO_AGENT, 200, reply)
    assert listed["gateway.catalog_sha256"] == catalog_digest({"tools": [{"name": "read"}]})

    def call(tool: str) -> dict:
        message = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool}}
        return build_record(
            Exchange("github", "alice", "s", "POST"), book, TO_SERVER, None, message
        )

    assert call("read")["gateway.tool_listed"] is True
    assert call("delete_everything")["gateway.tool_listed"] is False


def test_tool_error_and_rpc_error_are_told_apart() -> None:
    ex = Exchange("github", "alice", "s", "POST", requests={"2": ("tools/call", "read")})
    tool_error = {"jsonrpc": "2.0", "id": 2, "result": {"content": [], "isError": True}}
    bad_args = {"jsonrpc": "2.0", "id": 2, "error": {"code": -32602, "message": "bad args"}}
    crashed = {"jsonrpc": "2.0", "id": 2, "error": {"code": -32603, "message": "internal"}}

    assert build_record(ex, SessionBook(), TO_AGENT, 200, tool_error)["error.type"] == "tool_error"
    # OpenTelemetry: -32602 is the caller's mistake, not an error; the code is still logged.
    caller_mistake = build_record(ex, SessionBook(), TO_AGENT, 200, bad_args)
    assert caller_mistake["rpc.response.status_code"] == "-32602"
    assert "error.type" not in caller_mistake
    server_error = build_record(ex, SessionBook(), TO_AGENT, 200, crashed)
    assert (server_error["rpc.response.status_code"], server_error["error.type"]) == (
        "-32603",
        "-32603",
    )
