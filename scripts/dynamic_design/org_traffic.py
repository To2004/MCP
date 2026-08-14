"""A realistic org's call mix for an MCP server, as personas rather than per-tool weights.

The corpora this replaces drew tools with ``rng.choice`` over a list, so every tool held an
equal share and no tool was ever rare. That silently disabled the likelihood factor: ``L``
asks whether a tool is unusual for a deployment, and under a uniform draw nothing is.

Real API traffic is not uniform. It is dominated by automation polling a handful of
read endpoints, with human activity an order of magnitude below that and administrative
operations episodic. Rather than hand-picking 26 tool probabilities — which would be an
invitation to tune the distribution until the scorer looked good — the shape here is
declared one level up, as *who is calling*:

    a persona has a share of the org's total call volume, and its own preferences over the
    tools its job actually uses

The tool distribution is the marginal that falls out. It is heavy-tailed because roles are:
CI runs constantly, an admin acts a few times a week. Nothing in this file is derived from
running the scorer, and the weights are fixed before any call is scored.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

#: Share of total call volume, by role. Automation dominates; admin work is episodic.
#: These are the only free parameters, and they are set from how often a role acts, not
#: from anything the risk layer produces.
GITHUB_VOLUME: dict[str, float] = {
    "ci_bot": 0.52,
    "developer": 0.26,
    "reviewer": 0.11,
    "triager": 0.07,
    "release_manager": 0.03,
    "admin": 0.01,
}

#: What each role calls, and how often within its own work.
GITHUB_TOOLS: dict[str, dict[str, float]] = {
    "ci_bot": {
        "get_pull_request_status": 0.30,
        "list_commits": 0.22,
        "get_file_contents": 0.20,
        "get_pull_request_files": 0.12,
        "list_pull_requests": 0.10,
        "get_pull_request": 0.06,
    },
    "developer": {
        "get_file_contents": 0.28,
        "search_code": 0.16,
        "list_commits": 0.12,
        "list_issues": 0.10,
        "get_issue": 0.08,
        "search_issues": 0.08,
        "create_branch": 0.05,
        "create_or_update_file": 0.05,
        "push_files": 0.03,
        "create_pull_request": 0.03,
        "search_repositories": 0.02,
    },
    "reviewer": {
        "get_pull_request": 0.22,
        "get_pull_request_files": 0.20,
        "get_pull_request_comments": 0.18,
        "get_pull_request_reviews": 0.15,
        "create_pull_request_review": 0.13,
        "add_issue_comment": 0.07,
        "update_pull_request_branch": 0.05,
    },
    "triager": {
        "list_issues": 0.30,
        "get_issue": 0.22,
        "search_issues": 0.18,
        "add_issue_comment": 0.14,
        "update_issue": 0.10,
        "create_issue": 0.06,
    },
    "release_manager": {
        "list_pull_requests": 0.25,
        "get_pull_request_status": 0.20,
        "merge_pull_request": 0.20,
        "list_commits": 0.20,
        "create_branch": 0.15,
    },
    "admin": {
        "search_users": 0.35,
        "create_repository": 0.30,
        "fork_repository": 0.20,
        "search_repositories": 0.15,
    },
}

#: Tools that create or change server-side state. The live driver routes these to a
#: scratch repository it owns; the synthetic generator has no such constraint.
GITHUB_WRITES: frozenset[str] = frozenset({
    "add_issue_comment", "create_branch", "create_issue", "create_or_update_file",
    "create_pull_request", "create_pull_request_review", "create_repository",
    "fork_repository", "merge_pull_request", "push_files", "update_issue",
    "update_pull_request_branch",
})

#: Page sizes as they actually arrive: mostly the API default, occasionally the maximum.
#: A uniform draw over the legal values — what the previous corpora did — makes every page
#: size equally ordinary and flattens the quartiles the runtime learns.
_PAGE_SIZES: tuple[tuple[int, float], ...] = (
    (30, 0.58), (100, 0.14), (50, 0.10), (10, 0.09), (5, 0.05), (1, 0.04),
)
_PAGE_NUMBERS: tuple[tuple[int, float], ...] = (
    (1, 0.79), (2, 0.11), (3, 0.05), (5, 0.03), (10, 0.02),
)
_ISSUE_STATES: tuple[tuple[str, float], ...] = (
    ("open", 0.72), ("all", 0.20), ("closed", 0.08),
)


@dataclass(frozen=True)
class Call:
    """One sampled call: which role made it, which tool, and with what arguments."""

    persona: str
    tool: str
    args: dict


def build_github_args(rng: random.Random, tool: str, state: dict) -> dict:
    """Concrete GitHub arguments, drawn from realistic value distributions.

    ``state`` supplies what only a live server can know — which repositories exist, which
    paths and issue numbers are real. The synthetic generator passes the same shape with
    recovered values, so both corpora share one argument distribution.
    """
    owner = state["owner"]
    repo = rng.choice(state["repos"])
    write_repo = state.get("write_repo") or repo
    size = _weighted(rng, _PAGE_SIZES)
    page = _weighted(rng, _PAGE_NUMBERS)
    paths = state.get("paths", {}).get(repo) or ["README.md"]
    issue = rng.choice(state.get("issues", {}).get(repo) or [1])
    pull = rng.choice(state.get("pulls", {}).get(repo) or [1])

    base = {"owner": owner, "repo": repo}
    match tool:
        case "get_file_contents":
            return base | {"path": rng.choice(paths)}
        case "list_commits":
            return base | {"perPage": size, "page": page}
        case "list_issues":
            return base | {"state": _weighted(rng, _ISSUE_STATES), "per_page": size, "page": page}
        case "list_pull_requests":
            return base | {"state": _weighted(rng, _ISSUE_STATES), "per_page": size, "page": page}
        case "get_issue":
            return base | {"issue_number": issue}
        case ("get_pull_request" | "get_pull_request_files" | "get_pull_request_comments"
              | "get_pull_request_reviews" | "get_pull_request_status"):
            return base | {"pull_number": pull}
        case "search_code":
            return {"q": f"repo:{owner}/{repo} {rng.choice(['def', 'import', 'class', 'TODO'])}",
                    "per_page": size, "page": page}
        case "search_issues":
            return {"q": f"repo:{owner}/{repo} is:issue "
                         f"{rng.choice(['is:open', 'is:closed', 'bug', 'label:enhancement'])}",
                    "per_page": size, "page": page}
        case "search_repositories":
            return {"query": rng.choice([f"user:{owner}", "language:python", "stars:>10000",
                                         "topic:mcp"]),
                    "perPage": size, "page": page}
        case "search_users":
            return {"q": rng.choice([owner, "location:israel", "language:go"]),
                    "per_page": size, "page": page}
        case "add_issue_comment":
            return {"owner": owner, "repo": write_repo, "issue_number": issue,
                    "body": rng.choice(["Looks good to me.", "Reproduced on main.",
                                        "Bumping this.", "Fixed by the linked PR."])}
        case "create_issue":
            return {"owner": owner, "repo": write_repo,
                    "title": rng.choice(["Flaky test on CI", "Update dependencies",
                                         "Docs are out of date", "Timeout under load"]),
                    "body": "Filed by the traffic generator."}
        case "update_issue":
            return {"owner": owner, "repo": write_repo, "issue_number": issue,
                    "state": rng.choice(["open", "closed"])}
        case "create_branch":
            return {"owner": owner, "repo": write_repo,
                    "branch": f"feature/{rng.randrange(10**6):06d}"}
        case "create_or_update_file":
            return {"owner": owner, "repo": write_repo,
                    "path": f"notes/{rng.randrange(10**6):06d}.md",
                    "content": "generated", "message": "chore: generated commit",
                    "branch": "main"}
        case "push_files":
            count = rng.choice([1, 1, 1, 2, 3, 8])
            return {"owner": owner, "repo": write_repo, "branch": "main",
                    "message": "chore: batch", "files": [
                        {"path": f"notes/{rng.randrange(10**6):06d}.md", "content": "generated"}
                        for _ in range(count)]}
        case "create_pull_request":
            return {"owner": owner, "repo": write_repo, "title": "Automated change",
                    "head": f"feature/{rng.randrange(10**6):06d}", "base": "main"}
        case "create_pull_request_review":
            return {"owner": owner, "repo": write_repo, "pull_number": pull,
                    "body": "Reviewed.", "event": rng.choice(["COMMENT", "APPROVE"])}
        case "merge_pull_request":
            return {"owner": owner, "repo": write_repo, "pull_number": pull,
                    "merge_method": rng.choice(["merge", "squash", "rebase"])}
        case "update_pull_request_branch":
            return {"owner": owner, "repo": write_repo, "pull_number": pull}
        case "create_repository":
            return {"name": f"scratch-{rng.randrange(10**6):06d}",
                    "private": True, "autoInit": True}
        case "fork_repository":
            return {"owner": owner, "repo": repo}
        case _:
            return base


#: Slack. A workspace's volume is dominated by assistants and bots reading history, with
#: people searching and posting an order of magnitude below that, and workspace
#: administration rare.
SLACK_VOLUME: dict[str, float] = {
    "assistant_bot": 0.44,
    "member": 0.31,
    "channel_manager": 0.14,
    "people_ops": 0.08,
    "workspace_admin": 0.03,
}

SLACK_TOOLS: dict[str, dict[str, float]] = {
    "assistant_bot": {
        "conversations_history": 0.38,
        "conversations_replies": 0.24,
        "conversations_unreads": 0.18,
        "channels_list": 0.12,
        "conversations_mark": 0.08,
    },
    "member": {
        "conversations_search_messages": 0.30,
        "conversations_history": 0.22,
        "channels_me": 0.14,
        "users_search": 0.12,
        "conversations_replies": 0.10,
        "conversations_add_message": 0.08,
        "channels_list": 0.04,
    },
    "channel_manager": {
        "channels_list": 0.34,
        "conversations_history": 0.22,
        "conversations_join": 0.16,
        "conversations_mark": 0.14,
        "conversations_leave": 0.09,
        "conversations_add_message": 0.05,
    },
    "people_ops": {
        "users_search": 0.34,
        "usergroups_list": 0.28,
        "usergroups_me": 0.18,
        "usergroups_users_update": 0.12,
        "channels_me": 0.08,
    },
    "workspace_admin": {
        "usergroups_list": 0.30,
        "usergroups_update": 0.25,
        "usergroups_create": 0.20,
        "usergroups_users_update": 0.15,
        "channels_list": 0.10,
    },
}

SLACK_WRITES: frozenset[str] = frozenset({
    "conversations_add_message", "conversations_join", "conversations_leave",
    "conversations_mark", "usergroups_create", "usergroups_update",
    "usergroups_users_update",
})

#: Slack's page limits, as they actually arrive. The API default dominates.
_SLACK_LIMITS: tuple[tuple[int, float], ...] = (
    (100, 0.52), (50, 0.16), (20, 0.13), (200, 0.09), (10, 0.06), (1, 0.04),
)
_CHANNEL_TYPES: tuple[tuple[str, float], ...] = (
    ("public_channel", 0.61), ("public_channel,private_channel", 0.18),
    ("im", 0.12), ("mpim", 0.05), ("private_channel", 0.04),
)


def build_slack_args(rng: random.Random, tool: str, state: dict) -> dict:
    """Concrete Slack arguments, drawn from realistic value distributions."""
    channel = rng.choice(state.get("channels") or ["C0000000000"])
    limit = _weighted(rng, _SLACK_LIMITS)
    types = _weighted(rng, _CHANNEL_TYPES)
    group = rng.choice(state.get("usergroups") or ["S0000000000"])

    match tool:
        case "conversations_history":
            return {"channel_id": channel, "limit": limit}
        case "conversations_replies":
            return {"channel_id": channel, "thread_ts": state.get("thread_ts", "0.0"),
                    "limit": limit}
        case "conversations_search_messages":
            return {"search_query": rng.choice(["the", "release", "incident", "a", "thanks"]),
                    "filter_in_channel": channel, "limit": limit}
        case "conversations_unreads":
            return {"channel_types": types,
                    "max_channels": _weighted(rng, _SLACK_LIMITS),
                    "max_messages_per_channel": rng.choice([10, 10, 10, 50, 1])}
        case "channels_list":
            return {"channel_types": types, "limit": limit}
        case "channels_me":
            return {"channel_types": types, "limit": limit}
        case "users_search":
            return {"query": rng.choice(["a", "tomer", "ops", "bot"]), "limit": limit}
        case "usergroups_list":
            return {"include_count": True, "include_disabled": False, "include_users": False}
        case "usergroups_me":
            return {"action": "list"}
        case "conversations_join" | "conversations_leave":
            return {"channel_id": channel}
        case "conversations_mark":
            return {"channel_id": channel, "ts": state.get("thread_ts", "0.0")}
        case "conversations_add_message":
            return {"channel_id": channel,
                    "text": rng.choice(["Ack.", "Deploying now.", "On it.", "Thanks!"])}
        case "usergroups_create":
            return {"name": f"group-{rng.randrange(10**6):06d}",
                    "handle": f"g{rng.randrange(10**6):06d}", "description": "generated"}
        case "usergroups_update":
            return {"usergroup_id": group, "description": "generated"}
        case "usergroups_users_update":
            return {"usergroup_id": group,
                    "users": rng.choice([["U1"], ["U1", "U2"], ["U1", "U2", "U3"]])}
        case _:
            return {}


#: Calendar. Scheduling automation reads availability constantly; people check their own
#: week; assistants do the bulk of the writing; account administration is rare.
CALENDAR_VOLUME: dict[str, float] = {
    "scheduling_bot": 0.45,
    "employee": 0.31,
    "exec_assistant": 0.14,
    "room_bot": 0.07,
    "workspace_admin": 0.03,
}

CALENDAR_TOOLS: dict[str, dict[str, float]] = {
    "scheduling_bot": {
        "list-events": 0.40,
        "get-freebusy": 0.30,
        "get-current-time": 0.20,
        "get-event": 0.10,
    },
    "employee": {
        "list-events": 0.34,
        "search-events": 0.24,
        "get-event": 0.16,
        "create-event": 0.10,
        "respond-to-event": 0.08,
        "update-event": 0.05,
        "list-calendars": 0.03,
    },
    "exec_assistant": {
        "search-events": 0.24,
        "list-events": 0.20,
        "create-event": 0.18,
        "update-event": 0.14,
        "get-freebusy": 0.10,
        "delete-event": 0.08,
        "create-events": 0.06,
    },
    "room_bot": {
        "get-freebusy": 0.52,
        "list-calendars": 0.28,
        "list-events": 0.20,
    },
    "workspace_admin": {
        "list-calendars": 0.40,
        "list-colors": 0.28,
        "manage-accounts": 0.20,
        "get-current-time": 0.12,
    },
}

CALENDAR_WRITES: frozenset[str] = frozenset({
    "create-event", "create-events", "delete-event", "update-event",
    "respond-to-event", "manage-accounts",
})

#: How far ahead a query looks. A week dominates; a year is a rare sweep.
_WINDOW_DAYS: tuple[tuple[int, float], ...] = (
    (7, 0.44), (1, 0.22), (30, 0.18), (14, 0.09), (90, 0.05), (365, 0.02),
)


def build_calendar_args(rng: random.Random, tool: str, state: dict) -> dict:
    """Concrete Calendar arguments, drawn from realistic value distributions."""
    calendars = state.get("calendars") or ["primary"]
    #: Most calls name one calendar; a sweep across several is uncommon.
    how_many = rng.choice([1, 1, 1, 1, 1, 1, 1, 2, 2, 3])
    picked = [rng.choice(calendars) for _ in range(min(how_many, len(calendars)))]
    days = _weighted(rng, _WINDOW_DAYS)
    start = state.get("now", "2026-08-14T00:00:00Z")
    end = state.get("horizon", {}).get(days, start)
    event = rng.choice(state.get("events") or ["evt0"])

    match tool:
        case "list-events":
            return {"calendarId": picked, "timeMin": start, "timeMax": end}
        case "search-events":
            return {"calendarId": picked[0],
                    "query": rng.choice(["standup", "1:1", "review", "a", "sync"]),
                    "timeMin": start, "timeMax": end}
        case "get-event":
            return {"calendarId": picked[0], "eventId": event}
        case "get-freebusy":
            return {"calendars": [{"id": c} for c in picked],
                    "timeMin": start, "timeMax": end}
        case "list-calendars" | "list-colors" | "get-current-time":
            return {}
        case "create-event":
            return {"calendarId": picked[0], "summary": "Generated meeting",
                    "start": start, "end": end, "sendUpdates": "none"}
        case "create-events":
            count = rng.choice([2, 2, 3, 5])
            return {"calendarId": picked[0], "sendUpdates": "none",
                    "events": [{"summary": f"Generated {i}", "start": start, "end": end}
                               for i in range(count)]}
        case "update-event":
            return {"calendarId": picked[0], "eventId": event, "summary": "Updated",
                    "sendUpdates": "none"}
        case "delete-event":
            return {"calendarId": picked[0], "eventId": event, "sendUpdates": "none"}
        case "respond-to-event":
            return {"calendarId": picked[0], "eventId": event,
                    "response": rng.choice(["accepted", "tentative", "declined"])}
        case "manage-accounts":
            return {"action": "list"}
        case _:
            return {}


@dataclass(frozen=True)
class Profile:
    """One server's traffic model: who calls it, what they call, and how to build args."""

    volume: dict[str, float]
    tools: dict[str, dict[str, float]]
    writes: frozenset[str]
    args: object          # Callable[[random.Random, str, dict], dict]


