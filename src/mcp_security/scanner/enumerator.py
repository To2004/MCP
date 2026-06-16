"""Enumerate the assets each connected MCP server can reach (read-only).

The enumeration is **generic by default**: every MCP server, whatever its kind,
exposes what it can reach through the protocol itself — ``list_resources`` plus
whatever read-only enumeration tools it declares. :func:`_generic_live_enumerate`
uses only those, so an unknown server kind is still meaningfully scanned without
any per-kind code.

On top of that, *local stores* get fast-path optimizations: a filesystem root is
walked with ``os.walk`` and a sqlite db is read with ``sqlite3`` — robust, no
subprocess, and exactly the data the server is configured to reach. These are
registered in :data:`LOCAL_ENUMERATORS` and tried first when a local target
exists; everything else (and any empty local result) falls through to the generic
protocol path, and an empty result there falls through to the web/theorise
resolver.

Every tool invocation is routed through the read-only :mod:`safety` gate.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import anyio

from mcp_security.sensitivity import BAND, DB_COLUMN_ANCHOR, FILETYPE_SENSITIVITY

from .config_reader import ConnectionSpec
from .introspect import _open_session
from .safety import is_read_only

logger = logging.getLogger(__name__)

DEFAULT_MAX_FILES = 20_000
DEFAULT_MAX_DEPTH = 25
_LIVE_TIMEOUT = 30.0

AssetSource = Literal["enumerated", "web", "theorised"]


@dataclass
class AssetGroup:
    """One row-to-be: a file-type, table, channel, resource, or any asset unit."""

    name: str
    count: int = 1
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()


@dataclass
class AssetInventory:
    """All assets enumerated for one server."""

    server: str
    kind: str
    assets: list[AssetGroup] = field(default_factory=list)
    source: AssetSource = "enumerated"
    note: str = ""
    context: str = ""  # server self-description (tool/resource descriptions) for the ranker

    @property
    def is_empty(self) -> bool:
        return not self.assets


# ===========================================================================
# Local fast-path enumerators (optimizations for local stores)
# ===========================================================================
def _most_sensitive_ext(filenames: list[str]) -> str | None:
    """Return the extension of the most sensitive file directly in a directory.

    Used to rank a directory by what it holds, reusing the shared filetype
    taxonomy — so a folder with a ``.sql``/``.pem`` inherits that sensitivity
    without any directory-specific anchor table.
    """
    best_ext, best_band = None, 0
    for fname in filenames:
        ext = Path(fname).suffix.lstrip(".").lower()
        band = BAND.get(FILETYPE_SENSITIVITY.get(ext, ""), 0)
        if band > best_band:
            best_ext, best_band = ext, band
    return best_ext


def _enumerate_filesystem(
    spec: ConnectionSpec,
    *,
    by_file: bool = False,
    max_files: int = DEFAULT_MAX_FILES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> AssetInventory:
    """Inventory the configured root(s) read-only: directories + files.

    Directories are always emitted as assets (so the scan reflects the layout),
    each tagged with the most sensitive file-type it directly contains so the
    shared taxonomy ranks it. Files are aggregated by extension by default, or
    listed individually when ``by_file`` is set.
    """
    inv = AssetInventory(server=spec.name, kind="filesystem")
    if not spec.roots:
        return inv  # no local root → caller tries the generic path

    counts: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    file_rows: list[AssetGroup] = []
    dir_info: dict[str, dict] = {}  # abs dirpath -> {label, count, ext, band, examples}
    seen = 0

    for root in spec.roots:
        base = Path(root).expanduser()
        if not base.is_dir():
            logger.debug("filesystem root %s is not a readable directory", base)
            continue
        base_depth = len(base.parts)
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            if len(Path(dirpath).parts) - base_depth >= max_depth:
                dirnames[:] = []
                continue
            rel = os.path.relpath(dirpath, base)
            label = base.name if rel == "." else os.path.join(base.name, rel)
            top_ext = _most_sensitive_ext(filenames)
            dir_info[dirpath] = {
                "label": label,
                "count": len(filenames),
                "ext": top_ext,
                "band": BAND.get(FILETYPE_SENSITIVITY.get(top_ext or "", ""), 0),
                "examples": tuple(sorted(dirnames)[:3]) or tuple(sorted(filenames)[:3]),
            }
            for fname in filenames:
                ext = Path(fname).suffix.lstrip(".").lower() or "(noext)"
                if by_file:
                    file_rows.append(
                        AssetGroup(name=os.path.join(label, fname), tags=(f"ext:{ext}",))
                    )
                else:
                    counts[ext] = counts.get(ext, 0) + 1
                    if len(examples.setdefault(ext, [])) < 3:
                        examples[ext].append(os.path.relpath(dirpath, base))
                seen += 1
                if seen >= max_files:
                    inv.note = f"capped at {max_files} files"
                    break
            if seen >= max_files:
                break

    dir_rows = _build_dir_rows(dir_info)
    if by_file:
        files = file_rows
    else:
        files = [
            AssetGroup(name=f".{ext}", count=counts[ext], examples=tuple(examples[ext]))
            for ext in sorted(counts, key=lambda e: -counts[e])
        ]
    inv.assets = dir_rows + files
    return inv


def _build_dir_rows(dir_info: dict[str, dict]) -> list[AssetGroup]:
    """Turn collected directory info into assets, ranked by subtree contents.

    A directory inherits the most sensitive file-type found anywhere *beneath*
    it, not just directly inside — reading a folder exposes its whole subtree.
    """
    rows: list[AssetGroup] = []
    for dirpath, info in dir_info.items():
        best_ext, best_band = info["ext"], info["band"]
        prefix = dirpath.rstrip(os.sep) + os.sep
        for other, oinfo in dir_info.items():
            if other.startswith(prefix) and oinfo["band"] > best_band:
                best_ext, best_band = oinfo["ext"], oinfo["band"]
        tags = ("directory",) + ((f"ext:{best_ext}",) if best_ext else ())
        rows.append(
            AssetGroup(
                name=f"{info['label']}/",
                count=info["count"],
                tags=tags,
                examples=info["examples"],
            )
        )
    return rows


def _enumerate_sqlite(spec: ConnectionSpec, *, by_file: bool = False) -> AssetInventory:
    """List tables and tag PII-ish columns via an immutable read-only connection.

    ``by_file`` is accepted for a uniform local-enumerator signature but ignored:
    the asset unit for a SQL store is the table, not a file.
    """
    inv = AssetInventory(server=spec.name, kind="sqlite")
    if not spec.roots:
        return inv

    anchor_cols = set(DB_COLUMN_ANCHOR)
    for db_path in spec.roots:
        path = Path(db_path).expanduser()
        if not path.is_file():
            logger.debug("sqlite db %s not found", path)
            continue
        try:
            with sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True) as conn:
                tables = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                ]
                for table in tables:
                    cols = [r[1].lower() for r in conn.execute(f'PRAGMA table_info("{table}")')]
                    try:
                        nrows = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    except sqlite3.Error:
                        nrows = 0
                    tags = tuple(
                        f"column:{c}" for c in cols if any(a in c for a in anchor_cols)
                    )
                    inv.assets.append(AssetGroup(name=table, count=nrows, tags=tags))
        except sqlite3.Error as exc:
            logger.warning("failed to read sqlite db %s: %s", path, exc)
            inv.note = f"sqlite error: {exc}"
    return inv


# A local enumerator only applies when the spec points at a local store (roots).
# Each accepts a ``by_file`` keyword (filesystem honors it; sqlite ignores it).
LOCAL_ENUMERATORS: dict[str, Callable[..., AssetInventory]] = {
    "filesystem": _enumerate_filesystem,
    "sqlite": _enumerate_sqlite,
}


# ===========================================================================
# Generic protocol enumeration — works for ANY MCP server, no per-kind code
# ===========================================================================
def _has_no_required_args(tool) -> bool:
    """True if the tool can be called with empty arguments."""
    schema = getattr(tool, "inputSchema", None) or {}
    required = schema.get("required") if isinstance(schema, dict) else None
    return not required


def _extension_tags(name: str, mime: str | None) -> tuple[str, ...]:
    """Ranking hints derived generically from a resource name / mime type."""
    tags: list[str] = []
    suffix = Path(name).suffix.lstrip(".").lower()
    if suffix:
        tags.append(f"ext:{suffix}")
    if mime:
        tags.append(f"mime:{mime}")
    return tuple(tags)


def _parse_tool_result(result) -> list[AssetGroup]:
    """Best-effort, schema-agnostic parse of a list-tool result into assets.

    Handles JSON arrays of strings, JSON arrays of objects (name/id/title/uri),
    and single objects wrapping such an array. Anything unparseable yields [].
    """
    text = "".join(
        getattr(item, "text", "") or "" for item in (getattr(result, "content", []) or [])
    )
    if not text.strip():
        return []
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []

    if isinstance(data, dict):
        # Unwrap the first list value (e.g. {"channels": [...]}).
        data = next((v for v in data.values() if isinstance(v, list)), [])
    if not isinstance(data, list):
        return []

    groups: list[AssetGroup] = []
    for row in data:
        if isinstance(row, str):
            groups.append(AssetGroup(name=row))
        elif isinstance(row, dict):
            name = row.get("name") or row.get("id") or row.get("title") or row.get("uri")
            if not name:
                continue
            tags: list[str] = []
            if row.get("is_private"):
                tags.append("private")
            if row.get("is_im") or row.get("is_dm"):
                tags.append("dm")
            groups.append(AssetGroup(name=str(name), tags=tuple(tags)))
    return groups


async def _generic_live_enumerate(spec: ConnectionSpec) -> AssetInventory:
    """Enumerate any server via the MCP protocol: resources + read-only tools."""
    inv = AssetInventory(server=spec.name, kind=spec.kind)
    by_name: dict[str, AssetGroup] = {}

    async with _open_session(spec) as session:
        # 1. Declared resources are the protocol-native assets.
        for res in await _safe_list_resources(session):
            name = res.get("name") or res.get("uri") or "resource"
            by_name.setdefault(name, AssetGroup(name=name, tags=_extension_tags(name, res.get("mime"))))

        # 2. Any read-only, no-arg tool that enumerates: call it, parse rows.
        tools = (await session.list_tools()).tools
        inv.context = _describe_server(tools)
        used: list[str] = []
        for tool in tools:
            schema = getattr(tool, "inputSchema", {}) or {}
            if not is_read_only(tool.name, tool.description or "", schema):
                continue
            if not _has_no_required_args(tool):
                continue
            try:
                result = await session.call_tool(tool.name, {})
            except Exception as exc:  # noqa: BLE001 — best-effort enumeration
                logger.debug("tool %s failed: %s", tool.name, exc)
                continue
            rows = _parse_tool_result(result)
            if rows:
                used.append(tool.name)
                for g in rows:
                    by_name.setdefault(g.name, g)

        if used:
            inv.note = "via " + ", ".join(used)

    inv.assets = list(by_name.values())
    return inv


_MAX_CONTEXT_TOOLS = 25


def _describe_server(tools) -> str:
    """Summarize what a server does from its tool names + descriptions.

    This is the signal the ranker's understanding agent uses to reason about a
    server it has never seen — no per-kind knowledge required. Truncated so a
    sprawling toolset cannot blow up the prompt.
    """
    lines: list[str] = []
    for tool in tools[:_MAX_CONTEXT_TOOLS]:
        desc = (getattr(tool, "description", "") or "").strip().splitlines()
        first = desc[0].strip() if desc else ""
        lines.append(f"- {tool.name}: {first}" if first else f"- {tool.name}")
    return "\n".join(lines)


async def _safe_list_resources(session) -> list[dict]:
    try:
        res = await session.list_resources()
    except Exception as exc:  # noqa: BLE001 — many servers don't implement it
        logger.debug("list_resources unavailable: %s", exc)
        return []
    return [
        {
            "name": getattr(r, "name", "") or "",
            "uri": str(getattr(r, "uri", "")),
            "mime": getattr(r, "mimeType", None),
        }
        for r in res.resources
    ]


# ===========================================================================
# Per-kind enumeration THROUGH the MCP protocol — drive the server's own tools.
#
# Used when the spec is a *configured server* (has a command/url): instead of
# reading the local store directly, the scanner asks the running server via its
# own read-only tools. This is per-kind by necessity — the procedure (which tool
# to call, with what argument, how to recurse) differs per server kind. Every
# call still goes through the read-only :func:`is_read_only` gate.
# ===========================================================================

# Tool-name candidates per kind; first existing read-only match is used.
_SQLITE_LIST_TOOLS = ("list_tables", "list_table", "show_tables", "get_tables")
_SQLITE_DESCRIBE_TOOLS = ("describe_table", "table_info", "get_table_schema", "table_schema")
_FS_ROOT_TOOLS = ("list_allowed_directories", "list_roots", "get_allowed_directories")
_FS_TREE_TOOLS = ("directory_tree", "tree", "list_directory_tree")
_FS_LIST_TOOLS = ("list_directory", "list_dir", "read_directory", "ls")


def _tool_index(tools) -> dict[str, object]:
    return {t.name: t for t in tools}


def _pick_tool(index: dict, candidates: tuple[str, ...]):
    """First candidate tool that exists and passes the read-only safety gate."""
    for name in candidates:
        tool = index.get(name)
        if tool is None:
            continue
        schema = getattr(tool, "inputSchema", {}) or {}
        if is_read_only(name, getattr(tool, "description", "") or "", schema):
            return tool
    return None


def _required_arg(tool, default: str) -> str:
    """Name of the tool's first required argument (e.g. ``table_name``/``path``)."""
    req = (getattr(tool, "inputSchema", {}) or {}).get("required") or []
    return req[0] if req else default


