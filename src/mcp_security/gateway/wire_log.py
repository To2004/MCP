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

v5 (spec 2.1, 2.9) adds, only on a route whose ``LogPolicy.v5`` is on, so a v1-v4 route's lines
never change: how strongly the caller was identified (B3), the protocol era and its conformance
issues (E3, E7, from ``protocol_era.py``), era-free argument and reply sizes, the logical call
and the server's outcome (ARG-1), the raw reply bytes (RPL-1), and a verdict line for a body
that cannot be read (GW-1). :class:`BoundedSessionBook` is v5's session book (E9, DEP-5).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from mcp_security.gateway.effects import EffectMap
from mcp_security.gateway.http_wire import UnparsedVerdict
from mcp_security.gateway.protocol_era import (
    META_CLIENT,
    META_PROTOCOL,
    SCORED_METHODS,
    LogicalCalls,
    argument_bytes,
    call_outcome,
    classify_request,
    reply_payload_bytes,
    request_issues,
)
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
#: Where protocol 2026-07-28 carries the client and version in every request: META_PROTOCOL
#: and META_CLIENT, from ``protocol_era.py``.
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
    "unparsed": WARN,  # GW-1
}
#: Sessions whose owner is remembered after they end, so a later takeover is still seen.
MAX_SESSION_OWNERS = 100_000
#: LOG-1 (v5, spec 4.2): the fields lines carry once v5's gateway writes them (Batch 1 on).
BASELINE_KEY_FIELD = "gateway.baseline_key"  # B1: whose history the call extends
ZONE_FIELD = "gateway.zone"  # B9d: the caller's zone
PROTOCOL_ERA_FIELD = "gateway.protocol_era"  # E3: legacy or modern
PROTOCOL_ISSUES_FIELD = "gateway.protocol_issues"  # E7: conformance issues, logged not scored
REPLY_WIRE_BYTES_FIELD = "gateway.reply_wire_bytes"  # RPL-1: raw reply bytes on the wire
LOGICAL_CALL_FIELD = "gateway.logical_call"  # ARG-1: continuations fold into one call
#: ARG-1: accepted or rejected by the server; "continued" on an MRTR input_required answer
OUTCOME_FIELD = "gateway.outcome"
LOG1_FIELDS = (
    BASELINE_KEY_FIELD,
    ZONE_FIELD,
    PROTOCOL_ERA_FIELD,
    PROTOCOL_ISSUES_FIELD,
    REPLY_WIRE_BYTES_FIELD,
    LOGICAL_CALL_FIELD,
    OUTCOME_FIELD,
)
#: LOG-1 lines (``gateway.notice``): the route clock folded the day's references (CAL-7),
#: the route switched to a re-learned policy (DEP-4), many callers set records at once (CAL-6).
BEHAVIOUR_FOLD, POLICY_SWITCHED, FLAG_SURGE = "behaviour_fold", "policy_switched", "flag_surge"
LOG1_NOTICES = (BEHAVIOUR_FOLD, POLICY_SWITCHED, FLAG_SURGE)
#: B3 (v5, spec 4.2): how strongly the caller was identified, beside the LOG-1 fields.
IDENTITY_STRENGTH_FIELD = "gateway.identity_strength"
#: B3 values (revised 2026-10-27, spec 2.9 D5: history per agent), by the key a call's history
#: is kept under: a person's, on a route that opts into ``baseline_key = "user"``; the signed-in
#: agent's (D5's default); or the reported client name and address of a caller that did not
#: sign in (self-reported).
IDENTITY_USER, IDENTITY_SERVICE, IDENTITY_NONE = "user", "service", "none"
#: How an unauthenticated exchange says so (``config.NO_AUTH``; config imports this module).
NO_AUTH = "none"
#: ARG-1 (v5): the era-free sizes the engine reads, on request and reply lines, so an offline
#: re-score of the log gets the same inputs as the live gateway.
ARG_BYTES_FIELD = "gateway.arg_bytes"  # bytes of params.arguments
REPLY_BYTES_FIELD = "gateway.reply_bytes"  # bytes of result.content
V5_CALL_FIELDS = (ARG_BYTES_FIELD, REPLY_BYTES_FIELD)
#: GW-1 (v5): the notice for a request body the gateway cannot read, and its fields.
UNPARSED = "unparsed"
UNPARSED_REASON_FIELD = "gateway.unparsed_reason"
REFUSED_FIELD = "gateway.refused"
#: DEP-5: a session idle this long is forgotten, every map of it at once.
SESSION_TTL_S = 3_600.0
#: DEP-5: sessions kept per caller; a caller's junk ids evict its own sessions, never another's
#: (the engine's legacy quota, E8, is the same 64).
MAX_SESSIONS_PER_CALLER = 64
#: E9: an owner is bound only when the server answered a request on the session with a success
#: status (2xx), so it took the id. A junk or ended id (2025-11-25 transports: 404 for an ended
#: session, 400 for a missing one), a refusal (401, 403, 429), a failure (5xx) or no answer
#: binds nobody. (Part A's rule, any status but 400 and 404, also bound on those.)
SESSION_TAKEN_STATUSES = range(200, 300)
#: Whose quota a session counts against before any caller presented it.
UNATTRIBUTED = ""
SESSION_BOOK_FORMAT = "session-book/1"


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

    ``v5``: write v5's fields (B3, LOG-1, ARG-1). Off, a line is exactly what v1-v4 wrote,
    whatever the exchange carries.
    """

    bodies: str = "all"
    effects: EffectMap | None = None
    pseudonyms: Pseudonymizer = field(default_factory=Pseudonymizer)
    v5: bool = False

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
class CallFacts:
    """v5 (ARG-1): what the gateway learns about one call in an exchange. A body can carry
    several JSON-RPC requests, so these are kept per request id (``Exchange.calls``)."""

    arg_bytes: int | None = None  # bytes of params.arguments (era-free)
    reply_bytes: int | None = None  # bytes of result.content (era-free)
    logical_call: str | None = None  # the logical call this request continues
    #: "accepted" or "rejected" by the server, or "continued" (an MRTR input_required answer)
    outcome: str | None = None


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
    # ── v5 (E3, E7, RPL-1, ARG-1; set from Batch 1 on, never written while empty) ──
    era: str | None = None  # E3: "legacy" or "modern", for the whole request
    protocol_issues: tuple[str, ...] = ()  # E7: conformance issues, logged and never scored
    reply_wire_bytes: int | None = None  # RPL-1: raw bytes of the HTTP reply
    calls: dict[str, CallFacts] = field(default_factory=dict)  # ARG-1: request id -> facts
    baseline_key: str | None = None  # B1: whose history the call extends (LOG-1)
    zone: str | None = None  # B9d: the caller's IANA zone (LOG-1)

    def answering(self, message: dict) -> tuple[str | None, str | None]:
        """The method and tool of the request this reply answers."""
        return self.requests.get(_id_key(message.get("id")), (None, None))

    def call_facts(self, message: dict) -> CallFacts:
        """ARG-1: the facts kept for the request with ``message``'s id (a request or the
        reply answering it); empty facts when none were kept."""
        return self.calls.get(_id_key(message.get("id")), CallFacts())


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


def with_v5_facts(
    exchange: Exchange, headers: Mapping[str, str], messages: list[dict], calls: LogicalCalls
) -> Exchange:
    """The exchange with v5's wire facts (E3, E7, ARG-1): the request's era and conformance
    issues, and for each scored request (tools/call, resources/read, prompts/get) its argument
    bytes and logical call (``calls`` is the route's :class:`LogicalCalls`; a new call's key is
    the exchange id and request id). ``headers`` are the request's HTTP headers."""
    caller = exchange.baseline_key or exchange.agent_id or exchange.agent or UNATTRIBUTED
    facts = {}
    for message in messages:
        if message.get("method") in SCORED_METHODS and "id" in message:
            request_id = _id_key(message["id"])
            fresh = f"{exchange.id}/{request_id}"
            key = calls.key_for(caller, message, exchange.received, fresh)
            facts[request_id] = CallFacts(arg_bytes=argument_bytes(message), logical_call=key)
    view = classify_request(exchange.http_method, headers, messages)
    issues = request_issues(exchange.http_method, headers, messages)
    return replace(exchange, era=view.era, protocol_issues=issues, calls=facts)


