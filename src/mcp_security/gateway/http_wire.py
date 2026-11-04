"""What the HTTP layer says about a request, read with care.

- The client's address behind trusted proxies. ``X-Forwarded-For`` is written by whoever
  sends the request, so it is believed only when the peer is a proxy the config trusts,
  and only up to the first hop that is not one: each proxy appends the address it saw, so
  the list is read right to left (OpenTelemetry: ``client.address`` is the client behind
  any intermediaries).
- MCP 2026-07-28 mirrors the method and tool name into ``Mcp-Method`` / ``Mcp-Name``; a
  value outside plain ASCII is sent as ``=?base64?...?=`` and must be decoded before it is
  compared with the body.
- The JSON-RPC messages in a body or an SSE stream, read without changing a byte of it.
  The reply tap (RPL-1) counts the raw bytes, buffers in a ``bytearray`` and finds SSE frame
  ends by scanning only the new bytes, so a 50 MB reply costs linear time; above an optional
  size cap a body or frame is counted but not parsed.
- GW-1 (v5 routes only): why a request body cannot be read as JSON-RPC (an encoded body,
  broken JSON, no JSON-RPC object), and the gateway's verdict on it. An encoded body is always
  refused (415), since a server that inflates it would run a call nobody scored; any other is
  forwarded and logged, or refused with 400 on a ``fail_closed_unparsed`` route.
"""

from __future__ import annotations

import base64
import binascii
import ipaddress
import json
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network

Network = IPv4Network | IPv6Network
SENTINEL_PREFIX, SENTINEL_SUFFIX = "=?base64?", "?="
SSE_CONTENT_TYPE = "text/event-stream"
#: An SSE frame ends with an empty line: ``\n`` then ``\n`` or ``\r\n``, the first ``\n`` maybe
#: after a ``\r`` (the same frames as replacing ``\r\n`` by ``\n`` and splitting on ``\n\n``).
#: The tap finds each ``\n`` with ``bytearray.find`` and checks the bytes after it.
LF, CR = ord("\n"), ord("\r")
#: The longest frame end (``\r\n\r\n``): an over-cap frame keeps this many bytes minus one.
SSE_FRAME_END_MAX_BYTES = 4
#: RPL-1: the size cap a v5 route passes to :class:`MessageTap`: a reply body or SSE frame
#: larger than this is counted, not parsed. (None, the default, parses every size, as v1-v4.)
MAX_PARSED_REPLY_BYTES = 16 * 1024 * 1024
#: GW-1: why a request body is not read (``gateway.unparsed_reason``).
UNPARSED_ENCODED = "content_encoding"  # a Content-Encoding other than identity
#: Not JSON (bad UTF-8 or syntax, an integer longer than Python reads), nested too deep to
#: read, or holding a lone surrogate (an escaped ``\ud800`` or its raw bytes), which
#: ``json.loads`` accepts but no UTF-8 text, so no log line, can carry.
UNPARSED_JSON = "invalid_json"
UNPARSED_NOT_JSONRPC = "not_jsonrpc"  # JSON, but not (only) JSON-RPC objects
UNPARSED_REASONS = (UNPARSED_ENCODED, UNPARSED_JSON, UNPARSED_NOT_JSONRPC)
IDENTITY_ENCODINGS = frozenset({"", "identity"})
#: The JSON escape that can spell a surrogate; a body that is pure ASCII without it holds none.
JSON_UNICODE_ESCAPE = b"\\u"
#: GW-1: what a ``fail_closed_unparsed`` route answers a body it cannot read.
UNPARSED_REFUSED_STATUS = 400
#: GW-1: what every v5 route answers an encoded body (RFC 9110 15.5.16: 415 for an unsupported
#: content coding, with ``Accept-Encoding`` naming the codings it takes).
UNPARSED_ENCODED_STATUS = 415
ACCEPT_ENCODING_HEADER, IDENTITY_CODING = "Accept-Encoding", "identity"
#: GW-1: the reasons refused whatever ``fail_closed_unparsed`` says. Express's ``express.json()``
#: inflates gzip and deflate bodies by default, so a forwarded encoded body can run unscored.
ALWAYS_REFUSED = frozenset({UNPARSED_ENCODED})


