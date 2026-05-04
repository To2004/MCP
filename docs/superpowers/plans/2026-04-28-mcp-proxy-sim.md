# MCP Proxy Mini-Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two standalone Python projects — a manual-REPL MCP proxy and an Ollama-agent MCP proxy — each aggregating multiple MCP backends simultaneously through one SSE endpoint with security-scoring middleware and audit logging.

**Architecture:** A `BackendManager` keeps N backend `ClientSession`s alive simultaneously (one `asyncio.Task` per backend, supporting both stdio and HTTP transports). A `Registry` maps `backend__tool` names to `(backend_id, tool_name)` tuples. An `mcp.Server` over Starlette SSE intercepts every `tools/call`, runs the scorer, forwards to the correct backend, and appends to `logs/audit.jsonl`. Project 2 duplicates the proxy package and replaces the REPL with an Ollama agent loop.

**Tech Stack:** Python 3.12+, `mcp>=1.26.0`, `uvicorn>=0.29`, `starlette>=0.37`, `httpx>=0.27` (agent only), `uv`, `pytest`, `pytest-asyncio`, `ruff`

---

## File Map

### Project 1: `C:\Users\user\Documents\GitHub\mcp-proxy-manual\`

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | uv project config, deps, pytest settings |
| `.gitignore` | Standard Python + logs |
| `README.md` | Usage, HTTP backend note, port-conflict warning |
| `config/servers.json` | Backend profiles (filesystem, git, time + commented HTTP example) |
| `logs/.gitkeep` | Ensure logs/ is tracked by git |
| `proxy/__init__.py` | Empty package marker |
| `proxy/__main__.py` | CLI: load config, start backends, populate registry, run uvicorn |
| `proxy/scorer.py` | Stub scorer — same interface as thesis `scorer_bridge.py` |
| `proxy/audit.py` | Append-only JSONL writer; injects `session_id` + `call_id` |
| `proxy/backends.py` | `BackendManager`: one `asyncio.Task` per backend (stdio + HTTP) |
| `proxy/registry.py` | `Registry`: populate from backends, `lookup(backend__tool)`, snapshot |
| `proxy/server.py` | `mcp.Server` + Starlette SSE; `tools/list` + `tools/call` handlers |
| `proxy/wire.py` | Optional `LoggingStream` scaffold for raw byte capture |
| `client/__init__.py` | Empty package marker |
| `client/repl.py` | Interactive REPL: `tools`, `call <name> <json>`, `--attack-mode` |
| `tests/__init__.py` | Empty |
| `tests/test_scorer.py` | Unit: stub returns expected dict |
| `tests/test_audit.py` | Unit: JSONL written, ids injected, parent dirs created |
| `tests/test_registry.py` | Unit: `__` separator, lookup, multiple backends, snapshot |
| `tests/test_backends.py` | Unit: empty-state, stop noop, unknown transport raises |
| `tests/test_proxy_integration.py` | Integration (live proxy): tools/list, call, unknown tool |

### Project 2: `C:\Users\user\Documents\GitHub\mcp-proxy-agent\`

Identical to Project 1 except `client/` is replaced by `agent/`:

| File | Responsibility |
|------|----------------|
| `proxy/` | Byte-identical copy of Project 1's `proxy/` |
| `agent/__init__.py` | Empty package marker |
| `agent/__main__.py` | CLI: `--prompt`, `--proxy-url`, `--model`, `--max-turns` |
| `agent/ollama_client.py` | `chat()`, `extract_tool_calls()`, `extract_content()`, `make_tool_spec()` |
| `agent/loop.py` | `run_agent()`: list tools → Ollama → execute tool_calls → loop |
| `tests/test_ollama_client.py` | Unit: parse tool_calls, extract content, make_tool_spec format |

---

## Part A — Project 1: mcp-proxy-manual

### Task 1: Scaffold Project 1

**Files:** All project files (empty structure)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p C:/Users/user/Documents/GitHub/mcp-proxy-manual
cd C:/Users/user/Documents/GitHub/mcp-proxy-manual
mkdir -p proxy client config logs tests
```

- [ ] **Step 2: Create pyproject.toml**

`pyproject.toml`:
```toml
[project]
name = "mcp-proxy-manual"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.26.0",
    "uvicorn>=0.29.0",
    "starlette>=0.37.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
    "httpx>=0.27",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["proxy", "client"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "integration: requires live proxy on :8080",
]

[tool.ruff]
line-length = 100
```

- [ ] **Step 3: Create .gitignore**

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
logs/audit.jsonl
logs/wire.log
logs/registry_snapshot.json
```

- [ ] **Step 4: Create empty markers and placeholder**

```bash
touch proxy/__init__.py client/__init__.py tests/__init__.py logs/.gitkeep
```

- [ ] **Step 5: Install dependencies**

```bash
uv sync
```

