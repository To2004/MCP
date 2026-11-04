"""A mostly-ordinary GitHub-like organisation, as the MCP server would see it.

The 26 real GitHub MCP tools with their static levels (github-helios static scan), about 100
repositories with sensitivity 2-5, and agents with their own habits:

- people (developers, leads, SREs, PMs) working through Claude Code, Cursor, VS Code Copilot or
  a desktop client that keeps one session open all day;
- bots: CI bots on cloud runners (many /16 networks), issue-triage bots, report scripts that page
  through every repository.

Ordinary life, labelled so false alarms can be attributed (``legit`` tags): vacations, sick
days, travel (time zone and hotel network), client switches, ISP changes, team transfers, role
changes, new hires exploring, on-call nights, a release crunch, new project repositories, the
monthly report run. Three org-wide changes: a VPN change (day 110), a server release that adds
four tools (day 130) and a repository migration (day 150).

Rare *gray* episodes (``gray`` = episode id): risky but not attacks. Bulk export, a peek at a
sensitive repository, a stuck agent loop, mass cleanup, a weekend batch, copying from a sensitive
repository, a huge paste, a personal script on the same token, slow scope creep, over-fetching,
and a misconfigured bot loop.

Each message is a tuple ``ROW`` (see below); a world is ``{agent: [rows in time order]}``.

**World versions.** ``build_world(..., world_version="v4")`` (the default) is the world every
v1-v4 result was computed on, bit for bit under ``PYTHONHASHSEED=0``: a person's repositories are
still ordered by Python's salted ``hash()``. ``world_version="v5"`` turns on the v5 simulator
changes (design spec 4.5). Each is a field of :class:`WorldOptions`, so a world family can set
them one by one:

- EV-01 ``stable_order``: repositories ordered by a blake2b digest (:func:`stable_hash`), so a
  world is a pure function of (seed, profile, calendar, options) under any ``PYTHONHASHSEED``;
- EV-06 :class:`Calendar`: the org-wide change days, the release crunch and the gray window.
  ``Calendar()`` is today's; :func:`draw_calendar` draws one from :class:`CalendarRanges`;
- EV-07 ``extended_rows``: rows grow three columns (``ROW_V5``): the bytes of ``result.content``
  the server returned (:func:`response_size`), the asset's exposure and its owner;
- EV-08 ``scaled_roster``: bots and hires as shares of the size (150 agents give today's
  roster); ``churn_per_year``: people join and leave all year (family W8); ``bot_gray_rate``:
  gray episodes for bots (token reuse, CI scope creep, a misconfigured writer);
- EV-09 ``plain_share``: the share of gray episodes in their *plain* variant, which keeps the
  agent's usual hours, network, client and session opening, so no giveaway gives it away.
  Labels are stratified per kind across the world (:func:`stratified_variants`), so each
  kind's split is within one episode of ``plain_share``;
- EV-09b ``public_repos``: public repositories in every organisation; ``toxic_flow``: a gray
  kind that copies from a sensitive repository into a public one (classic and plain);
- D5 ``sticky_addresses``: an agent keeps its egress address (below), so the key of a caller
  without sign-in, its client family plus its address (spec 2.1), splits and merges agents as
  a deployment would see them.

**Owners** (v5 rows). ``owner`` is the GitHub owner argument a call names: a repository
namespace, never a caller key (deployments have no user ids, spec 8 D5). Every organisation
repository is owned by ``ORG_OWNER``, migrated ones included: the migration renames a
repository inside the organisation (``platform/<name>``) and never changes its owner. A
person's own repository outside the organisation is owned by ``account:<agent>`` (the classic
toxic flow's target). So a copy into a foreign owner (SEQ-2) happens in that gray kind only.

**Addresses.** v1-v4 draw a fresh host inside the /16 for every session. With
``sticky_addresses`` the /16 is unchanged (the Network dimension sees the same values) but
the host is the agent's egress address: one home address per agent (a new one with a new
ISP), a slot of a small NAT pool for the office and for each VPN (shared by everyone there,
the same slot for the same person), one address per hotel stay and per carrier day, one host
per triage or report bot, and a fresh runner per CI job. The draws of v1-v4 are still made,
so no other column moves.

Every number this module produces is synthetic; it is a development-world input, never a paper
number by itself.
"""

from __future__ import annotations

import functools
import hashlib
import math
import random
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import NamedTuple, TypeVar

T = TypeVar("T")

DAY, HOUR = 86_400.0, 3_600.0
BASE_DAY = 20_003  # 2024-10-07, a Monday: simulation day 0
N_DAYS = 180
VPN_CHANGE_DAY, ROLLOUT_DAY, MIGRATION_DAY = 110, 130, 150
CRUNCH_DAYS = range(120, 124)
GRAY_FROM, GRAY_TO = 95, 172
N_TEAMS = 10

# ts, method, session, tool, asset, sensitivity, operation, address, client, size, static,
# legit, gray
ROW = (
    "ts",
    "method",
    "session",
    "tool",
    "asset",
    "sens",
    "op",
    "address",
    "client",
    "size",
    "static",
    "legit",
    "gray",
)
#: EV-07, EV-09b: a v5 row adds the bytes of ``result.content`` the server returned (0 for a
#: housekeeping message), the asset's exposure and its owner (None without an asset)
ROW_V5 = (*ROW, "resp", "exposure", "owner")
RESP_COLUMN, EXPOSURE_COLUMN, OWNER_COLUMN = (
    ROW_V5.index(c) for c in ("resp", "exposure", "owner")
)

#: tool -> (operation, static level), from the github-helios static scan
TOOLS = {
    "create_or_update_file": ("write", 4),
    "search_repositories": ("read", 3),
    "create_repository": ("write", 4),
    "get_file_contents": ("read", 3),
    "push_files": ("write", 4),
    "create_issue": ("write", 4),
    "create_pull_request": ("write", 4),
    "fork_repository": ("write", 4),
    "create_branch": ("write", 4),
    "list_commits": ("metadata", 2),
    "list_issues": ("metadata", 2),
    "update_issue": ("write", 4),
    "add_issue_comment": ("write", 3),
    "search_code": ("read", 3),
    "search_issues": ("read", 3),
    "search_users": ("read", 3),
    "get_issue": ("read", 3),
    "get_pull_request": ("read", 3),
    "list_pull_requests": ("metadata", 2),
    "create_pull_request_review": ("write", 4),
    "merge_pull_request": ("write", 4),
    "get_pull_request_files": ("metadata", 2),
    "get_pull_request_status": ("metadata", 2),
    "update_pull_request_branch": ("write", 4),
    "get_pull_request_comments": ("read", 3),
    "get_pull_request_reviews": ("read", 3),
}
#: added by the server release on ROLLOUT_DAY
NEW_TOOLS = {
    "list_tags": ("metadata", 2),
    "get_workflow_runs": ("read", 3),
    "create_release": ("write", 4),
    "rerun_workflow": ("write", 4),
}
CATALOG = {**TOOLS, **NEW_TOOLS}
REVIEW_TOOLS = frozenset(
    {"get_pull_request", "get_pull_request_reviews", "get_pull_request_status"}
)
PAGED = frozenset({"list_issues", "list_pull_requests", "list_commits", "search_issues"})
NO_ASSET = frozenset({"search_repositories", "search_users"})

ROLE_TOOLS = {
    "dev": {
        "get_file_contents": 20,
        "search_code": 8,
        "get_issue": 6,
        "list_issues": 5,
        "get_pull_request": 6,
        "list_pull_requests": 4,
        "get_pull_request_files": 4,
        "get_pull_request_comments": 3,
        "list_commits": 3,
        "search_issues": 2,
        "create_or_update_file": 6,
        "push_files": 2,
        "create_branch": 2,
        "create_pull_request": 2,
        "add_issue_comment": 4,
        "update_issue": 2,
        "create_issue": 1.5,
        "create_pull_request_review": 1.5,
        "get_pull_request_status": 2,
        "get_pull_request_reviews": 1,
        "update_pull_request_branch": 0.5,
        "merge_pull_request": 0.3,
        "search_repositories": 0.3,
        "fork_repository": 0.05,
        "search_users": 0.1,
        "create_repository": 0.02,
    },
    "lead": {
        "get_pull_request": 10,
        "get_pull_request_files": 8,
        "get_pull_request_reviews": 6,
        "get_pull_request_status": 5,
        "create_pull_request_review": 6,
        "merge_pull_request": 3,
        "add_issue_comment": 5,
        "list_pull_requests": 6,
        "get_file_contents": 8,
        "list_issues": 4,
        "update_issue": 3,
        "search_issues": 2,
        "create_issue": 2,
        "search_code": 2,
        "get_issue": 3,
        "list_commits": 2,
        "search_users": 0.3,
        "search_repositories": 0.3,
    },
    "sre": {
        "get_file_contents": 15,
        "search_code": 8,
        "list_commits": 5,
        "create_or_update_file": 6,
        "create_pull_request": 3,
        "get_pull_request": 4,
        "create_branch": 2,
        "push_files": 2,
        "list_issues": 3,
        "get_issue": 3,
        "add_issue_comment": 3,
        "update_issue": 2,
        "merge_pull_request": 1,
        "get_pull_request_status": 2,
        "get_pull_request_reviews": 1,
        "list_pull_requests": 2,
        "search_repositories": 0.5,
    },
    "pm": {
        "list_issues": 10,
        "get_issue": 10,
        "search_issues": 8,
        "create_issue": 5,
        "update_issue": 5,
        "add_issue_comment": 6,
        "list_pull_requests": 3,
        "get_pull_request": 2,
        "search_repositories": 1,
        "get_file_contents": 1,
    },
}
ROLE_VOLUME = {"dev": 90, "lead": 60, "sre": 70, "pm": 40}
NEW_TOOL_INTEREST = {
    "dev": ("list_tags", "get_workflow_runs", "create_release", "rerun_workflow"),
    "lead": ("list_tags", "create_release"),
    "sre": ("get_workflow_runs", "rerun_workflow", "list_tags"),
    "pm": (),
}

OFFICE, VPN_OLD, VPN_NEW = (203, 0), (100, 70), (100, 90)
HOME_POOL = [(70 + i, 10) for i in range(40)]
CARRIER_POOL = [(100, 64 + i) for i in range(6)]
CLOUD_POOL = [(20, i) for i in range(60)] + [(3, i) for i in range(60)]
HUMAN_CLIENTS = ("claude-code", "cursor", "vscode-copilot")
GRAY_KINDS = {
    "bulk_export": 3,
    "sensitive_peek": 3,
    "slow_loop": 2,
    "mass_cleanup": 2,
    "off_hours_batch": 2,
    "cross_copy": 2,
    "big_paste": 1,
    "shadow_script": 2,
    "scope_creep": 2,
    "overfetch": 2,
}

# ── v5 constants ───────────────────────────────────────────────────────────────────────────
WORLD_V4, WORLD_V5 = "v4", "v5"
WORLD_VERSIONS = (WORLD_V4, WORLD_V5)
EVAL_FROM = 90  # the first scored day of a run (normal_org_sim.EVAL_FROM)
NEVER = 10**9  # a day that never comes: an org-wide change that is not in the calendar
MIN_N_DAYS = 120  # the late-hire window and the gray window need a horizon at least this long
DAYS_PER_YEAR, DAYS_PER_WEEK = 365, 7
STABLE_HASH_BYTES = 8  # EV-01: blake2b digest size
ORDER_MODULUS = 9973  # repo_prefs: the order key, as v1-v4 computed it from hash()
FIRST_PROJECT_WEEK = 3  # build_org: new project repositories from this week on

