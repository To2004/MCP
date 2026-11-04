#!/usr/bin/env python3
"""Drive an external MCP server through the gateway the way a web agent would.

Connects with the real ``mcp`` Streamable-HTTP client, lists tools, and makes a few
read-only calls on public data. ``--direct`` also fetches the catalog straight from the
upstream and checks the gateway returned the identical one — the agent cannot tell.
``--protocol modern`` starts each connection with the stateless 2026-07-28 protocol
(``server/discover``, no session) instead of the ``initialize`` handshake; the upstream has
to speak it.

    GATEWAY_AGENT_TOKEN=<access token from the identity provider> \
        uv run python scripts/gateway_demo_agent.py --route deepwiki \
        --direct https://mcp.deepwiki.com/mcp
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os

from mcp_security.agent_session import LEGACY, PROTOCOL_HELP, PROTOCOLS, agent_session

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


async def tool_catalog(url: str, headers: dict[str, str], protocol: str) -> list[dict]:
    """The server's tools/list, as plain JSON (the wire's camelCase field names)."""
    async with agent_session(url, protocol=protocol, headers=headers) as session:
        tools = (await session.list_tools()).tools
        return [tool.model_dump(mode="json", by_alias=True) for tool in tools]


async def run_plan(
    url: str, headers: dict[str, str], plan: list[tuple[str, dict]], protocol: str
) -> None:
    """One agent session: start it (``--protocol``), list tools, then each call in the plan."""
    async with agent_session(url, protocol=protocol, headers=headers) as session:
        tools = (await session.list_tools()).tools
        print(f"session open: {len(tools)} tools")
        for name, arguments in plan:
            result = await session.call_tool(name, arguments)
            text = " ".join(getattr(c, "text", "") for c in result.content)
            flag = "ERROR " if result.is_error else ""
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
    parser.add_argument(
        "--protocol",
        choices=PROTOCOLS,
        default=LEGACY,
        help=PROTOCOL_HELP,
    )
    args = parser.parse_args()

    via_url = f"{args.gateway.rstrip('/')}/{args.route}"
    agent_headers = _bearer("GATEWAY_AGENT_TOKEN")
    asyncio.run(run_plan(via_url, agent_headers, PLANS[args.route], args.protocol))
    if args.direct:
        via = asyncio.run(tool_catalog(via_url, agent_headers, args.protocol))
        direct_headers = _bearer(args.direct_key_env)
        direct = asyncio.run(tool_catalog(args.direct, direct_headers, args.protocol))
        same = json.dumps(via, sort_keys=True) == json.dumps(direct, sort_keys=True)
        print(f"catalog via gateway == direct: {same} ({len(via)} tools)")


if __name__ == "__main__":
    main()
