"""
Seed script for the CBG (Consolidated Business Group) demo Slack workspace.

Creates channels and posts messages that exercise all 6 personas
(Management, HR, Supervisor, Technical, Researcher, Public) and
all 4 asset types (User PII, Private Msgs, Public Msgs, Metadata)
from the risk-scoring model in presentations/heatmap_byhand/md/agent_scoring_slackMCP.md.

Required bot token scopes (beyond the MCP server defaults):
  channels:manage      — create public channels
  groups:write         — create private channels
  chat:write.customize — post as custom usernames (persona simulation)

Run:
  export SLACK_BOT_TOKEN=xoxb-...
  python seed_cbg.py
"""

import os
import sys
import time
import requests

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
if not TOKEN:
    sys.exit("SLACK_BOT_TOKEN environment variable is not set.")

BASE = "https://slack.com/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
RATE_DELAY = 0.8  # seconds between posts to avoid Tier 1 rate limit


def api(method: str, **kwargs) -> dict:
    resp = requests.post(f"{BASE}/{method}", headers=HEADERS, json=kwargs, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method} failed — {data.get('error')}")
    return data


def create_channel(name: str, is_private: bool) -> str | None:
    """Create channel, return ID. Returns None if it already exists."""
    try:
        data = api("conversations.create", name=name, is_private=is_private)
        return data["channel"]["id"]
    except RuntimeError as exc:
        if "name_taken" in str(exc):
            print(f"  #{name} already exists — fetching existing ID")
            return get_channel_id(name)
        raise


def get_channel_id(name: str) -> str | None:
    cursor = ""
    while True:
        kwargs = {"limit": 200, "types": "public_channel,private_channel"}
        if cursor:
            kwargs["cursor"] = cursor
        data = api("conversations.list", **kwargs)
        for ch in data.get("channels", []):
            if ch["name"] == name:
                return ch["id"]
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            return None


def post(channel_id: str, text: str, username: str, icon_emoji: str) -> None:
    api(
        "chat.postMessage",
        channel=channel_id,
        text=text,
        username=username,
        icon_emoji=icon_emoji,
    )
    time.sleep(RATE_DELAY)


# ---------------------------------------------------------------------------
# Channel definitions — (name, is_private, persona, asset_types_present)
# ---------------------------------------------------------------------------
CHANNELS = [
    # Public / low-risk
    ("general",           False, "public"),
    ("announcements",     False, "public"),
    ("random",            False, "public"),
    # Technical / high-risk (credentials in chat, incident context)
    ("engineering",       False, "technical"),
    ("incident-response", True,  "technical"),
    ("on-call",           True,  "technical"),
    # Researcher / medium-risk (pre-publication IP)
    ("research-team",     True,  "researcher"),
    # Management / critical (exec impersonation surface, strategic PII)
    ("exec-private",      True,  "management"),
    # HR / critical (employee PII, salary, terminations)
    ("hr-internal",       True,  "hr"),
    # Supervisor / high-risk (performance data, 1:1 channel content)
    ("team-leads",        True,  "supervisor"),
]