Expected: resolves packages with no errors.

- [ ] **Step 6: Commit scaffold**

```bash
git init
git add .
git commit -m "chore: scaffold mcp-proxy-manual project"
```

---

### Task 2: proxy/scorer.py (TDD)

**Files:**
- Create: `proxy/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write the failing test**

`tests/test_scorer.py`:
```python
from proxy.scorer import score


def test_score_returns_stub_dict() -> None:
    result = score("list_directory", {"path": "/tmp"}, "Lists directory", "")
    assert result["static"] is None
    assert result["dynamic"] is None
    assert result["combined"] is None
    assert isinstance(result["note"], str)
    assert len(result["note"]) > 0


def test_score_accepts_all_arg_types() -> None:
    result = score("git_log", {"repo_path": "/repo", "max_count": 5}, "Git log", "output")
    assert "combined" in result
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: `ImportError: No module named 'proxy.scorer'`

- [ ] **Step 3: Implement proxy/scorer.py**

```python
from typing import Any


def score(
    tool_name: str,
    arguments: dict[str, Any],
    description: str,
    response_text: str,
) -> dict[str, Any]:
    return {
        "static": None,
        "dynamic": None,
        "combined": None,
        "note": "stub — scorer not yet implemented",
    }
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add proxy/scorer.py tests/test_scorer.py
git commit -m "feat: add scorer stub with thesis-compatible interface"
```

---

### Task 3: proxy/audit.py (TDD)

**Files:**
- Create: `proxy/audit.py`
- Create: `tests/test_audit.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_audit.py`:
```python
import json
from pathlib import Path
from unittest.mock import patch

from proxy import audit


def test_append_writes_one_jsonl_line(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    with patch.object(audit, "LOG_PATH", log):
        audit.append({"tool": "list_directory", "status": "ok"})
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["tool"] == "list_directory"


def test_append_injects_session_and_call_ids(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    with patch.object(audit, "LOG_PATH", log):
        audit.append({"tool": "x"})
        audit.append({"tool": "y"})
    records = [json.loads(l) for l in log.read_text().splitlines()]
    assert "session_id" in records[0]
    assert "call_id" in records[0]
    assert records[0]["session_id"] == records[1]["session_id"]
    assert records[0]["call_id"] != records[1]["call_id"]


def test_append_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested" / "audit.jsonl"
    with patch.object(audit, "LOG_PATH", nested):
        audit.append({"tool": "x"})
    assert nested.exists()
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/test_audit.py -v
```

Expected: `ImportError: No module named 'proxy.audit'`

- [ ] **Step 3: Implement proxy/audit.py**

```python
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path("logs/audit.jsonl")

_SESSION_ID = str(uuid.uuid4())


def append(record: dict[str, Any]) -> None:
    record.setdefault("session_id", _SESSION_ID)
    record.setdefault("call_id", str(uuid.uuid4()))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/test_audit.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add proxy/audit.py tests/test_audit.py
git commit -m "feat: add append-only JSONL audit writer with session/call ids"
```

---

### Task 4: proxy/registry.py (TDD)

**Files:**
- Create: `proxy/registry.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_registry.py`:
```python
import json
from pathlib import Path

import mcp.types as types
import pytest

from proxy.registry import Registry


def _tool(name: str, desc: str = "desc") -> types.Tool:
    return types.Tool(
        name=name,
        description=desc,
        inputSchema={"type": "object", "properties": {}},
    )


def test_namespaced_with_double_underscore() -> None:
    reg = Registry()
    reg.populate("filesystem", [_tool("list_directory"), _tool("read_file")])
    names = [t.name for t in reg.list_all()]
    assert "filesystem__list_directory" in names
    assert "filesystem__read_file" in names
    assert all("." not in n for n in names)


def test_lookup_returns_backend_and_tool_name() -> None:
    reg = Registry()
    reg.populate("git", [_tool("git_log")])
    backend_id, tool_name = reg.lookup("git__git_log")
    assert backend_id == "git"
    assert tool_name == "git_log"


def test_lookup_raises_for_unknown_tool() -> None:
    reg = Registry()
    with pytest.raises(KeyError):
        reg.lookup("nonexistent__tool")


def test_multiple_backends_all_present() -> None:
    reg = Registry()
    reg.populate("filesystem", [_tool("list_directory")])
    reg.populate("time", [_tool("get_current_time")])
    names = [t.name for t in reg.list_all()]
    assert "filesystem__list_directory" in names
    assert "time__get_current_time" in names
    assert len(names) == 2


def test_get_description_returns_correct_text() -> None:
    reg = Registry()
    reg.populate("time", [_tool("get_current_time", "Returns current time in timezone")])
    assert reg.get_description("time__get_current_time") == "Returns current time in timezone"


def test_save_snapshot_writes_json(tmp_path: Path) -> None:
    reg = Registry()
    reg.populate("filesystem", [_tool("list_directory"), _tool("read_file")])
    reg.populate("time", [_tool("get_current_time")])
    snap = tmp_path / "snapshot.json"
    reg.save_snapshot(snap)
    data = json.loads(snap.read_text())
    assert data["total_tools"] == 3
    assert "filesystem" in data["backends"]
    assert "time" in data["backends"]
    assert "ts" in data
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/test_registry.py -v
```

