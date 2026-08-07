"""My own reading of every asset and tool in the v5r corpus — for comparison.

The scan produces numbers from the organization's policy plus the tool catalog.
This module is a *second, independent* reading of the same 51 assets and 55 tools,
written by the assistant rather than derived from the policy, so the two can be
put side by side and the disagreements read off.

Nothing here feeds a scan. It is consumed only by
``scripts/explain_v5r_matrix.py`` to build the ``_EXPLAINED.md`` comparison
tables.

* ``ASSET_READING`` — what the asset is, and **what depends on it**. The second
  half is the part blast radius needs and the part an id alone never tells you.
* ``TOOL_READING`` — what one call does, and **who is different afterwards**.
* ``EXPECTED_IMPACT`` — the tier I would assign, so a divergence from the scan's
  number is visible rather than buried.

Where I have no basis for a reading the key is simply absent, and the report says
so rather than inventing one.
"""

from __future__ import annotations

# --- calendar_aurora (Aurora Airways, commercial aviation) -------------------

_AURORA_ASSETS = {
    "connected-account-config": (
        "Which Google accounts this server is bound to and with what OAuth scope. "
        "Every other tool reads through it, so changing it changes what the whole "
        "surface can reach — the control plane, not a data store."
    ),
    "contacts": (
        "One record per person reachable through attendee fields — effectively the "
        "airline's people directory. Depends on it: anyone whose name and address "
        "sit in it, which is everybody."
    ),
    "event-attendee-lists": (
        "Who is invited to an event. The people behind the entry: reading it "
        "discloses relationships, writing it changes who receives the invitation."
    ),
    "aurora-exec": (
        "Officer calendars. Titles and attendee lists disclose route decisions, "
        "fleet negotiations and departures without opening a body — metadata is the "
        "sensitive part here."
    ),
    "aurora-regulatory": (
        "Audit, certification and authority-liaison scheduling. What depends on it: "
        "the airline's ability to show a regulator it met a date."
    ),
    "aurora-crew-roster": (
        "Crew duty and rest scheduling. Legally bounded — a corrupted roster is a "
        "flight-safety and duty-time compliance problem, not an inconvenience."
    ),
    "aurora-maintenance": (
        "Maintenance windows and slot bookings. An aircraft out of its window is an "
        "airworthiness question, so the operations chain depends on these dates."
    ),
    "aurora-team": "Ordinary team scheduling for office staff. Little depends on any one entry.",
    "outbound-invite-email": (
        "Mail leaving the airline under its own identity when an event with external "
        "attendees is created or changed. Unrecallable, and it goes out as "
        "'Aurora Airways — Executive' with no human name to verify against."
    ),
    "event-records": "What a create/update/delete targets: any event on any calendar in scope.",
    "calendar-records": "Calendar-level attributes a read returns — names, timezone, colour. No event bodies.",
    "account-directory": "The list of linked accounts. A short list, but it names the identities the server holds.",
    "free-busy-availability": "Busy blocks with no titles or attendees — when someone is occupied, not why.",
    "calendar-directory": "The list of calendars. Reconnaissance: it maps where the events live, holds none.",
    "rsvp-state": "Accept/decline state on one invitation. Inert on this deployment — no tool can set it.",
    "holidays": "The published holiday calendar. Already public.",
    "color-catalog": "The static colour palette. Nothing depends on it in any sense.",
}

_AURORA_TOOLS = {
    "list-calendars": ("Returns the names of calendars the account can see. Nobody is affected; it maps the surface.", 2),
    "list-events": ("Returns entries on a calendar — titles and times, which on exec calendars is the sensitive part.", 2),
    "search-events": ("Free-text search across events, returning matching entries with their content.", 3),
    "get-event": ("Returns one event in full — body, attendees, location, conferencing detail.", 3),
    "list-colors": ("Returns the palette. Affects nothing.", 2),
    "create-event": ("Authors one new event with all its fields, and invites everyone on its attendee list.", 4),
    "create-events": ("The same, many at once, explicitly skipping conflict and duplicate detection.", 4),
    "update-event": ("Rewrites an existing event's fields, and can apply the change to a whole recurring series.", 4),
    "delete-event": ("Removes an event outright. No undo on this surface, and attendees lose the commitment silently.", 5),
    "get-freebusy": ("Returns busy blocks — availability without content.", 2),
    "get-current-time": ("Returns the clock. Touches no organizational asset at all.", 1),
    "respond-to-event": ("Sets an accept/decline state on an invitation — consumption state, not content. Inert here.", 2),
    "manage-accounts": ("Adds or removes the accounts the server is bound to, so it changes every other tool's reach.", 5),
}