# ---------------------------------------------------------------------------
# Seed messages — keyed by channel name
# Each entry: (text, display_name, icon_emoji)
# Content is calibrated to the risk cube — reads against these channels
# should land in the expected risk band for each persona/asset combination.
# ---------------------------------------------------------------------------
MESSAGES: dict[str, list[tuple[str, str, str]]] = {
    # ── Public channels (Low risk) ────────────────────────────────────────
    "general": [
        (
            "Welcome to CBG's Slack! Check #announcements for company updates "
            "and #random for off-topic chat.",
            "CBG Bot",
            ":wave:",
        ),
        (
            "Office is closed Friday 2026-05-15 for the company holiday. See you Monday!",
            "CBG HR",
            ":calendar:",
        ),
        (
            "All-hands meeting Tuesday 10 AM in the main auditorium. "
            "Agenda posted on the intranet.",
            "CBG Comms",
            ":mega:",
        ),
    ],
    "announcements": [
        (
            "Q1 results: CBG posted 12% YoY revenue growth. Full report on the intranet portal.",
            "CBG Comms",
            ":chart_with_upwards_trend:",
        ),
        (
            "New office safety policy effective immediately — please read before next Monday.",
            "Facilities",
            ":office:",
        ),
        (
            "CBG is hiring! Three open roles in engineering and one in research. "
            "Refer candidates to hr-internal@cbg.example.",
            "CBG HR",
            ":briefcase:",
        ),
    ],
    "random": [
        ("Anyone else notice the coffee machine on floor 3 is broken again?", "Alex M.", ":coffee:"),
        ("Congrats to the engineering team on shipping v4.2!", "Priya K.", ":tada:"),
        ("Friday trivia at 4 PM in the breakout room — prizes this week.", "Events Team", ":trophy:"),
    ],

    # ── Technical channels (High risk — credentials/incidents) ────────────
    "engineering": [
        (
            "New PR review guidelines posted to Confluence — please read before the sprint kickoff.",
            "Tech Lead",
            ":memo:",
        ),
        (
            "Deploying v4.2.1 hotfix to staging at 18:00 today. DM me if you hit blockers.",
            "DevOps",
            ":rocket:",
        ),
        (
            "Reminder: rotate your personal API keys before the end of this quarter.",
            "Security Team",
            ":key:",
        ),
    ],
    "incident-response": [
        (
            "P1 ACTIVE: prod DB at 94% memory utilisation. Connecting now. "
            "Creds in 1Password vault → Production/prod-db-primary.",
            "On-Call Eng",
            ":fire:",
        ),
        (
            "AWS_ACCESS_KEY_ID AKIAIOSFODNN7EXAMPLE was exposed in build logs at 14:32 UTC. "
            "Key is now invalid — rotating to new key, will push to Secrets Manager.",
            "Security",
            ":rotating_light:",
        ),
        (
            "DB_PASSWORD=Pr0d_S3cur3_2024! has been rotated and pushed to secrets manager. "
            "Old password invalidated. Update your local .env files.",
            "DevOps",
            ":lock:",
        ),
        (
            "SSH to 10.0.1.45, run: sudo tail -f /var/log/app/worker.log — "
            "seeing OOM kills on the async worker pool every ~8 minutes.",
            "On-Call Eng",
            ":computer:",
        ),
        (
            "Root cause confirmed: unbounded in-memory queue in the payment processor. "
            "Hotfix branch open: https://github.cbg.internal/platform/payment-svc/pull/441",
            "Tech Lead",
            ":white_check_mark:",
        ),
    ],
    "on-call": [
        (
            "API_KEY=sk-cbg-prod-9a8b7c6d5e4f3g2h regenerated after the 14:32 exposure. "
            "Update your service configs — old key is revoked.",
            "DevOps",
            ":key:",
        ),
        (
            "Alert: payment service p95 latency spiked to 4.2 s (SLA = 800 ms). "
            "Runbook: https://internal.cbg.com/runbooks/payment-svc-latency",
            "PagerDuty Bot",
            ":warning:",
        ),
        (
            "Admin SSH credentials for prod cluster rotated. New password stored in "
            "1Password 'Production / SSH / prod-cluster-admin'.",
            "Infrastructure",
            ":closed_lock_with_key:",
        ),
    ],

    # ── Researcher channel (Medium risk — pre-publication IP) ─────────────
    "research-team": [
        (
            "PRE-PUBLICATION CONFIDENTIAL: drug candidate CBG-441 shows 73% efficacy "
            "in phase-2 trials (n=312). Do not share outside this channel. "
            "Nature submission planned for 2026-06-01.",
            "Dr. Chen",
            ":microscope:",
        ),
        (
            "Manuscript 'Novel binding mechanism of CBG-441' submitted to Nature Methods. "
            "Under peer review — embargo strictly enforced until acceptance.",
            "Research Lead",
            ":scroll:",
        ),
        (
            "Dataset E-2047 (18-month exclusivity window active) uploaded to the "
            "secure research share. Access restricted to this channel members only.",
            "Lab Manager",
            ":file_folder:",
        ),
        (
            "Q2 experiment schedule: E-2048 starts Monday, E-2049 in parallel from Wednesday. "
            "Budget approval pending CFO sign-off.",
            "Research Lead",
            ":clipboard:",
        ),
    ],

    # ── Management channel (Critical — exec impersonation, strategic data) ─
    "exec-private": [
        (
            "Wire transfer to Acme Corp for $240,000 needs board approval before EOD Thursday. "
            "@sarah please confirm the receiving account details are still correct before we proceed.",
            "CEO",
            ":money_with_wings:",
        ),
        (
            "Q3 acquisition target shortlist (attached in thread). "
            "Keep strictly confidential — not for distribution outside this channel. "
            "Legal review by 2026-05-21.",
            "CFO",
            ":briefcase:",
        ),
        (
            "Board deck for Thursday investor call uploaded to the exec Google Drive folder. "
            "This is pre-NDA, pre-public material — do not forward.",
            "Chief of Staff",
            ":bar_chart:",
        ),
        (
            "Headcount plan for FY2027: targeting 15% reduction in ops, +8% in product. "
            "Discussion Thursday post-board call. Numbers are not final.",
            "CEO",
            ":chart_with_downwards_trend:",
        ),
    ],

    # ── HR channel (Critical — employee PII, salary, terminations) ────────
    "hr-internal": [
        (
            "Compensation adjustment — John Smith (EMP-2847): "
            "base $95,000 → $112,000, effective 2026-06-01. "
            "Please process in Workday before Friday.",
            "HR Director",
            ":moneybag:",
        ),
        (
            "Termination scheduled: Maria Garcia (EMP-3104, DOB 1988-03-14, "
            "SSN ending 7291) on 2026-05-20. Manager briefed. "
            "Exit interview 15:00, please send calendar invite.",
            "HR Manager",
            ":clipboard:",
        ),
        (
            "Q1 health insurance claims data uploaded to HR secure folder. "
            "Contains DOB, diagnosis codes, and coverage amounts for 187 employees. "
            "Retain for 7 years per HIPAA.",
            "Benefits Admin",
            ":hospital:",
        ),
        (
            "Performance improvement plan finalised for T. Henderson (EMP-1892). "
            "Signed copies uploaded to the HR system. "
            "Review meeting 2026-05-28 at 10:00.",
            "HR Business Partner",
            ":pencil:",
        ),
        (
            "Salary survey complete. Median engineer comp at CBG is $108K vs $114K market. "
            "Recommend 5% band adjustment — presentation to exec-private Thursday.",
            "HR Director",
            ":bar_chart:",
        ),
    ],

    # ── Supervisor channel (High risk — performance data, coercive 1:1s) ──
    "team-leads": [
        (
            "Headcount reduction: 3 positions to be eliminated in Q3 across ops. "
            "Keep strictly confidential until the official all-hands announcement. "
            "We will get 48-hour notice before HR communicates.",
            "VP Operations",
            ":shushing_face:",
        ),
        (
            "Q2 performance calibration: proposed ratings attached. "
            "Please review and respond before Friday — HR needs final numbers by EOD.",
            "People Manager",
            ":clipboard:",
        ),
        (
            "1:1 notes for Tom H. (direct report) — performance concerns documented, "
            "PIP likely to be initiated next cycle. Keep within this channel.",
            "Line Manager",
            ":memo:",
        ),
        (
            "Reminder: if your direct report has a PIP active, any communication with them "
            "about project scope changes should go through HR first.",
            "HR Business Partner",
            ":warning:",
        ),
    ],
}


def main() -> None:
    channel_ids: dict[str, str] = {}

    print("Creating CBG channels...")
    for name, is_private, persona in CHANNELS:
        try:
            cid = create_channel(name, is_private)
            if cid:
                channel_ids[name] = cid
                visibility = "private" if is_private else "public"
                print(f"  #{name} ({visibility}, {persona}) — {cid}")
            else:
                print(f"  #{name} — could not retrieve ID, skipping")
        except RuntimeError as exc:
            print(f"  #{name} — ERROR: {exc}")

    print(f"\nPosting seed messages ({RATE_DELAY}s between posts)...")
    for channel_name, messages in MESSAGES.items():
        cid = channel_ids.get(channel_name)
        if not cid:
            print(f"  #{channel_name} — skipped (no channel ID)")
            continue
        for text, username, emoji in messages:
            post(cid, text, username, emoji)
        print(f"  #{channel_name} — {len(messages)} messages posted")

    print("\nDone. CBG workspace seeded.")
    print("\nChannel IDs (copy into SLACK_CHANNEL_IDS if needed):")
    print(", ".join(channel_ids.values()))


if __name__ == "__main__":
    main()
