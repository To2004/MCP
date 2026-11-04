"""D5: sticky egress addresses. A caller without sign-in is keyed by its client family and its
address (spec 2.1, ``oauth.reported_key``), so the world's addresses decide how many callers
an agent becomes. With ``sticky_addresses`` an agent keeps its egress address; its /16, and
every other column, stay as they were. Synthetic people, bots and worlds.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import replace

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

SMALL_AGENTS, SMALL_SEED = 12, 3
STICKY_SEED = 7
N_PEOPLE = 200
WEEKLY = range(0, W.N_DAYS, 7)
WORKDAY = 128  # a Wednesday in the gray window
ISP_CHANGE_DAY = 100
HOTEL = (150, 7)
TRIP = range(30, 35)
CARRIER_DAYS = range(60)
#: a person's egress outside the carrier pool: two homes, the office, two VPNs and a hotel
MAX_FIXED_ADDRESSES = 6
MIN_CI_RUNNERS = 1_000  # a CI bot's addresses over 180 days: a fresh runner for every job


def net16(address: str) -> tuple[int, int]:
    a, b, *_ = address.split(".")
    return int(a), int(b)


def reported_keys(rows: list[tuple]) -> set[tuple[str, str]]:
    """The callers a gateway sees without sign-in: (client family, address) pairs."""
    return {(r[8].split("/")[0], r[7]) for r in rows}


def people(n: int) -> list[W.Person]:
    out = []
    for i in range(n):
        spec = W.Spec(f"dev-{i:03d}", "dev", i % W.N_TEAMS, i)
        p = W.make_person(spec, random.Random(i), W.Profile())
        p.sticky_seed = STICKY_SEED
        out.append(p)
    return out


# ── the switch ───────────────────────────────────────────────────────────────────────────
def test_sticky_addresses_change_only_the_host() -> None:
    """The v1-v4 host draws are still made: every other column, and every /16, is the world
    without sticky addresses."""
    fresh = replace(W.V5_OPTIONS, sticky_addresses=False)
    a, ra, _ = W.build_world(SMALL_AGENTS, SMALL_SEED, options=fresh)
    b, rb, _ = W.build_world(SMALL_AGENTS, SMALL_SEED, options=W.V5_OPTIONS)
    assert ra == rb and set(a) == set(b)
    moved = 0
    for aid, rows in a.items():
        assert len(rows) == len(b[aid])
        for x, y in zip(rows, b[aid]):
            assert x[:7] + x[8:] == y[:7] + y[8:]
            assert net16(x[7]) == net16(y[7])
            moved += x[7] != y[7]
    assert moved
    assert not W.LEGACY_OPTIONS.sticky_addresses and W.V5_OPTIONS.sticky_addresses


def test_without_sticky_addresses_a_session_draws_a_fresh_host() -> None:
    p = W.make_person(W.Spec("dev-000", "dev", 0, 0), random.Random(0), W.Profile())
    assert W.person_address(p, W.OFFICE, 0, random.Random(1)) == W.ip(W.OFFICE, random.Random(1))
    with pytest.raises(ValueError, match="sticky"):
        W.person_egress(p, W.OFFICE, 0)


# ── a person's egress ────────────────────────────────────────────────────────────────────
def test_office_and_vpns_egress_through_small_nat_pools() -> None:
    """Everyone in the office (or on a VPN) shares a pool of NAT_POOL_SIZE addresses, and a
    person always goes out through the same one."""
    crowd = people(N_PEOPLE)
    pools = []
    for net in W.NAT_NETWORKS:
        pool = {W.person_egress(p, net, day) for p in crowd for day in WEEKLY}
        assert len(pool) == W.NAT_POOL_SIZE
        assert all(net16(a) == net for a in pool)
        for p in crowd:
            assert len({W.person_egress(p, net, day) for day in WEEKLY}) == 1
        pools.append(pool)
    assert not set.intersection(*pools)


def test_home_address_stays_until_the_isp_changes() -> None:
    (p,) = people(1)
    p.isp_change = (ISP_CHANGE_DAY, p.home)  # a new contract, even on the same /16
    before = {W.person_egress(p, p.home, day) for day in range(ISP_CHANGE_DAY)}
    after = {W.person_egress(p, p.home, day) for day in range(ISP_CHANGE_DAY, W.N_DAYS)}
    assert len(before) == len(after) == 1 and before != after


def test_a_hotel_stay_has_one_address_and_a_carrier_day_its_own() -> None:
    (p,) = people(1)
    p.travel = {day: HOTEL for day in TRIP}
    assert len({W.person_egress(p, HOTEL, day) for day in TRIP}) == 1
    carrier = W.CARRIER_POOL[0]
    by_day = [W.person_egress(p, carrier, day) for day in CARRIER_DAYS]
    assert by_day == [W.person_egress(p, carrier, day) for day in CARRIER_DAYS]
    assert all(a != b for a, b in zip(by_day, by_day[1:]))


# ── a world's addresses ──────────────────────────────────────────────────────────────────
def test_people_keep_a_handful_of_addresses(v5_world: tuple) -> None:
    world, roles, _ = v5_world
    for aid, rows in world.items():
        if roles[aid] in W.ROLE_TOOLS:
            ordinary = [r for r in rows if not r[12]]
            fixed = {r[7] for r in ordinary if net16(r[7]) not in W.CARRIER_POOL}
            assert 1 <= len(fixed) <= MAX_FIXED_ADDRESSES, (aid, sorted(fixed))


def test_the_office_nat_puts_several_people_behind_one_address(v5_world: tuple) -> None:
    """Behind the office NAT several people share an address; with the same client family
    they share one reported key, a merge the per-strength results must show (D5)."""
    world, _, _ = v5_world
    users: dict[str, set[str]] = defaultdict(set)
    for aid, rows in world.items():
        for r in rows:
            if net16(r[7]) == W.OFFICE:
                users[r[7]].add(aid)
    assert 1 <= len(users) <= W.NAT_POOL_SIZE
    assert max(len(u) for u in users.values()) >= 2


def test_bots_keep_their_host_and_ci_jobs_get_fresh_runners(v5_world: tuple) -> None:
    world, roles, _ = v5_world
    checked = set()
    for aid, rows in world.items():
        role = roles[aid]
        if role in W.ROLE_TOOLS:
            continue
        addresses = {r[7] for r in rows if not r[12]}
        if role == "ci_bot":
            assert len(addresses) >= MIN_CI_RUNNERS
        else:
            assert len(addresses) == 1
        checked.add(role)
    assert checked == {"ci_bot", "report_bot"}  # the fixture world has no triage bot


@pytest.mark.parametrize("role", ["triage_bot", "report_bot"])
def test_a_bots_plain_episodes_come_from_its_host(role: str) -> None:
    org = W.build_org(5, public_repos=True)
    spec = W.Spec(f"{role}-000", role, 0, 0)
    kinds = W.BOT_GRAY_KINDS[role]
    plan = [
        (WORKDAY + 7 * i, kind, W.episode_id(kind, spec.aid, i, W.PLAIN))
        for i, kind in enumerate(kinds)
    ]
    rows = W.gen_bot(spec, org, 5, None, W.Profile(), options=W.V5_OPTIONS, gray_plan=plan)
    assert {r[12] for r in rows if r[12]} == {ep for _, _, ep in plan}
    assert len({r[7] for r in rows}) == 1


def test_plain_episodes_keep_the_agents_reported_key(v5_world: tuple) -> None:
    """A plain episode comes from one of the agent's own (client family, address) keys, so a
    caller without sign-in brings its history along (CI aside: every job is a new runner)."""
    world, roles, _ = v5_world
    checked = 0
    for aid, rows in world.items():
        if roles[aid] == "ci_bot":
            continue
        own = reported_keys([r for r in rows if not r[12]])
        for r in rows:
            if r[12] and W.parse_episode(r[12]).variant == W.PLAIN:
                assert reported_keys([r]) <= own, (aid, r[12], r[7])
                checked += 1
    assert checked
