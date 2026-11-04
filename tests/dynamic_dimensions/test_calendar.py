"""EV-06: the calendar of org-wide changes, the release crunch and the gray window.

``Calendar()`` is today's calendar; a drawn calendar respects its ranges and gaps, and a world
built on a calendar shows the changes on that calendar's days only. Synthetic worlds.
"""

from __future__ import annotations

import random
from dataclasses import replace

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

N_DRAWS = 2_000
PRESENT_TOLERANCE = 0.03  # 6,000 Bernoulli(0.8) draws: SD about 0.005
SMALL_AGENTS, SMALL_SEED = 12, 3
#: a calendar unlike today's in every field
MOVED = W.Calendar(
    vpn_change_day=100,
    rollout_day=141,
    migration_day=125,
    crunch_start=150,
    crunch_len=4,
    gray_from=100,
    gray_to=160,
)
TZ_SLACK_DAYS = 1  # a row's UTC day can be one off its local (simulation) day
DAY_OF_WEEK_SHIFT = (2, 5)  # gray days move back to a Friday or forward to a Saturday
CREEP_DAYS = W.BOT_CREEP_DAYS  # person scope creep lasts as long (gen_person: 15 days)
N_PLANS = 2_000  # people's gray plans (Poisson 0.6 episodes each)
LATE_GRAY_TO = 175  # the latest end of a drawn 180-day gray window (n_days - 5), a Monday
WEEKEND_ONLY = {"off_hours_batch": 1.0}
SATURDAY_OF_WEEK = 5  # day % 7 (day 0 is a Monday)


