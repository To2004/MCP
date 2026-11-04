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

v5's route and sign-in fields (spec 2.9, 4.3), each off or unchanged at its default:

- B1 ``baseline_key``: whose history a call extends (:func:`baseline_mode`). v5 keeps it per
  agent: the signed-in agent, else the agent's reported client name and address (D5). The
  opt-in ``"user"`` keys it per person through ``oauth.user_claim`` (Entra: ``"oid"``);
- B9d ``zone_map`` and ``oauth.zone_claim``: the caller's zone, from a directory map
  (:func:`load_zone_map`), else the token's claim, else ``route_zone`` (``oauth.ZoneResolver``);
- B10 ``shared_egress``: a per-platform egress table whose entries are marked verified or
  UNVERIFIED (``egress/table.py``; :func:`route_egress_table`, :func:`route_shared_networks`);
- PS7 ``legacy_gate``, PS9 ``upstream_audit_header`` (:func:`with_audit_header`), PS10
  ``pseudonymize_origin`` and ``log_origin``.

DEP-8 (revised 2026-10-27, D5): a v5 route without sign-in runs in full, each caller keyed by
its reported client name and address (``oauth.reported_key``), so there is no refusal switch.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import MISSING, asdict, dataclass, fields
from pathlib import Path
from types import MappingProxyType

from mcp_security.behaviour.clock import zone
from mcp_security.behaviour.engine import V5
from mcp_security.gateway.egress.table import EgressTable, load_egress_table
from mcp_security.gateway.wire_log import BODIES

SCORING_MODES = ("inline", "background", "off")
OAUTH_KEYS = frozenset(
    {
        "issuer",
        "jwks_uri",
        "public_url",
        "algorithms",
        "scopes_supported",
        "leeway_s",
        "user_claim",
        "zone_claim",
    }
)
#: B1: whose baseline a call extends.
#: - "agent" (v5, revised 2026-10-27, D5: deployments have no user ids, at most an agent id):
#:   the signed-in agent, SHA-256(iss|app|user) (``Identity.id``), and, for a caller that did
#:   not sign in, its reported client name and address (``oauth.reported_key``).
#: - "user" (opt-in, for tokens that name people): SHA-256(iss|user claim), so one person
#:   keeps one history across agent applications.
#: - "user_app" (v1-v4): ``Identity.id`` too, but every caller without sign-in shares the one
#:   "anonymous" history.
BASELINE_AGENT, BASELINE_USER, BASELINE_USER_APP = "agent", "user", "user_app"
BASELINE_KEYS = (BASELINE_AGENT, BASELINE_USER, BASELINE_USER_APP)
DEFAULT_USER_CLAIM = "sub"
#: B1: claims that name the token, the application, the tenant, the session or a group, never
#: one person. A per-person key on one of them would split a person by application or session
#: again, or merge many people (a tenant, a role) into one history.
NOT_USER_CLAIMS = frozenset(
    "iss aud exp nbf iat jti nonce auth_time acr amr cnf ver uti "  # the token itself
    "client_id azp appid cid act may_act "  # the application, and who acts for it
    "scope scp roles groups wids "  # what it may do; groups of people
    "tid sid idp".split()  # the tenant, the sign-in session, the upstream provider
)
OAUTH, NO_AUTH = "oauth", "none"  # how an identity was established
AGENT_ID_CHARS = 12  # an agent id: the start of SHA-256 over issuer, app and user
DEFAULT_LOG_DIR = Path("runs/gateway")
DEFAULT_HASH_KEY_ENV = "GATEWAY_LOG_KEY"
#: PS10: how the caller's origin is written to the log. "raw": the address as received
#: (today's lines). "network_pseudonym": the keyed pseudonym of its network, the value the
#: behaviour layer saw, so an offline re-score of the log feeds the engine the same value.
LOG_ORIGIN_RAW, LOG_ORIGIN_NETWORK_PSEUDONYM = "raw", "network_pseudonym"
LOG_ORIGINS = (LOG_ORIGIN_RAW, LOG_ORIGIN_NETWORK_PSEUDONYM)
#: The route fields v5 added. While one holds its default it is left out of the route's
#: config digest (:func:`digest_view`), so a pre-v5 route keeps its ``config_sha256``.
V5_ROUTE_FIELDS = (
    "baseline_key",
    "zone_map",
    "route_zone",
    "shared_egress",
    "fail_closed_unparsed",
    "upstream_audit_header",
    "legacy_gate",
    "pseudonymize_origin",
    "log_origin",
)
V5_FLAG_FIELDS = (
    "fail_closed_unparsed",
    "legacy_gate",
    "pseudonymize_origin",
)
V5_PATH_FIELDS = ("zone_map", "shared_egress")
#: PS7: the legacy B x L gate's two numbers (1-125 scale) under their v5 names, and the names
#: they had before v5, written beside them as aliases until gateway-log/4.
GATE_RISK, GATE_FACTOR = "gate_risk", "gate_factor"
GATE_ALIASES = MappingProxyType({GATE_RISK: "risk", GATE_FACTOR: "factor"})
#: PS9: an HTTP field name is an RFC 9110 token.
HEADER_TOKEN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
#: PS9: headers the audit join may never take, because an exchange id under one of them would
#: change how the upstream reads the request: credentials, the hop's own fields (RFC 9110
#: 7.6.1), routing and forwarding, content negotiation, conditional and range requests, the
#: browser's fields, SSE resumption, and (by prefix) the representation and the MCP session.
RESERVED_HEADERS = frozenset(
    "authorization cookie connection keep-alive te trailer transfer-encoding upgrade "
    "host forwarded via max-forwards x-real-ip origin referer user-agent accept "
    "expect range last-event-id".split()
)
MCP_HEADER_PREFIX = "mcp-"  # Mcp-Session-Id, MCP-Protocol-Version, Mcp-Method, Mcp-Name
RESERVED_HEADER_PREFIXES = (
    MCP_HEADER_PREFIX,
    "content-",  # Content-Type, -Length, -Encoding: the body
    "accept-",  # Accept-Encoding, -Language, -Charset
    "proxy-",  # Proxy-Authorization, Proxy-Connection
    "x-forwarded-",  # X-Forwarded-For (the trusted-proxy rule reads it), -Host, -Proto
    "if-",  # If-Match, If-None-Match, If-Modified-Since
    "sec-",  # Sec-Fetch-*: set by browsers only
)
#: B9d: the version of a zone-map file this gateway reads.
ZONE_MAP_VERSION = 1


