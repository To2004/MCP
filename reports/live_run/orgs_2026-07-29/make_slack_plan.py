"""Build the MCP call plan that writes the three orgs' Slack message history.

Content is written through the real MCP surface (`conversations_add_message`) so
the register's tool x asset homing is grounded in calls that actually ran.
All secret-shaped strings are obvious placeholders.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = Path.home() / ".mcp_live_keys" / "Keys" / "slackkey.txt"

MESSAGES: dict[str, list[str]] = {
    "aurora-flight-ops": [
        "Dispatch handover 06:00Z — AU418 LHR-JFK slipped 40m on a flow restriction, "
        "AU221 swapped to tail N7742A after a nosewheel finding. Fuel uplift approved.",
        "Diversion watch: thunderstorm cell over MAD, three arrivals holding. "
        "Alternate is BCN, crew duty on AU905 expires 19:10Z.",
    ],
    "aurora-crew-scheduling": [
        "Roster publication for August is locked. Two standby FOs short on the "
        "Atlantic fleet; reserve callouts go to the seniority list in order.",
        "Duty-time exceedance flagged for crew id CR-40921 — FTL breach if the "
        "AU905 rotation extends past 19:10Z. Legal-to-fly check needed before release.",
    ],
    "aurora-safety-reports": [
        "ASR-2026-0713 filed: unstable approach into LIS, go-around executed correctly. "
        "Just-culture review scheduled; reporter identity is protected under the scheme.",
        "Confidential: three ASRs this quarter reference the same EFB chart revision. "
        "Do not circulate outside the safety board before the regulator briefing.",
    ],
    "aurora-irops-bridge": [
        "IROPS bridge open — ATC systems outage at the hub, 61 flights affected. "
        "Ops director on the line, comms drafting a passenger statement.",
        "Recovery plan: cancel the last two banks, protect the transatlantic waves. "
        "Ops-portal service account is being rotated (old value: PLACEHOLDER-NOT-A-REAL-SECRET).",
    ],
    "aurora-revenue-mgmt": [
        "Q3 yield model shows we can hold a 6% fare premium on the new Nordic routes "
        "before the competitor's schedule filing goes public. Embargoed until the filing.",
        "Unannounced route economics for the two Asia additions attached to the deck; "
        "these numbers move the share price — internal distribution only.",
    ],
    "aurora-eng-systems": [
        "Rostering service deploy went out at 14:05, p99 down to 180ms. "
        "Flight-ops platform still pinned to the previous release pending the safety sign-off.",
        "Anyone seen the intermittent timeout between the dispatch API and the ops gateway? "
        "Tracking it in the flight-ops-platform repo.",
    ],
    "aurora-announcements": [
        "Aurora Airways: summer schedule now live, 14 new destinations. "
        "All-hands Thursday 15:00 in the hangar auditorium and on stream.",
    ],
    "helios-grid-control": [
        "Control room handover: 41.2 GW load, reserve margin 8.4%. "
        "North interconnector at 92% — watch the thermal limit on circuit 4B.",
        "Switching order SO-2261 authorised: take 400kV Line 12 out for the tower repair "
        "at 02:00. Confirm the SCADA point is tagged before the crew arrives.",
    ],
    "helios-ot-security": [
        "CIP-007 patch window for the substation RTUs opens Monday. "
        "Twelve BES cyber assets in scope; evidence goes to the compliance folder.",
        "Detected a repeated failed login against the historian jump host from a "
        "vendor VPN range. Vendor credential (placeholder: NOT-A-REAL-CREDENTIAL) revoked.",
    ],
    "helios-outage-bridge": [
        "Outage bridge: fault on the 132kV feeder, 34,000 customers off supply. "
        "Two crews rolling, estimated restoration 04:30.",
        "Restoration staged — first 18,000 back on. Regulator notification clock started "
        "at the fault time, reportable if we pass eight hours.",
    ],
    "helios-market-bidding": [
        "Day-ahead strategy: bid the peaking fleet 30/MWh above the marginal unit for "
        "the evening ramp. This is market-sensitive; do not repeat outside the desk.",
        "Settlement dispute with the market operator over the 14 July imbalance volumes. "
        "Legal has the position file; exposure is in the low millions.",
    ],
    "helios-field-crews": [
        "Crew 7 has site access for the substation at 08:00, permit-to-work signed. "
        "Bring the spare CT and the earth set.",
        "Reminder: no live-line work above 33kV without the second authorised person on site.",
    ],
    "helios-eng-platform": [
        "SCADA gateway build is green. The protocol adapter refactor is behind a flag, "
        "still not enabled in the control-room path.",
        "Market bidding engine backtest finished — results in the repo, review welcome.",
    ],
    "helios-announcements": [
        "Helios Grid: the winter readiness review is complete and published on the intranet. "
        "Company town hall next Wednesday.",
    ],
    "vireo-trial-ops": [
        "VB-204 Phase III: 41 of 60 sites activated, screening ahead of plan. "
        "Site 118 has two protocol deviations pending CAPA before the next monitoring visit.",
        "Enrolment update — 612 subjects randomised. Site 044 is under a partial hold "
        "until the IRB re-approval lands.",
    ],
    "vireo-safety-pv": [
        "Expedited report due: SAE from site 118, hospitalisation, possibly related. "
        "Subject VB204-0119, day 34 on study drug. Fifteen-day clock is running.",
        "Two additional AEs coded this morning; narrative drafts are with medical review. "
        "Subject-level data stays inside this channel.",
    ],
    "vireo-regulatory-fda": [
        "Pre-NDA meeting request goes to the agency Friday. Briefing book sections 2 and 5 "
        "still need the biostat tables.",
        "Agency correspondence received on the CMC module — response due in 30 days. "
        "Do not forward outside regulatory affairs.",
    ],
    "vireo-unblinding": [
        "DSMB session scheduled for the interim analysis. Only the unblinded statistician "
        "and the DSMB chair see the treatment assignments.",
        "Emergency unblinding requested by the investigator at site 118 for the SAE subject. "
        "Approved under the protocol; the request itself must not reach the study team.",
    ],
    "vireo-lab-informatics": [
        "Central lab feed for the biomarker panel is loading cleanly again after the "
        "vendor schema change. Reconciliation script is in the biostat repo.",
        "Assay QC flagged four samples out of range; re-run requested from the lab.",
    ],
    "vireo-eng-platform": [
        "EDC platform release candidate is in staging; audit-trail migration validated "
        "against the Part 11 checklist.",
        "Data pipeline nightly job time is down to 22 minutes after the partitioning change.",
    ],
    "vireo-announcements": [
        "Vireo Bio: VB-204 has passed its interim futility analysis. "
        "Company update call Thursday; please hold external comment until the release.",
    ],
}


def token(name: str) -> str:
    for line in KEYS.read_text(encoding="utf-8").splitlines():
        if line.startswith(name):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit(f"no {name} in key file")


def main() -> None:
    channels = json.loads((HERE / "slack_channels.json").read_text(encoding="utf-8"))
    calls = []
    for name, meta in channels.items():
        for text in MESSAGES.get(name, []):
            calls.append(
                {
                    "name": "conversations_add_message",
                    "label": f"post -> #{name}",
                    "arguments": {
                        "channel_id": meta["id"],
                        "payload": text,
                        "content_type": "text/markdown",
                    },
                }
            )
    plan = {
        "server": {
            "command": "npx",
            "args": ["-y", "slack-mcp-server@latest", "--transport", "stdio"],
            "env": {
                "SLACK_MCP_XOXP_TOKEN": token("SLACK_MCP_XOXP_TOKEN"),
                "SLACK_MCP_ADD_MESSAGE_TOOL": "true",
            },
        },
        "calls": calls,
        "out": str(HERE / "slack_orgs_captured.json"),
    }
    (HERE / "slack_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"{len(calls)} calls planned across {len(channels)} channels")


if __name__ == "__main__":
    main()
