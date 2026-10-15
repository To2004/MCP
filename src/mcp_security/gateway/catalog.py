"""The server's tool catalog, as the gateway saw it: the input a static scan needs.

Every ``tools/list`` reply that passed through the gateway is in the route's log. This
collects the tools from the latest session that listed them (following ``nextCursor``
pages, which arrive as separate replies) and writes them in the shape ``static-scan``
reads: ``{"tools": [...]}``. The SHA-256 of that file names the catalog, so a scan can be
matched to the exact tool list it was run on.

    uv run python -m mcp_security.gateway.catalog --config routes.json --route github
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp_security.gateway.proxy import load_config
from mcp_security.gateway.wire_log import (
    LIST_METHOD,
    TO_AGENT,
    TO_SERVER,
    catalog_bytes,
    catalog_digest,
)
from mcp_security.gateway.log_file import read_log


def extract_catalog(records: list[dict]) -> dict:
    """The tools of the most recent session that listed them, in the order they were sent."""
    list_ids: set[tuple] = set()
    by_session: dict[str | None, dict[str, dict]] = {}
    latest: str | None = None
    for record in records:
        message = record.get("message") or {}
        session, direction = record.get("mcp.session.id"), record["gateway.direction"]
        key = (session, message.get("id"))
        if direction == TO_SERVER and message.get("method") == LIST_METHOD:
            list_ids.add(key)
        elif direction == TO_AGENT and key in list_ids:
            tools = (message.get("result") or {}).get("tools") or []
            page = by_session.setdefault(session, {})
            page.update({tool["name"]: tool for tool in tools if "name" in tool})
            latest = session
    if latest is None:
        raise ValueError("no tools/list reply in the log")
    return {"tools": list(by_session[latest].values())}


def main() -> None:
    """Write ``<log_dir>/<route>_catalog.json`` from the route's log and print its digest."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--route", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    catalog = extract_catalog(read_log(config.log_dir / f"{args.route}.jsonl"))
    out = config.log_dir / f"{args.route}_catalog.json"
    out.write_bytes(catalog_bytes(catalog))
    print(f"{len(catalog['tools'])} tools -> {out}  sha256 {catalog_digest(catalog)[:16]}")


if __name__ == "__main__":
    main()