#: EV-09b exposure values (the engine's PUBLIC, INTERNAL, PRIVATE)
EXPOSURE_PUBLIC, EXPOSURE_INTERNAL, EXPOSURE_PRIVATE = "public", "internal", "private"
PRIVATE_FROM_SENS = 4  # an organisation repository this sensitive is private, else internal
PUBLIC_SENS = 1  # whatever is in a public repository is public
ORG_OWNER = "org"  # the owner of every organisation repository, migrated ones included
MIGRATED_NAMESPACE = "platform"  # a migrated repository is renamed "platform/<name>"
#: the owner of a person's own repository outside the organisation: a namespace label, never
#: a caller key
PERSONAL_OWNER_PREFIX = "account:"
TEAM_PUBLIC_REPOS = (2, 4)  # EV-09b: how many teams own a public repository, uniform
SHARED_PUBLIC_REPOS = ("oss-sdk", "docs-public")  # EV-09b: public repositories nobody owns

#: EV-06 org-wide changes, by name
VPN_CHANGE, TOOL_ROLLOUT, REPO_MIGRATION = "vpn_change", "tool_rollout", "repo_migration"
ORG_CHANGES = (VPN_CHANGE, TOOL_ROLLOUT, REPO_MIGRATION)

#: EV-07 response model. Synthetic: EV-26 measures real sizes from GH Archive.
RESPONSE_ENVELOPE_BYTES = 60  # the content wrapper around every result
DEFAULT_PER_PAGE, OVERFETCH_PER_PAGE = 30, 100
OVERFETCH_MEDIAN_ITEMS = 300  # an unfiltered list (state=all): almost every page is full
ITEM_COUNT_SIGMA = 0.9  # items a page returns: lognormal around the tool's median
SIZE_JITTER_SIGMA = 0.25  # one draw scales a whole page (items differ in size)
MAX_FILE_BYTES = 1_000_000  # the contents API returns files up to 1 MB
WRITE_ECHO_BYTES = (1_000, 3_000)  # a write echoes the object it made, uniform
#: list and search tools: (bytes per returned item, median items on a page)
LIST_RESPONSES = {
    "list_issues": (2_600, 12),
    "list_pull_requests": (5_200, 12),
    "list_commits": (1_400, 12),
    "get_pull_request_files": (2_200, 6),
    "get_pull_request_comments": (1_300, 5),
    "get_pull_request_reviews": (1_100, 3),
    "list_tags": (260, 12),
    "get_workflow_runs": (2_400, 12),
    "search_issues": (2_600, 8),
    "search_code": (900, 8),
    "search_repositories": (1_800, 8),
    "search_users": (450, 8),
}
#: single-object reads: (median bytes, lognormal sigma)
OBJECT_RESPONSES = {
    "get_file_contents": (4_000, 1.3),
    "get_issue": (3_500, 0.6),
    "get_pull_request": (6_500, 0.5),
    "get_pull_request_status": (1_500, 0.4),
}

#: EV-08 roster shares (150 agents give today's 21 bots and 10 hires)
BOT_SHARE = (14, 100)
HIRE_SHARE = (1, 15)
BOT_SPLIT = (("ci_bot", 12), ("triage_bot", 4), ("report_bot", 5))
PEOPLE_ROLES = ("dev", "lead", "sre", "pm")
PEOPLE_WEIGHTS = (62, 12, 14, 12)
EARLY_HIRE_DAYS = (30, 80)  # the first half of the hires start in this window
LATE_HIRE_FROM = 95  # ... the rest from this day to HIRE_END_MARGIN before the end
HIRE_END_MARGIN = 20  # make_person needs 20 days after a start for its own draws
LEGACY_CI_BOTS, LEGACY_BOT_LOOPS = 12, 3  # 3 of today's 12 CI bots get a stuck loop
MIN_TENURE_DAYS = 30  # EV-08 churn: a leaver stays at least this long
MAX_CHURN_PER_YEAR = 1.0
BOT_GRAY_RATE = 0.4  # EV-08: gray episodes per bot over the gray window (Poisson mean)

#: EV-09 variants
CLASSIC, PLAIN = "classic", "plain"
VARIANTS = (CLASSIC, PLAIN)
PLAIN_SHARE_V5 = 0.5  # held-out worlds mix plain and classic 1:1
ID_PARTS = 3  # an episode id is kind:agent:index, plus :variant once labelled
PLAIN_SESSION_INDEX = 99  # a plain episode's session id is shaped like an ordinary one
SESSION_RESUME_SHARE = 0.03  # 3% of a person's sessions resume without initialize
TOOLS_LIST_SHARE = 0.5  # half of a person's sessions list the tools after initialize
PERSON_INITIALIZE_LEAD_S = 1.0  # a person's initialize comes 1 s before the first call ...
PERSON_TOOLS_LIST_LEAD_S = 0.5  # ... and tools/list half a second before it
BOT_INITIALIZE_LEAD_S = 0.5  # a bot's job opens with initialize half a second before its call
TRAVEL_HOURS_AHEAD = 7  # a traveller works 7 hours ahead
#: plain cross_copy (the session split, N16): the writes come in a new session, this long
#: after the last read. Inside E5's 10-minute read-then-write window
#: (unsafe_sequence.SEQUENCE_WINDOW_S = 600 s), so the session-free check can see the copy and
#: v4's per-session check cannot. Waiting past the window is an adaptive kind (Part A E5, f11).
CROSS_COPY_PAUSE_S = (60.0, 540.0)
CROSS_COPY_READS, CROSS_COPY_WRITES = (3, 5), (2, 3)  # v1-v4's episode shape
CROSS_COPY_GAP_MEAN_S = 30.0

#: EV-09b: copy from a sensitive repository into a public one
TOXIC_FLOW = "toxic_flow"
GRAY_KINDS_V5 = {**GRAY_KINDS, TOXIC_FLOW: 2}
SCRATCH_REPO = "scratch"  # the classic toxic flow pushes into "<agent>/scratch-<day>"
TOXIC_FLOW_READS, TOXIC_FLOW_WRITES = (2, 5), (1, 3)  # reads of the source, writes after
TOXIC_FLOW_GAP_MEAN_S = 30.0  # between two calls of the episode, exponential
CREATE_REPOSITORY_GAP_MEAN_S = 60.0  # classic: after create_repository, before the first push

#: EV-08 bot gray kinds, by bot role
BOT_LOOP = "bot_loop"
BOT_TOKEN_REUSE = "bot_token_reuse"  # a person drives the bot's token
BOT_SCOPE_CREEP = "bot_scope_creep"  # a CI bot reads other teams' repositories
BOT_MISCONFIGURED_WRITER = "bot_misconfigured_writer"  # repeated update_issue
BOT_GRAY_KINDS = {
    "ci_bot": (BOT_TOKEN_REUSE, BOT_SCOPE_CREEP, BOT_MISCONFIGURED_WRITER),
    "triage_bot": (BOT_TOKEN_REUSE, BOT_MISCONFIGURED_WRITER),
    "report_bot": (BOT_TOKEN_REUSE,),
}
#: a bot's own hours (UTC): CI is busy on working hours, triage runs around the clock, the
#: report runs at 06:00
BOT_USUAL_HOURS = {"ci_bot": (7.0, 20.0), "triage_bot": (0.0, 24.0), "report_bot": (6.0, 6.1)}
TOKEN_REUSE_EVENING = (19.0, 23.0)  # classic token reuse: a person in the evening, from home
PERSON_LIKE_TOOLS = (
    "get_file_contents",
    "search_code",
    "get_issue",
    "list_pull_requests",
    "create_or_update_file",
)
TOKEN_REUSE_REPOS, TOKEN_REUSE_CALLS = (2, 5), (15, 50)  # the person's repositories and calls
TOKEN_REUSE_GAP_MEAN_S = 40.0
CREEP_TOOLS = ("get_file_contents", "list_commits", "get_pull_request")
BOT_CREEP_DAYS = 15  # plain CI scope creep lasts this many days
CLASSIC_CREEP_HOURS = (0.0, 5.0)  # classic CI scope creep runs at night
CLASSIC_CREEP_TARGETS, CLASSIC_CREEP_CALLS = (8, 15), (30, 60)  # one night burst
CLASSIC_CREEP_GAP_S = (1.0, 4.0)
PLAIN_CREEP_JOBS, PLAIN_CREEP_JOB_CALLS = (2, 6), (1, 3)  # per workday, and per extra job
PLAIN_CREEP_GAP_S = (0.5, 2.0)
CLASSIC_WRITER_CALLS, CLASSIC_WRITER_GAP_S = (200, 400), (1.0, 3.0)  # one tight loop
PLAIN_WRITER_CALLS, PLAIN_WRITER_JOB_CALLS = (60, 150), (1, 5)  # paced over job sessions
PLAIN_WRITER_GAP_S, PLAIN_WRITER_PAUSE_S = (0.5, 1.5), (60.0, 300.0)
#: the stuck CI loop (v1-v4's shape): its hours (UTC) and calls; classic calls are 1 s apart
BOT_LOOP_HOURS, BOT_LOOP_CALLS = (8.0, 18.0), (400, 800)
CLASSIC_LOOP_GAP_S = 1.0
PLAIN_LOOP_GAP_S = (0.5, 2.0)  # the plain loop keeps the bot's own jittered gaps

#: D5 sticky addresses: the office and each VPN egress through a NAT pool this large
NAT_POOL_SIZE = 4
NAT_NETWORKS = (OFFICE, VPN_OLD, VPN_NEW)
HOST_OCTET_3, HOST_OCTET_4 = 256, 254  # as :func:`ip` draws a host: x.y.[0, 255].[1, 254]


# ── v5 world switches, hashing and the calendar ───────────────────────────────────────────
@dataclass(frozen=True)
class WorldOptions:
    """Which v5 simulator changes are on. All off is the v1-v4 world (``LEGACY_OPTIONS``).

    ``stable_order`` (EV-01) orders repositories by :func:`stable_hash`; ``extended_rows``
    (EV-07, EV-09b) adds ``resp``, ``exposure`` and ``owner`` to every row (``ROW_V5``);
    ``scaled_roster`` (EV-08) sizes bots and hires by share; ``churn_per_year`` (EV-08) is the
    share of people who leave, and of new people who join, per year; ``bot_gray_rate`` (EV-08)
    is the mean number of gray episodes per bot; ``plain_share`` (EV-09) is the share of gray
    episodes in their plain variant (0 keeps v1-v4 episode ids); ``public_repos`` and
    ``toxic_flow`` (EV-09b) add public repositories and the toxic-flow kind;
    ``sticky_addresses`` (D5) gives each agent its egress address instead of a fresh host per
    session (module docstring, *Addresses*).
    """

    stable_order: bool = False
    extended_rows: bool = False
    scaled_roster: bool = False
    churn_per_year: float = 0.0
    bot_gray_rate: float = 0.0
    plain_share: float = 0.0
    public_repos: bool = False
    toxic_flow: bool = False
    sticky_addresses: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.churn_per_year <= MAX_CHURN_PER_YEAR:
            raise ValueError(f"churn_per_year {self.churn_per_year} not in [0, 1]")
        if self.bot_gray_rate < 0:
            raise ValueError(f"bot_gray_rate {self.bot_gray_rate} is negative")
        if not 0.0 <= self.plain_share <= 1.0:
            raise ValueError(f"plain_share {self.plain_share} not in [0, 1]")
        if self.toxic_flow and not self.public_repos:
            raise ValueError("toxic_flow needs public_repos: its plain variant writes to one")


LEGACY_OPTIONS = WorldOptions()
V5_OPTIONS = WorldOptions(
    stable_order=True,
    extended_rows=True,
    scaled_roster=True,
    churn_per_year=0.0,  # only the churn family (W8) turns it on, at 0.1-0.3
    bot_gray_rate=BOT_GRAY_RATE,
    plain_share=PLAIN_SHARE_V5,
    public_repos=True,
    toxic_flow=True,
    sticky_addresses=True,
)


def options_for(world_version: str) -> WorldOptions:
    """The switches of a world version: ``"v4"`` is today's world, ``"v5"`` every v5 change."""
    if world_version == WORLD_V4:
        return LEGACY_OPTIONS
    if world_version == WORLD_V5:
        return V5_OPTIONS
    raise ValueError(f"unknown world_version {world_version!r}; expected one of {WORLD_VERSIONS}")


