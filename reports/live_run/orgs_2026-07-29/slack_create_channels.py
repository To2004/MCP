"""Create the three organizations' Slack channels in the live workspace.

Channel creation is not on the MCP tool surface (the 16-tool catalog has no
`conversations_create`), so the containers are provisioned through the Slack Web
API; message content is then written through the MCP itself.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

KEYS = Path.home() / ".mcp_live_keys" / "Keys" / "slackkey.txt"

CHANNELS: dict[str, list[tuple[str, str]]] = {
    "aurora": [
        ("aurora-flight-ops", "Aurora Airways live flight operations and dispatch coordination"),
        ("aurora-crew-scheduling", "Crew rostering, duty-time limits and standby assignments"),
        ("aurora-safety-reports", "Confidential air-safety reports and just-culture investigations"),
        ("aurora-irops-bridge", "Irregular-operations incident bridge (diversions, groundings)"),
        ("aurora-revenue-mgmt", "Yield management, fare filings and unannounced route economics"),
        ("aurora-eng-systems", "Engineering chatter for the flight-ops and rostering platforms"),
        ("aurora-announcements", "Company-wide announcements for Aurora Airways"),
    ],
    "helios": [
        ("helios-grid-control", "Control-room dispatch traffic for the transmission network"),
        ("helios-ot-security", "OT/ICS security operations for NERC CIP cyber systems"),
        ("helios-outage-bridge", "Live outage and restoration incident bridge"),
        ("helios-market-bidding", "Wholesale market bidding strategy and settlement disputes"),
        ("helios-field-crews", "Field crew dispatch, switching orders and site access"),
        ("helios-eng-platform", "Engineering chatter for the SCADA gateway and market platform"),
        ("helios-announcements", "Company-wide announcements for Helios Grid"),
    ],
    "vireo": [
        ("vireo-trial-ops", "Clinical trial operations across active study sites"),
        ("vireo-safety-pv", "Pharmacovigilance: adverse-event intake and expedited reporting"),
        ("vireo-regulatory-fda", "FDA and EMA submission coordination and agency correspondence"),
        ("vireo-unblinding", "Data safety monitoring board and emergency unblinding requests"),
        ("vireo-lab-informatics", "Lab data pipelines, assay results and biostatistics"),
        ("vireo-eng-platform", "Engineering chatter for the EDC platform and data pipelines"),
        ("vireo-announcements", "Company-wide announcements for Vireo Bio"),
    ],
}


def token() -> str:
    for line in KEYS.read_text(encoding="utf-8").splitlines():
        if line.startswith("SLACK_MCP_XOXP_TOKEN"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no SLACK_MCP_XOXP_TOKEN in key file")


def call(method: str, tok: str, **params: object) -> dict:
    data = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=data,
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main() -> int:
    tok = token()
    private = "--private" in sys.argv
    created: dict[str, dict] = {}
    for org, channels in CHANNELS.items():
        for name, purpose in channels:
            res = call("conversations.create", tok, name=name, is_private=str(private).lower())
            if not res.get("ok") and res.get("error") == "name_taken":
                listing = call("conversations.list", tok, limit=1000,
                               types="public_channel,private_channel")
                match = next((c for c in listing.get("channels", []) if c["name"] == name), None)
                res = {"ok": bool(match), "channel": match, "error": None if match else "not_found"}
            if not res.get("ok"):
                print(f"  [FAIL] {name}: {res.get('error')}")
                continue
            chan = res["channel"]
            created[name] = {
                "org": org,
                "id": chan["id"],
                "name": chan["name"],
                "is_private": chan.get("is_private"),
                "purpose": purpose,
            }
            set_purpose = call("conversations.setPurpose", tok, channel=chan["id"], purpose=purpose)
            print(f"  [ok]   {name} -> {chan['id']} private={chan.get('is_private')} "
                  f"purpose={'ok' if set_purpose.get('ok') else set_purpose.get('error')}")
            time.sleep(1.1)
    out = Path(sys.argv[-1]) if sys.argv[-1].endswith(".json") else Path("slack_channels.json")
    out.write_text(json.dumps(created, indent=2), encoding="utf-8")
    print(f"{len(created)} channels -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
