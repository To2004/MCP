#!/usr/bin/env python3
"""Sweep every tool of the three live MCP servers across every container.

The existing corpus exercises whatever its personas happened to do, so most
``(tool, asset)`` cells never fire. This sweep aims at coverage instead: each
advertised tool, run against each container the register knows, so the binding
evaluation has real calls in as many cells as the live surfaces allow.

Safety, following ``live_call_run.py``:

* reads run freely — they change nothing;
* writes are tagged with :data:`PROBE_TAG`, confined to sandbox artifacts this
  run creates, and cleaned up afterwards from ids captured in this run's own
  responses;
* Slack is **read-only** here: its catalog has no delete verb, so a message
  written cannot be withdrawn;
* no verb that removes a user, revokes the caller's access or deletes a
  pre-existing repository is ever called.

Writes to the register's prohibited surfaces (the crew-roster and maintenance
calendars, the CIP-perimeter repositories) are deliberately **not** performed:
this is a coverage sweep, not an attack corpus.

Usage::

    PATH=<node-env>/bin:$PATH uv run python scripts/live_call_sweep.py --reads-only
    PATH=<node-env>/bin:$PATH uv run python scripts/live_call_sweep.py
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "reports" / "live_run" / "orgs_2026-07-29"))

from mcp_live import StdioMCP  # noqa: E402

from mcp_security.binding.identifiers import name_coverage  # noqa: E402
from mcp_security.static_scoring.server_policies import (  # noqa: E402
    parse_asset_register,
    policy_for,
)

KEYS = Path.home() / ".mcp_live_keys" / "Keys"
OUT = REPO_ROOT / "reports" / "experiments" / "v8" / "sweep"
PROBE_TAG = "[mcp-v8-sweep]"
STAMP = "2026-08-06"
OWNER = "To2004"

#: A container name binds to a register asset only at or above this coverage,
#: the threshold validated against all three live listings (18/18, 0 false
#: positives across 40 cross-organization decoys).
LABEL_FLOOR = 0.8

rows: list[dict] = []
_idx = 0


def boot(client: StdioMCP) -> list[dict]:
    client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "v8-sweep", "version": "1.0"}})
    client.notify("notifications/initialized")
    return client.request("tools/list").get("result", {}).get("tools", [])


def call(client: StdioMCP, org: str, tool: str, args: dict, asset: str,
         category: str = "SWEEP") -> tuple[str, str]:
    """Run one call and record it in the corpus shape."""
    global _idx
    _idx += 1
    try:
        resp = client.request("tools/call", {"name": tool, "arguments": args})
        body = resp.get("result", resp.get("error"))
        if isinstance(body, dict) and body.get("content"):
            evidence = "".join(p.get("text", "") for p in body["content"])
            status = "ERROR" if body.get("isError") else "OK"
        else:
            evidence, status = json.dumps(body), "ERROR"
    except Exception as exc:  # a dead server must not lose the rows already taken
        evidence, status = f"{type(exc).__name__}: {exc}", "ERROR"
    rows.append({
        "index": _idx, "timestamp": f"{STAMP}T12:00:{_idx % 60:02d}", "org": org,
        "persona": f"sweep@{org}", "category": category, "asset": asset, "tool": tool,
        "status": status, "args": json.dumps(args, ensure_ascii=False),
        "output": evidence[:2000], "run_id": "v8_sweep", "synthetic": "false",
    })
    print(f"  [{'ok ' if status == 'OK' else 'ERR'}] {org:16s} {asset:26s} {tool}")
    time.sleep(0.1)
    return status, evidence


def label_for(name: str, register: list) -> str | None:
    """The register asset a live container name denotes, or None."""
    scored = [(name_coverage(name, row.asset_id), row.asset_id) for row in register]
    score, asset = max(scored) if scored else (0.0, "")
    return asset if score >= LABEL_FLOOR else None


# --------------------------------------------------------------------------- #
# calendar_aurora
# --------------------------------------------------------------------------- #
def sweep_calendar(reads_only: bool) -> None:
    register = parse_asset_register(policy_for("calendar_aurora").text)
    client = StdioMCP("npx", ["-y", "@cocal/google-calendar-mcp"],
                      {"GOOGLE_OAUTH_CREDENTIALS": str(KEYS / "googlecalendarkey.json"),
                       "GOOGLE_CALENDAR_MCP_TOKEN_PATH": str(KEYS / "googlecalendartoken.json")})
    org = "calendar_aurora"
    try:
        boot(client)
        _, listing = call(client, org, "list-calendars", {}, "calendar-directory")
        calendars = {c["id"]: c.get("summary", "") for c in json.loads(listing)["calendars"]}
        mine = {cid: label_for(name, register) for cid, name in calendars.items()}
        mine = {cid: asset for cid, asset in mine.items() if asset}
        print(f"  -- {len(mine)} aurora calendars in register scope --")

        call(client, org, "list-colors", {}, "color-catalog")
        call(client, org, "get-current-time", {}, "clock")
        window = {"timeMin": "2026-08-01T00:00:00Z", "timeMax": "2026-12-31T00:00:00Z"}
        # The server caps free/busy at a three-month span, so this one query
        # cannot reuse the wider listing window.
        call(client, org, "get-freebusy",
             {"calendars": [{"id": c} for c in list(mine)[:3]],
              "timeMin": "2026-09-01T00:00:00Z", "timeMax": "2026-11-01T00:00:00Z"},
             "free-busy-availability")

        first_event: dict[str, str] = {}
        for cid, asset in mine.items():
            _, out = call(client, org, "list-events", {"calendarId": cid, **window}, asset)
            call(client, org, "search-events",
                 {"calendarId": cid, "query": "review", **window}, asset)
            try:
                events = json.loads(out).get("events", [])
                if events:
                    first_event[cid] = events[0]["id"]
                    call(client, org, "get-event",
                         {"calendarId": cid, "eventId": events[0]["id"]}, asset)
            except (ValueError, KeyError, IndexError):
                pass

        if reads_only:
            return
        # Writes: the ordinary team calendar only. The register prohibits writes
        # to the crew-roster and maintenance calendars, and this is a coverage
        # sweep rather than a policy-violation corpus.
        team = next((cid for cid, a in mine.items() if a == "aurora-team"), None)
        if team is None:
            return
        created: list[str] = []
        _, out = call(client, org, "create-event",
                      {"calendarId": team, "summary": f"{PROBE_TAG} coverage probe",
                       "start": "2026-12-28T10:00:00", "end": "2026-12-28T10:15:00",
                       "timeZone": "Europe/London", "sendUpdates": "none"}, "aurora-team")
        try:
            created.append(json.loads(out)["event"]["id"])
        except (ValueError, KeyError):
            pass
        _, out = call(client, org, "create-events",
                      {"calendarId": team, "sendUpdates": "none", "events": [
                          {"summary": f"{PROBE_TAG} bulk probe",
                           "start": "2026-12-29T10:00:00", "end": "2026-12-29T10:15:00",
                           "timeZone": "Europe/London"}]}, "event-records")
        try:
            created += [e["id"] for e in json.loads(out).get("results", []) if "id" in e]
        except ValueError:
            pass
        for event_id in created[:1]:
            call(client, org, "update-event",
                 {"calendarId": team, "eventId": event_id,
                  "summary": f"{PROBE_TAG} coverage probe (updated)",
                  "sendUpdates": "none"}, "aurora-team")
            call(client, org, "respond-to-event",
                 {"calendarId": team, "eventId": event_id, "response": "accepted"}, "rsvp-state")
        print(f"  -- calendar cleanup: {len(created)} probe events --")
        for event_id in created:
            call(client, org, "delete-event",
                 {"calendarId": team, "eventId": event_id, "sendUpdates": "none"},
                 "event-records", category="CLEANUP")
    finally:
        client.close()


# --------------------------------------------------------------------------- #
# github_helios
# --------------------------------------------------------------------------- #
def gh_rest(method: str, path: str, token: str, body: dict | None = None) -> int:
    """Direct REST, used only for cleanup verbs the MCP catalog does not expose."""
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", method,
           "-H", f"Authorization: token {token}", "-H", "Accept: application/vnd.github+json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    cmd.append(f"https://api.github.com{path}")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else -1


def sweep_github(reads_only: bool) -> None:
    register = parse_asset_register(policy_for("github_helios").text)
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                           check=True).stdout.strip()
    client = StdioMCP("npx", ["-y", "@modelcontextprotocol/server-github"],
                      {"GITHUB_PERSONAL_ACCESS_TOKEN": token})
    org = "github_helios"
    try:
        boot(client)
        _, out = call(client, org, "search_repositories",
                      {"query": f"user:{OWNER}", "perPage": 100}, "repository-catalog")
        repos = [i["name"] for i in json.loads(out).get("items", [])]
        mine = {r: label_for(r, register) for r in repos}
        mine = {r: a for r, a in mine.items() if a}
        print(f"  -- {len(mine)} helios repositories in register scope --")

        call(client, org, "search_users", {"q": f"user:{OWNER}"}, "platform-user-directory")
        call(client, org, "search_code", {"q": f"user:{OWNER} helios"}, "code-records")
        call(client, org, "search_issues", {"q": f"user:{OWNER} is:issue"}, "issue-catalog")

        for repo, asset in mine.items():
            base = {"owner": OWNER, "repo": repo}
            call(client, org, "get_file_contents", {**base, "path": "README.md"}, asset)
            call(client, org, "list_commits", base, asset)
            _, out = call(client, org, "list_issues", {**base, "state": "all"}, asset)
            try:
                issues = json.loads(out)
                if isinstance(issues, list) and issues:
                    call(client, org, "get_issue",
                         {**base, "issue_number": issues[0]["number"]}, asset)
            except (ValueError, KeyError, IndexError):
                pass
            _, out = call(client, org, "list_pull_requests", {**base, "state": "all"}, asset)
            try:
                prs = json.loads(out)
                if isinstance(prs, list) and prs:
                    number = prs[0]["number"]
                    for verb in ("get_pull_request", "get_pull_request_files",
                                 "get_pull_request_status", "get_pull_request_comments",
                                 "get_pull_request_reviews"):
                        call(client, org, verb, {**base, "pull_number": number}, asset)
            except (ValueError, KeyError, IndexError):
                pass

        if reads_only:
            return
        # Writes: the public site only — never inside the CIP perimeter.
        repo = next((r for r, a in mine.items() if a == "helios-public-site"), None)
        if repo is None:
            return
        base = {"owner": OWNER, "repo": repo}
        branch = f"sweep/coverage-{STAMP}"
        branches, issues = [], []
        status, _ = call(client, org, "create_branch",
                         {**base, "branch": branch, "from_branch": "main"}, "branch-heads")
        if status == "OK":
            branches.append(branch)
            call(client, org, "create_or_update_file",
                 {**base, "branch": branch, "path": f"sweep-{STAMP}.md",
                  "message": f"{PROBE_TAG} coverage probe",
                  "content": f"{PROBE_TAG}\n"}, "repository-contents")
            call(client, org, "push_files",
                 {**base, "branch": branch, "message": f"{PROBE_TAG} push probe",
                  "files": [{"path": f"sweep-{STAMP}-b.md", "content": f"{PROBE_TAG}\n"}]},
                 "repository-contents")
            call(client, org, "create_pull_request",
                 {**base, "title": f"{PROBE_TAG} coverage probe", "head": branch,
                  "base": "main", "body": PROBE_TAG}, "pull-request-records")
        _, out = call(client, org, "create_issue",
                      {**base, "title": f"{PROBE_TAG} coverage probe", "body": PROBE_TAG},
                      "issue-records")
        try:
            number = json.loads(out)["number"]
            issues.append(number)
            call(client, org, "add_issue_comment",
                 {**base, "issue_number": number, "body": f"{PROBE_TAG} comment"},
                 "issues-and-comments")
            call(client, org, "update_issue",
                 {**base, "issue_number": number, "labels": ["triage"]}, "issue-records")
        except (ValueError, KeyError):
            pass

        print(f"  -- github cleanup: {len(branches)} branches, {len(issues)} issues --")
        for number in issues:
            gh_rest("PATCH", f"/repos/{OWNER}/{repo}/issues/{number}", token, {"state": "closed"})
        for name in branches:
            gh_rest("DELETE", f"/repos/{OWNER}/{repo}/git/refs/heads/{name}", token)
    finally:
        client.close()


# --------------------------------------------------------------------------- #
# slack_vireo — read-only: this catalog cannot delete a message
# --------------------------------------------------------------------------- #
def sweep_slack() -> None:
    register = parse_asset_register(policy_for("slack_vireo").text)
    token = next(line.split("=", 1)[1].strip().strip('"')
                 for line in (KEYS / "slackkey.txt").read_text().splitlines()
                 if line.startswith("SLACK_MCP_XOXP_TOKEN"))
    client = StdioMCP("npx", ["-y", "slack-mcp-server@latest", "--transport", "stdio"],
                      {"SLACK_MCP_XOXP_TOKEN": token, "SLACK_MCP_ADD_MESSAGE_TOOL": "false"})
    org = "slack_vireo"
    try:
        boot(client)
        _, out = call(client, org, "channels_list",
                      {"channel_types": "public_channel", "limit": 100}, "channel-directory")
        channels = {}
        for line in out.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 2 and parts[0].startswith("C"):
                asset = label_for(parts[1], register)
                if asset:
                    channels[parts[0]] = asset
        print(f"  -- {len(channels)} vireo channels in register scope --")

        call(client, org, "channels_me", {}, "agent-channel-membership")
        call(client, org, "usergroups_list", {}, "usergroup-directory")
        call(client, org, "usergroups_me", {"action": "list"}, "usergroup-membership")
        call(client, org, "users_search", {"query": "a", "limit": 5}, "user-directory")
        call(client, org, "conversations_unreads", {}, "read-markers")
        for cid, asset in channels.items():
            _, out = call(client, org, "conversations_history",
                          {"channel_id": cid, "limit": 5}, asset)
            call(client, org, "conversations_search_messages",
                 {"filter_in_channel": cid, "search_query": "update", "limit": 5}, asset)
            for line in out.splitlines()[1:2]:
                ts = line.split(",")[0]
                if ts and ts[0].isdigit():
                    call(client, org, "conversations_replies",
                         {"channel_id": cid, "thread_ts": ts, "limit": 5}, asset)
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reads-only", action="store_true",
                        help="skip every write, even the tagged sandbox ones")
    parser.add_argument("--only", action="append", choices=["calendar", "github", "slack"])
    options = parser.parse_args()
    wanted = options.only or ["calendar", "github", "slack"]

    OUT.mkdir(parents=True, exist_ok=True)
    if "calendar" in wanted:
        print("\n=== calendar_aurora ===")
        sweep_calendar(options.reads_only)
    if "github" in wanted:
        print("\n=== github_helios ===")
        sweep_github(options.reads_only)
    if "slack" in wanted:
        print("\n=== slack_vireo ===")
        sweep_slack()

    path = OUT / "sweep_calls.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print(f"\nwrote {path}: {len(rows)} calls, {ok} OK, {len(rows) - ok} ERROR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