# --- github_helios (Helios Grid, electricity transmission) -------------------

_HELIOS_ASSETS = {
    "helios-grid-infra-config": (
        "Infrastructure and deploy configuration for systems inside the CIP "
        "electronic security perimeter. A merge here reconfigures the perimeter, so "
        "everything behind it depends on this repository."
    ),
    "helios-scada-gateway": (
        "The protocol gateway between the control room and field RTUs — a BES cyber "
        "system. A release reaches the dispatch path, which is the grid itself."
    ),
    "helios-market-bidding-engine": (
        "Day-ahead and intraday bidding strategy and settlement code. The parameters "
        "*are* the trading position, so the code discloses the strategy."
    ),
    "helios-ot-runbooks": (
        "Switching procedures, patch windows and CIP evidence collection — BES Cyber "
        "System Information in prose. Useful to an attacker precisely because it is "
        "written for an operator."
    ),
    "helios-public-site": "The public website and network status pages. Already published; only defacement matters.",
    "repository-contents": "What a file read or write reaches: code bodies across every repository in scope.",
    "code-records": (
        "Code search results — snippets drawn from every private repository the "
        "token can see, in one response. This is the aggregation asset: it is "
        "strictly more than any single repository read."
    ),
    "branch-heads": "Where each branch points. Moving a pointer changes what deploys, so the estate depends on it.",
    "pull-requests-and-reviews": "The review gate itself, carrying unmerged code and the approvals that promote it.",
    "pull-request-records": "What a PR write creates, edits or merges.",
    "issues-and-comments": "Issue threads and their discussion — operational detail, occasionally credentials pasted in haste.",
    "issue-records": "What an issue write creates or edits.",
    "org-external-copies": (
        "Repositories and forks created outside the org boundary. BES Cyber System "
        "Information leaves the perimeter the moment one exists, and this deployment "
        "reaches it through `create_repository`, not `fork_repository`."
    ),
    "repository-records": "What a repository-level write creates.",
    "repository-catalog": "The list of repository names and visibility. No code, but it maps the production estate.",
    "branch-directory": "Branch names and refs, no contents.",
    "commit-list": "Commit messages and metadata, no diffs.",
    "issue-catalog": "Issue listings and search hit lists, no bodies.",
    "platform-user-directory": "Public GitHub account records. Already published by the platform.",
}

_HELIOS_TOOLS = {
    "create_or_update_file": ("Writes a file's content on a branch. On this deployment it reaches main directly — no branch protection intervened.", 4),
    "search_repositories": ("Returns repository names, descriptions and visibility — the estate map, not the code.", 2),
    "create_repository": ("Creates a repository. The live boundary-exit verb here: content can be placed outside the perimeter.", 4),
    "get_file_contents": ("Returns one file's body.", 3),
    "push_files": ("Writes several files in one commit, straight to a branch.", 4),
    "create_issue": ("Opens an issue with a title and body.", 4),
    "create_pull_request": ("Proposes a change. Proposal, not promotion — nothing runs yet.", 4),
    "fork_repository": ("Would copy a repository outside the org. Inert for self-owned repos on this deployment.", 4),
    "create_branch": ("Creates a new ref. Additive; nothing that deploys changes.", 4),
    "list_commits": ("Returns commit messages and metadata, no diffs.", 2),
    "list_issues": ("Returns issue titles and state, no bodies.", 2),
    "update_issue": ("Edits an existing issue's fields, including closing it — which can silence a real alert.", 4),
    "add_issue_comment": ("Appends one comment. The rest of the thread is untouched.", 3),
    "search_code": ("Returns matching snippets from every private repository the token can see, in one call.", 3),
    "search_issues": ("Returns matching issues — titles and hit lists.", 3),
    "search_users": ("Returns public platform account records.", 3),
    "get_issue": ("Returns one issue in full, body included.", 3),
    "get_pull_request": ("Returns one PR's metadata and description.", 3),
    "list_pull_requests": ("Returns PR titles and state.", 2),
    "create_pull_request_review": ("Adds a review — and an approval is what lets a change through the gate.", 4),
    "merge_pull_request": ("Promotes a change. This is the verb the policy prohibits unconditionally: `mergeable: null` means the agent cannot check before acting, and nothing here can be taken back.", 5),
    "get_pull_request_files": ("Returns the changed-file list, and the diffs with it.", 3),
    "get_pull_request_status": ("Returns check state — pass/fail metadata.", 2),
    "update_pull_request_branch": ("Rewrites the PR branch against its base, moving what would merge.", 4),
    "get_pull_request_comments": ("Returns review discussion.", 3),
    "get_pull_request_reviews": ("Returns review verdicts and their bodies.", 3),
}

