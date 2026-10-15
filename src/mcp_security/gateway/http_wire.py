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
"""

from __future__ import annotations

import base64
import binascii
import ipaddress
import json
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network

Network = IPv4Network | IPv6Network
SENTINEL_PREFIX, SENTINEL_SUFFIX = "=?base64?", "?="


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


class MessageTap:
    """Reads JSON-RPC messages out of a response body fed chunk by chunk.

    SSE frames are emitted as soon as each one is complete, so a long-lived stream is logged
    while it is open; a plain JSON body is parsed once it ends.
    """

    def __init__(self, content_type: str) -> None:
        self._sse = content_type.startswith("text/event-stream")
        self._buffer = b""

    def feed(self, chunk: bytes) -> list[dict]:
        self._buffer += chunk
        if not self._sse:
            return []
        self._buffer = self._buffer.replace(b"\r\n", b"\n")
        *frames, self._buffer = self._buffer.split(b"\n\n")
        return [message for frame in frames for message in _sse_messages(frame)]

    def close(self) -> list[dict]:
        rest, self._buffer = self._buffer, b""
        return _sse_messages(rest) if self._sse else parse_messages(rest)


def _sse_messages(frame: bytes) -> list[dict]:
    data = [line[5:].lstrip() for line in frame.split(b"\n") if line.startswith(b"data:")]
    return parse_messages(b"\n".join(data))
