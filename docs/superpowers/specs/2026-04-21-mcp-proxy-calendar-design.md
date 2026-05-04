# MCP Proxy + Google Calendar — Design Spec

Connect a Python MCP client to the `google-calendar-mcp` server via `mcp-proxy`, establishing a proxied channel to call real Google Calendar tools.

## Goal

Get a working end-to-end flow: client → proxy → Calendar server → Google Calendar API. Use the 12 available tools (list events, create event, etc.). No risk scoring in this phase — baseline connectivity only.

## Architecture

```
[Python MCP Client]
        |
        | HTTP/SSE (localhost:8080)
        v
[mcp-proxy]
        |
        | stdio
        v
[npx @cocal/google-calendar-mcp]
        |
        | HTTPS (OAuth 2.0)
        v
[Google Calendar API]
```

## Components

### 1. Google OAuth Credentials
- Create a Google Cloud project
- Enable the Google Calendar API
- Create OAuth 2.0 credentials (Desktop application type)
- Add your email as a test user on the OAuth consent screen
- Download `credentials.json`, set path via `GOOGLE_OAUTH_CREDENTIALS` env var
- Run `npx @cocal/google-calendar-mcp auth` once to complete browser OAuth flow

### 2. google-calendar-mcp (stdio server)
- Run via: `npx @cocal/google-calendar-mcp`
- Transport: stdio
- Exposes 12 tools: `list-calendars`, `list-events`, `search-events`, `create-event`, `update-event`, `delete-event`, `respond-to-event`, `get-freebusy`, `get-current-time`, `list-colors`, `manage-accounts`

### 3. mcp-proxy (transport bridge)
- Install: `uv tool install git+https://github.com/sparfenyuk/mcp-proxy`
- Wraps the stdio server and exposes an SSE endpoint on port 8080
- Run: `mcp-proxy --port 8080 -- npx @cocal/google-calendar-mcp`

### 4. Python MCP Client
- Uses the `mcp` Python SDK
- Connects to `http://localhost:8080/sse`
- Actions: list tools, call tools, print responses

## Run Sequence

```bash
# Terminal 1 — proxy wrapping the calendar server
GOOGLE_OAUTH_CREDENTIALS=/path/to/credentials.json \
mcp-proxy --port 8080 -- npx @cocal/google-calendar-mcp

# Terminal 2 — Python client
uv run python -m mcp_security.main
```

## Success Criteria

1. `mcp-proxy` starts without error
2. Python client connects and receives tool list (12 tools)
3. Client calls `list-calendars` and gets a real response
4. Client calls `list-events` and gets real calendar events

## Out of Scope (this phase)

- Risk scoring or attack simulation
- Context Forge / IBM gateway
- Any production deployment
