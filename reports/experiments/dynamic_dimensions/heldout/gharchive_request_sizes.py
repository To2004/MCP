"""EV-26, the real-data ladder's first step: GitHub request sizes from GH Archive hourly files.

Every number this module prints is "real public activity, not MCP traffic" (:data:`LABEL`).

**Mapping** (Part A EV-26; the GitHub MCP server's tool names, as ``normal_org_world.TOOLS``):

==========================  =========  ===========================  ==============================
GH Archive event            action     MCP tool                     arguments rendered
==========================  =========  ===========================  ==============================
IssuesEvent                 opened     create_issue                 owner, repo, title, body
IssueCommentEvent           created    add_issue_comment            owner, repo, issue_number, body
PullRequestEvent            opened     create_pull_request          owner, repo, title, body, head,
                                                                    base
PullRequestReviewEvent      created    create_pull_request_review   owner, repo, pullNumber, body,
                                                                    event
==========================  =========  ===========================  ==============================

Each mapped event is rendered as the ``tools/call`` request an agent would send and measured
twice:

- ``arg_bytes``, as v5 logs it (ARG-1: compact ``params.arguments``,
  :func:`protocol_era.argument_bytes`). It does not depend on the protocol era.
- ``message_bytes``, as v1-v4 log it (``gateway.message_bytes``: the JSON-RPC message
  re-serialised with Python's default separators, ``wire_log._bytes``), rendered as a
  **legacy-era** request, with no ``params._meta``. Under MCP 2026-07-28 every request also
  carries ``_meta`` (``io.modelcontextprotocol/protocolVersion``, ``clientCapabilities`` and
  ``clientInfo``), so v4's message bytes of modern traffic are larger by that envelope. The v4
  rates here are unaffected, as learning and evaluation share one rendering, but a size bank of
  message bytes (``--bank-measure message_bytes``) fits legacy-era worlds only.

A ``null`` body is left out, as a client leaves out an unset optional argument. An event whose
payload the archive trimmed (no title and no body) counts as text-missing, never as size 0.

**Caller and day** (spec 2.1, 6.1 and 8 D5). The caller is the GitHub account
(:data:`CALLER_KEY`, :data:`CALLER_NOTE`). For ``[bot]`` and coding-agent accounts that is the
per-agent key, v5's default; a person's account is the analog of the opt-in
``baseline_key = "user"``. No user id is assumed anywhere. An extract keeps each actor's UTC day
in two parts, 00:00-04:00 and 04:00-24:00 (:data:`EARLY`, :data:`LATE`; the split is
``clock.DAY_START_HOUR``), so the days of either convention are rebuilt from one extract by
merging parts (:func:`actor_days`):

- :data:`V4_DAYS`: the UTC day, v1-v4's agent-day key (``int(ts // DAY_S)``);
- :data:`V5_DAYS`: B9's day in the route zone UTC, the fallback for a caller whose zone is
  unknown, which rolls over at 04:00 (``policy.learning_day``; spec 6.1's agent-day key, R2-9).
  A v5 day spans two UTC days, so the first and the last day of the extracted range, and the
  days beside a missing one, are incomplete and dropped.

**Limits and rates.** The rule is ``size > limit`` (``engine.py`` ``_rules``). A route is an
organisation and learns its own limits on days ``[learn_from, learn_from + LEARN_DAYS)``
(``pooled``: one route for every organisation). Its realised rate is ``#{agent-days with some
call over its limit} / #{agent-days with a mapped call}`` on the days after learning.

- v4 (Part A EV-26, :func:`learn_v4_limits`): ``policy.derive_policy``'s procedure on message
  bytes over v4 days. Per tool, the :data:`QUANTILE` (99.5%) nearest-rank quantile of the
  agent-days' largest request, rounded up to a whole KB, for a tool with at least
  :data:`MIN_TOOL_DAYS` agent-days; every other tool uses the same quantile over the
  agent-days' largest request of any tool.
- v5 (RF1, the spec's Hyp5, :func:`learn_v5_limits`): ``policy.request_lines`` on argument
  bytes over v5 agent-days, the line ``derive_policy`` learns with a v5 base. A route with fewer
  than ``policy.MIN_LINE_DAYS`` agent-days left once its top identity is out learns no line. It
  is reported as not learned and never scored against the written default.

**Privacy** (spec 6.9, PS10). Logins, organisation and repository names are replaced at
extraction by keyed HMAC-SHA256 pseudonyms (:func:`keyed_pseudonymizer`, key from
:data:`KEY_ENV`). Extraction refuses to run without a key, because an unkeyed hash of a login is
undone by hashing candidates. The key is made once per run and deleted when the run's extracts,
the EV-14 bank's included, are done; the pseudonyms then link to nothing. Every file a key
wrote carries its :func:`key_check`, so a selection, an extract or a merge made under another
key fails loudly instead of matching nothing. Extracts hold per-actor maxima of day parts under
pseudonyms: no event, text, login, repository name or GitHub id. They stay on the cluster.
:func:`summarise` publishes aggregates only: :func:`size_quantiles` suppresses a cell under
:data:`MIN_PUBLISH_CALLS` calls, and a route's limits, a rate cell or a class total from fewer
than :data:`MIN_PUBLISH_ACTORS` distinct actors is suppressed too. Downloading is a separate
step (``scripts/dynamic_design/gharchive_array.sbatch``); this module only reads local files.

Stages, each a subcommand (paths are local files; ``.gz`` is read as gzip)::

    python -m reports.experiments.dynamic_dimensions.heldout.gharchive_request_sizes \\
        orgs --out orgs/2024-12-01.json.gz HOURLY.json.gz ...       # people per organisation
        select-orgs --out selection.json orgs/*.json.gz              # top 20 + 20 at random
        extract --day 2024-12-01 --orgs selection.json --out sizes/2024-12-01.json.gz HOURLY ...
        summarise --out sizes_summary.json [--bank bank.json] sizes/*.json.gz

The shared GH Archive reader (:func:`iter_events`, :func:`actor_class`, the pseudonyms and their
key check, the organisation selection, the day parts and conventions) also serves
``gharchive_actor_cadence.py`` (X2).
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import random
import sys
from bisect import bisect_right
from collections import Counter, defaultdict
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import TextIO

from mcp_security.behaviour import policy
from mcp_security.behaviour.clock import DAY_S, DAY_START_HOUR, DEFAULT_ZONE, HOUR_S
from mcp_security.behaviour.engine import (
    ACCEPTED,
    CALL_METHOD,
    V4,
    V5,
    WRITE,
    BehaviourConfig,
    Message,
)
from mcp_security.behaviour.policy import KB, MIN_TOOL_DAYS, QUANTILE
from mcp_security.gateway.protocol_era import argument_bytes
from mcp_security.gateway.pseudonym import Pseudonymizer

LABEL = "real public activity, not MCP traffic"
#: Spec 8 D5: the caller key of every extract, and what it stands for under v5.
CALLER_KEY = "github-account"
CALLER_NOTE = (
    "One history per GitHub account. For [bot] and coding-agent accounts that is the per-agent "
    "key, v5's default (spec 2.1): the per-agent evidence. A person's account merges every agent "
    "and client the person uses, the analog of the opt-in baseline_key = 'user': its history is "
    "longer and denser than a per-agent key's, so its records are rarer (biased low)."
)
#: Part A EV-26: the window ends before GitHub's 2025-09-08 brownout; from 2025-10-07 on,
#: pull-request events carry no title or body.
WINDOW_START = date(2024, 12, 1)
WINDOW_END = date(2025, 8, 27)
EPOCH = date(1970, 1, 1)  # day number 0
LEARN_DAYS = 30  # limits are learned on days 0-29 of the run, rates measured after
KEY_ENV = "GHARCHIVE_PSEUDONYM_KEY"
MIN_KEY_CHARS = 32  # e.g. ``openssl rand -hex 32`` gives 64
ACTOR_ROLE, ORG_ROLE, REPO_ROLE = "actor", "org", "repo"  # pseudonym domains
KEY_CHECK_ROLE, KEY_CHECK_TEXT = "check", "gharchive-key-check"  # see key_check

PERSON, BOT, AGENT = "person", "bot", "agent"
ACTOR_CLASSES = (PERSON, BOT, AGENT)
BOT_SUFFIX = "[bot]"
COMMENT_PREFIX = "#"
#: Coding-agent accounts, matched without case. UNVERIFIED: these names are not checked against
#: the archive; replace them with ``--agent-logins`` (one login per line).
AGENT_LOGINS = frozenset(
    {
        "copilot",
        "copilot-swe-agent[bot]",
        "devin-ai-integration[bot]",
        "claude[bot]",
        "cursor[bot]",
        "chatgpt-codex-connector[bot]",
        "google-labs-jules[bot]",
    }
)

CREATE_ISSUE = "create_issue"
ADD_ISSUE_COMMENT = "add_issue_comment"
CREATE_PULL_REQUEST = "create_pull_request"
CREATE_PULL_REQUEST_REVIEW = "create_pull_request_review"
#: (event type, action) -> MCP tool.
TOOL_EVENTS: dict[tuple[str, str], str] = {
    ("IssuesEvent", "opened"): CREATE_ISSUE,
    ("IssueCommentEvent", "created"): ADD_ISSUE_COMMENT,
    ("PullRequestEvent", "opened"): CREATE_PULL_REQUEST,
    ("PullRequestReviewEvent", "created"): CREATE_PULL_REQUEST_REVIEW,
}
TOOLS = tuple(TOOL_EVENTS.values())
#: A review's state -> the ``event`` argument of create_pull_request_review.
REVIEW_EVENTS = {"approved": "APPROVE", "changes_requested": "REQUEST_CHANGES"}
DEFAULT_REVIEW_EVENT = "COMMENT"
JSONRPC_VERSION = "2.0"
REQUEST_ID = 1  # a fixed id, so the envelope is the same for every call of a tool

ARG_BYTES, MESSAGE_BYTES = "arg_bytes", "message_bytes"
MEASURES = (ARG_BYTES, MESSAGE_BYTES)
MEASURE_NOTES = {
    ARG_BYTES: "bytes of params.arguments (ARG-1): the same in both protocol eras",
    MESSAGE_BYTES: "whole legacy-era message, no params._meta: fits legacy-era worlds only",
}
QUANTILES = (0.5, 0.9, 0.99, 0.995, 0.999)
MIN_PUBLISH_CALLS = 20  # a published size cell holds at least this many calls
MIN_PUBLISH_ACTORS = 10  # a published route, rate or cadence cell describes this many actors
ALL_CLASSES = "all"
POOLED = "(pooled)"  # the route name when every organisation learns one set of limits

#: Day parts: an extract keeps 00:00-04:00 and 04:00-24:00 UTC of each actor's day apart.
EARLY, LATE = 0, 1
PARTS = (EARLY, LATE)
SPLIT_S = DAY_START_HOUR * HOUR_S  # 04:00, v5's rollover (clock.DAY_START_HOUR)
#: Day conventions, named after the designs that key agent-days so (see the module docstring).
V4_DAYS, V5_DAYS = V4, V5
DAY_CONVENTIONS = (V4_DAYS, V5_DAYS)
DAY_NOTES = {
    V4_DAYS: "UTC days, v1-v4's agent-day key",
    V5_DAYS: "v5 days: route zone UTC (B9's fallback for an unknown zone), 04:00 rollover",
}
#: A route's limits are a design's: its measure and its day convention.
DESIGN_MEASURES = {V4: MESSAGE_BYTES, V5: ARG_BYTES}
DESIGN_DAYS = {V4: V4_DAYS, V5: V5_DAYS}
PROCEDURES = {
    V4: (
        "v4 derive_policy (Part A EV-26): message bytes over v4 days; per tool with at least "
        "50 agent-days the q0.995 nearest rank of its agent-days' largest request, else the same "
        "over every tool's; rounded up to a whole KB"
    ),
    V5: (
        "v5 RF1 (Hyp5): policy.request_lines on argument bytes over v5 agent-days (k r_t, the "
        "top identity left out); a route under policy.MIN_LINE_DAYS agent-days learns no line"
    ),
}

#: Part A EV-26: the top 20 organisations by distinct people, plus 20 at random with 20-200.
TOP_ORGS = 20
RANDOM_ORGS = 20
MIN_ORG_ACTORS = 20
MAX_ORG_ACTORS = 200
SELECTION_SEED = 26
#: :func:`policy_messages` puts an agent-day at noon of its day number, which lies inside the
#: day under both conventions.
NOON_S = DAY_S / 2
UTC_ZONE = DEFAULT_ZONE

SCHEMA_ORGS = "gharchive-org-people/2"
SCHEMA_SELECTION = "gharchive-org-selection/2"
SCHEMA_SIZES = "gharchive-request-sizes/2"
SCHEMA_SUMMARY = "gharchive-request-sizes-summary/2"
SCHEMA_BANK = "gharchive-size-bank/1"
GZIP_SUFFIX = ".gz"
STDIN_PATH = "-"


class PseudonymKeyError(RuntimeError):
    """The pseudonym key is missing or too short, so extraction refuses to run (PS10)."""


class SelectionKeyError(ValueError):
    """A file was made under another pseudonym key than this run's: its pseudonyms would
    match nothing (an organisation selection kept nothing, an exclusion excluded nothing)."""


# ── reading and pseudonyms (shared with gharchive_actor_cadence.py) ────────────────────────


def keyed_pseudonymizer(
    env_var: str = KEY_ENV, environ: Mapping[str, str] | None = None
) -> Pseudonymizer:
    """A keyed pseudonymizer from ``env_var``; :class:`PseudonymKeyError` when the variable
    is unset or shorter than :data:`MIN_KEY_CHARS`. The key is never written anywhere."""
    value = (os.environ if environ is None else environ).get(env_var, "")
    if len(value) < MIN_KEY_CHARS:
        raise PseudonymKeyError(
            f"set {env_var} to a random key of at least {MIN_KEY_CHARS} characters"
            " (one per run; delete it when the run's extracts are done)"
        )
    return Pseudonymizer(value.encode())


def pseudonym(pseudonymizer: Pseudonymizer, role: str, value: str) -> str:
    """The keyed pseudonym of ``value`` in ``role`` (actor, org, repo): one name in two roles
    gives two unrelated pseudonyms. ``ValueError`` for an unkeyed pseudonymizer."""
    if not pseudonymizer.keyed:
        raise ValueError("GH Archive pseudonyms must be keyed (logins are guessable)")
    return pseudonymizer.of(f"{role}:{value}")


def key_check(pseudonymizer: Pseudonymizer) -> str:
    """The run key's fingerprint, written into every file the key makes: the keyed pseudonym
    of a fixed text. Equal under one key, unrelated across keys, and it tells nothing about any
    login. ``ValueError`` for an unkeyed pseudonymizer."""
    return pseudonym(pseudonymizer, KEY_CHECK_ROLE, KEY_CHECK_TEXT)


@contextmanager
def _open_text(path: str | Path) -> Iterator[TextIO]:
    if str(path) == STDIN_PATH:
        yield sys.stdin
        return
    path = Path(path)
    if path.suffix == GZIP_SUFFIX:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            yield handle
    else:
        with path.open(encoding="utf-8") as handle:
            yield handle


def iter_events(paths: Iterable[str | Path], stats: Counter | None = None) -> Iterator[dict]:
    """Stream the events of GH Archive JSON-lines files (gzip when the name ends in ``.gz``;
    ``-`` is stdin), in file order. A line that is not a JSON object is counted in
    ``stats["parse_errors"]`` and skipped; a corrupt gzip stream raises (``OSError``,
    ``EOFError``), so a truncated download fails loudly."""
    stats = Counter() if stats is None else stats
    for path in paths:
        with _open_text(path) as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    stats["parse_errors"] += 1
                    continue
                if not isinstance(event, dict):
                    stats["parse_errors"] += 1
                    continue
                yield event


def event_time(event: Mapping) -> float:
    """The event's ``created_at`` as epoch seconds; ``ValueError`` when it is missing or has
    no zone."""
    text = event.get("created_at")
    if not isinstance(text, str):
        raise ValueError("event has no created_at")
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError(f"created_at has no zone: {text!r}")
    return moment.timestamp()


def utc_day(ts: float) -> int:
    """The UTC day number (from 1970-01-01) of epoch seconds ``ts``."""
    return math.floor(ts / DAY_S)


def day_number(day: date) -> int:
    """The day number (from 1970-01-01) of a calendar date."""
    return (day - EPOCH).days


def iso_day(day: int) -> str:
    """The ISO date (``YYYY-MM-DD``) of a day number."""
    return date.fromordinal(EPOCH.toordinal() + day).isoformat()


def actor_login(event: Mapping) -> str:
    """The actor's login; ``ValueError`` when the event names none."""
    login = (event.get("actor") or {}).get("login")
    if not isinstance(login, str) or not login:
        raise ValueError("event has no actor login")
    return login


