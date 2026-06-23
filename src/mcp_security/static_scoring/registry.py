"""Server registries: the input to the static-scoring pipeline.

A :class:`ServerRegistry` is everything the pipeline needs to score a server at
design time — the full tool registry (with the server's self-declared
annotations) and the asset classes the server can reach. It is deliberately
decoupled from how that data is obtained: the loaders here build registries from
the project's own simulation/demo data (the captured ``tools_catalog.csv`` for
the filesystem MCP, the live ``cbg.db`` schema for the sqlite MCP), but any
producer that yields the same shape works.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Captured filesystem MCP tool registry from the proxy simulation.
_FS_TOOLS_CATALOG = REPO_ROOT / "logs/proxy/parsed/tools_catalog.csv"
_FS_SERVER_NAME = "secure-filesystem-server"
# Demo filesystem whose extensions stand in for the server's asset classes.
_FS_DEMO_ROOT = REPO_ROOT / "demo/corp_filesystem"
# Demo sqlite database whose tables/columns are the server's asset classes.
_SQLITE_DEMO_DB = REPO_ROOT / "demo/cbg_sqlite/cbg.db"


@dataclass
class ToolSpec:
    """One tool in a server's registry, as the pipeline sees it."""

    name: str
    description: str = ""
    # Self-declared MCP annotations — hints only, never trusted as ground truth.
    read_only_hint: bool | None = None
    destructive_hint: bool | None = None
    idempotent_hint: bool | None = None

    def to_prompt_json(self) -> dict:
        """The registry entry shape the per-tool prompts expect."""
        return {
            "tool_name": self.name,
            "description": self.description,
            "annotations": {
                "read_only_hint": self.read_only_hint,
                "destructive_hint": self.destructive_hint,
                "idempotent_hint": self.idempotent_hint,
            },
        }


@dataclass
class AssetSpec:
    """One asset class the server can reach (a file type, a table, etc.)."""

    asset_id: str
    description: str = ""
    # Free-form tags the fallback heuristics key on (e.g. "column:ssn", "ext:pem").
    tags: tuple[str, ...] = ()

    def to_prompt_json(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "description": self.description,
            "tags": list(self.tags),
        }


@dataclass
class ServerRegistry:
    """A full server description: its tools and the asset classes it reaches."""

    server: str
    kind: str
    tools: list[ToolSpec] = field(default_factory=list)
    assets: list[AssetSpec] = field(default_factory=list)
    # Optional app catalog for the baseline stage: {app_id: purpose}.
    apps: dict[str, str] = field(default_factory=dict)

    def tools_json(self) -> list[dict]:
        return [t.to_prompt_json() for t in self.tools]

    def assets_json(self) -> list[dict]:
        return [a.to_prompt_json() for a in self.assets]


# ---------------------------------------------------------------------------
# Loaders — build registries from the project's simulation/demo data
# ---------------------------------------------------------------------------
def _dedup_filesystem_tools(catalog: Path, server_name: str) -> list[ToolSpec]:
    """Read distinct tools for one server from a captured ``tools_catalog.csv``.

    The catalog repeats every tool once per session; we keep the first sighting
    of each tool name and carry its self-declared read/destructive/idempotent
    hints through verbatim.
    """

    def _bool(cell: str) -> bool | None:
        cell = cell.strip().lower()
        return {"true": True, "false": False}.get(cell)

    seen: OrderedDict[str, ToolSpec] = OrderedDict()
    with catalog.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("server_name") != server_name:
                continue
            name = row["tool_name"]
            if name in seen:
                continue
            seen[name] = ToolSpec(
                name=name,
                description=row.get("description", ""),
                read_only_hint=_bool(row.get("read_only_hint", "")),
                destructive_hint=_bool(row.get("destructive_hint", "")),
                idempotent_hint=_bool(row.get("idempotent_hint", "")),
            )
    if not seen:
        raise ValueError(f"No tools for {server_name!r} in {catalog}")
    return list(seen.values())


