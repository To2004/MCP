"""Discover assets from configured MCP stores and save them for rubric ranking.

Discovery runs on the login node (no GPU/LLM needed). The ranking step
(``rank_assets_with_rubric.py``) consumes the JSON this writes and runs on a
SLURM GPU node where Ollama/Qwen is available.

Targets:
  * sqlite MCP server — enumerated live through its own tools (list_tables +
    describe_table) via ``uvx mcp-server-sqlite``.
  * filesystem store — the demo corp filesystem, read directly via ``--root``.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_security.scanner.config_reader import ConnectionSpec, spec_from_root
from mcp_security.scanner.enumerator import enumerate_assets

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "reports" / "discovered_assets.json"


def _targets() -> list[ConnectionSpec]:
    return [
        ConnectionSpec(
            name="sqlite-mcp",
            kind="sqlite",
            transport="stdio",
            command="uvx",
            args=("mcp-server-sqlite", "--db-path", str(REPO / "demo/corp_sqlite/corp.db")),
            scope="cli",
        ),
        spec_from_root(str(REPO / "demo/corp_filesystem"), kind="filesystem"),
    ]


def main() -> None:
    servers = []
    for spec in _targets():
        inv = enumerate_assets(spec)
        servers.append(
            {
                "server": spec.name,
                "kind": inv.kind,
                "source": inv.source,
                "note": inv.note,
                "context": inv.context,
                "assets": [
                    {"name": a.name, "tags": list(a.tags), "count": a.count} for a in inv.assets
                ],
            }
        )
        print(f"{spec.name:14} kind={inv.kind:10} assets={len(inv.assets)}  ({inv.note})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(servers, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT} ({sum(len(s['assets']) for s in servers)} assets total)")


if __name__ == "__main__":
    main()