def org_login(event: Mapping) -> str | None:
    """The owning organisation's login, or None for a repository outside any organisation."""
    login = (event.get("org") or {}).get("login")
    return login if isinstance(login, str) and login else None


def repo_name(event: Mapping) -> str:
    """The repository's ``owner/name``; ``ValueError`` when the event names none."""
    name = (event.get("repo") or {}).get("name")
    if not isinstance(name, str) or "/" not in name:
        raise ValueError("event has no repository name")
    return name


def actor_class(login: str, agent_logins: Iterable[str] = AGENT_LOGINS) -> str:
    """:data:`AGENT` for a listed coding-agent account, :data:`BOT` for any other login
    ending in ``[bot]``, else :data:`PERSON` (case-insensitive)."""
    lowered = login.lower()
    if lowered in {name.lower() for name in agent_logins}:
        return AGENT
    return BOT if lowered.endswith(BOT_SUFFIX) else PERSON


def load_agent_logins(path: str | Path | None) -> frozenset[str]:
    """Agent logins from a file, one per line, lowered (blank lines and ``#`` comments, also
    indented ones, skipped); :data:`AGENT_LOGINS` when ``path`` is None."""
    if path is None:
        return AGENT_LOGINS
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    stripped = (line.strip() for line in lines)
    return frozenset(s.lower() for s in stripped if s and not s.startswith(COMMENT_PREFIX))


