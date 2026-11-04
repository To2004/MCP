"""Who the agent is, and the notes a manager could know about its day, in plain words.

The people's habits (time zone, vacations, travel, ...) are rebuilt exactly as
``normal_org_world.gen_person`` draws them: ``make_person`` is the first thing it draws from the
agent's own random stream. The notes are true facts of the simulated day:

- ``calendar`` (shown as "About the owner"): the owner's own life (``person_day_tags`` and the
  labels on the day's calls);
- ``company`` (shown as "About the company"): an org-wide change on that day (secure-link change,
  server release, repository migration, launch week), whatever the agent itself did, plus the
  monthly report run for report bots.

``latent_cause`` finds the benign changes the simulator does not label on the day they show: the
labels of an internet-provider change and an app switch cover three calendar days, while the
agent may first use the new line or app days later. The key records it; the card shows nothing.
"""

from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from normal_org_world import (  # noqa: E402
    CRUNCH_DAYS,
    MIGRATION_DAY,
    NEW_TOOLS,
    ROLE_TOOLS,
    ROLLOUT_DAY,
    VPN_CHANGE_DAY,
    Person,
    Profile,
    is_workday,
    make_person,
    roster,
)

PERSON_SEED_STEP = 1_000_003  # normal_org_world.gen_person: Random(seed * step + idx)
TRAVEL_HOURS_AHEAD = 7  # normal_org_world.gen_person: a traveller works 7 hours ahead
EVENT_WEEK = 7  # "this week" after an org-wide change
MIGRATION_SPAN = 3  # the days the migration labels its calls
DAYS_PER_WEEK = 7
TWO_WEEKS = 14
WEEK_WORDS = {1: "a week", 2: "two weeks", 3: "three weeks", 4: "four weeks"}
NOTE_JOIN = ". "  # two notes are two sentences

ROLE_WHO: dict[str, str] = {
    "dev": "A coding assistant used by one programmer",
    "lead": "A coding assistant used by a team lead, who reviews and approves code",
    "sre": "An assistant used by an engineer who keeps the company's computers running",
    "pm": "An assistant used by a product manager, who plans the team's work",
    "ci_bot": "A bot that checks every proposed code change",
    "triage_bot": "A bot that sorts and labels new tasks all day",
    "report_bot": "A bot that writes the team's daily report",
}
#: label -> the latent cause it stands for, when the label missed the day the change showed
LATENT_ISP, LATENT_CLIENT = "isp_change", "client_switch"
#: personal labels, in the order their notes are written
PERSONAL_TAGS = (
    "new_hire",
    "back_from_vacation",
    "travel",
    "team_transfer",
    "role_change",
    "client_switch",
    "isp_change",
    "on_call_incident",
    "new_project",
)
#: org-wide labels (the notes come from the day, these only add the later echoes)
ORG_TAGS = (
    "release_crunch",
    "org_vpn_change",
    "org_tool_rollout",
    "org_repo_migration",
    "monthly_report",
)


@dataclass(frozen=True)
class AgentProfile:
    """What the cards need to know about an agent besides its calls."""

    agent: str
    role: str
    tz: float  # hours from the server's clock (bots: 0)
    person: Person | None


def agent_profiles(n_agents: int, seed: int, profile: Profile) -> dict[str, AgentProfile]:
    """Every agent's role, home time zone and (for people) habits, as the world drew them."""
    out = {}
    for spec in roster(n_agents, seed):
        person = None
        if spec.role in ROLE_TOOLS:
            rng = random.Random(seed * PERSON_SEED_STEP + spec.idx)
            person = make_person(spec, rng, profile)
        out[spec.aid] = AgentProfile(spec.aid, spec.role, person.tz if person else 0.0, person)
    return out


def who_text(role: str) -> str:
    """The agent's role in one plain sentence."""
    return ROLE_WHO[role]


def ago(days: int) -> str:
    """0 -> today, 1 -> yesterday, 9 -> 9 days ago, 15 -> 2 weeks ago."""
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < TWO_WEEKS:
        return f"{days} days ago"
    return f"{days // DAYS_PER_WEEK} weeks ago"


def vacation_note(person: Person, day: int) -> str:
    """``The owner came back today from two weeks of vacation``."""
    last_off = day - 1
    while last_off >= 0 and last_off not in person.off:
        last_off -= 1
    first_off = last_off
    while first_off - 1 >= 0 and (first_off - 1 in person.off or not is_workday(first_off - 1)):
        first_off -= 1
    weeks = max(1, round((last_off - first_off + 1) / DAYS_PER_WEEK))
    length = WEEK_WORDS.get(weeks, f"{weeks} weeks")
    back = next(d for d in range(last_off + 1, day + 1) if is_workday(d) or d == day)
    when = ago(day - back)
    if when == "today":
        return f"The owner came back today from {length} of vacation"
    return f"The owner came back from {length} of vacation {when}"