def stable_hash(*parts: object) -> int:
    """EV-01: a hash that does not depend on ``PYTHONHASHSEED``: the blake2b digest (8 bytes,
    big-endian) of the parts' ``str`` joined by ``|``."""
    text = "|".join(str(part) for part in parts)
    digest = hashlib.blake2b(text.encode(), digest_size=STABLE_HASH_BYTES).digest()
    return int.from_bytes(digest, "big")


def stable_unit(*parts: object) -> float:
    """:func:`stable_hash` as a number in [0, 1)."""
    return stable_hash(*parts) / 2 ** (8 * STABLE_HASH_BYTES)


def stable_rng(*parts: object) -> random.Random:
    """A generator seeded by :func:`stable_hash` of the parts, for draws kept apart from an
    agent's main stream (so turning a feature on does not move the rest of the world)."""
    return random.Random(stable_hash(*parts))


@functools.lru_cache(maxsize=None)
def _stable_order_key(aid: str, team: int, name: str) -> int:
    return stable_hash(aid, team, name) % ORDER_MODULUS


@dataclass(frozen=True)
class Calendar:
    """EV-06: the days of the org-wide changes, the release crunch and the gray window.

    ``Calendar()`` is today's calendar (VPN change on day 110, tool rollout on 130, repository
    migration on 150, crunch 120-123, gray window 95-172 of 180 days), so it reproduces the
    v1-v4 worlds. A change not in ``changes_present`` never happens: its day stays recorded for
    provenance, and :attr:`vpn_at`, :attr:`rollout_at` and :attr:`migration_at` give ``NEVER``.
    """

    n_days: int = N_DAYS
    vpn_change_day: int = VPN_CHANGE_DAY
    rollout_day: int = ROLLOUT_DAY
    migration_day: int = MIGRATION_DAY
    crunch_start: int = CRUNCH_DAYS.start
    crunch_len: int = len(CRUNCH_DAYS)
    gray_from: int = GRAY_FROM
    gray_to: int = GRAY_TO
    changes_present: tuple[str, ...] = ORG_CHANGES

    def __post_init__(self) -> None:
        if self.n_days < MIN_N_DAYS:
            raise ValueError(f"n_days {self.n_days} < {MIN_N_DAYS}")
        for name in ("vpn_change_day", "rollout_day", "migration_day"):
            if not 0 <= getattr(self, name) < self.n_days:
                raise ValueError(f"{name} {getattr(self, name)} not in [0, {self.n_days})")
        if self.crunch_len < 0 or not 0 <= self.crunch_start <= self.n_days - self.crunch_len:
            raise ValueError(f"crunch {self.crunch_start}+{self.crunch_len} not in the horizon")
        if not 0 <= self.gray_from <= self.gray_to < self.n_days:
            raise ValueError(f"gray window {self.gray_from}-{self.gray_to} not in the horizon")
        unknown = [c for c in self.changes_present if c not in ORG_CHANGES]
        if unknown or len(set(self.changes_present)) != len(self.changes_present):
            raise ValueError(
                f"changes_present {self.changes_present} must be distinct of {ORG_CHANGES}"
            )

    def _at(self, change: str, day: int) -> int:
        return day if change in self.changes_present else NEVER

    @property
    def vpn_at(self) -> int:
        """The VPN change day, or ``NEVER``."""
        return self._at(VPN_CHANGE, self.vpn_change_day)

    @property
    def rollout_at(self) -> int:
        """The day the server release adds ``NEW_TOOLS``, or ``NEVER``."""
        return self._at(TOOL_ROLLOUT, self.rollout_day)

    @property
    def migration_at(self) -> int:
        """The day 12 team repositories are renamed ``platform/<name>``, or ``NEVER``."""
        return self._at(REPO_MIGRATION, self.migration_day)

    @property
    def crunch_days(self) -> range:
        """The release-crunch days."""
        return range(self.crunch_start, self.crunch_start + self.crunch_len)


DEFAULT_CALENDAR = Calendar()


@dataclass(frozen=True)
class CalendarRanges:
    """EV-06: the ranges a held-out calendar is drawn from (Part A's preregistered ranges).

    Change days ~ U{eval_from + change_from_offset, n_days - change_end_margin}, pairwise at
    least ``min_change_gap`` apart; each change is present with probability
    ``change_present_p``. Crunch start ~ U{eval_from, n_days - crunch_end_margin}. Gray window:
    from eval_from + U{gray_from_offsets}, to n_days - U{gray_end_margins}.
    """

    n_days: int = N_DAYS
    eval_from: int = EVAL_FROM
    change_from_offset: int = 5
    change_end_margin: int = 20
    min_change_gap: int = 7
    change_present_p: float = 0.8
    crunch_end_margin: int = 10
    crunch_len: int = len(CRUNCH_DAYS)
    gray_from_offsets: tuple[int, int] = (3, 10)
    gray_end_margins: tuple[int, int] = (5, 10)


def draw_calendar(rng: random.Random, ranges: CalendarRanges | None = None) -> Calendar:
    """EV-06: a random calendar from ``ranges``. The three change days are uniform over the
    sets that keep every pair ``min_change_gap`` apart (no rejection loop), in random order."""
    r = ranges or CalendarRanges()
    lo, hi = r.eval_from + r.change_from_offset, r.n_days - r.change_end_margin
    slack = (len(ORG_CHANGES) - 1) * (r.min_change_gap - 1)
    if hi - slack - lo + 1 < len(ORG_CHANGES):
        raise ValueError(f"change window {lo}-{hi} cannot hold gaps of {r.min_change_gap}")
    starts = sorted(rng.sample(range(lo, hi - slack + 1), len(ORG_CHANGES)))
    days = [z + i * (r.min_change_gap - 1) for i, z in enumerate(starts)]
    rng.shuffle(days)
    present = tuple(c for c in ORG_CHANGES if rng.random() < r.change_present_p)
    crunch_start = rng.randint(r.eval_from, r.n_days - r.crunch_end_margin)
    gray_from = r.eval_from + rng.randint(*r.gray_from_offsets)
    gray_to = r.n_days - rng.randint(*r.gray_end_margins)
    return Calendar(
        n_days=r.n_days,
        vpn_change_day=days[0],
        rollout_day=days[1],
        migration_day=days[2],
        crunch_start=crunch_start,
        crunch_len=r.crunch_len,
        gray_from=gray_from,
        gray_to=gray_to,
        changes_present=present,
    )


def seeded_calendar(seed: int, ranges: CalendarRanges | None = None) -> Calendar:
    """EV-06: the held-out calendar of the world with this seed (its own generator, so the
    world's other draws do not move)."""
    return draw_calendar(stable_rng(seed, "calendar"), ranges)


class Episode(NamedTuple):
    """A gray episode id, parsed: ``kind:agent:index`` (v1-v4) or ``kind:agent:index:variant``."""

    kind: str
    agent: str
    index: int
    variant: str


def episode_id(kind: str, agent: str, index: int, variant: str | None = None) -> str:
    """The ``gray`` column of an episode's rows; v1-v4 ids carry no variant."""
    base = f"{kind}:{agent}:{index}"
    return base if variant is None else f"{base}:{variant}"


def parse_episode(ep: str) -> Episode:
    """Split an episode id; an id without a variant is a classic episode."""
    parts = ep.split(":")
    if len(parts) == ID_PARTS:
        return Episode(parts[0], parts[1], int(parts[2]), CLASSIC)
    if len(parts) == ID_PARTS + 1 and parts[ID_PARTS] in VARIANTS:
        return Episode(parts[0], parts[1], int(parts[2]), parts[ID_PARTS])
    raise ValueError(f"not an episode id: {ep!r}")


def stratified_variants(episodes: Iterable[str], seed: int, plain_share: float) -> dict[str, str]:
    """EV-09: each unlabelled episode id (``kind:agent:index``) -> the id with its variant.

    Within each kind, the world's episodes are ordered by a stable hash of the world seed and
    the id, and the first ``floor(plain_share x k + u)`` of the kind's k episodes are plain,
    with ``u`` a stable uniform per kind. So each kind's split is within one episode of
    ``plain_share x k``, exact in expectation, and no generator moves. ``plain_share = 0``
    keeps the v1-v4 ids.
    """
    if not 0.0 <= plain_share <= 1.0:
        raise ValueError(f"plain_share {plain_share} not in [0, 1]")
    ids = list(episodes)
    if len(set(ids)) != len(ids):
        raise ValueError("episode ids must be distinct")
    by_kind: dict[str, list[str]] = {}
    for ep in ids:
        if len(ep.split(":")) != ID_PARTS:
            raise ValueError(f"{ep!r} is not an unlabelled episode id")
        by_kind.setdefault(parse_episode(ep).kind, []).append(ep)
    if plain_share == 0:
        return {ep: ep for ep in ids}
    labels: dict[str, str] = {}
    for kind, eps in by_kind.items():
        order = sorted(eps, key=lambda ep: (stable_hash(seed, "variant", ep), ep))
        n_plain = math.floor(plain_share * len(order) + stable_unit(seed, "variant", kind))
        for rank, ep in enumerate(order):
            labels[ep] = f"{ep}:{PLAIN if rank < n_plain else CLASSIC}"
    return labels


def row_names(options: WorldOptions) -> tuple[str, ...]:
    """The column names of a world's rows under ``options``."""
    return ROW_V5 if options.extended_rows else ROW


def world_digest(world: dict[str, list[tuple]], roles: dict[str, str] | None = None) -> str:
    """EV-01/EV-02: SHA-256 over the agents in sorted order, each agent's role and the
    ``repr`` of its rows (floats print shortest round-trip, so the digest is exact)."""
    h = hashlib.sha256()
    for aid in sorted(world):
        role = roles.get(aid) if roles is not None else None
        h.update(repr((aid, role)).encode())
        h.update(repr(world[aid]).encode())
    return h.hexdigest()


# ── profiles, repositories, roster ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Profile:
    """Org-level habits; the defaults are the main organisation."""

    file_write_kb: float = 2.5  # median file-write request, lognormal
    file_write_sigma: float = 1.2
    push_files_share: float = 1.0  # multiplier on push_files in people's habits
    paste_kb: tuple[int, int] = (100, 500)  # a big paste, uniform
    big_paste_weight: float = 1.0  # multiplier on big_paste among the gray kinds


#: "more git": other GitHub organisations for the size-per-tool check
PROFILES = {
    "main": Profile(),
    "more_pastes": Profile(paste_kb=(15, 100), big_paste_weight=4),
    "heavy_files": Profile(
        file_write_kb=8,
        file_write_sigma=1.3,
        push_files_share=3,
        paste_kb=(15, 100),
        big_paste_weight=4,
    ),
}


@dataclass
class Repo:
    """A repository. ``exposure`` defaults by sensitivity (EV-09b). ``owner`` is the owner a
    call names (module docstring, *Owners*); the migration renames a repository on its
    ``migration_day`` and keeps its owner."""

    name: str
    team: int | None
    sens: int
    created: int = 0
    migrated: bool = False
    exposure: str | None = None
    owner: str = ORG_OWNER
    migration_day: int = MIGRATION_DAY

    def __post_init__(self) -> None:
        if self.exposure is None:
            private = self.sens >= PRIVATE_FROM_SENS
            self.exposure = EXPOSURE_PRIVATE if private else EXPOSURE_INTERNAL

    def name_on(self, day: int) -> str:
        """The repository's name on ``day`` (migrated ones are renamed ``platform/<name>``)."""
        moved = self.migrated and day >= self.migration_day
        return f"{MIGRATED_NAMESPACE}/{self.name}" if moved else self.name


def personal_public_repo(aid: str, day: int) -> Repo:
    """EV-09b: a public repository a person makes outside the organisation (classic toxic
    flow's target), under the namespace ``account:<aid>`` (a repository owner, not a caller
    key)."""
    return Repo(
        f"{aid}/{SCRATCH_REPO}-{day}",
        None,
        PUBLIC_SENS,
        exposure=EXPOSURE_PUBLIC,
        owner=f"{PERSONAL_OWNER_PREFIX}{aid}",
    )


