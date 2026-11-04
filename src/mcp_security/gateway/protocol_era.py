"""Which MCP era a request speaks, what it breaks, and which logical call it belongs to.

v5 of the dynamic layer must give the same scores whether a caller speaks legacy MCP
(revision 2025-11-25 and earlier: an ``initialize`` handshake and optional sessions) or modern
MCP (2026-07-28: no handshake, no sessions, the version and capabilities in every request's
``_meta``). This module holds the wire facts that make that possible; it is pure, and the
gateway (``wire_log.py``) and the simulator call the same functions.

- **E3, era:** :func:`classify` says legacy or modern for one message, :func:`classify_request`
  for a whole HTTP request.
- **E7, conformance:** :func:`conformance_issues` lists what a modern client request breaks
  (missing ``_meta`` keys or headers, a header that disagrees with the body or comes twice,
  legacy headers, a batch). The issues are logged, never scored.
- **ARG-1, era-free inputs:** :func:`argument_bytes` (``params.arguments``) and
  :func:`reply_payload_bytes` (``result.content``) do not depend on the envelope;
  :func:`call_outcome` says whether the server accepted a call; :class:`LogicalCalls` folds an
  MRTR continuation, or a retry of a rejected call, into the call it continues.

Sources: knowledge base note ``01-mcp-protocol.md`` (MCP 2026-07-28, SEP-2567, SEP-2575, read
on primary sources there). The SEP-2322 (MRTR) wire names and the rejecting error codes were
verified on 2026-10-27 against the 2026-07-28 specification and the MCP Python SDK 2.3.0
(``mcp_types``, ``mcp.shared.inbound``), which ``tests/gateway/test_protocol_era.py`` pins.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from mcp_security.behaviour.engine import ACCEPTED, LEGACY_ERA, MODERN_ERA, REJECTED
from mcp_security.gateway.http_wire import decode_header_value

#: The first modern revision (versioning page: "Modern = revision 2026-07-28 and later").
MODERN_FROM = "2026-07-28"
#: The version a server SHOULD assume when a request carries no ``MCP-Protocol-Version``
#: header (KB 01: "MAY treat a request that omits the header as protocol version 2025-03-26").
ASSUMED_VERSION = "2025-03-26"
#: A revision identifier is an ISO date; only those are compared (as strings) with MODERN_FROM,
#: so a header such as ``garbage`` cannot sort above it.
REVISION_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: The only HTTP method that carries a modern request: GET and DELETE are legacy (a modern-only
#: server answers them with 405).
MODERN_HTTP_METHOD = "POST"

INIT_METHOD = "initialize"
CALL_METHOD = "tools/call"
RESOURCE_READ_METHOD = "resources/read"
PROMPT_GET_METHOD = "prompts/get"
#: Methods whose ``Mcp-Name`` header is REQUIRED (2026-07-28 Streamable HTTP) - also the methods
#: v5 scores as calls (AI-10). The name they carry is ``params.name``, or ``params.uri``.
NAMED_METHODS = frozenset({CALL_METHOD, RESOURCE_READ_METHOD, PROMPT_GET_METHOD})
SCORED_METHODS = NAMED_METHODS

#: Per-request ``_meta`` keys of protocol 2026-07-28.
META_PROTOCOL = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_CLIENT = "io.modelcontextprotocol/clientInfo"

#: Request headers, lower case (HTTP names are case-insensitive; lookups lower-case them).
PROTOCOL_HEADER = "mcp-protocol-version"
SESSION_HEADER = "mcp-session-id"
LAST_EVENT_HEADER = "last-event-id"
METHOD_HEADER = "mcp-method"
NAME_HEADER = "mcp-name"
#: The routing headers a server compares with the body, as the spec spells them in an issue.
#: Sent twice, a reader taking the first copy and one taking the last act on different calls
#: (the SDK's ``find_duplicated_routing_header`` rejects the request); the gateway reads the
#: first copy, as Starlette's ``Headers.get`` does in the proxy.
ROUTING_HEADERS = {
    PROTOCOL_HEADER: "MCP-Protocol-Version",
    METHOD_HEADER: "Mcp-Method",
    NAME_HEADER: "Mcp-Name",
}

#: E7 conformance issues, as logged in ``gateway.protocol_issues``.
ISSUE_META_VERSION = "meta:protocolVersion"
ISSUE_META_CAPABILITIES = "meta:clientCapabilities"
ISSUE_HEADER_VERSION = "header:MCP-Protocol-Version"
ISSUE_HEADER_METHOD = "header:Mcp-Method"
ISSUE_HEADER_NAME = "header:Mcp-Name"
ISSUE_MISMATCH_VERSION = "mismatch:MCP-Protocol-Version"
ISSUE_MISMATCH_METHOD = "mismatch:Mcp-Method"
ISSUE_MISMATCH_NAME = "mismatch:Mcp-Name"
ISSUE_DUPLICATE_PREFIX = "duplicate:"  # + the header's name: a routing header sent twice
ISSUE_DUPLICATE_VERSION = ISSUE_DUPLICATE_PREFIX + ROUTING_HEADERS[PROTOCOL_HEADER]
ISSUE_DUPLICATE_METHOD = ISSUE_DUPLICATE_PREFIX + ROUTING_HEADERS[METHOD_HEADER]
ISSUE_DUPLICATE_NAME = ISSUE_DUPLICATE_PREFIX + ROUTING_HEADERS[NAME_HEADER]
ISSUE_LEGACY_SESSION = "legacy:Mcp-Session-Id"
ISSUE_LEGACY_EVENT = "legacy:Last-Event-ID"
#: A JSON-RPC batch: added in 2025-03-26, removed in 2025-06-18 (KB 01), so a modern request
#: never carries one. Raised per request (:func:`request_issues`) when a body holds more than one
#: message; a one-element array reads as one message and is not seen.
ISSUE_LEGACY_BATCH = "legacy:batch"

#: ARG-1: a server's answers that reject a request, verified on 2026-10-27 against the 2026-07-28
#: specification (spec 2.1) and the MCP Python SDK 2.3.0 (``mcp_types.jsonrpc``; its server sends
#: each code with the HTTP status in ``mcp.shared.inbound.ERROR_CODE_HTTP_STATUS``). HTTP 400 for
#: a malformed modern request or a missing session id, 404 for an ended session or an unknown
#: method, 405 for GET/DELETE on a modern-only server. JSON-RPC -32602 invalid params (a missing
#: protocol version or an unknown resource included), -32601 method not found, -32020 header
#: mismatch, -32021 a required client capability not declared, -32022 unsupported protocol
#: version. Every other answer counts as accepted (:func:`call_outcome`).
REJECTING_HTTP_STATUSES = frozenset({400, 404, 405})
INVALID_PARAMS, METHOD_NOT_FOUND = -32602, -32601
HEADER_MISMATCH, MISSING_CLIENT_CAPABILITY, UNSUPPORTED_VERSION = -32020, -32021, -32022
REJECTING_RPC_CODES = frozenset(
    {
        INVALID_PARAMS,
        METHOD_NOT_FOUND,
        HEADER_MISMATCH,
        MISSING_CLIENT_CAPABILITY,
        UNSUPPORTED_VERSION,
    }
)
#: ARG-1: an MRTR ``input_required`` answer. The logical call is not over: the client retries
#: it with the answers, and only that retry's answer accepts or rejects it. It is not an outcome
#: of the call (spec 2.1), so nothing is committed on it.
CONTINUED = "continued"
OUTCOMES = (ACCEPTED, REJECTED, CONTINUED)

#: SEP-2322 (MRTR) wire names, verified on 2026-10-27 against the 2026-07-28 specification
#: (``basic/patterns/mrtr``) and the SDK's ``InputRequiredResult`` and
#: ``InputResponseRequestParams``. The interim answer is a *result*
#: ``{"resultType": "input_required", "inputRequests": {...}, "requestState": "..."}``, allowed
#: only on tools/call, resources/read and prompts/get. The client retries the same method, name
#: and arguments under a **new** JSON-RPC id, with ``params.inputResponses`` and the echoed
#: ``params.requestState`` (in ``params``, not ``_meta``).
MRTR_RESULT_TYPE_FIELD = "resultType"
MRTR_INPUT_REQUIRED = "input_required"
MRTR_REQUEST_STATE_FIELD = "requestState"
MRTR_INPUT_RESPONSES_FIELD = "inputResponses"

#: Where each scored method's answer carries its payload (``result.<field>``): the bytes a
#: caller read. tools/call: ``content`` (spec ARG-1); resources/read: ``contents``;
#: prompts/get: ``messages``.
PAYLOAD_FIELDS = {
    CALL_METHOD: "content",
    RESOURCE_READ_METHOD: "contents",
    PROMPT_GET_METHOD: "messages",
}

#: ARG-1: sizes and digests encode text as UTF-8, letting a lone surrogate through as its three
#: bytes: ``json.loads`` accepts one (escaped, or as raw bytes), and a strict encode would raise.
UTF8, SURROGATES = "utf-8", "surrogatepass"

#: ARG-1: a modern request retried over legacy after a rejection folds into the call it retries
#: only within this many seconds of it.
FALLBACK_FOLD_S = 5.0
#: An MRTR request state is remembered this long for its continuation (the user may take a
#: while to answer an elicitation); the same idle time as a session (DEP-5).
REQUEST_STATE_TTL_S = 3_600.0
#: Each of :class:`LogicalCalls`'s maps keeps at most this many entries, oldest dropped first
#: (the same bound as ``framework.MAX_PENDING_CALLS``).
MAX_LOGICAL_CALLS = 65_536


@dataclass(frozen=True)
class ProtocolView:
    """E3: a message's era and the protocol versions the request states.

    ``version`` is the one the request speaks: the body's ``_meta`` version, else the header,
    else ``initialize``'s ``protocolVersion``, else :data:`ASSUMED_VERSION`.
    """

    era: str  # LEGACY_ERA or MODERN_ERA
    version: str
    version_header: str | None = None  # MCP-Protocol-Version, as sent
    version_body: str | None = None  # params._meta's protocolVersion, when a string


def classify(http_method: str, headers: Mapping[str, str], message: dict | None) -> ProtocolView:
    """E3: legacy or modern, for one message of a request.

    Modern iff the request is a POST, the message is not ``initialize``, and either its
    ``_meta`` names a protocol version (a non-empty string) or its ``MCP-Protocol-Version``
    header names :data:`MODERN_FROM` or later. Everything else is legacy: ``initialize``, GET
    and DELETE, a legacy header, and a request with neither header nor ``_meta`` (version
    2025-03-26 assumed). A header sent twice counts by its first copy, as the proxy reads it.
    """
    header = _headers(headers).get(PROTOCOL_HEADER)
    body = _text(_meta(message).get(META_PROTOCOL))
    initializing = isinstance(message, dict) and message.get("method") == INIT_METHOD
    init_version = _text(_params(message).get("protocolVersion")) if initializing else None
    modern = (
        http_method.upper() == MODERN_HTTP_METHOD
        and not initializing
        and (body is not None or is_modern_revision(header))
    )
    return ProtocolView(
        era=MODERN_ERA if modern else LEGACY_ERA,
        version=body or header or init_version or ASSUMED_VERSION,
        version_header=header,
        version_body=body,
    )


def classify_request(
    http_method: str, headers: Mapping[str, str], messages: Iterable[dict]
) -> ProtocolView:
    """E3: the era of a whole HTTP request. Modern only if every message with a method is; a
    request without one is classified from its headers. The versions are those of the first
    message with a method. A batch of modern messages stays modern: no revision since
    2025-06-18 allows a batch, so :func:`request_issues` logs it as ``legacy:batch``."""
    views = [classify(http_method, headers, m) for m in messages if _has_method(m)]
    if not views:
        return classify(http_method, headers, None)
    first = views[0]
    if all(view.era == MODERN_ERA for view in views):
        return first
    return ProtocolView(LEGACY_ERA, first.version, first.version_header, first.version_body)


def is_modern_revision(version: object) -> bool:
    """A revision identifier (an ISO date) of :data:`MODERN_FROM` or later."""
    return (
        isinstance(version, str) and bool(REVISION_DATE.match(version)) and (version >= MODERN_FROM)
    )


def conformance_issues(
    view: ProtocolView, headers: Mapping[str, str], message: dict | None, http: bool = True
) -> tuple[str, ...]:
    """E7: what a modern client request breaks, in a fixed order; empty for a legacy request,
    a notification or a reply (2026-07-28 sets the per-request fields on client requests only).
    ``clientInfo`` is optional (a SHOULD, KB 01), so its absence is no issue.

    ``http`` adds the Streamable HTTP header rules (stdio has no headers)."""
    if view.era != MODERN_ERA or not _is_client_request(message):
        return ()
    meta = _meta(message)
    issues = []
    if _text(meta.get(META_PROTOCOL)) is None:
        issues.append(ISSUE_META_VERSION)
    if not isinstance(meta.get(META_CAPABILITIES), dict):
        issues.append(ISSUE_META_CAPABILITIES)
    if http:
        issues.extend(_header_issues(view, headers, message))
    return tuple(issues)


def request_issues(
    http_method: str, headers: Mapping[str, str], messages: Iterable[dict], http: bool = True
) -> tuple[str, ...]:
    """E7: the issues of every message in one request, each once, in first-seen order, then
    ``legacy:batch`` when the body held more than one message; empty when the request is
    legacy (:func:`classify_request`)."""
    messages = list(messages)
    if classify_request(http_method, headers, messages).era != MODERN_ERA:
        return ()
    seen: dict[str, None] = {}
    for message in messages:
        view = classify(http_method, headers, message)
        for issue in conformance_issues(view, headers, message, http):
            seen.setdefault(issue)
    if len(messages) > 1:
        seen.setdefault(ISSUE_LEGACY_BATCH)
    return tuple(seen)


def call_outcome(status: int | None, reply: dict | None) -> str:
    """ARG-1: whether the server accepted the call ``reply`` answers.

    Rejected: HTTP 400/404/405, or a JSON-RPC error in :data:`REJECTING_RPC_CODES` (-32602,
    -32601, -32020, -32021, -32022). Continued: an MRTR ``input_required`` result (the call goes
    on in a retry). Anything else is accepted - a tool that ran and failed (``isError``)
    included, as the server took it. So are a 401, 403, 429 or 5xx status and the JSON-RPC codes
    -32600, -32603 and -32700, which spec 2.1 does not list: whether the server took such a call
    is an open author decision (Batch 1 review, I6 finding 5).
    """
    if status in REJECTING_HTTP_STATUSES:
        return REJECTED
    error = reply.get("error") if isinstance(reply, dict) else None
    if isinstance(error, dict) and error.get("code") in REJECTING_RPC_CODES:
        return REJECTED
    if _input_required(reply):
        return CONTINUED
    return ACCEPTED


def json_bytes(value: object) -> int:
    """UTF-8 bytes of ``value`` as compact JSON: one size for the same value however a client
    spaced or ordered it (ARG-1's era-free size). A lone surrogate, which ``json.loads`` lets
    through (an escaped ``\\ud800`` or its raw bytes), counts its three bytes instead of raising."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    return len(text.encode(UTF8, SURROGATES))


def argument_bytes(message: dict) -> int:
    """ARG-1: request bytes, the bytes of ``params.arguments`` (absent counts as ``{}``). The
    envelope (``_meta``, headers, ids) never counts, so both eras give the same size."""
    arguments = _params(message).get("arguments")
    return json_bytes({} if arguments is None else arguments)


def reply_payload_bytes(method: str | None, reply: dict | None) -> int | None:
    """ARG-1: reply bytes, the bytes of the result's payload (``result.content`` for a tool
    call; see :data:`PAYLOAD_FIELDS`). None for an error, an MRTR ``input_required`` result or
    a method that is not scored. A result's ``_meta`` never counts."""
    field = PAYLOAD_FIELDS.get(method or "")
    result = reply.get("result") if isinstance(reply, dict) else None
    if field is None or not isinstance(result, dict) or _input_required(reply):
        return None
    return json_bytes(result.get(field, []))


def request_state_of(message: dict | None) -> str | None:
    """The MRTR request state a retried call echoes, ``params.requestState`` (see
    :data:`MRTR_REQUEST_STATE_FIELD`)."""
    state = _params(message).get(MRTR_REQUEST_STATE_FIELD)
    return state if isinstance(state, str) and state else None


def minted_request_state(reply: dict | None) -> str | None:
    """The MRTR request state an ``input_required`` result hands the client, if any."""
    result = reply.get("result") if isinstance(reply, dict) else None
    if not _input_required(reply) or not isinstance(result, dict):
        return None
    state = result.get(MRTR_REQUEST_STATE_FIELD)
    return state if isinstance(state, str) and state else None


@dataclass
class _Attempt:
    """One request of a logical call: its key, when it was sent, how the server answered."""

    key: str
    ts: float
    outcome: str | None = None


#: What makes two requests the same call: caller, method, name and a digest of the arguments.
CallSignature = tuple[str, str, str, bytes]


class LogicalCalls:
    """ARG-1: the logical call each scored request belongs to, for one route.

    A request starts a new logical call (keyed by the ``fresh`` key the caller gives) unless:

    - it is an **MRTR continuation**: it echoes a request state an ``input_required`` answer
      minted for the same caller, method, name and arguments (identical arguments imply the
      same touched asset). A continuation that changes its arguments is a new call;
    - it is a **retry of a rejected call**: the same caller, method, name and arguments within
      :data:`FALLBACK_FOLD_S` of an attempt the server rejected (a modern request retried over
      legacy after a 400). A repeat of an *accepted* call is never folded, so identical calls
      in a burst stay separate calls (Burst, Call rate and Repetition see each of them).

    Memory is bounded: recent attempts are kept for the fold window, unanswered calls and
    request states up to :data:`MAX_LOGICAL_CALLS` each, request states for at most
    :data:`REQUEST_STATE_TTL_S`; the oldest go first.
    """

    def __init__(
        self,
        fold_window_s: float = FALLBACK_FOLD_S,
        state_ttl_s: float = REQUEST_STATE_TTL_S,
        max_entries: int = MAX_LOGICAL_CALLS,
    ) -> None:
        if fold_window_s < 0 or state_ttl_s < 0 or max_entries < 1:
            raise ValueError("fold window and state TTL must be >= 0, max_entries >= 1")
        self.fold_window_s = fold_window_s
        self.state_ttl_s = state_ttl_s
        self.max_entries = max_entries
        self._recent: OrderedDict[CallSignature, _Attempt] = OrderedDict()
        self._unanswered: OrderedDict[str, CallSignature] = OrderedDict()
        self._states: OrderedDict[tuple[str, str], tuple[str, CallSignature, float]] = OrderedDict()

    def key_for(self, caller: str, message: dict, ts: float, fresh: str) -> str:
        """The logical-call key of ``message`` (a scored request by ``caller`` at ``ts``):
        the key of the call it continues, else ``fresh``."""
        self._expire(ts)
        signature = call_signature(caller, message)
        key = self._continued(caller, signature, request_state_of(message))
        previous = self._recent.get(signature)
        if key is None and previous is not None and previous.outcome == REJECTED:
            key = previous.key if ts - previous.ts <= self.fold_window_s else None
        key = key or fresh
        self._recent[signature] = _Attempt(key, ts)
        self._recent.move_to_end(signature)
        self._unanswered[key] = signature
        self._unanswered.move_to_end(key)
        _trim(self._recent, self.max_entries)
        _trim(self._unanswered, self.max_entries)
        return key

    def answered(self, key: str | None, outcome: str, reply: dict | None, ts: float) -> None:
        """The server answered the request of logical call ``key`` with ``outcome``
        (:func:`call_outcome`); an ``input_required`` ``reply`` leaves a request state for its
        continuation. An unknown or None key does nothing."""
        signature = self._unanswered.pop(key, None) if key is not None else None
        if signature is None:
            return
        attempt = self._recent.get(signature)
        if attempt is not None and attempt.key == key:
            attempt.outcome = outcome
        state = minted_request_state(reply) if outcome == CONTINUED else None
        if state is not None:
            self._states[(signature[0], state)] = (key, signature, ts)
            self._states.move_to_end((signature[0], state))
            _trim(self._states, self.max_entries)

    @property
    def entries(self) -> int:
        """Entries held across every map (for memory checks). Not ``__len__``: an empty book
        must not be falsy."""
        return len(self._recent) + len(self._unanswered) + len(self._states)

    def _continued(self, caller: str, signature: CallSignature, state: str | None) -> str | None:
        """The key of the call an MRTR continuation continues, consuming its request state."""
        found = self._states.get((caller, state)) if state is not None else None
        if found is None or found[1] != signature:
            return None
        del self._states[(caller, state)]
        return found[0]

    def _expire(self, now: float) -> None:
        while self._recent:
            signature, attempt = next(iter(self._recent.items()))
            if now - attempt.ts <= self.fold_window_s:
                break
            del self._recent[signature]
        while self._states:
            entry, (_, _, minted) = next(iter(self._states.items()))
            if now - minted <= self.state_ttl_s:
                break
            del self._states[entry]


def call_signature(caller: str, message: dict) -> CallSignature:
    """What makes two requests the same call: caller, method, name (or URI) and a SHA-256 of
    the canonical arguments. Absent arguments count as ``{}``, as in :func:`argument_bytes`;
    ``[]``, ``""`` or ``0`` stay themselves, and the name keeps its JSON type (``null`` is not
    ``"None"``)."""
    params = _params(message)
    name = params.get("name") if "name" in params else params.get("uri")
    arguments = params.get("arguments")
    canonical = json.dumps(
        {} if arguments is None else arguments, sort_keys=True, ensure_ascii=False, default=str
    )
    digest = hashlib.sha256(canonical.encode(UTF8, SURROGATES)).digest()
    named = json.dumps(name, ensure_ascii=False, default=str)
    return (caller, str(message.get("method")), named, digest)


def _header_issues(view: ProtocolView, headers: Mapping[str, str], message: dict) -> list[str]:
    """The Streamable HTTP rules of 2026-07-28: required headers, header = body, each routing
    header once, no legacy headers."""
    items = _header_items(headers)
    first = _first_values(items)
    method = message.get("method")
    issues = []
    if view.version_header is None:
        issues.append(ISSUE_HEADER_VERSION)
    if METHOD_HEADER not in first:
        issues.append(ISSUE_HEADER_METHOD)
    if method in NAMED_METHODS and NAME_HEADER not in first:
        issues.append(ISSUE_HEADER_NAME)
    if view.version_header is not None and view.version_body is not None:
        if view.version_header != view.version_body:
            issues.append(ISSUE_MISMATCH_VERSION)
    if METHOD_HEADER in first and first[METHOD_HEADER] != method:
        issues.append(ISSUE_MISMATCH_METHOD)
    if NAME_HEADER in first:
        params = _params(message)
        named = params.get("name") if "name" in params else params.get("uri")
        if decode_header_value(first[NAME_HEADER]) != named:
            issues.append(ISSUE_MISMATCH_NAME)
    repeated = _repeated(items)
    issues.extend(
        ISSUE_DUPLICATE_PREFIX + label
        for name, label in ROUTING_HEADERS.items()
        if name in repeated
    )
    if SESSION_HEADER in first:
        issues.append(ISSUE_LEGACY_SESSION)
    if LAST_EVENT_HEADER in first:
        issues.append(ISSUE_LEGACY_EVENT)
    return issues


def _headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Lower-cased header names, each with its first value (Starlette's ``Headers.get``)."""
    return _first_values(_header_items(headers))


def _header_items(headers: Mapping[str, str]) -> list[tuple[str, str]]:
    """Every (lower-cased name, value) pair, repeats included: Starlette's ``Headers.items``
    lists each copy; ``httpx.Headers`` joins copies in ``items`` and lists them in
    ``multi_items``."""
    multi = getattr(headers, "multi_items", None)
    pairs = multi() if callable(multi) else headers.items()
    return [(str(name).lower(), value) for name, value in pairs]


def _first_values(items: list[tuple[str, str]]) -> dict[str, str]:
    first: dict[str, str] = {}
    for name, value in items:
        first.setdefault(name, value)
    return first


def _repeated(items: list[tuple[str, str]]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for name, _ in items:
        (repeated if name in seen else seen).add(name)
    return repeated


def _text(value: object) -> str | None:
    """A non-empty string, else None: an empty version is no version."""
    return value if isinstance(value, str) and value else None


def _params(message: dict | None) -> dict:
    params = message.get("params") if isinstance(message, dict) else None
    return params if isinstance(params, dict) else {}


def _meta(message: dict | None) -> dict:
    meta = _params(message).get("_meta")
    return meta if isinstance(meta, dict) else {}


def _has_method(message: object) -> bool:
    return isinstance(message, dict) and isinstance(message.get("method"), str)


def _is_client_request(message: object) -> bool:
    return isinstance(message, dict) and _has_method(message) and "id" in message


def _input_required(reply: dict | None) -> bool:
    result = reply.get("result") if isinstance(reply, dict) else None
    return isinstance(result, dict) and result.get(MRTR_RESULT_TYPE_FIELD) == MRTR_INPUT_REQUIRED


def _trim(entries: OrderedDict, limit: int) -> None:
    while len(entries) > limit:
        entries.popitem(last=False)
