"""Launch a third-party FastMCP finance server over Streamable HTTP.

The finance MCP servers under ``external/`` default to stdio transport, but the
MITM capture stack (``run_mitm_finance.py`` → mitmdump reverse proxy →
``captured.jsonl``) needs the server to speak HTTP. This launcher imports a
server module's existing ``FastMCP`` instance, overrides its host/port, and runs
it over ``streamable-http`` — without editing the vendored server source.

Driven entirely by environment variables so one launcher fits every server:

    FIN_SERVER_DIR   directory added to sys.path so the module imports (required)
    FIN_MODULE       importable module name that defines the FastMCP instance (required)
    FIN_ATTR         attribute name in that module (required). By default it is
                     the FastMCP instance itself; if FIN_FACTORY=1 it is a
                     zero-argument factory that *returns* the FastMCP instance.
    FIN_FACTORY      "1" → call FIN_ATTR to build the instance (default: use as-is)
    FIN_HOST         bind host (default 127.0.0.1)
    FIN_PORT         bind port (default 8080)
    FIN_TRANSPORT    "sse" (default) or "streamable-http". Older FastMCP builds
                     (mcp < 1.8) only speak "sse"; both are HTTP so mitmdump
                     fronts either. If the chosen transport is rejected we fall
                     back to the other one.

Run (inside the target server's own uv environment)::

    FIN_SERVER_DIR=external/yahoo-finance-mcp FIN_MODULE=server \
    FIN_ATTR=yfinance_server FIN_PORT=8080 \
    uv run --project external/yahoo-finance-mcp python \
        logs/proxy/servers/finance_http_launcher.py
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _require(var: str) -> str:
    value = os.environ.get(var)
    if not value:
        raise SystemExit(f"finance_http_launcher: environment variable {var} is required")
    return value


def main() -> None:
    server_dir = Path(_require("FIN_SERVER_DIR")).resolve()
    module_name = _require("FIN_MODULE")
    attr = _require("FIN_ATTR")
    host = os.environ.get("FIN_HOST", "127.0.0.1")
    port = int(os.environ.get("FIN_PORT", "8080"))
    transport = os.environ.get("FIN_TRANSPORT", "sse")

    if not server_dir.is_dir():
        raise SystemExit(f"finance_http_launcher: FIN_SERVER_DIR not found: {server_dir}")
    sys.path.insert(0, str(server_dir))

    use_factory = os.environ.get("FIN_FACTORY", "").strip() in {"1", "true", "yes"}

    module = importlib.import_module(module_name)
    try:
        target = getattr(module, attr)
    except AttributeError as exc:  # noqa: BLE001
        raise SystemExit(
            f"finance_http_launcher: module {module_name!r} has no attribute {attr!r}"
        ) from exc

    if use_factory:
        if not callable(target):
            raise SystemExit(
                f"finance_http_launcher: FIN_FACTORY set but {module_name}.{attr} is not callable"
            )
        print(f"[launcher] building instance via factory {module_name}.{attr}()", flush=True)
        server = target()
    else:
        server = target

    # The classic mcp.server.fastmcp.FastMCP keeps host/port in `.settings`; the
    # standalone fastmcp 2.x FastMCP takes them as run() kwargs. Support both.
    settings = getattr(server, "settings", None)
    uses_settings = settings is not None and hasattr(settings, "port")
    if uses_settings:
        settings.host = host
        settings.port = port

    # Try the requested transport; fall back to the other HTTP transport if the
    # installed FastMCP version doesn't know it (mcp < 1.8 → sse only).
    fallback = "streamable-http" if transport == "sse" else "sse"
    for chosen in (transport, fallback):
        try:
            print(f"[launcher] {module_name}.{attr} → {chosen} on {host}:{port}", flush=True)
            if uses_settings:
                server.run(transport=chosen)
            else:
                server.run(transport=chosen, host=host, port=port)
            return
        except ValueError as exc:
            if "transport" in str(exc).lower():
                print(f"[launcher] {chosen} unavailable ({exc}); trying {fallback}", flush=True)
                continue
            raise
    raise SystemExit(f"finance_http_launcher: no usable HTTP transport for {module_name}.{attr}")


if __name__ == "__main__":
    main()