def _filesystem_assets(root: Path) -> list[AssetSpec]:
    """take1 asset classes for a filesystem MCP = the distinct file *types*.

    Groups files by extension. Fast and small, but the *path* — where the
    sensitivity usually lives (``patients/``, ``clients/``) — is discarded, so a
    patient record and a grocery list both become ``.txt``. take2 fixes this.
    """
    exts: dict[str, int] = {}
    for path in root.rglob("*"):
        if path.is_file():
            ext = path.suffix.lstrip(".").lower() or "noext"
            exts[ext] = exts.get(ext, 0) + 1
    return [
        AssetSpec(
            asset_id=f".{ext}" if ext != "noext" else "(no extension)",
            description=f"{count} {ext} file(s) in the store",
            tags=(f"ext:{ext}",),
        )
        for ext, count in sorted(exts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


# Cap per-file enumeration so a large tree can't explode the matrix / GPU cost.
_MAX_FILES_BY_PATH = 80
_FS_IGNORE = {".gitkeep", ".gitignore", ".DS_Store"}


def _filesystem_assets_by_file(root: Path) -> list[AssetSpec]:
    """take2 asset classes = one per file, identified by its full relative path.

    The asset id is the path itself (``patients/alice_johnson/medical_history.txt``)
    so the model — and the offline keyword fallback — can see what the file *is*
    from its directory and name, not just its extension. Sorted for determinism
    and capped at :data:`_MAX_FILES_BY_PATH`.
    """
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name not in _FS_IGNORE)
    if len(files) > _MAX_FILES_BY_PATH:
        files = files[:_MAX_FILES_BY_PATH]
    assets: list[AssetSpec] = []
    for path in files:
        rel = path.relative_to(root)
        ext = path.suffix.lstrip(".").lower() or "noext"
        # Tag each path segment so the fallback can match on folders too.
        seg_tags = tuple(f"path:{seg.lower()}" for seg in rel.parts[:-1])
        assets.append(
            AssetSpec(
                asset_id=str(rel),
                description=f"file at {rel}",
                tags=(f"ext:{ext}", *seg_tags),
            )
        )
    return assets


_FS_DEFAULT_APPS = {
    "dev_assistant": "Engineering agent reading and editing source under the repo",
    "finance_console": "Finance agent reading contracts and spreadsheets, no code",
}


def load_filesystem_registry(
    root: Path | None = None,
    *,
    server: str | None = None,
    apps: dict[str, str] | None = None,
    by_file: bool = False,
) -> ServerRegistry:
    """Build a filesystem MCP registry from the captured tool registry + a root.

    All filesystem demos front the same ``secure-filesystem-server`` tool set
    (captured once in the proxy simulation); only the asset corpus differs, so
    the registry is parametrized by ``root``. ``by_file`` selects take2 per-file,
    full-path assets instead of take1 by-extension grouping.
    """
    if server is None:
        server = _FS_SERVER_NAME if root is None else f"fs:{root.name}"
    root = root or _FS_DEMO_ROOT
    tools = _dedup_filesystem_tools(_FS_TOOLS_CATALOG, _FS_SERVER_NAME)
    assets = _filesystem_assets_by_file(root) if by_file else _filesystem_assets(root)
    return ServerRegistry(
        server=server,
        kind="filesystem",
        tools=tools,
        assets=assets,
        apps=apps or _FS_DEFAULT_APPS,
    )


# The sqlite MCP server (logs/proxy/servers/mcp_cbg_sqlite_server.py) exposes a
# fixed five-tool registry; the proxy never captured its catalog, so we declare
# it from the server source — the single source of truth for that server.
_SQLITE_TOOLS: list[ToolSpec] = [
    ToolSpec("list_tables", "Discover available tables.", read_only_hint=True),
    ToolSpec("describe_table", "Column names and types for one table.", read_only_hint=True),
    ToolSpec("read_query", "Run a SELECT statement (read-only enforced).", read_only_hint=True),
    ToolSpec(
        "write_query",
        "Run INSERT / UPDATE / DELETE (DDL blocked).",
        read_only_hint=False,
        destructive_hint=True,
    ),
    ToolSpec(
        "insert_row",
        "Insert one row into a table.",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
    ),
]


def _sqlite_assets(db: Path) -> list[AssetSpec]:
    """Asset classes for a sqlite MCP = its tables, tagged by column names.

    Connects read-only and reads the schema only — never table contents.
    """
    assets: list[AssetSpec] = []
    uri = f"file:{db}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            cols = [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")]
            tags = tuple(f"column:{c.lower()}" for c in cols)
            assets.append(
                AssetSpec(
                    asset_id=table,
                    description=f"Table with columns: {', '.join(cols)}",
                    tags=tags,
                )
            )
    finally:
        conn.close()
    return assets


_SQLITE_DEFAULT_APPS = {
    "research_portal": "Research/business agent running SELECTs across the tables",
    "admin_console": "Admin agent that may insert or update rows",
}


def load_sqlite_registry(
    db: Path | None = None,
    *,
    server: str | None = None,
    apps: dict[str, str] | None = None,
) -> ServerRegistry:
    """Build a sqlite MCP registry from the fixed tool set + a live db schema."""
    if server is None:
        server = "cbg-sqlite-server" if db is None else f"sqlite:{db.parent.name}"
    db = db or _SQLITE_DEMO_DB
    return ServerRegistry(
        server=server,
        kind="sqlite",
        tools=list(_SQLITE_TOOLS),
        assets=_sqlite_assets(db),
        apps=apps or _SQLITE_DEFAULT_APPS,
    )


