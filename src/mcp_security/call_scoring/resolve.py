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
# Argument keys that carry a calendar identifier.
_CALENDAR_KEYS = ("calendar", "calendar_id", "calendar_name", "cal")
# Argument keys that carry a repository identifier.
_REPO_KEYS = ("repo", "repository", "repo_name", "name", "full_name")

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
    # Per-file (take2) scans key assets by relative path; by-extension (take1)
    # scans key by ".ext". Detect which the scan used and match accordingly so
    # the ranker scores against ALL files, not just file types, when available.
    if any("/" in key for key in table.asset_sensitivity):
        return _resolve_filesystem_by_path(call, path, table)
    ext = _extension(path)
    if ext in table.asset_sensitivity:
        return ResolvedAsset(ext, table.asset_sensitivity[ext], f"path extension {ext}", True)
    return _unresolved(f"extension {ext} not in table")


# A directory-scope asset id ends with "/" (or is the bare root "/").
_ROOT_DIR_ID = "/"


def _segments(value: str) -> list[str]:
    """Lowercased, separator-normalised path segments (drops empties + slashes)."""
    return [s for s in value.replace("\\", "/").lower().strip("/").split("/") if s]


def _is_dir_asset(asset: str) -> bool:
    return asset.endswith("/") or asset == _ROOT_DIR_ID


def _best_suffix_match(target: list[str], assets: list[str]) -> str | None:
    """Longest asset whose segments are a trailing suffix of ``target`` segments."""
    best: tuple[str, int] | None = None
    for asset in assets:
        aseg = _segments(asset)
        if aseg and len(aseg) <= len(target) and target[-len(aseg):] == aseg:
            if best is None or len(aseg) > best[1]:
                best = (asset, len(aseg))
    return best[0] if best else None


def _resolve_filesystem_by_path(call: Call, path: str, table: StaticTable) -> ResolvedAsset:
    """Match a call's path to a scanned asset by segment-aligned suffix.

    Call paths are absolute (often Windows) and rooted differently than the scan
    (``...\\corp_filesystem_sim\\sensitive\\x.csv`` vs the scanned relative
    ``sensitive/x.csv``), so we match on the trailing path segments, longest first.
    Resolution order, never guessing beyond what was scanned:

    1. the exact **file** asset, when the path names a scanned file;
    2. the **directory-scope** asset, when the path names a scanned folder
       (an enumeration/fan-out target — list, tree, search, folder op);
    3. the nearest **ancestor directory scope**, when the path is a file the scan
       did not enumerate but which sits inside a scanned folder (scope fallback);
    4. the **store-root scope**, as a last resort, when the path is the store root.
    """
    segs = _segments(path)
    files = [a for a in table.asset_sensitivity if not _is_dir_asset(a)]
    dirs = [a for a in table.asset_sensitivity if _is_dir_asset(a)]

    file_hit = _best_suffix_match(segs, files)
    if file_hit is not None:
        return ResolvedAsset(file_hit, table.asset_sensitivity[file_hit], f"file {file_hit}", True)

    dir_hit = _best_suffix_match(segs, [d for d in dirs if d != _ROOT_DIR_ID])
    if dir_hit is not None:
        return ResolvedAsset(
            dir_hit, table.asset_sensitivity[dir_hit], f"directory scope {dir_hit}", True
        )

    # Scope fallback: walk up the path's ancestors to the nearest scanned folder.
    for k in range(len(segs) - 1, 0, -1):
        anc = _best_suffix_match(segs[:k], [d for d in dirs if d != _ROOT_DIR_ID])
        if anc is not None:
            leaf = segs[-1] if segs else path
            return ResolvedAsset(
                anc, table.asset_sensitivity[anc], f"scope {anc} (ancestor of {leaf})", True
            )

    if _ROOT_DIR_ID in table.asset_sensitivity:
        return ResolvedAsset(
            _ROOT_DIR_ID, table.asset_sensitivity[_ROOT_DIR_ID], "store-root scope", True
        )
    return _unresolved("path not among scanned files or folders")


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


# Calendar tools that target a specific scope regardless of a calendar argument.
_CALENDAR_TOOL_SCOPE = {"access_contacts": "contacts"}
# When a calendar op names no calendar, it acts on the agent's own schedule.
_CALENDAR_DEFAULT = "personal"


def _resolve_calendar(call: Call, table: StaticTable) -> ResolvedAsset:
    """Resolve a calendar call to its target calendar scope.

    Some tools pin a scope (``access_contacts`` always reads the directory). Others
    name a calendar argument; a calendar op that names none acts on the agent's own
    ``personal`` calendar (the sensible default), so it is still scorable.
    """
    pinned = _CALENDAR_TOOL_SCOPE.get(call.tool)
    if pinned and pinned in table.asset_sensitivity:
        return ResolvedAsset(pinned, table.asset_sensitivity[pinned], f"calendar {pinned}", True)
    cal = _first_arg(call.args, _CALENDAR_KEYS)
    if cal is None and _CALENDAR_DEFAULT in table.asset_sensitivity:
        cal = _CALENDAR_DEFAULT
        basis = f"calendar {cal} (default scope)"
    else:
        basis = f"calendar {cal}"
    if cal and cal in table.asset_sensitivity:
        return ResolvedAsset(cal, table.asset_sensitivity[cal], basis, True)
    if cal:
        return _unresolved(f"calendar {cal} not in table")
    return _unresolved("no calendar argument")


def _resolve_github(call: Call, table: StaticTable) -> ResolvedAsset:
    """Resolve a GitHub call to its target repository scope (by repo argument)."""
    repo = _first_arg(call.args, _REPO_KEYS)
    if repo:
        # Owner-qualified names ("org/backend-api") reduce to the repo segment.
        repo = repo.split("/")[-1]
    if repo and repo in table.asset_sensitivity:
        return ResolvedAsset(repo, table.asset_sensitivity[repo], f"repo {repo}", True)
    if repo:
        return _unresolved(f"repo {repo} not in table")
    return _unresolved("no repository argument")


def resolve_asset(call: Call, table: StaticTable) -> ResolvedAsset:
    """Resolve the asset class a call targets within its server's static table.

    Dispatch prefers the authoritative ``server_kind`` recorded by the scanner;
    only older scans without it fall back to substring-matching the LLM-inferred
    ``mcp_kind`` (which can be free text like "team messaging workspace").
    """
    if table.server_kind:
        kind = table.server_kind.lower()
        dispatch = {
            "filesystem": _resolve_filesystem, "sqlite": _resolve_sql,
            "slack": _resolve_channel, "calendar": _resolve_calendar,
            "github": _resolve_github,
        }
        if kind in dispatch:
            return dispatch[kind](call, table)

    kind = table.mcp_kind.lower()
    if "filesystem" in kind:
        return _resolve_filesystem(call, table)
    if "sql" in kind or "database" in kind:
        return _resolve_sql(call, table)
    if "communication" in kind or "slack" in kind or "messaging" in kind:
        return _resolve_channel(call, table)
    if "calendar" in kind or "schedul" in kind:
        return _resolve_calendar(call, table)
    if "github" in kind or "repositor" in kind or "version control" in kind:
        return _resolve_github(call, table)
    return _unresolved(f"no resolver for kind {table.mcp_kind!r}")
