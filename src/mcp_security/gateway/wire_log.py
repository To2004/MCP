"""What the gateway writes for every message: one JSON line, nothing secret, nothing guessed.

A deployment has no labels and no roles, only the wire. So each line records what the
wire says and nothing else — who connected (the agent's token, as a name; the address;
the client's own name from ``initialize``), when, in which session and at which position,
what was asked, what came back and how long it took. Field names follow the OpenTelemetry
MCP semantic conventions where one exists (``mcp.*``, ``gen_ai.tool.name``,
``jsonrpc.request.id``, ``client.address``, ``error.type``); the gateway's own are
``gateway.*``. A field that does not apply is left out, not written as null.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "gateway-log/2"
TO_SERVER = "agent->server"
TO_AGENT = "server->agent"
FROM_GATEWAY = "gateway"
LIST_METHOD = "tools/list"
CALL_METHOD = "tools/call"
INIT_METHOD = "initialize"
TOOL_ERROR = "tool_error"  # the call ran and the tool reported failure (result.isError)


def catalog_bytes(catalog: dict) -> bytes:
    """A catalog file's exact bytes; stable for the same tools in the same order."""
    return (json.dumps(catalog, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode()


def catalog_digest(catalog: dict) -> str:
    """SHA-256 of the catalog file: changes whenever any tool, schema or description does."""
    return hashlib.sha256(catalog_bytes(catalog)).hexdigest()


@dataclass(frozen=True)
class Exchange:
    """One HTTP request and what every log line it produces shares."""

    route: str
    agent: str
    session: str | None
    http_method: str
    client_address: str | None = None
    client_port: int | None = None
    user_agent: str | None = None
    protocol_version: str | None = None
    client_info: str | None = None  # "name/version" from an initialize in this request
    requests: dict[str, tuple[str | None, str | None]] = field(default_factory=dict)
    received: float = field(default_factory=time.time)

    def answering(self, message: dict) -> tuple[str | None, str | None]:
        """The method and tool of the request this reply answers."""
        return self.requests.get(_id_key(message.get("id")), (None, None))


def requests_in(messages: list[dict]) -> dict[str, tuple[str | None, str | None]]:
    """Request id -> (method, tool) for the requests in one body, to label their replies."""
    return {
        _id_key(m["id"]): (m.get("method"), _tool_of(m))
        for m in messages
        if "id" in m and "method" in m
    }


def client_info_of(messages: list[dict]) -> str | None:
    """The client's self-reported ``name/version``, from an initialize request."""
    for message in messages:
        if message.get("method") == INIT_METHOD:
            info = (message.get("params") or {}).get("clientInfo") or {}
            if info.get("name"):
                return f"{info['name']}/{info.get('version', '?')}"
    return None


class SessionBook:
    """Per-session state the wire implies: message order, client name, the tools it listed."""

    def __init__(self) -> None:
        self._seq: dict[str, int] = {}
        self._client: dict[str, str] = {}
        self._listed: dict[str, set[str]] = {}
        self._catalog: dict[str, str] = {}

    def start(self, session: str, client_info: str | None) -> None:
        if client_info:
            self._client[session] = client_info

    def next_seq(self, session: str) -> int:
        self._seq[session] = self._seq.get(session, 0) + 1
        return self._seq[session]

    def client(self, session: str | None) -> str | None:
        return self._client.get(session) if session else None

    def saw_tools(self, session: str, tools: list[dict], digest: str) -> None:
        self._listed.setdefault(session, set()).update(t.get("name") for t in tools)
        self._catalog[session] = digest

    def catalog(self, session: str | None) -> str | None:
        """Digest of the tool list this session was shown, if it asked for one."""
        return self._catalog.get(session) if session else None

    def listed(self, session: str | None, tool: str | None) -> bool | None:
        """Was ``tool`` in this session's tools/list? None: the session never listed."""
        if session not in self._listed:
            return None
        return tool in self._listed[session]

    def end(self, session: str | None) -> None:
        for book in (self._seq, self._client, self._listed, self._catalog):
            book.pop(session, None)


def build_record(
    exchange: Exchange, book: SessionBook, direction: str, status: int | None, message: dict | None
) -> dict:
    """One log line for one JSON-RPC message (``None`` for a bodiless request)."""
    now = time.time()
    rpc = message or {}
    session = exchange.session
    method, tool = (rpc.get("method"), _tool_of(rpc))
    if direction == TO_AGENT and method is None:
        method, tool = exchange.answering(rpc)
    result = rpc.get("result") if isinstance(rpc.get("result"), dict) else {}
    listed = catalog_digest({"tools": result["tools"]}) if "tools" in result else None
    if direction == TO_AGENT and method == LIST_METHOD and session and listed:
        book.saw_tools(session, result["tools"], listed)
    record = {
        "schema": SCHEMA,
        "ts": now,
        "gateway.route": exchange.route,
        "gateway.direction": direction,
        "gateway.agent": exchange.agent,
        "gateway.client": book.client(session) or exchange.client_info,
        "gateway.seq": book.next_seq(session) if session else None,
        "client.address": exchange.client_address,
        "client.port": exchange.client_port,
        "user_agent.original": exchange.user_agent,
        "http.request.method": exchange.http_method,
        "http.response.status_code": status,
        "mcp.session.id": session,
        "mcp.protocol.version": exchange.protocol_version,
        "mcp.method.name": method,
        "jsonrpc.request.id": rpc.get("id"),
        "gen_ai.tool.name": tool,
        "error.type": _error_type(rpc) if direction != TO_SERVER else None,
        "gateway.duration_s": round(now - exchange.received, 4) if direction != TO_SERVER else None,
        "gateway.message_bytes": len(json.dumps(message, ensure_ascii=False)) if message else 0,
        "gateway.tool_listed": book.listed(session, tool)
        if direction == TO_SERVER and method == CALL_METHOD
        else None,
        "gateway.catalog_sha256": listed if method == LIST_METHOD else None,
        "message": message,
    }
    return {key: value for key, value in record.items() if value is not None}


def decision_record(
    exchange: Exchange,
    book: SessionBook,
    call: dict,
    decision: dict,
    scanned_catalog: str | None,
    ts: float,
) -> dict:
    """The framework's verdict on one ``tools/call``, written before the call is forwarded.

    ``gateway.catalog_match`` says whether the tool list this session was shown is the one
    the route's scan was run on (None: the session never listed tools, or the scan did not
    record its catalog), so a score can be trusted only as far as that holds.
    """
    session = exchange.session
    shown = book.catalog(session)
    record = {
        "schema": SCHEMA,
        "ts": ts,
        "gateway.route": exchange.route,
        "gateway.direction": FROM_GATEWAY,
        "gateway.agent": exchange.agent,
        "gateway.seq": book.next_seq(session) if session else None,
        "mcp.session.id": session,
        "mcp.method.name": CALL_METHOD,
        "jsonrpc.request.id": call.get("id"),
        "gen_ai.tool.name": _tool_of(call),
        "gateway.catalog_match": shown == scanned_catalog if shown and scanned_catalog else None,
        "gateway.decision": decision,
    }
    return {key: value for key, value in record.items() if value is not None}


def notice_record(exchange: Exchange, notice: str, **fields: object) -> dict:
    """Something the gateway noticed about the route, not a message on the wire."""
    return {
        "schema": SCHEMA,
        "ts": time.time(),
        "gateway.route": exchange.route,
        "gateway.direction": FROM_GATEWAY,
        "gateway.agent": exchange.agent,
        "mcp.session.id": exchange.session,
        "gateway.notice": notice,
        **fields,
    }


class MessageLog:
    """Append-only JSONL, one file per route. A write failure is reported, never raised:
    the log must not be able to break the agent's session."""

    def __init__(self, log_dir: Path) -> None:
        self._dir = log_dir

    def write(self, route: str, record: dict) -> None:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            with (self._dir / f"{route}.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            print(f"gateway: log write failed for {route}: {exc}", file=sys.stderr)


#: v1 lines (before ``schema``) used these keys; readers rename them so old logs still score.
V1_KEYS = {
    "route": "gateway.route",
    "agent": "gateway.agent",
    "session": "mcp.session.id",
    "direction": "gateway.direction",
    "http": "http.request.method",
    "status": "http.response.status_code",
}


def read_log(path: Path) -> list[dict]:
    """Every record in a gateway log, in write order, with v1 keys renamed to v2."""
    with path.open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    return [
        record if "schema" in record else {V1_KEYS.get(k, k): v for k, v in record.items()}
        for record in records
    ]


def _id_key(rpc_id: object) -> str:
    return json.dumps(rpc_id)


def _tool_of(message: dict) -> str | None:
    if message.get("method") != CALL_METHOD:
        return None
    return (message.get("params") or {}).get("name")


def _error_type(message: dict) -> str | None:
    if isinstance(message.get("error"), dict):
        return str(message["error"].get("code"))
    if isinstance(message.get("result"), dict) and message["result"].get("isError"):
        return TOOL_ERROR
    return None
