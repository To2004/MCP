"""Resolve a call's arguments to the asset class its target server table uses.

Each static table keys its assets differently by kind:

* filesystem — file extensions (``.pem``, ``.csv``) plus ``(no extension)``;
* SQL database — table names (``employees``, ``api_keys``);
* communication platform — channel names.

Resolution is best-effort: when the argument names a concrete asset that the
table knows, the call scores against that exact cell; otherwise it is marked
unresolved and the scorer falls back to a worst-case estimate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath

from .loader import Call
from .tables import StaticTable

# Argument keys that carry a filesystem path, in priority order.
_PATH_KEYS = ("path", "paths", "source", "destination", "file", "uri")
# Argument keys that carry a SQL statement or a bare table name.
_QUERY_KEYS = ("query", "sql", "statement")
_TABLE_KEYS = ("table_name", "table")
# Argument keys that carry a channel/conversation identifier.
_CHANNEL_KEYS = ("channel", "channel_id", "channel_name", "conversation")

_SQL_TABLE_RE = re.compile(r"\b(?:from|into|update|table)\s+[\"'`\[]?(\w+)", re.IGNORECASE)


@dataclass(frozen=True)
class ResolvedAsset:
    """The asset a call targets, plus how it was determined."""

    asset: str | None
    sensitivity: int | None
    basis: str
    resolved: bool


def _first_arg(args: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in args and args[key]:
            value = args[key]
            if isinstance(value, list):
                value = value[0] if value else None
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _extension(path: str) -> str:
    """Return a lowercased ``.ext`` for a path, or ``(no extension)``."""
    name = PureWindowsPath(path).name if "\\" in path else PurePosixPath(path).name
    suffix = PurePosixPath(name).suffix.lower()
    return suffix if suffix else "(no extension)"


def _unresolved(basis: str) -> ResolvedAsset:
    return ResolvedAsset(asset=None, sensitivity=None, basis=basis, resolved=False)


def _resolve_filesystem(call: Call, table: StaticTable) -> ResolvedAsset:
    path = _first_arg(call.args, _PATH_KEYS)
    if path is None:
        return _unresolved("no path argument")
    ext = _extension(path)
    if ext in table.asset_sensitivity:
        return ResolvedAsset(ext, table.asset_sensitivity[ext], f"path extension {ext}", True)
    return _unresolved(f"extension {ext} not in table")


def _resolve_sql(call: Call, table: StaticTable) -> ResolvedAsset:
    name = _first_arg(call.args, _TABLE_KEYS)
    if name is None:
        query = _first_arg(call.args, _QUERY_KEYS)
        if query:
            match = _SQL_TABLE_RE.search(query)
            name = match.group(1) if match else None
    if name and name in table.asset_sensitivity:
        return ResolvedAsset(name, table.asset_sensitivity[name], f"table {name}", True)
    if name:
        return _unresolved(f"table {name} not in table")
    return _unresolved("no table/query argument")


def _resolve_channel(call: Call, table: StaticTable) -> ResolvedAsset:
    channel = _first_arg(call.args, _CHANNEL_KEYS)
    if channel and channel in table.asset_sensitivity:
        return ResolvedAsset(channel, table.asset_sensitivity[channel], f"channel {channel}", True)
    if channel:
        return _unresolved(f"channel {channel} not in table")
    return _unresolved("no channel argument")


def resolve_asset(call: Call, table: StaticTable) -> ResolvedAsset:
    """Resolve the asset class a call targets within its server's static table."""
    kind = table.mcp_kind.lower()
    if "filesystem" in kind:
        return _resolve_filesystem(call, table)
    if "sql" in kind or "database" in kind:
        return _resolve_sql(call, table)
    if "communication" in kind or "slack" in kind:
        return _resolve_channel(call, table)
    return _unresolved(f"no resolver for kind {table.mcp_kind!r}")
