"""Plain words for numbers, times, sizes, tools, apps and networks on the study's cards.

Counts are rounded the way people say them, sizes are pages of text (one fixed rule, 1 page =
3 KB, applied to the shown number, the same way in "usual" and "today"; no KB on the page),
hours are clock times ("9 am-5 pm"), and tools, apps and networks get neutral names a
non-technical reader knows ("read a file", "home", "its usual app"). No brand names: a
participant's view of one product must never colour the answer. Place words are short (office,
home, old secure link, the cloud), so the connection line stays short on a phone. A "project" is a repository, a
"task" an issue and a "change request" a pull request.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

SIM_DIR = Path(__file__).resolve().parent.parent
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from normal_org_world import (  # noqa: E402
    CARRIER_POOL,
    CLOUD_POOL,
    HOME_POOL,
    OFFICE,
    VPN_NEW,
    VPN_OLD,
)

LOW_PERCENTILE, HIGH_PERCENTILE = 10, 90
CLOSE_RANGE = 0.15  # a range this narrow (share of its top) reads as "about X"
MOST_DAYS, SOME_DAYS, EVERY_DAY = 0.75, 0.25, 0.98
#: one page of text; every size on a card is this many bytes per page, rounded like a count
PAGE_BYTES = 3_000
LESS_THAN_A_PAGE = "less than a page"
NEVER = "0 (never)"
MAX_LISTED = 3  # names listed before "and N more"
HOURS_PER_DAY = 24
NOON = 12
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
#: tool -> plain words; "project" is a repository, "task" an issue, "change request" a PR
TOOL_WORDS: dict[str, str] = {
    "create_or_update_file": "change a file",
    "search_repositories": "search for projects",
    "create_repository": "create a project",
    "get_file_contents": "read a file",
    "push_files": "add several files at once",
    "create_issue": "open a task",
    "create_pull_request": "open a change request",
    "fork_repository": "copy a project",
    "create_branch": "start a side copy to work on",
    "list_commits": "look at recent changes",
    "list_issues": "list tasks",
    "update_issue": "update a task",
    "add_issue_comment": "comment on a task",
    "search_code": "search across all the code",
    "search_issues": "search tasks",
    "search_users": "search for people",
    "get_issue": "read a task",
    "get_pull_request": "read a change request",
    "list_pull_requests": "list change requests",
    "create_pull_request_review": "review a change request",
    "merge_pull_request": "approve and merge a change request",
    "get_pull_request_files": "list files in a change request",
    "get_pull_request_status": "check whether a change request passed its checks",
    "update_pull_request_branch": "bring a change request up to date",
    "get_pull_request_comments": "read change request comments",
    "get_pull_request_reviews": "read change request reviews",
    "list_tags": "list version labels",
    "get_workflow_runs": "look at the automatic checks",
    "create_release": "publish a new version",
    "rerun_workflow": "run the automatic checks again",
}
#: client program family -> what kind of program it is (no brand names on the cards)
APP, BOT_PROGRAM, OWN_PROGRAM = "app", "bot program", "own program"
APP_KINDS: dict[str, str] = {
    "claude-code": APP,
    "cursor": APP,
    "vscode-copilot": APP,
    "claude-desktop": APP,
    "openai-agents": BOT_PROGRAM,
    "langchain-mcp-adapters": BOT_PROGRAM,
    "mcp": BOT_PROGRAM,
    "python-requests": OWN_PROGRAM,
}
#: (kind, today's use) -> words; "usual" is for a program it uses as always
APP_TODAY: dict[tuple[str, str], str] = {
    (APP, "usual"): "its usual app",
    (APP, "usual many"): "its usual apps",
    (APP, "new"): "a different app",
    (APP, "rare"): "an app it rarely uses",
    (BOT_PROGRAM, "usual"): "its usual bot program",
    (BOT_PROGRAM, "usual many"): "its usual bot programs",
    (BOT_PROGRAM, "new"): "a different bot program",
    (BOT_PROGRAM, "rare"): "a bot program it rarely uses",
    (OWN_PROGRAM, "usual"): "its own small program",
    (OWN_PROGRAM, "usual many"): "its own small programs",
    (OWN_PROGRAM, "new"): "its own small program instead of an app",
    (OWN_PROGRAM, "rare"): "its own small program instead of an app",
}
INTERNAL_FIRST_OCTET = 10
#: short place words: the connection line must stay short on a phone
OFFICE_WORDS, HOME_WORDS = "office", "home"
OLD_LINK, NEW_LINK = "old secure link", "new secure link"
PHONE_WORDS, CLOUD_WORDS = "a phone network", "the cloud"
COMPANY_WORDS, OUTSIDE_WORDS = "company computers", "an outside network"
#: a place it knows, but a network of it it never used
ANOTHER_PLACE: dict[str, str] = {
    OFFICE_WORDS: "another office network",
    OLD_LINK: "another secure-link address",
    NEW_LINK: "another secure-link address",
    HOME_WORDS: "a different home line",
    PHONE_WORDS: "a different phone network",
    CLOUD_WORDS: "a new cloud address",
    COMPANY_WORDS: "other company computers",
    OUTSIDE_WORDS: "another outside network",
}


def round_plain(value: float) -> int:
    """Round a count the way people say it: 7, 35, 120, 1,400."""
    if value < 20:
        return int(round(value))
    if value < 100:
        return int(5 * round(value / 5))
    if value < 1000:
        return int(10 * round(value / 10))
    return int(100 * round(value / 100))


def ranked(counts: Counter, n: int | None = None) -> list[tuple[object, int]]:
    """The ``n`` most common values, ties by name (``Counter.most_common`` ties by insertion
    order, which follows set order)."""
    items = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return items if n is None else items[:n]


def number(value: int) -> str:
    """A count with a thousands separator."""
    return f"{value:,}"


def spread(values: list[float]) -> tuple[float, float]:
    """The 10th and 90th percentiles."""
    low, high = np.percentile(values, [LOW_PERCENTILE, HIGH_PERCENTILE])
    return float(low), float(high)


def plain_range(values: list[float], never: str = NEVER) -> str:
    """``about X`` or ``X-Y`` over its usual days; ``never`` if always 0."""
    if not values or max(values) == 0:
        return never
    low, high = spread(values)
    low_r, high_r = round_plain(low), round_plain(high)
    middle = round_plain((low + high) / 2)
    if high_r - low_r <= max(1, CLOSE_RANGE * high_r) and middle > 0:
        return f"about {number(middle)}"
    return f"{number(low_r)}-{number(high_r)}"


def pages(size_bytes: float) -> int:
    """A size as whole pages of text (``PAGE_BYTES`` each), rounded like a count; 0 is less
    than half a page."""
    return round_plain(size_bytes / PAGE_BYTES)


def pages_text(n: int) -> str:
    """``1 page``, ``12 pages``."""
    return "1 page" if n == 1 else f"{number(n)} pages"


def size_today(size_bytes: int) -> str:
    """``about 3 pages`` or ``less than a page``."""
    n = pages(size_bytes)
    return LESS_THAN_A_PAGE if n == 0 else f"about {pages_text(n)}"


def size_usual(sizes: list[int]) -> str:
    """The range of its daily biggest upload in pages: ``2-10 pages``, ``up to 10 pages``."""
    low, high = (pages(v) for v in spread(sizes))
    if high == 0:
        return LESS_THAN_A_PAGE
    if low == high:
        return f"about {pages_text(high)}"
    if low == 0:
        return f"up to {pages_text(high)}"
    return f"{number(low)}-{number(high)} pages"


def clock(hour: int) -> str:
    """0 -> midnight, 12 -> noon, 9 -> 9 am, 17 -> 5 pm."""
    hour %= HOURS_PER_DAY
    if hour == 0:
        return "midnight"
    if hour == NOON:
        return "noon"
    return f"{hour} am" if hour < NOON else f"{hour - NOON} pm"


def hour_spans(hours: set[int]) -> list[tuple[int, int]]:
    """Active hours as (start, end) clock spans; a span may run past midnight."""
    if len(hours) >= HOURS_PER_DAY:
        return [(0, HOURS_PER_DAY)]
    spans: list[list[int]] = []
    for h in sorted(hours):
        if spans and h == spans[-1][1]:
            spans[-1][1] = h + 1
        else:
            spans.append([h, h + 1])
    if len(spans) > 1 and spans[0][0] == 0 and spans[-1][1] == HOURS_PER_DAY:
        last = spans.pop()
        spans[0] = [last[0], HOURS_PER_DAY + spans[0][1]]
    return sorted((start, end) for start, end in spans)


def span_text(start: int, end: int) -> str:
    """``9 am-5 pm``, ``2-3 am`` (one "am" or "pm" when both ends share it)."""
    first, last = clock(start), clock(end)
    start_h, end_h = start % HOURS_PER_DAY, end % HOURS_PER_DAY
    named = {0, NOON}  # midnight and noon have no am/pm to share
    same_half = start_h not in named and end_h not in named
    if same_half and (start_h < NOON) == (end_h < NOON) and start_h < end_h:
        first = first.rsplit(" ", 1)[0]
    return f"{first}-{last}"


def hours_text(hours: set[int]) -> str:
    """Today's active hours: ``9 am-5 pm``, ``2-3 am and 9 am-6 pm``, ``around the clock``."""
    if not hours:
        return "no actions"
    spans = hour_spans(hours)
    if spans == [(0, HOURS_PER_DAY)]:
        return "around the clock"
    parts = [span_text(start, end) for start, end in spans]
    if len(parts) > MAX_LISTED:
        return f"on and off, in {len(hours)} of the {HOURS_PER_DAY} hours"
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def names_text(names: list[str]) -> str:
    """``a, b and c``; past three, ``a, b, c and 2 more``."""
    if len(names) > MAX_LISTED:
        return ", ".join(names[:MAX_LISTED]) + f" and {len(names) - MAX_LISTED} more"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def frequency(share: float) -> str:
    """Share of its days -> every day / most days / some days / rare."""
    if share >= EVERY_DAY:
        return "every day"
    if share >= MOST_DAYS:
        return "most days"
    if share >= SOME_DAYS:
        return "some days"
    return "rare"


