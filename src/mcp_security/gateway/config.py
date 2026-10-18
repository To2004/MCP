"""The gateway's routes file: upstream servers, the identity provider, and how the log is written.

    {
      "log_dir": "runs/gateway",
      "hash_key_env": "GATEWAY_LOG_KEY",
      "trusted_proxies": ["127.0.0.1/32"],
      "oauth": {"issuer": "https://idp.example", "jwks_uri": "https://idp.example/jwks",
                "public_url": "https://gateway.example", "scopes_supported": ["mcp:tools"]},
      "upstreams": {"github": {"url": "https://...", "key_env": "GITHUB_TOKEN", ...}}
    }

Who a caller is comes only from the organisation's identity provider: people sign in there,
services use client credentials, and the gateway reads the caller from the signed access
token (``oauth.py``). Nobody is named in this file. Without ``oauth`` every caller is
``anonymous`` — for local testing only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mcp_security.gateway.wire_log import BODIES

SCORING_MODES = ("inline", "background", "off")
OAUTH_KEYS = frozenset(
    {"issuer", "jwks_uri", "public_url", "algorithms", "scopes_supported", "leeway_s"}
)
OAUTH, NO_AUTH = "oauth", "none"  # how an identity was established
AGENT_ID_CHARS = 12  # an agent id: the start of SHA-256 over issuer, app and user
DEFAULT_LOG_DIR = Path("runs/gateway")
DEFAULT_HASH_KEY_ENV = "GATEWAY_LOG_KEY"


@dataclass(frozen=True)
class Identity:
    """Who sent a request, as the identity provider's signed access token says.

    ``user`` is the token's ``sub`` (the person, or the service for client credentials),
    ``app`` and ``agent`` its ``client_id`` (the agent application registered at the
    provider), ``id`` one stable key per issuer, app and user — the key for baselines and
    session ownership. Never from the wire's own say-so: the client's ``clientInfo`` is
    self-reported and logged separately as ``gateway.client``.
    """

    agent: str
    user: str | None = None
    app: str | None = None
    id: str | None = None
    auth: str = OAUTH
    issuer: str | None = None  # oauth: who signed the token
    scopes: tuple[str, ...] = ()  # oauth: what the token allows
    token_id: str | None = None  # oauth: the token's jti, for revocation and audit
    actors: tuple[str, ...] = ()  # oauth: who acts on the user's behalf (RFC 8693 act), outer first

    @property
    def key(self) -> str:
        """Whose history and sessions these are: the id, or the name when there is none."""
        return self.id or self.agent


ANONYMOUS = Identity("anonymous", auth=NO_AUTH)  # no identity provider: local testing only


@dataclass(frozen=True)
class Upstream:
    """One external MCP server, reached at ``/{name}`` on the gateway."""

    name: str
    url: str
    key_env: str | None = None  # env var holding the upstream credential; never the value
    key_header: str = "Authorization"
    key_prefix: str = "Bearer "
    scan: str | None = None  # scan artifact (cells/bands); None = record only
    kind: str | None = None  # breadth-spec kind for the runtime factor
    breadth: str | None = None  # breadth spec file for this catalog; None = the kind's default
    rules: str | None = None  # stage-2 input rules (<server>.json); None = no input level
    importance: str | None = None  # static-scan input importance: typed effect fields
    log_bodies: str = "all"  # message bodies in the log: "all", "requests" or "none"
    history: str = "route"  # runtime-factor history: one per "route", or per "caller"
    scoring: str = "inline"  # "inline" before forwarding, "background" after, or "off"
    state_file: str | None = None  # dynamic history: loaded at start, saved at shutdown
    state_every: int = 0  # also save after every N scored calls (0: only at shutdown)

    def __post_init__(self) -> None:
        if self.scoring not in SCORING_MODES:
            raise ValueError(f"upstream {self.name!r}: scoring must be one of {SCORING_MODES}")
        if self.log_bodies not in BODIES:
            raise ValueError(f"upstream {self.name!r}: log_bodies must be one of {BODIES}")


@dataclass(frozen=True)
class OAuthConfig:
    """The identity provider whose access tokens the gateway accepts (OAuth 2.1 resource
    server, as the MCP authorization spec makes an MCP server)."""

    issuer: str  # must equal the token's iss
    jwks_uri: str  # where the provider publishes its signing keys
    public_url: str  # the gateway as clients reach it; a route's resource is public_url/route
    algorithms: tuple[str, ...] = ("RS256", "ES256")
    scopes_supported: tuple[str, ...] = ()
    leeway_s: int = 30  # clock skew allowed on exp / nbf

    def resource(self, route: str) -> str:
        """A route's canonical URI: the audience its tokens must carry (RFC 8707)."""
        return f"{self.public_url.rstrip('/')}/{route}"

    def metadata_url(self, route: str) -> str:
        """Where a route's Protected Resource Metadata is served (RFC 9728, path-inserted)."""
        return f"{self.public_url.rstrip('/')}/.well-known/oauth-protected-resource/{route}"


def oauth_of(raw: dict | None) -> OAuthConfig | None:
    """The ``oauth`` section, checked: issuer, jwks_uri and public_url are required."""
    if raw is None:
        return None
    unknown = set(raw) - OAUTH_KEYS
    missing = {"issuer", "jwks_uri", "public_url"} - set(raw)
    if unknown or missing:
        raise ValueError(f"oauth: unknown keys {sorted(unknown)}, missing {sorted(missing)}")
    lists = {k: tuple(raw[k]) for k in ("algorithms", "scopes_supported") if k in raw}
    return OAuthConfig(**{**raw, **lists})


@dataclass(frozen=True)
class GatewayConfig:
    """Routes, the identity provider, and where logs go."""

    upstreams: dict[str, Upstream]
    log_dir: Path = DEFAULT_LOG_DIR
    trusted_proxies: tuple[str, ...] = ()  # addresses/CIDRs whose X-Forwarded-For is believed
    hash_key_env: str = DEFAULT_HASH_KEY_ENV  # env var holding the log's pseudonym key
    oauth: OAuthConfig | None = None  # the identity provider; None: everyone is anonymous


def load_config(path: Path) -> GatewayConfig:
    """Read the routes file. Fails loudly on a route without a URL, a bad ``oauth`` section,
    or an ``agents`` table (removed: names now come only from the identity provider)."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "agents" in raw:
        raise ValueError(
            "routes file: 'agents' is no longer supported; callers are identified by the "
            "identity provider's tokens — configure 'oauth' (services: client credentials)"
        )
    upstreams = {}
    for name, entry in raw["upstreams"].items():
        if not entry.get("url"):
            raise ValueError(f"upstream {name!r} has no url")
        upstreams[name] = Upstream(name=name, **entry)
    return GatewayConfig(
        upstreams=upstreams,
        log_dir=Path(raw.get("log_dir", DEFAULT_LOG_DIR)),
        trusted_proxies=tuple(raw.get("trusted_proxies", ())),
        hash_key_env=raw.get("hash_key_env", DEFAULT_HASH_KEY_ENV),
        oauth=oauth_of(raw.get("oauth")),
    )
