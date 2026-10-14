"""Observe-only MCP gateway: forward every message to an external server, record it, change nothing.

The agent is configured with the gateway's URL instead of the server's. Each request is
logged, forwarded with the upstream credential the gateway holds, and the reply is streamed
back byte for byte as it arrives — no headers added, no body rewritten — so the model on the
other side sees exactly what the upstream sent.

On a scanned route every ``tools/call`` is scored by the whole framework (``framework.py``:
static cell, runtime factor, input level) *before* it is forwarded, and the verdict is
logged; nothing is ever blocked. A tool list the route's scan was not run on is saved under
``<log_dir>/catalogs/`` for the static scan. ``score.py`` re-scores a saved log offline.

    uv run python -m mcp_security.gateway.proxy --config src/mcp_security/gateway/routes.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

from mcp_security.gateway.framework import RouteScorer, load_artifacts
from mcp_security.gateway.wire_log import (
    CALL_METHOD,
    FROM_GATEWAY,
    TO_AGENT,
    TO_SERVER,
    Exchange,
    MessageLog,
    SessionBook,
    build_record,
    catalog_bytes,
    client_info_of,
    decision_record,
    notice_record,
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
ANONYMOUS = "anonymous"
CONNECT_TIMEOUT_S = 10.0
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
METHODS = ["GET", "POST", "DELETE"]


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


@dataclass(frozen=True)
class GatewayConfig:
    """Routes, known agents (by SHA-256 of their gateway token), and where logs go."""

    upstreams: dict[str, Upstream]
    agents: dict[str, str] = field(default_factory=dict)  # empty = no agent auth (demo)
    log_dir: Path = Path("runs/gateway")


def load_config(path: Path) -> GatewayConfig:
    """Read the routes file. Fails loudly on a route without a URL."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    upstreams = {}
    for name, entry in raw["upstreams"].items():
        if not entry.get("url"):
            raise ValueError(f"upstream {name!r} has no url")
        upstreams[name] = Upstream(name=name, **entry)
    return GatewayConfig(
        upstreams=upstreams,
        agents=dict(raw.get("agents", {})),
        log_dir=Path(raw.get("log_dir", "runs/gateway")),
    )


def token_hash(token: str) -> str:
    """How an agent token is stored in the config: its SHA-256, never the token."""
    return hashlib.sha256(token.encode()).hexdigest()


def parse_messages(raw: bytes) -> list[dict]:
    """JSON-RPC messages in a body: one object, a batch, or nothing. Garbage is kept visible."""
    if not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [{"unparsed": raw.decode("utf-8", errors="replace")}]
    items = parsed if isinstance(parsed, list) else [parsed]
    return [item for item in items if isinstance(item, dict)]


class MessageTap:
    """Reads JSON-RPC messages out of a response body fed chunk by chunk.

    SSE frames are emitted as soon as each one is complete, so a long-lived stream is logged
    while it is open; a plain JSON body is parsed once it ends.
    """

    def __init__(self, content_type: str) -> None:
        self._sse = content_type.startswith("text/event-stream")
        self._buffer = b""

    def feed(self, chunk: bytes) -> list[dict]:
        self._buffer += chunk
        if not self._sse:
            return []
        self._buffer = self._buffer.replace(b"\r\n", b"\n")
        *frames, self._buffer = self._buffer.split(b"\n\n")
        return [message for frame in frames for message in _sse_messages(frame)]

    def close(self) -> list[dict]:
        rest, self._buffer = self._buffer, b""
        return _sse_messages(rest) if self._sse else parse_messages(rest)


def _sse_messages(frame: bytes) -> list[dict]:
    data = [line[5:].lstrip() for line in frame.split(b"\n") if line.startswith(b"data:")]
    return parse_messages(b"\n".join(data))