# Slack MCP — a genuinely different kind (messaging, not files/rows). Tools from
# demo/slack_mcp/index.ts; note there are NO destructive tools (max impact 2).
# Channels (asset classes) and their privacy/category from demo/slack_mcp/seed_cbg.py.
_SLACK_TOOLS: list[ToolSpec] = [
    ToolSpec("slack_list_channels", "List channels in the workspace.", read_only_hint=True),
    ToolSpec(
        "slack_get_channel_history", "Get recent messages from a channel.", read_only_hint=True
    ),
    ToolSpec(
        "slack_get_thread_replies", "Get all replies in a message thread.", read_only_hint=True
    ),
    ToolSpec("slack_get_users", "List users in the workspace.", read_only_hint=True),
    ToolSpec("slack_get_user_profile", "Get a user's detailed profile.", read_only_hint=True),
    ToolSpec("slack_post_message", "Post a new message to a channel.", read_only_hint=False),
    ToolSpec("slack_reply_to_thread", "Reply to a message thread.", read_only_hint=False),
    ToolSpec("slack_add_reaction", "Add a reaction emoji to a message.", read_only_hint=False),
]

# (channel, is_private, category) — straight from the seed script.
_SLACK_CHANNELS: list[tuple[str, bool, str]] = [
    ("general", False, "public"),
    ("announcements", False, "public"),
    ("random", False, "public"),
    ("engineering", False, "technical"),
    ("incident-response", True, "technical"),
    ("on-call", True, "technical"),
    ("research-team", True, "researcher"),
    ("exec-private", True, "management"),
    ("hr-internal", True, "hr"),
    ("team-leads", True, "supervisor"),
]


def load_slack_registry() -> ServerRegistry:
    """Build the slack MCP registry from the demo server + seeded channels."""
    assets = [
        AssetSpec(
            asset_id=name,
            description=f"{'private' if private else 'public'} {category} channel",
            tags=(f"channel:{'private' if private else 'public'}", f"category:{category}"),
        )
        for name, private, category in _SLACK_CHANNELS
    ]
    return ServerRegistry(
        server="slack-mcp-server",
        kind="slack",
        tools=list(_SLACK_TOOLS),
        assets=assets,
        apps={
            "notify_bot": "Bot that posts release notes to public channels",
            "support_agent": "Agent that reads channel history to answer questions",
        },
    )


# All demo servers, keyed by a friendly name. The filesystem demos share one
# tool registry over different corpora; the sqlite demos share one tool set over
# different schemas. This is the full set of "simulations" the --all runner scores.
_DEMO = REPO_ROOT / "demo"
_FS_DEMOS = {
    "corp_filesystem": ("secure-filesystem-server", _DEMO / "corp_filesystem"),
    "law_firm_fs": ("law-firm-fs", _DEMO / "law_firm_fs"),
    "medical_clinic_fs": ("medical-clinic-fs", _DEMO / "medical_clinic_fs"),
    "media_studio_fs": ("media-studio-fs", _DEMO / "media_studio_fs"),
}


def _demo_servers(*, by_file: bool) -> dict[str, Callable[[], ServerRegistry]]:
    """Build the demo-server registry map. ``by_file`` toggles take1/take2 for
    the filesystem demos; sqlite and slack are name-based and unchanged."""
    servers: dict[str, Callable[[], ServerRegistry]] = {
        name: (lambda s=server, r=root: load_filesystem_registry(r, server=s, by_file=by_file))
        for name, (server, root) in _FS_DEMOS.items()
    }
    servers["cbg_sqlite"] = lambda: load_sqlite_registry(
        _DEMO / "cbg_sqlite/cbg.db", server="cbg-sqlite-server"
    )
    servers["corp_sqlite"] = lambda: load_sqlite_registry(
        _DEMO / "corp_sqlite/corp.db", server="corp-sqlite-server"
    )
    servers["slack"] = load_slack_registry  # different kind: messaging, no destructive tools
    return servers


# take1 (by-extension) and take2 (per-file full path) variants of the demo set.
DEMO_SERVERS: dict[str, Callable[[], ServerRegistry]] = _demo_servers(by_file=False)
DEMO_SERVERS_TAKE2: dict[str, Callable[[], ServerRegistry]] = _demo_servers(by_file=True)

# CLI --kind shortcuts (the canonical filesystem/sqlite servers) plus every demo
# by name (slack is registered inside DEMO_SERVERS).
LOADERS: dict[str, Callable[[], ServerRegistry]] = {
    "filesystem": load_filesystem_registry,
    "sqlite": load_sqlite_registry,
    **DEMO_SERVERS,
}


def load_registry_from_json(path: Path) -> ServerRegistry:
    """Load a registry from a JSON file (escape hatch for arbitrary servers)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return ServerRegistry(
        server=data["server"],
        kind=data["kind"],
        tools=[ToolSpec(**t) for t in data.get("tools", [])],
        assets=[
            AssetSpec(**{**a, "tags": tuple(a.get("tags", ()))}) for a in data.get("assets", [])
        ],
        apps=data.get("apps", {}),
    )