def reply_facts(exchange: Exchange, status: int | None, message: dict | None) -> CallFacts | None:
    """ARG-1: the facts of the scored call a reply answers - its argument bytes and logical
    call (from :func:`with_v5_facts`), the reply's payload bytes and the server's outcome
    (``protocol_era.call_outcome``). None for anything but a reply to a scored request; a
    bodiless reply's outcome is ``call_outcome(status, None)`` for every call of the exchange."""
    if not isinstance(message, dict) or "method" in message:
        return None
    request = exchange.calls.get(_id_key(message.get("id")))
    if request is None:
        return None
    method, _ = exchange.answering(message)
    return replace(
        request,
        reply_bytes=reply_payload_bytes(method, message),
        outcome=call_outcome(status, message),
    )


def identity_strength(exchange: Exchange) -> str:
    """B3 (revised 2026-10-27, spec 2.9 D5): how strongly the key a call's history is kept
    under was established.

    - ``none``: the caller did not sign in (or was refused), so its key is what it reports about
      itself, its client name and address (``oauth.reported_key``);
    - ``user``: it signed in and the route keys history per person (the opt-in
      ``baseline_key = "user"``): the exchange's baseline key is not its agent key;
    - ``service``: it signed in and its history is the signed-in agent's (``Identity.id``, D5's
      default), also while the exchange carries no baseline key.

    The token's shape is not guessed: ``sub == client_id`` marks client credentials at Okta
    but not at Auth0 (``<client_id>@clients``), Entra (the service principal's id) or Keycloak
    (a service-account user), and D5's deployments have no user ids anyway."""
    if exchange.agent is None or exchange.auth in (None, NO_AUTH):
        return IDENTITY_NONE
    agent_keys = (exchange.agent_id, exchange.agent)
    if exchange.baseline_key is not None and exchange.baseline_key not in agent_keys:
        return IDENTITY_USER
    return IDENTITY_SERVICE


