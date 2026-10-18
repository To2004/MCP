"""OAuth: every caller signs in at the identity provider; the signed token says who it is."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp_security.gateway.log_file import read_log
from mcp_security.gateway.oauth import actor_chain
from mcp_security.gateway.proxy import GatewayConfig, Upstream, create_app
from tests.gateway.tokens import (
    GATEWAY,
    ISSUER,
    OAUTH,
    OTHER_KEY,
    RESOURCE,
    bearer,
    mint,
    verifier,
)

USER = "5f0c1e6a-user"
CALL = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "list_commits", "arguments": {"repo": "r"}},
}


def _token(**claims: object) -> str:
    return mint(**{"sub": USER, **claims})


@pytest.fixture
def seen_headers() -> list[dict[str, str]]:
    return []


@pytest.fixture
def gateway(
    tmp_path: Path, seen_headers: list[dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> httpx.AsyncClient:
    async def mcp(request: Request) -> Response:
        seen_headers.append({k.lower(): v for k, v in request.headers.items()})
        reply = {"jsonrpc": "2.0", "id": 2, "result": {"content": []}}
        return JSONResponse(reply, headers={"mcp-session-id": "s-1"})

    upstream = Starlette(routes=[Route("/mcp", mcp, methods=["POST"])])
    monkeypatch.setenv("UPSTREAM_KEY", "upstream-secret")
    config = GatewayConfig(
        upstreams={"github": Upstream(name="github", url="http://up/mcp", key_env="UPSTREAM_KEY")},
        log_dir=tmp_path,
        oauth=OAUTH,
    )
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream))
    app = create_app(config, client=client, verifier=verifier())
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=GATEWAY)


async def test_the_caller_is_named_by_the_signed_token(
    gateway: httpx.AsyncClient, tmp_path: Path, seen_headers: list[dict[str, str]]
) -> None:
    token = _token()
    reply = await gateway.post("/github", json=CALL, headers=bearer(token))

    assert reply.status_code == 200
    request = read_log(tmp_path / "github.jsonl")[0]
    assert (request["user.id"], request["gateway.app"], request["gateway.agent"]) == (
        USER,
        "claude-code",
        "claude-code",
    )
    assert (request["gateway.auth"], request["gateway.issuer"]) == ("oauth", ISSUER)
    assert (request["gateway.scopes"], request["gateway.token_id"]) == (["mcp:tools"], "tok-81")
    expected_id = hashlib.sha256(f"{ISSUER}|claude-code|{USER}".encode()).hexdigest()
    assert request["gateway.agent_id"] == expected_id[:12]
    assert seen_headers[-1]["authorization"] == "Bearer upstream-secret"  # never passed through
    assert token not in (tmp_path / "github.jsonl").read_text()


@pytest.mark.parametrize(
    ("token", "reason"),
    [
        (lambda: _token(exp=int(time.time()) - 3600), "token_expired"),
        (lambda: _token(aud=f"{GATEWAY}/other"), "wrong_audience"),  # minted for another server
        (lambda: _token(iss="https://evil.example"), "wrong_issuer"),
        (lambda: _token(key=OTHER_KEY), "bad_signature"),  # right kid, forged with another key
        (lambda: _token(kid="key-9"), "unknown_signing_key"),
        (lambda: _token(client_id=None), "missing_claim"),
        (lambda: _token(sub=None), "missing_claim"),
        (lambda: "not.a.jwt", "invalid_token"),
        (lambda: "random-opaque-token", "invalid_token"),  # not even a JWT
    ],
)
async def test_a_bad_token_is_refused_with_its_reason(
    gateway: httpx.AsyncClient, tmp_path: Path, token, reason: str
) -> None:
    reply = await gateway.post("/github", json=CALL, headers=bearer(token()))

    assert reply.status_code == 401
    assert 'error="invalid_token"' in reply.headers["www-authenticate"]
    [refused] = read_log(tmp_path / "github.jsonl")
    assert (refused["gateway.notice"], refused["gateway.reason"]) == ("auth_failed", reason)


async def test_a_401_tells_the_client_where_to_sign_in(gateway: httpx.AsyncClient) -> None:
    reply = await gateway.post("/github", json=CALL)

    challenge = reply.headers["www-authenticate"]
    assert reply.status_code == 401
    assert f'resource_metadata="{GATEWAY}/.well-known/oauth-protected-resource/github"' in challenge
    assert 'scope="mcp:tools"' in challenge and "error=" not in challenge  # no token: no error

    metadata = (await gateway.get("/.well-known/oauth-protected-resource/github")).json()
    assert metadata["resource"] == RESOURCE
    assert metadata["authorization_servers"] == [ISSUER]
    assert (await gateway.get("/.well-known/oauth-protected-resource/nowhere")).status_code == 404


async def test_delegation_is_logged_as_the_actor_chain(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    act = {"sub": "assistant-svc", "act": {"sub": "orchestrator"}}
    await gateway.post("/github", json=CALL, headers=bearer(_token(act=act)))

    assert read_log(tmp_path / "github.jsonl")[0]["gateway.act"] == [
        "assistant-svc",
        "orchestrator",
    ]
    assert actor_chain(None) == ()


async def test_two_users_of_one_app_do_not_share_a_session(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=CALL, headers=bearer(_token(sub="user-a")))
    other = bearer(_token(sub="user-b"), **{"mcp-session-id": "s-1"})
    await gateway.post("/github", json=CALL, headers=other)

    [notice] = [r for r in read_log(tmp_path / "github.jsonl") if r.get("gateway.notice")]
    assert notice["gateway.notice"] == "session_agent_mismatch"
    assert notice["user.id"] == "user-b"  # same app, same name: told apart by the user
