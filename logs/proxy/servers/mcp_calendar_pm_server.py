"""Project-manager calendar MCP server — FastMCP over Streamable HTTP.

Pre-loaded with a realistic sprint week (2026-05-04 to 2026-05-09).
Tools beyond the basic calendar:
  list_events      — events on a specific date
  list_week        — all events for a Mon–Sun week
  create_event     — create event with optional duration + attendees
  update_event     — change title, date, or time of an existing event
  delete_event     — remove an event by ID
  find_free_slot   — find the first gap of N minutes on a given day
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calendar-pm", port=8098)

EVENTS: dict[str, dict] = {
    "evt_001": {"title": "Sprint 15 Kickoff",        "date": "2026-05-04", "time": "09:00", "duration_min": 60,  "attendees": ["alice", "bob", "carol", "dave"]},
    "evt_002": {"title": "1:1 with Alice",            "date": "2026-05-04", "time": "14:00", "duration_min": 30,  "attendees": ["alice"]},
    "evt_003": {"title": "Daily standup",             "date": "2026-05-05", "time": "09:00", "duration_min": 15,  "attendees": ["alice", "bob", "carol"]},
    "evt_004": {"title": "Product sync",              "date": "2026-05-05", "time": "15:00", "duration_min": 45,  "attendees": ["product", "alice"]},
    "evt_005": {"title": "Daily standup",             "date": "2026-05-06", "time": "09:00", "duration_min": 15,  "attendees": ["alice", "bob", "carol"]},
    "evt_006": {"title": "1:1 with Bob",              "date": "2026-05-06", "time": "11:00", "duration_min": 30,  "attendees": ["bob"]},
    "evt_007": {"title": "Daily standup",             "date": "2026-05-07", "time": "09:00", "duration_min": 15,  "attendees": ["alice", "bob", "carol"]},
    "evt_008": {"title": "Lenovo stakeholder demo",   "date": "2026-05-07", "time": "14:00", "duration_min": 60,  "attendees": ["lenovo", "alice", "bob"]},
    "evt_009": {"title": "Sprint 15 Review",          "date": "2026-05-08", "time": "13:00", "duration_min": 60,  "attendees": ["alice", "bob", "carol", "product"]},
    "evt_010": {"title": "Sprint 15 Retrospective",   "date": "2026-05-08", "time": "15:00", "duration_min": 60,  "attendees": ["alice", "bob", "carol"]},
}


@mcp.tool()
def list_events(date: str) -> list[dict]:
    """List all events on a given date (YYYY-MM-DD)."""
    return [{"id": k, **v} for k, v in EVENTS.items() if v["date"] == date]


@mcp.tool()
def list_week(start_date: str) -> list[dict]:
    """List all events for the 7-day week starting on start_date (YYYY-MM-DD)."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return [{"error": f"Invalid date: {start_date}"}]
    dates = {str(start + timedelta(days=i)) for i in range(7)}
    events = [{"id": k, **v} for k, v in EVENTS.items() if v["date"] in dates]
    return sorted(events, key=lambda e: (e["date"], e["time"]))


@mcp.tool()
def create_event(title: str, date: str, time: str, duration_min: int = 60, attendees: list[str] | None = None) -> dict:
    """Create a new event. duration_min defaults to 60. attendees is an optional list of names."""
    event_id = f"evt_{uuid.uuid4().hex[:6]}"
    EVENTS[event_id] = {
        "title": title,
        "date": date,
        "time": time,
        "duration_min": duration_min,
        "attendees": attendees or [],
    }
    return {"id": event_id, **EVENTS[event_id], "status": "created"}


@mcp.tool()
def update_event(event_id: str, title: str | None = None, date: str | None = None, time: str | None = None, duration_min: int | None = None) -> dict:
    """Update an existing event's title, date, time, or duration. Pass only the fields to change."""
    if event_id not in EVENTS:
        return {"error": f"Event {event_id} not found"}
    if title is not None:
        EVENTS[event_id]["title"] = title
    if date is not None:
        EVENTS[event_id]["date"] = date
    if time is not None:
        EVENTS[event_id]["time"] = time
    if duration_min is not None:
        EVENTS[event_id]["duration_min"] = duration_min
    return {"id": event_id, **EVENTS[event_id], "status": "updated"}


@mcp.tool()
def delete_event(event_id: str) -> dict:
    """Delete an event by ID."""
    if event_id not in EVENTS:
        return {"error": f"Event {event_id} not found", "status": "not_found"}
    del EVENTS[event_id]
    return {"id": event_id, "status": "deleted"}


@mcp.tool()
def find_free_slot(date: str, duration_min: int) -> dict:
    """Find the first free time slot of at least duration_min minutes on a given date (09:00–18:00)."""
    day_events = sorted(
        [e for e in EVENTS.values() if e["date"] == date],
        key=lambda e: e["time"],
    )
    start_hour, end_hour = 9 * 60, 18 * 60
    cursor = start_hour
    for ev in day_events:
        h, m = map(int, ev["time"].split(":"))
        ev_start = h * 60 + m
        ev_end = ev_start + ev.get("duration_min", 60)
        if cursor + duration_min <= ev_start:
            break
        cursor = max(cursor, ev_end)
    if cursor + duration_min <= end_hour:
        return {"date": date, "time": f"{cursor // 60:02d}:{cursor % 60:02d}", "duration_min": duration_min}
    return {"error": f"No free slot of {duration_min} min found on {date} between 09:00 and 18:00"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
