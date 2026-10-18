"""Observe-only MCP gateway: forward every message to an external server, record it, change nothing.

The agent is configured with the gateway's URL instead of the server's. Each request is
logged, forwarded with the upstream credential the gateway holds, and the reply is streamed
back byte for byte as it arrives — no headers added, no body rewritten — so the model on the
other side sees exactly what the upstream sent.

On a scanned route every ``tools/call`` is scored by the whole framework (``framework.py``:
static cell, runtime factor, input level) *before* it is forwarded, and the verdict is
logged; nothing is ever blocked. A tool list the route's scan was not run on is saved under
``<log_dir>/catalogs/`` for the static scan. ``score.py`` re-scores a saved log offline.

Refused requests are logged too (OWASP: authentication failures, unexpected requests): a
bad or missing token as ``auth_failed`` in the route's log, an unknown route in
``_gateway.jsonl``. A session used by an agent other than the one that opened it is logged
as ``session_agent_mismatch`` — still forwarded, as the gateway never blocks.

    uv run python -m mcp_security.gateway.proxy --config src/mcp_security/gateway/routes.json
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, replace
from pathlib import Path

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from mcp_security.gateway.config import (
    ANONYMOUS,
    GatewayConfig,
    Identity,
    Upstream,
    load_config,
)
from mcp_security.gateway.effects import EffectMap
from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.http_wire import (
    MessageTap,
    Network,
    client_behind,
    decode_header_value,
    parse_messages,
    parse_networks,
)
from mcp_security.gateway.log_file import MessageLog
from mcp_security.gateway.oauth import NO_TOKEN, AuthError, TokenVerifier
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import (
    CALL_METHOD,
    TO_AGENT,
    TO_SERVER,
    Exchange,
    LogPolicy,
    SessionBook,
    build_record,
    catalog_bytes,
    client_info_of,
    decision_record,
    gateway_record,
    notice_record,
    protocol_of,
    requests_in,
)

#: Headers that describe one network hop, never the message (RFC 9110 §7.6.1).
HOP_BY_HOP = frozenset(
    "connection keep-alive proxy-authenticate proxy-authorization te trailer "
    "transfer-encoding upgrade".split()
)
#: Not sent upstream: httpx sets host/length; the agent's token is ours, not the server's;
#: and asking for identity encoding keeps the relayed bytes readable for the log.
NOT_SENT_UPSTREAM = HOP_BY_HOP | {"host", "content-length", "authorization", "accept-encoding"}
#: Everything else the upstream says is passed down untouched, including Mcp-Session-Id.
NOT_SENT_DOWNSTREAM = HOP_BY_HOP
SESSION_HEADER = "mcp-session-id"
PROTOCOL_HEADER = "mcp-protocol-version"
METHOD_HEADER = "mcp-method"
NAME_HEADER = "mcp-name"
ORIGIN_HEADER = "origin"
FORWARDED_HEADER = "x-forwarded-for"
GATEWAY_FILE = "_gateway"  # log file for requests that match no route
MAX_ROUTE_CHARS = 100  # an unknown route name is the caller's text: logged, but cut
DIGEST_CHARS = 12
CONNECT_TIMEOUT_S = 10.0
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
METHODS = ["GET", "POST", "DELETE"]


class Gateway:
    """The request handler: identify the agent, log, forward, relay and log the reply."""

    def __init__(
        self,
        config: GatewayConfig,
        client: httpx.AsyncClient,
        verifier: TokenVerifier | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.verifier = verifier or (TokenVerifier(config.oauth) if config.oauth else None)
        self.agent_names: dict[str, str] = {}  # identity key -> agent name, for notices
        self.log = MessageLog(config.log_dir)
        self.sessions = SessionBook()
        if self.verifier is None:
            print(
                "gateway: no identity provider configured (oauth): every caller is "
                "'anonymous' — for local testing only, never in front of a real credential",
                file=sys.stderr,
            )
        self.trusted: tuple[Network, ...] = parse_networks(config.trusted_proxies)
        pseudonyms = Pseudonymizer.from_env(config.hash_key_env)
        self.refusals = LogPolicy(pseudonyms=pseudonyms)
        self.policies = {name: _policy(u, pseudonyms) for name, u in config.upstreams.items()}
        if not pseudonyms.keyed and any(u.log_bodies != "all" for u in config.upstreams.values()):
            print(
                f"gateway: {config.hash_key_env} is not set; pseudonyms are unkeyed SHA-256 "
                "and low-entropy values (recipients, repository names) can be guessed",
                file=sys.stderr,
            )
        self.scorers: dict[str, RouteScorer] = {}
        for name, upstream in config.upstreams.items():
            artifacts = load_artifacts(
                name, upstream.scan, upstream.breadth, upstream.rules, upstream.kind
            )
            if artifacts and upstream.scoring != "off":
                self.scorers[name] = RouteScorer(name, artifacts, history=upstream.history)
                self._restore_state(upstream)
        self._scored: dict[str, int] = {}
        # Tool lists already accounted for: the one each route's scan was run on.
        self.catalogs: dict[str, set[str]] = {
            name: {s.artifacts.scanned_catalog} if s.artifacts.scanned_catalog else set()
            for name, s in self.scorers.items()
        }

    async def handle(self, request: Request) -> Response:
        route = request.path_params["route"]
        upstream = self.config.upstreams.get(route)
        if upstream is None:
            self._refuse(request, GATEWAY_FILE, route[:MAX_ROUTE_CHARS], "unknown_route")
            return Response(status_code=404)
        try:
            identity = await self._identify(request, route)
        except AuthError as refused:
            self._refuse(request, route, route, "auth_failed", **{"gateway.reason": refused.reason})
            return self._unauthorized(route, refused.reason)
        self.agent_names[identity.key] = (  # who to name when another agent takes the session
            f"{identity.agent} ({identity.user})" if identity.user else identity.agent
        )

        body = await request.body()
        messages = parse_messages(body)
        exchange = _exchange(request, upstream.name, identity, messages, self.trusted)
        if exchange.session and (owner := self.sessions.claim(exchange.session, identity.key)):
            fields = {
                "gateway.session_owner": self.agent_names.get(owner, owner),
                "gateway.session_owner_id": owner,
                "gateway.session_ended": self.sessions.ended(exchange.session) or None,
            }
            self._notice(exchange, "session_agent_mismatch", **fields)
        for message in messages or [None]:  # a bodiless GET/DELETE still shows up
            record = self._log(exchange, TO_SERVER, None, message)
            if message and message.get("method") == CALL_METHOD:
                self._schedule(upstream, exchange, message, record["ts"])
        try:
            reply = await self.client.send(
                self.client.build_request(
                    request.method,
                    _target_url(upstream.url, request),
                    headers=_upstream_headers(request, upstream),
                    content=body,
                ),
                stream=True,
            )
        except httpx.TransportError as exc:
            fields = {"error.type": type(exc).__name__, "gateway.error": str(exc)}
            self._notice(exchange, "upstream_unreachable", **fields)
            return Response(status_code=502)

        # The server assigns the session on `initialize`; carry it onto the reply's lines.
        session = reply.headers.get(SESSION_HEADER) or exchange.session
        if session and session != exchange.session:
            self.sessions.claim(session, identity.key)  # a new session belongs to its opener
        if session and exchange.client_info:
            self.sessions.start(session, exchange.client_info)
        headers = {k: v for k, v in reply.headers.items() if k.lower() not in NOT_SENT_DOWNSTREAM}
        relay = self._relay(reply, replace(exchange, session=session))
        return StreamingResponse(relay, status_code=reply.status_code, headers=headers)

    async def _relay(self, reply: httpx.Response, exchange: Exchange) -> AsyncIterator[bytes]:
        """Yield upstream bytes unchanged; log each complete message on the side."""
        tap = MessageTap(reply.headers.get("content-type", ""))
        logged = False
        try:
            async for chunk in reply.aiter_raw():
                yield chunk
                for message in tap.feed(chunk):
                    logged = True
                    self._watch_catalog(
                        exchange, self._log(exchange, TO_AGENT, reply.status_code, message)
                    )
            for message in tap.close():
                logged = True
                self._watch_catalog(
                    exchange, self._log(exchange, TO_AGENT, reply.status_code, message)
                )
            if not logged:  # 202 to a notification, a DELETE's answer: the status still counts
                self._log(exchange, TO_AGENT, reply.status_code, None)
        finally:
            await reply.aclose()
            if exchange.http_method == "DELETE":  # the client ended the session
                self.sessions.end(exchange.session)

    async def _identify(self, request: Request, route: str) -> Identity:
        """Who sent the request, as the identity provider's signed access token says;
        ``AuthError`` says why the token does not hold. No provider: ``anonymous``."""
        if self.verifier is None:
            return ANONYMOUS
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthError(NO_TOKEN)
        return await asyncio.to_thread(self.verifier.verify, token, route)  # may fetch keys

    def _unauthorized(self, route: str, reason: str) -> Response:
        """401, pointing a client to where it can sign in when OAuth is on (MCP, RFC 9728)."""
        if self.verifier is None:
            return Response(status_code=401)
        return Response(
            status_code=401, headers={"WWW-Authenticate": self.verifier.challenge(route, reason)}
        )

    async def resource_metadata(self, request: Request) -> Response:
        """A route's Protected Resource Metadata (RFC 9728): which provider issues its tokens."""
        route = request.path_params["route"]
        if self.verifier is None or route not in self.config.upstreams:
            return Response(status_code=404)
        return JSONResponse(self.verifier.metadata(route))

    def _log(
        self, exchange: Exchange, direction: str, status: int | None, message: dict | None
    ) -> dict:
        policy = self.policies[exchange.route]
        record = build_record(exchange, self.sessions, direction, status, message, policy)
        self.log.write(exchange.route, record)
        return record

    def _notice(self, exchange: Exchange, notice: str, **fields: object) -> None:
        policy = self.policies[exchange.route]
        self.log.write(exchange.route, notice_record(exchange, notice, policy, **fields))

    def _refuse(
        self, request: Request, file: str, route: str, notice: str, **fields: object
    ) -> None:
        """A request the gateway turned away: who tried, from where — never the token."""
        exchange = _exchange(request, route, None, [], self.trusted)
        self.log.write(file, notice_record(exchange, notice, self.refusals, **fields))

    def announce(self, notice: str) -> None:
        """A start or stop line in every route's log: what this run is, so a reader can tell
        a restart (session state reset, new config, new scan) from a quiet period."""
        for name, upstream in self.config.upstreams.items():
            scorer, policy = self.scorers.get(name), self.policies[name]
            fields = {
                "gateway.config_sha256": _config_digest(upstream),
                "gateway.artifacts": scorer.artifacts.digests if scorer else None,
                "gateway.effects_sha256": policy.effects.digest if policy.effects else None,
                "gateway.log_bodies": policy.bodies,
                "gateway.pseudonyms_keyed": policy.pseudonyms.keyed,
                "gateway.auth": "oauth" if self.verifier else "none",
                "gateway.oauth_issuer": self.config.oauth.issuer if self.config.oauth else None,
            }
            self.log.write(name, gateway_record(name, notice, **fields))

    def _schedule(self, upstream: Upstream, exchange: Exchange, call: dict, ts: float) -> None:
        """Inline: score now, before forwarding. Background: score once the call is on its
        way upstream, on the same event loop, in arrival order (FIFO)."""
        if upstream.scoring == "background":
            asyncio.get_running_loop().call_soon(self._decide, exchange, call, ts)
        else:
            self._decide(exchange, call, ts)

    def _decide(self, exchange: Exchange, call: dict, ts: float) -> None:
        """Score one tools/call with the route's framework and log the verdict."""
        scorer = self.scorers.get(exchange.route)
        if scorer is None:
            return
        params = call.get("params") or {}
        try:
            decision = scorer.score(
                params.get("name"),
                params.get("arguments") or {},
                ts,
                caller=exchange.agent_id or exchange.agent,
            )
        except Exception as exc:  # noqa: BLE001 — a scoring bug must never break the agent's call; it is logged, not hidden
            decision = {"error": f"{type(exc).__name__}: {exc}"}
        decision["artifacts"] = scorer.artifacts.digests
        record = decision_record(
            exchange,
            self.sessions,
            call,
            decision,
            scorer.artifacts.scanned_catalog,
            ts,
            self.policies[exchange.route],
        )
        self.log.write(exchange.route, record)
        upstream = self.config.upstreams[exchange.route]
        self._scored[exchange.route] = done = self._scored.get(exchange.route, 0) + 1
        if upstream.state_every and done % upstream.state_every == 0:
            self.save_state(exchange.route)

    def save_state(self, route: str | None = None) -> None:
        """Write each scored route's dynamic history to its ``state_file`` (atomic replace)."""
        for name, scorer in self.scorers.items():
            path = self.config.upstreams[name].state_file
            if not path or (route and name != route):
                continue
            target = Path(path)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                partial = target.with_suffix(target.suffix + ".partial")
                partial.write_text(json.dumps(scorer.snapshot_all()), encoding="utf-8")
                partial.replace(target)
            except OSError as exc:
                print(f"gateway: could not save state for {name}: {exc}", file=sys.stderr)

    def _restore_state(self, upstream: Upstream) -> None:
        """Continue the route's dynamic history where the last run stopped, if it was saved."""
        if upstream.state_file and Path(upstream.state_file).exists():
            snapshot = json.loads(Path(upstream.state_file).read_text(encoding="utf-8"))
            self.scorers[upstream.name].restore_all(snapshot)

    def _watch_catalog(self, exchange: Exchange, record: dict) -> None:
        """Save a tool list this route's scan was not run on, once, for the static scan."""
        digest = record.get("gateway.catalog_sha256")
        known = self.catalogs.setdefault(exchange.route, set())
        if not digest or digest in known:
            return
        known.add(digest)
        path = self.config.log_dir / "catalogs" / f"{exchange.route}-{digest[:12]}.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(catalog_bytes({"tools": record["message"]["result"]["tools"]}))
        except OSError as exc:
            print(f"gateway: could not save catalog {path}: {exc}", file=sys.stderr)
        fields = {"gateway.catalog_sha256": digest, "gateway.catalog_file": str(path)}
        self._notice(exchange, "catalog_not_scanned", **fields)


