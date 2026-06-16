"""Discover connected MCP servers from Claude Code config.

Claude Code stores MCP server definitions in ``~/.claude.json`` — both a
top-level ``mcpServers`` map and a per-project one under
``projects[<path>].mcpServers``. (Project scope can also live in a project's
``.mcp.json``.) Note that ``~/.claude/settings.json`` does **not** hold
mcpServers — that is permissions/config only.

Each definition is parsed into a :class:`ConnectionSpec`: a transport-agnostic
connection record plus, for filesystem-like servers, the asset roots to walk.
Secrets are never retained: only env-var *key names* are kept, never values.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ServerKind = Literal["filesystem", "sqlite", "slack", "github", "other"]
Transport = Literal["stdio", "sse", "http"]

# Substrings that identify a server kind from its package/command/args.
_KIND_MARKERS: tuple[tuple[ServerKind, tuple[str, ...]], ...] = (
    ("filesystem", ("server-filesystem", "mcp-filesystem", "mcp-server-filesystem")),
    ("sqlite", ("server-sqlite", "mcp-server-sqlite", "mcp-sqlite")),
    ("slack", ("server-slack", "mcp-server-slack", "mcp-slack")),
    ("github", ("github-mcp-server", "server-github", "mcp-server-github")),
)


@dataclass(frozen=True)
class ConnectionSpec:
    """A single connectable MCP server and its asset store, secrets redacted."""

    name: str
    kind: ServerKind
    transport: Transport
    command: str | None = None
    args: tuple[str, ...] = ()
    roots: tuple[str, ...] = ()  # filesystem roots or sqlite db path(s)
    env_keys: tuple[str, ...] = ()  # names only — values are never retained
    url: str | None = None
    scope: str = "global"  # "global" or the project path it was found under


def default_claude_json() -> Path:
    """Path to the user's Claude Code config."""
    return Path.home() / ".claude.json"


def infer_kind(package: str, args: tuple[str, ...]) -> ServerKind:
    """Classify a server kind from its package name and launch args."""
    haystack = " ".join((package, *args)).lower()
    for kind, markers in _KIND_MARKERS:
        if any(marker in haystack for marker in markers):
            return kind
    return "other"


def _extract_fs_roots(args: tuple[str, ...]) -> tuple[str, ...]:
    """Pull filesystem roots from server-filesystem launch args.

    Roots are the trailing positional path arguments — anything that looks like
    a path (absolute, ``~``-relative, or an existing relative dir) and is not an
    npx/uvx flag or the package token itself.
    """
    roots: list[str] = []
    for arg in args:
        if arg.startswith("-"):
            continue
        if "server-filesystem" in arg or arg in {"npx", "uvx", "-y"}:
            continue
        if arg.startswith(("/", "~", "./", "../")) or Path(arg).expanduser().is_dir():
            roots.append(arg)
    return tuple(roots)


def _extract_sqlite_db(args: tuple[str, ...]) -> tuple[str, ...]:
    """Pull the sqlite db path from ``--db-path <path>`` style args."""
    roots: list[str] = []
    for i, arg in enumerate(args):
        if arg in {"--db-path", "--db", "--database"} and i + 1 < len(args):
            roots.append(args[i + 1])
        elif arg.endswith((".db", ".sqlite", ".sqlite3")):
            roots.append(arg)
    return tuple(roots)


def _parse_entry(name: str, raw: dict, scope: str) -> ConnectionSpec | None:
    """Convert one mcpServers entry into a ConnectionSpec, or None if unusable."""
    if not isinstance(raw, dict):
        logger.warning("skipping malformed mcpServers entry %r in %s", name, scope)
        return None

    command = raw.get("command")
    args = tuple(str(a) for a in raw.get("args", []) or [])
    url = raw.get("url")
    env_keys = tuple((raw.get("env") or {}).keys())

    # Transport: explicit type wins, else url => sse/http, else stdio.
    declared = (raw.get("type") or raw.get("transport") or "").lower()
    if declared in {"sse", "http", "streamable-http", "https"}:
        transport: Transport = "http" if "http" in declared else "sse"
    elif url:
        transport = "sse"
    else:
        transport = "stdio"

    package = command or url or name
    kind = infer_kind(package, args)

    roots: tuple[str, ...] = ()
    if kind == "filesystem":
        roots = _extract_fs_roots(args)
    elif kind == "sqlite":
        roots = _extract_sqlite_db(args)

    return ConnectionSpec(
        name=name,
        kind=kind,
        transport=transport,
        command=command,
        args=args,
        roots=roots,
        env_keys=env_keys,
        url=url,
        scope=scope,
    )


def _parse_servers_map(servers: dict, scope: str) -> list[ConnectionSpec]:
    specs: list[ConnectionSpec] = []
    for name, raw in (servers or {}).items():
        spec = _parse_entry(name, raw, scope)
        if spec is not None:
            specs.append(spec)
    return specs


def read_configured_servers(
    claude_json: Path | None = None,
    project_mcp_json: Path | None = None,
) -> list[ConnectionSpec]:
    """Read all configured MCP servers (global + every project), deduplicated.

    Args:
        claude_json: override for ``~/.claude.json`` (mainly for tests).
        project_mcp_json: optional project-scope ``.mcp.json`` to merge in.

    Returns specs in a stable order; later duplicates (same name+scope) are
    dropped. Missing/unreadable files yield an empty contribution, not an error.
    """
    claude_json = claude_json or default_claude_json()
    specs: list[ConnectionSpec] = []

    data = _load_json(claude_json)
    if data:
        specs += _parse_servers_map(data.get("mcpServers", {}), "global")
        for proj_path, proj in (data.get("projects") or {}).items():
            if isinstance(proj, dict):
                specs += _parse_servers_map(proj.get("mcpServers", {}), proj_path)

    if project_mcp_json:
        proj_data = _load_json(project_mcp_json)
        if proj_data:
            specs += _parse_servers_map(
                proj_data.get("mcpServers", {}), str(project_mcp_json)
            )

    return _dedupe(specs)


def _dedupe(specs: list[ConnectionSpec]) -> list[ConnectionSpec]:
    seen: set[tuple[str, str]] = set()
    out: list[ConnectionSpec] = []
    for spec in specs:
        key = (spec.name, spec.scope)
        if key in seen:
            continue
        seen.add(key)
        out.append(spec)
    return out


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("failed to read %s: %s", path, exc)
        return None


def spec_from_root(root: str, kind: ServerKind = "filesystem") -> ConnectionSpec:
    """Synthesize a local spec for a --root override (no config needed)."""
    return ConnectionSpec(
        name=f"{kind}:{Path(root).name or root}",
        kind=kind,
        transport="stdio",
        roots=(root,),
        scope="cli",
    )
