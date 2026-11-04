"""EV-08: a roster that scales with the organisation's size, churn (hires and leavers all
year, family W8) and gray episodes for bots. Synthetic rosters and worlds.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import replace

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

BOT_ROLES = ("ci_bot", "triage_bot", "report_bot")
CHURN_SEEDS = range(40)
CHURN_TOLERANCE = 0.15  # relative, on the mean over 40 rosters of 150 agents
TZ_SLACK_DAYS = 1  # a row's UTC day can be one off its local (simulation) day
RATE_BOTS = 500  # bots per role for the mean of bot_gray_plan_for's episode count
RATE_TOLERANCE = 0.1  # on a mean of 500 Poisson(0.4) counts: SD about 0.03
#: a 150-day calendar: every change and the gray window inside the horizon
SHORT = W.Calendar(n_days=150, vpn_change_day=100, rollout_day=110, migration_day=120, gray_to=140)


def counts(specs: list[W.Spec]) -> tuple[Counter, int, int]:
    """(bots by role, hires, regular people)."""
    bots = Counter(s.role for s in specs if s.role in BOT_ROLES)
    hires = sum(1 for s in specs if s.role in W.ROLE_TOOLS and s.start)
    people = sum(1 for s in specs if s.role in W.ROLE_TOOLS and not s.start)
    return bots, hires, people


@pytest.mark.parametrize("seed", [1, 7, 11, 21])
def test_scaled_roster_at_150_is_todays(seed: int) -> None:
    assert W.scaled_roster(150, seed) == W.roster(150, seed)
    assert W.world_roster(150, seed, options=W.V5_OPTIONS) == W.roster(150, seed)


def test_scaled_roster_at_50() -> None:
    bots, hires, people = counts(W.scaled_roster(50, 7))
    assert bots == Counter({"ci_bot": 4, "triage_bot": 1, "report_bot": 2})
    assert (sum(bots.values()), hires, people) == (7, 3, 40)


def test_tiny_organisations() -> None:
    bots, hires, people = counts(W.scaled_roster(5, 7))
    assert (bots, hires, people) == (Counter({"ci_bot": 1}), 1, 3)
    with pytest.raises(ValueError, match="no regular people"):
        W.scaled_roster(2, 7)


@pytest.mark.parametrize("n", [3, 5, 17, 30, 50, 99, 150, 151, 300, 800])
def test_scaled_roster_shares(n: int) -> None:
    specs = W.scaled_roster(n, 3)
    bots, hires, people = counts(specs)
    assert len(specs) == n
    assert sum(bots.values()) == max(1, round(0.14 * n + 1e-9))
    assert hires == max(1, round(n / 15 + 1e-9))
    assert people >= 1
    assert [s.idx for s in specs] == list(range(n))
    assert len({s.aid for s in specs}) == n


def test_hires_start_in_their_windows() -> None:
    for n_days in (W.N_DAYS, 365):
        specs = W.scaled_roster(300, 9, n_days=n_days)
        starts = sorted(s.start for s in specs if s.start)
        early = starts[: (len(starts) + 1) // 2]
        late = starts[(len(starts) + 1) // 2 :]
        assert all(W.EARLY_HIRE_DAYS[0] <= d <= W.EARLY_HIRE_DAYS[1] for d in early)
        assert all(W.LATE_HIRE_FROM <= d <= n_days - W.HIRE_END_MARGIN for d in late)


def test_legacy_roster_keeps_its_quirk() -> None:
    """v1-v4 always add 21 bots and 10 hires: a 30-agent request gives 31 agents."""
    assert len(W.roster(30, 7)) == 31
    assert W.world_roster(30, 7) == W.roster(30, 7)


def test_legacy_roster_refuses_a_short_horizon() -> None:
    """The v1-v4 roster starts late hires up to day 160: on a 150-day calendar it says so
    instead of failing deep in make_person; the scaled roster fits the horizon."""
    with pytest.raises(ValueError, match="v1-v4 roster needs n_days"):
        W.world_roster(40, 7, calendar=SHORT)
    with pytest.raises(ValueError, match="v1-v4 roster needs n_days"):
        W.build_world(40, 7, calendar=SHORT, world_version=W.WORLD_V4)
    specs = W.world_roster(40, 7, options=W.V5_OPTIONS, calendar=SHORT)
    assert max(s.start for s in specs) <= SHORT.n_days - W.HIRE_END_MARGIN


def test_a_moved_calendar_needs_an_explicit_world_version() -> None:
    """The default v4 world orders repositories by the salted hash(): a drawn calendar must
    say which world it wants."""
    with pytest.raises(ValueError, match="explicit world_version"):
        W.build_world(40, 7, calendar=SHORT)


def test_no_churn_changes_nothing() -> None:
    specs = W.scaled_roster(150, 4)
    assert W.add_churn(specs, 4, 0.0, W.N_DAYS) == specs


@pytest.mark.parametrize("rate", [0.1, 0.3])
def test_churn_rate_is_per_year(rate: float) -> None:
    """Leavers and joiners, annualised over the run, average the stated rate."""
    left, joined = [], []
    for seed in CHURN_SEEDS:
        base = W.scaled_roster(150, seed)
        people = sum(1 for s in base if s.role in W.ROLE_TOOLS)
        out = W.add_churn(base, seed, rate, W.N_DAYS)
        per_year = W.DAYS_PER_YEAR / W.N_DAYS
        left.append(sum(1 for s in out if s.end is not None) / people * per_year)
        joined.append((len(out) - len(base)) / people * per_year)
    assert abs(statistics.mean(left) - rate) < CHURN_TOLERANCE * rate
    assert abs(statistics.mean(joined) - rate) < CHURN_TOLERANCE * rate


def test_leavers_and_joiners_are_valid() -> None:
    base = W.scaled_roster(150, 2)
    out = W.add_churn(base, 2, 0.3, W.N_DAYS)
    assert [replace_end(s) for s in out[: len(base)]] == base  # the base roster is kept
    leavers = [s for s in out if s.end is not None]
    joiners = out[len(base) :]
    assert leavers and joiners
    for s in leavers:
        assert s.role in W.ROLE_TOOLS
        assert s.start + W.MIN_TENURE_DAYS <= s.end <= W.N_DAYS - 1
    for s in joiners:
        assert s.role in W.PEOPLE_ROLES and s.end is None
        assert 1 <= s.start <= W.N_DAYS - W.HIRE_END_MARGIN
    assert [s.idx for s in out] == list(range(len(out)))
    assert len({s.aid for s in out}) == len(out)
    with pytest.raises(ValueError):
        W.add_churn(base, 2, 1.5, W.N_DAYS)


def replace_end(spec: W.Spec) -> W.Spec:
    return W.Spec(spec.aid, spec.role, spec.team, spec.idx, spec.start)


def test_churn_in_a_world() -> None:
    """A leaver has no rows from his last day on; a joiner none before his first; a leaver's
    gray episodes all come before he leaves."""
    options = replace(W.V5_OPTIONS, churn_per_year=0.3)
    specs = W.world_roster(40, 3, options=options)
    world, roles, _ = W.build_world(40, 3, options=options)
    assert set(world) == {s.aid for s in specs} and len(roles) == len(specs)
    leavers = [s for s in specs if s.end is not None]
    assert leavers
    for s in specs:
        days = [int(r[0] // W.DAY) - W.BASE_DAY for r in world[s.aid]]
        if s.start:
            assert min(days) >= s.start - TZ_SLACK_DAYS
        if s.end is not None:
            assert max(days) < s.end + TZ_SLACK_DAYS
    loops = {r[12] for rs in world.values() for r in rs if r[12].startswith(W.BOT_LOOP)}
    assert len(loops) == 1  # 4 CI bots: round(4 x 3 / 12) = 1 stuck loop


@pytest.mark.parametrize("role", BOT_ROLES)
def test_bot_gray_kinds_follow_the_role(role: str) -> None:
    kinds, cal = Counter(), W.DEFAULT_CALENDAR
    for idx in range(60):
        spec = W.Spec(f"{role}-{idx:03d}", role, 0, idx)
        for day, kind, ep in W.bot_gray_plan_for(spec, 5, cal, 3.0):
            kinds[kind] += 1
            assert cal.gray_from - 2 <= day <= cal.gray_to and W.is_workday(day)
            assert ep == W.episode_id(kind, spec.aid, W.parse_episode(ep).index)  # no variant
    assert set(kinds) == set(W.BOT_GRAY_KINDS[role])


@pytest.mark.parametrize("role", BOT_ROLES)
def test_bot_gray_episodes_average_the_rate(role: str) -> None:
    """A bot has Poisson(BOT_GRAY_RATE) gray episodes over the gray window."""
    calendar, rate = W.DEFAULT_CALENDAR, W.BOT_GRAY_RATE
    counts = [
        len(W.bot_gray_plan_for(W.Spec(f"{role}-{i:03d}", role, 0, i), 9, calendar, rate))
        for i in range(RATE_BOTS)
    ]
    assert abs(statistics.mean(counts) - rate) < RATE_TOLERANCE


def test_people_get_no_bot_episodes_and_rate_zero_gives_none() -> None:
    person = W.Spec("dev-000", "dev", 0, 0)
    bot = W.Spec("ci_bot-001", "ci_bot", 0, 1)
    assert W.bot_gray_plan_for(person, 5, W.DEFAULT_CALENDAR, 3.0) == []
    assert W.bot_gray_plan_for(bot, 5, W.DEFAULT_CALENDAR, 0.0) == []


def test_bot_episodes_do_not_move_ordinary_bot_traffic() -> None:
    """A bot's gray episodes draw from their own generators: its other rows are the same."""
    org = W.build_org(5, public_repos=True)
    spec = W.Spec("ci_bot-000", "ci_bot", 0, 0)
    plan = [(130, W.BOT_TOKEN_REUSE, "bot_token_reuse:ci_bot-000:0:plain")]
    quiet = W.gen_bot(spec, org, 5, None, W.Profile(), options=W.V5_OPTIONS)
    busy = W.gen_bot(spec, org, 5, None, W.Profile(), options=W.V5_OPTIONS, gray_plan=plan)
    assert [r for r in busy if not r[12]] == quiet
    assert len(busy) > len(quiet)


def test_random_roster_is_seeded() -> None:
    assert W.scaled_roster(77, 13) == W.scaled_roster(77, 13)
    base = W.scaled_roster(77, 13)
    assert W.add_churn(base, 13, 0.2, W.N_DAYS) == W.add_churn(base, 13, 0.2, W.N_DAYS)
    assert W.add_churn(base, 13, 0.2, W.N_DAYS) != W.add_churn(base, 14, 0.2, W.N_DAYS)