# ── day parts and conventions (shared with gharchive_actor_cadence.py) ─────────────────────


def part_of(ts: float) -> int:
    """The part of its UTC day ``ts`` falls in: :data:`EARLY` before 04:00, else :data:`LATE`."""
    return EARLY if ts - utc_day(ts) * DAY_S < SPLIT_S else LATE


def check_convention(convention: str) -> None:
    """``ValueError`` unless ``convention`` is one of :data:`DAY_CONVENTIONS`."""
    if convention not in DAY_CONVENTIONS:
        raise ValueError(f"convention must be one of {DAY_CONVENTIONS}, not {convention!r}")


def convention_day(day: int, part: int, convention: str) -> int:
    """The day of ``convention`` that part ``part`` of UTC day ``day`` belongs to: the UTC
    day for v4; for v5 the day before when the part is :data:`EARLY` (00:00-04:00 is still the
    day before, as ``clock.local_day`` rolls over at 04:00)."""
    check_convention(convention)
    if part not in PARTS:
        raise ValueError(f"part must be one of {PARTS}, not {part!r}")
    return day - 1 if convention == V5_DAYS and part == EARLY else day


def utc_days_of(day: int, convention: str) -> tuple[int, ...]:
    """The UTC days whose parts make up ``convention``'s ``day``: one for v4, two for v5."""
    check_convention(convention)
    return (day,) if convention == V4_DAYS else (day, day + 1)


def extracted_days(days_read: Collection[int], rows_days: Iterable[int]) -> frozenset[int]:
    """The UTC days an extract read: ``days_read`` when known, else every day between the
    first and the last day of ``rows_days`` (an extract built without ``--day``)."""
    if days_read:
        return frozenset(days_read)
    seen = list(rows_days)
    return frozenset(range(min(seen), max(seen) + 1)) if seen else frozenset()


# ── organisations: people per organisation, then the selection ─────────────────────────────


def org_people(
    events: Iterable[Mapping],
    pseudonymizer: Pseudonymizer,
    agent_logins: Iterable[str] = AGENT_LOGINS,
    stats: Counter | None = None,
) -> dict[str, set[str]]:
    """Organisation pseudonym -> pseudonyms of the people (not bots, not agents) with an
    event in one of its repositories."""
    stats = Counter() if stats is None else stats
    agents = frozenset(name.lower() for name in agent_logins)
    people: dict[str, set[str]] = defaultdict(set)
    for event in events:
        stats["events"] += 1
        org = org_login(event)
        try:
            login = actor_login(event)
        except ValueError:
            stats["bad_events"] += 1
            continue
        if org is None or actor_class(login, agents) != PERSON:
            continue
        people[pseudonym(pseudonymizer, ORG_ROLE, org)].add(
            pseudonym(pseudonymizer, ACTOR_ROLE, login)
        )
    return dict(people)


@dataclass(frozen=True)
class OrgSelection:
    """The organisations EV-26 measures: the ``top`` ones by distinct people and the ones
    ``drawn`` at random among those with a mid-sized count (pseudonyms)."""

    top: tuple[str, ...]
    drawn: tuple[str, ...]
    seed: int
    people: Mapping[str, int] = field(default_factory=dict)

    @property
    def orgs(self) -> frozenset[str]:
        """Every selected organisation."""
        return frozenset(self.top) | frozenset(self.drawn)

    def to_json(self, check: str) -> dict:
        """JSON-safe data for :func:`load_org_selection`, stamped with the key ``check``."""
        return {
            "schema": SCHEMA_SELECTION,
            "key_check": check,
            "seed": self.seed,
            "top": list(self.top),
            "drawn": list(self.drawn),
            "people": {org: self.people[org] for org in sorted(self.orgs) if org in self.people},
        }


def select_orgs(
    people: Mapping[str, int],
    *,
    top: int = TOP_ORGS,
    drawn: int = RANDOM_ORGS,
    min_actors: int = MIN_ORG_ACTORS,
    max_actors: int = MAX_ORG_ACTORS,
    seed: int = SELECTION_SEED,
    exclude: Iterable[str] = (),
) -> OrgSelection:
    """The ``top`` organisations by distinct people (ties: the smaller pseudonym), plus
    ``drawn`` at random (``seed``) among the rest with ``min_actors``-``max_actors`` people;
    fewer when fewer qualify. ``exclude`` keeps organisations out (the EV-14 bank's are
    disjoint from the evaluated ones).

    The draw is not reproducible from ``seed`` alone: the pool is ordered by keyed pseudonyms,
    so another key draws other organisations from the same seed. Once the key is deleted, the
    selection file is the only record of the draw; keep it frozen."""
    if min(top, drawn, min_actors) < 0 or max_actors < min_actors:
        raise ValueError("counts must be non-negative and min_actors <= max_actors")
    excluded = frozenset(exclude)
    ranked = sorted((org for org in people if org not in excluded), key=lambda o: (-people[o], o))
    chosen = tuple(ranked[:top])
    pool = sorted(org for org in ranked[top:] if min_actors <= people[org] <= max_actors)
    picked = tuple(sorted(random.Random(seed).sample(pool, min(drawn, len(pool)))))
    return OrgSelection(chosen, picked, seed, {org: people[org] for org in chosen + picked})


