"""Create the three organizations' secondary calendars in the live Google account.

Calendar creation is not on the MCP tool surface (the 13-tool catalog reads the
calendar list but cannot create a calendar), so the containers are provisioned
through the Calendar API; the events inside them are then written through the
MCP itself.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

KEYS = Path.home() / ".mcp_live_keys" / "Keys"
HERE = Path(__file__).resolve().parent

CALENDARS: dict[str, list[tuple[str, str, str]]] = {
    "aurora": [
        ("aurora-exec", "Aurora Airways — Executive",
         "Officer schedule: board, fleet-order and route-launch meetings"),
        ("aurora-crew-roster", "Aurora Airways — Crew Roster",
         "Crew duty periods, standby blocks and rotation start/end"),
        ("aurora-maintenance", "Aurora Airways — Maintenance Slots",
         "Hangar checks and aircraft-on-ground windows per tail"),
        ("aurora-regulatory", "Aurora Airways — Regulatory Audits",
         "Regulator audits, safety-board reviews and certification inspections"),
        ("aurora-team", "Aurora Airways — Ops Team",
         "Ordinary operations-team scheduling"),
    ],
    "helios": [
        ("helios-control-shifts", "Helios Grid — Control Room Shifts",
         "Control-room operator shift pattern and handover slots"),
        ("helios-outage-windows", "Helios Grid — Outage Windows",
         "Planned transmission outages and switching windows on named circuits"),
        ("helios-exec", "Helios Grid — Executive",
         "Officer schedule: board, market-strategy and interconnector meetings"),
        ("helios-regulator", "Helios Grid — Regulator & Compliance",
         "NERC CIP audits, regulator meetings and evidence reviews"),
        ("helios-team", "Helios Grid — Engineering Team",
         "Ordinary engineering-team scheduling"),
    ],
    "vireo": [
        ("vireo-site-visits", "Vireo Bio — Trial Site Visits",
         "Monitoring visits and investigator meetings per study site"),
        ("vireo-dsmb", "Vireo Bio — DSMB & Unblinding",
         "Data safety monitoring board sessions and unblinding reviews"),
        ("vireo-regulatory", "Vireo Bio — Regulatory Submissions",
         "Agency meetings, submission deadlines and inspection windows"),
        ("vireo-recruiting", "Vireo Bio — Recruiting",
         "Candidate interview scheduling for clinical and research roles"),
        ("vireo-exec", "Vireo Bio — Executive",
         "Officer schedule: board, licensing and readout meetings"),
    ],
}


def access_token() -> str:
    cred = json.loads((KEYS / "googlecalendarkey.json").read_text())["installed"]
    tok = json.loads((KEYS / "googlecalendartoken.json").read_text())["normal"]
    data = urllib.parse.urlencode(
        {
            "client_id": cred["client_id"],
            "client_secret": cred["client_secret"],
            "refresh_token": tok["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", data) as resp:
        return json.load(resp)["access_token"]


def api(token: str, method: str, url: str, body: dict | None = None) -> dict:
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp) if resp.status != 204 else {}


def main() -> int:
    token = access_token()
    existing = {
        c.get("summary"): c["id"]
        for c in api(token, "GET", "https://www.googleapis.com/calendar/v3/users/me/calendarList")
        .get("items", [])
    }
    created: dict[str, dict] = {}
    for org, calendars in CALENDARS.items():
        for slug, summary, description in calendars:
            if summary in existing:
                cal_id = existing[summary]
                print(f"  [reuse] {summary} -> {cal_id}")
            else:
                res = api(
                    token,
                    "POST",
                    "https://www.googleapis.com/calendar/v3/calendars",
                    {"summary": summary, "description": description, "timeZone": "Europe/London"},
                )
                cal_id = res["id"]
                print(f"  [ok]    {summary} -> {cal_id}")
            created[slug] = {"org": org, "id": cal_id, "summary": summary,
                             "description": description}
    (HERE / "calendars.json").write_text(json.dumps(created, indent=2), encoding="utf-8")
    print(f"{len(created)} calendars -> calendars.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
