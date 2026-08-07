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
    # MCP's fourth hint: the tool interacts with EXTERNAL entities rather than a
    # closed domain (spec 2025-03-26). Previously dropped on load, so nothing
    # downstream could see a boundary-crossing tool declare itself.
    open_world_hint: bool | None = None
    # The tool's JSON input schema, straight from the server's tools/list.
    input_schema: dict = field(default_factory=dict)

    def parameters(self) -> list[dict]:
        """Flatten the input schema into ``{name, type, description, required}``."""
        props = self.input_schema.get("properties", {}) if self.input_schema else {}
        required = set(self.input_schema.get("required", [])) if self.input_schema else set()
        return [
            {
                "name": name,
                "type": spec.get("type", "any") if isinstance(spec, dict) else "any",
                "description": spec.get("description", "") if isinstance(spec, dict) else "",
                "required": name in required,
            }
            for name, spec in props.items()
        ]

    def to_prompt_json(self) -> dict:
        """The registry entry shape the per-tool prompts expect."""
        return {
            "tool_name": self.name,
            "description": self.description,
            "parameters": self.parameters(),
            "annotations": {
                "read_only_hint": self.read_only_hint,
                "destructive_hint": self.destructive_hint,
                "idempotent_hint": self.idempotent_hint,
                "open_world_hint": self.open_world_hint,
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
    # Optional organizational profile written by the people deploying this server
    # (docs/mcp-tools/server-profiles.md, loaded by
    # :mod:`mcp_security.static_scoring.server_profiles`). Empty for a normal scan;
    # when set, the desc-mode pipeline puts it in front of every scoring stage.
    description: str = ""

    def tools_json(self) -> list[dict]:
        return [t.to_prompt_json() for t in self.tools]

    def tools_json_compact(self) -> list[dict]:
        """Name + description only, for the domain-inference prompt.

        Domain inference sees the WHOLE tool set in one context and only needs to
        recognise the domain, not each tool's parameters — so it drops the input
        schemas that make a large server's full ``tools_json`` overflow the model's
        context window (per-tool stages still get the full schema, one tool at a
        time).
        """
        return [{"tool_name": t.name, "description": t.description} for t in self.tools]

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
# Cap directory-scope assets independently of files.
_MAX_DIRS_BY_PATH = 24
_FS_IGNORE = {".gitkeep", ".gitignore", ".DS_Store"}
# Directory-scope asset ids carry a trailing slash so they never collide with a
# file of the same name; the store root is the bare slash.
_DIR_SUFFIX = "/"
_ROOT_DIR_ID = "/"


def _directory_scope_assets(rels: list[Path]) -> list[AssetSpec]:
    """Build directory-scope assets from the relative paths of the scanned files.

    A directory scope is a *container* asset: enumeration/fan-out tools
    (list_directory, directory_tree, search_files, multi-file reads) and any call
    that targets a folder rather than a single file score against it. The scope's
    description lists what it contains (file count + extensions) so the LLM can
    judge how much one enumeration would expose; the worst child extension is
    tagged so the offline fallback can see sensitive contents too.
    """
    children: dict[str, list[Path]] = {}
    for rel in rels:
        for parent in rel.parents:  # e.g. sensitive/security, sensitive, .
            key = "" if parent == Path(".") else str(parent)
            children.setdefault(key, []).append(rel)
    scopes: list[AssetSpec] = []
    # Largest scopes first (root, then broad dirs) so the cap keeps the most
    # consequential containers; deterministic tie-break on the path.
    for key in sorted(children, key=lambda k: (-len(children[k]), k))[:_MAX_DIRS_BY_PATH]:
        members = children[key]
        exts = sorted({(p.suffix.lstrip(".").lower() or "noext") for p in members})
        asset_id = _ROOT_DIR_ID if key == "" else key + _DIR_SUFFIX
        label = "store root" if key == "" else key
        seg_tags = tuple(f"path:{seg.lower()}" for seg in Path(key).parts) if key else ()
        scopes.append(
            AssetSpec(
                asset_id=asset_id,
                description=(
                    f"directory scope '{label}' containing {len(members)} file(s) "
                    f"[{', '.join(exts)}] — one enumeration exposes all of them"
                ),
                tags=("kind:directory", *(f"ext:{e}" for e in exts), *seg_tags),
            )
        )
    return scopes


def _filesystem_assets_by_file(root: Path) -> list[AssetSpec]:
    """take2 asset classes = one per file (full relative path) PLUS directory scopes.

    The file asset id is the path itself (``patients/alice/medical_history.txt``)
    so the model can see what the file *is* from its directory and name. In
    addition, one *directory-scope* asset is emitted per folder (and the root) so
    enumeration/fan-out tools and folder-targeted calls resolve to a concrete
    container instead of being dropped as unresolved. Sorted for determinism and
    capped at :data:`_MAX_FILES_BY_PATH` files / :data:`_MAX_DIRS_BY_PATH` dirs.
    """
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name not in _FS_IGNORE)
    if len(files) > _MAX_FILES_BY_PATH:
        files = files[:_MAX_FILES_BY_PATH]
    rels = [path.relative_to(root) for path in files]
    assets: list[AssetSpec] = []
    for rel in rels:
        ext = rel.suffix.lstrip(".").lower() or "noext"
        # Tag each path segment so the fallback can match on folders too.
        seg_tags = tuple(f"path:{seg.lower()}" for seg in rel.parts[:-1])
        assets.append(
            AssetSpec(
                asset_id=str(rel),
                description=f"file at {rel}",
                tags=(f"ext:{ext}", *seg_tags),
            )
        )
    assets.extend(_directory_scope_assets(rels))
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

# Mutable-state assets: everything the write tools can CHANGE, beyond the
# channel containers themselves. "Asset" here means any state a tool call can
# alter — even non-typical state like reaction emojis or read cursors — because
# each is its own damage surface at design time. (id, description); tagged
# kind:mutable-state so downstream consumers can tell them from scope assets.
_SLACK_MUTABLE_STATE: list[tuple[str, str]] = [
    (
        "channel-messages",
        "message stream of every reachable channel — write tools append messages "
        "and thread replies seen by all members (spam, phishing, impersonating the org)",
    ),
    (
        "message-reactions",
        "emoji-reaction state on existing messages — reactions act as ack/approval "
        "signals, so a forged reaction can spoof a sign-off",
    ),
    (
        "read-markers",
        "per-conversation read/unread cursors — marking a conversation read can bury "
        "security alerts or approvals the user never saw",
    ),
    (
        "usergroup-membership",
        "user-group composition and metadata (@group aliases) — changing who is in a "
        "group redirects pages, mentions and escalations",
    ),
    (
        "agent-channel-membership",
        "the agent's own channel join/leave state — joining widens what it can read "
        "and post; leaving removes it from oversight channels",
    ),
]


def _mutable_state_assets(entries: list[tuple[str, str]]) -> list[AssetSpec]:
    """Build mutable-state :class:`AssetSpec`\\ s from ``(id, description)`` pairs."""
    return [
        AssetSpec(
            asset_id=asset_id,
            description=f"mutable state: {description}",
            tags=("kind:mutable-state", f"state:{asset_id}"),
        )
        for asset_id, description in entries
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
    assets.extend(_mutable_state_assets(_SLACK_MUTABLE_STATE))
    # Read-surface assets: state no tool mutates but that read tools expose —
    # every tool must have an asset it affects.
    assets.append(
        AssetSpec(
            asset_id="user-directory",
            description=(
                "workspace member directory — names, emails, phone numbers and titles "
                "of every user (PII), exposed by the user-listing/profile tools"
            ),
            tags=("kind:read-surface", "category:pii"),
        )
    )
    assets.append(
        AssetSpec(
            asset_id="channel-directory",
            description=(
                "the channel catalog — which channels exist, their names, topics and "
                "membership; listing it reveals the org's team structure and where "
                "sensitive conversations live"
            ),
            tags=("kind:read-surface", "category:catalog"),
        )
    )
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


# Google Calendar MCP — a scheduling server. Assets are CALENDARS (scopes); the
# threat surface is mass deletion, external invites (exfil), contact-directory
# reads (PII), and oversized-attendee events. Tools mirror the captured calendar
# session (logs/proxy/sessions/calendar_pm_sim). Destructive tools push impact 3.
_CALENDAR_TOOLS: list[ToolSpec] = [
    ToolSpec("list_calendars", "List the calendars the agent can access.", read_only_hint=True),
    ToolSpec("list_events", "List events on a calendar in a date range.", read_only_hint=True),
    ToolSpec("list_week", "List a week of events on a calendar.", read_only_hint=True),
    ToolSpec("get_event", "Read one event's full details.", read_only_hint=True),
    ToolSpec("find_free_slot", "Find a free time slot across attendees.", read_only_hint=True),
    ToolSpec("access_contacts", "Read the contact directory (names, emails).", read_only_hint=True),
    ToolSpec(
        "create_event",
        "Create an event with attendees.",
        read_only_hint=False,
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "event title"},
                "date": {"type": "string", "description": "event date"},
                "calendar": {"type": "string", "description": "target calendar id"},
                "attendees": {"type": "array", "description": "attendee usernames/emails invited"},
                "duration_min": {"type": "number", "description": "meeting length in minutes"},
            },
            "required": ["title", "date"],
        },
    ),
    ToolSpec(
        "update_event",
        "Modify an existing event.",
        read_only_hint=False,
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "calendar": {"type": "string", "description": "target calendar id"},
                "attendees": {"type": "array", "description": "attendee usernames/emails invited"},
                "duration_min": {"type": "number", "description": "meeting length in minutes"},
            },
            "required": ["event_id"],
        },
    ),
    ToolSpec(
        "send_email_invite",
        "Email an invite to external attendees.",
        read_only_hint=False,
        destructive_hint=False,
    ),
    ToolSpec("delete_event", "Delete one event.", read_only_hint=False, destructive_hint=True),
    ToolSpec(
        "delete_all_events",
        "Delete every event on a calendar.",
        read_only_hint=False,
        destructive_hint=True,
    ),
]

