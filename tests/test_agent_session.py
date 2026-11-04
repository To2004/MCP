"""Tests for mcp_security.agent_session: one agent's MCP session, legacy or modern protocol.

Each test serves a real mcp 2.x server in-process (an ``MCPServer`` behind httpx2's ASGI
transport), so the handshake, the headers and the tool call cross the real Streamable HTTP
client and server; only the network is replaced.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
import pytest
from mcp.server.mcpserver import MCPServer

from mcp_security.agent_session import LEGACY, MODERN, agent_session

#: The server's DNS-rebinding guard admits 127.0.0.1 hosts; the port is never dialled.
URL = "http://127.0.0.1:8000/mcp"
HEADERS = {"Authorization": "Bearer agent-token", "X-Agent-Id": "alice"}


def _echo_server() -> MCPServer:
    server = MCPServer("agent-session-test")

    @server.tool()
    def echo(text: str) -> str:
        """Return the text."""
        return text

    return server


@asynccontextmanager
async def _serving() -> AsyncIterator[tuple[httpx2.ASGITransport, list[dict[str, str]]]]:
    """A running echo server as an httpx2 transport, and the headers of each request it got."""
    server = _echo_server()
    app = server.streamable_http_app()
    seen: list[dict[str, str]] = []

    async def recording_app(scope, receive, send) -> None:
        if scope["type"] == "http":
            seen.append({key.decode(): value.decode() for key, value in scope["headers"]})
        await app(scope, receive, send)

    async with server.session_manager.run():
        yield httpx2.ASGITransport(app=recording_app), seen


async def test_legacy_starts_with_initialize_and_opens_a_session() -> None:
    async with _serving() as (transport, seen):
        async with agent_session(
            URL, protocol=LEGACY, headers=HEADERS, transport=transport
        ) as session:
            result = await session.call_tool("echo", {"text": "hi"})
            assert session.protocol_version == "2025-11-25"
            assert session.initialize_result is not None
            assert session.discover_result is None

    assert [block.text for block in result.content] == ["hi"]
    assert not result.is_error
    assert any("mcp-session-id" in headers for headers in seen)  # the server opened one


async def test_modern_starts_with_discover_and_no_session() -> None:
    async with _serving() as (transport, seen):
        async with agent_session(
            URL, protocol=MODERN, headers=HEADERS, transport=transport
        ) as session:
            result = await session.call_tool("echo", {"text": "hi"})
            assert session.protocol_version == "2026-07-28"
            assert session.discover_result is not None
            assert session.initialize_result is None

    assert [block.text for block in result.content] == ["hi"]
    assert seen[0]["mcp-method"] == "server/discover"
    assert not any("mcp-session-id" in headers for headers in seen)


@pytest.mark.parametrize("protocol", [LEGACY, MODERN])
async def test_headers_ride_on_every_request(protocol: str) -> None:
    async with _serving() as (transport, seen):
        async with agent_session(URL, protocol=protocol, headers=HEADERS, transport=transport):
            pass

    assert seen
    for headers in seen:
        assert headers["authorization"] == HEADERS["Authorization"]
        assert headers["x-agent-id"] == HEADERS["X-Agent-Id"]


async def test_unknown_protocol_fails_before_connecting() -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(500)

    with pytest.raises(ValueError, match="protocol must be one of"):
        async with agent_session(
            URL, protocol="2026-07-28", transport=httpx2.MockTransport(handler)
        ):
            pass
    assert requests == []