@dataclass(frozen=True)
class Identity:
    """Who sent a request, as the identity provider's signed access token says.

    ``user`` is the token's ``sub`` (the person, or the service for client credentials),
    ``app`` and ``agent`` its ``client_id`` (the agent application registered at the
    provider), ``id`` one stable key per issuer, app and user — the key for session ownership
    and for baselines (v1-v4, and v5's per-agent default, D5). Never from the wire's own
    say-so: the client's ``clientInfo`` is self-reported and logged separately as
    ``gateway.client``.

    B1 (v5): ``person`` is the value of the route's user claim (``sub`` by default, ``oid``
    on Entra), and ``baseline_key`` = SHA-256(iss|person)[:12], the per-person key of the
    opt-in ``"user"`` mode; ``baseline_source`` names the claim it came from (``sub`` when
    the configured claim was missing). B9: ``zone`` is the token's zone claim, when one is
    configured and names an IANA zone.
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
    person: str | None = None  # B1: the user claim's value
    baseline_key: str | None = None  # B1: SHA-256(iss|person)[:12]
    baseline_source: str | None = None  # B1: the claim ``person`` came from
    zone: str | None = None  # B9: the zone claim's IANA zone

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
    behaviour_policy: str | None = None  # behaviour layer's limits/steps (behaviour/policy.py)
    # ── v5 (spec 2.9, 4.3): read by the route scorer and the proxy from Batch 2 on ──
    baseline_key: str | None = None  # B1: BASELINE_KEYS; None: by design (:func:`baseline_mode`)
    zone_map: str | None = None  # B9d: JSON file mapping a person to an IANA zone
    #: B9d, CAL-7: the route's IANA zone. When set it overrides the behaviour policy's
    #: ``route_zone`` (the scorer applies it with ``behaviour.replace_config``); None: the
    #: policy's zone (UTC by default).
    route_zone: str | None = None
    shared_egress: str | None = None  # B10: per-platform egress table (JSON file)
    fail_closed_unparsed: bool = False  # GW-1: refuse (400) a body that does not parse
    #: PS9: the request header that carries the gateway's exchange id upstream, so the
    #: upstream's audit log can be joined to the gateway's attribution (:func:`with_audit_header`).
    upstream_audit_header: str | None = None
    #: PS7: run the legacy B x L gate and write ``gate_risk`` and ``gate_factor`` with their
    #: pre-v5 aliases ``risk`` and ``factor`` (:func:`gate_fields`); False skips the gate.
    legacy_gate: bool = True
    pseudonymize_origin: bool = False  # PS10: keyed pseudonyms for network and client values
    log_origin: str = LOG_ORIGIN_RAW  # PS10: how the origin is written to the log

    def __post_init__(self) -> None:
        if self.scoring not in SCORING_MODES:
            raise ValueError(f"upstream {self.name!r}: scoring must be one of {SCORING_MODES}")
        if self.log_bodies not in BODIES:
            raise ValueError(f"upstream {self.name!r}: log_bodies must be one of {BODIES}")
        if self.log_origin not in LOG_ORIGINS:
            raise ValueError(f"upstream {self.name!r}: log_origin must be one of {LOG_ORIGINS}")
        if self.baseline_key is not None and self.baseline_key not in BASELINE_KEYS:
            raise ValueError(f"upstream {self.name!r}: baseline_key must be one of {BASELINE_KEYS}")
        if self.route_zone is not None:
            if not isinstance(self.route_zone, str):
                raise ValueError(f"upstream {self.name!r}: route_zone must be an IANA zone name")
            zone(self.route_zone)  # ValueError for an unknown zone
        _check_v5_route(self)


def _check_v5_route(upstream: Upstream) -> None:
    """``ValueError`` for a v5 route field of the wrong type, a log origin that the behaviour
    layer would not see (PS10), or an audit header that is not a free header name (PS9)."""
    where = f"upstream {upstream.name!r}"
    for name in V5_FLAG_FIELDS:
        if not isinstance(getattr(upstream, name), bool):
            raise ValueError(f"{where}: {name} must be true or false")
    for name in V5_PATH_FIELDS:
        value = getattr(upstream, name)
        if value is not None and not (isinstance(value, str) and value.strip()):
            raise ValueError(f"{where}: {name} must be a file path")
    if upstream.log_origin != LOG_ORIGIN_RAW and not upstream.pseudonymize_origin:
        raise ValueError(f"{where}: log_origin {upstream.log_origin!r} needs pseudonymize_origin")
    header = upstream.upstream_audit_header
    if header is None:
        return
    if not (isinstance(header, str) and HEADER_TOKEN.fullmatch(header)):
        raise ValueError(f"{where}: upstream_audit_header must be an HTTP header name")
    lowered = header.lower()
    if (
        lowered in RESERVED_HEADERS
        or lowered.startswith(RESERVED_HEADER_PREFIXES)
        or lowered == upstream.key_header.lower()
    ):
        raise ValueError(f"{where}: upstream_audit_header {header!r} is reserved")


def digest_view(upstream: Upstream) -> dict:
    """The route config its ``config_sha256`` covers: every field, except a v5 field
    (:data:`V5_ROUTE_FIELDS`) still at its default, so the digest of a route that sets none
    of them is the one it had before v5 (the gateway hashes this, sorted, as JSON)."""
    defaults = {f.name: f.default for f in fields(Upstream) if f.default is not MISSING}
    return {
        name: value
        for name, value in asdict(upstream).items()
        if not (name in V5_ROUTE_FIELDS and value == defaults[name])
    }


def baseline_mode(upstream: Upstream | None, design: str) -> str:
    """B1: whose baseline the route's calls extend. The route's ``baseline_key`` when set;
    otherwise ``"agent"`` for a v5 behaviour design (D5) and ``"user_app"`` (today's) for
    v1-v4."""
    if upstream is not None and upstream.baseline_key is not None:
        return upstream.baseline_key
    return BASELINE_AGENT if design == V5 else BASELINE_USER_APP


def audit_headers(upstream: Upstream, exchange_id: str) -> dict[str, str]:
    """PS9: the header the proxy adds to the upstream request: the gateway's exchange id under
    the route's ``upstream_audit_header``, or nothing when the route sets none. It never
    carries the caller's identity or token."""
    if upstream.upstream_audit_header is None:
        return {}
    return {upstream.upstream_audit_header: exchange_id}


def with_audit_header(
    headers: Mapping[str, str], upstream: Upstream, exchange_id: str
) -> dict[str, str]:
    """PS9: the headers of the request sent upstream, with :func:`audit_headers` added. A
    copy the caller sent, in any letter case, is dropped first: the agent must never choose
    the id the upstream's audit log is joined on. Without the route's header, ``headers``."""
    name = upstream.upstream_audit_header
    if name is None:
        return dict(headers)
    return without_header(headers, name) | audit_headers(upstream, exchange_id)


def without_header(headers: Mapping[str, str], name: str) -> dict[str, str]:
    """``headers`` without any field named ``name`` in any letter case (field names are
    case-insensitive, RFC 9110 5.1), before the gateway sets its own value of that field."""
    lowered = name.lower()
    return {key: value for key, value in headers.items() if key.lower() != lowered}


def gate_fields(risk: float | None, factor: float | None) -> dict[str, float | None]:
    """PS7: the legacy gate's numbers as a decision carries them on a ``legacy_gate`` route:
    ``gate_risk`` and ``gate_factor``, plus the pre-v5 names ``risk`` and ``factor``."""
    named = {GATE_RISK: risk, GATE_FACTOR: factor}
    return named | {GATE_ALIASES[name]: value for name, value in named.items()}


# ── B9d: the organisation's directory map of zones ─────────────────────────────────────


@dataclass(frozen=True)
class ZoneDirectory:
    """B9d: a person -> IANA zone map, exported from the organisation's directory and kept by
    its administrators (a zone a user can edit himself would let him move his hour profile).
    Keys are the values of the sign-in's user claim (``oauth.user_claim``), as tokens carry
    them: ``Identity.person``, which for an agent signed in as itself names the agent (D5)."""

    zones: Mapping[str, str]

    def zone_of(self, person: str | None) -> str | None:
        """The person's zone, or None when the map does not name him."""
        return self.zones.get(person) if person else None


def load_zone_map(path: str | Path) -> ZoneDirectory:
    """B9d: a zone-map file, ``{"version": 1, "users": {"<user claim value>": "<IANA zone>"}}``.
    Fails loudly on another version, a malformed entry or an unknown zone."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != ZONE_MAP_VERSION:
        raise ValueError(f"zone map {path}: expected version {ZONE_MAP_VERSION}")
    users = raw.get("users")
    if not isinstance(users, dict):
        raise ValueError(f"zone map {path}: 'users' must map a user to a zone")
    for person, name in users.items():
        if not (isinstance(person, str) and person and isinstance(name, str)):
            raise ValueError(f"zone map {path}: every entry maps a user id to a zone name")
        zone(name)  # ValueError for an unknown zone
    return ZoneDirectory(MappingProxyType(dict(users)))


def route_zone_directory(upstream: Upstream | None) -> ZoneDirectory | None:
    """B9d: the route's zone map, loaded; None when the route names none."""
    if upstream is None or upstream.zone_map is None:
        return None
    return load_zone_map(upstream.zone_map)


# ── B10: the route's shared egress ──────────────────────────────────────────────────────


def route_egress_table(upstream: Upstream | None) -> EgressTable | None:
    """B10: the route's egress table, read once; None when the route names none. On a
    ``raw``-origin route an offline re-score recomputes network values from this file, so its
    ``digest`` belongs with the route's artifact digests and its ``unverified`` labels on the
    start line."""
    if upstream is None or upstream.shared_egress is None:
        return None
    return load_egress_table(upstream.shared_egress)


def route_shared_networks(upstream: Upstream | None) -> tuple[tuple[str, str], ...]:
    """B10: the route's shared networks, for ``BehaviourConfig.shared_networks``; () (every
    design unchanged) when the route names no egress table."""
    table = route_egress_table(upstream)
    return () if table is None else table.shared_networks()


# ── the identity provider and the whole file ───────────────────────────────────────────


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
    user_claim: str = DEFAULT_USER_CLAIM  # B1: the claim naming the person (Entra: "oid")
    zone_claim: str | None = None  # B9: the claim holding the user's IANA zone, if any

    def __post_init__(self) -> None:
        if not (isinstance(self.user_claim, str) and self.user_claim):
            raise ValueError("oauth: user_claim must name a claim")
        if self.user_claim in NOT_USER_CLAIMS:
            raise ValueError(f"oauth: user_claim {self.user_claim!r} does not name a person")
        if self.zone_claim is not None and not (
            isinstance(self.zone_claim, str) and self.zone_claim
        ):
            raise ValueError("oauth: zone_claim must name a claim")

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


def check_origin_key(config: GatewayConfig, environ: Mapping[str, str] | None = None) -> None:
    """PS10: ``ValueError`` when a route pseudonymises origins but ``hash_key_env`` is unset.
    Unkeyed SHA-256 of a /16 is reversed by trying all 65,536 of them."""
    env = os.environ if environ is None else environ
    if env.get(config.hash_key_env):
        return
    keyed = sorted(name for name, u in config.upstreams.items() if u.pseudonymize_origin)
    if keyed:
        raise ValueError(
            f"routes {keyed}: pseudonymize_origin needs a key in ${config.hash_key_env}"
        )


def load_config(
    path: Path, environ: Mapping[str, str] | None = None, check_keys: bool = True
) -> GatewayConfig:
    """Read the routes file. Fails loudly on a route without a URL, a bad ``oauth`` section,
    an ``agents`` table (removed: names now come only from the identity provider), or, with
    ``check_keys``, a route that pseudonymises origins with no key in ``environ`` (the process
    environment). A reader that never pseudonymises (``catalog.py``) may pass False."""
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
    config = GatewayConfig(
        upstreams=upstreams,
        log_dir=Path(raw.get("log_dir", DEFAULT_LOG_DIR)),
        trusted_proxies=tuple(raw.get("trusted_proxies", ())),
        hash_key_env=raw.get("hash_key_env", DEFAULT_HASH_KEY_ENV),
        oauth=oauth_of(raw.get("oauth")),
    )
    if check_keys:
        check_origin_key(config, environ)
    return config