def calendar_note(agent: AgentProfile, day: int, tags: set[str]) -> str | None:
    """The owner's own life on that day, or ``None``."""
    person = agent.person
    notes = []
    for tag in PERSONAL_TAGS:
        if tag not in tags:
            continue
        if tag == "new_project":
            whose = "the owner's team" if person else "the team it serves"
            notes.append(f"In the last two weeks, {whose} started a new project")
        elif tag == "on_call_incident":
            notes.append("The owner was on call, and there was an outage during the night")
        elif person is None:
            continue
        elif tag == "new_hire":
            notes.append(f"The owner joined the company {ago(day - person.spec.start)}")
        elif tag == "back_from_vacation":
            notes.append(vacation_note(person, day))
        elif tag == "travel":
            ahead = f"{TRAVEL_HOURS_AHEAD} hours ahead of home"
            notes.append(f"The owner is traveling abroad this week ({ahead})")
        elif tag == "team_transfer":
            notes.append(f"The owner moved to another team {ago(day - person.transfer[0])}")
        elif tag == "role_change":
            notes.append(
                f"The owner changed jobs {ago(day - person.role_change)}: "
                "now works on keeping the company's computers running"
            )
        elif tag == "client_switch":
            notes.append("The owner switched to a new coding app this week")
        elif tag == "isp_change":
            notes.append("The owner changed home internet provider this week")
    return NOTE_JOIN.join(notes) if notes else None


def org_events(day: int, tags: set[str]) -> list[tuple[str, str]]:
    """(event name, plain note) of the org-wide changes on that day."""
    n_new = len(NEW_TOOLS)
    events = []
    if day in CRUNCH_DAYS:
        note = (
            "Launch week: the company is putting out a new version of its software, and many "
            "people are working late"
        )
        events.append(("release_crunch", note))
    if VPN_CHANGE_DAY <= day < VPN_CHANGE_DAY + EVENT_WEEK:
        note = "This week the company switched everyone from the old secure link to a new one"
        events.append(("vpn_change", note))
    elif "org_vpn_change" in tags:
        note = "A few weeks ago the company switched everyone from the old secure link to a new one"
        events.append(("vpn_change", note))
    if day == ROLLOUT_DAY:
        note = f"Today the code server added {n_new} new kinds of actions for everyone"
        events.append(("tool_rollout", note))
    elif ROLLOUT_DAY < day < ROLLOUT_DAY + EVENT_WEEK:
        note = f"This week the code server added {n_new} new kinds of actions for everyone"
        events.append(("tool_rollout", note))
    elif "org_tool_rollout" in tags:
        note = f"Recently the code server added {n_new} new kinds of actions for everyone"
        events.append(("tool_rollout", note))
    if MIGRATION_DAY <= day < MIGRATION_DAY + MIGRATION_SPAN or "org_repo_migration" in tags:
        note = "This week the company moved some projects to a new place, so their names changed"
        events.append(("repo_migration", note))
    if "monthly_report" in tags:
        events.append(("monthly_report", "Start of the month: the monthly reports run today"))
    return events


def company_note(day: int, tags: set[str]) -> str | None:
    """The org-wide changes on that day, or ``None``."""
    events = org_events(day, tags)
    return NOTE_JOIN.join(note for _, note in events) if events else None


def org_event_name(day: int, tags: set[str]) -> str | None:
    """The org-wide changes on that day as one key value, e.g. ``vpn_change``."""
    events = org_events(day, tags)
    return "+".join(name for name, _ in events) if events else None


def network_text(prefix: tuple[int, int]) -> str:
    """A /16 prefix as ``engine.network_of`` writes it: ``70.10.0.0/16``."""
    first, second = prefix
    return f"{first}.{second}.0.0/16"


def first_day_with(days: dict, day_from: int, used: Callable[[object], bool]) -> int | None:
    """The first simulation day from ``day_from`` whose facts satisfy ``used``."""
    return next((d for d in sorted(days) if d >= day_from and used(days[d])), None)


def latent_cause(agent: AgentProfile, days: dict, day: int, tags: set[str]) -> str | None:
    """A benign change that first showed on ``day`` without its label: the first day on the new
    home internet line after an internet-provider change, or on the new app after a switch.

    ``days`` maps a day to the agent's ``study_facts.DayFacts`` (networks and app families).
    """
    person = agent.person
    if person is None:
        return None
    isp_day, new_home = person.isp_change
    if LATENT_ISP not in tags and isp_day <= day:
        network = network_text(new_home)
        if first_day_with(days, isp_day, lambda f: network in f.networks) == day:
            return LATENT_ISP
    if LATENT_CLIENT not in tags and person.switch_day <= day and person.switch_to:
        app = person.switch_to
        if first_day_with(days, person.switch_day, lambda f: app in f.apps) == day:
            return LATENT_CLIENT
    return None
