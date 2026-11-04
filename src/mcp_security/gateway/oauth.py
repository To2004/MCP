"""The gateway as an OAuth 2.1 resource server: who a caller is, read from a signed token.

With an identity provider configured (``config.OAuthConfig``), an agent signs in there — the
MCP authorization flow — and sends ``Authorization: Bearer <JWT>``. The gateway checks the
token: the signature against the provider's published keys (JWKS), the issuer, the audience
(it must name this route: RFC 8707, so a token minted for another server is refused), and the
expiry. Then it reads the caller from the token
(RFC 9068 claims): ``sub`` is the user, ``client_id`` the agent application, ``scope``
what it may do, ``jti`` the token's id, and ``act`` (RFC 8693) who acts on whose behalf.

The gateway also says where to sign in: each route's Protected Resource Metadata
(RFC 9728) names the provider, and every 401 points to it in ``WWW-Authenticate``, so a
stock MCP client finds its way without being told. The token is never sent upstream.

v5 reads more about the caller (spec 2.1), all of it pure functions of the token and the
log line, so the live gateway and an offline re-score agree:

- B1: which key a route's behaviour history uses (:func:`baseline_caller`, and offline
  :func:`logged_baseline_caller`). v5 keeps it per agent (D5): the signed-in agent, else what
  a caller without sign-in reports about itself (:func:`reported_key`). The per-person key
  SHA-256(iss|user claim) (:func:`baseline_key_of`) is the opt-in ``"user"`` mode, whose
  fallbacks to ``sub`` are counted for the route (:class:`UserClaimReport`);
- B2, E11: the Client value, (authenticated app, clientInfo family or "(none)")
  (:func:`client_pair`);
- B9d: the caller's zone from the directory map, else the token's claim, else the route zone,
  with the share of callers on the route zone (:class:`ZoneResolver`);
- PS10: keyed pseudonyms of the network and client values (:func:`pseudonymous_network`,
  :func:`pseudonymous_client`).
"""

from __future__ import annotations

import hashlib
import ipaddress
from collections import Counter, OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

import jwt

from mcp_security.behaviour.clock import DEFAULT_ZONE
from mcp_security.behaviour.clock import zone as iana_zone
from mcp_security.behaviour.engine import client_family
from mcp_security.gateway.config import (
    AGENT_ID_CHARS,
    BASELINE_AGENT,
    BASELINE_KEYS,
    BASELINE_USER,
    BASELINE_USER_APP,
    DEFAULT_USER_CLAIM,
    LOG_ORIGIN_RAW,
    LOG_ORIGINS,
    NO_AUTH,
    OAUTH,
    Identity,
    OAuthConfig,
    ZoneDirectory,
)
from mcp_security.gateway.egress.table import is_platform_network
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import BASELINE_KEY_FIELD

KEY_CACHE_S = 300  # how long fetched signing keys are reused before the JWKS is read again
REQUIRED_CLAIMS = ["exp", "iss", "aud", "sub"]
NO_TOKEN = "no_bearer_token"
#: B1: the claim a baseline falls back to when the route's user claim is missing; RFC 9068
#: makes ``sub`` required, so every verified token has it.
FALLBACK_USER_CLAIM = "sub"
#: E11: the client family of a request that names no client: a value like any other, so
#: leaving the name out is itself new for a caller who always sends one.
NO_CLIENT = "(none)"
#: B1 (D5): a caller without sign-in is keyed by what it reports about itself. This domain
#: keeps such a key apart from any signed-in key, and an IPv6 address counts by its /64,
#: inside which privacy addresses rotate.
REPORTED_KEY_DOMAIN = "reported"
NO_ADDRESS = "(none)"
IPV6_KEY_PREFIX = 64
#: DEP-6: the log fields (``wire_log``) an offline re-score rebuilds a caller's key from, on
#: a line written before ``gateway.baseline_key``; ``user.id`` holds the token's ``sub``.
AGENT_ID_FIELD, AGENT_FIELD, USER_ID_FIELD = "gateway.agent_id", "gateway.agent", "user.id"
AUTH_FIELD, ISSUER_FIELD = "gateway.auth", "gateway.issuer"
CLIENT_FIELD, ADDRESS_FIELD = "gateway.client", "client.address"
LOGGED_USER_CLAIM = "sub"
#: B9d: where a caller's zone came from. ``route`` is the fallback whose share is reported.
ZONE_FROM_MAP, ZONE_FROM_CLAIM, ZONE_FROM_ROUTE = "map", "claim", "route"
ZONE_SOURCES = (ZONE_FROM_MAP, ZONE_FROM_CLAIM, ZONE_FROM_ROUTE)
#: B1: whether a caller's per-person key came from the route's user claim or fell back.
CLAIM_FROM_TOKEN, CLAIM_FELL_BACK = "claim", "fallback"
#: B1, B9d: callers a route report remembers (their latest source), the most recent kept.
MAX_REPORT_CALLERS = 100_000
#: PS10: pseudonym prefixes, one domain per kind of value, so equal pseudonyms always mean
#: equal values of the same kind, and a reader can tell a pseudonym from a raw value.
NETWORK_PSEUDONYM, APP_PSEUDONYM, CLIENT_PSEUDONYM = "net:", "app:", "client:"
PSEUDONYM_DOMAIN_SEPARATOR = "\x1f"


