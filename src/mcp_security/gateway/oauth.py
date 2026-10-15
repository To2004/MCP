"""The gateway as an OAuth 2.1 resource server: who a caller is, read from a signed token.

With an identity provider configured (``config.OAuthConfig``), an agent nobody listed
signs in there — the MCP authorization flow — and sends ``Authorization: Bearer <JWT>``.
The gateway checks the token: the signature against the provider's published keys
(JWKS), the issuer, the audience (it must name this route: RFC 8707, so a token minted for
another server is refused), and the expiry. Then it reads the caller from the token
(RFC 9068 claims): ``sub`` is the user, ``client_id`` the agent application, ``scope``
what it may do, ``jti`` the token's id, and ``act`` (RFC 8693) who acts on whose behalf.

The gateway also says where to sign in: each route's Protected Resource Metadata
(RFC 9728) names the provider, and every 401 points to it in ``WWW-Authenticate``, so a
stock MCP client finds its way without being told. The token is never sent upstream.
"""

from __future__ import annotations

import hashlib
from typing import Protocol

import jwt

from mcp_security.gateway.config import AGENT_ID_CHARS, OAUTH, Identity, OAuthConfig

KEY_CACHE_S = 300  # how long fetched signing keys are reused before the JWKS is read again
JWT_PARTS = 3  # header.payload.signature
REQUIRED_CLAIMS = ["exp", "iss", "aud", "sub"]
NO_TOKEN = "no_bearer_token"


class AuthError(Exception):
    """A request the gateway refuses; ``reason`` is what the log records."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SigningKeys(Protocol):
    """Where verification keys come from: ``jwt.PyJWKClient`` live, a fixed set in tests."""

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


def looks_like_jwt(token: str) -> bool:
    """A JWT has three dot-separated parts; a table token is one random string."""
    return token.count(".") == JWT_PARTS - 1


class TokenVerifier:
    """Checks an access token for one route and returns the caller it names."""

    def __init__(self, config: OAuthConfig, keys: SigningKeys | None = None) -> None:
        self.config = config
        self._keys = keys or jwt.PyJWKClient(config.jwks_uri, cache_keys=True, lifespan=KEY_CACHE_S)

    def verify(self, token: str, route: str) -> Identity:
        """The caller this token names, or ``AuthError`` with why it is refused. Blocking on
        a key-cache miss (the JWKS is fetched): call it off the event loop."""
        try:
            key = self._keys.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=list(self.config.algorithms),
                audience=self.config.resource(route),
                issuer=self.config.issuer,
                leeway=self.config.leeway_s,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("token_expired") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthError("wrong_audience") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthError("wrong_issuer") from exc
        except jwt.MissingRequiredClaimError as exc:
            raise AuthError("missing_claim") from exc
        except jwt.InvalidSignatureError as exc:
            raise AuthError("bad_signature") from exc
        except jwt.PyJWKClientError as exc:
            raise AuthError("unknown_signing_key") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("invalid_token") from exc
        return identity_from_claims(claims)

    def metadata(self, route: str) -> dict:
        """The route's Protected Resource Metadata (RFC 9728)."""
        document = {
            "resource": self.config.resource(route),
            "authorization_servers": [self.config.issuer],
            "bearer_methods_supported": ["header"],
            "resource_name": route,
        }
        if self.config.scopes_supported:
            document["scopes_supported"] = list(self.config.scopes_supported)
        return document

    def challenge(self, route: str, reason: str) -> str:
        """The ``WWW-Authenticate`` value for a 401: where to sign in, and — for a token
        that was sent but refused — ``error="invalid_token"`` (RFC 6750)."""
        parts = [f'resource_metadata="{self.config.metadata_url(route)}"']
        if self.config.scopes_supported:
            parts.append(f'scope="{" ".join(self.config.scopes_supported)}"')
        if reason != NO_TOKEN:
            parts.append('error="invalid_token"')
        return "Bearer " + ", ".join(parts)


def identity_from_claims(claims: dict) -> Identity:
    """The caller a verified token names. ``id`` is one per issuer, app and user, so each
    user of each agent application gets a baseline of its own."""
    client = claims.get("client_id") or claims.get("azp")
    if not client:
        raise AuthError("missing_claim")
    user, issuer = str(claims["sub"]), str(claims["iss"])
    agent_id = hashlib.sha256(f"{issuer}|{client}|{user}".encode()).hexdigest()[:AGENT_ID_CHARS]
    return Identity(
        agent=str(client),
        user=user,
        app=str(client),
        id=agent_id,
        auth=OAUTH,
        issuer=issuer,
        scopes=tuple(str(claims.get("scope", "")).split()),
        token_id=str(claims["jti"]) if claims.get("jti") else None,
        actors=actor_chain(claims.get("act")),
    )


def actor_chain(act: object) -> tuple[str, ...]:
    """RFC 8693 ``act``: the acting party, then whoever acts for it, outermost first."""
    chain: list[str] = []
    while isinstance(act, dict) and act.get("sub"):
        chain.append(str(act["sub"]))
        act = act.get("act")
    return tuple(chain)
