"""Make the example log: one gateway run on the remote GitHub MCP with every kind of line.

Nobody is named in the gateway's config: every caller signs in at the identity provider
(``identity_provider.py``, standing in for the organisation's own) and the gateway reads who
it is from the signed token. The run:

1. alice signs in with ``claude-code`` (the stock ``mcp`` OAuth client: 401, discovery,
   authorization code with PKCE, token) and makes read-only calls on a public repository —
   one ends in a tool error, one names a tool that does not exist — then ends her session;
2. the ``ci-bot`` service gets a token with client credentials and makes one call;
3. bob signs in with ``claude-code`` and makes one call, then sends one on alice's ended
   session;
4. a token that expired, a token minted for another server, and a request to a route the
   gateway does not have.

Writes ``github.jsonl`` and ``_gateway.jsonl`` here, replacing them, and the two readable
views of the log (``log_view.py``).

    uv run python reports/experiments/gateway/log_example/make_example.py   # needs `gh` login
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import uvicorn
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from mcp.shared.exceptions import McpError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_provider import REDIRECT_URI, SCOPE, IdentityProvider  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "routes.json"
LOG_FILES = ("github.jsonl", "_gateway.jsonl")
#: The same log rendered for reading (log_view.py): one line per event, and by session.
VIEWS = {"github_view.txt": [], "github_grouped.txt": ["--grouped"]}
IDP_PORT, GATEWAY_PORT = 18800, 18781  # must match routes.json
ISSUER = f"http://127.0.0.1:{IDP_PORT}"
ROUTE_URL = f"http://127.0.0.1:{GATEWAY_PORT}/github"
APP, SERVICE = "claude-code", "ci-bot"
LOG_KEY = "example-key"  # GATEWAY_LOG_KEY for the run: pseudonyms are keyed HMACs
PROTOCOL = "2025-11-25"
START_TRIES, START_WAIT_S, STOP_WAIT_S, HTTP_TIMEOUT_S = 100, 0.1, 20, 30
EXPIRED_S = -3600
REPO = {"owner": "modelcontextprotocol", "repo": "python-sdk"}
ALICE_PLAN = [
    ("search_repositories", {"query": "repo:modelcontextprotocol/python-sdk"}),
    ("get_file_contents", {**REPO, "path": "README.md"}),
    (
        "list_commits",
        {**REPO, "perPage": 3, "since": "2026-09-01T00:00:00Z", "until": "2026-10-01T00:00:00Z"},
    ),
    ("get_file_contents", {**REPO, "path": "no-such-file.md"}),  # the tool reports an error
    ("no_such_tool", {}),  # JSON-RPC -32602: the caller's mistake
]
BOT_PLAN = [("list_pull_requests", {**REPO, "perPage": 2})]
BOB_PLAN = [("list_issues", {**REPO, "perPage": 2})]
ONE_CALL = {
    "jsonrpc": "2.0",
    "id": 99,
    "method": "tools/call",
    "params": {"name": "list_commits", "arguments": {**REPO, "perPage": 1}},
}


class TokenStore:
    """What an installed agent app keeps: its registration and the signed-in user's token."""

    def __init__(self) -> None:
        self.tokens: OAuthToken | None = None
        self.client = OAuthClientInformationFull(  # registered by an administrator
            client_id=APP, redirect_uris=[REDIRECT_URI], token_endpoint_auth_method="none"
        )

    async def get_tokens(self) -> OAuthToken | None:
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self.client

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client = client_info


def sign_in(store: TokenStore) -> OAuthClientProvider:
    """The SDK's own OAuth client; only the browser is automated (open the sign-in page,
    catch the redirect's code)."""
    caught: dict[str, str] = {}

    async def open_browser(url: str) -> None:
        async with httpx.AsyncClient() as browser:
            reply = await browser.get(url, follow_redirects=False)
        query = parse_qs(urlparse(reply.headers["location"]).query)
        caught.update(code=query["code"][0], state=query.get("state", [""])[0])

    async def redirected() -> tuple[str, str | None]:
        return caught["code"], caught["state"]

    metadata = OAuthClientMetadata(redirect_uris=[REDIRECT_URI], scope=SCOPE)
    return OAuthClientProvider(ROUTE_URL, metadata, store, open_browser, redirected)