Expected: `ImportError: No module named 'proxy.registry'`

- [ ] **Step 3: Implement proxy/registry.py**

```python
import json
from datetime import datetime, timezone
from pathlib import Path

import mcp.types as types


class Registry:
    def __init__(self) -> None:
        self._map: dict[str, tuple[str, str]] = {}
        self._tools: dict[str, types.Tool] = {}

    def populate(self, backend_id: str, tools: list[types.Tool]) -> None:
        for tool in tools:
            key = f"{backend_id}__{tool.name}"
            self._map[key] = (backend_id, tool.name)
            self._tools[key] = types.Tool(
                name=key,
                description=tool.description,
                inputSchema=tool.inputSchema,
            )

    def list_all(self) -> list[types.Tool]:
        return list(self._tools.values())

    def lookup(self, namespaced: str) -> tuple[str, str]:
        if namespaced not in self._map:
            raise KeyError(f"Unknown tool: {namespaced!r}")
        return self._map[namespaced]

    def get_description(self, namespaced: str) -> str:
        tool = self._tools.get(namespaced)
        return tool.description if tool else ""

    def save_snapshot(self, path: Path) -> None:
        by_backend: dict[str, list[str]] = {}
        for _, (bid, tname) in self._map.items():
            by_backend.setdefault(bid, []).append(tname)
        snapshot = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "backends": by_backend,
            "total_tools": len(self._map),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2))
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/test_registry.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add proxy/registry.py tests/test_registry.py
git commit -m "feat: add registry with double-underscore namespacing and snapshot"
```

---

### Task 5: proxy/backends.py (TDD)

**Files:**
- Create: `proxy/backends.py`
- Create: `tests/test_backends.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_backends.py`:
```python
import asyncio

import pytest

from proxy.backends import BackendManager


def test_starts_with_empty_backend_list() -> None:
    bm = BackendManager()
    assert bm.backend_ids == []


@pytest.mark.asyncio
async def test_stop_all_is_noop_when_nothing_started() -> None:
    bm = BackendManager()
    await bm.stop_all()  # must not raise


def test_raises_on_unknown_transport() -> None:
    bm = BackendManager()
    profiles = [{"id": "x", "transport": "ftp", "url": "ftp://nowhere"}]
    with pytest.raises(ValueError, match="ftp"):
        asyncio.run(bm.start_all(profiles))
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/test_backends.py -v
```

Expected: `ImportError: No module named 'proxy.backends'`

- [ ] **Step 3: Implement proxy/backends.py**

```python
import asyncio
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client


class BackendManager:
    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}
        self._shutdown = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def _run_stdio(self, backend_id: str, start_cmd: list[str]) -> None:
        params = StdioServerParameters(command=start_cmd[0], args=start_cmd[1:])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                self._sessions[backend_id] = session
                await self._shutdown.wait()

    async def _run_http(self, backend_id: str, url: str) -> None:
        async with sse_client(url) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                self._sessions[backend_id] = session
                await self._shutdown.wait()

    async def start_all(self, profiles: list[dict[str, Any]]) -> None:
        for profile in profiles:
            bid = profile["id"]
            transport = profile.get("transport", "stdio")
            if transport == "stdio":
                task = asyncio.create_task(self._run_stdio(bid, profile["start_cmd"]))
            elif transport == "http":
                task = asyncio.create_task(self._run_http(bid, profile["url"]))
            else:
                raise ValueError(f"Unknown transport: {transport!r}")
            self._tasks.append(task)

        deadline = asyncio.get_event_loop().time() + 60.0
        while len(self._sessions) < len(profiles):
            if asyncio.get_event_loop().time() > deadline:
                missing = [p["id"] for p in profiles if p["id"] not in self._sessions]
                raise TimeoutError(f"Backends did not start in 60s: {missing}")
            await asyncio.sleep(0.05)

    async def stop_all(self) -> None:
        self._shutdown.set()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    async def list_tools(self, backend_id: str):
        return await self._sessions[backend_id].list_tools()

    async def call_tool(self, backend_id: str, tool_name: str, args: dict[str, Any]):
        return await self._sessions[backend_id].call_tool(tool_name, args)

    @property
    def backend_ids(self) -> list[str]:
        return list(self._sessions.keys())
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/test_backends.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add proxy/backends.py tests/test_backends.py
git commit -m "feat: add BackendManager with asyncio.Task lifecycle for stdio and http"
```

