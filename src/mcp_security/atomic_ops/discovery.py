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


def _try_live_introspect(server: ServerEntry) -> list[dict] | None:
    """Attempt to spawn the server via subprocess and call tools/list.

    Returns None on any failure; logs the reason. This is intentionally
    best-effort — many servers need credentials, runtime envs (Node, Docker),
    or network access that may not be available.

    Implementation note: this is a skeleton. Implementing it for every
    npx/uvx package without credentials is out of scope for the first pass;
    cached JSONs in data/tool_lists/ serve as the practical source.
    """
    logger.info("live introspection skipped (skeleton) for %s", server.name)
    return None
