"""A gateway log rendered for people, the way a normal log reads: one line per event.

Every record becomes one row in aligned columns — time, level, who (agent id and name,
user id), which session and request, the event, its result, how long it took and how
big it was — and ends with ``key=value`` details (arguments, the verdict's parts, a
notice's reason). Ids are the log's own: the agent id from the config, the session and
request ids as the pseudonyms the log holds, shortened to their first characters. Colour
marks the level when printing to a terminal. ``--grouped`` gives the other view instead:
grouped by session, one block per exchange (``log_grouped.py``).

The JSONL file stays the record (append-only, chained); this only reads it.

    uv run python -m mcp_security.gateway.log_view <log.jsonl> [--grouped] [--out view.txt]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mcp_security.gateway.log_file import read_log, verify_chain
from mcp_security.gateway.log_grouped import render_grouped
from mcp_security.gateway.log_text import (
    RUN_NOTICES,
    SHORT_ID,
    call_arguments,
    clock,
    exchange_key,
    level_of,
    outcome,
    overview,
    pad,
    size_text,
    spans_days,
    summary_lines,
    value_text,
)
from mcp_security.gateway.wire_log import (
    CALL_METHOD,
    ERROR,
    FROM_GATEWAY,
    TO_AGENT,
    TO_SERVER,
    WARN,
)

COLUMNS = (
    "TIME",
    "LEVEL",
    "AGENT_ID",
    "AGENT",
    "USER_ID",
    "SESSION",
    "REQUEST",
    "EVENT",
    "RESULT",
    "DURATION",
    "SIZE",
)
DETAILS = "DETAILS"  # last column: not padded, as long as it needs
#: Column widths; USER_ID fits a whole UUID — ids are looked up, so they are never cut.
CAPS = {"EVENT": 40, "RESULT": 22, "AGENT": 16, "USER_ID": 36, "AGENT_ID": 16}
RIGHT = frozenset({"DURATION", "SIZE"})
EMPTY = "-"
GAP = "  "
LEGEND = "→ request   ← reply   ◆ verdict, before forwarding   ! notice   ▶ ■ gateway start / stop"
COLOR_MODES = ("auto", "always", "never")
ANSI = {WARN: "\033[33m", ERROR: "\033[31m", "dim": "\033[2m", "bold": "\033[1m"}
RESET = "\033[0m"
BODILESS = {"GET": "GET  (stream)", "DELETE": "DELETE  (end session)"}
ACCEPTED, ACK = 202, "notification ack"  # a notification's reply: 202, no body, no method


def render(records: list[dict], title: str, chain: str, color: bool = False) -> str:
    """The whole log as rows, with a header and a summary."""
    with_date = spans_days(records)
    rows = [_row(record, with_date) for record in records]
    widths = {
        column: min(CAPS.get(column, 99), max([len(column), *(len(r[column]) for r in rows)]))
        for column in COLUMNS
    }
    header = _join({c: c for c in COLUMNS} | {DETAILS: DETAILS}, widths)
    lines = [f"Gateway log  {title}", *overview(records, chain), LEGEND, ""]
    lines.append(_paint(header, "bold", color))
    for record, row in zip(records, rows, strict=True):
        text = _join(row, widths)
        lines.append(_paint(text, level_of(record), color))
    exchanges = len({exchange_key(r, n) for n, r in enumerate(records, 1) if not _is_run(r)})
    lines += ["", *summary_lines(records, exchanges)]
    return "\n".join(line.rstrip() for line in lines) + "\n"


def _row(record: dict, with_date: bool) -> dict[str, str]:
    """One record as its column texts."""
    event, result, details = _what(record)
    duration = record.get("gateway.duration_s")
    return {
        "TIME": clock(record, with_date),
        "LEVEL": level_of(record).upper(),
        "AGENT_ID": _short(record.get("gateway.agent_id"), CAPS["AGENT_ID"]),
        "AGENT": _short(record.get("gateway.agent"), CAPS["AGENT"]),
        "USER_ID": _short(record.get("user.id"), CAPS["USER_ID"]),
        "SESSION": str(record.get("mcp.session.id") or "")[:SHORT_ID],  # a prefix, like git's
        "REQUEST": str(record.get("gateway.exchange_id") or "")[:SHORT_ID],
        "EVENT": _short(event, CAPS["EVENT"]),
        "RESULT": _short(result, CAPS["RESULT"]),
        "DURATION": f"{duration:.2f} s" if isinstance(duration, (int, float)) else "",
        "SIZE": size_text(record.get("gateway.message_bytes")),
        DETAILS: " ".join(f"{k}={_quote(v)}" for k, v in details if v not in (None, "")),
    }


def _what(record: dict) -> tuple[str, str, list[tuple[str, object]]]:
    """The event, its result, and the details, for any kind of record."""
    notice, direction = record.get("gateway.notice"), record.get("gateway.direction")
    if notice in RUN_NOTICES:
        return ("▶ " if notice == "gateway_started" else "■ ") + notice, "", _run_details(record)
    if notice:
        return f"! {notice}", str(record.get("gateway.reason") or ""), _notice_details(record)
    if "gateway.decision" in record:
        return f"◆ verdict {record.get('gen_ai.tool.name') or ''}".rstrip(), *_verdict(record)
    if direction == TO_SERVER:
        return f"→ {_target(record)}", "", _request_details(record)
    if direction == TO_AGENT:
        status = record.get("http.response.status_code")
        kept = record.get("message") is not None or not record.get("gateway.message_bytes")
        result = f"{status or ''} {outcome(record)}".replace("JSON-RPC error", "JSON-RPC").strip()
        target = _target(record) if record.get("mcp.method.name") or status != ACCEPTED else ACK
        return f"← {target}", result, [("body", None if kept else "not-kept")]
    if direction == FROM_GATEWAY:
        return "! gateway", "", [("message", (record.get("message") or {}).get("error"))]
    return str(direction or "?"), "", []


def _target(record: dict) -> str:
    method, tool = record.get("mcp.method.name"), record.get("gen_ai.tool.name")
    if method:
        return f"{method} {tool}" if tool else method
    http = str(record.get("http.request.method") or "")
    return BODILESS.get(http, http) if record.get("gateway.direction") == TO_SERVER else http


def _request_details(record: dict) -> list[tuple[str, object]]:
    if record.get("mcp.method.name") == "initialize":
        return [
            ("client", record.get("gateway.client")),
            ("protocol", record.get("mcp.protocol.version")),
        ]
    if record.get("mcp.method.name") != CALL_METHOD:
        return []
    args = call_arguments(record)
    effects = record.get("gateway.effects") or {}
    details: list[tuple[str, object]] = (
        sorted(args.items())
        if args is not None
        else [("keys", ",".join(record.get("gateway.arg_keys") or []))]
    )
    if args is None:  # values not logged: the typed fields are what there is
        for name in ("which", "how_much", "action"):
            details += [(f"{name}.{k}", v) for k, v in (effects.get(name) or {}).items()]
    details += [
        ("when_days", effects.get("when_span_days")),
        ("recipients", effects.get("who_count")),
        ("carried", size_text(effects.get("carried_bytes"))),
        ("tool_listed", "no" if record.get("gateway.tool_listed") is False else None),
        ("header_mismatch", ",".join(record.get("gateway.header_mismatch") or []) or None),
        ("trace", record.get("trace_id")),
    ]
    return details


def _verdict(record: dict) -> tuple[str, list[tuple[str, object]]]:
    d = record["gateway.decision"]
    if "error" in d:
        return "failed", [("error", d["error"])]
    if d.get("risk") is None:
        return "no score", [("reason", d.get("reasons"))]
    match = record.get("gateway.catalog_match")
    level = f"{d['input_level']}({d.get('input_set_by')})" if d.get("input_level") else None
    details = [
        ("cell", f"{d['cell']:.1f}"),
        ("factor", f"{d['factor']:.2f}"),
        ("asset", d.get("asset")),
        ("basis", d.get("basis")),
        ("input", level),
        ("catalog", "scanned" if match is True else "differs" if match is False else None),
    ]
    return f"risk {d['risk']:.1f} {d.get('band') or ''}".strip(), details


def _notice_details(record: dict) -> list[tuple[str, object]]:
    return [
        ("owner", record.get("gateway.session_owner")),
        ("owner_id", record.get("gateway.session_owner_id")),
        ("ended", "yes" if record.get("gateway.session_ended") else None),
        (
            "route",
            record.get("gateway.route") if record["gateway.notice"] == "unknown_route" else None,
        ),
        ("from", record.get("client.address")),
        ("saved", record.get("gateway.catalog_file")),
        (
            "error",
            f"{record.get('error.type')}: {record.get('gateway.error')}"
            if record.get("gateway.error")
            else None,
        ),
    ]


def _run_details(record: dict) -> list[tuple[str, object]]:
    if record["gateway.notice"] != "gateway_started":
        return []
    artifacts = record.get("gateway.artifacts") or {}
    keyed = record.get("gateway.pseudonyms_keyed")
    return [
        ("config", str(record.get("gateway.config_sha256", ""))[:SHORT_ID]),
        *((name, str(digest)[:SHORT_ID]) for name, digest in artifacts.items()),
        ("importance", str(record.get("gateway.effects_sha256") or "")[:SHORT_ID]),
        ("bodies", record.get("gateway.log_bodies")),
        ("pseudonyms", None if keyed is None else ("keyed" if keyed else "unkeyed")),
        ("auth", record.get("gateway.auth")),
    ]


def _is_run(record: dict) -> bool:
    return record.get("gateway.notice") in RUN_NOTICES


def _join(row: dict[str, str], widths: dict[str, int]) -> str:
    cells = []
    for column in COLUMNS:
        text = row[column] or EMPTY
        cells.append(text.rjust(widths[column]) if column in RIGHT else pad(text, widths[column]))
    return GAP.join([*cells, row.get(DETAILS, "")])


def _short(value: object, width: int) -> str:
    if value is None or value == "":
        return ""
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "…"


def _quote(value: object) -> str:
    """A ``key=value`` value: bare when it has no spaces, quotes or ``=``, else JSON-quoted."""
    text = value_text(value)
    return json.dumps(text, ensure_ascii=False) if any(c in text for c in ' "=') else text


def _paint(text: str, style: str, color: bool) -> str:
    return f"{ANSI[style]}{text}{RESET}" if color and style in ANSI else text


def main() -> None:
    """``<log.jsonl> [--grouped] [--color auto|always|never] [--out view.txt]``."""
    parser = argparse.ArgumentParser(description="Render a gateway log for reading.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--grouped", action="store_true", help="by session, one block per exchange")
    parser.add_argument("--color", choices=COLOR_MODES, default="auto")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    broken = verify_chain(args.path)
    chain = f"hash chain BROKEN at {broken[:5]}" if broken else "hash chain intact"
    records = read_log(args.path)
    color = args.color == "always" or (
        args.color == "auto" and not args.out and sys.stdout.isatty()
    )
    if args.grouped:
        view = render_grouped(records, str(args.path), chain)
    else:
        view = render(records, str(args.path), chain, color=color)
    if args.out:
        args.out.write_text(view, encoding="utf-8")
        print(f"{args.path} -> {args.out}")
    else:
        print(view, end="")


if __name__ == "__main__":
    main()