def _parse_payload(text: str):
    """Parse a tool's text result as JSON or Python-repr (some servers emit repr)."""
    text = text.strip()
    if not text:
        return None
    for parse in (json.loads, ast.literal_eval):
        try:
            return parse(text)
        except (ValueError, SyntaxError):
            continue
    return None


async def _call_payload(session, tool_name: str, args: dict):
    """Call a read-only tool and return its parsed payload (or None)."""
    result = await session.call_tool(tool_name, args)
    text = "".join(
        getattr(c, "text", "") or "" for c in (getattr(result, "content", []) or [])
    )
    return _parse_payload(text)


def _row_names(data) -> list[str]:
    """Pull names from a list of strings or dicts (name/table/id/title keys)."""
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    if not isinstance(data, list):
        return []
    names: list[str] = []
    for row in data:
        if isinstance(row, str):
            names.append(row)
        elif isinstance(row, dict):
            name = row.get("name") or row.get("table") or row.get("id") or row.get("title")
            if name:
                names.append(str(name))
    return names


async def _mcp_enumerate_sqlite(spec: ConnectionSpec, session) -> AssetInventory:
    """Find tables via the server's ``list_tables`` + ``describe_table`` tools."""
    inv = AssetInventory(server=spec.name, kind="sqlite")
    tools = (await session.list_tools()).tools
    inv.context = _describe_server(tools)
    index = _tool_index(tools)

    list_tool = _pick_tool(index, _SQLITE_LIST_TOOLS)
    if list_tool is None:
        return inv  # no read-only list-tables tool → caller falls back
    tables = _row_names(await _call_payload(session, list_tool.name, {}))

    describe_tool = _pick_tool(index, _SQLITE_DESCRIBE_TOOLS)
    arg = _required_arg(describe_tool, "table_name") if describe_tool else ""
    anchor_cols = set(DB_COLUMN_ANCHOR)
    for table in tables:
        if table.startswith("sqlite_"):
            continue
        tags: tuple[str, ...] = ()
        if describe_tool is not None:
            cols_payload = await _call_payload(session, describe_tool.name, {arg: table})
            cols = [
                str(c.get("name", "")).lower()
                for c in (cols_payload or [])
                if isinstance(c, dict)
            ]
            tags = tuple(f"column:{c}" for c in cols if any(a in c for a in anchor_cols))
        inv.assets.append(AssetGroup(name=table, tags=tags))

    used = list_tool.name + (f" + {describe_tool.name}" if describe_tool else "")
    inv.note = f"via {used}"
    return inv