async def session(label: str, plan: list, auth=None, headers: dict | None = None) -> str:
    """One MCP session: initialize, list tools, run the plan. Returns its session id."""
    async with streamablehttp_client(ROUTE_URL, headers=headers, auth=auth) as (read, write, sid):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()
            print(f"{label}: {len((await mcp.list_tools()).tools)} tools")
            for tool, args in plan:
                try:
                    result = await mcp.call_tool(tool, args)
                    print(f"{label}: {tool:<20} isError={result.isError}")
                except McpError as exc:
                    print(f"{label}: {tool:<20} JSON-RPC error {exc.error.code}")
            return sid()


async def service_token(idp: IdentityProvider) -> str:
    """ci-bot's token, by client credentials — no person, no browser."""
    form = {
        "grant_type": "client_credentials",
        "client_id": SERVICE,
        "client_secret": idp.secrets[SERVICE],
        "resource": ROUTE_URL,
        "scope": SCOPE,
    }
    async with httpx.AsyncClient() as http:
        reply = await http.post(f"{ISSUER}/token", data=form)
    reply.raise_for_status()
    return reply.json()["access_token"]


async def raw_call(path: str, token: str, session_id: str | None = None) -> int:
    headers = {
        "content-type": "application/json",
        "accept": "application/json, text/event-stream",
        "mcp-protocol-version": PROTOCOL,
        "authorization": f"Bearer {token}",
    }
    if session_id:
        headers["mcp-session-id"] = session_id
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as http:
        reply = await http.post(
            f"http://127.0.0.1:{GATEWAY_PORT}{path}", json=ONE_CALL, headers=headers
        )
    return reply.status_code


async def run(idp: IdentityProvider) -> None:
    idp.signed_in = "alice"
    alice_session = await session("alice (claude-code)", ALICE_PLAN, auth=sign_in(TokenStore()))
    bot = await service_token(idp)
    await session("ci-bot (service)", BOT_PLAN, headers={"Authorization": f"Bearer {bot}"})
    idp.signed_in = "bob"
    bob = TokenStore()
    await session("bob (claude-code)", BOB_PLAN, auth=sign_in(bob))
    bob_token = bob.tokens.access_token if bob.tokens else ""
    print(f"bob on alice's ended session: {await raw_call('/github', bob_token, alice_session)}")
    alice_sub = "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21"
    expired = idp.mint(alice_sub, APP, ROUTE_URL, ttl=EXPIRED_S)
    print(f"expired token: {await raw_call('/github', expired)}")
    elsewhere = idp.mint(alice_sub, APP, f"http://127.0.0.1:{GATEWAY_PORT}/slack")
    print(f"token minted for another server: {await raw_call('/github', elsewhere)}")
    print(f"unknown route: {await raw_call('/gitlab', bob_token)}")


async def main() -> None:
    """Start the provider and the gateway, run the callers, stop both, render the views."""
    for name in LOG_FILES:
        (HERE / name).unlink(missing_ok=True)
    idp = IdentityProvider(ISSUER)
    server = uvicorn.Server(
        uvicorn.Config(idp.app(), host="127.0.0.1", port=IDP_PORT, log_level="warning")
    )
    idp_task = asyncio.create_task(server.serve())
    github_token = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True
    ).stdout.strip()
    env = os.environ | {"GATEWAY_LOG_KEY": LOG_KEY, "GITHUB_TOKEN": github_token}
    command = [sys.executable, "-m", "mcp_security.gateway.proxy", "--config", str(CONFIG)]
    gateway = subprocess.Popen(
        [*command, "--port", str(GATEWAY_PORT)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        await _wait_for_port(GATEWAY_PORT)
        await run(idp)
    finally:
        gateway.send_signal(signal.SIGINT)  # uvicorn shuts down: lifespan logs gateway_stopped
        gateway.communicate(timeout=STOP_WAIT_S)
        server.should_exit = True
        await idp_task
    log = os.path.relpath(HERE / LOG_FILES[0])  # the views name the log as the reader runs them
    view = [sys.executable, "-m", "mcp_security.gateway.log_view", log]
    for name, flags in VIEWS.items():
        subprocess.run([*view, *flags, "--out", str(HERE / name)], check=True)


async def _wait_for_port(port: int) -> None:
    for _ in range(START_TRIES):
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            return
        except OSError:
            await asyncio.sleep(START_WAIT_S)
    raise RuntimeError(f"gateway did not open port {port}")


if __name__ == "__main__":
    asyncio.run(main())