def _policy(upstream: Upstream, pseudonyms: Pseudonymizer) -> LogPolicy:
    effects = EffectMap.load(Path(upstream.importance)) if upstream.importance else None
    return LogPolicy(bodies=upstream.log_bodies, effects=effects, pseudonyms=pseudonyms)


def _config_digest(upstream: Upstream) -> str:
    """Digest of one route's config (env var *names* only — no secret is in it)."""
    canonical = json.dumps(asdict(upstream), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:DIGEST_CHARS]


def _exchange(
    request: Request,
    route: str,
    identity: Identity | None,
    messages: list[dict],
    trusted: tuple[Network, ...] = (),
) -> Exchange:
    """What the wire says about one request: who sent it, from where, in which session."""
    peer = request.client.host if request.client else None
    address = client_behind(peer, request.headers.get(FORWARDED_HEADER), trusted)
    forwarded = address != peer
    return Exchange(
        route=route,
        agent=identity.agent if identity else None,
        agent_id=identity.id if identity else None,
        auth=identity.auth if identity else None,
        issuer=identity.issuer if identity else None,
        scopes=identity.scopes if identity else (),
        token_id=identity.token_id if identity else None,
        actors=identity.actors if identity else (),
        user=identity.user if identity else None,
        app=identity.app if identity else None,
        session=request.headers.get(SESSION_HEADER),
        http_method=request.method,
        client_address=address,
        client_port=None if forwarded or not request.client else request.client.port,
        peer_address=peer if forwarded else None,
        user_agent=request.headers.get("user-agent"),
        origin=request.headers.get(ORIGIN_HEADER),
        protocol_version=request.headers.get(PROTOCOL_HEADER) or protocol_of(messages),
        client_info=client_info_of(messages),
        method_header=request.headers.get(METHOD_HEADER),
        name_header=decode_header_value(request.headers.get(NAME_HEADER)),
        requests=requests_in(messages),
    )