# Mutable-state assets for the calendar kind: what the write tools can change,
# beyond the calendar containers — event bodies, attendee lists, the outbound
# invite email they trigger, the user's RSVP state, and (in real catalogs with
# account-management tools) the connected-account configuration itself.
_CALENDAR_MUTABLE_STATE: list[tuple[str, str]] = [
    (
        "event-records",
        "the events themselves — titles, times, locations and descriptions are "
        "editable and deletable (meeting sabotage, planted lure links, mass wipe)",
    ),
    (
        "event-attendee-lists",
        "attendee lists of events — adding an external address forwards the event's "
        "details and every update outside the org (invite-based exfiltration)",
    ),
    (
        "outbound-invite-email",
        "invite/notification email sent on the user's behalf — external recipients "
        "receive attacker-chosen content under the user's identity",
    ),
    (
        "rsvp-state",
        "the user's accept/decline responses to invitations — a forged RSVP silently "
        "commits or frees the user's time and signals attendance",
    ),
    (
        "connected-account-config",
        "which calendar accounts the server is bound to — account-management tools "
        "can add or switch accounts, changing whose data every other tool touches",
    ),
]


# (calendar_id, category, note) — the calendar scopes an agent can target.
_CALENDAR_SCOPES: list[tuple[str, str, str]] = [
    ("personal", "personal", "the user's own schedule"),
    ("team", "team", "shared engineering team calendar"),
    ("executive", "executive", "exec/board calendar — M&A, comp, strategy meetings"),
    ("recruiting", "recruiting", "candidate interview schedule — PII of applicants"),
    ("contacts", "directory", "contact directory: names, emails, phone numbers (PII)"),
    ("holidays", "public", "public company holiday calendar"),
]