class Gateway:
    """The request handler: identify the agent, log, forward, relay and log the reply."""

    def __init__(self, config: GatewayConfig, client: httpx.AsyncClient) -> None:
        self.config = config
        self.client = client
        self.log = MessageLog(config.log_dir)
        self.sessions = SessionBook()
        self.scorers: dict[str, RouteScorer] = {}
        for name, upstream in config.upstreams.items():
            artifacts = load_artifacts(
                name, upstream.scan, upstream.breadth, upstream.rules, upstream.kind
            )
            if artifacts:
                self.scorers[name] = RouteScorer(name, artifacts)
        # Tool lists already accounted for: the one each route's scan was run on.
        self.catalogs: dict[str, set[str]] = {
            name: {s.artifacts.scanned_catalog} if s.artifacts.scanned_catalog else set()
            for name, s in self.scorers.items()
        }

    async def handle(self, request: Request) -> Response:
        upstream = self.config.upstreams.get(request.path_params["route"])
        if upstream is None:
            return Response(status_code=404)
        agent = self._identify(request)
        if agent is None:
            return Response(status_code=401)

        body = await request.body()
        messages = parse_messages(body)
        exchange = _exchange(request, upstream.name, agent, messages)
        for message in messages or [None]:  # a bodiless GET/DELETE still shows up
            record = self._log(exchange, TO_SERVER, None, message)
            if message and message.get("method") == CALL_METHOD:
                self._decide(exchange, message, record["ts"])  # before it is forwarded
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
            self._log(exchange, FROM_GATEWAY, None, {"error": f"upstream unreachable: {exc}"})
            return Response(status_code=502)

        # The server assigns the session on `initialize`; carry it onto the reply's lines.
        session = reply.headers.get(SESSION_HEADER) or exchange.session
        if session and exchange.client_info:
            self.sessions.start(session, exchange.client_info)
        headers = {k: v for k, v in reply.headers.items() if k.lower() not in NOT_SENT_DOWNSTREAM}
        relay = self._relay(reply, replace(exchange, session=session))
        return StreamingResponse(relay, status_code=reply.status_code, headers=headers)

    async def _relay(self, reply: httpx.Response, exchange: Exchange) -> AsyncIterator[bytes]:
        """Yield upstream bytes unchanged; log each complete message on the side."""
        tap = MessageTap(reply.headers.get("content-type", ""))
        try:
            async for chunk in reply.aiter_raw():
                yield chunk
                for message in tap.feed(chunk):
                    self._watch_catalog(
                        exchange, self._log(exchange, TO_AGENT, reply.status_code, message)
                    )
            for message in tap.close():
                self._watch_catalog(
                    exchange, self._log(exchange, TO_AGENT, reply.status_code, message)
                )
        finally:
            await reply.aclose()
            if exchange.http_method == "DELETE":  # the client ended the session
                self.sessions.end(exchange.session)

    def _identify(self, request: Request) -> str | None:
        if not self.config.agents:
            return ANONYMOUS
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        return self.config.agents.get(token_hash(token))

    def _log(
        self, exchange: Exchange, direction: str, status: int | None, message: dict | None
    ) -> dict:
        record = build_record(exchange, self.sessions, direction, status, message)
        self.log.write(exchange.route, record)
        return record

    def _decide(self, exchange: Exchange, call: dict, ts: float) -> None:
        """Score one tools/call with the route's framework and log the verdict."""
        scorer = self.scorers.get(exchange.route)
        if scorer is None:
            return
        params = call.get("params") or {}
        try:
            decision = scorer.score(params.get("name"), params.get("arguments") or {}, ts)
        except Exception as exc:  # noqa: BLE001 — a scoring bug must never break the agent's call; it is logged, not hidden
            decision = {"error": f"{type(exc).__name__}: {exc}"}
        decision["artifacts"] = scorer.artifacts.digests
        record = decision_record(
            exchange, self.sessions, call, decision, scorer.artifacts.scanned_catalog, ts
        )
        self.log.write(exchange.route, record)

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
        notice = notice_record(
            exchange,
            "catalog_not_scanned",
            **{"gateway.catalog_sha256": digest, "gateway.catalog_file": str(path)},
        )
        self.log.write(exchange.route, notice)


def _exchange(request: Request, route: str, agent: str, messages: list[dict]) -> Exchange:
    """What the wire says about one request: who sent it, from where, in which session."""
    init = next((m for m in messages if m.get("method") == "initialize"), {})
    version = request.headers.get(PROTOCOL_HEADER) or (init.get("params") or {}).get(
        "protocolVersion"
    )
    return Exchange(
        route=route,
        agent=agent,
        session=request.headers.get(SESSION_HEADER),
        http_method=request.method,
        client_address=request.client.host if request.client else None,
        client_port=request.client.port if request.client else None,
        user_agent=request.headers.get("user-agent"),
        protocol_version=version,
        client_info=client_info_of(messages),
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


def create_app(config: GatewayConfig, client: httpx.AsyncClient | None = None) -> Starlette:
    """The gateway as an ASGI app. Pass ``client`` to point it at a test upstream."""
    owns_client = client is None
    http = client or httpx.AsyncClient(
        timeout=httpx.Timeout(CONNECT_TIMEOUT_S, read=None),  # SSE streams stay open
        follow_redirects=False,  # a redirect is the upstream's answer; relay it as-is
    )
    gateway = Gateway(config, http)

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        yield
        if owns_client:
            await http.aclose()

    return Starlette(
        routes=[
            Route("/{route}", gateway.handle, methods=METHODS),
            Route("/{route}/{rest:path}", gateway.handle, methods=METHODS),
        ],
        lifespan=lifespan,
    )


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
    uvicorn.run(create_app(config), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