def parse_networks(entries: tuple[str, ...] | list[str]) -> tuple[Network, ...]:
    """Trusted proxy addresses or CIDRs; fails loudly on one that is neither."""
    return tuple(ipaddress.ip_network(entry, strict=False) for entry in entries)


def client_behind(
    peer: str | None, forwarded: str | None, trusted: tuple[Network, ...]
) -> str | None:
    """The client's address: the peer itself, unless the peer is a trusted proxy — then the
    nearest ``X-Forwarded-For`` hop that is not one (an unreadable hop stops the walk)."""
    if not peer or not forwarded or not _trusted(_address(peer), trusted):
        return peer
    address = peer
    for hop in reversed([part.strip() for part in forwarded.split(",")]):
        parsed = _address(hop)
        if parsed is None:
            break
        address = hop
        if not _trusted(parsed, trusted):
            break
    return address


def decode_header_value(value: str | None) -> str | None:
    """An ``Mcp-Name`` / ``Mcp-Param-*`` value with the base64 sentinel removed; a value
    that claims base64 but is not is returned as sent, so it shows up as a mismatch."""
    if value is None or not (value.startswith(SENTINEL_PREFIX) and value.endswith(SENTINEL_SUFFIX)):
        return value
    try:
        inner = value[len(SENTINEL_PREFIX) : -len(SENTINEL_SUFFIX)]
        return base64.b64decode(inner, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return value


def _address(text: str) -> IPv4Address | IPv6Address | None:
    try:
        return ipaddress.ip_address(text)
    except ValueError:
        return None


def _trusted(address: IPv4Address | IPv6Address | None, trusted: tuple[Network, ...]) -> bool:
    return address is not None and any(address in network for network in trusted)


def parse_messages(raw: bytes) -> list[dict]:
    """JSON-RPC messages in a body: one object, a batch, or nothing. Garbage is kept visible."""
    if not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [{"unparsed": raw.decode("utf-8", errors="replace")}]
    items = parsed if isinstance(parsed, list) else [parsed]
    return [item for item in items if isinstance(item, dict)]


def body_problem(raw: bytes, content_encoding: str | None = None) -> str | None:
    """GW-1: why the gateway cannot read this request body as JSON-RPC, or None.

    An empty body is no problem (a GET, a DELETE). A ``Content-Encoding`` other than identity
    is one, since the bytes are not the JSON the server will decode; so is JSON that does not
    load or that holds a lone surrogate (:data:`UNPARSED_JSON`), and JSON that is not an object
    or a batch of objects only (:func:`parse_messages` would drop what is not an object). The
    proxy asks this before it parses or logs the body's messages.
    """
    if not raw.strip():
        return None
    codings = [part.strip().lower() for part in (content_encoding or "").split(",")]
    if any(coding not in IDENTITY_ENCODINGS for coding in codings):
        return UNPARSED_ENCODED
    try:
        parsed = json.loads(raw)
    except (ValueError, RecursionError):  # JSONDecodeError and UnicodeDecodeError included
        return UNPARSED_JSON
    items = parsed if isinstance(parsed, list) else [parsed]
    if not items or not all(isinstance(item, dict) for item in items):
        return UNPARSED_NOT_JSONRPC
    if not _utf8_writable(raw, parsed):
        return UNPARSED_JSON
    return None


def _utf8_writable(raw: bytes, parsed: object) -> bool:
    """Can ``parsed`` (read from ``raw``) be written back as strict UTF-8 JSON? Not when it
    holds a lone surrogate: ``json.loads`` passes an escaped ``\\ud800``, and the raw bytes
    ``ED A0 80``, through as one, and the log, the sizes and the pseudonyms would raise on it."""
    if raw.isascii() and JSON_UNICODE_ESCAPE not in raw:
        return True  # neither an escape nor a raw byte that could spell a surrogate
    try:
        json.dumps(parsed, ensure_ascii=False).encode()
    except (UnicodeEncodeError, RecursionError):
        return False
    return True


@dataclass(frozen=True)
class UnparsedVerdict:
    """GW-1: the gateway's verdict on a body it cannot read. ``refused``: answer
    :attr:`status` (with :attr:`headers`) and do not forward; otherwise forward it as today and
    log the verdict, so an unscored forward is never silent."""

    reason: str  # one of UNPARSED_REASONS
    refused: bool

    @property
    def status(self) -> int | None:
        """The status to answer instead of forwarding; None when the body is forwarded."""
        if not self.refused:
            return None
        return (
            UNPARSED_ENCODED_STATUS if self.reason == UNPARSED_ENCODED else UNPARSED_REFUSED_STATUS
        )

    @property
    def headers(self) -> dict[str, str]:
        """The headers of the refusal: ``Accept-Encoding: identity`` for an encoded body."""
        if self.refused and self.reason == UNPARSED_ENCODED:
            return {ACCEPT_ENCODING_HEADER: IDENTITY_CODING}
        return {}


def unparsed_verdict(
    raw: bytes, content_encoding: str | None, fail_closed: bool
) -> UnparsedVerdict | None:
    """GW-1: the verdict on a request body on a v5 route, or None when it reads as JSON-RPC
    (v1-v4 routes forward every body as before and ask nothing). A reason in
    :data:`ALWAYS_REFUSED` is refused whatever ``fail_closed`` (the route's
    ``fail_closed_unparsed``) says; the others are refused only on a fail-closed route."""
    reason = body_problem(raw, content_encoding)
    if reason is None:
        return None
    return UnparsedVerdict(reason, refused=fail_closed or reason in ALWAYS_REFUSED)


@dataclass(frozen=True)
class Frame:
    """One reply body (JSON) or SSE event, as read. ``wire_bytes``: its raw bytes, the frame
    end included. ``parsed``: False when it was over the tap's size cap and only counted."""

    messages: list[dict]
    wire_bytes: int
    parsed: bool = True


class MessageTap:
    """Reads JSON-RPC messages out of a response body fed chunk by chunk.

    SSE frames are emitted as soon as each one is complete, so a long-lived stream is logged
    while it is open; a plain JSON body is parsed once it ends. Each chunk costs time in its own
    length (RPL-1): bytes go into a ``bytearray`` and only new bytes are searched for a frame
    end. ``wire_bytes`` counts every raw byte fed. With ``max_parse_bytes`` set, a body or frame
    longer than that is counted but not kept or parsed (``unparsed`` counts them); None, the
    default, parses every size.

    Every route reads replies with this tap, v1-v4 included. Its messages are those of the
    pre-RPL-1 tap for any chunking of a stream whose lines end in LF or CRLF, and for any stream
    read in one chunk: the frames of replacing ``\\r\\n`` by ``\\n`` and splitting on ``\\n\\n``
    over the whole stream. On a stream with bare CRs (which SSE allows as line ends, and neither
    tap reads as one) the old tap's frames depended on where the chunks fell; this one's do not.
    """

    def __init__(self, content_type: str, max_parse_bytes: int | None = None) -> None:
        if max_parse_bytes is not None and max_parse_bytes < 0:
            raise ValueError(f"max_parse_bytes must be >= 0, not {max_parse_bytes}")
        self._sse = content_type.startswith(SSE_CONTENT_TYPE)
        self.max_parse_bytes = max_parse_bytes
        self.wire_bytes = 0  # RPL-1: raw bytes of the reply so far
        self.unparsed = 0  # bodies or frames over the cap, counted and not parsed
        self._buffer = bytearray()
        self._scan_from = 0  # where the next search for an SSE frame end starts
        self._dropped = 0  # bytes of the current over-cap body or frame not kept

    def feed(self, chunk: bytes) -> list[dict]:
        """The messages of every frame this chunk completes."""
        return [message for frame in self.feed_frames(chunk) for message in frame.messages]

    def close(self) -> list[dict]:
        """The messages of what is left once the reply has ended."""
        return [message for frame in self.close_frames() for message in frame.messages]

    def feed_frames(self, chunk: bytes) -> list[Frame]:
        """Every frame this chunk completes (none for a JSON body until it ends)."""
        self.wire_bytes += len(chunk)
        if not self._sse:
            self._keep(chunk)
            return []
        buffer = self._buffer
        buffer += chunk
        frames, start = [], 0
        while (found := self._frame_end(start)) is not None:
            begin, end = found
            frames.append(self._frame(buffer[start:begin], end - start))
            start = end
        if start:
            del buffer[:start]
            self._scan_from -= start
        if self._over_cap(len(buffer)):  # keep only what a frame end may still start in
            dropped = max(0, len(buffer) - (SSE_FRAME_END_MAX_BYTES - 1))  # a cap under 3 too
            self._dropped += dropped
            del buffer[:dropped]
            self._scan_from = max(0, self._scan_from - dropped)
        return frames

    def close_frames(self) -> list[Frame]:
        """What is left once the reply has ended: the JSON body, or a last unterminated frame."""
        rest = bytes(self._buffer)
        self._buffer.clear()
        self._scan_from = 0
        if not rest and not self._dropped:
            return []
        if self._sse:
            return [self._frame(rest, len(rest))]
        if self._dropped:
            return [self._skipped(len(rest))]
        return [Frame(parse_messages(rest), len(rest))]

    def _frame_end(self, start: int) -> tuple[int, int] | None:
        """The next SSE frame end in the buffer, as (where it begins, where it ends), searching
        from where the last search stopped; None when there is none yet. A ``\n`` at the end
        whose meaning needs the next bytes is searched again after the next chunk."""
        buffer, size = self._buffer, len(self._buffer)
        while (newline := buffer.find(b"\n", self._scan_from)) != -1:
            after = newline + 1
            if after < size and buffer[after] == LF:
                end = after + 1
            elif after + 1 < size and buffer[after] == CR and buffer[after + 1] == LF:
                end = after + 2
            elif after == size or (after + 1 == size and buffer[after] == CR):
                self._scan_from = newline  # undecided until more bytes come
                return None
            else:
                self._scan_from = after
                continue
            self._scan_from = end
            begin = newline - 1 if newline > start and buffer[newline - 1] == CR else newline
            return begin, end
        self._scan_from = size
        return None

    def _keep(self, chunk: bytes) -> None:
        """A JSON body's chunk: kept until the body ends, or only counted once over the cap."""
        if self._dropped:
            self._dropped += len(chunk)
            return
        self._buffer += chunk
        if self._over_cap(len(self._buffer)):
            self._dropped = len(self._buffer)
            self._buffer.clear()

    def _frame(self, raw: bytes | bytearray, wire_bytes: int) -> Frame:
        """One SSE frame: its ``data:`` lines parsed, unless it (or its dropped head) is over
        the cap."""
        if self._dropped or self._over_cap(len(raw)):
            return self._skipped(wire_bytes)
        normalized = bytes(raw).replace(b"\r\n", b"\n")
        return Frame(_sse_messages(normalized), wire_bytes)

    def _skipped(self, wire_bytes: int) -> Frame:
        frame = Frame([], self._dropped + wire_bytes, parsed=False)
        self._dropped = 0
        self.unparsed += 1
        return frame

    def _over_cap(self, size: int) -> bool:
        return self.max_parse_bytes is not None and size > self.max_parse_bytes


def _sse_messages(frame: bytes) -> list[dict]:
    data = [line[5:].lstrip() for line in frame.split(b"\n") if line.startswith(b"data:")]
    return parse_messages(b"\n".join(data))