def read_selection(path: str | Path) -> tuple[frozenset[str], str]:
    """A ``select-orgs`` file's organisation pseudonyms and its key check, unchecked."""
    data = read_json(path)
    if data.get("schema") != SCHEMA_SELECTION:
        raise ValueError(f"{path} is not an organisation selection ({SCHEMA_SELECTION})")
    return frozenset(data["top"]) | frozenset(data["drawn"]), str(data["key_check"])


def load_org_selection(path: str | Path, pseudonymizer: Pseudonymizer) -> frozenset[str]:
    """The organisation pseudonyms of a ``select-orgs`` file made under this run's key;
    :class:`SelectionKeyError` when another key made it (its pseudonyms would match nothing)."""
    orgs, check = read_selection(path)
    if check != key_check(pseudonymizer):
        raise SelectionKeyError(
            f"{path} was made under another pseudonym key: its organisations match nothing"
            " under this one (start a new run from the key step)"
        )
    return orgs


# ── one event -> one tools/call request and its sizes ──────────────────────────────────────


def mapped_tool(event: Mapping) -> str | None:
    """The MCP tool an event maps to (:data:`TOOL_EVENTS`), or None."""
    kind, action = event.get("type"), (event.get("payload") or {}).get("action")
    if not isinstance(kind, str) or not isinstance(action, str):
        return None
    return TOOL_EVENTS.get((kind, action))


def _text(obj: Mapping, name: str) -> dict[str, str]:
    value = obj.get(name)
    return {name: value} if isinstance(value, str) else {}


def _number(obj: Mapping, name: str, as_name: str) -> dict[str, int]:
    value = obj.get(name)
    return {as_name: value} if isinstance(value, int) and not isinstance(value, bool) else {}


def call_arguments(event: Mapping, tool: str) -> dict | None:
    """The ``params.arguments`` of the ``tool`` call the event stands for; None when the
    archive trimmed its text (no title and no body). ``ValueError`` for an unknown tool or an
    event without a repository."""
    owner, repo = repo_name(event).split("/", 1)
    payload = event.get("payload") or {}
    base = {"owner": owner, "repo": repo}
    if tool in (CREATE_ISSUE, CREATE_PULL_REQUEST):
        holder = payload.get("issue" if tool == CREATE_ISSUE else "pull_request") or {}
        if "title" not in holder and "body" not in holder:
            return None
        args = base | {"title": holder.get("title") or ""} | _text(holder, "body")
        if tool == CREATE_PULL_REQUEST:
            for side in ("head", "base"):
                ref = (holder.get(side) or {}).get("ref")
                args |= {side: ref} if isinstance(ref, str) else {}
        return args
    if tool == ADD_ISSUE_COMMENT:
        comment = payload.get("comment") or {}
        if "body" not in comment:
            return None
        return (
            base
            | _number(payload.get("issue") or {}, "number", "issue_number")
            | _text(comment, "body")
        )
    if tool == CREATE_PULL_REQUEST_REVIEW:
        review = payload.get("review") or {}
        if "body" not in review:
            return None
        event_name = REVIEW_EVENTS.get(review.get("state"), DEFAULT_REVIEW_EVENT)
        pull = _number(payload.get("pull_request") or {}, "number", "pullNumber")
        return base | pull | _text(review, "body") | {"event": event_name}
    raise ValueError(f"unknown tool {tool!r}")


def request_message(tool: str, arguments: Mapping) -> dict:
    """The JSON-RPC ``tools/call`` request carrying ``arguments``, as a legacy-era client
    sends it (no ``params._meta``)."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": REQUEST_ID,
        "method": CALL_METHOD,
        "params": {"name": tool, "arguments": dict(arguments)},
    }


def message_bytes(message: Mapping) -> int:
    """The size v1-v4 log as ``gateway.message_bytes`` (``wire_log._bytes``). On a
    :func:`request_message` that is the legacy-era size; a 2026-07-28 request adds its
    ``params._meta``."""
    return len(json.dumps(message, ensure_ascii=False).encode())


@dataclass(frozen=True)
class RequestSize:
    """One rendered call's sizes: v5's ``arg_bytes`` (ARG-1) and v4's ``message_bytes``."""

    tool: str
    arg_bytes: int
    message_bytes: int


def request_size(tool: str, arguments: Mapping) -> RequestSize:
    """Both sizes of the ``tool`` call with ``arguments``."""
    message = request_message(tool, arguments)
    return RequestSize(tool, argument_bytes(message), message_bytes(message))


# ── extraction: per-actor maxima of day parts and size histograms ──────────────────────────


