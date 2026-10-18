"""The catalogs the input-typing pass reads: one entry per MCP server.

Each entry names a **live-captured** tool list — the server's real surface, with
the schema constraints (``enum``, ``pattern``, ``minItems``, ``minimum``, …) the
typing questions depend on. There is deliberately **no fallback**: a server
either has a captured catalog or it is not typed. A hand-modelled stand-in would
be typed just as confidently and the answers would describe a server that does
not exist — which is exactly what happened when calendar was read from
``static_scoring.registry`` (11 simulated tools, 9 declared arguments) instead of
the captured catalog (13 real tools, 110 declared arguments).

``expected_tools`` is the count documented in ``reports/live_run/MCP_INVENTORY.md``
and is enforced at load time, so pointing an entry at the wrong file fails loudly
rather than producing a plausible run against the wrong server.

## Adding a server

1. Capture its tool list (``tools/list``) to a JSON file holding
   ``{"tools": [{"name", "description", "inputSchema"}, …]}``.
2. Record it in ``MCP_INVENTORY.md`` with its package and tool count.
3. Add one ``Catalog`` below. Nothing else changes: the CLI's choices, the
   sbatch loop and the summariser all read this table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "reports" / "live_run"


@dataclass(frozen=True)
class Catalog:
    """One MCP server's captured tool list."""

    server: str
    path: Path
    package: str
    expected_tools: int
    captured: str

    def load(self) -> list[dict]:
        """Tool definitions with their full input schema.

        Raises rather than degrading: a missing or unexpected catalog is a
        configuration error, not something to work around.
        """
        if not self.path.exists():
            raise SystemExit(
                f"{self.server}: no captured catalog at {self.path.relative_to(REPO)}. "
                "Capture the server's tools/list first; there is no fallback.")
        blob = json.loads(self.path.read_text())
        raw = blob.get("tools")
        if not raw:
            raise SystemExit(f"{self.server}: {self.path.relative_to(REPO)} has no 'tools'.")
        if len(raw) != self.expected_tools:
            raise SystemExit(
                f"{self.server}: catalog has {len(raw)} tools, MCP_INVENTORY.md documents "
                f"{self.expected_tools}. Either the capture is stale or this entry points "
                "at the wrong file — fix one of them before typing.")
        return [
            {
                "tool_name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("input_schema") or t.get("inputSchema") or {},
            }
            for t in raw
        ]


# Ordered as in MCP_INVENTORY.md.
CATALOGS: dict[str, Catalog] = {
    c.server: c
    for c in (
        Catalog(
            server="github",
            path=LIVE / "github_real_toollist.json",
            package="@modelcontextprotocol/server-github",
            expected_tools=26,
            captured="2026-07-06",
        ),
        Catalog(
            server="calendar",
            path=LIVE / "orgs_2026-07-29" / "verify_calendar.json",
            package="@cocal/google-calendar-mcp",
            expected_tools=13,
            captured="2026-07-29",
        ),
        Catalog(
            server="slack",
            path=LIVE / "slack_real_toollist.json",
            package="slack-mcp-server (korotovsky)",
            expected_tools=16,
            captured="2026-07-06",
        ),
        Catalog(
            server="filesystem",
            path=REPO / "reports" / "experiments" / "static_scanner" / "inputs" / "filesystem.json",
            package="@modelcontextprotocol/server-filesystem",
            expected_tools=14,
            captured="2026-06-08",
        ),
        Catalog(
            server="sqlite",
            path=REPO / "reports" / "experiments" / "static_scanner" / "inputs" / "sqlite.json",
            package="cbg-sqlite-server",
            expected_tools=5,
            captured="2026-06-08",
        ),
        # Captured from the gateway's log of the remote server, not from MCP_INVENTORY.md.
        Catalog(
            server="github_remote",
            path=REPO / "reports" / "experiments" / "gateway" / "github_remote" / "github_remote.json",
            package="remote GitHub MCP (api.githubcopilot.com/mcp/)",
            expected_tools=49,
            captured="2026-10-14",
        ),
    )
}

SERVERS = tuple(CATALOGS)


def load_tools(server: str) -> list[dict]:
    """Tool definitions for one server, or a loud failure."""
    if server not in CATALOGS:
        raise SystemExit(f"unknown server {server!r}; known: {', '.join(SERVERS)}")
    return CATALOGS[server].load()


def main() -> int:
    """Check every catalog: file present, parses, tool count as documented."""
    for cat in CATALOGS.values():
        tools = cat.load()
        args = sum(len((t["input_schema"] or {}).get("properties", {})) for t in tools)
        no_args = sum(1 for t in tools if not (t["input_schema"] or {}).get("properties"))
        print(f"{cat.server:9s} {len(tools):3d} tools · {args:4d} declared arguments · "
              f"{no_args} with none · {cat.package} · captured {cat.captured}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
