"""The identity provider for the example run, standing in for the organisation's own
(Okta, Microsoft Entra ID, Keycloak).

It does what the MCP authorization spec asks of one, and nothing more:

- metadata (RFC 8414) and a key set (JWKS) the gateway checks signatures against;
- clients registered by an administrator in advance — no self-registration, so the
  ``client_id`` in a token names an application someone vouched for;
- people sign in with the authorization-code flow and PKCE (S256); services use client
  credentials;
- the ``resource`` parameter becomes the token's audience (RFC 8707);
- JWT access tokens (RFC 9068): ``iss``, ``sub``, ``aud``, ``client_id``, ``scope``, ``jti``.

The browser step is automatic: ``signed_in`` names the person at the keyboard.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

KID = "idp-key-2026-10"
TOKEN_TTL_S = 600
SCOPE = "mcp:tools"
REDIRECT_URI = "http://127.0.0.1:9/callback"  # the agent app's registered callback
RSA_EXPONENT, RSA_BITS = 65537, 2048
#: The directory: who exists at the provider. The gateway is told none of it.
PEOPLE = {
    "alice": {"sub": "a4c9e2d1-77b0-4f5e-9c11-0d3f5a8e6b21", "department": "R&D"},
    "bob": {"sub": "0b7f13aa-2c94-4e0d-8a6f-5e19c3d70f44", "department": "Sales"},
}
SERVICE_ACCOUNTS = {"ci-bot": {"sub": "5d2e8c40-1f6a-4b37-a0e9-c4b81f2d9a73"}}
#: Applications an administrator registered: a public client for people, a service.
CLIENTS = {
    "claude-code": {"type": "public", "redirect_uris": [REDIRECT_URI]},
    "ci-bot": {"type": "confidential"},
}


class IdentityProvider:
    """One issuer: its signing key, its registered clients, its sign-ins in progress."""

    def __init__(self, issuer: str) -> None:
        self.issuer = issuer
        self.key = rsa.generate_private_key(public_exponent=RSA_EXPONENT, key_size=RSA_BITS)
        self.secrets = {
            cid: secrets.token_urlsafe(24)
            for cid, c in CLIENTS.items()
            if c["type"] == "confidential"
        }
        self.codes: dict[str, dict] = {}
        self.signed_in = "alice"

    def mint(self, sub: str, client_id: str, audience: str, ttl: int = TOKEN_TTL_S) -> str:
        """An access token as this provider issues it (also used to show refused ones)."""
        now = int(time.time())
        claims = {
            "iss": self.issuer,
            "sub": sub,
            "aud": audience,
            "client_id": client_id,
            "scope": SCOPE,
            "jti": secrets.token_hex(8),
            "iat": now,
            "exp": now + ttl,
        }
        return jwt.encode(
            claims, self.key, algorithm="RS256", headers={"kid": KID, "typ": "at+jwt"}
        )

    def app(self) -> Starlette:
        return Starlette(
            routes=[
                Route("/.well-known/oauth-authorization-server", self._metadata),
                Route("/authorize", self._authorize),
                Route("/token", self._token, methods=["POST"]),
                Route("/jwks", self._jwks),
            ]
        )

    async def _metadata(self, _: Request) -> Response:
        return JSONResponse(
            {
                "issuer": self.issuer,
                "authorization_endpoint": f"{self.issuer}/authorize",
                "token_endpoint": f"{self.issuer}/token",
                "jwks_uri": f"{self.issuer}/jwks",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "client_credentials"],
                "code_challenge_methods_supported": ["S256"],
                "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
                "scopes_supported": [SCOPE],
            }
        )

    async def _authorize(self, request: Request) -> Response:
        q = request.query_params
        client = CLIENTS.get(q.get("client_id", ""))
        if not client or q.get("redirect_uri") not in client.get("redirect_uris", []):
            return JSONResponse({"error": "unauthorized_client"}, status_code=400)
        if q.get("code_challenge_method") != "S256":
            return JSONResponse({"error": "invalid_request"}, status_code=400)
        code = secrets.token_urlsafe(16)
        self.codes[code] = {
            "sub": PEOPLE[self.signed_in]["sub"],
            "client_id": q["client_id"],
            "challenge": q["code_challenge"],
            "resource": q.get("resource"),
        }
        target = f"{q['redirect_uri']}?{urlencode({'code': code, 'state': q.get('state', '')})}"
        return RedirectResponse(target, status_code=302)

    async def _token(self, request: Request) -> Response:
        form = await request.form()
        client_id, resource = str(form.get("client_id", "")), str(form.get("resource", ""))
        if form.get("grant_type") == "client_credentials":
            if self.secrets.get(client_id) != form.get("client_secret") or not resource:
                return JSONResponse({"error": "invalid_client"}, status_code=401)
            sub = SERVICE_ACCOUNTS[client_id]["sub"]
        else:
            grant = self.codes.pop(str(form.get("code")), None)
            verifier = str(form.get("code_verifier", "")).encode()
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier).digest()).rstrip(b"=")
            if (
                not grant
                or grant["client_id"] != client_id
                or challenge.decode() != grant["challenge"]
            ):
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            sub, resource = grant["sub"], resource or grant["resource"]
        token = self.mint(sub, client_id, resource)
        return JSONResponse(
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": TOKEN_TTL_S,
                "scope": SCOPE,
            }
        )

    async def _jwks(self, _: Request) -> Response:
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key(), as_dict=True)
        return JSONResponse({"keys": [{**jwk, "kid": KID, "alg": "RS256", "use": "sig"}]})
