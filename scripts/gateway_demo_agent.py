#!/usr/bin/env python3
"""Drive an external MCP server through the gateway the way a web agent would.

Connects with the real ``mcp`` Streamable-HTTP client, lists tools, and makes a few
read-only calls on public data. ``--direct`` also fetches the catalog straight from the
upstream and checks the gateway returned the identical one — the agent cannot tell.

    GATEWAY_AGENT_TOKEN=... uv run python scripts/gateway_demo_agent.py --route deepwiki \
        --direct https://mcp.deepwiki.com/mcp
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

DEFAULT_GATEWAY = "http://127.0.0.1:8765"
PUBLIC_REPO = ("modelcontextprotocol", "python-sdk")
PREVIEW_CHARS = 90
#: Read-only calls on a public repository, per route.
PLANS: dict[str, list[tuple[str, dict]]] = {
    "github": [
        ("search_repositories", {"query": "repo:modelcontextprotocol/python-sdk"}),
        (
            "get_file_contents",
            {"owner": PUBLIC_REPO[0], "repo": PUBLIC_REPO[1], "path": "README.md"},
        ),
        ("list_issues", {"owner": PUBLIC_REPO[0], "repo": PUBLIC_REPO[1], "perPage": 5}),
        ("list_commits", {"owner": PUBLIC_REPO[0], "repo": PUBLIC_REPO[1], "perPage": 5}),
    ],
    "deepwiki": [
        ("read_wiki_structure", {"repoName": "/".join(PUBLIC_REPO)}),
        (
            "ask_wiki_question",
            {"repoName": "/".join(PUBLIC_REPO), "question": "What transports exist?"},
        ),
    ],
}


async def tool_catalog(url: str, headers: dict[str, str]) -> list[dict]:
    """The server's tools/list, as plain JSON."""
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return [tool.model_dump(mode="json") for tool in (await session.list_tools()).tools]


async def run_plan(url: str, headers: dict[str, str], plan: list[tuple[str, dict]]) -> None:
    """One agent session: initialize, list tools, then each call in the plan."""
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print(f"session open: {len(tools)} tools")
            for name, arguments in plan:
                result = await session.call_tool(name, arguments)
                text = " ".join(getattr(c, "text", "") for c in result.content)
                flag = "ERROR " if result.isError else ""
                print(f"  {name}: {flag}{text[:PREVIEW_CHARS]!r}")


def _bearer(env_var: str | None) -> dict[str, str]:
    token = os.environ.get(env_var) if env_var else None
    return {"Authorization": f"Bearer {token}"} if token else {}


def main() -> None:
    """Run the plan for ``--route`` through the gateway; optionally compare catalogs."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--route", required=True, choices=sorted(PLANS))
    parser.add_argument("--gateway", default=DEFAULT_GATEWAY)
    parser.add_argument("--direct", help="upstream URL, to check the catalogs are identical")
    parser.add_argument("--direct-key-env", help="env var with the upstream key for --direct")
    args = parser.parse_args()

    via_url = f"{args.gateway.rstrip('/')}/{args.route}"
    agent_headers = _bearer("GATEWAY_AGENT_TOKEN")
    asyncio.run(run_plan(via_url, agent_headers, PLANS[args.route]))
    if args.direct:
        via = asyncio.run(tool_catalog(via_url, agent_headers))
        direct = asyncio.run(tool_catalog(args.direct, _bearer(args.direct_key_env)))
        same = json.dumps(via, sort_keys=True) == json.dumps(direct, sort_keys=True)
        print(f"catalog via gateway == direct: {same} ({len(via)} tools)")


if __name__ == "__main__":
    main()
