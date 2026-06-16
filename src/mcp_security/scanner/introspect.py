"""Live, passive introspection of an MCP server via the official ``mcp`` SDK.

Opens a session (stdio subprocess or SSE/HTTP), initializes it, and lists the
declared tools/resources. Strictly passive: it never calls a tool here — that is
the enumerator's job, behind the read-only safety gate. Every connection is
bounded by a timeout so a hanging server cannot stall a scan; all failures are
captured as ``reachable=False`` rather than raised.

The async core (:func:`introspect`) is also what backs the long-stubbed live
path in ``atomic_ops.discovery`` via a connection-spec registry.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config_reader import ConnectionSpec

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20.0


@dataclass
class IntrospectResult:
    """Outcome of connecting to one server and listing what it declares."""

    spec: ConnectionSpec
    tools: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    reachable: bool = False
    error: str | None = None


def _resolve_env(env_keys: tuple[str, ...]) -> dict[str, str]:
    """Resolve env values from the real environment at call time (never logged)."""
    return {k: os.environ[k] for k in env_keys if k in os.environ}


@asynccontextmanager
async def _open_session(spec: ConnectionSpec):
    """Yield an initialized ClientSession for stdio or SSE transports."""
    if spec.transport == "stdio":
        if not spec.command:
            raise ValueError(f"stdio server {spec.name!r} has no command")
        params = StdioServerParameters(
            command=spec.command,
            args=list(spec.args),
            env={**os.environ, **_resolve_env(spec.env_keys)},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        # SSE / streamable-http. Imported lazily so stdio-only runs don't pay for it.
        from mcp.client.sse import sse_client

        if not spec.url:
            raise ValueError(f"{spec.transport} server {spec.name!r} has no url")
        async with sse_client(spec.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def _list_resources_safe(session: ClientSession) -> list[dict]:
    """list_resources, tolerating servers that don't implement the method."""
    try:
        result = await session.list_resources()
    except Exception as exc:  # noqa: BLE001 — many servers raise "Method not found"
        logger.debug("list_resources unavailable: %s", exc)
        return []
    return [
        {
            "uri": str(getattr(r, "uri", "")),
            "name": getattr(r, "name", "") or "",
            "mimeType": getattr(r, "mimeType", None),
        }
        for r in result.resources
    ]


async def introspect(spec: ConnectionSpec, timeout: float = DEFAULT_TIMEOUT) -> IntrospectResult:
    """Connect, initialize, and list tools + resources. Never raises."""

    async def _run() -> IntrospectResult:
        async with _open_session(spec) as session:
            tools_result = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "inputSchema": getattr(t, "inputSchema", {}) or {},
                }
                for t in tools_result.tools
            ]
            resources = await _list_resources_safe(session)
            return IntrospectResult(
                spec=spec, tools=tools, resources=resources, reachable=True
            )

    try:
        with anyio.fail_after(timeout):
            return await _run()
    except TimeoutError:
        return IntrospectResult(spec=spec, reachable=False, error=f"timeout after {timeout}s")
    except Exception as exc:  # noqa: BLE001 — surface any connect failure as a row, not a crash
        return IntrospectResult(spec=spec, reachable=False, error=f"{type(exc).__name__}: {exc}")


def introspect_sync(spec: ConnectionSpec, timeout: float = DEFAULT_TIMEOUT) -> IntrospectResult:
    """Blocking wrapper around :func:`introspect` for the CLI / sync callers."""
    return anyio.run(introspect, spec, timeout)