@dataclass
class RequestDay:
    """Per tool, the largest request in each measure and the number of calls, of one actor
    in one organisation (both pseudonyms). An extract row covers ``part`` (:data:`EARLY` or
    :data:`LATE`) of UTC day ``day``; with ``part`` None the row is a whole day of some
    convention, which :func:`actor_days` makes."""

    org: str
    actor: str
    actor_class: str
    day: int
    part: int | None
    largest_args: dict[str, int] = field(default_factory=dict)
    largest_message: dict[str, int] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, int, int | None]:
        """(organisation, actor, day, part)."""
        return (self.org, self.actor, self.day, self.part)

    def add(self, size: RequestSize, calls: int = 1) -> None:
        """Fold ``calls`` calls whose largest is ``size`` into the row."""
        tool = size.tool
        self.largest_args[tool] = max(self.largest_args.get(tool, 0), size.arg_bytes)
        self.largest_message[tool] = max(self.largest_message.get(tool, 0), size.message_bytes)
        self.calls[tool] = self.calls.get(tool, 0) + calls

    def add_row(self, other: RequestDay) -> None:
        """Fold every tool of ``other`` into this row (no key check: :meth:`merge` has one)."""
        for tool, calls in other.calls.items():
            size = RequestSize(tool, other.largest_args[tool], other.largest_message[tool])
            self.add(size, calls)

    def merge(self, other: RequestDay) -> None:
        """Fold another copy of the same row (same key) into this one."""
        if other.key != self.key:
            raise ValueError("only rows with the same key merge")
        self.add_row(other)

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json`."""
        return {
            "org": self.org,
            "actor": self.actor,
            "class": self.actor_class,
            "day": self.day,
            "part": self.part,
            ARG_BYTES: self.largest_args,
            MESSAGE_BYTES: self.largest_message,
            "calls": self.calls,
        }

    @classmethod
    def from_json(cls, data: Mapping) -> RequestDay:
        """:meth:`to_json` output back."""
        part = data["part"]
        return cls(
            data["org"],
            data["actor"],
            data["class"],
            int(data["day"]),
            None if part is None else int(part),
            dict(data[ARG_BYTES]),
            dict(data[MESSAGE_BYTES]),
            dict(data["calls"]),
        )


#: measure -> actor class -> tool -> size -> calls
Histograms = dict[str, dict[str, dict[str, Counter]]]


def _histograms() -> Histograms:
    return {m: defaultdict(lambda: defaultdict(Counter)) for m in MEASURES}


@dataclass
class RequestExtract:
    """What ``extract`` keeps of some hourly files: the key check, the UTC days read (empty
    when not declared), counts, size histograms (the size bank's source) and, unless
    histograms-only, the per-actor day parts."""

    key_check: str = ""
    utc_days: set[int] = field(default_factory=set)
    files_read: list[str] = field(default_factory=list)
    stats: Counter = field(default_factory=Counter)
    histograms: Histograms = field(default_factory=_histograms)
    parts: dict[tuple[str, str, int, int | None], RequestDay] = field(default_factory=dict)

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json` (sizes become string keys)."""
        return {
            "schema": SCHEMA_SIZES,
            "label": LABEL,
            "key_check": self.key_check,
            "utc_days": sorted(self.utc_days),
            "files_read": sorted(self.files_read),
            "stats": dict(sorted(self.stats.items())),
            "histograms": {
                measure: {
                    name: {tool: {str(s): n for s, n in sorted(c.items())} for tool, c in t.items()}
                    for name, t in by_class.items()
                }
                for measure, by_class in self.histograms.items()
            },
            "parts": [self.parts[key].to_json() for key in sorted(self.parts)],
        }

    @classmethod
    def from_json(cls, data: Mapping) -> RequestExtract:
        """:meth:`to_json` output back."""
        if data.get("schema") != SCHEMA_SIZES:
            raise ValueError(f"not a request-size extract ({SCHEMA_SIZES})")
        out = cls(
            key_check=str(data["key_check"]),
            utc_days={int(d) for d in data["utc_days"]},
            files_read=list(data["files_read"]),
            stats=Counter(data["stats"]),
        )
        for measure, by_class in data["histograms"].items():
            for cls_name, by_tool in by_class.items():
                for tool, sizes in by_tool.items():
                    out.histograms[measure][cls_name][tool].update(
                        {int(s): n for s, n in sizes.items()}
                    )
        for row in data["parts"]:
            part = RequestDay.from_json(row)
            out.parts[part.key] = part
        return out


def _wanted_org(
    org: str, orgs: frozenset[str] | None, exclude: frozenset[str], stats: Counter
) -> bool:
    if org in exclude or (orgs is not None and org not in orgs):
        stats["other_org"] += 1
        return False
    return True


def extract_requests(
    events: Iterable[Mapping],
    pseudonymizer: Pseudonymizer,
    *,
    day: int | None = None,
    orgs: frozenset[str] | None = None,
    exclude_orgs: Iterable[str] = (),
    agent_logins: Iterable[str] = AGENT_LOGINS,
    keep_days: bool = True,
) -> RequestExtract:
    """Size every mapped event in an organisation repository. ``day`` (a UTC day number)
    declares the day the files hold: events outside it are counted (``outside_day``) and
    dropped, and the extract records the day as read. ``orgs`` (pseudonyms) keeps only those
    organisations (None: all), ``exclude_orgs`` drops some; ``keep_days=False`` keeps the
    histograms only (the EV-14 bank needs no actor-days)."""
    out = RequestExtract(key_check=key_check(pseudonymizer))
    if day is not None:
        out.utc_days.add(day)
    stats = out.stats
    excluded = frozenset(exclude_orgs)
    agents = frozenset(name.lower() for name in agent_logins)
    org_names: dict[str, str] = {}  # login -> pseudonym, in memory only
    for event in events:
        stats["events"] += 1
        tool = mapped_tool(event)
        if tool is None:
            continue
        org = org_login(event)
        if org is None:
            stats["no_org"] += 1
            continue
        org_p = org_names.get(org)
        if org_p is None:
            org_p = org_names[org] = pseudonym(pseudonymizer, ORG_ROLE, org)
        if not _wanted_org(org_p, orgs, excluded, stats):
            continue
        try:
            login, ts = actor_login(event), event_time(event)
            arguments = call_arguments(event, tool)
        except ValueError:
            stats["bad_events"] += 1
            continue
        if day is not None and utc_day(ts) != day:
            stats["outside_day"] += 1
            continue
        if arguments is None:
            stats[f"text_missing:{tool}"] += 1
            continue
        stats[f"mapped:{tool}"] += 1
        size = request_size(tool, arguments)
        cls_name = actor_class(login, agents)
        out.histograms[ARG_BYTES][cls_name][tool][size.arg_bytes] += 1
        out.histograms[MESSAGE_BYTES][cls_name][tool][size.message_bytes] += 1
        if keep_days:
            key = (org_p, pseudonym(pseudonymizer, ACTOR_ROLE, login), utc_day(ts), part_of(ts))
            row = out.parts.get(key)
            if row is None:
                row = out.parts[key] = RequestDay(*key[:2], cls_name, *key[2:])
            row.add(size)
    return out


def merge_extracts(extracts: Iterable[RequestExtract]) -> RequestExtract:
    """Several extracts as one: counts and histograms add, parts merge. ``ValueError`` when
    they were made under different pseudonym keys or declare one UTC day twice."""
    out = RequestExtract()
    for part in extracts:
        if part.key_check and out.key_check and part.key_check != out.key_check:
            raise ValueError("extracts made under different pseudonym keys do not merge")
        out.key_check = out.key_check or part.key_check
        twice = out.utc_days & part.utc_days
        if twice:
            raise ValueError(f"UTC days extracted twice: {sorted(twice)}")
        out.utc_days |= part.utc_days
        out.files_read.extend(part.files_read)
        out.stats.update(part.stats)
        for measure, by_class in part.histograms.items():
            for cls_name, by_tool in by_class.items():
                for tool, sizes in by_tool.items():
                    out.histograms[measure][cls_name][tool].update(sizes)
        for key, row in part.parts.items():
            if key in out.parts:
                out.parts[key].merge(row)
            else:
                out.parts[key] = RequestDay.from_json(row.to_json())
    return out


# ── days of a convention ───────────────────────────────────────────────────────────────────


def actor_days(
    parts: Iterable[RequestDay],
    convention: str,
    *,
    pooled: bool = False,
    utc_days: Collection[int] = (),
) -> dict[tuple[str, str, int], RequestDay]:
    """Extract parts merged into whole agent-days of ``convention``: (route, actor, day) ->
    the day (``part`` None). The route is the organisation, or :data:`POOLED` with ``pooled``,
    where an actor's parts in several organisations make one agent-day, as one log holding
    them all would. A day is kept only when every UTC day it spans was read: ``utc_days``
    (the extract's), else every day between the parts' first and last. ``ValueError`` for a
    row that is already a whole day."""
    check_convention(convention)
    rows = list(parts)
    if any(row.part not in PARTS for row in rows):
        raise ValueError("actor_days merges extract parts, not whole days")
    read = extracted_days(utc_days, (row.day for row in rows))
    out: dict[tuple[str, str, int], RequestDay] = {}
    for row in rows:
        day = convention_day(row.day, row.part, convention)
        if not read.issuperset(utc_days_of(day, convention)):
            continue
        route = POOLED if pooled else row.org
        key = (route, row.actor, day)
        merged = out.get(key)
        if merged is None:
            merged = out[key] = RequestDay(route, row.actor, row.actor_class, day, None)
        merged.add_row(row)
    return out


def policy_messages(days: Iterable[RequestDay]) -> list[Message]:
    """One engine message per (whole day, tool), at noon of the day's number, carrying the
    day's largest request: ``size`` (message bytes, v1-v4) and ``arg_bytes`` (v5), accepted, a
    write, zone UTC.

    Noon lies inside the day under both conventions, so the learner keys each message to its
    own day when the days were made (:func:`actor_days`) in the convention of the learner's
    design: :data:`V4_DAYS` for ``policy.derive_policy`` with a v1-v4 base, :data:`V5_DAYS`
    with a v5 base. Then the learner sets the same request limits as from every call (a
    request limit reads only agent-day maxima; ``test_gharchive.py`` checks both designs on
    event streams). Days of the other convention give other agent-days: v5's 04:00 rollover
    moves calls made before 04:00 UTC to the day before. Its other lines (Burst, Sweep,
    required steps) mean nothing here. Pass one route's days; parts raise ``ValueError``."""
    rows = list(days)
    if any(row.part is not None for row in rows):
        raise ValueError("policy_messages takes whole days (actor_days), not extract parts")
    out = [
        Message(
            ts=d.day * DAY_S + NOON_S,
            agent=d.actor,
            method=CALL_METHOD,
            tool=tool,
            operation=WRITE,
            size=d.largest_message[tool],
            arg_bytes=d.largest_args[tool],
            outcome=ACCEPTED,
            zone=UTC_ZONE,
        )
        for d in rows
        for tool in sorted(d.calls)
    ]
    return sorted(out, key=lambda m: (m.ts, m.agent, m.tool))


# ── aggregates: quantiles, limits, realised rates ──────────────────────────────────────────


def _check_quantile(q: float) -> None:
    if not 0 < q <= 1:
        raise ValueError(f"q must be in (0, 1], not {q!r}")


def nearest_rank(values: Sequence[float], q: float) -> float:
    """``policy._quantile``'s rule: the ``ceil(q n)``-th smallest of ``n`` values (at most
    the largest). ``ValueError`` for no values or ``q`` outside (0, 1]."""
    _check_quantile(q)
    if not values:
        raise ValueError("no values")
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1)]