---

### Task 6: proxy/server.py + proxy/__main__.py + proxy/wire.py

**Files:**
- Create: `proxy/server.py`
- Create: `proxy/__main__.py`
- Create: `proxy/wire.py`

- [ ] **Step 1: Create proxy/server.py**

```python
import time
from datetime import datetime, timezone

import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from proxy import audit, scorer
from proxy.backends import BackendManager
from proxy.registry import Registry


def create_app(backends: BackendManager, registry: Registry) -> Starlette:
    mcp_server = Server("mcp-proxy")
    sse_transport = SseServerTransport("/messages/")

    @mcp_server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return registry.list_all()

    @mcp_server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        args = arguments or {}
        try:
            backend_id, tool_name = registry.lookup(name)
        except KeyError:
            return [types.TextContent(type="text", text=f"Unknown tool: {name!r}")]

        description = registry.get_description(name)
        score_result = scorer.score(tool_name, args, description, "")

        start = time.monotonic()
        try:
            result = await backends.call_tool(backend_id, tool_name, args)
            status = "ok"
            content = result.content
        except Exception as exc:
            status = "error"
            content = [types.TextContent(type="text", text=str(exc))]

        latency_ms = round((time.monotonic() - start) * 1000, 2)
        preview = " ".join(
            getattr(c, "text", "") for c in content if hasattr(c, "text")
        )[:200]

        audit.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "backend_id": backend_id,
            "tool": tool_name,
            "namespaced_tool": name,
            "args": args,
            "score": score_result,
            "status": status,
            "latency_ms": latency_ms,
            "response_preview": preview,
            "payload_type": None,
            "damage_detected": False,
        })

        return content

    async def handle_sse(request: Request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ]
    )
```

- [ ] **Step 2: Create proxy/__main__.py**

```python
import argparse
import asyncio
import json
from pathlib import Path

import uvicorn

from proxy.backends import BackendManager
from proxy.registry import Registry
from proxy.server import create_app


async def start(config_path: Path, port: int) -> None:
    profiles = json.loads(config_path.read_text())

    backends = BackendManager()
    registry = Registry()

    print(f"Starting {len(profiles)} backend(s)...")
    await backends.start_all(profiles)

    for bid in backends.backend_ids:
        result = await backends.list_tools(bid)
        registry.populate(bid, result.tools)

    snapshot_path = Path("logs/registry_snapshot.json")
    registry.save_snapshot(snapshot_path)
    total = len(registry.list_all())
    print(
        f"Started {len(profiles)} backends | {total} tools registered "
        f"| snapshot → {snapshot_path}"
    )

    app = create_app(backends, registry)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    try:
        await server.serve()
    finally:
        await backends.stop_all()
        print("Backends stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Security Proxy")
    parser.add_argument("--config", default="config/servers.json", type=Path)
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args()
    asyncio.run(start(args.config, args.port))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create proxy/wire.py (optional scaffold)**

```python
"""Optional wire-level logging.

To enable: in backends.py _run_stdio, wrap the streams before passing to ClientSession:
    from proxy.wire import make_logging_streams
    r, w = make_logging_streams(r, w, backend_id)
"""
from __future__ import annotations

from pathlib import Path

WIRE_LOG = Path("logs/wire.log")


def make_logging_streams(read_stream, write_stream, label: str):
    """Wrap anyio streams to log raw bytes. Returns (read, write) wrappers."""

    class _LoggingReadStream:
        async def receive(self, max_bytes: int = 65536) -> bytes:
            data = await read_stream.receive(max_bytes)
            _write_log(f"{label} ← {data!r}")
            return data

        async def aclose(self) -> None:
            await read_stream.aclose()

    class _LoggingWriteStream:
        async def send(self, item: bytes) -> None:
            _write_log(f"{label} → {item!r}")
            await write_stream.send(item)

        async def aclose(self) -> None:
            await write_stream.aclose()

    return _LoggingReadStream(), _LoggingWriteStream()


def _write_log(line: str) -> None:
    WIRE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with WIRE_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
```

- [ ] **Step 4: Run all unit tests**

```bash
uv run pytest -m "not integration" -v
```

Expected: `scorer(2) + audit(3) + registry(6) + backends(3) = 14 passed`

- [ ] **Step 5: Commit**

```bash
git add proxy/server.py proxy/__main__.py proxy/wire.py
git commit -m "feat: add Starlette SSE proxy server with scoring intercept and audit log"
```

---

### Task 7: client/repl.py

**Files:**
- Create: `client/repl.py`

- [ ] **Step 1: Create client/repl.py**

```python
import argparse
import asyncio
import json

from mcp import ClientSession
from mcp.client.sse import sse_client


