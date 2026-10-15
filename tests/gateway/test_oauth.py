"""OAuth: a caller nobody listed signs in at the identity provider; the token says who it is."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp_security.gateway.config import OAuthConfig
from mcp_security.gateway.log_file import read_log
from mcp_security.gateway.oauth import TokenVerifier, actor_chain
from mcp_security.gateway.proxy import GatewayConfig, Upstream, create_app

ISSUER = "https://idp.example"
GATEWAY = "http://gw"
RESOURCE = f"{GATEWAY}/github"
KID = "key-1"
LISTED_TOKEN = "ci-bot-token"
CALL = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "list_commits", "arguments": {"repo": "r"}},
}
OAUTH = OAuthConfig(
    issuer=ISSUER,
    jwks_uri=f"{ISSUER}/jwks",
    public_url=GATEWAY,
    scopes_supported=("mcp:tools",),
)


def _key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


SIGNING_KEY, OTHER_KEY = _key(), _key()


class FixedKeys:
    """The provider's JWKS, held in memory: what ``jwt.PyJWKClient`` would have fetched."""

    def __init__(self, key: rsa.RSAPrivateKey) -> None:
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
        self._set = jwt.PyJWKSet.from_dict({"keys": [{**jwk, "kid": KID, "alg": "RS256"}]})

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        kid = jwt.get_unverified_header(token).get("kid")
        try:
            return self._set[kid]
        except KeyError as exc:
            raise jwt.PyJWKClientError(f"no key {kid}") from exc


def _token(key: rsa.RSAPrivateKey = SIGNING_KEY, kid: str = KID, **claims: object) -> str:
    now = int(time.time())
    body = {
        "iss": ISSUER,
        "aud": RESOURCE,
        "sub": "5f0c1e6a-user",
        "client_id": "claude-code",
        "scope": "mcp:tools",
        "jti": "tok-81",
        "iat": now,
        "exp": now + 300,
        **claims,
    }
    body = {k: v for k, v in body.items() if v is not None}
    return jwt.encode(body, key, algorithm="RS256", headers={"kid": kid})


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
        agents={hashlib.sha256(LISTED_TOKEN.encode()).hexdigest(): "ci-bot"},
        log_dir=tmp_path,
        oauth=OAUTH,
    )
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=upstream))
    app = create_app(config, client=client, verifier=TokenVerifier(OAUTH, FixedKeys(SIGNING_KEY)))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=GATEWAY)


def _bearer(token: str, **headers: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}", **headers}


async def test_a_caller_nobody_listed_is_named_by_the_token(
    gateway: httpx.AsyncClient, tmp_path: Path, seen_headers: list[dict[str, str]]
) -> None:
    token = _token()
    reply = await gateway.post("/github", json=CALL, headers=_bearer(token))

    assert reply.status_code == 200
    request = read_log(tmp_path / "github.jsonl")[0]
    assert (request["user.id"], request["gateway.app"], request["gateway.agent"]) == (
        "5f0c1e6a-user",
        "claude-code",
        "claude-code",
    )
    assert (request["gateway.auth"], request["gateway.issuer"]) == ("oauth", ISSUER)
    assert (request["gateway.scopes"], request["gateway.token_id"]) == (["mcp:tools"], "tok-81")
    expected_id = hashlib.sha256(f"{ISSUER}|claude-code|5f0c1e6a-user".encode()).hexdigest()
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
        (lambda: "random-opaque-token", "unknown_token"),
    ],
)
async def test_a_bad_token_is_refused_with_its_reason(
    gateway: httpx.AsyncClient, tmp_path: Path, token, reason: str
) -> None:
    reply = await gateway.post("/github", json=CALL, headers=_bearer(token()))

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
    await gateway.post("/github", json=CALL, headers=_bearer(_token(act=act)))

    assert read_log(tmp_path / "github.jsonl")[0]["gateway.act"] == [
        "assistant-svc",
        "orchestrator",
    ]
    assert actor_chain(None) == ()


async def test_two_users_of_one_app_do_not_share_a_session(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    await gateway.post("/github", json=CALL, headers=_bearer(_token(sub="user-a")))
    other = _bearer(_token(sub="user-b"), **{"mcp-session-id": "s-1"})
    await gateway.post("/github", json=CALL, headers=other)

    [notice] = [r for r in read_log(tmp_path / "github.jsonl") if r.get("gateway.notice")]
    assert notice["gateway.notice"] == "session_agent_mismatch"
    assert notice["user.id"] == "user-b"  # same app, same name: told apart by the user


async def test_a_listed_token_still_works_beside_oauth(
    gateway: httpx.AsyncClient, tmp_path: Path
) -> None:
    reply = await gateway.post("/github", json=CALL, headers=_bearer(LISTED_TOKEN))

    assert reply.status_code == 200
    request = read_log(tmp_path / "github.jsonl")[0]
    assert (request["gateway.agent"], request["gateway.auth"]) == ("ci-bot", "token")
