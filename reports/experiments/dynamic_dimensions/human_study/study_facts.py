"""What one agent did on one day, and the same agent's usual days, as the nine card rows.

Every card has the same nine rows (``ROWS``), in the same order. "Usual" is the same agent's last
90 days up to yesterday (its active days: days with at least one action), as the engine sees its
history; "today" is the agent-day itself. Ranges are the 10th-90th percentile of the active days,
so about 1 active day in 5 falls a little outside them. Times are the owner's home time zone
(bots: the server's clock). The wording is ``study_words.py``.

The simulator records no page size for list calls, so "Most items it asked for at once" is
``NOT_RECORDED`` on every card. It stays in the data (every card keeps all nine rows, so the
presence of a row is never a cue), but it is in ``HIDDEN_ROWS``: the page and ``cards.txt`` do not
show it and it is not a "what stood out" option.
"""

from __future__ import annotations

import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent
for path in (Path(__file__).resolve().parent, SIM_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mcp_security.behaviour.engine import (  # noqa: E402
    SAME_CALL_WINDOW_S,
    BehaviourConfig,
    client_family,
    network_of,
)
from normal_org_world import BASE_DAY, DAY, HOUR  # noqa: E402
from study_words import (  # noqa: E402
    ANOTHER_PLACE,
    APP_TODAY,
    CLOUD_WORDS,
    HOURS_PER_DAY,
    MAX_LISTED,
    NEVER,
    SOME_DAYS,
    app_kind,
    frequency,
    hour_spans,
    hours_text,
    names_text,
    network_place,
    number,
    plain_range,
    program_count,
    qualifier,
    ranked,
    size_today,
    size_usual,
    tool_name,
    unique,
)

#: (row id, label), in the fixed order every card uses
ROWS: tuple[tuple[str, str], ...] = (
    ("hours", "Hours it worked"),
    ("actions", "Actions in the day"),
    ("projects", "Projects it touched"),
    ("changes", "Changes it made"),
    ("kinds", "Kinds of actions"),
    ("upload", "Biggest single upload"),
    ("downloads", "Most items it asked for at once"),
    ("repeats", "Quick repeats"),
    ("connection", "Where it connected from"),
)
ROW_IDS: tuple[str, ...] = tuple(row_id for row_id, _ in ROWS)
#: rows kept in the data but not shown: not recorded on any card
HIDDEN_ROWS = frozenset({"downloads"})
NOT_RECORDED = "not recorded"
NOTHING_NEW = "nothing new"
NEW_TO_IT, RARE_FOR_IT = "new to it", "rare for it"
HISTORY_DAYS = 90  # the engine's window: days today-89 .. yesterday
COMMON_HOUR_SHARE = 0.25  # an hour of the day is "usual" if active on this share of its days
NIGHT_HOURS = frozenset({22, 23, 0, 1, 2, 3, 4, 5})  # 10 pm to 6 am, as the word list says
FEW_NIGHTS = 5
RARE_DAYS = 2  # a tool, network or app used on at most this many of its days is "rare for it"
SENSITIVE_LEVEL = 4  # sensitivity 4-5 is "marked sensitive"
WRITE = "write"
CALL = "tools/call"
MANY_NETWORKS = 10  # a place with more networks than this says "many addresses" (cloud runners)
TOP_TOOLS = 2  # "mostly X and Y"
WEEKEND = frozenset({5, 6})
DAYS_PER_WEEK = 7


@dataclass
class DayFacts:
    """One agent-day, as the server saw it (no arguments of the calls)."""

    calls: int = 0
    hours: set[int] = field(default_factory=set)  # local hours with an action
    local_dates: set[int] = field(default_factory=set)  # local dates (sim days) of its actions
    assets: dict[str, int] = field(default_factory=dict)  # project -> sensitivity
    writes: int = 0
    max_size: int = 0  # bytes, the largest action
    max_repeat: int = 0  # most calls of one tool on one project within 10 minutes
    networks: set[str] = field(default_factory=set)  # /16, on any message
    apps: set[str] = field(default_factory=set)  # client family, on any message
    tools: Counter = field(default_factory=Counter)


@dataclass(frozen=True)
class History:
    """The agent's active days in the 90 days up to yesterday."""

    days: dict[int, DayFacts]
    weekend_days_in_window: int

    @property
    def active(self) -> list[DayFacts]:
        return [facts for _, facts in sorted(self.days.items())]


def collect_facts(
    rows: list[tuple], tz: float, config: BehaviourConfig | None = None
) -> dict[int, DayFacts]:
    """Per simulation day, what one agent did (rows in time order, ``normal_org_world.ROW``)."""
    config = config or BehaviourConfig()
    days: dict[int, DayFacts] = {}
    recent: dict[tuple, deque] = {}
    for ts, method, _session, tool, asset, sens, op, address, client, size, *_ in rows:
        day = int(ts // DAY) - BASE_DAY
        facts = days.setdefault(day, DayFacts())
        network = network_of(address, config)
        if network:
            facts.networks.add(network)
        app = client_family(client)
        if app:
            facts.apps.add(app)
        if method != CALL:
            continue
        facts.calls += 1
        facts.hours.add(local_hour(ts, tz))
        facts.local_dates.add(local_date(ts, tz))
        facts.tools[tool] += 1
        facts.max_size = max(facts.max_size, size)
        if op == WRITE:
            facts.writes += 1
        if asset:
            facts.assets[asset] = sens or 0
        window = recent.setdefault((tool, asset), deque())
        window.append(ts)
        while window[0] <= ts - SAME_CALL_WINDOW_S:
            window.popleft()
        facts.max_repeat = max(facts.max_repeat, len(window))
    return days


def local_hour(ts: float, tz: float) -> int:
    """The hour of day (0-23) in a time zone ``tz`` hours from the server's clock."""
    return int((ts / HOUR + tz) % HOURS_PER_DAY)


def local_date(ts: float, tz: float) -> int:
    """The simulation day of ``ts`` on the owner's own calendar (``tz`` hours from the server)."""
    return int((ts + tz * HOUR) // DAY) - BASE_DAY


def history_of(days: dict[int, DayFacts], day: int) -> History:
    """The active days among ``day - 89`` .. ``day - 1`` (the engine's 90-day window)."""
    window = range(day - HISTORY_DAYS + 1, day)
    active = {d: days[d] for d in window if d in days and days[d].calls}
    weekends = sum(1 for d in window if d % DAYS_PER_WEEK in WEEKEND)
    return History(active, weekends)


def worked_on_weekend(facts: DayFacts, day: int) -> bool:
    """Whether a day's actions fall on a weekend of the owner's own calendar."""
    dates = facts.local_dates or {day}
    return any(d % DAYS_PER_WEEK in WEEKEND for d in dates)


# ── the nine rows ────────────────────────────────────────────────────────────────────────
def card_rows(today: DayFacts, history: History) -> list[dict[str, str]]:
    """Every row of ``ROWS``, in order: ``{"id", "usual", "today"}``."""
    past = history.active
    texts = {
        "hours": (hours_usual(history), hours_text(today.hours)),
        "actions": (plain_range([f.calls for f in past]), number(today.calls)),
        "projects": (projects_usual(past), projects_today(today, past)),
        "changes": (plain_range([f.writes for f in past]), number(today.writes)),
        "kinds": (kinds_usual(past), kinds_today(today, past)),
        "upload": (size_usual([f.max_size for f in past]), size_today(today.max_size)),
        "downloads": (NOT_RECORDED, NOT_RECORDED),
        "repeats": (repeats_usual(past), number(repeats(today.max_repeat))),
        "connection": (connection_usual(past), connection_today(today, past)),
    }
    return [
        {"id": row_id, "usual": texts[row_id][0], "today": texts[row_id][1]} for row_id in ROW_IDS
    ]


def hours_usual(history: History) -> str:
    """The hours active on a quarter of its days, plus nights and weekends."""
    past = history.active
    share = Counter(h for f in past for h in f.hours)
    common = {h for h, n in share.items() if n >= COMMON_HOUR_SHARE * len(past)}
    if not common:
        common = {h for h, _ in ranked(share, 1)}
    spans = hour_spans(common)
    if spans == [(0, HOURS_PER_DAY)]:
        return "around the clock"
    parts = [hours_text(common)]
    if not common & NIGHT_HOURS:
        nights = sum(1 for f in past if f.hours & NIGHT_HOURS)
        parts.append(
            "never at night"
            if nights == 0
            else "once at night"
            if nights == 1
            else "a few nights"
            if nights <= FEW_NIGHTS
            else "many nights"
        )
    weekend_days = sum(1 for d, f in history.days.items() if worked_on_weekend(f, d))
    if weekend_days == 0:
        parts.append("never on weekends")
    elif weekend_days <= SOME_DAYS * history.weekend_days_in_window:
        parts.append("rarely on weekends")
    else:
        parts.append("weekends too")
    return "; ".join(parts)


def projects_usual(past: list[DayFacts]) -> str:
    """``2-4 a day. 9 different ones in all, 1 of them marked sensitive.``"""
    seen: dict[str, int] = {}
    for f in past:
        seen.update(f.assets)
    daily = plain_range([len(f.assets) for f in past])
    if daily == NEVER:
        return NEVER
    sensitive = sum(1 for s in seen.values() if s >= SENSITIVE_LEVEL)
    marked = f"{number(sensitive)} of them" if sensitive else "none of them"
    return f"{daily} a day. {number(len(seen))} different ones in all, {marked} marked sensitive."


def projects_today(today: DayFacts, past: list[DayFacts]) -> str:
    """One pattern on every card: ``7 projects. New to it: 3. Marked sensitive: 2 (both new to
    it).``"""
    known = {a for f in past for a in f.assets}
    new = [a for a in today.assets if a not in known]
    sensitive = [a for a, s in today.assets.items() if s >= SENSITIVE_LEVEL]
    sensitive_new = sum(1 for a in sensitive if a not in known)
    count = len(today.assets)
    text = (
        f"{number(count)} {'project' if count == 1 else 'projects'}. New to it: "
        f"{number(len(new))}. Marked sensitive: {number(len(sensitive))}"
    )
    if sensitive:
        text += " " + sensitive_newness(len(sensitive), sensitive_new)
    return text + "."


def sensitive_newness(n_sensitive: int, n_new: int) -> str:
    """``(new to it)``, ``(not new to it)``, ``(all 4 new to it)``, ``(1 of them new to it)``."""
    if n_sensitive == 1:
        return f"({NEW_TO_IT})" if n_new else f"(not {NEW_TO_IT})"
    if n_new == n_sensitive:
        return f"(both {NEW_TO_IT})" if n_new == 2 else f"(all {number(n_new)} {NEW_TO_IT})"
    if n_new == 0:
        return f"(none {NEW_TO_IT})"
    return f"({number(n_new)} of them {NEW_TO_IT})"


def kinds_usual(past: list[DayFacts]) -> str:
    """``6-9 a day, mostly read a file and search across all the code``."""
    total: Counter = Counter()
    for f in past:
        total.update(f.tools)
    daily = plain_range([len(f.tools) for f in past])
    top = [tool_name(t) for t, _ in ranked(total, TOP_TOOLS)]
    return f"{daily} a day, mostly {names_text(top)}"


def kinds_today(today: DayFacts, past: list[DayFacts]) -> str:
    """``nothing new``, or what is new or rare for it, the fact first."""
    days_used = Counter(t for f in past for t in f.tools)
    new = sorted(tool_name(t) for t in today.tools if t not in days_used)
    rare = sorted(tool_name(t) for t in today.tools if 0 < days_used[t] <= RARE_DAYS)
    parts = [novelty(new, NEW_TO_IT), novelty(rare, RARE_FOR_IT)]
    return "; ".join(p for p in parts if p) or NOTHING_NEW


def novelty(names: list[str], word: str) -> str:
    """``copy a project (rare for it)``; empty when there are none."""
    return f"{names_text(names)} {qualifier(len(names), word)}" if names else ""


def repeats(max_repeat: int) -> int:
    """Quick repeats: how many more times than once it did the same action on the same item
    within 10 minutes (the most in one stretch of the day)."""
    return max(0, max_repeat - 1)


def repeats_usual(past: list[DayFacts]) -> str:
    """``0-5``, ``about 2`` or ``0 (never)``."""
    return plain_range([repeats(f.max_repeat) for f in past])


# ── where it connected from ──────────────────────────────────────────────────────────────
def connection_usual(past: list[DayFacts]) -> str:
    """``office (most days), home (some days), +1 other place; 1 app``."""
    places: Counter = Counter()
    networks_per_place: dict[str, set[str]] = {}
    kinds: dict[str, set[str]] = {}
    for f in past:
        for place in {network_place(n) for n in f.networks}:
            places[place] += 1
        for n in f.networks:
            networks_per_place.setdefault(network_place(n), set()).add(n)
        for app in f.apps:
            kinds.setdefault(app_kind(app), set()).add(app)
    n_days = max(1, len(past))
    place_parts = []
    for place, days in ranked(places, MAX_LISTED):
        many = len(networks_per_place[place]) > MANY_NETWORKS
        extra = ", many addresses" if many else ""
        place_parts.append(f"{place} ({frequency(days / n_days)}{extra})")
    hidden = len(places) - MAX_LISTED
    if hidden > 0:
        place_parts.append(f"+{hidden} other {'place' if hidden == 1 else 'places'}")
    programs = [program_count(kind, len(apps)) for kind, apps in sorted(kinds.items())]
    return ", ".join(place_parts) + "; " + (" and ".join(programs) or "no app")


def connection_today(today: DayFacts, past: list[DayFacts]) -> str:
    """Today's places and program, the fact first: ``home; its usual app (nothing
    new)`` or ``office, the cloud (new to it); its own small program instead of an app (new
    to it)``."""
    network_days = Counter(n for f in past for n in f.networks)
    place_days = Counter(p for f in past for p in {network_place(n) for n in f.networks})
    app_days = Counter(a for f in past for a in f.apps)
    shown: dict[str, str] = {}  # place words -> "", "new" or "rare"
    for network in sorted(today.networks, key=lambda n: (-place_days[network_place(n)], n)):
        place = network_place(network)
        if network not in network_days:
            if place in place_days:
                words = place if place == CLOUD_WORDS and past_many(past, place) else None
                words = words or ANOTHER_PLACE.get(place, place)
                shown.setdefault(words, NEW_TO_IT if words != place else "")
            else:
                shown[place] = NEW_TO_IT
        elif network_days[network] <= RARE_DAYS:
            shown.setdefault(place, RARE_FOR_IT)
        else:
            shown[place] = ""  # a place it uses often, whatever its other networks
    places = [f"{p} ({q})" if q else p for p, q in shown.items()]
    program, odd = program_today(today, app_days)
    text = "; ".join(part for part in (", ".join(places), program) if part)
    if not odd and not any(shown.values()):
        text += f" ({NOTHING_NEW})"
    return text


def past_many(past: list[DayFacts], place: str) -> bool:
    """Whether it already used many networks of ``place`` (a new cloud address is ordinary)."""
    networks = {n for f in past for n in f.networks if network_place(n) == place}
    return len(networks) > MANY_NETWORKS


def program_today(today: DayFacts, app_days: Counter) -> tuple[str, bool]:
    """The words for today's app or program and whether any of it is new or rare."""
    parts, odd = [], False
    usual_kinds: Counter = Counter()
    for app in sorted(today.apps):
        kind = app_kind(app)
        if app not in app_days:
            parts.append(f"{APP_TODAY[(kind, 'new')]} ({NEW_TO_IT})")
            odd = True
        elif app_days[app] <= RARE_DAYS:
            parts.append(f"{APP_TODAY[(kind, 'rare')]} ({RARE_FOR_IT})")
            odd = True
        else:
            usual_kinds[kind] += 1
    for kind, n in sorted(usual_kinds.items()):
        parts.insert(0, APP_TODAY[(kind, "usual many" if n > 1 else "usual")])
    return " and ".join(unique(parts)), odd