class SessionBook:
    """Per-session state the wire implies: order, client name, the tools it listed, its owner.

    v1-v4's book: one for every route, an owner bound to whoever presents an id first, at most
    :data:`MAX_SESSION_OWNERS` owners and no limit on the other maps. v5 uses
    :class:`BoundedSessionBook`."""

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


@dataclass(slots=True)
class _Session:
    """Everything the bounded book keeps about one session, so it is evicted at once."""

    caller: str  # whose quota it counts against: its owner, else who presented it first
    last_seen: float
    owner: str | None = None
    seq: int = 0
    requests: int = 0
    client: str | None = None
    listed: set[str] | None = None
    catalog: str | None = None
    ended: bool = False


class BoundedSessionBook:
    """v5's session book for one route (E9, DEP-5), with :class:`SessionBook`'s interface.

    - **Owner bound on accept (E9).** :meth:`claim` only reports another caller's ownership;
      :meth:`accept` binds the owner once the server answered the id with a status in
      :data:`SESSION_TAKEN_STATUSES` (or minted it), so a junk or ended id is never claimed.
      The caller is the route's history key (on a v5 route the B1 baseline key, so callers
      without sign-in, keyed by their reported name and address, each get a quota).
    - **Bounded (DEP-5).** One record per session holds every map; it is dropped whole when it
      has been idle for ``ttl_s``, when its caller holds more than ``max_per_caller`` sessions
      (that caller's least recently seen first), or when the route holds more than
      ``max_sessions`` (the least recently seen first). The owner goes with the record, so a
      takeover after ``ttl_s`` of idleness is not seen (v4's book keeps up to
      :data:`MAX_SESSION_OWNERS` owners with no idle time).
    - **Persisted.** :meth:`snapshot` and :meth:`restore` keep the live records' owners, client
      names and ended marks. ``key`` (e.g. the route's pseudonym function) is applied to every
      session id first, so neither memory nor a snapshot holds the raw ids.

    ``clock`` gives the time (default ``time.time``, looked up per call).
    """

    def __init__(
        self,
        ttl_s: float = SESSION_TTL_S,
        max_per_caller: int = MAX_SESSIONS_PER_CALLER,
        max_sessions: int = MAX_SESSION_OWNERS,
        key: Callable[[str], str] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if ttl_s <= 0 or max_per_caller < 1 or max_sessions < 1:
            raise ValueError("ttl_s must be > 0, and max_per_caller and max_sessions >= 1")
        self.ttl_s = ttl_s
        self.max_per_caller = max_per_caller
        self.max_sessions = max_sessions
        self._key = key
        self._clock = clock
        self._sessions: OrderedDict[str, _Session] = OrderedDict()  # least recently seen first
        self._by_caller: dict[str, OrderedDict[str, None]] = {}

    @property
    def sessions(self) -> int:
        """Sessions held. Not ``__len__``: an empty book must not be falsy."""
        return len(self._sessions)

    @property
    def callers(self) -> int:
        """Callers holding at least one session."""
        return len(self._by_caller)

    def start(self, session: str, client_info: str | None) -> None:
        """The client named at ``initialize`` (``name/version``), kept for the session."""
        if client_info:
            self._touch(session).client = client_info

    def claim(self, session: str, agent: str) -> str | None:
        """The session's owner if it is not ``agent`` (checked before forwarding). Nothing is
        bound here: :meth:`accept` does that once the server answered."""
        record = self._touch(session, agent)
        return record.owner if record.owner not in (None, agent) else None

    def accept(self, session: str, agent: str, status: int | None) -> bool:
        """The server answered ``agent``'s request on ``session`` with ``status`` (None: no
        answer): bind ``agent`` as the owner if the server took the id (a 2xx) and nobody owns
        it yet. True when ``agent`` owns the session after this answer."""
        record = self._touch(session, agent)
        taken = status is not None and status in SESSION_TAKEN_STATUSES
        if taken and record.owner is None:
            record.owner = agent
            self._attribute(self._id(session), record, agent)
        return record.owner == agent

    def ended(self, session: str | None) -> bool:
        """Did the session's client end it (DELETE)? Its owner is still remembered."""
        record = self._get(session)
        return record is not None and record.ended

    def next_seq(self, session: str) -> int:
        """Position of the next line in the session (every message counted)."""
        record = self._touch(session)
        record.seq += 1
        return record.seq

    def next_request(self, session: str) -> int:
        """Position among the agent's own messages in the session (replies not counted)."""
        record = self._touch(session)
        record.requests += 1
        return record.requests

    def client(self, session: str | None) -> str | None:
        """The client the session named at ``initialize``, if it is still kept."""
        record = self._get(session)
        return record.client if record else None

    def saw_tools(self, session: str, tools: list[dict], digest: str) -> None:
        """The session was shown ``tools`` (a tools/list reply whose catalog has ``digest``)."""
        record = self._touch(session)
        record.listed = (record.listed or set()) | {t.get("name") for t in tools}
        record.catalog = digest

    def catalog(self, session: str | None) -> str | None:
        """Digest of the tool list this session was shown, if it asked for one."""
        record = self._get(session)
        return record.catalog if record else None

    def listed(self, session: str | None, tool: str | None) -> bool | None:
        """Was ``tool`` in this session's tools/list? None: the session never listed."""
        record = self._get(session)
        if record is None or record.listed is None:
            return None
        return tool in record.listed

    def end(self, session: str | None) -> None:
        """The client ended the session: forget its order, client and tools; an owned
        session keeps its owner (a server may still accept the id), an unowned one goes."""
        if not session or self._get(session) is None:
            return
        record = self._touch(session)
        if record.owner is None:
            self._remove(self._id(session))
            return
        record.seq = record.requests = 0
        record.client = record.listed = record.catalog = None
        record.ended = True

    def snapshot(self) -> dict:
        """The live records' owners, client names and ended marks, least recently seen first
        (E9: saved in the route's state file)."""
        self._expire(self._now())
        rows = [
            [key, r.caller, r.owner, r.last_seen, r.client, r.ended]
            for key, r in self._sessions.items()
        ]
        return {"format": SESSION_BOOK_FORMAT, "sessions": rows}

    def restore(self, data: dict) -> None:
        """Replace the book with a :meth:`snapshot`, dropping records idle past the TTL.

        ``ValueError``, with the book left as it was, for anything but a snapshot of this
        format: a malformed row, a session listed twice, an owner other than the row's caller,
        or a time that is not a finite number. A time ahead of the clock counts as now, so the
        book stays in least-recently-seen order."""
        if not isinstance(data, dict) or data.get("format") != SESSION_BOOK_FORMAT:
            raise ValueError(f"not a {SESSION_BOOK_FORMAT} snapshot")
        rows = data.get("sessions")
        if not isinstance(rows, list) or not all(_is_session_row(row) for row in rows):
            raise ValueError(f"malformed {SESSION_BOOK_FORMAT} sessions")
        keys = [row[0] for row in rows]
        if len(set(keys)) != len(keys):
            raise ValueError(f"{SESSION_BOOK_FORMAT}: a session is listed twice")
        now = self._now()
        live = sorted((row for row in rows if now - row[3] <= self.ttl_s), key=lambda r: r[3])
        self._sessions.clear()
        self._by_caller.clear()
        for key, caller, owner, last_seen, client, ended in live:
            seen = min(last_seen, now)
            self._insert(key, _Session(caller, seen, owner=owner, client=client, ended=ended))

    def _now(self) -> float:
        return self._clock() if self._clock else time.time()

    def _id(self, session: str) -> str:
        return self._key(session) if self._key else session

    def _get(self, session: str | None) -> _Session | None:
        if not session:
            return None
        self._expire(self._now())
        return self._sessions.get(self._id(session))

    def _touch(self, session: str, caller: str | None = None) -> _Session:
        """The session's record, seen now: created for ``caller`` if new; an unattributed one
        is attributed to ``caller``."""
        now = self._now()
        self._expire(now)
        key = self._id(session)
        record = self._sessions.get(key)
        if record is None:
            record = _Session(UNATTRIBUTED if caller is None else caller, now)
            self._insert(key, record)
            return record
        record.last_seen = now
        self._sessions.move_to_end(key)
        self._by_caller[record.caller].move_to_end(key)
        if caller is not None and record.owner is None and record.caller == UNATTRIBUTED:
            self._attribute(key, record, caller)
        return record

    def _insert(self, key: str, record: _Session) -> None:
        self._sessions[key] = record
        self._by_caller.setdefault(record.caller, OrderedDict())[key] = None
        self._evict(record.caller)

    def _attribute(self, key: str, record: _Session, caller: str) -> None:
        if record.caller == caller:
            return
        self._unlink(key, record.caller)
        record.caller = caller
        self._by_caller.setdefault(caller, OrderedDict())[key] = None
        self._evict(caller)

    def _evict(self, caller: str) -> None:
        """Past a quota: the caller's least recently seen session, then the route's."""
        own = self._by_caller[caller]
        while len(own) > self.max_per_caller:
            self._remove(next(iter(own)))
        while len(self._sessions) > self.max_sessions:
            self._remove(next(iter(self._sessions)))

    def _expire(self, now: float) -> None:
        while self._sessions:
            key, record = next(iter(self._sessions.items()))
            if now - record.last_seen <= self.ttl_s:
                return
            self._remove(key)

    def _remove(self, key: str) -> None:
        record = self._sessions.pop(key)
        self._unlink(key, record.caller)

    def _unlink(self, key: str, caller: str) -> None:
        own = self._by_caller[caller]
        del own[key]
        if not own:
            del self._by_caller[caller]


#: A snapshot row: [key, caller, owner or None, last_seen, client or None, ended].
_SESSION_ROW_TYPES = (str, str, (str, type(None)), (int, float), (str, type(None)), bool)


def _is_session_row(row: object) -> bool:
    """A row :meth:`BoundedSessionBook.snapshot` can write: the types above, a finite time (a
    bool is no time), and an owner that is the caller the session counts against (binding an
    owner attributes the session to it)."""
    if not isinstance(row, list) or len(row) != len(_SESSION_ROW_TYPES):
        return False
    if not all(isinstance(value, kinds) for value, kinds in zip(row, _SESSION_ROW_TYPES)):
        return False
    _, caller, owner, last_seen, _, _ = row
    finite = not isinstance(last_seen, bool) and math.isfinite(last_seen)
    return finite and owner in (None, caller)


#: Either session book: v1-v4's or v5's.
AnySessionBook = SessionBook | BoundedSessionBook


def build_record(
    exchange: Exchange,
    book: AnySessionBook,
    direction: str,
    status: int | None,
    message: dict | None,
    policy: LogPolicy = DEFAULT_POLICY,
) -> dict:
    """One log line for one JSON-RPC message (``None`` for a bodiless request). With
    ``policy.v5`` it also carries v5's fields (:func:`_v5_line_fields`), and a request with
    conformance issues is a WARN line."""
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
    v5 = _v5_line_fields(exchange, direction, status, message) if policy.v5 else {}
    warn = asked.get("gateway.header_mismatch") or v5.get(PROTOCOL_ISSUES_FIELD)
    record = {
        "schema": SCHEMA,
        "ts": now,
        "log.level": WARN if warn else INFO,
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
        **v5,
        "message": message if policy.keeps_body(direction, method) else None,
    }
    return {key: value for key, value in record.items() if value is not None}


def decision_record(
    exchange: Exchange,
    book: AnySessionBook,
    call: dict,
    decision: dict,
    scanned_catalog: str | None,
    ts: float,
    policy: LogPolicy = DEFAULT_POLICY,
) -> dict:
    """The framework's verdict on one ``tools/call``, written before the call is forwarded.

    ``gateway.catalog_match`` says whether the tool list this session was shown is the one
    the route's scan was run on (None: the session never listed tools, or the scan did not
    record its catalog), so a score can be trusted only as far as that holds. With
    ``policy.v5`` it also carries the caller's identity strength, the era, and the call's
    logical call and argument bytes.
    """
    session = exchange.session
    shown = book.catalog(session)
    facts = exchange.call_facts(call)
    v5 = _v5_who(exchange) if policy.v5 else {}
    if policy.v5:
        v5 |= {LOGICAL_CALL_FIELD: facts.logical_call, ARG_BYTES_FIELD: facts.arg_bytes}
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
        **v5,
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
        **(_v5_who(exchange) if policy.v5 else {}),
        "gateway.notice": notice,
        **fields,
    }
    return {key: value for key, value in record.items() if value is not None}