class AuthError(Exception):
    """A request the gateway refuses; ``reason`` is what the log records."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SigningKeys(Protocol):
    """Where verification keys come from: ``jwt.PyJWKClient`` live, a fixed set in tests."""

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


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
        return identity_from_claims(claims, self.config.user_claim, self.config.zone_claim)

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


def identity_from_claims(
    claims: Mapping[str, object],
    user_claim: str = DEFAULT_USER_CLAIM,
    zone_claim: str | None = None,
) -> Identity:
    """The caller a verified token names. ``id`` is one per issuer, app and user, so each
    user of each agent application gets a session owner of its own (and, in v1-v4, a
    baseline). B1: ``baseline_key`` is one per issuer and person, the value of ``user_claim``
    (``sub`` when the token lacks it, and ``baseline_source`` says so). B9: ``zone`` is the
    ``zone_claim`` value when it names an IANA zone."""
    client = claims.get("client_id") or claims.get("azp")
    if not client:
        raise AuthError("missing_claim")
    user, issuer = str(claims["sub"]), str(claims["iss"])
    agent_id = hashlib.sha256(f"{issuer}|{client}|{user}".encode()).hexdigest()[:AGENT_ID_CHARS]
    person, source = _person(claims, user_claim)
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
        person=person,
        baseline_key=baseline_key_of(issuer, person),
        baseline_source=source,
        zone=zone_from_claims(claims, zone_claim),
    )


def _person(claims: Mapping[str, object], user_claim: str) -> tuple[str, str]:
    """B1: the person a token names and the claim that named him: ``user_claim`` when it is
    a non-empty string or a number, else ``sub``."""
    value = claims.get(user_claim)
    named = isinstance(value, str) and bool(value)
    numbered = isinstance(value, int) and not isinstance(value, bool)
    if named or numbered:
        return str(value), user_claim
    return str(claims[FALLBACK_USER_CLAIM]), FALLBACK_USER_CLAIM


def actor_chain(act: object) -> tuple[str, ...]:
    """RFC 8693 ``act``: the acting party, then whoever acts for it, outermost first."""
    chain: list[str] = []
    while isinstance(act, dict) and act.get("sub"):
        chain.append(str(act["sub"]))
        act = act.get("act")
    return tuple(chain)


# ── B1: whose history a call extends ───────────────────────────────────────────────────


def baseline_key_of(issuer: str, person: str) -> str:
    """B1: the per-person baseline key of the opt-in ``"user"`` mode, SHA-256(iss|person)[:12].
    ``iss`` stays in it because a user id is unique only within its issuer (RFC 7519 4.1.2).
    :func:`logged_baseline_caller` rebuilds it for a line written before v5 (DEP-6)."""
    return hashlib.sha256(f"{issuer}|{person}".encode()).hexdigest()[:AGENT_ID_CHARS]


def reported_key(client_info: str | None, address: str | None) -> str:
    """B1 (revised 2026-10-27, D5): the history key of a caller that did not sign in,
    SHA-256("reported"|client family|address)[:12]. The family is ``clientInfo``'s name
    without its version, or "(none)", so an upgrade keeps the key. The address is the
    caller's IP, an IPv6 address cut to its /64. Both parts are self-reported: an agent that
    changes either one starts an empty history (spec 2.1)."""
    family = client_family(client_info) or NO_CLIENT
    text = f"{REPORTED_KEY_DOMAIN}|{family}|{_address_part(address)}"
    return hashlib.sha256(text.encode()).hexdigest()[:AGENT_ID_CHARS]


def _address_part(address: str | None) -> str:
    """:func:`reported_key`'s address: an IPv4 address as it is (also when IPv4-mapped), an
    IPv6 address as its /64 network, and anything else (none, a host name) as given."""
    if not address:
        return NO_ADDRESS
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return address
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/{IPV6_KEY_PREFIX}", strict=False))
    return str(ip)


def baseline_caller(
    mode: str, agent_key: str | None, user_key: str | None, reported: str | None = None
) -> str | None:
    """B1: the behaviour caller of a call.

    - ``"agent"`` (v5, D5): ``reported`` when it is given, which a caller passes only for a
      call without sign-in (:func:`reported_key`); otherwise the agent key.
    - ``"user"`` (opt-in): the per-person key when the caller has one, else the agent key.
    - ``"user_app"`` (v1-v4): the agent key, so callers without sign-in share "anonymous".

    The agent key is ``Identity.key``. Offline, :func:`logged_baseline_caller` gives the
    same key from a log line."""
    if mode not in BASELINE_KEYS:
        raise ValueError(f"baseline mode must be one of {BASELINE_KEYS}, not {mode!r}")
    if mode == BASELINE_USER and user_key:
        return user_key
    if mode == BASELINE_AGENT and reported:
        return reported
    return agent_key


def logged_baseline_caller(
    record: Mapping[str, object], mode: str, user_claim: str = DEFAULT_USER_CLAIM
) -> str | None:
    """B1, DEP-6: the key :func:`baseline_caller` gave a logged call live, for an offline
    re-score and the v5 migration replay (``score.py --design v5 --save-state``).

    - ``"user_app"`` (v1-v4): the agent key, ``gateway.agent_id`` else ``gateway.agent``.
    - Otherwise ``gateway.baseline_key`` when the line carries it (v5's gateway logs it).
    - A line written before it is rebuilt. A caller without sign-in gets :func:`reported_key`
      of ``gateway.client`` and ``client.address`` in ``"agent"`` mode; old lines log the
      address raw, after the trusted-proxy rule, as the live key used it. A signed-in caller
      gets its agent key, or in ``"user"`` mode with the ``sub`` claim SHA-256(
      ``gateway.issuer``|``user.id``). Another claim's value was never logged, so such a
      line keeps its agent key.
    """
    if mode not in BASELINE_KEYS:
        raise ValueError(f"baseline mode must be one of {BASELINE_KEYS}, not {mode!r}")
    agent_key = _logged_text(record, AGENT_ID_FIELD) or _logged_text(record, AGENT_FIELD)
    if mode == BASELINE_USER_APP:
        return agent_key
    if logged := _logged_text(record, BASELINE_KEY_FIELD):
        return logged
    if not _logged_sign_in(record):
        client, address = _logged_text(record, CLIENT_FIELD), _logged_text(record, ADDRESS_FIELD)
        return baseline_caller(mode, agent_key, None, reported_key(client, address))
    issuer, user = _logged_text(record, ISSUER_FIELD), _logged_text(record, USER_ID_FIELD)
    user_key = None
    if user_claim == LOGGED_USER_CLAIM and issuer and user:
        user_key = baseline_key_of(issuer, user)
    return baseline_caller(mode, agent_key, user_key)


def _logged_text(record: Mapping[str, object], name: str) -> str | None:
    """A log field's value when it is a non-empty string; None otherwise."""
    value = record.get(name)
    return value if isinstance(value, str) and value else None


def _logged_sign_in(record: Mapping[str, object]) -> bool:
    """Whether a logged call was signed in, by ``wire_log.identity_strength``'s rule: an
    agent was named and the identity came from a token, not from nothing (``none``)."""
    named = _logged_text(record, AGENT_FIELD) is not None
    return named and record.get(AUTH_FIELD) not in (None, NO_AUTH)


class LatestPerCaller:
    """The latest value seen for each caller, at most ``max_callers`` of them: the one least
    recently seen leaves first. The bounded tally behind a route's reports of zone sources
    (B9d) and user-claim fallbacks (B1)."""

    def __init__(self, max_callers: int = MAX_REPORT_CALLERS) -> None:
        if max_callers < 1:
            raise ValueError("max_callers must be at least 1")
        self._max_callers = max_callers
        self._latest: OrderedDict[str, str] = OrderedDict()

    def record(self, caller: str, value: str) -> None:
        """Remember ``value`` as ``caller``'s latest, and forget the stalest caller if full."""
        self._latest[caller] = value
        self._latest.move_to_end(caller)
        if len(self._latest) > self._max_callers:
            self._latest.popitem(last=False)

    def __len__(self) -> int:
        return len(self._latest)

    def __contains__(self, caller: object) -> bool:
        return caller in self._latest

    def counts(self) -> Counter[str]:
        """Callers per latest value."""
        return Counter(self._latest.values())

    def share(self, value: str) -> float:
        """The share of remembered callers whose latest value is ``value``; 0.0 before any."""
        return self.counts()[value] / len(self._latest) if self._latest else 0.0


def user_claim_fell_back(identity: Identity, user_claim: str) -> bool:
    """B1: True when a signed-in caller's token lacked the route's ``user_claim``, so the
    per-person key fell back to ``sub``; never for a ``sub`` route or a caller without one."""
    return identity.baseline_source is not None and identity.baseline_source != user_claim


class UserClaimReport:
    """B1, opt-in ``"user"`` mode: the share of signed-in callers whose token lacked the
    route's user claim. Their per-person key fell back to ``sub``, which on Entra is pairwise
    per application, so each of their apps starts a history of its own; the report makes
    that loud without refusing traffic. Counted per caller (latest state), bounded."""

    def __init__(
        self, user_claim: str = DEFAULT_USER_CLAIM, max_callers: int = MAX_REPORT_CALLERS
    ) -> None:
        self.user_claim = user_claim
        self._callers = LatestPerCaller(max_callers)

    def observe(self, identity: Identity, caller: str | None = None) -> bool:
        """Count a signed-in caller under ``caller`` (by default his agent key); returns
        whether his key fell back. A caller without sign-in is not counted."""
        fell_back = user_claim_fell_back(identity, self.user_claim)
        if identity.baseline_source is not None:
            state = CLAIM_FELL_BACK if fell_back else CLAIM_FROM_TOKEN
            self._callers.record(caller or identity.key, state)
        return fell_back

    def report(self) -> dict[str, object]:
        """The route's user-claim report: the claim, callers counted, the fallback share."""
        return {
            "user_claim": self.user_claim,
            "user_claim_callers": len(self._callers),
            "user_claim_fallback_share": self._callers.share(CLAIM_FELL_BACK),
        }


# ── B2, E11: the Client value ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ClientPair:
    """B2, E11: the Client value. ``app`` is the authenticated application (None without a
    token); ``family`` the self-reported clientInfo name without its version, or
    :data:`NO_CLIENT`. A borrowed token sent from another client program is a new pair."""

    app: str | None
    family: str


def authenticated_app(app: str | None, actors: Sequence[str] | None = ()) -> str | None:
    """B2: the agent application the identity provider names for the call: the current actor
    (RFC 8693 4.1, the outermost ``act``) if the token has one, else its ``client_id``."""
    return actors[0] if actors else app


def client_pair(
    app: str | None, actors: Sequence[str] | None, client_info: str | None
) -> ClientPair:
    """B2, E11: the Client value from the token's app and actors (live: ``Identity.app`` and
    ``Identity.actors``; offline: ``gateway.app`` and ``gateway.act``) and the self-reported
    ``name/version`` (``gateway.client``)."""
    return ClientPair(authenticated_app(app, actors), client_family(client_info) or NO_CLIENT)


# ── B9d: the caller's zone ─────────────────────────────────────────────────────────────


def zone_from_claims(claims: Mapping[str, object], zone_claim: str | None) -> str | None:
    """B9: the token's zone claim (OIDC ``zoneinfo``) when one is configured and names an IANA
    zone; None otherwise, so the caller falls back to the route zone."""
    if not zone_claim:
        return None
    value = claims.get(zone_claim)
    return value if isinstance(value, str) and _known_zone(value) else None


def _known_zone(name: str) -> bool:
    try:
        iana_zone(name)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class ZoneChoice:
    """B9d: a caller's IANA zone and where it came from (:data:`ZONE_SOURCES`)."""

    zone: str
    source: str


class ZoneResolver:
    """B9d: each caller's zone, from the directory map, else the token's zone claim, else the
    route zone, and the share of callers on that fallback.

    The route zone is the route's ``route_zone``, else its behaviour policy's (UTC by
    default). A claim is trusted less than the map: the user may be able to edit it. The
    share is over distinct callers (their latest source; the most recent
    :data:`MAX_REPORT_CALLERS` kept), for the route's report."""

    def __init__(
        self,
        route_zone: str = DEFAULT_ZONE,
        directory: ZoneDirectory | None = None,
        max_callers: int = MAX_REPORT_CALLERS,
    ) -> None:
        if not isinstance(route_zone, str):
            raise ValueError("route_zone must be an IANA zone name")
        iana_zone(route_zone)  # ValueError for an unknown zone
        self.route_zone = route_zone
        self.directory = directory
        self._sources = LatestPerCaller(max_callers)

    def resolve(
        self, caller: str | None, person: str | None = None, claim_zone: str | None = None
    ) -> ZoneChoice:
        """The zone of ``caller`` (counted under that key; None is not counted), given his
        directory id ``person`` (``Identity.person``) and his token's ``claim_zone``."""
        mapped = self.directory.zone_of(person) if self.directory else None
        if mapped is not None:
            choice = ZoneChoice(mapped, ZONE_FROM_MAP)
        elif claim_zone and _known_zone(claim_zone):
            choice = ZoneChoice(claim_zone, ZONE_FROM_CLAIM)
        else:
            choice = ZoneChoice(self.route_zone, ZONE_FROM_ROUTE)
        if caller is not None:
            self._sources.record(caller, choice.source)
        return choice

    def resolve_identity(self, identity: Identity, caller: str | None = None) -> ZoneChoice:
        """:meth:`resolve` for a signed-in caller, counted under ``caller``: the call's
        baseline caller (:func:`baseline_caller`), by default his agent key (D5)."""
        return self.resolve(caller or identity.key, identity.person, identity.zone)

    def fallback_share(self) -> float:
        """The share of counted callers whose zone is the route zone; 0.0 before any."""
        return self._sources.share(ZONE_FROM_ROUTE)

    def report(self) -> dict[str, object]:
        """The route's zone report: callers counted, the fallback share, callers per source."""
        counts = self._sources.counts()
        return {
            "zone_callers": len(self._sources),
            "zone_fallback_share": self.fallback_share(),
            "zone_sources": {source: counts.get(source, 0) for source in ZONE_SOURCES},
        }


# ── PS10: keyed origin pseudonyms ──────────────────────────────────────────────────────


def _pseudonym(prefix: str, value: str, pseudonyms: Pseudonymizer) -> str:
    if not pseudonyms.keyed:
        raise ValueError("origin pseudonyms need a key: unkeyed SHA-256 of a /16 is reversible")
    return prefix + pseudonyms.of(f"{prefix}{PSEUDONYM_DOMAIN_SEPARATOR}{value}")


def pseudonymous_network(network: str | None, pseudonyms: Pseudonymizer) -> str | None:
    """PS10: the keyed pseudonym of a network value, which the engine keeps unchanged (it is
    not an IP), so every design's verdicts are those of the raw value.

    ``network`` is the engine's ``network_of`` of the raw address, after trusted-proxy
    resolution and the shared-egress check. A platform label stays readable: the engine must
    see it to skip the org discount, and it names no one. A value that already is a network
    pseudonym (a ``network_pseudonym`` log re-scored offline) is returned as it is."""
    if network is None or is_platform_network(network) or network.startswith(NETWORK_PSEUDONYM):
        return network
    return _pseudonym(NETWORK_PSEUDONYM, network, pseudonyms)


def pseudonymous_client(pair: ClientPair, pseudonyms: Pseudonymizer) -> ClientPair:
    """PS10: the Client value with both parts pseudonymised (v5's ``Message.app`` and
    ``Message.client_family``); a missing app stays None and :data:`NO_CLIENT` stays as is."""
    app = None if pair.app is None else _pseudonym(APP_PSEUDONYM, pair.app, pseudonyms)
    family = pair.family
    if family != NO_CLIENT:
        family = _pseudonym(CLIENT_PSEUDONYM, family, pseudonyms)
    return ClientPair(app, family)


def pseudonymous_client_name(client: str | None, pseudonyms: Pseudonymizer) -> str | None:
    """PS10 for v1-v4's ``Message.client`` (``name/version``): the pseudonym of its family,
    which the engine's ``client_family`` keeps unchanged; None stays None."""
    family = client_family(client)
    return None if family is None else _pseudonym(CLIENT_PSEUDONYM, family, pseudonyms)


def logged_origin(
    log_origin: str, address: str | None, network_pseudonym: str | None
) -> str | None:
    """PS10: what the log's ``client.address`` holds: the raw address (``raw``), or the
    network pseudonym the engine saw (``network_pseudonym``)."""
    if log_origin not in LOG_ORIGINS:
        raise ValueError(f"log_origin must be one of {LOG_ORIGINS}, not {log_origin!r}")
    return address if log_origin == LOG_ORIGIN_RAW else network_pseudonym
