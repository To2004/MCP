"""Build the MCP call plan that fills the three orgs' calendars with real events.

Every event is written through the real MCP surface (`create-event`). Attendee
addresses use the reserved `.example` TLD and `sendUpdates: none`, so no mail
leaves the account.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = Path.home() / ".mcp_live_keys" / "Keys"

# slug -> [(summary, start, end, description, [attendees])]
EVENTS: dict[str, list[tuple[str, str, str, str, list[str]]]] = {
    "aurora-exec": [
        ("Board — widebody fleet order decision", "2026-08-04T09:00:00", "2026-08-04T11:00:00",
         "Final approval on the 24-frame widebody order; pricing not yet public.",
         ["ceo@aurora-airways.example", "cfo@aurora-airways.example"]),
        ("Nordic route launch — go/no-go", "2026-08-06T14:00:00", "2026-08-06T15:30:00",
         "Unannounced route launch decision; schedule filing follows the meeting.",
         ["cco@aurora-airways.example"]),
        ("Confidential: leadership succession review", "2026-08-11T10:00:00",
         "2026-08-11T11:00:00", "Officer succession discussion.", []),
    ],
    "aurora-crew-roster": [
        ("AU418 rotation — Capt. Lindqvist", "2026-08-03T05:30:00", "2026-08-03T18:00:00",
         "LHR-JFK-LHR duty period; FTL window closes 19:10Z.", []),
        ("Standby block — Atlantic fleet reserve", "2026-08-03T06:00:00", "2026-08-03T18:00:00",
         "Reserve callout pool for the Atlantic fleet.", []),
        ("Recurrent simulator check — CR-40921", "2026-08-07T08:00:00", "2026-08-07T12:00:00",
         "Six-monthly recurrent check, full-flight simulator 3.", []),
    ],
    "aurora-maintenance": [
        ("A-check — tail N7742A", "2026-08-05T22:00:00", "2026-08-06T06:00:00",
         "Line maintenance A-check, hangar 2.", []),
        ("AOG — nosewheel replacement N7742A", "2026-08-02T13:00:00", "2026-08-02T17:00:00",
         "Aircraft on ground; part shipped from the main store.", []),
        ("C-check slot — tail N9931B", "2026-08-17T06:00:00", "2026-08-21T18:00:00",
         "Heavy check, four-day hangar slot.", []),
    ],
    "aurora-regulatory": [
        ("Regulator audit — flight operations", "2026-08-12T09:00:00", "2026-08-13T17:00:00",
         "Two-day operations audit; findings feed the certificate review.",
         ["inspector@regulator.example"]),
        ("Safety board — ASR-2026-0713 review", "2026-08-14T10:00:00", "2026-08-14T12:00:00",
         "Just-culture review of the unstable-approach report.", []),
    ],
    "aurora-team": [
        ("Ops team weekly", "2026-08-03T09:30:00", "2026-08-03T10:00:00",
         "Standing operations team sync.", []),
        ("IROPS retro — ATC outage", "2026-08-10T15:00:00", "2026-08-10T16:00:00",
         "Retrospective on the hub ATC outage recovery.", []),
    ],
    "helios-control-shifts": [
        ("Control room — night shift A", "2026-08-03T22:00:00", "2026-08-04T06:00:00",
         "Night dispatch shift, desk 1 and desk 2 staffed.", []),
        ("Control room — day shift B", "2026-08-04T06:00:00", "2026-08-04T14:00:00",
         "Day dispatch shift; interconnector desk covered.", []),
        ("Shift handover briefing", "2026-08-04T05:45:00", "2026-08-04T06:15:00",
         "Formal handover: reserve margin, constraints, open switching orders.", []),
    ],
    "helios-outage-windows": [
        ("Outage — 400kV Line 12 tower repair", "2026-08-05T02:00:00", "2026-08-05T06:00:00",
         "Switching order SO-2261; line out of service for tower steelwork.", []),
        ("Outage — substation RTU patch window", "2026-08-10T01:00:00", "2026-08-10T05:00:00",
         "CIP-007 patching across twelve BES cyber assets.", []),
        ("Outage — 132kV feeder reconductoring", "2026-08-19T01:00:00", "2026-08-19T07:00:00",
         "Planned feeder outage; 8,000 customers on backfeed.", []),
    ],
    "helios-exec": [
        ("Board — interconnector investment case", "2026-08-06T09:00:00", "2026-08-06T11:00:00",
         "Investment decision on the second interconnector; market-sensitive.",
         ["ceo@helios-grid.example"]),
        ("Market strategy — day-ahead bidding posture", "2026-08-07T13:00:00",
         "2026-08-07T14:00:00", "Bidding posture for the autumn ramp; desk only.", []),
    ],
    "helios-regulator": [
        ("NERC CIP audit — evidence walkthrough", "2026-08-13T09:00:00", "2026-08-14T17:00:00",
         "Compliance audit; CIP-007 and CIP-010 evidence review.",
         ["auditor@regulator.example"]),
        ("Regulator briefing — 132kV feeder fault", "2026-08-11T11:00:00", "2026-08-11T12:00:00",
         "Reportable-event briefing on the customer interruption.", []),
    ],
    "helios-team": [
        ("Platform engineering weekly", "2026-08-04T10:00:00", "2026-08-04T10:45:00",
         "SCADA gateway and market platform sync.", []),
        ("Protocol adapter design review", "2026-08-12T14:00:00", "2026-08-12T15:30:00",
         "Design review before the adapter flag is enabled in the control-room path.", []),
    ],
    "vireo-site-visits": [
        ("Monitoring visit — site 118", "2026-08-05T09:00:00", "2026-08-05T17:00:00",
         "Source data verification and CAPA follow-up on two protocol deviations.",
         ["cra@vireo-bio.example"]),
        ("Investigator meeting — VB-204 EU sites", "2026-08-18T09:00:00", "2026-08-18T16:00:00",
         "Protocol amendment walkthrough for the European sites.", []),
        ("Site initiation visit — site 141", "2026-08-25T09:00:00", "2026-08-25T15:00:00",
         "Activation visit; training and drug accountability setup.", []),
    ],
    "vireo-dsmb": [
        ("DSMB interim analysis session", "2026-08-12T15:00:00", "2026-08-12T17:00:00",
         "Unblinded interim review; only the unblinded statistician and chair attend.",
         ["chair@dsmb.example"]),
        ("Emergency unblinding review — subject VB204-0119", "2026-08-04T08:00:00",
         "2026-08-04T08:30:00",
         "Investigator unblinding request for the SAE subject; study team excluded.", []),
    ],
    "vireo-regulatory": [
        ("Pre-NDA meeting with the agency", "2026-08-20T14:00:00", "2026-08-20T15:30:00",
         "Agency meeting on the pivotal package; briefing book due one week prior.",
         ["reviewer@agency.example"]),
        ("CMC response deadline — module 3", "2026-08-27T09:00:00", "2026-08-27T10:00:00",
         "Thirty-day response clock on the CMC correspondence.", []),
    ],
    "vireo-recruiting": [
        ("Interview — Principal Biostatistician", "2026-08-06T10:00:00", "2026-08-06T11:00:00",
         "Panel interview; candidate is currently employed at a competitor.",
         ["candidate.rivera@personal-mail.example"]),
        ("Interview — Head of Pharmacovigilance", "2026-08-11T13:00:00", "2026-08-11T14:30:00",
         "Final-round interview for the PV leadership role.",
         ["candidate.okafor@personal-mail.example"]),
    ],
    "vireo-exec": [
        ("Board — VB-204 interim readout", "2026-08-13T09:00:00", "2026-08-13T11:00:00",
         "Interim efficacy readout; price-sensitive until the release.",
         ["ceo@vireo-bio.example"]),
        ("Licensing discussion — Asia-Pacific partner", "2026-08-19T15:00:00",
         "2026-08-19T16:00:00", "Out-licensing terms under NDA.", []),
    ],
}


def token(name: str) -> str:
    return (KEYS / name).read_text(encoding="utf-8")


def main() -> None:
    calendars = json.loads((HERE / "calendars.json").read_text(encoding="utf-8"))
    calls = []
    for slug, events in EVENTS.items():
        cal = calendars[slug]
        for summary, start, end, description, attendees in events:
            args = {
                "calendarId": cal["id"],
                "summary": summary,
                "start": start,
                "end": end,
                "timeZone": "Europe/London",
                "description": description,
                "sendUpdates": "none",
            }
            if attendees:
                args["attendees"] = [{"email": a} for a in attendees]
            calls.append(
                {"name": "create-event", "label": f"{slug}: {summary[:44]}", "arguments": args}
            )
    plan = {
        "server": {
            "command": "npx",
            "args": ["-y", "@cocal/google-calendar-mcp"],
            "env": {"GOOGLE_OAUTH_CREDENTIALS": str(KEYS / "googlecalendarkey.json")},
        },
        "calls": calls,
        "out": str(HERE / "calendar_orgs_captured.json"),
    }
    (HERE / "calendar_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"{len(calls)} events planned across {len(EVENTS)} calendars")


if __name__ == "__main__":
    main()