def histogram_quantile(sizes: Mapping[float, int], q: float) -> float:
    """:func:`nearest_rank` of the values a value -> count histogram holds. ``ValueError``
    for an empty histogram or ``q`` outside (0, 1]."""
    _check_quantile(q)
    total = sum(sizes.values())
    if total <= 0:
        raise ValueError("empty histogram")
    rank = min(total - 1, math.ceil(q * total) - 1)
    seen = 0
    for size in sorted(sizes):
        seen += sizes[size]
        if seen > rank:
            return size
    raise AssertionError("unreachable: the rank is below the total")


def whole_kb(size: float) -> int:
    """``size`` rounded up to a whole KB (``policy._whole_kb``)."""
    return math.ceil(size / KB) * KB


def size_quantiles(
    histograms: Histograms,
    quantiles: Sequence[float] = QUANTILES,
    min_calls: int = MIN_PUBLISH_CALLS,
) -> dict:
    """Per measure, actor class (and :data:`ALL_CLASSES`) and tool: the number of calls and
    the nearest-rank quantiles; a cell under ``min_calls`` calls shows only its count."""
    out: dict = {}
    for measure, by_class in histograms.items():
        pooled: dict[str, Counter] = defaultdict(Counter)
        cells: dict[str, dict[str, Counter]] = {}
        for cls_name, by_tool in by_class.items():
            cells[cls_name] = dict(by_tool)
            for tool, sizes in by_tool.items():
                pooled[tool].update(sizes)
        cells[ALL_CLASSES] = dict(pooled)
        out[measure] = {
            cls_name: {
                tool: _quantile_cell(sizes, quantiles, min_calls)
                for tool, sizes in sorted(by_tool.items())
            }
            for cls_name, by_tool in sorted(cells.items())
        }
    return out


def _quantile_cell(sizes: Mapping[int, int], quantiles: Sequence[float], min_calls: int) -> dict:
    n = sum(sizes.values())
    if n < min_calls:
        return {"calls": n, "suppressed": True}
    return {"calls": n} | {f"q{q}": histogram_quantile(sizes, q) for q in quantiles}


@dataclass(frozen=True)
class RouteLimits:
    """A route's learned limits: per tool, and the ``fallback`` (``request_limit_bytes``)
    every other tool uses. ``design`` sets the measure and the day convention they were
    learned on and are held to (:data:`DESIGN_MEASURES`, :data:`DESIGN_DAYS`);
    ``learning_days`` counts the agent-days they were read from, ``actors`` the distinct
    actors behind the route's learning days."""

    by_tool: Mapping[str, int]
    fallback: int
    learning_days: int
    design: str = V4
    actors: int = 0

    def limit(self, tool: str) -> int:
        """The limit a call of ``tool`` is held to."""
        return self.by_tool.get(tool, self.fallback)


def _learning_rows(
    parts: Iterable[RequestDay],
    convention: str,
    learn_from: int,
    learn_days: int,
    pooled: bool,
    utc_days: Collection[int],
) -> dict[str, list[RequestDay]]:
    """Each route's whole days in ``[learn_from, learn_from + learn_days)``."""
    by_route: dict[str, list[RequestDay]] = defaultdict(list)
    days = actor_days(parts, convention, pooled=pooled, utc_days=utc_days)
    for key in sorted(days):
        d = days[key]
        if learn_from <= d.day < learn_from + learn_days:
            by_route[d.org].append(d)
    return by_route


def learn_v4_limits(
    parts: Iterable[RequestDay],
    learn_from: int,
    learn_days: int = LEARN_DAYS,
    *,
    quantile: float = QUANTILE,
    min_tool_days: int = MIN_TOOL_DAYS,
    pooled: bool = False,
    utc_days: Collection[int] = (),
) -> dict[str, RouteLimits]:
    """Each route's v4 limits (``policy.derive_policy``'s procedure on message bytes) from
    its v4 agent-days in ``[learn_from, learn_from + learn_days)``. A route with no agent-day
    there gets none."""
    out: dict[str, RouteLimits] = {}
    rows_by_route = _learning_rows(parts, V4_DAYS, learn_from, learn_days, pooled, utc_days)
    for route, rows in rows_by_route.items():
        per_tool: dict[str, list[int]] = defaultdict(list)
        for d in rows:
            for tool, size in d.largest_message.items():
                per_tool[tool].append(size)
        by_tool = {
            tool: whole_kb(nearest_rank(sizes, quantile))
            for tool, sizes in per_tool.items()
            if len(sizes) >= min_tool_days
        }
        largest = [max(d.largest_message.values()) for d in rows]
        actors = len({d.actor for d in rows})
        fallback = whole_kb(nearest_rank(largest, quantile))
        out[route] = RouteLimits(by_tool, fallback, len(rows), V4, actors)
    return out


@dataclass(frozen=True)
class V5Limits:
    """RF1's lines (:func:`learn_v5_limits`): ``limits`` for the routes that learned one,
    and ``not_learned``, route -> learning agent-days, for those that could not."""

    limits: Mapping[str, RouteLimits]
    not_learned: Mapping[str, int]


def learn_v5_limits(
    parts: Iterable[RequestDay],
    learn_from: int,
    learn_days: int = LEARN_DAYS,
    *,
    pooled: bool = False,
    base: BehaviourConfig | None = None,
    utc_days: Collection[int] = (),
) -> V5Limits:
    """Each route's RF1 line (Hyp5) from its v5 agent-days in ``[learn_from, learn_from +
    learn_days)``: ``policy.request_lines`` over ``policy.agent_days`` of the route's
    :func:`policy_messages`, which is what ``derive_policy`` with the v5 ``base`` learns for
    the request limits. A route whose line cannot be learned (fewer than
    ``policy.MIN_LINE_DAYS`` agent-days left once its top identity is out) is listed in
    ``not_learned``, never given the written default. ``ValueError`` for a base that is not
    v5, has RF1 off, or rolls over at another hour than the parts' split."""
    base = base or BehaviourConfig(design=V5)
    if base.design != V5 or not base.request_limit_pooled:
        raise ValueError("learn_v5_limits needs a v5 base with request_limit_pooled (RF1) on")
    if base.day_start_hour != DAY_START_HOUR:
        raise ValueError(f"the extract parts split at {DAY_START_HOUR:g}:00, the v5 rollover")
    limits: dict[str, RouteLimits] = {}
    not_learned: dict[str, int] = {}
    rows_by_route = _learning_rows(parts, V5_DAYS, learn_from, learn_days, pooled, utc_days)
    for route, rows in sorted(rows_by_route.items()):
        calls = policy.learned_calls(policy_messages(rows), base)
        days = policy.agent_days(calls, base)
        lines = policy.request_lines(days, policy.operation_classes(calls))
        if lines is None:
            not_learned[route] = len(days)
            continue
        actors = len({d.actor for d in rows})
        limits[route] = RouteLimits(dict(lines.limits), lines.fallback, lines.days, V5, actors)
    return V5Limits(limits, not_learned)


@dataclass(frozen=True)
class OversizedRate:
    """Agent-days with some call over its limit (``raised``) among ``active`` ones, of
    ``actors`` distinct actors."""

    raised: int
    active: int
    actors: int = 0

    @property
    def rate(self) -> float | None:
        """raised / active; None for no active agent-day."""
        return self.raised / self.active if self.active else None

    def to_json(self) -> dict:
        """JSON-safe data."""
        return {"raised": self.raised, "active": self.active, "rate": self.rate}


@dataclass
class _RateCell:
    raised: int = 0
    active: int = 0
    actors: set[str] = field(default_factory=set)

    def add(self, other: _RateCell) -> None:
        self.raised += other.raised
        self.active += other.active
        self.actors |= other.actors

    def rate(self) -> OversizedRate:
        return OversizedRate(self.raised, self.active, len(self.actors))