@dataclass
class Org:
    repos: list[Repo]
    team_repos: dict[int, list[Repo]]
    shared: list[Repo]
    sensitive5: list[Repo]
    infra: list[Repo]
    public: list[Repo] = field(default_factory=list)  # EV-09b
    calendar: Calendar = DEFAULT_CALENDAR  # EV-06

    def existing(self, day: int) -> list[Repo]:
        return [r for r in self.repos if r.created <= day]


def build_org(
    seed: int, *, calendar: Calendar = DEFAULT_CALENDAR, public_repos: bool = False
) -> Org:
    """The organisation's repositories. The v1-v4 draws come first and are unchanged; public
    repositories (EV-09b) are drawn after them, so the rest of the organisation stays put."""
    rng = random.Random(seed)
    repos, team_repos = [], {}
    for t in range(N_TEAMS):
        own = [Repo(f"t{t}-svc{i}", t, 2) for i in range(6)]
        own += [Repo(f"t{t}-tools", t, 3), Repo(f"t{t}-deploy", t, 4)]
        team_repos[t] = own
        repos += own
    shared = [
        Repo("docs-portal", None, 2),
        Repo("platform-lib-core", None, 2),
        Repo("platform-lib-ui", None, 2),
        Repo("platform-lib-auth", None, 3),
    ]
    infra = [
        Repo("infra-terraform", None, 4),
        Repo("infra-k8s", None, 4),
        Repo("security-policies", None, 4),
    ]
    sensitive5 = [
        Repo("secrets-config", None, 5),
        Repo("payroll-service", None, 5),
        Repo("customer-data-pipeline", None, 5),
    ]
    repos += shared + infra + sensitive5
    for week in range(FIRST_PROJECT_WEEK, calendar.n_days // 7):
        if rng.random() < 0.5:
            t = rng.randrange(N_TEAMS)
            r = Repo(f"t{t}-proj{week}", t, rng.choice((2, 2, 3)), week * 7 + rng.randrange(5))
            team_repos[t].append(r)
            repos.append(r)
    for r in rng.sample([r for r in repos if r.team is not None and r.created == 0], 12):
        r.migrated = True
        r.migration_day = calendar.migration_at
    public: list[Repo] = []
    if public_repos:
        for t in sorted(rng.sample(range(N_TEAMS), rng.randint(*TEAM_PUBLIC_REPOS))):
            r = Repo(f"t{t}-oss", t, PUBLIC_SENS, exposure=EXPOSURE_PUBLIC)
            team_repos[t].append(r)
            public.append(r)
        for name in SHARED_PUBLIC_REPOS:
            r = Repo(name, None, PUBLIC_SENS, exposure=EXPOSURE_PUBLIC)
            shared.append(r)
            public.append(r)
        repos += public
    return Org(repos, team_repos, shared, sensitive5, infra, public, calendar)


@dataclass
class Spec:
    """One agent of the roster. ``start`` > 0 is a hire's first day; ``end`` is a leaver's
    first day gone (EV-08 churn), None for an agent who stays."""

    aid: str
    role: str
    team: int
    idx: int
    start: int = 0
    end: int | None = None


def roster(n_agents: int, seed: int) -> list[Spec]:
    """About 86% people and 14% bots; ten new hires start during the run."""
    rng = random.Random(seed + 1)
    roles = ["ci_bot"] * 12 + ["triage_bot"] * 4 + ["report_bot"] * 5
    people = n_agents - len(roles) - 10
    roles += rng.choices(["dev", "lead", "sre", "pm"], [62, 12, 14, 12], k=people)
    specs = [Spec(f"{r}-{i:03d}", r, rng.randrange(N_TEAMS), i) for i, r in enumerate(roles)]
    for k in range(10):
        start = rng.randint(30, 80) if k < 5 else rng.randint(95, 160)
        i = len(specs)
        specs.append(Spec(f"dev-{i:03d}", "dev", rng.randrange(N_TEAMS), i, start))
    return specs


def _round_half_up(numerator: int, denominator: int) -> int:
    return (2 * numerator + denominator) // (2 * denominator)


def _split(total: int, parts: tuple[tuple[str, int], ...]) -> list[int]:
    """Largest-remainder split of ``total`` by the parts' weights; ties go to the first part."""
    weight = sum(w for _, w in parts)
    counts = [total * w // weight for _, w in parts]
    order = sorted(
        range(len(parts)), key=lambda i: (-(total * parts[i][1] % weight), i)
    )  # largest remainder first
    for i in order[: total - sum(counts)]:
        counts[i] += 1
    return counts


def scaled_roster(n_agents: int, seed: int, *, n_days: int = N_DAYS) -> list[Spec]:
    """EV-08: bots 14% of the agents (split 12:4:5 into CI, triage and report bots) and hires
    1/15, each at least 1; the rest are people. With 150 agents this is exactly
    :func:`roster`'s draw (21 bots, 10 hires, 119 people)."""
    n_bots = max(1, _round_half_up(n_agents * BOT_SHARE[0], BOT_SHARE[1]))
    n_hires = max(1, _round_half_up(n_agents * HIRE_SHARE[0], HIRE_SHARE[1]))
    people = n_agents - n_bots - n_hires
    if people < 1:
        raise ValueError(
            f"{n_agents} agents leave no regular people ({n_bots} bots, {n_hires} hires)"
        )
    rng = random.Random(seed + 1)
    roles: list[str] = []
    for (role, _), count in zip(BOT_SPLIT, _split(n_bots, BOT_SPLIT)):
        roles += [role] * count
    roles += rng.choices(PEOPLE_ROLES, PEOPLE_WEIGHTS, k=people)
    specs = [Spec(f"{r}-{i:03d}", r, rng.randrange(N_TEAMS), i) for i, r in enumerate(roles)]
    n_early = (n_hires + 1) // 2
    for k in range(n_hires):
        if k < n_early:
            start = rng.randint(*EARLY_HIRE_DAYS)
        else:
            start = rng.randint(LATE_HIRE_FROM, n_days - HIRE_END_MARGIN)
        i = len(specs)
        specs.append(Spec(f"dev-{i:03d}", "dev", rng.randrange(N_TEAMS), i, start))
    return specs


def add_churn(specs: list[Spec], seed: int, churn_per_year: float, n_days: int) -> list[Spec]:
    """EV-08 churn (family W8): people leave and new people join all through the run.

    Leavers and joiners are each Poisson with mean ``churn_per_year`` x people x n_days / 365.
    A leaver is a person (never a bot) who leaves on a day drawn after at least
    ``MIN_TENURE_DAYS``; a joiner gets a role from the people mix, a team and a first day in
    [1, n_days - 20]. Draws come from their own generator, so the rest of the roster is the
    one without churn.
    """
    if not 0.0 <= churn_per_year <= MAX_CHURN_PER_YEAR:
        raise ValueError(f"churn_per_year {churn_per_year} not in [0, 1]")
    out = list(specs)
    if churn_per_year == 0:
        return out
    rng = stable_rng(seed, "churn")
    people = [i for i, s in enumerate(out) if s.role in ROLE_TOOLS]
    mean = churn_per_year * len(people) * n_days / DAYS_PER_YEAR
    n_leave, n_join = poisson(rng, mean), poisson(rng, mean)
    for i in sorted(rng.sample(people, min(n_leave, len(people)))):
        first_possible = out[i].start + MIN_TENURE_DAYS
        if first_possible <= n_days - 1:
            out[i] = replace(out[i], end=rng.randint(first_possible, n_days - 1))
    for _ in range(n_join):
        role = rng.choices(PEOPLE_ROLES, PEOPLE_WEIGHTS)[0]
        team, start = rng.randrange(N_TEAMS), rng.randint(1, n_days - HIRE_END_MARGIN)
        i = len(out)
        out.append(Spec(f"{role}-{i:03d}", role, team, i, start))
    return out


def world_roster(
    n_agents: int,
    seed: int,
    *,
    options: WorldOptions = LEGACY_OPTIONS,
    calendar: Calendar = DEFAULT_CALENDAR,
) -> list[Spec]:
    """The roster :func:`build_world` uses: the v1-v4 one, or the scaled one plus churn.

    The v1-v4 roster draws its late hires up to day 160 whatever the horizon, and a hire needs
    20 days after his start, so it refuses a calendar shorter than ``N_DAYS``."""
    if not options.scaled_roster:
        if calendar.n_days < N_DAYS:
            raise ValueError(
                f"the v1-v4 roster needs n_days >= {N_DAYS} (got {calendar.n_days}); "
                "use the scaled roster (world_version='v5')"
            )
        specs = roster(n_agents, seed)
    else:
        specs = scaled_roster(n_agents, seed, n_days=calendar.n_days)
    return add_churn(specs, seed, options.churn_per_year, calendar.n_days)


def last_day(spec: Spec, calendar: Calendar) -> int:
    """The day after the agent's last day in the world."""
    return calendar.n_days if spec.end is None else min(spec.end, calendar.n_days)


def ip(net: tuple[int, int], rng: random.Random) -> str:
    return f"{net[0]}.{net[1]}.{rng.randrange(256)}.{rng.randrange(1, 255)}"


def egress_address(net: tuple[int, int], *key: object) -> str:
    """D5: a fixed host inside ``net`` for ``key``, in the range :func:`ip` draws from (a
    stable hash, so no generator moves)."""
    h = stable_hash("egress", net, *key)
    return f"{net[0]}.{net[1]}.{h % HOST_OCTET_3}.{1 + (h // HOST_OCTET_3) % HOST_OCTET_4}"


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    k, p, limit = 0, 1.0, math.exp(-lam)
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def request_size(tool: str, rng: random.Random, profile: Profile) -> int:
    op = CATALOG[tool][0]
    if tool in ("create_or_update_file", "push_files"):  # file contents
        median = profile.file_write_kb * 1000
        return int(300 + rng.lognormvariate(math.log(median), profile.file_write_sigma))
    if tool in (
        "create_issue",
        "add_issue_comment",
        "create_pull_request_review",
        "create_pull_request",
        "create_release",
    ):
        return int(250 + rng.lognormvariate(math.log(600), 1.0))
    return int(170 + rng.randrange(90)) if op != "write" else int(220 + rng.randrange(120))


def response_size(tool: str, rng: random.Random, *, overfetch: bool = False) -> int:
    """EV-07: bytes of ``result.content`` the server returns for one call of ``tool``.

    A list or search returns items x item bytes: ``perPage`` 30 and a filtered list (median 12
    items, 8 for a search), or, with ``overfetch``, ``perPage`` 100 on an unfiltered list.
    ``get_file_contents`` returns the file (lognormal, at most 1 MB), the other single reads one
    object, and a write echoes 1-3 KB. Synthetic sizes (EV-26 measures real ones).
    """
    if tool not in CATALOG:
        raise ValueError(f"unknown tool {tool!r}")
    if tool in LIST_RESPONSES:
        item_bytes, median = LIST_RESPONSES[tool]
        per_page = DEFAULT_PER_PAGE
        if overfetch:
            per_page, median = OVERFETCH_PER_PAGE, OVERFETCH_MEDIAN_ITEMS
        items = min(per_page, int(rng.lognormvariate(math.log(median), ITEM_COUNT_SIGMA)))
        page = items * item_bytes * rng.lognormvariate(0.0, SIZE_JITTER_SIGMA)
        return RESPONSE_ENVELOPE_BYTES + int(page)
    if tool in OBJECT_RESPONSES:
        median, sigma = OBJECT_RESPONSES[tool]
        body = min(MAX_FILE_BYTES, int(rng.lognormvariate(math.log(median), sigma)))
        return RESPONSE_ENVELOPE_BYTES + body
    if CATALOG[tool][0] == "write":
        return RESPONSE_ENVELOPE_BYTES + rng.randint(*WRITE_ECHO_BYTES)
    raise ValueError(f"no response model for {tool!r}")


def response_rng(seed: int, aid: str, options: WorldOptions) -> random.Random | None:
    """EV-07: the generator of an agent's response sizes, apart from its main stream (so the
    other columns are the same with or without them); None when rows are not extended."""
    return stable_rng(seed, aid, "resp") if options.extended_rows else None


def is_workday(day: int) -> bool:
    return day % 7 < 5


class Emitter:
    """Collects one agent's rows. With ``resp_rng`` (EV-07) every row is a ``ROW_V5`` row."""

    def __init__(
        self, rng: random.Random, profile: Profile, *, resp_rng: random.Random | None = None
    ) -> None:
        self.rng, self.rows, self.profile = rng, [], profile
        self.resp_rng = resp_rng

    def message(self, ts, method, session, address, client, legit="", gray=""):
        row = (
            ts,
            method,
            session,
            None,
            None,
            None,
            None,
            address,
            client,
            120 if method != "initialize" else 170,
            1,
            legit,
            gray,
        )
        if self.resp_rng is not None:
            row = (*row, 0, None, None)  # no result.content
        self.rows.append(row)

    def call(
        self,
        ts,
        session,
        tool,
        repo: Repo | None,
        day,
        address,
        client,
        legit="",
        gray="",
        size=None,
        *,
        overfetch: bool = False,
    ):
        op, static = CATALOG[tool]
        asset = repo.name_on(day) if repo is not None and tool not in NO_ASSET else None
        sens = repo.sens if repo is not None and asset else None
        tags = [legit] if legit else []
        if repo is not None and asset:
            if day - 14 <= repo.created <= day and repo.created > 0:
                tags.append("new_project")
            if repo.migrated and repo.migration_day <= day < repo.migration_day + 3:
                tags.append("org_repo_migration")
        row = (
            ts,
            "tools/call",
            session,
            tool,
            asset,
            sens,
            op,
            address,
            client,
            size if size is not None else request_size(tool, self.rng, self.profile),
            static,
            "|".join(tags),
            gray,
        )
        if self.resp_rng is not None:
            resp = response_size(tool, self.resp_rng, overfetch=overfetch)
            exposure = repo.exposure if repo is not None and asset else None
            owner = repo.owner if repo is not None and asset else None
            row = (*row, resp, exposure, owner)
        self.rows.append(row)


class _Session:
    """One gray episode's session: :meth:`call` emits a call at the session's clock ``t`` and
    moves the clock by ``gap``."""

    def __init__(
        self, em: Emitter, sid: str, address: str, client: str, day: int, ep: str, t: float
    ) -> None:
        self.em, self.sid, self.address, self.client = em, sid, address, client
        self.day, self.ep, self.t = day, ep, t
        self.last_call: float | None = None  # when the latest call was made

    def message(self, method: str, before: float) -> None:
        """A housekeeping message ``before`` seconds ahead of the first call."""
        self.em.message(self.t - before, method, self.sid, self.address, self.client, "", self.ep)

    def open_like_person(self, rng: random.Random) -> None:
        """EV-09: open the session the way the person opens an ordinary one (3% resume with
        no handshake; half of the others list the tools)."""
        if rng.random() > SESSION_RESUME_SHARE:
            self.message("initialize", PERSON_INITIALIZE_LEAD_S)
            if rng.random() < TOOLS_LIST_SHARE:
                self.message("tools/list", PERSON_TOOLS_LIST_LEAD_S)

    def call(
        self,
        tool: str,
        repo: Repo | None,
        gap: float,
        size: int | None = None,
        overfetch: bool = False,
    ) -> None:
        """Emit one call of ``tool`` on ``repo`` (``size``: its request bytes, else drawn)."""
        self.em.call(
            self.t,
            self.sid,
            tool,
            repo,
            self.day,
            self.address,
            self.client,
            "",
            self.ep,
            size,
            overfetch=overfetch,
        )
        self.last_call = self.t
        self.t += gap

    def follow_up(self, sid: str, pause: float) -> _Session:
        """A new session on the same address and client, ``pause`` seconds after this one's
        latest call (after its start if it made none)."""
        after = self.t if self.last_call is None else self.last_call
        return _Session(self.em, sid, self.address, self.client, self.day, self.ep, after + pause)


# ── people ─────────────────────────────────────────────────────────────────────────────────
@dataclass
class Person:
    spec: Spec
    rng: random.Random
    tz: float
    start_h: float
    span: float
    remote: bool
    desktop: bool
    family: str
    tetherer: bool
    home: tuple
    mean: float
    p_read_first: float
    weights: dict
    off: set = field(default_factory=set)
    back: set = field(default_factory=set)
    travel: dict = field(default_factory=dict)
    switch_day: int = 10**9
    switch_to: str = ""
    transfer: tuple = (10**9, 0)
    role_change: int = 10**9
    isp_change: tuple = (10**9, (0, 0))
    adopt: dict = field(default_factory=dict)
    vpn_tagged: bool = False
    calendar: Calendar = DEFAULT_CALENDAR  # EV-06
    sticky_seed: int | None = None  # D5: the world seed with sticky addresses, else None


def make_person(
    spec: Spec, rng: random.Random, profile: Profile, *, calendar: Calendar = DEFAULT_CALENDAR
) -> Person:
    n_days = calendar.n_days
    base = ROLE_TOOLS[spec.role]
    weights = {}
    for tool, w in base.items():
        if w < 1 and rng.random() < 0.5:
            continue  # personal habit: some rare tools he never uses
        weights[tool] = w * rng.lognormvariate(0, 0.5)
        if tool == "push_files":
            weights[tool] *= profile.push_files_share
    desktop = rng.random() < 0.25
    p = Person(
        spec,
        rng,
        rng.choice([0] * 7 + [-6, -6, 5.5]),
        rng.uniform(8, 10.5),
        rng.uniform(7, 9.5),
        rng.random() < 0.3,
        desktop,
        "claude-desktop" if desktop else rng.choice(HUMAN_CLIENTS),
        rng.random() < 0.15,
        rng.choice(HOME_POOL),
        ROLE_VOLUME[spec.role] * rng.lognormvariate(0, 0.4),
        rng.uniform(0.3, 0.7),
        weights,
        calendar=calendar,
    )
    for _ in range(rng.choice((1, 1, 2))):  # vacations
        a = rng.randint(spec.start + 10, n_days - 5)
        days = [d for d in range(a, a + 21) if is_workday(d)][: rng.randint(5, 12)]
        p.off.update(days)
        after = [d for d in range(days[-1] + 1, days[-1] + 8) if is_workday(d)][:2]
        p.back.update(after)
    p.off.update(d for d in range(spec.start, n_days) if is_workday(d) and rng.random() < 0.02)
    if rng.random() < 0.05:
        a = rng.randint(max(20, spec.start + 10), n_days - 10)
        hotel = (rng.randint(130, 220), rng.randrange(256))
        p.travel = {d: hotel for d in range(a, a + 7) if is_workday(d)}
    if not desktop and rng.random() < 0.25:
        p.switch_day = rng.randint(max(20, spec.start + 10), n_days - 5)
        p.switch_to = rng.choice([c for c in HUMAN_CLIENTS if c != p.family])
    if rng.random() < 0.04:
        p.transfer = (rng.randint(max(30, spec.start + 10), n_days - 10), rng.randrange(N_TEAMS))
    if spec.role == "dev" and rng.random() < 0.03:
        p.role_change = rng.randint(max(30, spec.start + 10), n_days - 10)
    if rng.random() < 0.05:
        p.isp_change = (rng.randint(max(20, spec.start + 10), n_days - 5), rng.choice(HOME_POOL))
    for tool in NEW_TOOL_INTEREST[spec.role]:
        if rng.random() < 0.35:
            p.adopt[tool] = rng.randint(calendar.rollout_at, calendar.rollout_at + 35)
    return p


def person_day_tags(p: Person, day: int) -> list[str]:
    tags = []
    if day in p.back:
        tags.append("back_from_vacation")
    if day in p.travel:
        tags.append("travel")
    if p.switch_day <= day < p.switch_day + 3:
        tags.append("client_switch")
    if p.transfer[0] <= day < p.transfer[0] + 14:
        tags.append("team_transfer")
    if p.role_change <= day < p.role_change + 14:
        tags.append("role_change")
    if p.isp_change[0] <= day < p.isp_change[0] + 3:
        tags.append("isp_change")
    if p.spec.start and day < p.spec.start + 21:
        tags.append("new_hire")
    if day in p.calendar.crunch_days and p.spec.role in ("dev", "lead"):
        tags.append("release_crunch")
    return tags


def repo_prefs(
    p: Person, org: Org, day: int, rng: random.Random, *, stable_order: bool = False
) -> list[tuple[Repo, float]]:
    """The person's repositories today and their weights. Their order (most used first) comes
    from Python's salted ``hash()`` in v1-v4 and from :func:`stable_hash` with ``stable_order``
    (EV-01)."""
    team = p.transfer[1] if day >= p.transfer[0] else p.spec.team
    role = "sre" if day >= p.role_change else p.spec.role
    own = [r for r in org.team_repos[team] if r.created <= day]
    if stable_order:
        order = sorted(own, key=lambda r: _stable_order_key(p.spec.aid, team, r.name))
    else:  # v1-v4: reproducible only under a fixed PYTHONHASHSEED
        order = sorted(own, key=lambda r: hash((p.spec.aid, team, r.name)) % ORDER_MODULUS)
    prefs = []
    for i, r in enumerate(order):
        w = 1 / (i + 1) ** 1.1
        if r.created > 0 and day - r.created < 60:
            w = 1.0  # a new project is where the work is
        if r.sens >= 4:
            w = 0.03 if role != "sre" else 0.3
        prefs.append((r, w))
    prefs += [(r, 0.05) for r in org.shared]
    if role == "sre":
        prefs += [(r, 0.4) for r in org.infra] + [(org.sensitive5[0], 0.05)]
    if p.spec.start and day < p.spec.start + 14:  # a new hire explores widely
        others = [r for r in org.existing(day) if r.sens < 5]
        prefs += [(r, 0.3) for r in rng.sample(others, min(12, len(others)))]
    return prefs


def pick(rng: random.Random, items: list[tuple[T, float]]) -> T:
    total = sum(w for _, w in items)
    x = rng.random() * total
    for item, w in items:
        x -= w
        if x <= 0:
            return item
    return items[-1][0]


def person_network(p: Person, day: int, rng: random.Random) -> tuple[int, int]:
    if day in p.travel:
        return p.travel[day]
    home = p.isp_change[1] if day >= p.isp_change[0] else p.home
    vpn = VPN_NEW if day >= p.calendar.vpn_at else VPN_OLD
    x = rng.random()
    if p.tetherer and x < 0.04:
        return rng.choice(CARRIER_POOL)
    if not p.remote and is_workday(day):
        return OFFICE if x < 0.75 else (vpn if x < 0.9 else home)
    return home if x < 0.78 else vpn


def home_network(p: Person, day: int) -> tuple[int, int]:
    """The person's home /16 on ``day`` (after an ISP change, the new one)."""
    return p.isp_change[1] if day >= p.isp_change[0] else p.home


def usual_network(p: Person, day: int, rng: random.Random) -> tuple[int, int]:
    """EV-09: a network from the person's ordinary mix, never the rare carrier hop."""
    net = person_network(p, day, rng)
    return home_network(p, day) if net in CARRIER_POOL else net


def person_egress(p: Person, net: tuple[int, int], day: int) -> str:
    """D5: the person's egress address on ``net`` on ``day`` (needs ``p.sticky_seed``): the
    office's or a VPN's NAT pool slot (the same slot for the same person), one address per
    carrier day, one per hotel stay, else the home address of the day's ISP."""
    seed, aid = p.sticky_seed, p.spec.aid
    if seed is None:
        raise ValueError("person_egress needs sticky addresses (p.sticky_seed)")
    if net in NAT_NETWORKS:
        slot = stable_hash(seed, aid, "nat", net) % NAT_POOL_SIZE
        return egress_address(net, seed, "nat", slot)
    if net in CARRIER_POOL:
        return egress_address(net, seed, aid, "carrier", day)
    if p.travel.get(day) == net:
        return egress_address(net, seed, aid, "hotel")
    return egress_address(net, seed, aid, "home", day >= p.isp_change[0])


def person_address(p: Person, net: tuple[int, int], day: int, rng: random.Random) -> str:
    """The address of one of the person's sessions on ``net``: v1-v4's fresh host, or with
    sticky addresses the person's egress address (:func:`person_egress`). The host is drawn
    either way, so no other column moves."""
    address = ip(net, rng)
    return address if p.sticky_seed is None else person_egress(p, net, day)


def gen_person(
    spec: Spec,
    org: Org,
    seed: int,
    gray_plan: list,
    profile: Profile,
    *,
    options: WorldOptions = LEGACY_OPTIONS,
) -> list[tuple]:
    cal = org.calendar
    rng = random.Random(seed * 1_000_003 + spec.idx)
    p = make_person(spec, rng, profile, calendar=cal)
    if options.sticky_addresses:
        p.sticky_seed = seed
    em = Emitter(rng, profile, resp_rng=response_rng(seed, spec.aid, options))
    sre_rota = spec.idx % 6
    gray_by_day: dict[int, list] = {}
    for day, kind, ep in gray_plan:
        gray_by_day.setdefault(day, []).append((kind, ep))
    creep: dict[int, str] = {}
    for d in range(spec.start, last_day(spec, cal)):
        tags = person_day_tags(p, d)
        family = p.switch_to if d >= p.switch_day else p.family
        client = f"{family}/1.{d // 30}.{rng.randrange(4)}"
        role = "sre" if d >= p.role_change else spec.role
        weights = dict(
            p.weights
            if role == spec.role
            else {t: w * rng.lognormvariate(0, 0.3) for t, w in ROLE_TOOLS["sre"].items()}
        )
        for tool, day0 in p.adopt.items():
            if d >= day0:
                weights[tool] = 1.5
        if spec.start and d < spec.start + 10:
            weights = {t: max(w, 1.0) for t, w in ROLE_TOOLS[spec.role].items()}
        prefs = repo_prefs(p, org, d, rng, stable_order=options.stable_order)
        for kind, ep in gray_by_day.get(d, ()):
            if kind == "scope_creep":  # already plain: extra reads inside ordinary sessions
                for k in range(15):
                    creep[d + k] = ep
            else:
                variant = parse_episode(ep).variant
                gray_episode(em, p, org, d, kind, ep, client, prefs, rng, variant=variant)
        working = d not in p.off and (is_workday(d) or rng.random() < 0.06)
        if role == "sre" and (d // 7) % 6 == sre_rota and rng.random() < 0.25:
            incident(em, p, org, d, client, rng)
        if not working:
            continue
        volume = p.mean * rng.lognormvariate(0, 0.45)
        if not is_workday(d):
            volume *= 0.25
        if "release_crunch" in tags:
            volume *= 2.3
        if spec.start and d < spec.start + 10:
            volume *= 1.2
        n_calls = max(3, int(volume))
        end_h = p.start_h + p.span + (4 if "release_crunch" in tags else 0)
        tz = p.tz + (TRAVEL_HOURS_AHEAD if d in p.travel else 0)
        day_tag = "|".join(tags)
        if p.desktop:
            plan = [(p.start_h + rng.uniform(0, 0.5), end_h, n_calls)]
        else:
            k = min(n_calls, 1 + poisson(rng, 2.5))
            starts = sorted(rng.uniform(p.start_h, end_h - 0.3) for _ in range(k))
            cuts = sorted(rng.random() for _ in range(k - 1))
            parts = [b - a for a, b in zip([0, *cuts], [*cuts, 1])]
            plan = [
                (s, min(end_h, s + 1.5), max(1, int(n_calls * f))) for s, f in zip(starts, parts)
            ]
        for i, (h0, h1, n) in enumerate(plan):
            net = person_network(p, d, rng)
            if family in HUMAN_CLIENTS or family == "claude-desktop":
                if p.vpn_tagged is False and net == VPN_NEW:
                    p.vpn_tagged = True
                    day_tag = "|".join([*tags, "org_vpn_change"])
            sid = f"{spec.aid}-{d}-{i}"
            t = (BASE_DAY + d) * DAY + (h0 - tz) * HOUR
            address = person_address(p, net, d, rng)
            if rng.random() > SESSION_RESUME_SHARE:  # 3% of sessions resume without initialize
                em.message(
                    t - PERSON_INITIALIZE_LEAD_S, "initialize", sid, address, client, day_tag
                )
                if rng.random() < TOOLS_LIST_SHARE:
                    em.message(
                        t - PERSON_TOOLS_LIST_LEAD_S, "tools/list", sid, address, client, day_tag
                    )
            gap = (h1 - h0) * HOUR / max(1, n) if p.desktop else None
            primary, secondary = pick(rng, prefs), pick(rng, prefs)
            for _ in range(n):
                tool = pick(rng, list(weights.items()))
                x = rng.random()
                repo = (
                    primary
                    if x < 0.8
                    else secondary
                    if x < 0.95
                    else (
                        rng.choice(org.shared)
                        if rng.random() < 0.6
                        else rng.choice([r for r in org.existing(d) if r.sens < 5])
                    )
                )
                if d in creep and rng.random() < 0.05:
                    others = [r for r in org.existing(d) if r.team not in (None, p.spec.team)]
                    em.call(
                        t,
                        sid,
                        "get_file_contents",
                        rng.choice(others),
                        d,
                        address,
                        client,
                        day_tag,
                        creep[d],
                    )
                    t += rng.expovariate(1 / 15)
                if tool in ("search_code", "search_issues") and rng.random() < 0.4:
                    repo = None
                legit = day_tag
                if tool in NEW_TOOLS and d < p.adopt.get(tool, 0) + 2:
                    legit = "|".join(x for x in (day_tag, "org_tool_rollout") if x)
                if (
                    CATALOG[tool][0] == "write"
                    and repo is not None
                    and rng.random() < p.p_read_first
                ):
                    em.call(t, sid, "get_file_contents", repo, d, address, client, legit)
                    t += rng.expovariate(1 / 10)
                if tool == "merge_pull_request" and rng.random() < 0.85:
                    em.call(t, sid, "get_pull_request_status", repo, d, address, client, legit)
                    t += rng.expovariate(1 / 10)
                em.call(t, sid, tool, repo, d, address, client, legit)
                if tool in PAGED and rng.random() < 0.3:
                    for _ in range(rng.randint(1, 5)):
                        t += rng.uniform(1, 2.5)
                        em.call(t, sid, tool, repo, d, address, client, legit)
                if gap:
                    t += gap * rng.uniform(0.3, 1.7)
                else:
                    t += rng.expovariate(1 / 20) if rng.random() > 0.1 else rng.expovariate(1 / 240)
    em.rows.sort(key=lambda r: r[0])
    return em.rows


def incident(em: Emitter, p: Person, org: Org, d: int, client: str, rng: random.Random) -> None:
    """An on-call night: 30-80 calls on infra and deploy repositories around 02:00 local."""
    sid = f"{p.spec.aid}-{d}-inc"
    t = (BASE_DAY + d) * DAY + (2 + rng.uniform(0, 2) - p.tz) * HOUR
    address = person_address(p, person_network(p, d, rng), d, rng)
    em.message(t - 1, "initialize", sid, address, client, "on_call_incident")
    deploy = next(r for r in org.team_repos[p.spec.team] if r.name.endswith("-deploy"))
    repos = org.infra + [deploy, org.sensitive5[0]]
    tools = {
        "get_file_contents": 10,
        "list_commits": 4,
        "search_code": 4,
        "create_or_update_file": 2,
        "create_pull_request": 1,
        "merge_pull_request": 1,
        "get_pull_request": 1,
    }
    for _ in range(rng.randint(30, 80)):
        repo = rng.choice(repos[:4]) if rng.random() < 0.9 else repos[4]
        em.call(
            t, sid, pick(rng, list(tools.items())), repo, d, address, client, "on_call_incident"
        )
        t += 2 if rng.random() < 0.2 else rng.expovariate(1 / 40)


def gray_episode(
    em: Emitter,
    p: Person,
    org: Org,
    d: int,
    kind: str,
    ep: str,
    client: str,
    prefs: list,
    rng: random.Random,
    *,
    variant: str = CLASSIC,
) -> None:
    """One risky-but-not-an-attack episode on day ``d``.

    The classic variant is the v1-v4 episode: its own session that always opens with
    ``initialize``, and for some kinds a giveaway (the weekend batch at 02:00, the shadow script
    at night from a cloud network with ``python-requests`` and no handshake). The plain
    variant (EV-09) keeps the person's usual hours, network and client and opens its session
    the way the person opens ordinary ones.
    """
    if variant == PLAIN:
        _plain_gray_episode(em, p, org, d, kind, ep, client, prefs, rng)
        return
    if variant != CLASSIC:
        raise ValueError(f"unknown variant {variant!r}")
    sid = f"{p.spec.aid}-{d}-g"
    hour = p.start_h + rng.uniform(1, max(1.5, p.span - 2))
    if kind == "off_hours_batch":
        hour = 2 + rng.uniform(0, 1)
    if kind == "shadow_script":
        hour = 1 + rng.uniform(0, 2)
    t = (BASE_DAY + d) * DAY + (hour - p.tz) * HOUR
    net = person_network(p, d, rng)
    own = [r for r, _ in prefs if r.team is not None and r.sens < 4] or [prefs[0][0]]
    if kind == "shadow_script":
        net, client = rng.choice(CLOUD_POOL), "python-requests/2.32"
        address = ip(net, rng)  # a cloud host, fresh for each run of the script
    else:
        address = person_address(p, net, d, rng)
    session = _Session(em, sid, address, client, d, ep, t)
    if kind != "shadow_script":
        session.message("initialize", 1.0)
    _episode_body(kind, session, p, org, d, own, prefs, rng, CLASSIC)


def _plain_gray_episode(
    em: Emitter,
    p: Person,
    org: Org,
    d: int,
    kind: str,
    ep: str,
    client: str,
    prefs: list,
    rng: random.Random,
) -> None:
    """EV-09: the plain variant. Hour: a usual working hour, in the day's time zone (a
    traveller's too). Network: the usual mix (the shadow script runs on the home /16), with
    the person's own address there under sticky addresses. Client: the person's own. Session:
    shaped like an ordinary one, opened like one."""
    tz = p.tz + (TRAVEL_HOURS_AHEAD if d in p.travel else 0)
    hour = p.start_h + rng.uniform(1, max(1.5, p.span - 2))
    t = (BASE_DAY + d) * DAY + (hour - tz) * HOUR
    net = home_network(p, d) if kind == "shadow_script" else usual_network(p, d, rng)
    own = [r for r, _ in prefs if r.team is not None and r.sens < 4] or [prefs[0][0]]
    sid = f"{p.spec.aid}-{d}-{PLAIN_SESSION_INDEX}"
    session = _Session(em, sid, person_address(p, net, d, rng), client, d, ep, t)
    session.open_like_person(rng)
    _episode_body(kind, session, p, org, d, own, prefs, rng, PLAIN)


def _episode_body(
    kind: str,
    s: _Session,
    p: Person,
    org: Org,
    d: int,
    own: list[Repo],
    prefs: list,
    rng: random.Random,
    variant: str,
) -> None:
    """The calls of one person's gray episode; the classic branches are v1-v4's, draw for draw
    (with ``public_repos`` off: cross_copy never writes into a public repository, so it stays
    apart from the toxic flow)."""
    call = s.call
    if kind == "bulk_export":
        targets = rng.sample(org.existing(d), min(len(org.existing(d)), rng.randint(20, 40)))
        for _ in range(rng.randint(60, 120)):
            call(
                rng.choice(("list_issues", "get_issue", "list_pull_requests", "get_file_contents")),
                rng.choice(targets),
                rng.expovariate(1 / 45),
            )
    elif kind == "sensitive_peek":
        target = rng.choice(org.sensitive5)
        for _ in range(rng.randint(2, 6)):
            call(rng.choice(("get_file_contents", "search_code")), target, rng.expovariate(1 / 60))
    elif kind == "slow_loop":
        repo, tool = (
            rng.choice(own),
            rng.choice(("get_pull_request_status", "get_issue", "list_commits")),
        )
        for _ in range(rng.randint(120, 300)):
            call(tool, repo, rng.uniform(6, 10))
    elif kind == "mass_cleanup":
        for _ in range(rng.randint(40, 80)):
            call("update_issue", rng.choice(own), rng.expovariate(1 / 40))
    elif kind == "off_hours_batch":
        for _ in range(rng.randint(40, 80)):
            call(
                rng.choice(("get_file_contents", "list_issues", "list_commits")),
                rng.choice(own),
                rng.uniform(5, 20),
            )
    elif kind == "cross_copy":
        source = rng.choice(org.infra + [org.sensitive5[0]])
        for _ in range(rng.randint(*CROSS_COPY_READS)):
            s.call("get_file_contents", source, rng.expovariate(1 / CROSS_COPY_GAP_MEAN_S))
        if variant == PLAIN:  # the session split: the writes come in a new session, in E5's window
            s = s.follow_up(
                f"{p.spec.aid}-{d}-{PLAIN_SESSION_INDEX + 1}", rng.uniform(*CROSS_COPY_PAUSE_S)
            )
            s.open_like_person(rng)
        targets = [r for r in own if r.exposure != EXPOSURE_PUBLIC]  # a public one: toxic flow
        for _ in range(rng.randint(*CROSS_COPY_WRITES)):
            s.call(
                "create_or_update_file",
                rng.choice(targets),
                rng.expovariate(1 / CROSS_COPY_GAP_MEAN_S),
            )
    elif kind == "big_paste":
        lo, hi = s.em.profile.paste_kb
        call("create_issue", rng.choice(own), 5, size=rng.randint(lo * 1000, hi * 1000))
    elif kind == "shadow_script":
        others = rng.sample(org.existing(d), 6)
        for _ in range(rng.randint(50, 150)):
            call(
                rng.choice(("list_issues", "get_issue", "get_file_contents")),
                rng.choice(own + others),
                rng.uniform(2, 6),
            )
    elif kind == "overfetch":
        for _ in range(20):
            call("list_issues", rng.choice(own), rng.uniform(2, 8), size=290, overfetch=True)
    elif kind == TOXIC_FLOW:
        _toxic_flow(s, p, org, d, prefs, rng, variant)
    else:
        raise ValueError(f"unknown gray kind {kind!r}")


def _toxic_flow(
    s: _Session, p: Person, org: Org, d: int, prefs: list, rng: random.Random, variant: str
) -> None:
    """EV-09b: read a sensitive repository (sensitivity 4-5), then write into a public one.
    Classic: a new personal public repository outside the organisation (``create_repository``
    then ``push_files``). Plain: an organisation public repository the person's team owns, or a
    shared one, with an ordinary ``create_or_update_file``."""
    if not org.public:
        raise ValueError("toxic_flow needs an organisation with public repositories")
    source = rng.choice(org.sensitive5 + org.infra)
    for _ in range(rng.randint(*TOXIC_FLOW_READS)):
        s.call("get_file_contents", source, rng.expovariate(1 / TOXIC_FLOW_GAP_MEAN_S))
    if variant == PLAIN:
        team_public = [r for r, _ in prefs if r.exposure == EXPOSURE_PUBLIC and r.team is not None]
        target = rng.choice(team_public or org.public)
        for _ in range(rng.randint(*TOXIC_FLOW_WRITES)):
            s.call("create_or_update_file", target, rng.expovariate(1 / TOXIC_FLOW_GAP_MEAN_S))
        return
    target = personal_public_repo(p.spec.aid, d)
    s.call("create_repository", target, rng.expovariate(1 / CREATE_REPOSITORY_GAP_MEAN_S))
    for _ in range(rng.randint(*TOXIC_FLOW_WRITES)):
        s.call("push_files", target, rng.expovariate(1 / TOXIC_FLOW_GAP_MEAN_S))


def gray_plan_for(
    spec: Spec,
    rng: random.Random,
    profile: Profile,
    *,
    calendar: Calendar = DEFAULT_CALENDAR,
    kinds: dict[str, float] | None = None,
) -> list[tuple[int, str, str]]:
    """A person's gray episodes: ``(day, kind, episode id)``, ids without a variant. ``kinds``
    defaults to ``GRAY_KINDS``; v5 passes ``GRAY_KINDS_V5`` (with the toxic flow). The weekend
    batch moves to its week's Saturday, or to the Saturday before when that one is past the
    horizon (never with today's calendar, so v1-v4 plans are unchanged)."""
    if spec.role not in ROLE_TOOLS or spec.start + 21 > calendar.gray_to:
        return []  # bots, and new hires who start too late for a gray episode
    weighted = [
        (k, w * (profile.big_paste_weight if k == "big_paste" else 1))
        for k, w in (GRAY_KINDS if kinds is None else kinds).items()
    ]
    plan = []
    for i in range(poisson(rng, 0.6)):
        kind = pick(rng, weighted)
        day = rng.randint(max(calendar.gray_from, spec.start + 21), calendar.gray_to)
        if kind == "off_hours_batch":
            day = day - day % 7 + 5  # a Saturday
            if day >= calendar.n_days:
                day -= DAYS_PER_WEEK  # the Saturday before: this week's is past the horizon
        elif not is_workday(day):
            day -= day % 7 - 4  # the Friday before
        if day >= spec.start + 21:
            plan.append((day, kind, episode_id(kind, spec.aid, i)))
    return plan


# ── bots ───────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class BotHabits:
    """What a bot ordinarily looks like, for its gray episodes (EV-08).

    ``initializes`` is False exactly for a stateless bot (a CI or triage bot whose jobs send
    no ``initialize``). Today every job, a stateless bot's too, carries a session id. Note for
    EV-04 (e) (Batch 2): once a stateless bot's calls carry no session id,
    :func:`_plain_bot_session` must drop the id too when ``initializes`` is False, or its
    plain episodes become its only calls with a session.
    """

    role: str
    client: str
    networks: tuple[tuple[int, int], ...]
    initializes: bool  # it opens each session with initialize
    teams: tuple[int, ...]  # a CI bot's teams
    #: D5: the bot's fixed host under sticky addresses (triage and report bots); None draws a
    #: fresh host for each job (CI runners, and every bot in v1-v4)
    address: str | None = None


def bot_address(habits: BotHabits, rng: random.Random) -> str:
    """The address of one of the bot's jobs: a fresh host on one of its networks, or its fixed
    host (``habits.address``). The host is drawn either way, so no other column moves."""
    address = ip(rng.choice(habits.networks), rng)
    return address if habits.address is None else habits.address


def bot_gray_plan_for(
    spec: Spec, seed: int, calendar: Calendar, rate: float
) -> list[tuple[int, str, str]]:
    """EV-08: a bot's gray episodes ``(day, kind, episode id)``, Poisson(``rate``) of the kinds
    its role allows (``BOT_GRAY_KINDS``), on a workday of the gray window. The ids carry no
    variant: :func:`build_world` labels them with the world's (:func:`stratified_variants`)."""
    kinds = BOT_GRAY_KINDS.get(spec.role, ())
    if not kinds or rate <= 0:
        return []
    rng = stable_rng(seed, spec.aid, "bot_gray_plan")
    plan = []
    for i in range(poisson(rng, rate)):
        kind = kinds[rng.randrange(len(kinds))]
        day = rng.randint(calendar.gray_from, calendar.gray_to)
        if not is_workday(day):
            day -= day % 7 - 4  # the Friday before
        plan.append((day, kind, episode_id(kind, spec.aid, i)))
    return plan


def _bot_repos(habits: BotHabits, spec: Spec, org: Org, d: int) -> list[Repo]:
    """The repositories the bot ordinarily works on, on day ``d``."""
    if habits.role == "ci_bot":
        return [r for tm in habits.teams for r in org.team_repos[tm] if r.created <= d]
    if habits.role == "report_bot":
        return [r for r in org.team_repos[spec.team] if r.created <= d]
    return org.existing(d)


def _plain_bot_session(
    em: Emitter, spec: Spec, habits: BotHabits, d: int, t: float, ep: str, rng: random.Random
) -> _Session:
    """A session shaped and opened like one of the bot's ordinary jobs: its id, address and
    client, and ``initialize`` half a second ahead exactly when the bot's jobs send one (see
    :class:`BotHabits` for stateless bots)."""
    sid = f"{spec.aid}-{d}-{int((t / HOUR) % 24)}-{rng.randrange(10**6)}"
    session = _Session(em, sid, bot_address(habits, rng), habits.client, d, ep, t)
    if habits.initializes:
        session.message("initialize", BOT_INITIALIZE_LEAD_S)
    return session


def _usual_bot_time(habits: BotHabits, d: int, rng: random.Random) -> float:
    return (BASE_DAY + d) * DAY + rng.uniform(*BOT_USUAL_HOURS[habits.role]) * HOUR


def bot_gray_episode(
    em: Emitter,
    spec: Spec,
    org: Org,
    d: int,
    kind: str,
    ep: str,
    habits: BotHabits,
    rng: random.Random,
) -> None:
    """EV-08: one bot gray episode on day ``d``; its variant comes from the episode id.

    - token reuse: a person drives the bot's token with person-like reads and a few writes;
      classic from a home network in the evening with a human client, plain with the bot's own
      client, networks and hours;
    - CI scope creep: reads of other teams' repositories; classic is one night burst from a
      cloud network outside the bot's pool, plain is 15 days of small extra jobs;
    - misconfigured writer: repeated ``update_issue`` on one repository; classic is a tight
      loop in one session, plain is paced over job-shaped sessions.
    """
    variant = parse_episode(ep).variant
    if kind == BOT_TOKEN_REUSE:
        pool = [r for r in org.existing(d) if r.sens < 5]
        repos = rng.sample(pool, min(len(pool), rng.randint(*TOKEN_REUSE_REPOS)))
        if variant == CLASSIC:
            t = (BASE_DAY + d) * DAY + rng.uniform(*TOKEN_REUSE_EVENING) * HOUR
            address = ip(rng.choice(HOME_POOL), rng)  # someone's home, not the bot's network
            client = f"{rng.choice(HUMAN_CLIENTS)}/1.{d // 30}.{rng.randrange(4)}"
            s = _Session(em, f"{spec.aid}-{d}-g", address, client, d, ep, t)
            s.message("initialize", PERSON_INITIALIZE_LEAD_S)
        else:
            s = _plain_bot_session(em, spec, habits, d, _usual_bot_time(habits, d, rng), ep, rng)
        for _ in range(rng.randint(*TOKEN_REUSE_CALLS)):
            s.call(
                rng.choice(PERSON_LIKE_TOOLS),
                rng.choice(repos),
                rng.expovariate(1 / TOKEN_REUSE_GAP_MEAN_S),
            )
    elif kind == BOT_SCOPE_CREEP:
        if variant == CLASSIC:
            other = _other_team_repos(habits, org, d)
            outside = [n for n in CLOUD_POOL if n not in habits.networks] or CLOUD_POOL
            t = (BASE_DAY + d) * DAY + rng.uniform(*CLASSIC_CREEP_HOURS) * HOUR
            s = _Session(
                em, f"{spec.aid}-{d}-g", ip(rng.choice(outside), rng), habits.client, d, ep, t
            )
            if habits.initializes:
                s.message("initialize", BOT_INITIALIZE_LEAD_S)
            targets = rng.sample(other, min(len(other), rng.randint(*CLASSIC_CREEP_TARGETS)))
            for _ in range(rng.randint(*CLASSIC_CREEP_CALLS)):
                s.call(
                    rng.choice(CREEP_TOOLS), rng.choice(targets), rng.uniform(*CLASSIC_CREEP_GAP_S)
                )
            return
        for day in range(d, min(d + BOT_CREEP_DAYS, org.calendar.n_days)):
            if not is_workday(day):
                continue
            other = _other_team_repos(habits, org, day)
            for _ in range(rng.randint(*PLAIN_CREEP_JOBS)):
                s = _plain_bot_session(
                    em, spec, habits, day, _usual_bot_time(habits, day, rng), ep, rng
                )
                for _ in range(rng.randint(*PLAIN_CREEP_JOB_CALLS)):
                    s.call(
                        rng.choice(CREEP_TOOLS), rng.choice(other), rng.uniform(*PLAIN_CREEP_GAP_S)
                    )
    elif kind == BOT_MISCONFIGURED_WRITER:
        repo = rng.choice(_bot_repos(habits, spec, org, d))
        t = _usual_bot_time(habits, d, rng)
        if variant == CLASSIC:
            s = _Session(em, f"{spec.aid}-{d}-g", bot_address(habits, rng), habits.client, d, ep, t)
            for _ in range(rng.randint(*CLASSIC_WRITER_CALLS)):
                s.call("update_issue", repo, rng.uniform(*CLASSIC_WRITER_GAP_S))
            return
        left = rng.randint(*PLAIN_WRITER_CALLS)
        while left > 0:
            s = _plain_bot_session(em, spec, habits, d, t, ep, rng)
            k = min(left, rng.randint(*PLAIN_WRITER_JOB_CALLS))
            for _ in range(k):
                s.call("update_issue", repo, rng.uniform(*PLAIN_WRITER_GAP_S))
            left -= k
            t = s.t + rng.uniform(*PLAIN_WRITER_PAUSE_S)
    else:
        raise ValueError(f"unknown bot gray kind {kind!r}")


def _other_team_repos(habits: BotHabits, org: Org, d: int) -> list[Repo]:
    return [r for r in org.existing(d) if r.team is not None and r.team not in habits.teams]


def gen_bot(
    spec: Spec,
    org: Org,
    seed: int,
    loop_day: int | None,
    profile: Profile,
    *,
    options: WorldOptions = LEGACY_OPTIONS,
    loop_episode: str | None = None,
    gray_plan: list[tuple[int, str, str]] | tuple = (),
) -> list[tuple]:
    """A bot's rows. ``loop_day``: a CI bot's stuck loop (``loop_episode`` its id, v1-v4's when
    None); ``gray_plan`` (EV-08) its other gray episodes, each drawn from its own generator so
    the bot's ordinary traffic does not move."""
    cal = org.calendar
    rng = random.Random(seed * 1_000_003 + spec.idx)
    em = Emitter(rng, profile, resp_rng=response_rng(seed, spec.aid, options))
    family = rng.choice(("openai-agents", "langchain-mcp-adapters", "mcp"))
    client = f"{family}/1.2.0"
    stateless = rng.random() < 0.5
    if spec.role == "ci_bot":
        pool = rng.sample(CLOUD_POOL, rng.choice((4, 12, 40)))
        teams = rng.sample(range(N_TEAMS), rng.randint(1, 3))
        habits = BotHabits(spec.role, client, tuple(pool), not stateless, tuple(teams))
        for d in range(cal.n_days):
            for h in range(24):
                busy = is_workday(d) and 7 <= h <= 20
                for _ in range(poisson(rng, 6 if busy else 1)):
                    t = (BASE_DAY + d) * DAY + h * HOUR + rng.uniform(0, HOUR)
                    sid = f"{spec.aid}-{d}-{h}-{rng.randrange(10**6)}"
                    address = ip(rng.choice(pool), rng)
                    repos = [r for tm in teams for r in org.team_repos[tm] if r.created <= d]
                    repo = rng.choice(repos)
                    if not stateless:
                        em.message(t - 0.5, "initialize", sid, address, client)
                    tools = ["get_pull_request", "get_pull_request_files"]
                    tools += ["get_pull_request_status"] * rng.randint(1, 3) + ["list_commits"]
                    if d >= cal.rollout_at + (spec.idx % 2):
                        tools.append("get_workflow_runs")
                    if rng.random() < 0.5:
                        tools.append("add_issue_comment")
                    if rng.random() < 0.1:
                        tools.append("create_pull_request_review")
                    for tool in tools:
                        legit = (
                            "org_tool_rollout"
                            if (tool == "get_workflow_runs" and d < cal.rollout_at + 3)
                            else ""
                        )
                        em.call(t, sid, tool, repo, d, address, client, legit)
                        t += rng.uniform(0.5, 2)
            if loop_day == d:
                ep = loop_episode or episode_id(BOT_LOOP, spec.aid, 0)
                if parse_episode(ep).variant == PLAIN:
                    _plain_bot_loop(em, spec, org, d, ep, habits, stable_rng(seed, ep))
                    continue
                sid, address = f"{spec.aid}-{d}-loop", ip(rng.choice(pool), rng)
                t = (BASE_DAY + d) * DAY + rng.uniform(*BOT_LOOP_HOURS) * HOUR
                repo = rng.choice(org.team_repos[teams[0]])
                for _ in range(rng.randint(*BOT_LOOP_CALLS)):
                    em.call(t, sid, "get_pull_request_status", repo, d, address, client, "", ep)
                    t += CLASSIC_LOOP_GAP_S
    elif spec.role == "triage_bot":
        net = (10, 40 + spec.idx % 10)
        host = _bot_host(net, seed, spec, options)
        habits = BotHabits(spec.role, client, (net,), not stateless, (), host)
        for d in range(cal.n_days):
            for q in range(96):
                t = (BASE_DAY + d) * DAY + q * 900 + rng.uniform(0, 60)
                sid, address = f"{spec.aid}-{d}-{q}", ip(net, rng)
                address = host or address
                if not stateless:
                    em.message(t - 0.5, "initialize", sid, address, client)
                for repo in rng.sample(org.existing(d), 3):
                    for _ in range(rng.randint(1, 3)):
                        em.call(t, sid, "list_issues", repo, d, address, client)
                        t += rng.uniform(0.5, 1.5)
                    for _ in range(rng.choice((0, 0, 1, 2))):
                        em.call(
                            t,
                            sid,
                            rng.choice(("update_issue", "add_issue_comment")),
                            repo,
                            d,
                            address,
                            client,
                        )
                        t += rng.uniform(0.5, 1.5)
    else:  # report_bot: daily, weekly (Monday) and monthly page walks
        net = (10, 60 + spec.idx % 10)
        host = _bot_host(net, seed, spec, options)
        habits = BotHabits(spec.role, client, (net,), True, (), host)
        for d in range(cal.n_days):
            t = (BASE_DAY + d) * DAY + 6 * HOUR + rng.uniform(0, 300)
            sid, address = f"{spec.aid}-{d}", ip(net, rng)
            address = host or address
            em.message(t - 0.5, "initialize", sid, address, client)
            repos = [r for r in org.team_repos[spec.team] if r.created <= d]
            pages, legit = 1, ""
            if d % 7 == 0:
                pages = 3
            if d % 30 == 1:
                repos, pages, legit = org.existing(d), rng.randint(2, 4), "monthly_report"
            for repo in repos:
                for tool in ("list_pull_requests", "list_issues"):
                    for _ in range(pages):
                        em.call(t, sid, tool, repo, d, address, client, legit)
                        t += rng.uniform(0.6, 1.4)
    for d, kind, ep in gray_plan:
        bot_gray_episode(em, spec, org, d, kind, ep, habits, stable_rng(seed, ep))
    em.rows.sort(key=lambda r: r[0])
    return em.rows


def _plain_bot_loop(
    em: Emitter, spec: Spec, org: Org, d: int, ep: str, habits: BotHabits, rng: random.Random
) -> None:
    """EV-09 for the stuck CI loop: a job-shaped session, opened as the bot opens its jobs,
    with the bot's own jittered gaps instead of exactly one second."""
    t = (BASE_DAY + d) * DAY + rng.uniform(*BOT_LOOP_HOURS) * HOUR
    repo = rng.choice(_bot_repos(habits, spec, org, d))
    s = _plain_bot_session(em, spec, habits, d, t, ep, rng)
    for _ in range(rng.randint(*BOT_LOOP_CALLS)):
        s.call("get_pull_request_status", repo, rng.uniform(*PLAIN_LOOP_GAP_S))


def _bot_host(net: tuple[int, int], seed: int, spec: Spec, options: WorldOptions) -> str | None:
    """D5: a triage or report bot's fixed host under sticky addresses, else None."""
    return egress_address(net, seed, spec.aid, "host") if options.sticky_addresses else None


def build_world(
    n_agents: int,
    seed: int,
    profile: Profile | None = None,
    *,
    world_version: str | None = None,
    calendar: Calendar | None = None,
    options: WorldOptions | None = None,
) -> tuple[dict, dict, Org]:
    """``({agent: rows}, {agent: role}, org)``.

    ``world_version`` ``"v4"`` (the default) is the v1-v4 world; ``"v5"`` turns on every v5
    change (``V5_OPTIONS``). ``options`` sets the switches one by one instead (not both).
    ``calendar`` defaults to today's (:data:`DEFAULT_CALENDAR`); any other calendar needs an
    explicit ``world_version`` or ``options``, since the default v4 order of repositories
    depends on ``PYTHONHASHSEED``.

    Every agent's gray plan is drawn first, then the world's episode ids are labelled with
    their variants per kind (:func:`stratified_variants`), then the rows are generated.
    """
    if options is not None and world_version is not None:
        raise ValueError("pass world_version or options, not both")
    default_switches = options is None and world_version is None
    if calendar is not None and calendar != DEFAULT_CALENDAR and default_switches:
        raise ValueError("a calendar other than today's needs an explicit world_version or options")
    options = options if options is not None else options_for(world_version or WORLD_V4)
    calendar = calendar if calendar is not None else DEFAULT_CALENDAR
    profile = profile or Profile()
    org = build_org(seed, calendar=calendar, public_repos=options.public_repos)
    specs = world_roster(n_agents, seed, options=options, calendar=calendar)
    rng = random.Random(seed + 2)
    ci = [s for s in specs if s.role == "ci_bot"]
    n_loops = _round_half_up(len(ci) * LEGACY_BOT_LOOPS, LEGACY_CI_BOTS)
    loops = {
        s.aid: rng.randint(calendar.gray_from, calendar.gray_to) for s in rng.sample(ci, n_loops)
    }
    kinds = GRAY_KINDS_V5 if options.toxic_flow else GRAY_KINDS
    plans: dict[str, list[tuple[int, str, str]]] = {}
    for spec in specs:
        if spec.role in ROLE_TOOLS:
            plan_rng = random.Random(seed * 7_919 + spec.idx)
            plan = gray_plan_for(spec, plan_rng, profile, calendar=calendar, kinds=kinds)
            plans[spec.aid] = [e for e in plan if spec.end is None or e[0] < spec.end]
        else:
            plans[spec.aid] = bot_gray_plan_for(spec, seed, calendar, options.bot_gray_rate)
    loop_ids = {aid: episode_id(BOT_LOOP, aid, 0) for aid in loops}
    every_id = [ep for plan in plans.values() for _, _, ep in plan] + list(loop_ids.values())
    labels = stratified_variants(every_id, seed, options.plain_share)
    world, roles = {}, {}
    for spec in specs:
        plan = [(day, kind, labels[ep]) for day, kind, ep in plans[spec.aid]]
        if spec.role in ROLE_TOOLS:
            world[spec.aid] = gen_person(spec, org, seed, plan, profile, options=options)
        else:
            loop_id = loop_ids.get(spec.aid)
            world[spec.aid] = gen_bot(
                spec,
                org,
                seed,
                loops.get(spec.aid),
                profile,
                options=options,
                loop_episode=labels[loop_id] if loop_id is not None else None,
                gray_plan=plan,
            )
        roles[spec.aid] = spec.role
    return world, roles, org
