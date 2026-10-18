"""A gateway log grouped for reading: by session, one block per HTTP exchange.

Each session gets a header (agent id and name, user id, app, client, address); under it,
each exchange is one block in a fixed order — the request with its arguments and typed
effects, the framework's verdict, the reply — with any notice where it happened. Requests
outside a session (refused logins, unknown routes) come next, then a summary. Times are
UTC; ``[n]`` is the record's position in the log. ``log_view.py --grouped`` prints it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from mcp_security.gateway.log_text import (
    REASONS,
    RUN_NOTICES,
    SHORT_ID,
    clock,
    exchange_key,
    outcome,
    overview,
    pad,
    size_text,
    summary_lines,
    value_text,
)
from mcp_security.gateway.wire_log import CALL_METHOD, TO_AGENT, TO_SERVER

WIDTH = 100  # wrap continuation lines here
INDENT = " " * 21  # continuation lines start under the text after "hh:mm:ss.mmm  [nn]  "
WHO_FIELDS = (("id", "gateway.agent_id"), ("user", "user.id"), ("app", "gateway.app"))
NOTICE_TEXT = {
    "session_agent_mismatch": "⚠ {agent} is using {owner}'s session{ended}",
    "catalog_not_scanned": "⚠ tool list differs from the scanned one; saved to {file}",
    "upstream_unreachable": "⚠ upstream unreachable: {error}",
    "auth_failed": "✗ refused: {reason}",
    "unknown_route": "✗ unknown route /{route}",
}
BODILESS = {"GET": "GET  open a server→client stream", "DELETE": "DELETE  end the session"}


@dataclass
class Block:
    """One HTTP exchange: every record that shares a ``gateway.exchange_id``."""

    lines: list[tuple[int, dict]] = field(default_factory=list)

    def first(self, key: str) -> Any:
        return next((r[key] for _, r in self.lines if r.get(key) is not None), None)


def render_grouped(records: list[dict], title: str, chain: str) -> str:
    """The whole grouped view as text."""
    runs, blocks = _split(records)
    sessions: dict[str | None, list[Block]] = {}
    for block in blocks:
        sessions.setdefault(block.first("mcp.session.id"), []).append(block)
    out = [f"Gateway log  {title}", *overview(records, chain), "", *_runs(runs), ""]
    for session, members in sessions.items():
        if session is not None:
            out += [*_session_header(session, members), *_blocks(members), ""]
    if None in sessions:
        out += ["== Outside any session " + "=" * 60, *_blocks(sessions[None]), ""]
    out += summary_lines([r for b in blocks for _, r in b.lines], len(blocks))
    return "\n".join(line.rstrip() for line in out) + "\n"


def _split(records: list[dict]) -> tuple[list[tuple[int, dict]], list[Block]]:
    runs, blocks, by_id = [], [], {}
    for number, record in enumerate(records, start=1):
        if record.get("gateway.notice") in RUN_NOTICES:
            runs.append((number, record))
            continue
        key = exchange_key(record, number)
        if key not in by_id:
            by_id[key] = Block()
            blocks.append(by_id[key])
        by_id[key].lines.append((number, record))
    return runs, blocks


def _runs(runs: list[tuple[int, dict]]) -> list[str]:
    lines = []
    for number, record in runs:
        if record["gateway.notice"] == "gateway_stopped":
            lines.append(f"{clock(record):<12}  [{number:>2}]  ■ gateway stopped")
            continue
        artifacts = record.get("gateway.artifacts") or {}
        if record.get("gateway.effects_sha256"):
            artifacts = {**artifacts, "importance": record["gateway.effects_sha256"]}
        digests = "  ".join(f"{name} {digest[:SHORT_ID]}" for name, digest in artifacts.items())
        keyed = "keyed" if record.get("gateway.pseudonyms_keyed") else "UNKEYED"
        lines.append(f"{clock(record):<12}  [{number:>2}]  ▶ gateway started")
        lines.append(
            f"{INDENT}config {str(record.get('gateway.config_sha256', '?'))[:SHORT_ID]}  {digests}"
        )
        lines.append(
            f"{INDENT}bodies {record.get('gateway.log_bodies', '?')}  ·  pseudonyms {keyed}"
            f"  ·  identity {record.get('gateway.auth') or '?'}"
            + (f" ({record['gateway.oauth_issuer']})" if record.get("gateway.oauth_issuer") else "")
        )
    return lines


def _session_header(session: str, blocks: list[Block]) -> list[str]:
    first = blocks[0]
    who = str(first.first("gateway.agent") or "anonymous")
    extra = [f"{k} {first.first(f)}" for k, f in WHO_FIELDS if first.first(f)]
    head = (
        f"== Session {session[:SHORT_ID]}  {who}"
        + (f" ({', '.join(extra)})" if extra else "")
        + " "
    )
    wire = [
        f"client {first.first('gateway.client')}" if first.first("gateway.client") else None,
        str(first.first("user_agent.original") or ""),
        f"from {first.first('client.address')}" if first.first("client.address") else None,
        f"MCP {first.first('mcp.protocol.version')}"
        if first.first("mcp.protocol.version")
        else None,
    ]
    return [head + "=" * max(4, 83 - len(head)), "   " + "  |  ".join(w for w in wire if w)]


def _blocks(blocks: list[Block]) -> list[str]:
    owner = blocks[0].first("gateway.agent") if blocks else None
    out = []
    for block in blocks:
        out.append("")
        for index, (number, record) in enumerate(block.lines):
            stamp = clock(record) if index == 0 else " " * 12
            text = _line(record, owner)
            out.append(f"{stamp:<12}  [{number:>2}]  {text[0]}")
            out += [INDENT + more for more in text[1:]]
    return out


def _line(record: dict, owner: object) -> list[str]:
    direction = record.get("gateway.direction")
    if record.get("gateway.notice"):
        return [_notice(record)]
    if "gateway.decision" in record:
        return _verdict(record)
    if direction == TO_SERVER:
        return _request(record, owner)
    if direction == TO_AGENT:
        return [_reply(record)]
    return [json.dumps(record, ensure_ascii=False)[:100]]


def _request(record: dict, owner: object) -> list[str]:
    method, http = record.get("mcp.method.name"), record.get("http.request.method")
    tool = record.get("gen_ai.tool.name")
    if tool:
        what = f"{method} {tool}"
    else:
        what = method or BODILESS.get(str(http), str(http))
    agent = record.get("gateway.agent")
    by = f"   (by {agent})" if agent and owner and agent != owner else ""
    lines = [f"→ {pad(str(what) + by, 58)} {size_text(record.get('gateway.message_bytes'))}"]
    if method == CALL_METHOD:
        lines += _arguments(record)
        if record.get("gateway.effects"):
            args = ((record.get("message") or {}).get("params") or {}).get("arguments")
            effects = _effects(record["gateway.effects"], values=not isinstance(args, dict))
            lines += _wrap("effects    ", effects, sep="  ·  ")
        if record.get("gateway.tool_listed") is False:
            lines.append("⚠ tool was not in this session's tools/list")
    if record.get("gateway.header_mismatch"):
        lines.append(f"⚠ headers name another call: {', '.join(record['gateway.header_mismatch'])}")
    if record.get("trace_id"):
        lines.append(f"trace      {record['trace_id']} / {record.get('span_id')}")
    return lines


def _arguments(record: dict) -> list[str]:
    args = ((record.get("message") or {}).get("params") or {}).get("arguments")
    tag = f"#{record['gateway.args_hash'][:SHORT_ID]}" if record.get("gateway.args_hash") else ""
    if isinstance(args, dict):
        parts = [f"{k}={value_text(v)}" for k, v in sorted(args.items())] or ["(none)"]
    else:
        parts = [", ".join(record.get("gateway.arg_keys") or []) or "(none)", "(values not logged)"]
    return _wrap("arguments  ", [*parts, tag] if tag else parts)


def _wrap(label: str, parts: list[str], sep: str = "  ") -> list[str]:
    """``label`` then ``parts`` joined by ``sep``, broken into lines that fit ``WIDTH``;
    a continued line starts under the first part."""
    room, hang = WIDTH - len(INDENT), " " * len(label)
    lines, current, empty = [], label, True
    for part in parts:
        candidate = current + part if empty else current + sep + part
        if not empty and len(candidate) > room:
            lines.append(current)
            current = hang + part
        else:
            current = candidate
        empty = False
    return [*lines, current]


def _effects(effects: dict, values: bool) -> list[str]:
    """The typed fields; with ``values`` False, only which inputs carry them (the values
    are already on the arguments line)."""
    parts = []
    for name in ("which", "how_much", "action"):
        if effects.get(name):
            shown = (f"{k}={value_text(v)}" if values else k for k, v in effects[name].items())
            parts.append(f"{name}: " + ", ".join(shown))
    if effects.get("who_count"):
        parts.append(f"who: {effects['who_count']} recipient(s)")
    if "when_span_days" in effects:
        parts.append(f"when: {effects['when_span_days']:g} days")
    if effects.get("carried_bytes"):
        parts.append(f"carried: {size_text(effects['carried_bytes'])}")
    return parts


def _verdict(record: dict) -> list[str]:
    d = record["gateway.decision"]
    if "error" in d:
        return [f"◆ verdict failed: {d['error']}"]
    if d.get("risk") is None:
        return [f"◆ verdict    no score: {d.get('reasons', 'tool not in scan')}"]
    band = f" {d['band']}" if d.get("band") else ""
    head = f"◆ verdict    risk {d['risk']:.1f}{band}  =  cell {d['cell']:.1f} × factor {d['factor']:.2f}"
    match = record.get("gateway.catalog_match")
    details = [
        f"asset {d.get('asset')} ({d.get('basis')})",
        f"input level {d['input_level']} ({d.get('input_set_by')})" if d.get("input_level") else "",
        "catalog = scanned" if match is True else "catalog ≠ scanned" if match is False else "",
    ]
    return [head, *_wrap("", [part for part in details if part], sep="  ·  ")]


def _reply(record: dict) -> str:
    status = record.get("http.response.status_code")
    kept = (
        ""
        if record.get("message") is not None or not record.get("gateway.message_bytes")
        else "  body not kept"
    )
    timing = f"{record['gateway.duration_s']:.2f} s" if "gateway.duration_s" in record else ""
    size = size_text(record.get("gateway.message_bytes"))
    ended = outcome(record) or record.get("mcp.method.name") or ""
    if record.get("mcp.method.name") == "tools/list" and ended.endswith("tools"):
        ended = f"tools/list: {ended}"
    return f"← {pad(f'{status} {ended}', 47)} {timing:>9}  {size}{kept}"


def _notice(record: dict) -> str:
    notice = record["gateway.notice"]
    template = NOTICE_TEXT.get(notice) or f"• {notice}"
    return template.format(
        agent=f"{record.get('gateway.agent')}"
        + (f" ({record['user.id']})" if record.get("user.id") else ""),
        owner=record.get("gateway.session_owner"),
        ended=" (after it was ended)" if record.get("gateway.session_ended") else "",
        file=record.get("gateway.catalog_file"),
        error=f"{record.get('error.type')}: {record.get('gateway.error')}",
        reason=REASONS.get(str(record.get("gateway.reason")), record.get("gateway.reason")),
        route=record.get("gateway.route"),
    )