def load_calendar_registry(
    tools: list[ToolSpec] | None = None, *, server: str = "google-calendar-mcp"
) -> ServerRegistry:
    """Build the Google Calendar MCP registry: fixed tool set + calendar scopes."""
    assets = [
        AssetSpec(
            asset_id=cal_id,
            description=f"{category} calendar — {note}",
            tags=(f"calendar:{category}",),
        )
        for cal_id, category, note in _CALENDAR_SCOPES
    ]
    assets.extend(_mutable_state_assets(_CALENDAR_MUTABLE_STATE))
    # Read-surface asset: free-slot/freebusy tools read availability across
    # attendees — schedule patterns of OTHER users, not just the caller's.
    assets.append(
        AssetSpec(
            asset_id="free-busy-availability",
            description=(
                "cross-user availability (free/busy) data — reveals when, how often "
                "and with whom every queried attendee meets (schedule surveillance)"
            ),
            tags=("kind:read-surface", "category:schedule"),
        )
    )
    assets.append(
        AssetSpec(
            asset_id="calendar-directory",
            description=(
                "the calendar catalog — which calendars exist and their names; "
                "listing it maps out where executive, recruiting or team schedules live"
            ),
            tags=("kind:read-surface", "category:catalog"),
        )
    )
    return ServerRegistry(
        server=server,
        kind="calendar",
        tools=list(tools or _CALENDAR_TOOLS),
        assets=assets,
        apps={
            "scheduler_bot": "Agent that books and reschedules team meetings",
            "exec_assistant": "Agent managing the executive calendar and invites",
        },
    )


