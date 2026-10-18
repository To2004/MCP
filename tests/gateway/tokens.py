"""A test identity provider held in memory: one signing key, its key set, tokens on demand.

The gateway's tests sign callers in the way a deployment does — with an access token the
provider signed — instead of listing them anywhere. ``verifier()`` checks tokens against
this key set without any network.
"""

from __future__ import annotations

import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from mcp_security.gateway.config import OAuthConfig
from mcp_security.gateway.oauth import TokenVerifier

ISSUER = "https://idp.example"
GATEWAY = "http://gw"
ROUTE = "github"
RESOURCE = f"{GATEWAY}/{ROUTE}"
KID = "key-1"
APP = "claude-code"  # the agent application, registered at the provider
TOKEN_TTL_S = 300
RSA_EXPONENT, RSA_BITS = 65537, 2048
OAUTH = OAuthConfig(
    issuer=ISSUER,
    jwks_uri=f"{ISSUER}/jwks",
    public_url=GATEWAY,
    scopes_supported=("mcp:tools",),
)


def new_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=RSA_EXPONENT, key_size=RSA_BITS)


SIGNING_KEY, OTHER_KEY = new_key(), new_key()


class FixedKeys:
    """The provider's published key set, in memory: what ``jwt.PyJWKClient`` would fetch."""

    def __init__(self, key: rsa.RSAPrivateKey) -> None:
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
        self._set = jwt.PyJWKSet.from_dict({"keys": [{**jwk, "kid": KID, "alg": "RS256"}]})

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        kid = jwt.get_unverified_header(token).get("kid")
        try:
            return self._set[kid]
        except KeyError as exc:
            raise jwt.PyJWKClientError(f"no key {kid}") from exc


def mint(
    sub: str | None = "alice-sub",
    key: rsa.RSAPrivateKey = SIGNING_KEY,
    kid: str = KID,
    **claims: object,
) -> str:
    """An access token as the provider would issue it; a claim set to None is left out."""
    now = int(time.time())
    body = {
        "iss": ISSUER,
        "aud": RESOURCE,
        "sub": sub,
        "client_id": APP,
        "scope": "mcp:tools",
        "jti": "tok-81",
        "iat": now,
        "exp": now + TOKEN_TTL_S,
        **claims,
    }
    body = {k: v for k, v in body.items() if v is not None}
    return jwt.encode(body, key, algorithm="RS256", headers={"kid": kid})


def verifier() -> TokenVerifier:
    return TokenVerifier(OAUTH, FixedKeys(SIGNING_KEY))


def bearer(token: str, **headers: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}", **headers}
