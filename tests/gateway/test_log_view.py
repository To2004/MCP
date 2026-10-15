"""The readable views of a gateway log: one line per event (default) and grouped by session."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mcp_security.gateway import log_view
from mcp_security.gateway.log_file import MessageLog
from mcp_security.gateway.log_grouped import render_grouped

SESSION = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
WHO = {
    "gateway.agent_id": "agt-1",
    "gateway.agent": "alice",
    "user.id": "u-1",
    "gateway.app": "claude-code",
}
CALL_FIELDS = {"mcp.session.id": SESSION, "mcp.method.name": "tools/call"}


def _line(direction: str, exchange: str, ts: float, **fields: object) -> dict:
    base = {"schema": "gateway-log/3", "ts": ts, "gateway.route": "github", "log.level": "info"}
    return {**base, "gateway.direction": direction, "gateway.exchange_id": exchange, **fields}


def _call(exchange: str, ts: float, args: dict | None, **fields: object) -> dict:
    keys = fields.pop("arg_keys", sorted(args or {}))
    message = {"method": "tools/call", "params": {"name": "list_commits", "arguments": args}}
    return _line(
        "agent->server",
        exchange,
        ts,
        **WHO,
        **CALL_FIELDS,
        **{"gen_ai.tool.name": "list_commits", "gateway.arg_keys": keys},
        **({"message": message} if args is not None else {}),
        **fields,
    )


def _reply(exchange: str, ts: float, **fields: object) -> dict:
    timing = {"http.response.status_code": 200, "gateway.duration_s": 0.5}
    return _line(
        "server->agent",
        exchange,
        ts,
        **WHO,
        **CALL_FIELDS,
        **timing,
        **{"gen_ai.tool.name": "list_commits", "gateway.message_bytes": 900},
        **fields,
    )


DECISION = {"risk": 20.0001, "band": "medium", "cell": 20.0, "factor": 1.0, "asset": "repo-a"}
MISMATCH = {"gateway.notice": "session_agent_mismatch", "gateway.session_owner": "alice"}
RECORDS = [
    _line("gateway", "", 0.0, **{"gateway.notice": "gateway_started", "gateway.log_bodies": "all"}),
    _call("x1", 1.0, {"owner": "o", "repo": "r"}, **{"gateway.effects": {"which": {"repo": "r"}}}),
    _line(
        "gateway",
        "x1",
        1.0,
        **WHO,
        **{"mcp.session.id": SESSION, "gen_ai.tool.name": "list_commits"},
        **{"gateway.decision": {**DECISION, "basis": "named"}},
    ),
    _reply("x1", 1.5),
    _call("x2", 2.0, None, arg_keys=["repo"], **{"gateway.effects": {"which": {"repo": "sec"}}}),
    _reply("x2", 2.5, **{"error.type": "tool_error"}),
    _line(
        "gateway",
        "x3",
        3.0,
        **{"gateway.agent": "bob", "mcp.session.id": SESSION, "log.level": "warn"},
        **MISMATCH,
    ),
    _line(
        "gateway",
        "x4",
        4.0,
        **{"gateway.notice": "auth_failed", "gateway.reason": "unknown_token", "log.level": "warn"},
    ),
    _line("gateway", "", 5.0, **{"gateway.notice": "gateway_stopped"}),
]


@pytest.fixture
def lines() -> list[str]:
    return log_view.render(RECORDS, "github.jsonl", "hash chain intact").splitlines()


def _row(lines: list[str], text: str) -> str:
    return next(line for line in lines if text in line)


def test_one_line_per_record_under_a_header_with_id_columns(lines: list[str]) -> None:
    header = _row(lines, "TIME")
    for column in ("LEVEL", "AGENT_ID", "AGENT", "USER_ID", "SESSION", "REQUEST", "EVENT"):
        assert column in header
    rows = lines[lines.index(header) + 1 : lines.index(header) + 1 + len(RECORDS)]
    assert len(rows) == len(RECORDS) and all(row.startswith("00:00:0") for row in rows)


def test_a_call_line_names_who_where_what_and_its_arguments(lines: list[str]) -> None:
    call = _row(lines, "→ tools/call list_commits")
    for text in ("INFO", "agt-1", "alice", "u-1", SESSION[:8], "x1", "owner=o repo=r"):
        assert text in call
    assert "risk 20.0 medium" in _row(lines, "◆ verdict list_commits")
    assert "cell=20.0 factor=1.00 asset=repo-a basis=named" in _row(lines, "◆ verdict list_")


def test_a_call_logged_without_its_body_shows_names_and_typed_values(lines: list[str]) -> None:
    call = [line for line in lines if "→ tools/call" in line][1]
    assert "keys=repo which.repo=sec" in call
    assert "200 tool error" in _row(lines, "tool error")


def test_notices_are_warnings_with_their_details(lines: list[str]) -> None:
    takeover = _row(lines, "! session_agent_mismatch")
    assert "WARN" in takeover and "bob" in takeover and "owner=alice" in takeover
    assert "unknown_token" in _row(lines, "! auth_failed")


def test_the_summary_counts_calls_outcomes_and_notices(lines: list[str]) -> None:
    text = "\n".join(lines)
    assert "tool calls 2 (1 ok, 1 tool error)" in text
    assert "notices  session_agent_mismatch 1, auth_failed 1" in text  # start/stop not counted
    assert "highest risk  20.0 medium  list_commits" in text
    assert all(line == line.rstrip() for line in lines)


def test_colour_marks_warnings_only_when_asked() -> None:
    plain = log_view.render(RECORDS, "g", "ok")
    coloured = log_view.render(RECORDS, "g", "ok", color=True)
    assert "\033[" not in plain
    assert "\033[33m" in _row(coloured.splitlines(), "! session_agent_mismatch")


def test_the_grouped_view_reads_request_verdict_reply_per_session() -> None:
    view = render_grouped(RECORDS, "github.jsonl", "hash chain intact")

    assert f"== Session {SESSION[:8]}  alice (id agt-1, user u-1, app claude-code)" in view
    request = view.index("→ tools/call list_commits")
    assert request < view.index("◆ verdict    risk 20.0 medium") < view.index("← 200 ok")
    assert "arguments  repo  (values not logged)" in view
    assert view.index("✗ refused: token matches no agent") > view.index("== Outside any session")


def test_the_command_writes_either_view_with_the_chain_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = MessageLog(tmp_path)
    for record in RECORDS:
        log.write("github", record)
    log.close()
    for flags, marker in (([], "AGENT_ID"), (["--grouped"], "== Session")):
        out = tmp_path / "view.txt"
        argv = ["log_view", str(tmp_path / "github.jsonl"), *flags, "--out", str(out)]
        monkeypatch.setattr(sys, "argv", argv)

        log_view.main()

        text = out.read_text()
        assert "hash chain intact" in text and marker in text and "\033[" not in text
