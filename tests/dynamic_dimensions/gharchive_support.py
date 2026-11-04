"""Synthetic GH Archive events for the extractor tests (``test_gharchive*.py``).

Every name here is invented: logins, organisations and repositories. Nothing is downloaded.
"""

from __future__ import annotations

import gzip
from datetime import UTC, date, datetime
from pathlib import Path

from mcp_security.behaviour.clock import DAY_S
from mcp_security.gateway.pseudonym import Pseudonymizer
from reports.experiments.dynamic_dimensions.heldout import gharchive_request_sizes as gs

KEY = "synthetic-test-key-0123456789abcdef"  # a test key, not a secret
OTHER_KEY = "another-synthetic-test-key-fedcba9876"
ORG_A, ORG_B, ORG_C = "acme-test", "globex-test", "initech-test"
PERSON_A, PERSON_B, BOT_A, AGENT_A = "dev-alpha", "dev-beta", "helper[bot]", "Agent-X[bot]"
AGENTS = frozenset({"agent-x[bot]"})
#: Names that must never appear in an extract or a summary.
IDENTITIES = (
    ORG_A,
    ORG_B,
    ORG_C,
    PERSON_A,
    PERSON_B,
    "helper",
    "Agent-X",
    "widgets",
    "gears",
    "sprockets",
)
SATURDAY = date(2025, 1, 4)
DAY = gs.day_number(SATURDAY)  # a Saturday
MONDAY = gs.day_number(date(2025, 1, 6))
HOUR = 3_600
MINUTE = 60


def pseudo(key: str = KEY) -> Pseudonymizer:
    """The keyed pseudonymizer of ``key``."""
    return gs.keyed_pseudonymizer(environ={gs.KEY_ENV: key})


def stamp(day: int, seconds: float) -> str:
    """ISO ``created_at`` for ``seconds`` after the start of UTC ``day``."""
    return datetime.fromtimestamp(day * DAY_S + seconds, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def event(
    kind: str,
    payload: dict,
    *,
    login: str = PERSON_A,
    org: str | None = ORG_A,
    repo: str = "widgets",
    day: int = DAY,
    seconds: float = HOUR,
) -> dict:
    """One GH Archive event in ``org``'s repository ``repo`` (a personal one without org)."""
    owner = org or login
    out = {
        "type": kind,
        "actor": {"login": login, "id": 1},
        "repo": {"name": f"{owner}/{repo}"},
        "payload": payload,
        "created_at": stamp(day, seconds),
    }
    return out | ({"org": {"login": org}} if org else {})


def comment(body: str, number: int = 7, **kw) -> dict:
    """An IssueCommentEvent (``add_issue_comment``)."""
    payload = {"action": "created", "issue": {"number": number}, "comment": {"body": body}}
    return event("IssueCommentEvent", payload, **kw)


def issue(title: str, body: str | None, action: str = "opened", **kw) -> dict:
    """An IssuesEvent (``create_issue`` when opened)."""
    return event("IssuesEvent", {"action": action, "issue": {"title": title, "body": body}}, **kw)


def review(body: str | None, state: str, number: int = 12, **kw) -> dict:
    """A PullRequestReviewEvent (``create_pull_request_review``)."""
    payload = {
        "action": "created",
        "review": {"body": body, "state": state},
        "pull_request": {"number": number},
    }
    return event("PullRequestReviewEvent", payload, **kw)


def push(**kw) -> dict:
    """A PushEvent: a write with no action."""
    return event("PushEvent", {"size": 1}, **kw)


def star(**kw) -> dict:
    """A WatchEvent: a call, not a write."""
    return event("WatchEvent", {"action": "started"}, **kw)


def write_gz(path: Path, lines: list[str]) -> Path:
    """Write JSON lines to a gzip file and return its path."""
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def assert_no_identities(text: str) -> None:
    """No invented login, organisation or repository name appears in ``text``."""
    for name in IDENTITIES:
        assert name not in text, name
