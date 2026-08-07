"""Consolidate the tool x asset probes into a coverage report.

Reads the probe result files, applies the corrected re-probes over the buggy
first pass, reclassifies the raw OK/ERROR verdicts into evidence grades, and
writes TOOL_ASSET_VERIFICATION.md plus the machine-readable matrix.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path("/home/ovadyat/MCP/reports/live_run/orgs_2026-07-29")
sys.path.insert(0, "/home/ovadyat/MCP/src")

# Grade, meaning, and whether it counts as "the register's claim is confirmed".
GRADES = {
    "VERIFIED": ("call ran against this asset and succeeded", True),
    "PROVEN-IN-PROVISIONING": ("this verb wrote this asset during the creation run", True),
    "REACHED-NO-OP": ("call addressed the asset; the API validated it and declined for "
                      "a state reason, not a reach reason", True),
    "SAME-VERB-VERIFIED": ("surface asset — the verb is confirmed on the concrete rows "
                           "it abstracts over", True),
    "NO-TOOL-CLAIMED": ("register claims no verb reaches this asset", True),
    "BLOCKED-BY-CREDENTIAL": ("token lacks the scope; homing unverified here", False),
    "BLOCKED-BY-PLAN": ("the workspace plan does not offer the feature", False),
    "BLOCKED-BY-SERVER-FLAG": ("server disables the verb behind an env flag", False),
    "NOT-EXECUTABLE-HERE": ("sandbox cannot produce the required precondition", False),
    "SKIPPED-BY-DESIGN": ("prohibited by the policy under test and irreversible", False),
}

# (section, asset, tool) -> (grade, note). Applied over the raw probe verdicts.
RECLASSIFY = {
    ("calendar_aurora", "aurora-crew-roster", "respond-to-event"): (
        "NOT-EXECUTABLE-HERE",
        "the account is the event organizer, and Google refuses a response from a "
        "non-attendee: 'You are not an attendee of this event'",
    ),
    ("calendar_aurora", "aurora-maintenance", "respond-to-event"): (
        "NOT-EXECUTABLE-HERE", "same: organizer, not attendee"),
    ("calendar_aurora", "aurora-team", "respond-to-event"): (
        "NOT-EXECUTABLE-HERE", "same: organizer, not attendee"),
    # Re-probed after the user token gained usergroups:read / usergroups:write /
    # groups:write and the server was launched with SLACK_MCP_MARK_TOOL=true.
    ("slack_vireo", "usergroup-membership", "usergroups_me"): (
        "VERIFIED", "returned the caller's group membership (empty on this workspace)"),
    ("slack_vireo", "usergroup-directory", "usergroups_list"): (
        "VERIFIED", "returned the group directory (empty on this workspace)"),
    ("slack_vireo", "usergroup-membership", "usergroups_create"): (
        "BLOCKED-BY-PLAN",
        "scopes are now present; Slack refuses with paid_teams_only — user groups "
        "are a paid-plan feature and this workspace is Free",
    ),
    ("slack_vireo", "usergroup-membership", "usergroups_update"): (
        "NOT-EXECUTABLE-HERE",
        "needs an existing usergroup_id, and none can exist on a Free workspace",
    ),
    ("slack_vireo", "usergroup-membership", "usergroups_users_update"): (
        "NOT-EXECUTABLE-HERE",
        "needs an existing usergroup_id, and none can exist on a Free workspace",
    ),
    ("slack_vireo", "read-markers", "conversations_mark"): (
        "VERIFIED",
        "ran once the server was launched with SLACK_MCP_MARK_TOOL=true; marked the "
        "channel read up to a real message ts",
    ),
    ("github_helios", "pull-request-records", "update_pull_request_branch"): (
        "REACHED-NO-OP",
        "GitHub validated the call against PR #1 and declined: 'There are no new "
        "commits on the base branch'",
    ),
    ("github_helios", "org-external-copies", "fork_repository"): (
        "NOT-EXECUTABLE-HERE",
        "GitHub cannot fork a repository into the account that already owns it; "
        "confirming this homing needs a second account or org",
    ),
}


def load() -> list[dict]:
    rows: dict[tuple, dict] = {}
    for name in ("calendar", "slack", "github"):
        for rec in json.loads((HERE / f"probe_results_{name}.json").read_text(encoding="utf-8")):
            rows[(rec["section"], rec["asset"], rec["tool"])] = rec
    # corrected re-probes win over the first pass
    for name, section in (("calendar", "calendar_aurora"), ("slack", "slack_vireo")):
        path = HERE / f"probe_results_{name}_fix.json"
        if not path.exists():
            continue
        for rec in json.loads(path.read_text(encoding="utf-8")):
            rows[(section, rec["asset"], rec["tool"])] = {**rec, "section": section}
    return list(rows.values())


def grade(rec: dict) -> tuple[str, str]:
    key = (rec["section"], rec["asset"], rec["tool"])
    if key in RECLASSIFY:
        return RECLASSIFY[key]
    verdict = rec["verdict"]
    if verdict == "OK":
        return "VERIFIED", ""
    if verdict == "SEE-ROW":
        return "SAME-VERB-VERIFIED", rec["evidence"]
    if verdict in GRADES:
        return verdict, rec["evidence"]
    return verdict, rec["evidence"]


def main() -> int:
    rows = [{**r, "grade": grade(r)[0], "note": grade(r)[1]} for r in load()]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tool_asset_matrix.json").write_text(
        json.dumps(sorted(rows, key=lambda r: (r["section"], r["asset"], r["tool"])), indent=2),
        encoding="utf-8",
    )
    per_section: dict[str, Counter] = {}
    for r in rows:
        per_section.setdefault(r["section"], Counter())[r["grade"]] += 1
    for section, counts in sorted(per_section.items()):
        confirmed = sum(n for g, n in counts.items() if GRADES.get(g, ("", False))[1])
        print(f"{section}: {sum(counts.values())} pairs, {confirmed} confirmed")
        for g, n in counts.most_common():
            print(f"    {g:24} {n}")
    print(f"\ntotal pairs: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