def _limits_design(limits: Mapping[str, RouteLimits]) -> str:
    designs = {lim.design for lim in limits.values()}
    if len(designs) > 1:
        raise ValueError(f"limits of several designs cannot be scored together: {designs}")
    return designs.pop() if designs else V4


def _rate_cells(
    parts: Iterable[RequestDay],
    limits: Mapping[str, RouteLimits],
    eval_from: int,
    pooled: bool,
    utc_days: Collection[int],
) -> dict[str, dict[str, _RateCell]]:
    design = _limits_design(limits)
    measure, convention = DESIGN_MEASURES[design], DESIGN_DAYS[design]
    cells: dict[str, dict[str, _RateCell]] = defaultdict(lambda: defaultdict(_RateCell))
    for d in actor_days(parts, convention, pooled=pooled, utc_days=utc_days).values():
        route = limits.get(d.org)
        if d.day < eval_from or route is None:
            continue
        sizes = d.largest_args if measure == ARG_BYTES else d.largest_message
        raised = any(size > route.limit(tool) for tool, size in sizes.items())
        for cls_name in (d.actor_class, ALL_CLASSES):
            cell = cells[d.org][cls_name]
            cell.raised += raised
            cell.active += 1
            cell.actors.add(d.actor)
    return cells


def oversized_rates(
    parts: Iterable[RequestDay],
    limits: Mapping[str, RouteLimits],
    eval_from: int,
    *,
    pooled: bool = False,
    utc_days: Collection[int] = (),
) -> dict[str, dict[str, OversizedRate]]:
    """Route -> actor class (and :data:`ALL_CLASSES`) -> the realised oversized rate on the
    agent-days from ``eval_from`` on (rule ``size > limit``). The limits' design sets the
    measure and the days: v4 limits hold message bytes on v4 days, v5 limits (RF1, Hyp5)
    argument bytes on v5 days. Routes without limits are left out."""
    cells = _rate_cells(parts, limits, eval_from, pooled, utc_days)
    return {
        org: {c: cell.rate() for c, cell in sorted(by_class.items())}
        for org, by_class in sorted(cells.items())
    }


# ── EV-14: the real size bank ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SizeBank:
    """Per tool, the empirical size distribution of one measure: ``sizes`` (ascending,
    distinct) and ``cumulative`` call counts. Sampling is deterministic for a seed."""

    measure: str
    sizes: Mapping[str, tuple[int, ...]]
    cumulative: Mapping[str, tuple[int, ...]]

    @classmethod
    def from_histograms(
        cls, histograms: Histograms, measure: str = ARG_BYTES, actor_class: str = ALL_CLASSES
    ) -> SizeBank:
        """The bank of ``measure`` for one actor class (:data:`ALL_CLASSES`: all of them)."""
        by_class = histograms[measure]
        classes = list(by_class) if actor_class == ALL_CLASSES else [actor_class]
        pooled: dict[str, Counter] = defaultdict(Counter)
        for cls_name in classes:
            for tool, sizes in by_class.get(cls_name, {}).items():
                pooled[tool].update(sizes)
        sizes: dict[str, tuple[int, ...]] = {}
        cumulative: dict[str, tuple[int, ...]] = {}
        for tool, counts in sorted(pooled.items()):
            ordered = tuple(sorted(s for s, n in counts.items() if n > 0))
            running, seen = [], 0
            for size in ordered:
                seen += counts[size]
                running.append(seen)
            if ordered:
                sizes[tool], cumulative[tool] = ordered, tuple(running)
        return cls(measure, sizes, cumulative)

    @property
    def tools(self) -> tuple[str, ...]:
        """The tools the bank can draw for."""
        return tuple(sorted(self.sizes))

    def total(self, tool: str) -> int:
        """Calls behind ``tool``'s distribution."""
        return self.cumulative[tool][-1]

    def size_at(self, tool: str, u: float) -> int:
        """The size at uniform ``u`` in [0, 1) (the inverse distribution function)."""
        if not 0 <= u < 1:
            raise ValueError(f"u must be in [0, 1), not {u!r}")
        total = self.total(tool)
        return self.sizes[tool][bisect_right(self.cumulative[tool], min(total - 1, int(u * total)))]

    def sample(self, tool: str, rng: random.Random) -> int:
        """One size for a ``tool`` call, drawn with ``rng``."""
        return self.size_at(tool, rng.random())

    def quantile(self, tool: str, q: float) -> int:
        """The bank's nearest-rank ``q`` quantile for ``tool``."""
        return histogram_quantile(dict(zip(self.sizes[tool], _counts(self.cumulative[tool]))), q)

    def to_json(self) -> dict:
        """JSON-safe data for :meth:`from_json`."""
        return {
            "schema": SCHEMA_BANK,
            "label": LABEL,
            "measure": self.measure,
            "measure_note": MEASURE_NOTES[self.measure],
            "tools": {
                tool: {"sizes": list(self.sizes[tool]), "cumulative": list(self.cumulative[tool])}
                for tool in self.tools
            },
        }

    @classmethod
    def from_json(cls, data: Mapping) -> SizeBank:
        """:meth:`to_json` output back."""
        if data.get("schema") != SCHEMA_BANK:
            raise ValueError(f"not a size bank ({SCHEMA_BANK})")
        tools = data["tools"]
        return cls(
            data["measure"],
            {t: tuple(v["sizes"]) for t, v in tools.items()},
            {t: tuple(v["cumulative"]) for t, v in tools.items()},
        )


def _counts(cumulative: Sequence[int]) -> list[int]:
    return [b - a for a, b in zip((0, *cumulative[:-1]), cumulative)]


# ── summary and files ──────────────────────────────────────────────────────────────────────


def _published_rate(cell: _RateCell, min_actors: int) -> dict:
    if len(cell.actors) < min_actors:
        return {"suppressed": True}
    return cell.rate().to_json()


def _published_limits(limits: RouteLimits, min_actors: int) -> dict:
    if limits.actors < min_actors:
        return {"suppressed": True}
    return {
        "by_tool": dict(sorted(limits.by_tool.items())),
        "fallback": limits.fallback,
        "learning_days": limits.learning_days,
    }


def _design_summary(
    parts: Sequence[RequestDay],
    limits: Mapping[str, RouteLimits],
    eval_from: int,
    pooled: bool,
    utc_days: Collection[int],
    min_actors: int,
) -> dict:
    cells = _rate_cells(parts, limits, eval_from, pooled, utc_days)
    total: dict[str, _RateCell] = defaultdict(_RateCell)
    for by_class in cells.values():
        for cls_name, cell in by_class.items():
            total[cls_name].add(cell)
    return {
        "limits": {
            route: _published_limits(lim, min_actors) for route, lim in sorted(limits.items())
        },
        "rates": {
            route: {c: _published_rate(cell, min_actors) for c, cell in sorted(by_class.items())}
            for route, by_class in sorted(cells.items())
        },
        "total": {c: _published_rate(cell, min_actors) for c, cell in sorted(total.items())},
    }


