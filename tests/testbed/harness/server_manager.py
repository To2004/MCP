"""Server lifecycle management for the MCP attack testbed."""

import json
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

STARTUP_TIMEOUT_SECONDS = 30


PROFILES_DIR = Path(__file__).parent.parent / "servers"


def load_profile(name: str) -> dict[str, Any]:
    """Load a server profile JSON by name.

    Args:
        name: The profile filename stem (without `.json` extension).

    Returns:
        Parsed profile dict.

    Raises:
        FileNotFoundError: If no matching profile file exists.
    """
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Server profile not found: {path}")
    return json.loads(path.read_text())


def install_server(profile: dict[str, Any]) -> None:
    """Run the server's install command if one is provided in the profile.

    Args:
        profile: Server profile dict, optionally containing an ``install`` key.
    """
    install_cmd = profile.get("install")
    if not install_cmd:
        return
    subprocess.run(install_cmd, shell=True, check=True)


@asynccontextmanager
async def stdio_session(profile: dict[str, Any]):
    """Start a stdio MCP server and yield an active ClientSession.

    Args:
        profile: Server profile dict containing a ``start_cmd`` list.

    Yields:
        An initialised :class:`mcp.ClientSession` connected to the server.
    """
    cmd = profile["start_cmd"]
    params = StdioServerParameters(command=cmd[0], args=cmd[1:])
    with anyio.fail_after(STARTUP_TIMEOUT_SECONDS):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


@asynccontextmanager
async def http_session(profile: dict[str, Any]):
    """Yield the profile dict for an HTTP MCP server.

    HTTP/DVMCP servers use raw JSON-RPC over HTTP rather than the stdio
    transport, so a ClientSession is not applicable here.  The attack runner
    detects ``isinstance(handle, dict)`` to know it should make direct HTTP
    calls instead of using the MCP SDK client.

    Args:
        profile: Server profile dict containing the HTTP base URL and other
            connection details.

    Yields:
        The profile dict unchanged so the runner can build requests directly.
    """
    yield profile


@asynccontextmanager
async def server_session(profile: dict[str, Any]):
    """Unified context manager: returns a ClientSession for stdio or the profile dict for HTTP.

    Dispatches to :func:`stdio_session` or :func:`http_session` based on the
    ``transport`` field in *profile* (default: ``"stdio"``).

    Args:
        profile: Server profile dict with an optional ``transport`` key.

    Yields:
        A :class:`mcp.ClientSession` for stdio servers, or the raw profile
        dict for HTTP servers.

    Raises:
        ValueError: If ``transport`` is not ``"stdio"`` or ``"http"``.
    """
    transport = profile.get("transport", "stdio")
    if transport == "stdio":
        async with stdio_session(profile) as session:
            yield session
    elif transport == "http":
        async with http_session(profile) as handle:
            yield handle
    else:
        raise ValueError(f"Unsupported transport: {transport}")