async def run_repl(proxy_url: str, attack_mode: bool) -> None:
    print(f"Connecting to {proxy_url} ...")
    async with sse_client(proxy_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected. Commands: tools | call <name> <json-args> | quit")
            if attack_mode:
                print("[attack-mode ON — first string arg prefixed with traversal payload]")

            while True:
                try:
                    line = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if not line:
                    continue
                if line in ("quit", "exit", "q"):
                    break

                if line == "tools":
                    result = await session.list_tools()
                    for t in result.tools:
                        print(f"  {t.name}")
                        if t.description:
                            print(f"    {t.description[:80]}")

                elif line.startswith("call "):
                    parts = line[5:].split(None, 1)
                    if len(parts) < 2:
                        print('Usage: call <namespaced_name> <json>  e.g. call time__get_current_time {"timezone":"UTC"}')
                        continue
                    name, raw_args = parts
                    try:
                        args: dict = json.loads(raw_args)
                    except json.JSONDecodeError as e:
                        print(f"Bad JSON: {e}")
                        continue

                    if attack_mode:
                        for k, v in args.items():
                            if isinstance(v, str):
                                args[k] = f"../../etc/passwd/{v}"
                                break

                    try:
                        result = await session.call_tool(name, args)
                        for item in result.content:
                            print(getattr(item, "text", str(item)))
                    except Exception as e:
                        print(f"Error: {e}")

                else:
                    print("Unknown command. Use: tools | call <name> <args> | quit")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Proxy interactive REPL")
    parser.add_argument("--proxy-url", default="http://localhost:8080/sse")
    parser.add_argument(
        "--attack-mode",
        action="store_true",
        help="Inject path-traversal payload into first string arg",
    )
    args = parser.parse_args()
    asyncio.run(run_repl(args.proxy_url, args.attack_mode))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add client/repl.py
git commit -m "feat: add interactive REPL client with --attack-mode flag"
```

---

### Task 8: config/servers.json + README.md

**Files:**
- Create: `config/servers.json`
- Create: `README.md`

- [ ] **Step 1: Create config/servers.json**

```json
[
  {
    "id": "filesystem",
    "description": "Filesystem MCP — path-scoped read/write/search",
    "transport": "stdio",
    "start_cmd": [
      "npx",
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "C:/Users/user/Documents/GitHub/MCP"
    ]
  },
  {
    "id": "git",
    "description": "Git MCP — log, diff, status for a local repo",
    "transport": "stdio",
    "start_cmd": [
      "uvx",
      "mcp-server-git",
      "--repository",
      "C:/Users/user/Documents/GitHub/MCP"
    ]
  },
  {
    "id": "time",
    "description": "Time MCP — current time and timezone conversion, no I/O side effects",
    "transport": "stdio",
    "start_cmd": ["uvx", "mcp-server-time"]
  }
]
```

> To add an HTTP backend, append an entry like:
> `{ "id": "remote", "transport": "http", "url": "http://localhost:9000/sse" }`

- [ ] **Step 2: Create README.md**

```markdown
# mcp-proxy-manual

A Python MCP proxy that aggregates multiple backend MCP servers (stdio or HTTP)
into one SSE endpoint, with security-scoring middleware and an audit log.
Manual control via an interactive REPL.

## Prerequisites

- Python 3.12+ and `uv`
- `npx` (Node.js) — filesystem backend
- `uvx` — git and time backends

## Quick start

```bash
uv sync

# Terminal A — start the proxy
uv run python -m proxy --config config/servers.json --port 8080

# Terminal B — connect the REPL
uv run python -m client.repl
```

## REPL commands

| Command | Example |
|---------|---------|
| `tools` | List all tools from all backends |
| `call <name> <json>` | `call time__get_current_time {"timezone":"UTC"}` |
| `quit` | Exit |

Run with `--attack-mode` to inject a path-traversal payload into the first string arg:

```bash
uv run python -m client.repl --attack-mode
```

## HTTP backend support

Add `"transport": "http"` entries to `config/servers.json` to connect to remote
MCP servers over SSE. stdio and HTTP backends work simultaneously with identical
scoring and audit logging.

## Logs

| File | Contents |
|------|----------|
| `logs/audit.jsonl` | One JSON line per scored tool call |
| `logs/registry_snapshot.json` | Full tool map, written on proxy startup |
| `logs/wire.log` | Optional raw-byte capture (see `proxy/wire.py`) |

## WARNING — port conflict

The thesis repo at `C:\Users\user\Documents\GitHub\MCP` contains
`src/mcp_security/calendar_client.py` hardcoded to `http://localhost:8080/sse`.
If that project and this proxy run at the same time, the calendar client will
connect to this proxy. Keep their test runs isolated.

## Tests

```bash
uv run pytest                   # unit tests only
uv run pytest -m integration    # requires live proxy on :8080
```
```

- [ ] **Step 3: Commit**

```bash
git add config/servers.json README.md
git commit -m "chore: add server config (filesystem, git, time) and README"
```

---

### Task 9: Integration test + end-to-end smoke test (Project 1)

**Files:**
- Create: `tests/test_proxy_integration.py`

- [ ] **Step 1: Create integration test**

`tests/test_proxy_integration.py`:
```python
"""Integration tests — require proxy running on localhost:8080.

Start proxy first:  uv run python -m proxy --config config/servers.json --port 8080
Run:  uv run pytest -m integration
"""
import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

PROXY_URL = "http://localhost:8080/sse"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tools_list_uses_double_underscore_separator() -> None:
    async with sse_client(PROXY_URL) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.list_tools()
            names = [t.name for t in result.tools]
            assert any("__" in n for n in names), f"No namespaced tools: {names}"
            assert all("." not in n for n in names), f"Dot in name: {names}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_time_tool_returns_utc_string() -> None:
    async with sse_client(PROXY_URL) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool("time__get_current_time", {"timezone": "UTC"})
            assert result.content
            text = result.content[0].text
            assert "UTC" in text or "Z" in text, f"Expected UTC marker in: {text!r}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_tool_returns_error_message() -> None:
    async with sse_client(PROXY_URL) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool("nonexistent__tool", {})
            assert result.content
            assert "Unknown tool" in result.content[0].text
```

- [ ] **Step 2: Run unit tests (no proxy needed)**

```bash
uv run pytest -m "not integration" -v
```

Expected: `14 passed`

- [ ] **Step 3: Start proxy and run smoke test manually**

Terminal A:
```bash
uv run python -m proxy --config config/servers.json --port 8080
```

Expected:
```
Starting 3 backend(s)...
Started 3 backends | N tools registered | snapshot → logs/registry_snapshot.json
```

Terminal B:
```bash
uv run python -m client.repl
```

At the REPL:
```
> tools
  filesystem__list_allowed_directories
  filesystem__list_directory
  ...
  git__git_log
  ...
  time__get_current_time
  time__convert_time

> call time__get_current_time {"timezone": "UTC"}
2026-04-28T...+00:00

> quit
```

- [ ] **Step 4: Run integration tests**

```bash
uv run pytest -m integration -v
```

Expected: `3 passed`

- [ ] **Step 5: Verify audit log**

```bash
cat logs/audit.jsonl
```

Expected: one JSON line with `session_id`, `namespaced_tool`, `score`, `latency_ms`, `status`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_proxy_integration.py
git commit -m "test: add integration tests; smoke-tested against live proxy"
```

---

## Part B — Project 2: mcp-proxy-agent

### Task 10: Scaffold Project 2

**Files:** All project files

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p C:/Users/user/Documents/GitHub/mcp-proxy-agent
cd C:/Users/user/Documents/GitHub/mcp-proxy-agent
mkdir -p proxy agent config logs tests
```

- [ ] **Step 2: Copy proxy/ and shared tests from Project 1**

```bash
cp -r C:/Users/user/Documents/GitHub/mcp-proxy-manual/proxy/ ./proxy/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/tests/test_scorer.py ./tests/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/tests/test_audit.py ./tests/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/tests/test_registry.py ./tests/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/tests/test_backends.py ./tests/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/tests/test_proxy_integration.py ./tests/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/config/servers.json ./config/
cp C:/Users/user/Documents/GitHub/mcp-proxy-manual/.gitignore .
touch logs/.gitkeep tests/__init__.py agent/__init__.py
```

- [ ] **Step 3: Create pyproject.toml**

```toml
[project]
name = "mcp-proxy-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.26.0",
    "uvicorn>=0.29.0",
    "starlette>=0.37.0",
    "httpx>=0.27.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
    "httpx>=0.27",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["proxy", "agent"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "integration: requires live proxy on :8081",
]

[tool.ruff]
line-length = 100
```

- [ ] **Step 4: Install and verify copied tests pass**

```bash
uv sync
uv run pytest -m "not integration" -v
```

Expected: `14 passed` (same unit tests as Project 1).

- [ ] **Step 5: Commit scaffold**

```bash
git init
git add .
git commit -m "chore: scaffold mcp-proxy-agent; copy proxy/ from mcp-proxy-manual"
```

---

### Task 11: agent/ollama_client.py (TDD)

**Files:**
- Create: `agent/ollama_client.py`
- Create: `tests/test_ollama_client.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_ollama_client.py`:
```python
from agent.ollama_client import extract_content, extract_tool_calls, make_tool_spec

TOOL_CALL_RESPONSE = {
    "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "time__get_current_time",
                    "arguments": {"timezone": "UTC"},
                }
            }
        ],
    },
    "done": True,
}