PROFILES: dict[str, Profile] = {
    "github": Profile(GITHUB_VOLUME, GITHUB_TOOLS, GITHUB_WRITES, build_github_args),
    "slack": Profile(SLACK_VOLUME, SLACK_TOOLS, SLACK_WRITES, build_slack_args),
    "calendar": Profile(CALENDAR_VOLUME, CALENDAR_TOOLS, CALENDAR_WRITES,
                        build_calendar_args),
}


def _weighted(rng: random.Random, options: dict[str, float] | tuple):
    """Draw one key in proportion to its weight."""
    pairs = tuple(options.items()) if isinstance(options, dict) else options
    total = sum(w for _, w in pairs)
    cut = rng.random() * total
    for key, weight in pairs:
        cut -= weight
        if cut <= 0:
            return key
    return pairs[-1][0]


def write_tools(server: str = "github") -> frozenset[str]:
    """Tools that create or change state on this server."""
    return PROFILES[server].writes


def tool_marginal(server: str = "github") -> dict[str, float]:
    """The overall tool distribution implied by one server's persona mix.

    Exposed so the shape can be inspected and reported without sampling it.
    """
    profile = PROFILES[server]
    marginal: dict[str, float] = {}
    for persona, volume in profile.volume.items():
        for tool, share in profile.tools[persona].items():
            marginal[tool] = marginal.get(tool, 0.0) + volume * share
    return dict(sorted(marginal.items(), key=lambda kv: -kv[1]))


def build_args(rng: random.Random, tool: str, state: dict, server: str = "github") -> dict:
    """Concrete arguments for one call on ``server``."""
    return PROFILES[server].args(rng, tool, state)


def sample_call(rng: random.Random, state: dict, server: str = "github") -> Call:
    """Draw one complete call: role, tool, and arguments."""
    profile = PROFILES[server]
    persona = str(_weighted(rng, profile.volume))
    tool = str(_weighted(rng, profile.tools[persona]))
    return Call(persona=persona, tool=tool, args=profile.args(rng, tool, state))
