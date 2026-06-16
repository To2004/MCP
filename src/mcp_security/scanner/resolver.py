"""Discover assets for servers that can't be enumerated locally.

When a server is unreachable or remote (no local store to walk), fall back to:

1. **Web** — look the package up (GitHub/npm) and have the local LLM extract the
   asset types it manages from the fetched README. ``source="web"``.
2. **Theorise** — if the web turns up nothing, the local LLM theorises the likely
   asset types from the server's name/kind. ``source="theorised"`` (low confidence).

This module only *discovers* asset names; risk ranking stays entirely in
:mod:`ranker`, so web/theorised assets are scored by the same code path as
enumerated ones. Web fetching is delegated to a caller-supplied ``fetcher`` so
this module stays dependency-light and testable. Every failure degrades to an
empty/theorised inventory — never raises.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from mcp_security.llm.ollama_client import query_ollama

from .config_reader import ConnectionSpec
from .enumerator import AssetGroup, AssetInventory

logger = logging.getLogger(__name__)

# A fetcher takes a package identifier and returns doc text (or None if it can't).
Fetcher = Callable[[str], str | None]


def _identifier(spec: ConnectionSpec) -> str:
    """A searchable identifier for the server's package."""
    if spec.args:
        pkgish = [a for a in spec.args if "/" in a or a.startswith("mcp")]
        if pkgish:
            return pkgish[0]
    return spec.url or spec.command or spec.name


def _extract_prompt(identifier: str, kind: str, doc: str) -> str:
    return (
        f"This is documentation for the MCP server '{identifier}' (kind: {kind}).\n"
        "List the asset TYPES it exposes to an agent — the data units an agent "
        "could read (e.g. file-types, tables, channels, repositories). Reply with "
        "JSON only, no prose, no risk scoring.\n"
        f"Docs (truncated):\n{doc[:6000]}\n"
        'Return: {"assets":["<name>", "<name>"]}'
    )


def _theorise_prompt(identifier: str, kind: str) -> str:
    return (
        f"No docs were found for the MCP server '{identifier}' (kind: {kind}).\n"
        "From the name and kind alone, THEORISE the asset types it most likely "
        "exposes to an agent. Reply JSON only, no prose, no risk scoring.\n"
        'Return: {"assets":["<name>", "<name>"]}'
    )


def _assets_to_groups(response: dict | None) -> list[AssetGroup]:
    if not response:
        return []
    names = response.get("assets", [])
    if not isinstance(names, list):
        return []
    return [AssetGroup(name=str(n)) for n in names if n]


def resolve_via_web(spec: ConnectionSpec, fetcher: Fetcher) -> AssetInventory:
    """Fetch the package's docs and LLM-extract its asset types. ``source=web``."""
    identifier = _identifier(spec)
    try:
        doc = fetcher(identifier)
    except Exception as exc:  # noqa: BLE001 — network is best-effort
        logger.debug("web fetch failed for %s: %s", identifier, exc)
        doc = None

    if not doc:
        return AssetInventory(server=spec.name, kind=spec.kind, source="web", note="no docs found")

    response = query_ollama(_extract_prompt(identifier, spec.kind, doc))
    inv = AssetInventory(
        server=spec.name, kind=spec.kind, source="web", note=f"from {identifier} docs"
    )
    inv.assets = _assets_to_groups(response)
    return inv


def theorise(spec: ConnectionSpec) -> AssetInventory:
    """LLM-theorise likely asset types from the name/kind. ``source=theorised``."""
    identifier = _identifier(spec)
    response = query_ollama(_theorise_prompt(identifier, spec.kind))
    inv = AssetInventory(
        server=spec.name, kind=spec.kind, source="theorised", note="theorised from name/kind"
    )
    inv.assets = _assets_to_groups(response)
    return inv


def resolve(spec: ConnectionSpec, fetcher: Fetcher | None = None) -> AssetInventory:
    """Web first (if a fetcher is given), then theorise. Always returns an inventory."""
    if fetcher is not None:
        web = resolve_via_web(spec, fetcher)
        if not web.is_empty:
            return web
    return theorise(spec)