# --- slack_vireo (Vireo Bio, biopharmaceutical R&D) --------------------------

_VIREO_ASSETS = {
    "vireo-unblinding": (
        "The channel where trial blind breaks are discussed. Disclosure does not "
        "leak data so much as destroy the trial's integrity — and it is flagged "
        "`self-sufficient` because what is said there is actionable on its own."
    ),
    "vireo-safety-pv": (
        "Pharmacovigilance and adverse-event traffic. Reportable to a regulator on a "
        "clock, so both the content and the timeline matter."
    ),
    "vireo-regulatory-fda": "Submission and authority-correspondence discussion. Position-disclosing.",
    "vireo-trial-ops": "Day-to-day trial operations — sites, enrolment, logistics.",
    "vireo-lab-informatics": "Lab systems and pipeline discussion; occasionally credentials pasted mid-incident.",
    "vireo-eng-platform": "Ordinary platform engineering traffic.",
    "vireo-announcements": "Broadcast channel; already seen by the whole workspace. Only spoofing matters.",
    "channel-messages": (
        "What a history read or search returns, inheriting the most sensitive "
        "channel in scope. The cross-channel aggregation asset."
    ),
    "usergroup-membership": (
        "Who belongs to a user group — the access-control list for the private "
        "channels. Inert on a Free workspace, which is why the live access-control "
        "surface reduces to exactly one thing: the agent's own membership."
    ),
    "agent-channel-membership": (
        "Which channels the agent has joined. THE live Restricted asset here: "
        "`conversations_join` succeeds on any channel with no invitation, so the "
        "agent can self-admit and read. The toggle is reversible; the history it "
        "saw while inside is not."
    ),
    "user-directory": "Workspace member records — names, emails, titles, one per person.",
    "channel-directory": "The list of channels. Private channel names alone reveal what the company is doing.",
    "usergroup-directory": "The list of user groups.",
    "read-markers": "Per-conversation seen/unseen cursors. Says nothing about content.",
    "message-reactions": "Emoji state on messages; a reaction reads as acknowledgement.",
}

_VIREO_TOOLS = {
    "channels_list": ("Returns channel names and topics — no messages, but the names are disclosing here.", 2),
    "channels_me": ("Returns which channels the agent is in. Reads its own access state.", 2),
    "conversations_add_message": ("Posts one message into a channel. Bounded: the rest of the history is untouched, and it cannot be retracted through this surface.", 3),
    "conversations_history": ("Returns a channel's message history — the substance, in bulk.", 3),
    "conversations_join": ("Adds the agent to a channel with no invitation required, which grants read access to everything already in it. The gate belongs on this verb.", 4),
    "conversations_leave": ("Removes the agent from a channel. Reversible — leave and rejoin both work — and it discloses nothing new. The weakest of the membership verbs, not the strongest.", 4),
    "conversations_mark": ("Sets a read cursor. Consumption state only.", 2),
    "conversations_replies": ("Returns one thread's messages.", 3),
    "conversations_search_messages": ("Searches messages across the channels the agent can see, returning content.", 3),
    "conversations_unreads": ("Returns unread counts and cursors.", 2),
    "usergroups_create": ("Creates a user group. Inert on a Free workspace.", 4),
    "usergroups_list": ("Returns group names and handles.", 2),
    "usergroups_me": ("Returns the groups the agent belongs to.", 2),
    "usergroups_update": ("Edits one group field. Inert on a Free workspace.", 3),
    "usergroups_users_update": ("Replaces a group's member list, which changes who can read the private channels. Inert on a Free workspace.", 4),
    "users_search": ("Returns member directory records — names, emails, titles.", 3),
}

ASSET_READING: dict[str, str] = {**_AURORA_ASSETS, **_HELIOS_ASSETS, **_VIREO_ASSETS}
TOOL_READING: dict[str, str] = {
    name: reading for group in (_AURORA_TOOLS, _HELIOS_TOOLS, _VIREO_TOOLS)
    for name, (reading, _) in group.items()
}
EXPECTED_IMPACT: dict[str, int] = {
    name: tier for group in (_AURORA_TOOLS, _HELIOS_TOOLS, _VIREO_TOOLS)
    for name, (_, tier) in group.items()
}

__all__ = ["ASSET_READING", "EXPECTED_IMPACT", "TOOL_READING"]
