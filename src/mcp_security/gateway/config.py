"""The gateway's routes file: upstream servers, known agents, and how the log is written.

    {
      "log_dir": "runs/gateway",
      "hash_key_env": "GATEWAY_LOG_KEY",
      "trusted_proxies": ["127.0.0.1/32"],
      "agents": {"<sha256 of token>": {"id": "agt-17", "agent": "ci-bot", "user": "u-0417",
                                       "app": "ci"}},
      "oauth": {"issuer": "https://idp.example", "jwks_uri": "https://idp.example/jwks",
                "public_url": "https://gateway.example", "scopes_supported": ["mcp:tools"]},
      "upstreams": {"github": {"url": "https://...", "key_env": "GITHUB_TOKEN", ...}}
    }

An ``agents`` entry may also be a plain name (``"<sha256>": "alice"``), as before. With
``oauth`` set, a caller nobody listed signs in at the identity provider instead, and the
gateway reads who it is from the signed token (``oauth.py``); both can be used together.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from mcp_security.gateway.wire_log import BODIES

SCORING_MODES = ("inline", "background", "off")
IDENTITY_KEYS = frozenset({"id", "agent", "user", "app"})
OAUTH_KEYS = frozenset(
    {"issuer", "jwks_uri", "public_url", "algorithms", "scopes_supported", "leeway_s"}
)
TOKEN_TABLE, OAUTH, NO_AUTH = "token", "oauth", "none"  # how an identity was established
AGENT_ID_CHARS = 12  # default agent id: the start of the token's SHA-256 (GitHub logs the same)
DEFAULT_LOG_DIR = Path("runs/gateway")
DEFAULT_HASH_KEY_ENV = "GATEWAY_LOG_KEY"


@dataclass(frozen=True)
class Identity:
    """Who a gateway token belongs to: its id, the agent's name, the user it acts for, its app.

    Never from the wire's own say-so: either the gateway hashes the bearer token and looks
    the hash up in ``agents`` (``auth`` = ``token``), or the token is an access token signed
    by the identity provider and the gateway reads it (``auth`` = ``oauth``: ``user`` is its
    ``sub``, ``app`` its ``client_id``). The client's own ``clientInfo`` is self-reported and
    logged separately as ``gateway.client``. ``id`` is the stable key for baselines: one per
    user and app. Use a pseudonym for ``user`` in the table, not an e-mail address.
    """

    agent: str
    user: str | None = None
    app: str | None = None
    id: str | None = None
    auth: str = TOKEN_TABLE
    issuer: str | None = None  # oauth: who signed the token
    scopes: tuple[str, ...] = ()  # oauth: what the token allows
    token_id: str | None = None  # oauth: the token's jti, for revocation and audit
    actors: tuple[str, ...] = ()  # oauth: who acts on the user's behalf (RFC 8693 act), outer first

    @property
    def key(self) -> str:
        """Whose history and sessions these are: the id, or the name when there is none."""
        return self.id or self.agent


ANONYMOUS = Identity("anonymous", auth=NO_AUTH)  # no agents, no oauth: local demo only


def identity_of(entry: str | dict, token_digest: str | None = None) -> Identity:
    """An ``agents`` entry (keyed by ``token_digest``) as an Identity; fails loudly on an
    entry it cannot read."""
    default_id = token_digest[:AGENT_ID_CHARS] if token_digest else None
    if isinstance(entry, str):
        return Identity(entry, id=default_id)
    if not isinstance(entry, dict) or not entry.get("agent"):
        raise ValueError(f"an agents entry needs an 'agent' name: {entry!r}")
    unknown = set(entry) - IDENTITY_KEYS
    if unknown:
        raise ValueError(f"unknown keys in agents entry {entry['agent']!r}: {sorted(unknown)}")
    agent_id = entry.get("id") or default_id
    return Identity(entry["agent"], entry.get("user"), entry.get("app"), agent_id)


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
    """Routes, known agents (by SHA-256 of their gateway token), and where logs go."""

    upstreams: dict[str, Upstream]
    agents: dict[str, str | dict] = field(default_factory=dict)  # empty = no agent auth (demo)
    log_dir: Path = DEFAULT_LOG_DIR
    trusted_proxies: tuple[str, ...] = ()  # addresses/CIDRs whose X-Forwarded-For is believed
    hash_key_env: str = DEFAULT_HASH_KEY_ENV  # env var holding the log's pseudonym key
    oauth: OAuthConfig | None = None  # accept the identity provider's access tokens


def load_config(path: Path) -> GatewayConfig:
    """Read the routes file. Fails loudly on a route without a URL or a bad agents entry."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    upstreams = {}
    for name, entry in raw["upstreams"].items():
        if not entry.get("url"):
            raise ValueError(f"upstream {name!r} has no url")
        upstreams[name] = Upstream(name=name, **entry)
    agents = dict(raw.get("agents", {}))
    for digest, entry in agents.items():
        identity_of(entry, digest)
    return GatewayConfig(
        upstreams=upstreams,
        agents=agents,
        log_dir=Path(raw.get("log_dir", DEFAULT_LOG_DIR)),
        trusted_proxies=tuple(raw.get("trusted_proxies", ())),
        hash_key_env=raw.get("hash_key_env", DEFAULT_HASH_KEY_ENV),
        oauth=oauth_of(raw.get("oauth")),
    )


def token_hash(token: str) -> str:
    """How an agent token is stored in the config: its SHA-256, never the token."""
    return hashlib.sha256(token.encode()).hexdigest()
