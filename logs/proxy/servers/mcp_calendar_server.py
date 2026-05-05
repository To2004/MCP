"""
Mock Google Calendar MCP server — runs natively over Streamable HTTP.
Represents a web-style MCP service (no mcp-proxy needed).
"""
from __future__ import annotations

import uuid

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("google-calendar-mock", port=8093)

EVENTS: dict[str, dict] = {
    "evt_001": {"title": "Team standup",     "date": "2026-05-05", "time": "09:00"},
    "evt_002": {"title": "Thesis review",    "date": "2026-05-05", "time": "14:00"},
    "evt_003": {"title": "Lunch w/ advisor", "date": "2026-05-06", "time": "12:30"},
}


@mcp.tool()
def list_events(date: str) -> list[dict]:
    """List all calendar events for a given date (YYYY-MM-DD)."""
    return [{"id": k, **v} for k, v in EVENTS.items() if v["date"] == date]


@mcp.tool()
def create_event(title: str, date: str, time: str) -> dict:
    """Create a new calendar event. Returns the new event with its ID."""
    event_id = f"evt_{uuid.uuid4().hex[:6]}"
    EVENTS[event_id] = {"title": title, "date": date, "time": time}
    return {"id": event_id, "title": title, "date": date, "time": time, "status": "created"}


@mcp.tool()
def delete_event(event_id: str) -> dict:
    """Delete a calendar event by ID."""
    if event_id not in EVENTS:
        return {"error": f"Event {event_id} not found", "status": "not_found"}
    del EVENTS[event_id]
    return {"id": event_id, "status": "deleted"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
