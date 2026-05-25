"""Static catalog of MCP servers we classify, plus paths to cached READMEs and tool lists.

Tier A servers have deeply-curated docs/mcp-tools/<name>.md READMEs and
hand-authored tool-list JSON files in this package's data/tool_lists/. Tier B
servers are README-only by default; if introspection succeeds later, the
tool list is cached at the same data/tool_lists/ path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(__file__).resolve().parent / "data" / "tool_lists"
DOCS_MCP_TOOLS = REPO_ROOT / "docs" / "mcp-tools"


@dataclass(frozen=True)
class ServerEntry:
    """One MCP server in the classification corpus."""

    name: str
    package: str
    tier: Literal["A", "B"]
    install_hint: str
    readme_path: Path | None = None
    tool_list_path: Path | None = None
    notes: str = ""

    def load_readme(self) -> str:
        if self.readme_path and self.readme_path.exists():
            return self.readme_path.read_text(encoding="utf-8")
        return ""

    def load_tool_list(self) -> list[dict]:
        if self.tool_list_path and self.tool_list_path.exists():
            with self.tool_list_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        return []


KNOWN_SERVERS: list[ServerEntry] = [
    ServerEntry(
        name="filesystem",
        package="@modelcontextprotocol/server-filesystem",
        tier="A",
        install_hint="npx -y @modelcontextprotocol/server-filesystem <root>",
        readme_path=DOCS_MCP_TOOLS / "filesystem.md",
        tool_list_path=DATA_DIR / "filesystem.json",
    ),
    ServerEntry(
        name="sqlite",
        package="mcp-server-sqlite",
        tier="A",
        install_hint="uvx mcp-server-sqlite --db-path <db>",
        readme_path=DOCS_MCP_TOOLS / "sqlite.md",
        tool_list_path=DATA_DIR / "sqlite.json",
    ),
    ServerEntry(
        name="slack",
        package="@modelcontextprotocol/server-slack",
        tier="A",
        install_hint="npx -y @modelcontextprotocol/server-slack (needs SLACK_BOT_TOKEN)",
        readme_path=DOCS_MCP_TOOLS / "slack.md",
        tool_list_path=DATA_DIR / "slack.json",
        notes="Reference server; 8 tools. Remote slackapi server has more.",
    ),
    ServerEntry(
        name="github",
        package="github/github-mcp-server",
        tier="A",
        install_hint="docker run -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server",
        readme_path=DOCS_MCP_TOOLS / "github.md",
        tool_list_path=DATA_DIR / "github.json",
        notes="~102 tools across 15 toolsets. Token scope = blast radius.",
    ),
    ServerEntry(
        name="memory",
        package="@modelcontextprotocol/server-memory",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-memory",
        tool_list_path=DATA_DIR / "memory.json",
        notes="Knowledge-graph memory; CRUD on entities/relations.",
    ),
    ServerEntry(
        name="git",
        package="mcp-server-git",
        tier="B",
        install_hint="uvx mcp-server-git",
        tool_list_path=DATA_DIR / "git.json",
        notes="Git operations (status, log, diff, commit, branch).",
    ),
    ServerEntry(
        name="fetch",
        package="mcp-server-fetch",
        tier="B",
        install_hint="uvx mcp-server-fetch",
        tool_list_path=DATA_DIR / "fetch.json",
        notes="HTTP GET tool; converts HTML to markdown.",
    ),
    ServerEntry(
        name="time",
        package="mcp-server-time",
        tier="B",
        install_hint="uvx mcp-server-time",
        tool_list_path=DATA_DIR / "time.json",
        notes="Time/timezone conversion; pure-function.",
    ),
    ServerEntry(
        name="everything",
        package="@modelcontextprotocol/server-everything",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-everything",
        tool_list_path=DATA_DIR / "everything.json",
        notes="Reference/demo server exercising every MCP capability.",
    ),
    ServerEntry(
        name="sequentialthinking",
        package="@modelcontextprotocol/server-sequentialthinking",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-sequentialthinking",
        tool_list_path=DATA_DIR / "sequentialthinking.json",
        notes="Single sequentialthinking tool for chain-of-thought.",
    ),
    ServerEntry(
        name="puppeteer",
        package="@modelcontextprotocol/server-puppeteer",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-puppeteer (archived)",
        tool_list_path=DATA_DIR / "puppeteer.json",
        notes="Browser automation; navigation/click/screenshot. Archived.",
    ),
    ServerEntry(
        name="brave-search",
        package="@modelcontextprotocol/server-brave-search",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-brave-search (API key)",
        tool_list_path=DATA_DIR / "brave-search.json",
        notes="Web search via Brave; archived in monorepo.",
    ),
    ServerEntry(
        name="postgres",
        package="@modelcontextprotocol/server-postgres",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-postgres <url>",
        tool_list_path=DATA_DIR / "postgres.json",
        notes="Postgres read-only query tool. Archived.",
    ),
    ServerEntry(
        name="gdrive",
        package="@modelcontextprotocol/server-gdrive",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-gdrive",
        tool_list_path=DATA_DIR / "gdrive.json",
        notes="Google Drive read access. Archived.",
    ),
    ServerEntry(
        name="redis",
        package="@modelcontextprotocol/server-redis",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-redis <url>",
        tool_list_path=DATA_DIR / "redis.json",
        notes="Redis KV operations. Archived.",
    ),
]


def get_server(name: str) -> ServerEntry:
    """Return the catalog entry by name; raises KeyError if not found."""
    for s in KNOWN_SERVERS:
        if s.name == name:
            return s
    raise KeyError(f"Unknown server: {name}")
