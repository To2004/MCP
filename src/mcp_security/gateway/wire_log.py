"""What the gateway writes for every message: one JSON line, nothing secret, nothing guessed.

A deployment has no labels and no roles, only the wire. So each line records what the
wire says and nothing else — who connected (the agent's token, as a name, and the user and
app it was issued for; the address; the client's own name), when, in which session and at
which position, what was asked, what came back and how long it took. Field names follow the
OpenTelemetry MCP semantic conventions where one exists (``mcp.*``, ``gen_ai.*``,
``jsonrpc.request.id``, ``rpc.response.status_code``, ``client.address``, ``error.type``);
the gateway's own are ``gateway.*``. A field that does not apply is left out, not null.

What the log compares but must not show — the session id, the call's arguments, its
recipients — is written as a pseudonym (``pseudonym.py``). How much of each message body is
kept is the route's choice (``LogPolicy.bodies``); the fields every dynamic dimension needs
(argument names, argument pseudonym, typed effects from ``effects.py``) are written either way.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from mcp_security.gateway.effects import EffectMap
from mcp_security.gateway.pseudonym import Pseudonymizer

SCHEMA = "gateway-log/3"
TO_SERVER = "agent->server"
TO_AGENT = "server->agent"
FROM_GATEWAY = "gateway"
LIST_METHOD = "tools/list"
CALL_METHOD = "tools/call"
INIT_METHOD = "initialize"
EXECUTE_TOOL = "execute_tool"  # gen_ai.operation.name for a tool call (OpenTelemetry)
TOOL_ERROR = "tool_error"  # the call ran and the tool reported failure (result.isError)
#: JSON-RPC codes OpenTelemetry's MCP conventions class as the caller's mistake, not an error:
#: parse error, invalid request, method not found, invalid params (also: no such tool),
#: resource not found. They are still logged, as ``rpc.response.status_code``.
NOT_ERRORS = frozenset({-32700, -32600, -32601, -32602, -32002})
#: Where protocol 2026-07-28 carries the client and version in every request.
META_PROTOCOL = "io.modelcontextprotocol/protocolVersion"
META_CLIENT = "io.modelcontextprotocol/clientInfo"
#: W3C trace context, propagated in ``params._meta`` (OpenTelemetry MCP conventions).
TRACEPARENT = re.compile(r"^[0-9a-f]{2}-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$")
BODIES = ("all", "requests", "none")
#: Severity of a line (ECS ``log.level``): a notice's, or info. A wire message is info even
#: when the server answered with an error — that is in its status, not the gateway's doing.
INFO, WARN, ERROR = "info", "warn", "error"
NOTICE_LEVELS = {
    "auth_failed": WARN,
    "unknown_route": WARN,
    "session_agent_mismatch": WARN,
    "catalog_not_scanned": WARN,
    "upstream_unreachable": ERROR,
}
#: Sessions whose owner is remembered after they end, so a later takeover is still seen.
MAX_SESSION_OWNERS = 100_000


def catalog_bytes(catalog: dict) -> bytes:
    """A catalog file's exact bytes; stable for the same tools in the same order."""
    return (json.dumps(catalog, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode()


def catalog_digest(catalog: dict) -> str:
    """SHA-256 of the catalog file: changes whenever any tool, schema or description does."""
    return hashlib.sha256(catalog_bytes(catalog)).hexdigest()


@dataclass(frozen=True)
class LogPolicy:
    """How one route's log treats message bodies and the values it hides.

    ``bodies``: ``all`` keeps every message; ``requests`` drops the server's replies;
    ``none`` drops every body. A ``tools/list`` reply is always kept — it is the server's
    public catalog, and ``catalog.py`` reads it from the log.
    """

    bodies: str = "all"
    effects: EffectMap | None = None
    pseudonyms: Pseudonymizer = field(default_factory=Pseudonymizer)

    def __post_init__(self) -> None:
        if self.bodies not in BODIES:
            raise ValueError(f"log bodies must be one of {BODIES}, not {self.bodies!r}")

    def keeps_body(self, direction: str, method: str | None) -> bool:
        if direction == FROM_GATEWAY or (direction == TO_AGENT and method == LIST_METHOD):
            return True
        return self.bodies == "all" or (self.bodies == "requests" and direction == TO_SERVER)

    def session(self, session: str | None) -> str | None:
        return self.pseudonyms.of(session) if session else None


DEFAULT_POLICY = LogPolicy()


@dataclass(frozen=True)
class Exchange:
    """One HTTP request and what every log line it produces shares."""

    route: str
    agent: str | None  # None: a refused request (no or unknown token)
    session: str | None
    http_method: str
    client_address: str | None = None
    client_port: int | None = None
    peer_address: str | None = None  # the proxy in front, when the address came from it
    user_agent: str | None = None
    origin: str | None = None
    protocol_version: str | None = None
    client_info: str | None = None  # "name/version" from initialize or the request's _meta
    user: str | None = None  # whom the agent's token was issued for (config, not the wire)
    app: str | None = None  # which agent application holds the token (config)
    agent_id: str | None = None  # stable id of the token's holder (config, or token hash)
    auth: str | None = None  # how the caller was identified: token, oauth or none
    issuer: str | None = None  # oauth: the identity provider that signed the token
    scopes: tuple[str, ...] = ()  # oauth: what the token allows
    token_id: str | None = None  # oauth: the token's jti
    actors: tuple[str, ...] = ()  # oauth: who acts on the user's behalf, outermost first
    method_header: str | None = None  # Mcp-Method (2026-07-28), to compare with the body
    name_header: str | None = None  # Mcp-Name, decoded
    requests: dict[str, tuple[str | None, str | None]] = field(default_factory=dict)
    received: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

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
    """The client's self-reported ``name/version``: from initialize, or from ``_meta``."""
    for message in messages:
        params = message.get("params") or {}
        info = params.get("clientInfo") if message.get("method") == INIT_METHOD else None
        info = info or (params.get("_meta") or {}).get(META_CLIENT) or {}
        if isinstance(info, dict) and info.get("name"):
            return f"{info['name']}/{info.get('version', '?')}"
    return None


def protocol_of(messages: list[dict]) -> str | None:
    """The protocol version a body states: initialize's, or a request's ``_meta``."""
    for message in messages:
        params = message.get("params") or {}
        version = params.get("protocolVersion") if message.get("method") == INIT_METHOD else None
        version = version or (params.get("_meta") or {}).get(META_PROTOCOL)
        if isinstance(version, str):
            return version
    return None


class SessionBook:
    """Per-session state the wire implies: order, client name, the tools it listed, its owner."""

    def __init__(self) -> None:
        self._seq: dict[str, int] = {}
        self._requests: dict[str, int] = {}
        self._client: dict[str, str] = {}
        self._listed: dict[str, set[str]] = {}
        self._catalog: dict[str, str] = {}
        self._owner: OrderedDict[str, str] = OrderedDict()
        self._ended: set[str] = set()

    def start(self, session: str, client_info: str | None) -> None:
        if client_info:
            self._client[session] = client_info

    def claim(self, session: str, agent: str) -> str | None:
        """Bind the session to the first agent seen on it; return the owner if it is not
        ``agent`` (MCP: bind session ids to the user, so one agent cannot ride another's)."""
        owner = self._owner.get(session)
        if owner is None:
            self._owner[session] = agent
            if len(self._owner) > MAX_SESSION_OWNERS:
                oldest, _ = self._owner.popitem(last=False)
                self._ended.discard(oldest)
            return None
        return owner if owner != agent else None

    def ended(self, session: str | None) -> bool:
        """Did the session's client end it (DELETE)? Its owner is still remembered."""
        return session in self._ended

    def next_seq(self, session: str) -> int:
        self._seq[session] = self._seq.get(session, 0) + 1
        return self._seq[session]

    def next_request(self, session: str) -> int:
        """Position among the agent's own messages in the session (replies not counted)."""
        self._requests[session] = self._requests.get(session, 0) + 1
        return self._requests[session]

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
        for book in (self._seq, self._requests, self._client, self._listed, self._catalog):
            book.pop(session, None)
        if session in self._owner:  # kept: a server may still accept the id (seen on GitHub)
            self._ended.add(session)


def build_record(
    exchange: Exchange,
    book: SessionBook,
    direction: str,
    status: int | None,
    message: dict | None,
    policy: LogPolicy = DEFAULT_POLICY,
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
    sent = direction == TO_SERVER
    asked = _request_fields(exchange, rpc, now, policy) if sent and rpc else {}
    record = {
        "schema": SCHEMA,
        "ts": now,
        "log.level": WARN if asked.get("gateway.header_mismatch") else INFO,
        "gateway.route": exchange.route,
        "gateway.direction": direction,
        "gateway.exchange_id": exchange.id,
        **_who(exchange),
        "gateway.client": book.client(session) or exchange.client_info,
        "gateway.seq": book.next_seq(session) if session else None,
        "gateway.request_seq": book.next_request(session) if sent and session and rpc else None,
        **_wire(exchange),
        "http.response.status_code": status,
        "mcp.session.id": policy.session(session),
        "mcp.protocol.version": exchange.protocol_version,
        "mcp.method.name": method,
        "gen_ai.operation.name": EXECUTE_TOOL if method == CALL_METHOD else None,
        "jsonrpc.request.id": _id_text(rpc.get("id")),
        "gen_ai.tool.name": tool,
        "rpc.response.status_code": None if sent else _rpc_code(rpc),
        "error.type": None if sent else _error_type(rpc),
        "gateway.duration_s": None if sent else round(now - exchange.received, 4),
        "gateway.message_bytes": _bytes(message) if message else 0,
        "gateway.tool_listed": book.listed(session, tool)
        if sent and method == CALL_METHOD
        else None,
        "gateway.catalog_sha256": listed if method == LIST_METHOD else None,
        **asked,
        "message": message if policy.keeps_body(direction, method) else None,
    }
    return {key: value for key, value in record.items() if value is not None}


def decision_record(
    exchange: Exchange,
    book: SessionBook,
    call: dict,
    decision: dict,
    scanned_catalog: str | None,
    ts: float,
    policy: LogPolicy = DEFAULT_POLICY,
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
        "log.level": ERROR if "error" in decision else INFO,
        "gateway.route": exchange.route,
        "gateway.direction": FROM_GATEWAY,
        "gateway.exchange_id": exchange.id,
        **_who(exchange),
        "gateway.seq": book.next_seq(session) if session else None,
        "mcp.session.id": policy.session(session),
        "mcp.method.name": CALL_METHOD,
        "gen_ai.operation.name": EXECUTE_TOOL,
        "jsonrpc.request.id": _id_text(call.get("id")),
        "gen_ai.tool.name": _tool_of(call),
        "gateway.catalog_match": shown == scanned_catalog if shown and scanned_catalog else None,
        "gateway.decision": decision,
    }
    return {key: value for key, value in record.items() if value is not None}


def notice_record(
    exchange: Exchange, notice: str, policy: LogPolicy = DEFAULT_POLICY, **fields: object
) -> dict:
    """Something the gateway noticed about one request, not a message on the wire."""
    record = {
        "schema": SCHEMA,
        "ts": time.time(),
        "log.level": NOTICE_LEVELS.get(notice, INFO),
        "gateway.route": exchange.route,
        "gateway.direction": FROM_GATEWAY,
        "gateway.exchange_id": exchange.id,
        **_who(exchange),
        **_wire(exchange),
        "mcp.session.id": policy.session(exchange.session),
        "gateway.notice": notice,
        **fields,
    }
    return {key: value for key, value in record.items() if value is not None}


def gateway_record(route: str, notice: str, **fields: object) -> dict:
    """Something about the gateway itself on one route: it started, it stopped."""
    record = {
        "schema": SCHEMA,
        "ts": time.time(),
        "log.level": INFO,
        "gateway.route": route,
        "gateway.direction": FROM_GATEWAY,
        "gateway.notice": notice,
        **fields,
    }
    return {key: value for key, value in record.items() if value is not None}


def _who(exchange: Exchange) -> dict:
    return {
        "gateway.agent_id": exchange.agent_id,
        "gateway.agent": exchange.agent,
        "user.id": exchange.user,
        "gateway.app": exchange.app,
        "gateway.auth": exchange.auth,
        "gateway.issuer": exchange.issuer,
        "gateway.scopes": list(exchange.scopes) or None,
        "gateway.token_id": exchange.token_id,
        "gateway.act": list(exchange.actors) or None,
    }


def _wire(exchange: Exchange) -> dict:
    return {
        "client.address": exchange.client_address,
        "client.port": exchange.client_port,
        "network.peer.address": exchange.peer_address,
        "user_agent.original": exchange.user_agent,
        "http.request.header.origin": [exchange.origin] if exchange.origin else None,
        "http.request.method": exchange.http_method,
    }


def _request_fields(exchange: Exchange, rpc: dict, ts: float, policy: LogPolicy) -> dict:
    """What a request carries beyond its method: trace context, header mismatches, and —
    for a tool call — its argument names, their pseudonym and the typed effects."""
    raw_params = rpc.get("params")
    params: dict = raw_params if isinstance(raw_params, dict) else {}
    meta = params.get("_meta")
    trace = TRACEPARENT.match(str(meta.get("traceparent", ""))) if isinstance(meta, dict) else None
    fields: dict = {
        "trace_id": trace.group(1) if trace else None,
        "span_id": trace.group(2) if trace else None,
        "gateway.header_mismatch": _header_mismatch(exchange, rpc, params) or None,
    }
    args = params.get("arguments")
    if rpc.get("method") == CALL_METHOD and isinstance(args, dict):
        canonical = json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)
        fields["gateway.arg_keys"] = sorted(args)
        fields["gateway.args_hash"] = policy.pseudonyms.of(canonical)
        if policy.effects:
            effects = policy.effects.extract(params.get("name"), args, ts, policy.pseudonyms)
            fields["gateway.effects"] = effects or None
    return fields


def _header_mismatch(exchange: Exchange, rpc: dict, params: dict) -> list[str]:
    """Headers that name a different method or tool than the body (2026-07-28 requires a
    server to reject these: a router reading the header and a server reading the body would
    act on different calls)."""
    mismatched = []
    if exchange.method_header is not None and exchange.method_header != rpc.get("method"):
        mismatched.append("Mcp-Method")
    if exchange.name_header is not None:
        named = params.get("name") if "name" in params else params.get("uri")
        if exchange.name_header != named:
            mismatched.append("Mcp-Name")
    return mismatched


def _id_key(rpc_id: object) -> str:
    return json.dumps(rpc_id)


def _id_text(rpc_id: object) -> str | None:
    """OpenTelemetry records the request id as a string, and not at all when it is null."""
    if rpc_id is None:
        return None
    return rpc_id if isinstance(rpc_id, str) else json.dumps(rpc_id)


def _bytes(message: dict) -> int:
    return len(json.dumps(message, ensure_ascii=False).encode())


def _tool_of(message: dict) -> str | None:
    if message.get("method") != CALL_METHOD:
        return None
    return (message.get("params") or {}).get("name")


def _rpc_code(message: dict) -> str | None:
    error = message.get("error")
    return str(error.get("code")) if isinstance(error, dict) else None


def _error_type(message: dict) -> str | None:
    error = message.get("error")
    if isinstance(error, dict):
        return None if error.get("code") in NOT_ERRORS else str(error.get("code"))
    if isinstance(message.get("result"), dict) and message["result"].get("isError"):
        return TOOL_ERROR
    return None