def _target_url(base: str, request: Request) -> str:
    rest = request.path_params.get("rest", "")
    url = f"{base.rstrip('/')}/{rest}" if rest else base
    return f"{url}?{request.url.query}" if request.url.query else url


def _upstream_headers(request: Request, upstream: Upstream) -> dict[str, str]:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in NOT_SENT_UPSTREAM}
    if upstream.key_env:
        key = os.environ.get(upstream.key_env)
        if not key:
            raise RuntimeError(f"env var {upstream.key_env} (key for {upstream.name}) is not set")
        headers[upstream.key_header] = f"{upstream.key_prefix}{key}"
    return headers


def create_app(
    config: GatewayConfig,
    client: httpx.AsyncClient | None = None,
    verifier: TokenVerifier | None = None,
) -> Starlette:
    """The gateway as an ASGI app. Pass ``client`` to point it at a test upstream, and
    ``verifier`` to check tokens against fixed keys instead of the provider's JWKS."""
    owns_client = client is None
    http = client or httpx.AsyncClient(
        timeout=httpx.Timeout(CONNECT_TIMEOUT_S, read=None),  # SSE streams stay open
        follow_redirects=False,  # a redirect is the upstream's answer; relay it as-is
    )
    gateway = Gateway(config, http, verifier)

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        gateway.announce("gateway_started")
        yield
        gateway.save_state()
        gateway.announce("gateway_stopped")
        gateway.log.close()
        if owns_client:
            await http.aclose()

    app = Starlette(
        routes=[
            Route(
                "/.well-known/oauth-protected-resource/{route}",
                gateway.resource_metadata,
                methods=["GET"],
            ),
            Route("/{route}", gateway.handle, methods=METHODS),
            Route("/{route}/{rest:path}", gateway.handle, methods=METHODS),
        ],
        lifespan=lifespan,
    )
    app.state.gateway = gateway  # for operations and tests: save_state(), scorers
    return app


def main() -> None:
    """Run the gateway: ``--config routes.json [--host H] [--port P]``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    config = load_config(args.config)
    for name, upstream in config.upstreams.items():
        print(f"gateway: http://{args.host}:{args.port}/{name}  ->  {upstream.url}")
    # proxy_headers off: uvicorn would otherwise believe X-Forwarded-For from 127.0.0.1 by
    # default, letting any local agent pick its logged address; trusted_proxies decides instead.
    uvicorn.run(
        create_app(config),
        host=args.host,
        port=args.port,
        log_level="warning",
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
