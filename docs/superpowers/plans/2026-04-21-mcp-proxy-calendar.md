# MCP Proxy + Google Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect a Python MCP client through `mcp-proxy` to the `google-calendar-mcp` server and successfully call real Google Calendar tools.

**Architecture:** Python client connects via SSE to `mcp-proxy` on port 8080; `mcp-proxy` spawns `npx @cocal/google-calendar-mcp` as a stdio child process; the calendar server authenticates to Google Calendar API via OAuth 2.0.

**Tech Stack:** Python 3.12, `mcp>=1.26.0`, `pytest-asyncio`, `mcp-proxy` (uv tool), Node.js / npx, Google OAuth 2.0

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/mcp_security/calendar_client.py` | Create | Async functions: `list_tools`, `call_tool`, `demo` |
| `src/mcp_security/main.py` | Modify | Entry point — calls `asyncio.run(demo())` |
| `tests/test_calendar_client.py` | Create | Unit tests with mocked MCP session |
| `pyproject.toml` | Modify | Add `pytest-asyncio`, set `asyncio_mode = "auto"` |

---

## Task 1: Google OAuth credentials (manual setup)

No code — do this before running anything.

- [ ] **Step 1: Create a Google Cloud project**

  Go to https://console.cloud.google.com → New Project → name it `mcp-calendar-test`.

- [ ] **Step 2: Enable Calendar API**

  In the project: APIs & Services → Enable APIs → search "Google Calendar API" → Enable.

- [ ] **Step 3: Create OAuth credentials**

  APIs & Services → Credentials → Create Credentials → OAuth client ID → Application type: **Desktop app** → name it `mcp-client` → Download JSON → save as `credentials.json` in the repo root.

- [ ] **Step 4: Add test user**

  APIs & Services → OAuth consent screen → Test users → Add your Google email.

- [ ] **Step 5: Verify file exists**

  ```bash
  ls credentials.json
  ```
  Expected: file exists, roughly 200-400 bytes of JSON.

- [ ] **Step 6: Add credentials.json to .gitignore**

  ```bash
  echo "credentials.json" >> .gitignore
  echo "token*.json" >> .gitignore
  git add .gitignore
  git commit -m "chore: ignore OAuth credential files"
  ```

---

## Task 2: Install mcp-proxy and pytest-asyncio

- [ ] **Step 1: Install mcp-proxy**

  ```bash
  uv tool install git+https://github.com/sparfenyuk/mcp-proxy
  ```

  Verify:
  ```bash
  mcp-proxy --help
  ```
  Expected: usage/help text printed with `--port`, `--host` options listed.

- [ ] **Step 2: Add pytest-asyncio to dev dependencies**

  ```bash
  uv add --dev pytest-asyncio
  ```

- [ ] **Step 3: Configure asyncio mode in pyproject.toml**

  In `pyproject.toml`, update the `[tool.pytest.ini_options]` section:

  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["src", "."]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  ```

- [ ] **Step 4: Verify pytest still works**

  ```bash
  uv run pytest
  ```
  Expected: all existing tests pass (or "no tests ran" if empty).

- [ ] **Step 5: Commit**

  ```bash
  git add pyproject.toml uv.lock
  git commit -m "chore: add pytest-asyncio, configure asyncio_mode=auto"
  ```

---

## Task 3: Write the calendar client module