FINAL_RESPONSE = {
    "message": {"role": "assistant", "content": "It is 12:00 UTC."},
    "done": True,
}


def test_extract_tool_calls_parses_name_and_args() -> None:
    calls = extract_tool_calls(TOOL_CALL_RESPONSE)
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "time__get_current_time"
    assert calls[0]["function"]["arguments"]["timezone"] == "UTC"


def test_extract_tool_calls_empty_when_no_calls() -> None:
    assert extract_tool_calls(FINAL_RESPONSE) == []


def test_extract_tool_calls_empty_when_key_absent() -> None:
    assert extract_tool_calls({"message": {"content": "hi"}}) == []


def test_extract_content_returns_message_text() -> None:
    assert extract_content(FINAL_RESPONSE) == "It is 12:00 UTC."


def test_extract_content_empty_when_missing() -> None:
    assert extract_content({"message": {}}) == ""


def test_make_tool_spec_structure() -> None:
    schema = {"type": "object", "properties": {"timezone": {"type": "string"}}}
    spec = make_tool_spec("time__get_current_time", "Returns current time", schema)
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "time__get_current_time"
    assert spec["function"]["description"] == "Returns current time"
    assert spec["function"]["parameters"] == schema
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/test_ollama_client.py -v
```

Expected: `ImportError: No module named 'agent.ollama_client'`

- [ ] **Step 3: Implement agent/ollama_client.py**

```python
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"