def utc_day(row: tuple) -> int:
    return int(row[0] // W.DAY) - W.BASE_DAY


def world_on(calendar: W.Calendar) -> dict:
    world, _, _ = W.build_world(SMALL_AGENTS, SMALL_SEED, calendar=calendar, options=W.V5_OPTIONS)
    return world


def calls(world: dict) -> list[tuple]:
    return [r for rows in world.values() for r in rows if r[1] == "tools/call"]


def test_default_calendar_is_todays() -> None:
    cal = W.Calendar()
    assert cal == W.DEFAULT_CALENDAR
    assert (cal.vpn_at, cal.rollout_at, cal.migration_at) == (
        W.VPN_CHANGE_DAY,
        W.ROLLOUT_DAY,
        W.MIGRATION_DAY,
    )
    assert cal.crunch_days == W.CRUNCH_DAYS
    assert (cal.gray_from, cal.gray_to, cal.n_days) == (W.GRAY_FROM, W.GRAY_TO, W.N_DAYS)


def test_an_absent_change_never_happens() -> None:
    cal = W.Calendar(changes_present=(W.TOOL_ROLLOUT,))
    assert cal.vpn_at == cal.migration_at == W.NEVER
    assert cal.rollout_at == W.ROLLOUT_DAY
    assert cal.vpn_change_day == W.VPN_CHANGE_DAY  # the drawn day stays for provenance


@pytest.mark.parametrize(
    "bad",
    [
        {"n_days": 100},
        {"vpn_change_day": 180},
        {"rollout_day": -1},
        {"crunch_start": 178, "crunch_len": 4},
        {"crunch_len": -1},
        {"gray_from": 150, "gray_to": 140},
        {"gray_to": 180},
        {"changes_present": ("vpn_change", "vpn_change")},
        {"changes_present": ("holiday",)},
    ],
)
def test_bad_calendars_are_refused(bad: dict) -> None:
    with pytest.raises(ValueError):
        W.Calendar(**bad)


@pytest.mark.parametrize("n_days", [W.N_DAYS, 365])
def test_drawn_calendars_respect_ranges_and_gaps(n_days: int) -> None:
    ranges = W.CalendarRanges(n_days=n_days)
    lo = ranges.eval_from + ranges.change_from_offset
    hi = n_days - ranges.change_end_margin
    change_days, present = set(), 0
    for i in range(N_DRAWS):
        cal = W.draw_calendar(random.Random(i), ranges)
        days = sorted((cal.vpn_change_day, cal.rollout_day, cal.migration_day))
        assert lo <= days[0] and days[-1] <= hi
        assert all(b - a >= ranges.min_change_gap for a, b in zip(days, days[1:]))
        assert ranges.eval_from <= cal.crunch_start <= n_days - ranges.crunch_end_margin
        assert cal.crunch_len == ranges.crunch_len
        assert ranges.eval_from + 3 <= cal.gray_from <= ranges.eval_from + 10
        assert n_days - 10 <= cal.gray_to <= n_days - 5
        assert cal.n_days == n_days
        change_days.update(days)
        present += len(cal.changes_present)
    assert change_days == set(range(lo, hi + 1))  # every allowed day is reachable
    share = present / (N_DRAWS * len(W.ORG_CHANGES))
    assert abs(share - ranges.change_present_p) < PRESENT_TOLERANCE


def test_each_change_takes_every_rank() -> None:
    """The changes are not always in today's order (VPN, then rollout, then migration)."""
    firsts = set()
    for i in range(200):
        cal = W.draw_calendar(random.Random(i))
        days = {"vpn": cal.vpn_change_day, "rollout": cal.rollout_day, "mig": cal.migration_day}
        firsts.add(min(days, key=days.get))
    assert firsts == {"vpn", "rollout", "mig"}


def test_impossible_ranges_raise() -> None:
    narrow = W.CalendarRanges(n_days=W.MIN_N_DAYS, eval_from=90, change_end_margin=20)
    with pytest.raises(ValueError, match="cannot hold"):
        W.draw_calendar(random.Random(0), narrow)


def test_seeded_calendar_is_a_function_of_the_seed() -> None:
    assert W.seeded_calendar(17) == W.seeded_calendar(17)
    assert len({W.seeded_calendar(seed) for seed in range(20)}) > 1


def test_world_follows_a_moved_calendar() -> None:
    world = world_on(MOVED)
    rows = calls(world)
    migrated = [utc_day(r) for r in rows if r[4] and r[4].startswith("platform/")]
    assert migrated and min(migrated) >= MOVED.migration_day - TZ_SLACK_DAYS
    tagged = [utc_day(r) for r in rows if "org_repo_migration" in r[11]]
    assert tagged
    assert all(MOVED.migration_day - 1 <= d <= MOVED.migration_day + 3 for d in tagged)
    new_tools = [utc_day(r) for r in rows if r[3] in W.NEW_TOOLS]
    assert new_tools and min(new_tools) >= MOVED.rollout_day - TZ_SLACK_DAYS
    crunch = [utc_day(r) for r in rows if "release_crunch" in r[11]]
    assert crunch
    assert all(150 - TZ_SLACK_DAYS <= d <= 153 + TZ_SLACK_DAYS for d in crunch)
    vpn_new = [utc_day(r) for rs in world.values() for r in rs if r[7].startswith("100.90.")]
    assert vpn_new and min(vpn_new) >= MOVED.vpn_change_day - TZ_SLACK_DAYS


def test_gray_episodes_start_in_the_gray_window() -> None:
    world = world_on(MOVED)
    first_day: dict[str, int] = {}
    for rs in world.values():
        for r in rs:
            if r[12]:
                first_day[r[12]] = min(first_day.get(r[12], 10**9), utc_day(r))
    assert first_day
    back, forward = DAY_OF_WEEK_SHIFT
    lo = MOVED.gray_from - back - TZ_SLACK_DAYS
    hi = MOVED.gray_to + forward + TZ_SLACK_DAYS
    for ep, day in first_day.items():
        kind = W.parse_episode(ep).kind
        # scope creep's first extra read can come on any of its 15 days
        last = hi + CREEP_DAYS if kind in ("scope_creep", W.BOT_SCOPE_CREEP) else hi
        assert lo <= day <= last, (ep, day)


def test_weekend_batch_stays_inside_the_horizon() -> None:
    """A weekend batch drawn on the last Monday of a window ending on day 175 (a drawn
    calendar can) would move to day 180, past the horizon; it takes the Saturday before."""
    calendar = W.Calendar(gray_to=LATE_GRAY_TO)
    spec = W.Spec("dev-000", "dev", 0, 0)
    days = []
    for seed in range(N_PLANS):
        rng = random.Random(seed)
        plan = W.gray_plan_for(spec, rng, W.Profile(), calendar=calendar, kinds=WEEKEND_ONLY)
        days += [day for day, _, _ in plan]
    assert len(days) > N_PLANS // 2
    assert max(days) == calendar.n_days - 7  # the last Saturday inside the horizon
    assert all(day % 7 == SATURDAY_OF_WEEK for day in days)


def test_absent_changes_leave_no_trace() -> None:
    world = world_on(replace(MOVED, changes_present=()))
    rows = calls(world)
    assert not [r for r in rows if r[4] and r[4].startswith("platform/")]
    assert not [r for r in rows if r[3] in W.NEW_TOOLS]
    assert not [r for rs in world.values() for r in rs if r[7].startswith("100.90.")]
    org_tags = ("org_repo_migration", "org_tool_rollout", "org_vpn_change")
    assert not [r for rs in world.values() for r in rs if any(t in r[11] for t in org_tags)]