- [ ] **Step 1: Write the failing tests first**

  Create `tests/test_calendar_client.py`:

  ```python
  import pytest
  from unittest.mock import AsyncMock, MagicMock, patch


  @pytest.mark.asyncio
  async def test_list_tools_initializes_session_and_returns_tools():
      mock_tool = MagicMock()
      mock_tool.name = "list-calendars"
      mock_session = AsyncMock()
      mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

      with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
           patch("mcp_security.calendar_client.ClientSession") as mock_cls:
          mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
          mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
          mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
          mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

          from mcp_security.calendar_client import list_tools
          tools = await list_tools("http://localhost:8080/sse")

      mock_session.initialize.assert_called_once()
      mock_session.list_tools.assert_called_once()
      assert tools == [mock_tool]


  @pytest.mark.asyncio
  async def test_call_tool_passes_name_and_arguments():
      mock_content = MagicMock()
      mock_result = MagicMock(content=[mock_content])
      mock_session = AsyncMock()
      mock_session.call_tool.return_value = mock_result

      with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
           patch("mcp_security.calendar_client.ClientSession") as mock_cls:
          mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
          mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
          mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
          mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

          from mcp_security.calendar_client import call_tool
          result = await call_tool("list-calendars", {}, "http://localhost:8080/sse")

      mock_session.initialize.assert_called_once()
      mock_session.call_tool.assert_called_once_with("list-calendars", {})
      assert result == mock_result


  @pytest.mark.asyncio
  async def test_call_tool_defaults_arguments_to_empty_dict():
      mock_session = AsyncMock()
      mock_session.call_tool.return_value = MagicMock(content=[])

      with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
           patch("mcp_security.calendar_client.ClientSession") as mock_cls:
          mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
          mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
          mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
          mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

          from mcp_security.calendar_client import call_tool
          await call_tool("get-current-time", url="http://localhost:8080/sse")

      mock_session.call_tool.assert_called_once_with("get-current-time", {})
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```bash
  uv run pytest tests/test_calendar_client.py -v
  ```
  Expected: `ImportError` or `ModuleNotFoundError` — `calendar_client` does not exist yet.

- [ ] **Step 3: Create the client module**

  Create `src/mcp_security/calendar_client.py`:

  ```python
  import asyncio
  from mcp import ClientSession
  from mcp.client.sse import sse_client

  PROXY_URL = "http://localhost:8080/sse"


  async def list_tools(url: str = PROXY_URL) -> list:
      async with sse_client(url) as (read, write):
          async with ClientSession(read, write) as session:
              await session.initialize()
              result = await session.list_tools()
              return result.tools


  async def call_tool(name: str, arguments: dict | None = None, url: str = PROXY_URL):
      if arguments is None:
          arguments = {}
      async with sse_client(url) as (read, write):
          async with ClientSession(read, write) as session:
              await session.initialize()
              return await session.call_tool(name, arguments)


  async def demo(url: str = PROXY_URL) -> None:
      print(f"Connecting to {url} ...")

      tools = await list_tools(url)
      print(f"\nAvailable tools ({len(tools)}):")
      for tool in tools:
          print(f"  - {tool.name}: {tool.description}")

      print("\nCalling list-calendars ...")
      result = await call_tool("list-calendars", url=url)
      for item in result.content:
          print(f"  {item}")

      print("\nCalling get-current-time ...")
      result = await call_tool("get-current-time", url=url)
      for item in result.content:
          print(f"  {item}")
  ```

- [ ] **Step 4: Run tests — expect pass**

  ```bash
  uv run pytest tests/test_calendar_client.py -v
  ```
  Expected:
  ```
  PASSED test_list_tools_initializes_session_and_returns_tools
  PASSED test_call_tool_passes_name_and_arguments
  PASSED test_call_tool_defaults_arguments_to_empty_dict
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add src/mcp_security/calendar_client.py tests/test_calendar_client.py
  git commit -m "feat: add MCP calendar client with list_tools and call_tool"
  ```

---

## Task 4: Update main.py to run the demo

- [ ] **Step 1: Replace main.py content**

  `src/mcp_security/main.py`:

  ```python
  import asyncio
  from mcp_security.calendar_client import demo


  def main() -> None:
      asyncio.run(demo())


  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Run all tests**

  ```bash
  uv run pytest -v
  ```
  Expected: all tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add src/mcp_security/main.py
  git commit -m "feat: wire calendar demo into main entry point"
  ```

---

## Task 5: Run the full stack end-to-end

- [ ] **Step 1: Complete OAuth flow (first time only)**

  ```bash
  GOOGLE_OAUTH_CREDENTIALS=./credentials.json npx @cocal/google-calendar-mcp auth
  ```
  Expected: browser opens → sign in → "Authentication successful" message in terminal.

- [ ] **Step 2: Start the proxy (Terminal 1)**

  ```bash
  GOOGLE_OAUTH_CREDENTIALS=./credentials.json mcp-proxy --port 8080 -- npx @cocal/google-calendar-mcp
  ```
  Expected: output like `Starting MCP proxy on port 8080` with no errors.

- [ ] **Step 3: Run the Python client (Terminal 2)**

  ```bash
  uv run python -m mcp_security.main
  ```
  Expected output:
  ```
  Connecting to http://localhost:8080/sse ...

  Available tools (12):
    - list-calendars: Display available calendars
    - list-events: Retrieve events with date filtering
    ...

  Calling list-calendars ...
    [your Google calendars listed here]

  Calling get-current-time ...
    [current time in your calendar timezone]
  ```

- [ ] **Step 4: Verify success criteria**

  - [ ] Proxy started without error
  - [ ] Tool list contains 12 tools
  - [ ] `list-calendars` returns real calendar names
  - [ ] `get-current-time` returns a valid timestamp