def unparsed_record(
    exchange: Exchange, verdict: UnparsedVerdict, policy: LogPolicy = DEFAULT_POLICY
) -> dict:
    """GW-1: the verdict on a request body the gateway cannot read (``http_wire``'s
    ``unparsed_verdict``), as a WARN notice: why, and whether the body was refused."""
    fields = {UNPARSED_REASON_FIELD: verdict.reason, REFUSED_FIELD: verdict.refused}
    return notice_record(exchange, UNPARSED, policy, **fields)


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


def _v5_who(exchange: Exchange) -> dict:
    """v5's fields on every line of an exchange: B3, and the LOG-1 caller fields and era."""
    return {
        IDENTITY_STRENGTH_FIELD: identity_strength(exchange),
        BASELINE_KEY_FIELD: exchange.baseline_key,
        ZONE_FIELD: exchange.zone,
        PROTOCOL_ERA_FIELD: exchange.era,
    }


def _v5_line_fields(
    exchange: Exchange, direction: str, status: int | None, message: dict | None
) -> dict:
    """v5's fields on a wire line. A request: its conformance issues, and for a scored call its
    argument bytes and logical call. A reply: the raw reply bytes when known, and for a reply
    to a scored call its payload bytes, logical call and outcome (a bodiless reply: the
    outcome its status gives the exchange's calls)."""
    fields = _v5_who(exchange)
    if direction == TO_SERVER and message:
        is_request = "method" in message and "id" in message
        facts = exchange.call_facts(message) if is_request else CallFacts()
        fields[PROTOCOL_ISSUES_FIELD] = list(exchange.protocol_issues) or None
        fields[ARG_BYTES_FIELD] = facts.arg_bytes
        fields[LOGICAL_CALL_FIELD] = facts.logical_call
    elif direction == TO_AGENT:
        fields[REPLY_WIRE_BYTES_FIELD] = exchange.reply_wire_bytes
        answered = reply_facts(exchange, status, message)
        if answered is not None:
            fields[REPLY_BYTES_FIELD] = answered.reply_bytes
            fields[LOGICAL_CALL_FIELD] = answered.logical_call
            fields[OUTCOME_FIELD] = answered.outcome
        elif message is None and exchange.calls:
            fields[OUTCOME_FIELD] = call_outcome(status, None)
    return fields


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
