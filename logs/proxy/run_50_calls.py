"""
50 varied MCP tool calls against the google-calendar-mcp proxy.
Logs every call (tool, args, result/error, category) to calls.log.
"""

import asyncio
import json
import logging
import time
from datetime import datetime

from mcp import ClientSession
from mcp.client.sse import sse_client

PROXY_URL = "http://localhost:8080/sse"
LOG_FILE = "logs/proxy/calls.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filemode="w",
)
log = logging.getLogger("calls")

CALLS = [
    # ── VALID CALLS ────────────────────────────────────────────────────────────
    ("VALID", "get-current-time",   {}),
    ("VALID", "list-calendars",     {}),
    ("VALID", "list-colors",        {}),
    ("VALID", "get-current-time",   {}),
    ("VALID", "list-calendars",     {}),
    ("VALID", "manage-accounts",    {"action": "list"}),
    ("VALID", "list-events",        {"calendarId": "primary", "maxResults": 5}),
    ("VALID", "list-events",        {"calendarId": "primary", "timeMin": "2026-01-01T00:00:00Z", "timeMax": "2026-12-31T23:59:59Z"}),
    ("VALID", "list-events",        {"calendarId": "primary", "maxResults": 1}),
    ("VALID", "search-events",      {"query": "meeting", "calendarId": "primary"}),
    ("VALID", "search-events",      {"query": "birthday", "calendarId": "primary"}),
    ("VALID", "search-events",      {"query": "lunch",    "calendarId": "primary"}),
    ("VALID", "get-freebusy",       {"timeMin": "2026-04-21T00:00:00Z", "timeMax": "2026-04-28T00:00:00Z", "calendars": [{"id": "primary"}]}),
    ("VALID", "list-events",        {"calendarId": "primary", "maxResults": 10}),
    ("VALID", "list-colors",        {}),
    # ── WRONG TOOL NAME ────────────────────────────────────────────────────────
    ("BAD_TOOL", "non-existent-tool",      {}),
    ("BAD_TOOL", "list_calendars",         {}),
    ("BAD_TOOL", "ListCalendars",          {}),
    ("BAD_TOOL", "get_current_time",       {}),
    ("BAD_TOOL", "LISTEVENTS",             {}),
    ("BAD_TOOL", "calendar-list",          {}),
    ("BAD_TOOL", "events/list",            {}),
    ("BAD_TOOL", "",                       {}),
    ("BAD_TOOL", "delete_all_events",      {}),
    ("BAD_TOOL", "admin-override",         {}),
    # ── MISSING / WRONG PARAMS ─────────────────────────────────────────────────
    ("BAD_PARAMS", "search-events",        {}),
    ("BAD_PARAMS", "get-event",            {}),
    ("BAD_PARAMS", "list-events",          {"maxResults": "not-a-number"}),
    ("BAD_PARAMS", "get-freebusy",         {"timeMin": "invalid-date"}),
    ("BAD_PARAMS", "respond-to-event",     {"calendarId": "primary"}),
    ("BAD_PARAMS", "update-event",         {}),
    ("BAD_PARAMS", "delete-event",         {}),
    ("BAD_PARAMS", "list-events",          {"calendarId": 12345}),
    ("BAD_PARAMS", "get-freebusy",         {"calendars": "primary"}),
    ("BAD_PARAMS", "create-event",         {"calendarId": "primary"}),
    # ── EDGE CASES / ATTACK-LIKE ───────────────────────────────────────────────
    ("EDGE", "search-events",      {"query": "' OR '1'='1", "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "<script>alert(1)</script>", "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "A" * 1000, "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "\x00\x01\x02", "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "שלום עולם", "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "🎉🚀💥", "calendarId": "primary"}),
    ("EDGE", "create-event",       {"calendarId": "primary", "summary": "<img src=x onerror=alert(1)>", "start": {"dateTime": "2026-04-22T10:00:00"}, "end": {"dateTime": "2026-04-22T11:00:00"}}),
    ("EDGE", "list-events",        {"calendarId": "../../etc/passwd", "maxResults": 1}),
    ("EDGE", "search-events",      {"query": "DROP TABLE events;--", "calendarId": "primary"}),
    ("EDGE", "list-events",        {"calendarId": "primary", "timeMin": "9999-12-31T00:00:00Z", "timeMax": "0001-01-01T00:00:00Z"}),
    ("EDGE", "get-freebusy",       {"timeMin": "2026-04-21T00:00:00Z", "timeMax": "2026-04-28T00:00:00Z", "calendars": [{"id": "../../secret"}]}),
    ("EDGE", "search-events",      {"query": "normal search", "calendarId": "primary", "extra_field": "injected"}),
    ("EDGE", "create-event",       {"calendarId": "primary", "summary": "x" * 5000, "start": {"dateTime": "2026-04-22T10:00:00"}, "end": {"dateTime": "2026-04-22T11:00:00"}}),
    ("EDGE", "search-events",      {"query": "${7*7}", "calendarId": "primary"}),
    ("EDGE", "search-events",      {"query": "{{7*7}}", "calendarId": "primary"}),
]

assert len(CALLS) == 50, f"Expected 50 calls, got {len(CALLS)}"


async def make_call(session: ClientSession, category: str, tool: str, args: dict, index: int) -> None:
    start = time.monotonic()
    status = "OK"
    result_preview = ""
    try:
        result = await session.call_tool(tool, args)
        elapsed = time.monotonic() - start
        if result.content:
            raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
            result_preview = raw[:120].replace("\n", " ")
        else:
            result_preview = "(empty response)"
        status = "OK"
    except Exception as exc:
        elapsed = time.monotonic() - start
        result_preview = str(exc)[:120]
        status = "ERROR"

    log.info(
        f"[{index:02d}] [{category:<11}] [{status:<5}] tool={tool!r:40s} "
        f"args_keys={list(args.keys())} elapsed={elapsed:.3f}s | {result_preview}"
    )
    print(f"  [{index:02d}] {category:<11} {status:<5}  {tool}")


async def run_all() -> None:
    log.info("=" * 100)
    log.info(f"SESSION START — {datetime.now().isoformat()} — {len(CALLS)} calls against {PROXY_URL}")
    log.info("=" * 100)

    print(f"\nRunning {len(CALLS)} calls against {PROXY_URL}\n")
    print(f"  {'#':<4} {'CATEGORY':<11} {'STATUS':<6} TOOL")
    print("  " + "-" * 60)

    async with sse_client(PROXY_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for i, (category, tool, args) in enumerate(CALLS, 1):
                await make_call(session, category, tool, args, i)
                await asyncio.sleep(0.3)

    log.info("=" * 100)
    log.info("SESSION END")
    log.info("=" * 100)
    print(f"\nDone. Full log at: logs/proxy/calls.log")


if __name__ == "__main__":
    asyncio.run(run_all())
