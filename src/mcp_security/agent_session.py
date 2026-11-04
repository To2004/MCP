"""Open one agent's MCP session over Streamable HTTP, in either protocol era (mcp SDK 2.x).

The gateway scripts (``scripts/gateway_demo_agent.py``, ``scripts/gateway_replay_corpus.py``)
connect the way an agent would, and ``--protocol`` picks how each connection starts:

- ``legacy`` (the default): the ``initialize`` handshake, at protocol 2025-11-25. The server
  opens a session and the client names it (``Mcp-Session-Id``) on every later request. The 1.x
  SDK connected only this way, so runs made before the 2.x port reproduce.
- ``modern``: the stateless 2026-07-28 protocol. One ``server/discover`` and no session; every
  request carries its own protocol version, client info and capabilities. A server that does
  not speak 2026-07-28 fails the connection instead of falling back to ``initialize``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

LEGACY = "legacy"
MODERN = "modern"
#: The values ``--protocol`` takes, the default first.
PROTOCOLS = (LEGACY, MODERN)
PROTOCOL_HELP = (
    "legacy: the initialize handshake (2025-11-25), as before the mcp 2.x port; "
    "modern: 2026-07-28 (server/discover, no session)"
)
#: The 1.x SDK's streamable-HTTP timeouts, which 2.x leaves to the caller's httpx2 client: 30 s
#: to connect, write or get a pooled connection; 300 s to read, as a server may hold a stream open.
TIMEOUT_S = 30.0
READ_TIMEOUT_S = 300.0


def agent_http_client(
    headers: Mapping[str, str] | None = None,
    transport: httpx2.AsyncBaseTransport | None = None,
) -> httpx2.AsyncClient:
    """The HTTP client one agent connects with: ``headers`` on every request, 1.x timeouts.

    Args:
        headers: Sent on every request of the session (e.g. ``Authorization``).
        transport: Replaces the network; tests pass an in-process ASGI app.
    """
    return httpx2.AsyncClient(
        headers=dict(headers or {}),
        timeout=httpx2.Timeout(TIMEOUT_S, read=READ_TIMEOUT_S),
        transport=transport,
    )


@asynccontextmanager
async def agent_session(
    url: str,
    *,
    protocol: str,
    headers: Mapping[str, str] | None = None,
    transport: httpx2.AsyncBaseTransport | None = None,
) -> AsyncIterator[ClientSession]:
    """An MCP session to ``url``, started with ``initialize`` (legacy) or ``server/discover``.

    Args:
        url: The server's (or the gateway route's) Streamable HTTP endpoint.
        protocol: ``legacy`` or ``modern``; see the module docstring.
        headers: Sent on every request of the session.
        transport: Replaces the network; tests pass an in-process ASGI app.

    Yields:
        The started session; its ``protocol_version`` is the version negotiated.

    Raises:
        ValueError: ``protocol`` is not one of ``PROTOCOLS`` (checked before connecting).
        mcp.MCPError: The server refused the handshake or the discovery.
    """
    if protocol not in PROTOCOLS:
        raise ValueError(f"protocol must be one of {PROTOCOLS}, got {protocol!r}")
    async with (
        agent_http_client(headers, transport) as http_client,
        streamable_http_client(url, http_client=http_client) as (read, write),
        ClientSession(read, write) as session,
    ):
        if protocol == MODERN:
            await session.discover()
        else:
            await session.initialize()
        yield session