def _collect_tree(
    nodes, base: str, tree: dict[str, list[str]], depth: int, max_depth: int,
    counter: list[int], max_entries: int,
) -> None:
    """Flatten a ``directory_tree`` payload into {dir_path: [filenames]}."""
    files_here = tree.setdefault(base, [])
    for node in nodes:
        if not isinstance(node, dict) or counter[0] >= max_entries:
            break
        name = str(node.get("name", ""))
        is_dir = node.get("type") == "directory" or "children" in node
        counter[0] += 1
        if is_dir:
            child = f"{base}/{name}"
            tree.setdefault(child, [])
            if depth < max_depth:
                _collect_tree(
                    node.get("children") or [], child, tree, depth + 1, max_depth,
                    counter, max_entries,
                )
        else:
            files_here.append(name)


def _filesystem_rows(tree: dict[str, list[str]], by_file: bool) -> list[AssetGroup]:
    """Build directory + file asset rows from a {dir_path: [filenames]} map."""
    dir_info: dict[str, dict] = {}
    counts: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    file_rows: list[AssetGroup] = []

    for dpath, filenames in tree.items():
        top = _most_sensitive_ext(filenames)
        dir_info[dpath] = {
            "label": dpath,
            "count": len(filenames),
            "ext": top,
            "band": BAND.get(FILETYPE_SENSITIVITY.get(top or "", ""), 0),
            "examples": tuple(sorted(filenames)[:3]),
        }
        for fname in filenames:
            ext = Path(fname).suffix.lstrip(".").lower() or "(noext)"
            if by_file:
                file_rows.append(AssetGroup(name=f"{dpath}/{fname}", tags=(f"ext:{ext}",)))
            else:
                counts[ext] = counts.get(ext, 0) + 1
                if len(examples.setdefault(ext, [])) < 3:
                    examples[ext].append(dpath)

    dirs = _build_dir_rows(dir_info)
    if by_file:
        return dirs + file_rows
    files = [
        AssetGroup(name=f".{ext}", count=counts[ext], examples=tuple(examples[ext]))
        for ext in sorted(counts, key=lambda e: -counts[e])
    ]
    return dirs + files


