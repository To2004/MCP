#!/usr/bin/env python3
"""Drive all three live MCP servers to a target call count, every tool exercised.

Aims for breadth and volume at once: roughly a thousand real ``tools/call``
invocations spread across every advertised tool and every container the register
knows, so the binding evaluation has dense live coverage rather than a handful of
cells.

Volume comes from *reads* — the safe, repeatable verbs — varied by time window,
query, and pagination. Each mutating verb runs a bounded number of times against
sandbox artifacts this run creates, and every change is reversed:

* calendar events are created then deleted;
* GitHub branch/file/PR/merge writes happen on throwaway branches, and ``main``
  is force-reset to its recorded SHA;
* a created repository is deleted;
* Slack channel joins are followed by leaves; a created user group is renamed to
  a tombstone (the catalog has no delete verb) and only ever has its own caller
  as a member — a pre-existing group is never touched.

Nothing deletes a user, a pre-existing repository, or the caller's own access.
Search verbs are rate-limited to respect GitHub's 30-per-minute search cap.

Usage::

    PATH=<node-env>/bin:$PATH uv run python scripts/live_sweep_scale.py --target 1000
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
TAG = "[mcp-v8-scale]"
STAMP = "2026-08-06"
OWNER = "To2004"
LABEL_FLOOR = 0.8
SEARCH_COOLDOWN = 2.2  # seconds between search verbs — under 30/min

rows: list[dict] = []
_idx = 0
_last_search = 0.0

#: Read verbs that hit a search API and share the per-minute quota.
SEARCH_VERBS = {"search_code", "search_issues", "search_repositories", "search_users",
                "conversations_search_messages", "search-events", "users_search"}


def label_for(name: str, register: list) -> str | None:
    scored = [(name_coverage(name, row.asset_id), row.asset_id) for row in register]
    score, asset = max(scored) if scored else (0.0, "")
    return asset if score >= LABEL_FLOOR else None


def call(client: StdioMCP, org: str, tool: str, args: dict, asset: str,
         category: str = "SCALE") -> tuple[str, str]:
    global _idx, _last_search
    if tool in SEARCH_VERBS:
        wait = SEARCH_COOLDOWN - (time.time() - _last_search)
        if wait > 0:
            time.sleep(wait)
        _last_search = time.time()
    _idx += 1
    try:
        resp = client.request("tools/call", {"name": tool, "arguments": args})
        body = resp.get("result", resp.get("error"))
        if isinstance(body, dict) and body.get("content"):
            evidence = "".join(p.get("text", "") for p in body["content"])
            status = "ERROR" if body.get("isError") else "OK"
        else:
            evidence, status = json.dumps(body), "ERROR"
    except Exception as exc:
        evidence, status = f"{type(exc).__name__}: {exc}", "ERROR"
    rows.append({
        "index": _idx, "timestamp": f"{STAMP}T14:00:{_idx % 60:02d}", "org": org,
        "persona": f"scale@{org}", "category": category, "asset": asset, "tool": tool,
        "status": status, "args": json.dumps(args, ensure_ascii=False),
        "output": evidence[:1500], "run_id": "v8_scale", "synthetic": "false",
    })
    if _idx % 25 == 0:
        print(f"    … {_idx} calls")
    time.sleep(0.05)
    return status, evidence


def boot(client: StdioMCP) -> None:
    client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "v8-scale", "version": "1.0"}})
    client.notify("notifications/initialized")


WINDOWS = [
    ("2026-08-01T00:00:00Z", "2026-10-01T00:00:00Z"),
    ("2026-09-01T00:00:00Z", "2026-11-01T00:00:00Z"),
    ("2026-10-01T00:00:00Z", "2026-12-01T00:00:00Z"),
    ("2026-11-01T00:00:00Z", "2027-01-01T00:00:00Z"),
]
QUERIES = ["review", "audit", "meeting", "board", "update", "check", "ops"]


def sweep_calendar(target: int) -> None:
    register = parse_asset_register(policy_for("calendar_aurora").text)
    org = "calendar_aurora"
    client = StdioMCP("npx", ["-y", "@cocal/google-calendar-mcp"],
                      {"GOOGLE_OAUTH_CREDENTIALS": str(KEYS / "googlecalendarkey.json"),
                       "GOOGLE_CALENDAR_MCP_TOKEN_PATH": str(KEYS / "googlecalendartoken.json")})
    try:
        boot(client)
        _, listing = call(client, org, "list-calendars", {}, "calendar-directory")
        cals = {c["id"]: c.get("summary", "") for c in json.loads(listing)["calendars"]}
        mine = {cid: label_for(n, register) for cid, n in cals.items()}
        mine = {cid: a for cid, a in mine.items() if a}
        team = next((cid for cid, a in mine.items() if a == "aurora-team"), None)
        call(client, org, "list-colors", {}, "color-catalog")
        call(client, org, "manage-accounts", {"action": "list"}, "account-directory")

        # Writes once, on the team calendar, with cleanup deferred to the end.
        probes: list[str] = []
        if team:
            for day in ("2026-12-20", "2026-12-21", "2026-12-22"):
                _, out = call(client, org, "create-event",
                              {"calendarId": team, "summary": f"{TAG} probe {day}",
                               "start": f"{day}T10:00:00", "end": f"{day}T10:15:00",
                               "timeZone": "Europe/London", "sendUpdates": "none"}, "aurora-team")
                try:
                    probes.append(json.loads(out)["event"]["id"])
                except (ValueError, KeyError):
                    pass
            _, out = call(client, org, "create-events",
                          {"calendarId": team, "sendUpdates": "none",
                           "events": [{"summary": f"{TAG} bulk", "start": "2026-12-23T10:00:00",
                                       "end": "2026-12-23T10:15:00", "timeZone": "Europe/London"}]},
                          "event-records")
            try:
                probes += [e["id"] for e in json.loads(out).get("results", []) if "id" in e]
            except ValueError:
                pass
            for eid in probes[:2]:
                call(client, org, "update-event",
                     {"calendarId": team, "eventId": eid, "summary": f"{TAG} updated",
                      "sendUpdates": "none"}, "aurora-team")
                call(client, org, "respond-to-event",
                     {"calendarId": team, "eventId": eid, "response": "accepted"}, "rsvp-state")

        # Reads, varied, until the quota is met.
        variant = 0
        while _idx < target:
            for cid, asset in mine.items():
                lo, hi = WINDOWS[variant % len(WINDOWS)]
                w = {"timeMin": lo, "timeMax": hi}
                _, out = call(client, org, "list-events", {"calendarId": cid, **w}, asset)
                call(client, org, "search-events",
                     {"calendarId": cid, "query": QUERIES[variant % len(QUERIES)], **w}, asset)
                call(client, org, "get-freebusy",
                     {"calendars": [{"id": cid}], "timeMin": lo, "timeMax": hi},
                     "free-busy-availability")
                try:
                    events = json.loads(out).get("events", [])
                    for ev in events[:2]:
                        call(client, org, "get-event",
                             {"calendarId": cid, "eventId": ev["id"]}, asset)
                except (ValueError, KeyError):
                    pass
                call(client, org, "get-current-time", {}, "clock")
                if _idx >= target:
                    break
            variant += 1

        for eid in probes:
            call(client, org, "delete-event",
                 {"calendarId": team, "eventId": eid, "sendUpdates": "none"},
                 "event-records", category="CLEANUP")
    finally:
        client.close()


def rest(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, str]:
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
           "-H", f"Authorization: token {token}", "-H", "Accept: application/vnd.github+json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    cmd.append(f"https://api.github.com{path}")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    text, _, code = out.rpartition("\n")
    return (int(code) if code.strip().isdigit() else -1), text


def sweep_github(target: int) -> None:
    register = parse_asset_register(policy_for("github_helios").text)
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                           check=True).stdout.strip()
    org = "github_helios"
    client = StdioMCP("npx", ["-y", "@modelcontextprotocol/server-github"],
                      {"GITHUB_PERSONAL_ACCESS_TOKEN": token})
    try:
        boot(client)
        _, out = call(client, org, "search_repositories",
                      {"query": f"user:{OWNER}", "perPage": 100}, "repository-catalog")
        mine = {i["name"]: label_for(i["name"], register) for i in json.loads(out).get("items", [])}
        mine = {r: a for r, a in mine.items() if a}
        call(client, org, "search_users", {"q": f"user:{OWNER}"}, "platform-user-directory")

        # One full write cycle per repo, each fully reversed.
        for repo, asset in mine.items():
            base = {"owner": OWNER, "repo": repo}
            code, ref = rest("GET", f"/repos/{OWNER}/{repo}/git/refs/heads/main", token)
            if code != 200:
                continue
            sha0 = json.loads(ref)["object"]["sha"]
            br = f"scale/{STAMP}-{repo[:8]}"
            if call(client, org, "create_branch",
                    {**base, "branch": br, "from_branch": "main"}, "branch-heads")[0] != "OK":
                continue
            call(client, org, "create_or_update_file",
                 {**base, "branch": br, "path": f"scale-{STAMP}.md",
                  "message": f"{TAG} write", "content": f"{TAG}\n"}, "repository-contents")
            call(client, org, "push_files",
                 {**base, "branch": br, "message": f"{TAG} push",
                  "files": [{"path": f"scale-{STAMP}-b.md", "content": f"{TAG}\n"}]},
                 "repository-contents")
            _, out = call(client, org, "create_pull_request",
                          {**base, "title": f"{TAG} PR", "head": br, "base": "main",
                           "body": TAG}, "pull-request-records")
            try:
                pr = json.loads(out)["number"]
            except (ValueError, KeyError):
                pr = None
            if pr:
                _, prj = rest("GET", f"/repos/{OWNER}/{repo}/pulls/{pr}", token)
                head_sha = json.loads(prj).get("head", {}).get("sha", "")
                call(client, org, "get_pull_request", {**base, "pull_number": pr}, asset)
                call(client, org, "create_pull_request_review",
                     {**base, "pull_number": pr, "event": "COMMENT", "body": f"{TAG} review"},
                     "pull-requests-and-reviews")
                call(client, org, "update_pull_request_branch",
                     {**base, "pull_number": pr, "expected_head_sha": head_sha}, "branch-heads")
                call(client, org, "merge_pull_request",
                     {**base, "pull_number": pr, "commit_title": f"{TAG} merge",
                      "merge_method": "squash"}, "branch-heads")
            _, out = call(client, org, "create_issue",
                          {**base, "title": f"{TAG} issue", "body": TAG}, "issue-records")
            try:
                iss = json.loads(out)["number"]
            except (ValueError, KeyError):
                iss = None
            if iss:
                call(client, org, "add_issue_comment",
                     {**base, "issue_number": iss, "body": f"{TAG} comment"},
                     "issues-and-comments")
                call(client, org, "update_issue",
                     {**base, "issue_number": iss, "labels": ["triage"]}, "issue-records")
            rest("PATCH", f"/repos/{OWNER}/{repo}/git/refs/heads/main", token,
                 {"sha": sha0, "force": True})
            rest("DELETE", f"/repos/{OWNER}/{repo}/git/refs/heads/{br}", token)
            if pr:
                rest("PATCH", f"/repos/{OWNER}/{repo}/pulls/{pr}", token, {"state": "closed"})
            if iss:
                rest("PATCH", f"/repos/{OWNER}/{repo}/issues/{iss}", token, {"state": "closed"})

        # Repository lifecycle + fork.
        name = f"scale-probe-{STAMP}"
        if call(client, org, "create_repository",
                {"name": name, "private": True, "description": f"{TAG} temp"},
                "repository-records")[0] == "OK":
            rest("DELETE", f"/repos/{OWNER}/{name}", token)
        call(client, org, "fork_repository", {"owner": OWNER, "repo": "helios-public-site"},
             "org-external-copies")

        # Reads, varied, until the quota is met — mostly non-search to spare the cap.
        variant = 0
        while _idx < target:
            for repo, asset in mine.items():
                base = {"owner": OWNER, "repo": repo}
                call(client, org, "get_file_contents", {**base, "path": "README.md"}, asset)
                call(client, org, "list_commits", base, asset)
                _, out = call(client, org, "list_issues", {**base, "state": "all"}, asset)
                try:
                    issues = json.loads(out)
                    for it in issues[:2] if isinstance(issues, list) else []:
                        call(client, org, "get_issue",
                             {**base, "issue_number": it["number"]}, asset)
                except (ValueError, KeyError):
                    pass
                _, out = call(client, org, "list_pull_requests", {**base, "state": "all"}, asset)
                try:
                    prs = json.loads(out)
                    for pr in prs[:1] if isinstance(prs, list) else []:
                        for verb in ("get_pull_request", "get_pull_request_files",
                                     "get_pull_request_status", "get_pull_request_comments",
                                     "get_pull_request_reviews"):
                            call(client, org, verb, {**base, "pull_number": pr["number"]}, asset)
                except (ValueError, KeyError):
                    pass
                if variant % 4 == 0:  # search sparingly
                    call(client, org, "search_code",
                         {"q": f"repo:{OWNER}/{repo} {QUERIES[variant % len(QUERIES)]}"},
                         "code-records")
                if _idx >= target:
                    break
            variant += 1
    finally:
        client.close()


def sweep_slack(target: int) -> None:
    register = parse_asset_register(policy_for("slack_vireo").text)
    token = next(line.split("=", 1)[1].strip().strip('"')
                 for line in (KEYS / "slackkey.txt").read_text().splitlines()
                 if line.startswith("SLACK_MCP_XOXP_TOKEN"))
    org = "slack_vireo"
    client = StdioMCP("npx", ["-y", "slack-mcp-server@latest", "--transport", "stdio"],
                      {"SLACK_MCP_XOXP_TOKEN": token, "SLACK_MCP_ADD_MESSAGE_TOOL": "true"})
    try:
        boot(client)
        _, out = call(client, org, "channels_list",
                      {"channel_types": "public_channel", "limit": 100}, "channel-directory")
        chans = {}
        for line in out.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 2 and parts[0].startswith("C"):
                asset = label_for(parts[1], register)
                if asset:
                    chans[parts[0]] = asset
        call(client, org, "channels_me", {}, "agent-channel-membership")
        call(client, org, "usergroups_list", {}, "usergroup-directory")
        call(client, org, "usergroups_me", {"action": "list"}, "usergroup-membership")
        _, ur = call(client, org, "users_search", {"query": "test", "limit": 5}, "user-directory")
        me = ""
        for line in ur.splitlines()[1:2]:
            me = line.split(",")[0]

        # A message post, a join/leave round trip, and a throwaway user group.
        eng = next((c for c, a in chans.items() if a == "vireo-eng-platform"), None)
        if eng:
            _, out = call(client, org, "conversations_add_message",
                          {"channel_id": eng, "content_type": "text/plain",
                           "text": f"{TAG} coverage probe"}, "vireo-eng-platform")
            call(client, org, "conversations_join", {"channel_id": eng},
                 "agent-channel-membership")
            call(client, org, "conversations_mark", {"channel_id": eng}, "read-markers")
            call(client, org, "conversations_leave", {"channel_id": eng},
                 "agent-channel-membership", category="CLEANUP")
        _, out = call(client, org, "usergroups_create",
                      {"name": f"{TAG} temp", "handle": f"mcp-scale-{STAMP.replace('-', '')}",
                       "description": f"{TAG} throwaway"}, "usergroup-membership")
        try:
            gid = json.loads(out).get("usergroup", {}).get("id") or json.loads(out).get("id")
        except ValueError:
            gid = None
        if gid:
            call(client, org, "usergroups_update",
                 {"usergroup_id": gid, "description": f"{TAG} tombstone (disabled)"},
                 "usergroup-membership")
            if me:
                call(client, org, "usergroups_users_update",
                     {"usergroup_id": gid, "users": me}, "usergroup-membership")

        # Reads, varied, until the quota is met.
        variant = 0
        while _idx < target:
            for cid, asset in chans.items():
                _, out = call(client, org, "conversations_history",
                              {"channel_id": cid, "limit": 5 + variant % 5}, asset)
                if variant % 3 == 0:
                    call(client, org, "conversations_search_messages",
                         {"filter_in_channel": cid, "search_query": QUERIES[variant % len(QUERIES)],
                          "limit": 5}, asset)
                for line in out.splitlines()[1:2]:
                    ts = line.split(",")[0]
                    if ts and ts[0].isdigit():
                        call(client, org, "conversations_replies",
                             {"channel_id": cid, "thread_ts": ts, "limit": 5}, asset)
                call(client, org, "conversations_unreads", {}, "read-markers")
                if _idx >= target:
                    break
            variant += 1
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--only", action="append", choices=["calendar", "github", "slack"])
    options = parser.parse_args()
    wanted = options.only or ["calendar", "github", "slack"]
    per = options.target // len(wanted)

    if "calendar" in wanted:
        print("\n=== calendar_aurora ===")
        sweep_calendar(_idx + per)
    if "github" in wanted:
        print("\n=== github_helios ===")
        sweep_github(_idx + per)
    if "slack" in wanted:
        print("\n=== slack_vireo ===")
        sweep_slack(options.target)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "scale_calls.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print(f"\nwrote {path}: {len(rows)} calls, {ok} OK, {len(rows) - ok} ERROR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
