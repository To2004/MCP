"""Static (design-time) misuse-scoring for MCP servers.

Builds a per-server risk table from the server's tool registry and asset
classes alone — before any request is seen — using an LLM pipeline anchored to
an inferred domain profile, with a deterministic offline fallback.

See :mod:`mcp_security.static_scoring.pipeline` for the entry point
:func:`build_static_table`.
"""

from __future__ import annotations

from .pipeline import BAND_THRESHOLDS, FORMULA, StaticScorer, band_label, build_static_table
from .registry import (
    DEMO_SERVERS,
    LOADERS,
    AssetSpec,
    ServerRegistry,
    ToolSpec,
    load_filesystem_registry,
    load_registry_from_json,
    load_sqlite_registry,
)

__all__ = [
    "BAND_THRESHOLDS",
    "FORMULA",
    "StaticScorer",
    "band_label",
    "build_static_table",
    "DEMO_SERVERS",
    "LOADERS",
    "AssetSpec",
    "ServerRegistry",
    "ToolSpec",
    "load_filesystem_registry",
    "load_registry_from_json",
    "load_sqlite_registry",
]
