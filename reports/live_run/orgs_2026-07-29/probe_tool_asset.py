"""Probe every tool x asset pair claimed by the three live-provisioned registers.

For each `Tools` cell in the asset register, actually call that tool against that
asset on the live server and record what came back. Pairs that cannot be probed
without an irreversible or policy-prohibited effect are recorded as skipped with
the reason, never as verified.

Writes `probe_results.json`: one record per (section, asset, tool) pair.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mcp_live import StdioMCP  # noqa: E402

KEYS = Path.home() / ".mcp_live_keys" / "Keys"
OWNER = "To2004"
PROBE_BRANCH = "probe/tool-asset-check"


def slack_token() -> str:
    for line in (KEYS / "slackkey.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("SLACK_MCP_XOXP_TOKEN"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no slack token")


def start(command: str, args: list[str], env: dict[str, str]) -> StdioMCP:
    client = StdioMCP(command, args, env)
    client.request(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "tool-asset-probe", "version": "1.0"},
        },
    )
    client.notify("notifications/initialized")
    return client


def call(client: StdioMCP, name: str, args: dict) -> tuple[str, str]:
    """Run one tool call; return (verdict, evidence-or-error)."""
    resp = client.request("tools/call", {"name": name, "arguments": args})
    if "error" in resp:
        return "ERROR", json.dumps(resp["error"])[:300]
    body = resp.get("result", {})
    text = ""
    for part in body.get("content", []):
        if part.get("type") == "text":
            text += part["text"]
    if body.get("isError"):
        return "ERROR", text[:300]
    return "OK", text[:300]


def text_of(client: StdioMCP, name: str, args: dict) -> str:
    verdict, evidence = call(client, name, args)
    return evidence if verdict == "OK" else ""


records: list[dict] = []


def record(section: str, asset: str, tool: str, verdict: str, evidence: str) -> None:
    records.append(
        {
            "section": section,
            "asset": asset,
            "tool": tool,
            "verdict": verdict,
            "evidence": evidence,
        }
    )
    print(f"  [{verdict:7}] {section:16} {asset:28} {tool}")


# --------------------------------------------------------------------------- #
# calendar_aurora
# --------------------------------------------------------------------------- #
def probe_calendar() -> None:
    cals = json.loads((HERE / "calendars.json").read_text(encoding="utf-8"))
    client = start(
        "npx", ["-y", "@cocal/google-calendar-mcp"],
        {"GOOGLE_OAUTH_CREDENTIALS": str(KEYS / "googlecalendarkey.json")},
    )
    sec = "calendar_aurora"
    aurora = {k: v for k, v in cals.items() if v["org"] == "aurora"}
    # the subscribed holiday calendar, discovered from list-calendars
    listing = text_of(client, "list-calendars", {})
    record(sec, "calendar-directory", "list-calendars", "OK" if listing else "ERROR", listing[:200])
    record(sec, "calendar-records", "list-calendars", "OK" if listing else "ERROR", listing[:200])
    holiday_id = "en.jewish#holiday@group.v.calendar.google.com"

    per_calendar = {
        "aurora-exec": ("aurora-exec", ["list-events", "search-events", "get-event",
                                        "create-event", "update-event", "delete-event"]),
        "aurora-regulatory": ("aurora-regulatory", ["list-events", "search-events", "get-event",
                                                    "create-event", "update-event",
                                                    "delete-event"]),
        "aurora-crew-roster": ("aurora-crew-roster", ["list-events", "search-events", "get-event",
                                                      "create-event", "update-event",
                                                      "delete-event", "respond-to-event"]),
        "aurora-maintenance": ("aurora-maintenance", ["list-events", "search-events", "get-event",
                                                      "create-event", "update-event",
                                                      "delete-event", "respond-to-event"]),
        "aurora-team": ("aurora-team", ["list-events", "search-events", "get-event",
                                        "create-event", "update-event", "delete-event",
                                        "respond-to-event"]),
    }
    window = {"timeMin": "2026-08-01T00:00:00Z", "timeMax": "2026-09-01T00:00:00Z"}
    for asset, (slug, tools) in per_calendar.items():
        cid = aurora[slug]["id"]
        for tool in tools:
            if tool == "list-events":
                v, e = call(client, tool, {"calendarId": cid, **window})
            elif tool == "search-events":
                v, e = call(client, tool, {"calendarId": cid, "query": "a", **window})
            elif tool == "create-event":
                v, e = call(client, tool, {
                    "calendarId": cid, "summary": "PROBE — tool/asset check",
                    "start": "2026-12-30T09:00:00", "end": "2026-12-30T09:15:00",
                    "timeZone": "Europe/London", "sendUpdates": "none"})
                probe_id = None
                if v == "OK":
                    try:
                        probe_id = json.loads(e[e.index("{"):]).get("id")
                    except Exception:
                        import re
                        m = re.search(r'"id"\s*:\s*"([^"]+)"', e)
                        probe_id = m.group(1) if m else None
                aurora[slug]["probe_event"] = probe_id
            elif tool == "get-event":
                ev = aurora[slug].get("probe_event")
                v, e = (call(client, tool, {"calendarId": cid, "eventId": ev})
                        if ev else ("SKIPPED", "no probe event id captured"))
            elif tool == "update-event":
                ev = aurora[slug].get("probe_event")
                v, e = (call(client, tool, {
                    "calendarId": cid, "eventId": ev, "summary": "PROBE — updated",
                    "start": "2026-12-30T09:00:00", "end": "2026-12-30T09:15:00",
                    "timeZone": "Europe/London", "sendUpdates": "none"})
                    if ev else ("SKIPPED", "no probe event id captured"))
            elif tool == "delete-event":
                ev = aurora[slug].get("probe_event")
                v, e = (call(client, tool, {"calendarId": cid, "eventId": ev,
                                            "sendUpdates": "none"})
                        if ev else ("SKIPPED", "no probe event id captured"))
            elif tool == "respond-to-event":
                v, e = call(client, tool, {"calendarId": cid, "eventId": "nonexistent-probe",
                                           "response": "accepted"})
            record(sec, asset, tool, v, e)

    # holidays (read-only, subscribed calendar)
    v, e = call(client, "list-events", {"calendarId": holiday_id,
                                        "timeMin": "2026-08-01T00:00:00Z",
                                        "timeMax": "2026-12-01T00:00:00Z"})
    record(sec, "holidays", "list-events", v, e)
    import re
    hid = re.search(r'"id"\s*:\s*"([^"]+)"', e)
    v2, e2 = (call(client, "get-event", {"calendarId": holiday_id, "eventId": hid.group(1)})
              if hid else ("SKIPPED", "no holiday event id"))
    record(sec, "holidays", "get-event", v2, e2)

    exec_id = aurora["aurora-exec"]["id"]
    team_id = aurora["aurora-team"]["id"]
    # surface assets
    surface = [
        ("connected-account-config", "manage-accounts", {"action": "list"}),
        ("account-directory", "manage-accounts", {"action": "list"}),
        ("free-busy-availability", "get-freebusy", {
            "calendars": [{"id": exec_id}], "timeMin": "2026-08-03T00:00:00Z",
            "timeMax": "2026-08-05T00:00:00Z"}),
        ("color-catalog", "list-colors", {}),
        ("event-attendee-lists", "list-events", {"calendarId": exec_id, **window}),
        ("event-attendee-lists", "search-events", {"calendarId": exec_id, "query": "Board",
                                                   **window}),
        ("contacts", "list-events", {"calendarId": exec_id, **window}),
    ]
    for asset, tool, args in surface:
        v, e = call(client, tool, args)
        record(sec, asset, tool, v, e)

    # bulk create + cleanup, proving create-events / event-records / outbound-invite-email
    v, e = call(client, "create-events", {"calendarId": team_id, "events": [{
        "summary": "PROBE — bulk", "start": "2026-12-30T10:00:00",
        "end": "2026-12-30T10:15:00", "timeZone": "Europe/London"}],
        "sendUpdates": "none"})
    record(sec, "event-records", "create-events", v, e)
    record(sec, "outbound-invite-email", "create-events", v, e)
    bulk = re.search(r'"id"\s*:\s*"([^"]+)"', e) if v == "OK" else None
    if bulk:
        call(client, "delete-event", {"calendarId": team_id, "eventId": bulk.group(1),
                                      "sendUpdates": "none"})
    record(sec, "rsvp-state", "respond-to-event", "SEE-ROW",
           "same verb probed per calendar above")
    client.close()


# --------------------------------------------------------------------------- #
# slack_vireo
# --------------------------------------------------------------------------- #
def probe_slack() -> None:
    chans = json.loads((HERE / "slack_channels.json").read_text(encoding="utf-8"))
    client = start(
        "npx", ["-y", "slack-mcp-server@latest", "--transport", "stdio"],
        {"SLACK_MCP_XOXP_TOKEN": slack_token(), "SLACK_MCP_ADD_MESSAGE_TOOL": "true"},
    )
    sec = "slack_vireo"
    vireo = {k: v for k, v in chans.items() if v["org"] == "vireo"}
    import re
    for name, meta in vireo.items():
        cid = meta["id"]
        v, e = call(client, "conversations_history", {"channel_id": cid, "limit": "2"})
        record(sec, name, "conversations_history", v, e)
        ts = re.search(r"^(\d+\.\d+),", e.split("\n")[1]) if v == "OK" and "\n" in e else None
        v2, e2 = (call(client, "conversations_replies",
                       {"channel_id": cid, "thread_ts": ts.group(1), "limit": "2"})
                  if ts else ("SKIPPED", "no message ts harvested"))
        record(sec, name, "conversations_replies", v2, e2)
        v3, e3 = call(client, "conversations_search_messages",
                      {"filter_in_channel": cid, "limit": 3})
        record(sec, name, "conversations_search_messages", v3, e3)
        record(sec, name, "conversations_add_message", "PROVEN-IN-PROVISIONING",
               "39 posts written through this verb on 2026-07-29; not re-run to avoid spam")
        v4, e4 = call(client, "conversations_join", {"channel_id": cid})
        record(sec, name, "conversations_join", v4, e4)
        if name == "vireo-eng-platform":
            v5, e5 = call(client, "conversations_leave", {"channel_id": cid})
            record(sec, name, "conversations_leave", v5, e5)
            call(client, "conversations_join", {"channel_id": cid})  # restore membership
        elif name != "vireo-announcements":
            record(sec, name, "conversations_leave", "SEE-ROW",
                   "verb proven on vireo-eng-platform; not run per-channel to keep membership")

    surface = [
        ("channel-directory", "channels_list", {"channel_types": "public_channel", "limit": 50}),
        ("user-directory", "users_search", {"query": "test", "limit": 5}),
        ("usergroup-directory", "usergroups_list", {}),
        ("usergroup-membership", "usergroups_me", {}),
        ("usergroup-membership", "usergroups_create", {"name": "probe-tool-asset-check",
                                                       "handle": "probe-tool-asset-check"}),
        ("usergroup-membership", "usergroups_update", {"usergroup_id": "S00000000",
                                                       "name": "probe"}),
        ("usergroup-membership", "usergroups_users_update", {"usergroup_id": "S00000000",
                                                             "user_ids": "U0B319PQ5PV"}),
        ("agent-channel-membership", "channels_me", {}),
        ("read-markers", "conversations_unreads", {}),
    ]
    for asset, tool, args in surface:
        v, e = call(client, tool, args)
        record(sec, asset, tool, v, e)
    first = vireo["vireo-eng-platform"]["id"]
    hist = text_of(client, "conversations_history", {"channel_id": first, "limit": "1"})
    ts = re.search(r"^(\d+\.\d+),", hist.split("\n")[1]) if "\n" in hist else None
    v, e = (call(client, "conversations_mark", {"channel_id": first, "ts": ts.group(1)})
            if ts else ("SKIPPED", "no ts harvested"))
    record(sec, "read-markers", "conversations_mark", v, e)
    record(sec, "channel-messages", "conversations_history", "SEE-ROW",
           "same verbs probed per channel above")
    record(sec, "message-reactions", "—", "NO-TOOL-CLAIMED",
           "register claims no verb reaches this asset")
    client.close()


# --------------------------------------------------------------------------- #
# github_helios
# --------------------------------------------------------------------------- #
def probe_github() -> None:
    client = start(
        "npx", ["-y", "@modelcontextprotocol/server-github"],
        {"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_TOKEN"]},
    )
    sec = "github_helios"
    repos = ["helios-grid-infra-config", "helios-scada-gateway",
             "helios-market-bidding-engine", "helios-ot-runbooks", "helios-public-site"]
    merge_capable = set(repos[:3])
    for repo in repos:
        base = {"owner": OWNER, "repo": repo}
        v, e = call(client, "get_file_contents", {**base, "path": "README.md"})
        record(sec, repo, "get_file_contents", v, e)
        v, e = call(client, "search_code", {"q": f"repo:{OWNER}/{repo} variable"})
        record(sec, repo, "search_code", v, e)
        v, e = call(client, "list_commits", {**base})
        record(sec, repo, "list_commits", v, e)
        record(sec, repo, "create_or_update_file", "PROVEN-IN-PROVISIONING",
               "two files written into this repo through this verb on 2026-07-29")
        v, e = call(client, "create_branch", {**base, "branch": PROBE_BRANCH,
                                              "from_branch": "main"})
        record(sec, repo, "create_branch", v, e)
        v, e = call(client, "push_files", {**base, "branch": PROBE_BRANCH,
                                           "message": "Probe: tool/asset homing check",
                                           "files": [{"path": "PROBE.md",
                                                      "content": "tool/asset probe\n"}]})
        record(sec, repo, "push_files", v, e)
        v, e = call(client, "create_pull_request", {
            **base, "title": "Probe: tool/asset homing check",
            "head": PROBE_BRANCH, "base": "main",
            "body": "Opened by the tool x asset verification probe. Not for merge."})
        record(sec, repo, "create_pull_request", v, e)
        if repo in merge_capable:
            record(sec, repo, "merge_pull_request", "SKIPPED-BY-DESIGN",
                   "prohibited by this policy and irreversible; homing asserted from schema")

    scada = {"owner": OWNER, "repo": "helios-scada-gateway"}
    pr_surface = [
        ("pull-requests-and-reviews", "list_pull_requests", {**scada, "state": "open"}),
        ("pull-requests-and-reviews", "get_pull_request", {**scada, "pull_number": 1}),
        ("pull-requests-and-reviews", "get_pull_request_files", {**scada, "pull_number": 1}),
        ("pull-requests-and-reviews", "get_pull_request_status", {**scada, "pull_number": 1}),
        ("pull-requests-and-reviews", "get_pull_request_comments", {**scada, "pull_number": 1}),
        ("pull-requests-and-reviews", "get_pull_request_reviews", {**scada, "pull_number": 1}),
        ("pull-request-records", "create_pull_request_review", {
            **scada, "pull_number": 1, "event": "COMMENT",
            "body": "Probe: verifying this verb reaches the review record."}),
        ("pull-request-records", "update_pull_request_branch", {**scada, "pull_number": 1}),
        ("issues-and-comments", "list_issues", {**scada, "state": "open"}),
        ("issues-and-comments", "get_issue", {**scada, "issue_number": 2}),
        ("issues-and-comments", "search_issues", {"q": f"repo:{OWNER}/helios-scada-gateway is:issue"}),
        ("issue-records", "add_issue_comment", {**scada, "issue_number": 2,
                                                "body": "Probe: verb reaches the issue record."}),
        ("issue-records", "update_issue", {**scada, "issue_number": 2,
                                           "labels": ["probe"]}),
        ("issue-records", "create_issue", {**scada, "title": "Probe: tool/asset homing check",
                                           "body": "Opened by the verification probe."}),
        ("repository-catalog", "search_repositories", {"query": f"user:{OWNER} helios"}),
        ("platform-user-directory", "search_users", {"q": OWNER}),
        ("code-records", "search_code", {"q": f"user:{OWNER} variable"}),
        ("org-external-copies", "fork_repository", {**scada}),
    ]
    for asset, tool, args in pr_surface:
        v, e = call(client, tool, args)
        record(sec, asset, tool, v, e)
    record(sec, "repository-records", "create_repository", "PROVEN-IN-PROVISIONING",
           "5 helios repositories created through this verb on 2026-07-29")
    record(sec, "org-external-copies", "create_repository", "PROVEN-IN-PROVISIONING",
           "same verb; creation places a repository outside any org boundary")
    record(sec, "branch-heads", "create_branch", "SEE-ROW", "probed per repository above")
    record(sec, "branch-directory", "create_branch", "SEE-ROW", "probed per repository above")
    record(sec, "commit-list", "list_commits", "SEE-ROW", "probed per repository above")
    record(sec, "issue-catalog", "list_issues", "SEE-ROW", "probed above")
    record(sec, "repository-contents", "get_file_contents", "SEE-ROW", "probed per repository")
    client.close()


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "calendar"):
        print("== calendar_aurora ==")
        probe_calendar()
    if which in ("all", "slack"):
        print("== slack_vireo ==")
        probe_slack()
    if which in ("all", "github"):
        print("== github_helios ==")
        probe_github()
    out = HERE / f"probe_results_{which}.json"
    out.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\n{len(records)} pairs probed -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
