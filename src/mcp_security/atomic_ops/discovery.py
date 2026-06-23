"""Discover an MCP server's tool list — live via subprocess when possible,
falling back to a cached JSON, then to README-only mode.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Literal

from .server_catalog import ServerEntry

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """What discovery returned for one server."""

    server: ServerEntry
    tools: list[dict] = field(default_factory=list)
    source: Literal["live", "cached", "readme_only"] = "readme_only"
    error: str | None = None

    @property
    def readme_only(self) -> bool:
        return self.source == "readme_only"


def discover_server(
    server: ServerEntry, prefer_live: bool = False
) -> DiscoveryResult:
    """Return the server's tools using the best available source.

    Order of preference (when prefer_live is True):
      1. Live introspection via MCP subprocess
      2. Cached JSON at server.tool_list_path
      3. README-only mode (empty tools list)

    When prefer_live is False (default), live introspection is skipped entirely
    — useful for deterministic test runs and CI.
    """
    if prefer_live:
        live = _try_live_introspect(server)
        if live is not None:
            return DiscoveryResult(server=server, tools=live, source="live")

    cached = _load_cached(server)
    if cached:
        return DiscoveryResult(server=server, tools=cached, source="cached")

    return DiscoveryResult(server=server, tools=[], source="readme_only")


def _load_cached(server: ServerEntry) -> list[dict]:
    if server.tool_list_path and server.tool_list_path.exists():
        try:
            with server.tool_list_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "failed to load cached tool list for %s: %s", server.name, exc
            )
    return []


# Optional registry mapping a server name to a live connection spec. Empty by
# default, so plain ServerEntry classification (and all existing tests) keep the
# README/cached behaviour. The scanner populates this to opt a server into real
# live introspection. See mcp_security.scanner.introspect.
_LIVE_REGISTRY: dict[str, object] = {}


def register_connection(server_name: str, spec: object) -> None:
    """Opt a server into live introspection by associating a ConnectionSpec."""
    _LIVE_REGISTRY[server_name] = spec


def _try_live_introspect(server: ServerEntry) -> list[dict] | None:
    """Attempt to connect to the server live and return its tools/list.

    Only servers registered via :func:`register_connection` are attempted; for
    everyone else this returns None and the caller falls back to cached/README
    sources. Best-effort — any connection failure also returns None.
    """
    spec = _LIVE_REGISTRY.get(server.name)
    if spec is None:
        logger.debug("no live connection registered for %s", server.name)
        return None
    try:
        from mcp_security.scanner.introspect import introspect_sync

        result = introspect_sync(spec)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — live path is strictly best-effort
        logger.info("live introspection failed for %s: %s", server.name, exc)
        return None
    if not result.reachable:
        logger.info("live introspection unreachable for %s: %s", server.name, result.error)
        return None
    return result.tools