def summarise(
    extract: RequestExtract,
    learn_from: int | None = None,
    learn_days: int = LEARN_DAYS,
    *,
    pooled: bool = False,
    min_actors: int = MIN_PUBLISH_ACTORS,
) -> dict:
    """The publishable EV-26 summary: size quantiles per tool and actor class; for v4 (Part
    A's procedure) and v5 (RF1, Hyp5) each route's learned limits and its realised oversized
    rate after learning, per actor class, and the totals over routes. A route's limits, a
    rate cell or a class total from fewer than ``min_actors`` distinct actors is suppressed;
    v5's routes that learned no line are counted, not named. ``learn_from`` defaults to the
    first day read. The UTC days read and the missing ones between them are listed."""
    parts = list(extract.parts.values())
    read = extracted_days(extract.utc_days, (p.day for p in parts))
    first = min(read, default=None)
    learn_from = first if learn_from is None else learn_from
    out = {
        "schema": SCHEMA_SUMMARY,
        "label": LABEL,
        "caller_key": CALLER_KEY,
        "caller_note": CALLER_NOTE,
        "stats": dict(sorted(extract.stats.items())),
        "files_read": len(extract.files_read),
        "utc_days": _days_read(read),
        "min_publish_actors": min_actors,
        "quantiles": size_quantiles(extract.histograms),
    }
    if learn_from is None:
        return out | {V4: {}, V5: {}}
    eval_from = learn_from + learn_days
    v4 = learn_v4_limits(parts, learn_from, learn_days, pooled=pooled, utc_days=read)
    v5 = learn_v5_limits(parts, learn_from, learn_days, pooled=pooled, utc_days=read)
    designs = {
        V4: _design_summary(parts, v4, eval_from, pooled, read, min_actors),
        V5: _design_summary(parts, v5.limits, eval_from, pooled, read, min_actors)
        | {
            "not_learned": {
                "routes": len(v5.not_learned),
                "agent_days": sum(v5.not_learned.values()),
            }
        },
    }
    return out | {
        "learn_from": learn_from,
        "learn_days": learn_days,
        "eval_from": eval_from,
        "pooled": pooled,
        **{
            design: {
                "procedure": PROCEDURES[design],
                "measure": DESIGN_MEASURES[design],
                "days": DAY_NOTES[DESIGN_DAYS[design]],
            }
            | body
            for design, body in designs.items()
        },
    }


def _days_read(read: Collection[int]) -> dict:
    """The first and the last UTC day read (ISO dates) and the days missing between them."""
    if not read:
        return {"first": None, "last": None, "missing": []}
    first, last = min(read), max(read)
    missing = [iso_day(d) for d in range(first, last + 1) if d not in read]
    return {"first": iso_day(first), "last": iso_day(last), "missing": missing}


def write_json(path: str | Path, data: object) -> None:
    """Write ``data`` as JSON (gzip with a fixed mtime when the name ends in ``.gz``),
    through a temporary file, so a killed task leaves no half-written output."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    part = path.with_name(path.name + ".part")
    with part.open("wb") as raw:
        if path.suffix == GZIP_SUFFIX:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as packed:
                packed.write(payload)
        else:
            raw.write(payload)
    os.replace(part, path)


def read_json(path: str | Path) -> dict:
    """A file :func:`write_json` wrote."""
    path = Path(path)
    if path.suffix == GZIP_SUFFIX:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(path.read_text(encoding="utf-8"))


def parse_day(text: str) -> int:
    """The day number of an ISO date ``YYYY-MM-DD``."""
    return day_number(date.fromisoformat(text))


def _command_orgs(args: argparse.Namespace) -> None:
    stats: Counter = Counter()
    pseudonymizer = keyed_pseudonymizer()
    people = org_people(
        iter_events(args.files, stats), pseudonymizer, load_agent_logins(args.agents), stats
    )
    write_json(
        args.out,
        {
            "schema": SCHEMA_ORGS,
            "key_check": key_check(pseudonymizer),
            "files_read": sorted(Path(f).name for f in args.files),
            "stats": dict(stats),
            "orgs": {org: sorted(actors) for org, actors in sorted(people.items())},
        },
    )


def _command_select(args: argparse.Namespace) -> None:
    people: dict[str, set[str]] = defaultdict(set)
    checks: set[str] = set()
    for part in args.parts:
        data = read_json(part)
        if data.get("schema") != SCHEMA_ORGS:
            raise ValueError(f"{part} is not an orgs part ({SCHEMA_ORGS})")
        checks.add(str(data["key_check"]))
        for org, actors in data["orgs"].items():
            people[org].update(actors)
    if len(checks) != 1:
        raise SelectionKeyError("the orgs parts were made under different pseudonym keys")
    (check,) = checks
    exclude: frozenset[str] = frozenset()
    if args.exclude:
        exclude, excluded_check = read_selection(args.exclude)
        if excluded_check != check:
            raise SelectionKeyError(f"{args.exclude} was made under another pseudonym key")
    selection = select_orgs(
        {org: len(actors) for org, actors in people.items()},
        top=args.top,
        drawn=args.random,
        min_actors=args.min_actors,
        max_actors=args.max_actors,
        seed=args.seed,
        exclude=exclude,
    )
    write_json(args.out, selection.to_json(check))


def _command_extract(args: argparse.Namespace) -> None:
    read_stats: Counter = Counter()
    pseudonymizer = keyed_pseudonymizer()
    part = extract_requests(
        iter_events(args.files, read_stats),
        pseudonymizer,
        day=parse_day(args.day),
        orgs=load_org_selection(args.orgs, pseudonymizer) if args.orgs else None,
        exclude_orgs=load_org_selection(args.exclude_orgs, pseudonymizer)
        if args.exclude_orgs
        else (),
        agent_logins=load_agent_logins(args.agents),
        keep_days=not args.histograms_only,
    )
    part.stats.update(read_stats)
    part.files_read = [Path(f).name for f in args.files]
    write_json(args.out, part.to_json())


def _command_summarise(args: argparse.Namespace) -> None:
    extract = merge_extracts(RequestExtract.from_json(read_json(p)) for p in args.parts)
    learn_from = parse_day(args.learn_from) if args.learn_from else None
    summary = summarise(extract, learn_from, args.learn_days, pooled=args.pooled)
    write_json(args.out, summary)
    if summary["utc_days"]["missing"]:
        print(f"gharchive: UTC days missing: {summary['utc_days']['missing']}", file=sys.stderr)
    if args.bank:
        bank = SizeBank.from_histograms(extract.histograms, args.bank_measure)
        write_json(args.bank, bank.to_json())


def build_parser() -> argparse.ArgumentParser:
    """The command line (see the module docstring)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    orgs = sub.add_parser("orgs", help="people per organisation, from hourly files")
    select = sub.add_parser("select-orgs", help="choose the organisations from orgs parts")
    extract = sub.add_parser("extract", help="per-actor day-part request sizes, one UTC day")
    summary = sub.add_parser("summarise", help="aggregates from extract parts")
    for cmd in (orgs, extract):
        cmd.add_argument("files", nargs="+", help="GH Archive hourly files (.json.gz)")
        cmd.add_argument("--agents", help="file of coding-agent logins (default AGENT_LOGINS)")
    for cmd in (orgs, select, extract, summary):
        cmd.add_argument("--out", required=True)
    select.add_argument("parts", nargs="+")
    select.add_argument("--top", type=int, default=TOP_ORGS)
    select.add_argument("--random", type=int, default=RANDOM_ORGS)
    select.add_argument("--min-actors", type=int, default=MIN_ORG_ACTORS)
    select.add_argument("--max-actors", type=int, default=MAX_ORG_ACTORS)
    select.add_argument("--seed", type=int, default=SELECTION_SEED)
    select.add_argument("--exclude", help="a selection whose organisations stay out")
    extract.add_argument("--day", required=True, help="the UTC day the files hold, YYYY-MM-DD")
    extract.add_argument("--orgs", help="keep only this selection's organisations")
    extract.add_argument("--exclude-orgs", help="drop this selection's organisations")
    extract.add_argument("--histograms-only", action="store_true", help="no actor-days")
    summary.add_argument("parts", nargs="+")
    summary.add_argument("--learn-from", help="first learning day, YYYY-MM-DD")
    summary.add_argument("--learn-days", type=int, default=LEARN_DAYS)
    summary.add_argument("--pooled", action="store_true", help="one set of limits for all")
    summary.add_argument("--bank", help="also write the EV-14 size bank here")
    summary.add_argument("--bank-measure", choices=MEASURES, default=ARG_BYTES)
    return parser


COMMANDS = {
    "orgs": _command_orgs,
    "select-orgs": _command_select,
    "extract": _command_extract,
    "summarise": _command_summarise,
}


def main(argv: Sequence[str] | None = None) -> None:
    """Run one stage."""
    args = build_parser().parse_args(argv)
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
