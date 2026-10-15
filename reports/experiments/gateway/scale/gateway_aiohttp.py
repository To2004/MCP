"""Experiment: the same gateway (logging, scoring, catalog check), aiohttp as upstream client.

Not part of the gateway: it tests whether the per-process collapse under concurrency is
httpx/httpcore's connection pool (profiled: 70% of the time in
``_assign_requests_to_connections`` at 256 agents). aiohttp is not a project dependency, so
this runs from a separate venv with the repo's ``src`` on PYTHONPATH:

    uv venv runs/exp-venv-aiohttp && uv pip install --python runs/exp-venv-aiohttp/bin/python \
        aiohttp uvicorn starlette httpx requests
    PYTHONPATH=src runs/exp-venv-aiohttp/bin/python gateway_aiohttp.py routes.json 18800
"""

import sys
from dataclasses import replace
from pathlib import Path

import aiohttp
import httpx
import uvicorn
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from mcp_security.gateway import proxy
from mcp_security.gateway.oauth import AuthError
from mcp_security.gateway.wire_log import CALL_METHOD, TO_AGENT, TO_SERVER


class AioGateway(proxy.Gateway):
    session: aiohttp.ClientSession | None = None

    async def handle(self, request: Request) -> Response:
        upstream = self.config.upstreams.get(request.path_params["route"])
        if upstream is None:
            return Response(status_code=404)
        try:
            agent = await self._identify(request, upstream.name)
        except AuthError as refused:
            return self._unauthorized(upstream.name, refused.reason)
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=0), auto_decompress=False)
        body = await request.body()
        messages = proxy.parse_messages(body)
        exchange = proxy._exchange(request, upstream.name, agent, messages)
        for message in messages or [None]:
            record = self._log(exchange, TO_SERVER, None, message)
            if message and message.get("method") == CALL_METHOD:
                self._schedule(upstream, exchange, message, record["ts"])
        try:
            reply = await self.session.request(
                request.method, proxy._target_url(upstream.url, request),
                headers=proxy._upstream_headers(request, upstream), data=body)
        except aiohttp.ClientError:
            return Response(status_code=502)
        session = reply.headers.get(proxy.SESSION_HEADER) or exchange.session
        if session and exchange.client_info:
            self.sessions.start(session, exchange.client_info)
        headers = {k: v for k, v in reply.headers.items()
                   if k.lower() not in proxy.NOT_SENT_DOWNSTREAM}
        return StreamingResponse(self._relay_aio(reply, replace(exchange, session=session)),
                                 status_code=reply.status, headers=headers)

    async def _relay_aio(self, reply: aiohttp.ClientResponse, exchange):
        tap = proxy.MessageTap(reply.headers.get("content-type", ""))
        try:
            async for chunk in reply.content.iter_any():
                yield chunk
                for message in tap.feed(chunk):
                    self._watch_catalog(exchange, self._log(exchange, TO_AGENT, reply.status, message))
            for message in tap.close():
                self._watch_catalog(exchange, self._log(exchange, TO_AGENT, reply.status, message))
        finally:
            reply.release()


config_path, port = Path(sys.argv[1]), int(sys.argv[2])
config = proxy.load_config(config_path)
proxy.Gateway = AioGateway  # create_app builds the gateway from this name
app = proxy.create_app(config, client=httpx.AsyncClient())
uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