# GitHub MCP — a source-control server. Assets are REPOSITORIES (scopes); the
# threat surface is reading secret-bearing config, pushing to protected branches,
# deleting files, and merging unreviewed PRs. Destructive/write tools push impact.
_GITHUB_TOOLS: list[ToolSpec] = [
    ToolSpec("search_repositories", "Search repositories.", read_only_hint=True),
    ToolSpec("get_file_contents", "Read a file from a repository.", read_only_hint=True),
    ToolSpec("list_commits", "List a repository's commits.", read_only_hint=True),
    ToolSpec("get_issue", "Read an issue and its comments.", read_only_hint=True),
    ToolSpec("create_issue", "Open a new issue.", read_only_hint=False),
    ToolSpec(
        "create_or_update_file",
        "Write or overwrite a file in a repo.",
        read_only_hint=False,
        destructive_hint=True,
    ),
    ToolSpec(
        "push_files",
        "Push multiple files in one commit.",
        read_only_hint=False,
        destructive_hint=True,
    ),
    ToolSpec(
        "delete_file", "Delete a file from a repo.", read_only_hint=False, destructive_hint=True
    ),
    ToolSpec("create_pull_request", "Open a pull request.", read_only_hint=False),
    ToolSpec(
        "merge_pull_request",
        "Merge a pull request into the base branch.",
        read_only_hint=False,
        destructive_hint=True,
    ),
    ToolSpec("fork_repository", "Fork a repository to another account.", read_only_hint=False),
]

# Mutable-state assets for the github kind: state the write tools can change
# across ANY reachable repo, beyond the repository containers — branch heads,
# issues/comments, PRs and their reviews/merge state — plus org-external copies
# (forks, new repositories) that tool calls can bring into existence.
_GITHUB_MUTABLE_STATE: list[tuple[str, str]] = [
    (
        "branch-heads",
        "branch heads and commit history — file writes, pushes and merges rewrite "
        "what CI builds and what reviewers see as the current code",
    ),
    (
        "issues-and-comments",
        "issues, their state and comments — closing real alerts, retitling reports, "
        "or planting comment instructions that other agents later read and follow",
    ),
    (
        "pull-requests-and-reviews",
        "pull requests, their reviews and merge state — an approving review plus a "
        "merge lands unreviewed code on a protected branch",
    ),
    (
        "org-external-copies",
        "forks and newly created repositories under other accounts — a fork is a "
        "complete copy of the code outside the org's control (egress + staging ground)",
    ),
]


# (repo, category, note) — the repositories an agent can target.
_GITHUB_REPOS: list[tuple[str, str, str]] = [
    ("public-website", "public", "the public marketing site — open source"),
    ("internal-docs", "internal", "internal engineering documentation"),
    ("backend-api", "source", "core backend service source code"),
    ("payments-service", "source", "payment processing service — handles card flows"),
    ("infra-config", "secrets", "infra/CI config: deploy keys, tokens, .env templates"),
    ("ml-research", "source", "proprietary ML research and model weights pointers"),
]


def load_github_registry(
    tools: list[ToolSpec] | None = None, *, server: str = "github-mcp"
) -> ServerRegistry:
    """Build the GitHub MCP registry: fixed tool set + repository scopes."""
    assets = [
        AssetSpec(
            asset_id=repo,
            description=f"{category} repository — {note}",
            tags=(f"repo:{category}",),
        )
        for repo, category, note in _GITHUB_REPOS
    ]
    assets.extend(_mutable_state_assets(_GITHUB_MUTABLE_STATE))
    # Read-surface asset: real catalogs expose user search — public account
    # profiles, low sensitivity but a reconnaissance surface.
    assets.append(
        AssetSpec(
            asset_id="platform-user-directory",
            description=(
                "public GitHub user/organization account profiles reachable via user "
                "search — public data, but enables contributor reconnaissance"
            ),
            tags=("kind:read-surface", "category:public"),
        )
    )
    assets.append(
        AssetSpec(
            asset_id="repository-catalog",
            description=(
                "the repository catalog — which repositories exist plus their names, "
                "descriptions and visibility; searching it maps the org's codebase "
                "and singles out secret-bearing or payment repos to target"
            ),
            tags=("kind:read-surface", "category:catalog"),
        )
    )
    return ServerRegistry(
        server=server,
        kind="github",
        tools=list(tools or _GITHUB_TOOLS),
        assets=assets,
        apps={
            "ci_bot": "Agent that opens PRs and reads files for CI",
            "release_bot": "Agent that pushes release commits and merges PRs",
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


# Public aliases — the scanner reuses these disk/schema asset builders and the
# default app catalogs, but sources its *tools* from the Excel tool catalog.
filesystem_assets = _filesystem_assets
filesystem_assets_by_file = _filesystem_assets_by_file
sqlite_assets = _sqlite_assets
FS_DEFAULT_APPS = _FS_DEFAULT_APPS
SQLITE_DEFAULT_APPS = _SQLITE_DEFAULT_APPS
# Declarative-registry servers (assets come from the registry, not disk): the
# scanner calls these directly for the messaging/scheduling/source-control kinds.
CALENDAR_TOOLS = _CALENDAR_TOOLS
GITHUB_TOOLS = _GITHUB_TOOLS
SLACK_TOOLS = _SLACK_TOOLS


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