async def _mcp_enumerate_filesystem(
    spec: ConnectionSpec,
    session,
    *,
    by_file: bool = False,
    max_entries: int = DEFAULT_MAX_FILES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> AssetInventory:
    """Find files/directories via the server's own listing tools (read-only).

    Prefers a recursive ``directory_tree`` tool; falls back to a shallow
    ``list_directory`` of each root. Roots come from the spec, or the server's
    ``list_allowed_directories`` tool.
    """
    inv = AssetInventory(server=spec.name, kind="filesystem")
    tools = (await session.list_tools()).tools
    inv.context = _describe_server(tools)
    index = _tool_index(tools)

    roots = list(spec.roots)
    if not roots:
        root_tool = _pick_tool(index, _FS_ROOT_TOOLS)
        if root_tool is not None:
            roots = _row_names(await _call_payload(session, root_tool.name, {})) or ["."]
        else:
            roots = ["."]

    tree_tool = _pick_tool(index, _FS_TREE_TOOLS)
    list_tool = _pick_tool(index, _FS_LIST_TOOLS)
    if tree_tool is None and list_tool is None:
        return inv  # no read-only listing tool → caller falls back to generic

    tree: dict[str, list[str]] = {}
    counter = [0]
    for root in roots:
        label = Path(root).name or root
        if tree_tool is not None:
            payload = await _call_payload(
                session, tree_tool.name, {_required_arg(tree_tool, "path"): root}
            )
            tree.setdefault(label, [])
            if isinstance(payload, list):
                _collect_tree(payload, label, tree, 1, max_depth, counter, max_entries)
        else:
            payload = await _call_payload(
                session, list_tool.name, {_required_arg(list_tool, "path"): root}
            )
            tree[label] = [n for n in _row_names(payload)]

    inv.assets = _filesystem_rows(tree, by_file)
    inv.note = f"via {(tree_tool or list_tool).name}"
    if counter[0] >= max_entries:
        inv.note += f"; capped at {max_entries} entries"
    return inv


# Per-kind enumerators that drive a live server's tools (vs reading disk).
MCP_KIND_ENUMERATORS: dict[str, Callable] = {
    "sqlite": _mcp_enumerate_sqlite,
    "filesystem": _mcp_enumerate_filesystem,
}


async def _run_mcp_kind(spec: ConnectionSpec, by_file: bool) -> AssetInventory:
    """Open a session and run the per-kind MCP enumerator, bounded + never raising."""
    try:
        with anyio.fail_after(_LIVE_TIMEOUT):
            async with _open_session(spec) as session:
                fn = MCP_KIND_ENUMERATORS[spec.kind]
                if spec.kind == "filesystem":
                    return await fn(spec, session, by_file=by_file)
                return await fn(spec, session)
    except TimeoutError:
        return AssetInventory(server=spec.name, kind=spec.kind, note="live enumeration timed out")
    except Exception as exc:  # noqa: BLE001 — empty inventory routes to the next path
        return AssetInventory(server=spec.name, kind=spec.kind, note=f"{type(exc).__name__}: {exc}")


# ===========================================================================
# Dispatch
# ===========================================================================
def enumerate_assets(spec: ConnectionSpec, *, by_file: bool = False) -> AssetInventory:
    """Enumerate one server's assets. Never raises; empty result ⇒ try resolver.

    Order: a *configured* fs/sqlite server is enumerated **through its own MCP
    tools** (ask the server); a raw ``--root`` local store is read directly;
    anything else falls to generic protocol enumeration. ``by_file`` lists
    individual files for a filesystem store instead of aggregating by extension.
    """
    try:
        # Configured server with a known kind → ask the server's own tools.
        if (spec.command or spec.url) and spec.kind in MCP_KIND_ENUMERATORS:
            inv = anyio.run(_run_mcp_kind, spec, by_file)
            if not inv.is_empty:
                return inv
        # Raw local store (--root), or MCP path came back empty → read directly.
        local = LOCAL_ENUMERATORS.get(spec.kind)
        if local is not None and spec.roots:
            inv = local(spec, by_file=by_file)
            if not inv.is_empty:
                return inv
        return anyio.run(_run_generic, spec)
    except Exception as exc:  # noqa: BLE001 — empty inventory routes to resolver
        logger.warning("enumeration failed for %s: %s", spec.name, exc)
        return AssetInventory(server=spec.name, kind=spec.kind, note=f"{type(exc).__name__}: {exc}")


async def _run_generic(spec: ConnectionSpec) -> AssetInventory:
    try:
        with anyio.fail_after(_LIVE_TIMEOUT):
            return await _generic_live_enumerate(spec)
    except TimeoutError:
        return AssetInventory(server=spec.name, kind=spec.kind, note="live enumeration timed out")
    except Exception as exc:  # noqa: BLE001
        return AssetInventory(server=spec.name, kind=spec.kind, note=f"{type(exc).__name__}: {exc}")