def network_place(network: str) -> str:
    """A /16 in plain words: office, home, the cloud..."""
    first, second = (int(part) for part in network.split("/")[0].split(".")[:2])
    prefix = (first, second)
    if prefix == OFFICE:
        return OFFICE_WORDS
    if prefix == VPN_OLD:
        return OLD_LINK
    if prefix == VPN_NEW:
        return NEW_LINK
    if prefix in HOME_POOL:
        return HOME_WORDS
    if prefix in CARRIER_POOL:
        return PHONE_WORDS
    if prefix in CLOUD_POOL:
        return CLOUD_WORDS
    if first == INTERNAL_FIRST_OCTET:
        return COMPANY_WORDS
    return OUTSIDE_WORDS


def app_kind(app: str) -> str:
    """What kind of program a client family is: an app, a bot program or its own program."""
    return APP_KINDS.get(app, APP)


def program_count(kind: str, n: int) -> str:
    """``1 app``, ``2 apps``, ``1 bot program``, ``its own small program``."""
    if kind == OWN_PROGRAM:
        return "its own small program" if n == 1 else f"{n} small programs of its own"
    return f"{n} {kind}" if n == 1 else f"{n} {kind}s"


def qualifier(n: int, word: str) -> str:
    """``(new to it)``, ``(both new to it)``, ``(all new to it)``."""
    if n == 1:
        return f"({word})"
    return f"(both {word})" if n == 2 else f"(all {word})"


def tool_name(tool: str) -> str:
    """A tool in plain words."""
    return TOOL_WORDS.get(tool, tool.replace("_", " "))


def unique(names: list[str]) -> list[str]:
    """Names in their first order, each once."""
    return list(dict.fromkeys(names))