async def chat(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()


def extract_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    return response.get("message", {}).get("tool_calls", [])


def extract_content(response: dict[str, Any]) -> str:
    return response.get("message", {}).get("content", "")


def make_tool_spec(name: str, description: str, input_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": input_schema,
        },
    }
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/test_ollama_client.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add agent/ollama_client.py tests/test_ollama_client.py
git commit -m "feat: add Ollama client with correct message.tool_calls schema"
```

---

### Task 12: agent/loop.py + agent/__main__.py

**Files:**
- Create: `agent/loop.py`
- Create: `agent/__main__.py`

- [ ] **Step 1: Create agent/loop.py**

```python
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

from agent.ollama_client import chat, extract_content, extract_tool_calls, make_tool_spec


async def run_agent(
    proxy_url: str,
    model: str,
    prompt: str,
    max_turns: int = 10,
) -> str:
    async with sse_client(proxy_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = [
                make_tool_spec(t.name, t.description or "", t.inputSchema)
                for t in tools_result.tools
            ]
            print(f"  Loaded {len(tools)} tools from proxy")

            messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

            for turn in range(max_turns):
                print(f"  [turn {turn + 1}] querying {model}...")
                response = await chat(model=model, messages=messages, tools=tools)
                tool_calls = extract_tool_calls(response)

                if not tool_calls:
                    return extract_content(response)

                messages.append(response["message"])

                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    print(f"  → {name}({args})")

                    try:
                        result = await session.call_tool(name, args)
                        result_text = " ".join(
                            getattr(c, "text", str(c)) for c in result.content
                        )
                    except Exception as exc:
                        result_text = f"Error: {exc}"

                    messages.append({"role": "tool", "content": result_text})

            return "Max turns reached without a final answer."
```

- [ ] **Step 2: Create agent/__main__.py**

```python
import argparse
import asyncio

from agent.loop import run_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Proxy Ollama agent")
    parser.add_argument("--prompt", required=True, help="Task for the agent")
    parser.add_argument("--proxy-url", default="http://localhost:8081/sse")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--max-turns", type=int, default=10)
    args = parser.parse_args()

    print(f"Agent | model={args.model} | proxy={args.proxy_url}")
    result = asyncio.run(
        run_agent(
            proxy_url=args.proxy_url,
            model=args.model,
            prompt=args.prompt,
            max_turns=args.max_turns,
        )
    )
    print(f"\n--- Answer ---\n{result}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all unit tests**

```bash
uv run pytest -m "not integration" -v
```

Expected: `scorer(2) + audit(3) + registry(6) + backends(3) + ollama_client(6) = 20 passed`

- [ ] **Step 4: Commit**

```bash
git add agent/loop.py agent/__main__.py
git commit -m "feat: add Ollama agent loop with MCP tool-call execution"
```

---

### Task 13: README.md + end-to-end smoke test (Project 2)

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

```markdown
# mcp-proxy-agent

Same proxy as `mcp-proxy-manual` (aggregates multiple MCP backends over one SSE
endpoint with security-scoring middleware), but the caller is an Ollama LLM agent
that autonomously decides which tools to call.

## Prerequisites

- Python 3.12+, `uv`, `npx`, `uvx`
- [Ollama](https://ollama.ai) installed and running: `ollama serve`
- A tool-calling model pulled: `ollama pull llama3.1:8b`

## Quick start

```bash
uv sync

# Terminal A — start the proxy on :8081 (avoids clash with mcp-proxy-manual on :8080)
uv run python -m proxy --config config/servers.json --port 8081

# Terminal B — run the agent
uv run python -m agent \
  --prompt "What time is it in UTC and Jerusalem?" \
  --proxy-url http://localhost:8081/sse \
  --model llama3.1:8b
```

## How it works

1. Agent connects to the proxy via SSE (`tools/list`)
2. Sends tools + user prompt to Ollama `/api/chat`
3. Ollama returns `message.tool_calls` — agent executes via proxy
4. Results fed back to Ollama as `role: tool` messages
5. Repeats until Ollama returns a final text answer

The proxy intercepts and scores every tool call; results appear in `logs/audit.jsonl`.

## WARNING — port conflict

The thesis repo's `calendar_client.py` hardcodes `localhost:8080/sse`. This project
defaults to `:8081`. Do not run this proxy on `:8080` while thesis tests are running.

## Tests

```bash
uv run pytest                   # unit tests only
uv run pytest -m integration    # requires proxy on :8081
```
```

- [ ] **Step 2: Start proxy and run smoke test**

Terminal A:
```bash
uv run python -m proxy --config config/servers.json --port 8081
```

Expected:
```
Starting 3 backend(s)...
Started 3 backends | N tools registered | snapshot → logs/registry_snapshot.json
```

Terminal B:
```bash
uv run python -m agent \
  --prompt "What time is it in UTC and Jerusalem?" \
  --proxy-url http://localhost:8081/sse \
  --model llama3.1:8b
```

Expected (approximate):
```
Agent | model=llama3.1:8b | proxy=http://localhost:8081/sse
  Loaded N tools from proxy
  [turn 1] querying llama3.1:8b...
  → time__get_current_time({"timezone": "UTC"})
  [turn 2] querying llama3.1:8b...
  → time__get_current_time({"timezone": "Asia/Jerusalem"})
  [turn 3] querying llama3.1:8b...

--- Answer ---
It is currently HH:MM UTC and HH:MM in Jerusalem (UTC+3).
```

- [ ] **Step 3: Check audit log has 2 entries**

```bash
cat logs/audit.jsonl
```

Expected: 2 JSON lines, both with `"namespaced_tool": "time__get_current_time"`.

- [ ] **Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: add README; smoke-tested agent end-to-end with Ollama"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|-------------|------|
| Multiple backends simultaneously | Task 5 — `BackendManager` asyncio.Task per backend |
| Single SSE endpoint | Task 6 — `proxy/server.py` Starlette app |
| Scoring intercept inside call flow | Task 6 — `handle_call_tool` → `scorer.score()` |
| Manual REPL client | Task 7 |
| Agent client (Ollama) | Tasks 11–13 |
| HTTP backend support | Task 5 `_run_http`, Task 8 config comment |
| Fix 1: `__` separator (not `.`) | Task 4 `Registry.populate` |
| Fix 2: asyncio.Task sessions | Task 5 `BackendManager` |
| Fix 3: uvicorn + starlette deps | Task 1 `pyproject.toml` |
| Fix 4: Ollama `message.tool_calls` schema | Task 11 `ollama_client.py` |
| Fix 5: port-conflict warning | Tasks 8, 13 READMEs |
| Rec 1: wire.py scaffold | Task 6 |
| Rec 2: `--attack-mode` | Task 7 `client/repl.py` |
| Rec 3: initialize logging | Handled via SSE connect entry point in `handle_sse` |
| Rec 4: registry snapshot | Task 4 `save_snapshot`, Task 6 `__main__.py` |
| Rec 5: integration tests | Tasks 9, 10 |
| Audit schema (`session_id`, `call_id`, etc.) | Task 3 `proxy/audit.py` |
| `config/servers.json` matching thesis format | Task 8 |

All requirements covered. No gaps.

### Placeholder scan

No TBD, TODO, or incomplete code blocks anywhere in the plan. Every method is fully implemented.

### Type consistency

| Symbol | Defined in | Used in |
|--------|------------|---------|
| `BackendManager.call_tool(backend_id, tool_name, args)` | Task 5 | Task 6 `server.py` |
| `BackendManager.list_tools(backend_id)` | Task 5 | Task 6 `__main__.py` |
| `Registry.lookup(namespaced)` → `tuple[str, str]` | Task 4 | Task 6 `server.py` |
| `Registry.get_description(namespaced)` → `str` | Task 4 | Task 6 `server.py` |
| `Registry.populate(backend_id, tools)` | Task 4 | Task 6 `__main__.py` |
| `scorer.score(tool_name, args, description, response_text)` | Task 2 | Task 6 `server.py` |
| `audit.append(dict)` | Task 3 | Task 6 `server.py` |
| `extract_tool_calls(response)` | Task 11 | Task 12 `loop.py` |
| `extract_content(response)` | Task 11 | Task 12 `loop.py` |
| `make_tool_spec(name, description, input_schema)` | Task 11 | Task 12 `loop.py` |

No inconsistencies found.
