"""EV-09: plain variants of every gray kind (no giveaways) and their stratified labels; EV-09b:
public repositories in every organisation and the toxic-flow kind; EV-08: the bot gray kinds'
two variants.

A plain episode's hour, /16, client and session opening must each come from the agent's
ordinary habits. Synthetic people, bots and worlds.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict

import pytest

from mcp_security.behaviour.engine import SEQUENCE_WINDOW_S
from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

PERSON_KINDS = [k for k in W.GRAY_KINDS_V5 if k != "scope_creep"]  # scope creep: gen_person
SEEDS = range(15)
CROSS_COPY_SEEDS = range(60)  # enough people whose team owns a public repository
WORKDAY, SATURDAY = 128, 131  # simulation days (day 0 is a Monday)
HOTEL = (150, 7)  # a traveller's hotel /16
LABEL_WORLDS = 2_000
LABEL_TOLERANCE = 0.05  # on a share of 2,000 Bernoulli(0.5) draws: SD about 0.011
#: kinds with k episodes in one world, for the stratified labels
KIND_SIZES = {"bulk_export": 1, "slow_loop": 2, "mass_cleanup": 5, "cross_copy": 9, "x": 40}
SHARES = (0.25, W.PLAIN_SHARE_V5, 0.8)
MIN_OPENED_SHARE = 0.8  # plain sessions that open with initialize (the resume rate is 3%)
MIN_SENSITIVE_SOURCE = 4
BOT_POOL = ((20, 1), (20, 2), (3, 4))
BOT_TEAM = 2
MAX_PLAIN_JOB_CALLS = 5
LOOP_BOTS = (2, 3)  # CI bots (world seed 5) of both habits: 2 initializes, 3 is stateless
TS_EPS = 1e-3  # seconds: float error on a difference of two Unix timestamps


def net16(address: str) -> tuple[int, int]:
    a, b, *_ = address.split(".")
    return int(a), int(b)


def local_hour(p: W.Person, day: int, ts: float) -> float:
    tz = p.tz + (W.TRAVEL_HOURS_AHEAD if day in p.travel else 0)
    return (ts - (W.BASE_DAY + day) * W.DAY) / W.HOUR + tz


def plain_hour_window(p: W.Person) -> tuple[float, float]:
    """The local hours a plain episode starts in: a usual working hour of the person's."""
    return p.start_h + 1, p.start_h + max(1.5, p.span - 2)


def ordinary_networks(p: W.Person, day: int) -> set[tuple[int, int]]:
    """The /16s a person uses on an ordinary ``day`` (the carrier hop aside)."""
    vpn = W.VPN_NEW if day >= p.calendar.vpn_at else W.VPN_OLD
    nets = {W.OFFICE, vpn, W.home_network(p, day)}
    if day in p.travel:
        nets.add(p.travel[day])
    return nets


def run_episode(
    kind: str, variant: str, seed: int, *, travel: tuple[int, int] | None = None
) -> tuple[W.Person, W.Org, int, str, list]:
    """One person's gray episode of ``kind``, rows unsorted (as emitted). ``travel``: the
    person is on a trip on the episode's day, at this hotel /16."""
    org = W.build_org(seed, public_repos=True)
    spec = W.Spec("dev-900", "dev", seed % W.N_TEAMS, 900)
    rng = random.Random(seed)
    p = W.make_person(spec, rng, W.Profile())
    day = SATURDAY if kind == "off_hours_batch" else WORKDAY
    if travel is not None:
        p.travel = {day: travel}
    em = W.Emitter(rng, W.Profile(), resp_rng=random.Random(seed))
    prefs = W.repo_prefs(p, org, day, rng, stable_order=True)
    family = p.switch_to if day >= p.switch_day else p.family
    client = f"{family}/1.{day // 30}.0"
    ep = W.episode_id(kind, spec.aid, 0, variant)
    W.gray_episode(em, p, org, day, kind, ep, client, prefs, rng, variant=variant)
    return p, org, day, client, em.rows


def sessions(rows: list) -> dict[str, list]:
    out: dict[str, list] = defaultdict(list)
    for r in rows:
        out[r[2]].append(r)
    return out


def first_call(rows: list) -> float:
    return min(r[0] for r in rows if r[1] == "tools/call")


def housekeeping(rows: list) -> list[tuple[float, str]]:
    return sorted((r[0], r[1]) for r in rows if r[1] != "tools/call")


def opens_like_a_person(rows: list) -> bool:
    """Assert one session opens as a person's ordinary ones do: nothing (a resumed session),
    or ``initialize`` 1 s before the first call, maybe then ``tools/list`` half a second
    before it. Return whether it sent ``initialize``."""
    start = first_call(rows)
    init = (start - W.PERSON_INITIALIZE_LEAD_S, "initialize")
    listed = (start - W.PERSON_TOOLS_LIST_LEAD_S, "tools/list")
    assert housekeeping(rows) in ([], [init], [init, listed])
    return bool(housekeeping(rows))


# ── EV-09: variant labels ────────────────────────────────────────────────────────────────
def test_stratified_variants_split_each_kind_within_one() -> None:
    ids = [W.episode_id(k, f"dev-{i:03d}", 0) for k, n in KIND_SIZES.items() for i in range(n)]
    for share in SHARES:
        labels = W.stratified_variants(ids, 7, share)
        assert set(labels) == set(ids)
        assert all(labels[ep].startswith(f"{ep}:") for ep in ids)  # the id keeps its 3 parts
        plain = Counter(W.parse_episode(v).kind for v in labels.values() if v.endswith("plain"))
        for kind, n in KIND_SIZES.items():
            assert abs(plain[kind] - share * n) < 1, (share, kind)
        assert W.stratified_variants(list(reversed(ids)), 7, share) == labels  # order-free


def test_stratified_variants_are_exact_in_expectation() -> None:
    """A kind with one episode is plain in about half of the worlds."""
    one = W.episode_id("bulk_export", "dev-001", 0)
    plain = sum(
        W.parse_episode(W.stratified_variants([one], seed, W.PLAIN_SHARE_V5)[one]).variant
        == W.PLAIN
        for seed in range(LABEL_WORLDS)
    )
    assert abs(plain / LABEL_WORLDS - W.PLAIN_SHARE_V5) < LABEL_TOLERANCE


def test_stratified_variants_edges() -> None:
    ids = [W.episode_id("bulk_export", f"dev-{i:03d}", 0) for i in range(5)]
    assert W.stratified_variants(ids, 7, 0.0) == {ep: ep for ep in ids}  # v1-v4 ids
    every = W.stratified_variants(ids, 7, 1.0).values()
    assert {W.parse_episode(ep).variant for ep in every} == {W.PLAIN}
    with pytest.raises(ValueError, match="unlabelled"):
        W.stratified_variants([f"{ids[0]}:plain"], 7, 0.5)
    with pytest.raises(ValueError, match="distinct"):
        W.stratified_variants([ids[0], ids[0]], 7, 0.5)
    with pytest.raises(ValueError, match="plain_share"):
        W.stratified_variants(ids, 7, 1.5)


def test_world_variants_are_stratified(v5_world: tuple) -> None:
    """In a world, each kind's plain count is within one episode of half its episodes (scope
    creep aside: an episode whose 15 days fall on leave leaves no row)."""
    world, _, _ = v5_world
    variants: dict[str, Counter] = defaultdict(Counter)
    for rows in world.values():
        for ep in {r[12] for r in rows if r[12]}:
            parsed = W.parse_episode(ep)
            variants[parsed.kind][parsed.variant] += 1
    variants.pop("scope_creep", None)
    assert len(variants) >= len(PERSON_KINDS) // 2
    for kind, count in variants.items():
        assert abs(count[W.PLAIN] - W.PLAIN_SHARE_V5 * count.total()) < 1, (kind, count)


def test_parse_episode() -> None:
    legacy = W.parse_episode("bulk_export:dev-001:2")
    assert legacy == W.Episode("bulk_export", "dev-001", 2, W.CLASSIC)
    assert W.parse_episode("toxic_flow:dev-001:0:plain").variant == W.PLAIN
    assert W.episode_id("x", "dev-001", 3, W.PLAIN) == "x:dev-001:3:plain"
    for bad in ("x", "a:b:c:weird", "a:b:notint", "a:b:1:plain:extra"):
        with pytest.raises(ValueError):
            W.parse_episode(bad)


# ── EV-09: plain episodes look ordinary ──────────────────────────────────────────────────
@pytest.mark.parametrize("kind", PERSON_KINDS)
def test_plain_episode_keeps_hours_network_client_and_session(kind: str) -> None:
    for seed in SEEDS:
        p, _, day, client, rows = run_episode(kind, W.PLAIN, seed)
        assert [r for r in rows if r[1] == "tools/call"]
        lo, hi = plain_hour_window(p)
        assert lo <= local_hour(p, day, first_call(rows)) <= hi
        for sid, rs in sessions(rows).items():
            assert sid.startswith(f"{p.spec.aid}-{day}-") and not sid.endswith("-g")
            assert p.start_h <= local_hour(p, day, first_call(rs)) <= p.start_h + p.span
            assert sum(r[1] == "initialize" for r in rs) <= 1
        for r in rows:
            assert net16(r[7]) in ordinary_networks(p, day), (kind, seed, r[7])
            assert r[8] == client


@pytest.mark.parametrize("kind", PERSON_KINDS)
def test_plain_sessions_open_like_the_persons_own(kind: str) -> None:
    """A plain session sends initialize 1 s before its first call, as 97% of the person's
    ordinary sessions do (3% resume), never the shadow script's missing handshake."""
    opened, total = 0, 0
    for seed in SEEDS:
        *_, rows = run_episode(kind, W.PLAIN, seed)
        for rs in sessions(rows).values():
            opened += opens_like_a_person(rs)
            total += 1
    assert opened >= MIN_OPENED_SHARE * total, (kind, opened, total)


@pytest.mark.parametrize("kind", PERSON_KINDS)
def test_plain_episode_on_a_travel_day_keeps_the_trips_hours_and_network(kind: str) -> None:
    """On a trip, a plain episode starts in a usual working hour of the trip's time zone (7
    hours ahead) and comes from the hotel (the plain shadow script runs at home)."""
    for seed in SEEDS:
        p, _, day, _, rows = run_episode(kind, W.PLAIN, seed, travel=HOTEL)
        lo, hi = plain_hour_window(p)
        assert lo <= local_hour(p, day, first_call(rows)) <= hi, (kind, seed)
        nets = {net16(r[7]) for r in rows}
        assert nets == ({W.home_network(p, day)} if kind == "shadow_script" else {HOTEL})


@pytest.mark.parametrize("kind", ["shadow_script", "off_hours_batch"])
def test_classic_episodes_keep_their_giveaways(kind: str) -> None:
    """The classic variant is v1-v4's: the night hour, and for the shadow script the cloud
    network, ``python-requests`` and no handshake."""
    for seed in SEEDS:
        p, _, day, _, rows = run_episode(kind, W.CLASSIC, seed)
        calls = [r for r in rows if r[1] == "tools/call"]
        start = (min(r[0] for r in calls) - (W.BASE_DAY + day) * W.DAY) / W.HOUR + p.tz
        assert 1.0 <= start <= 3.0
        if kind == "shadow_script":
            assert all(net16(r[7]) in W.CLOUD_POOL for r in rows)
            assert all(r[8].startswith("python-requests/") for r in rows)
            assert not [r for r in rows if r[1] == "initialize"]
        else:
            assert rows[0][1] == "initialize" and rows[0][2].endswith("-g")


@pytest.mark.parametrize("kind", [k for k in PERSON_KINDS if k != "shadow_script"])
def test_classic_sessions_always_initialize(kind: str) -> None:
    """v1-v4: every classic session but the shadow script's opens with initialize, 1 s ahead."""
    for seed in SEEDS:
        *_, rows = run_episode(kind, W.CLASSIC, seed)
        (rs,) = sessions(rows).values()
        assert housekeeping(rs) == [(first_call(rs) - 1.0, "initialize")]


def test_plain_cross_copy_splits_the_session_inside_the_window() -> None:
    """The session split (N16): reads in one session, writes in a new one, the first write
    within E5's read-then-write window of the last read."""
    for seed in SEEDS:
        _, _, _, _, rows = run_episode("cross_copy", W.PLAIN, seed)
        calls = [r for r in rows if r[1] == "tools/call"]
        reads = [r for r in calls if r[3] == "get_file_contents"]
        writes = [r for r in calls if r[3] == "create_or_update_file"]
        assert reads and writes
        assert len({r[2] for r in reads}) == 1 and len({r[2] for r in writes}) == 1
        assert reads[0][2] != writes[0][2]
        pause = min(r[0] for r in writes) - max(r[0] for r in reads)
        lo, hi = W.CROSS_COPY_PAUSE_S
        assert lo - TS_EPS <= pause <= hi + TS_EPS
    assert W.CROSS_COPY_PAUSE_S[1] < SEQUENCE_WINDOW_S


def test_classic_cross_copy_stays_in_one_session() -> None:
    for seed in SEEDS:
        _, _, _, _, rows = run_episode("cross_copy", W.CLASSIC, seed)
        assert len({r[2] for r in rows}) == 1


@pytest.mark.parametrize("variant", W.VARIANTS)
def test_cross_copy_never_writes_into_a_public_repository(variant: str) -> None:
    """A write into a public repository after a sensitive read is the toxic flow, a kind of
    its own; cross_copy keeps to the team's non-public repositories."""
    teams_with_public = 0
    for seed in CROSS_COPY_SEEDS:
        p, org, _, _, rows = run_episode("cross_copy", variant, seed)
        writes = [r for r in rows if r[3] == "create_or_update_file"]
        assert writes and all(r[W.EXPOSURE_COLUMN] != W.EXPOSURE_PUBLIC for r in writes)
        teams_with_public += any(r in org.public for r in org.team_repos[p.spec.team])
    assert teams_with_public  # some of these teams own a public repository


def test_plain_episodes_look_ordinary_in_the_world(v5_world: tuple) -> None:
    """In a whole world, every plain episode's /16 and client were also used on the agent's
    ordinary rows, and it starts in an hour the agent ordinarily calls in."""
    world, roles, _ = v5_world
    checked = 0
    for aid, rows in world.items():
        ordinary = [r for r in rows if not r[12]]
        nets = {net16(r[7]) for r in ordinary}
        clients = {r[8].split("/")[0] for r in ordinary}
        hours = {int((r[0] % W.DAY) // W.HOUR) for r in ordinary if r[1] == "tools/call"}
        episodes: dict[str, list] = defaultdict(list)
        for r in rows:
            if r[12] and W.parse_episode(r[12]).variant == W.PLAIN:
                episodes[r[12]].append(r)
        for ep, rs in episodes.items():
            assert all(net16(r[7]) in nets for r in rs), ep
            assert all(r[8].split("/")[0] in clients for r in rs), ep
            first = min(r[0] for r in rs)
            assert int((first % W.DAY) // W.HOUR) in hours, ep
            checked += 1
    assert checked >= 5


# ── EV-09b: public repositories ──────────────────────────────────────────────────────────
def test_every_v5_organisation_has_public_repositories() -> None:
    def key(r: W.Repo) -> tuple:
        return (r.name, r.team, r.sens, r.created, r.migrated)

    for seed in range(20):
        legacy, org = W.build_org(seed), W.build_org(seed, public_repos=True)
        team_public = [r for r in org.public if r.team is not None]
        assert W.TEAM_PUBLIC_REPOS[0] <= len(team_public) <= W.TEAM_PUBLIC_REPOS[1]
        assert [r.name for r in org.public if r.team is None] == list(W.SHARED_PUBLIC_REPOS)
        for r in org.public:
            assert (r.exposure, r.sens, r.migrated) == (W.EXPOSURE_PUBLIC, W.PUBLIC_SENS, False)
        assert all(r in org.team_repos[r.team] for r in team_public)
        assert all(r in org.shared for r in org.public if r.team is None)
        # the rest of the organisation is the v1-v4 one
        assert [key(r) for r in org.repos if r not in org.public] == [key(r) for r in legacy.repos]
        assert legacy.public == []


def test_exposure_follows_sensitivity() -> None:
    assert W.Repo("a", 1, W.PRIVATE_FROM_SENS).exposure == W.EXPOSURE_PRIVATE
    assert W.Repo("a", 1, W.PRIVATE_FROM_SENS - 1).exposure == W.EXPOSURE_INTERNAL
    assert W.Repo("a", 1, 2, exposure=W.EXPOSURE_PUBLIC).exposure == W.EXPOSURE_PUBLIC


def test_migration_renames_but_keeps_the_owner() -> None:
    """The migration is a rename inside the organisation: ``platform/<name>``, same owner."""
    org = W.build_org(3)
    moved = [r for r in org.repos if r.migrated]
    assert moved
    for r in moved:
        after = r.migration_day
        assert r.name_on(after - 1) == r.name
        assert r.name_on(after) == f"{W.MIGRATED_NAMESPACE}/{r.name}"
        assert r.owner == W.ORG_OWNER


def test_public_repositories_get_ordinary_reads_and_writes(v5_world: tuple) -> None:
    world, _, _ = v5_world
    public = [
        r
        for rows in world.values()
        for r in rows
        if r[1] == "tools/call" and not r[12] and r[W.EXPOSURE_COLUMN] == W.EXPOSURE_PUBLIC
    ]
    assert public
    assert {r[6] for r in public} >= {"write", "read"}


# ── EV-09b: toxic flow ───────────────────────────────────────────────────────────────────
def test_toxic_flow_classic_pushes_into_a_new_personal_public_repository() -> None:
    for seed in SEEDS:
        p, org, _, _, rows = run_episode(W.TOXIC_FLOW, W.CLASSIC, seed)
        calls = [r for r in rows if r[1] == "tools/call"]
        reads = [r for r in calls if r[3] == "get_file_contents"]
        writes = calls[len(reads) :]
        assert reads and calls[: len(reads)] == reads  # every read comes first
        assert len({r[4] for r in reads}) == 1 and reads[0][5] >= MIN_SENSITIVE_SOURCE
        assert writes[0][3] == "create_repository" and len(writes) >= 2
        assert {r[3] for r in writes[1:]} == {"push_files"}
        for r in writes:
            assert r[4].startswith(f"{p.spec.aid}/") and r[5] == W.PUBLIC_SENS
            assert r[W.EXPOSURE_COLUMN] == W.EXPOSURE_PUBLIC
            assert r[W.OWNER_COLUMN] == f"{W.PERSONAL_OWNER_PREFIX}{p.spec.aid}"
        assert not {r[4] for r in writes} & {r.name for r in org.repos}


def test_toxic_flow_plain_writes_into_an_organisation_public_repository() -> None:
    for seed in SEEDS:
        _, org, _, _, rows = run_episode(W.TOXIC_FLOW, W.PLAIN, seed)
        calls = [r for r in rows if r[1] == "tools/call"]
        reads = [r for r in calls if r[3] == "get_file_contents"]
        writes = [r for r in calls if r[6] == "write"]
        assert reads and reads[0][5] >= MIN_SENSITIVE_SOURCE
        assert writes and {r[3] for r in writes} == {"create_or_update_file"}
        assert {r[4] for r in writes} <= {r.name for r in org.public}
        assert {r[W.OWNER_COLUMN] for r in writes} == {W.ORG_OWNER}
        assert max(r[0] for r in reads) < min(r[0] for r in writes)


def test_toxic_flow_needs_public_repositories() -> None:
    with pytest.raises(ValueError, match="public_repos"):
        W.WorldOptions(toxic_flow=True)
    org = W.build_org(1)
    spec = W.Spec("dev-900", "dev", 1, 900)
    rng = random.Random(1)
    p = W.make_person(spec, rng, W.Profile())
    em = W.Emitter(rng, W.Profile())
    prefs = W.repo_prefs(p, org, WORKDAY, rng)
    with pytest.raises(ValueError, match="public repositories"):
        W.gray_episode(em, p, org, WORKDAY, W.TOXIC_FLOW, "e", "cursor/1", prefs, rng)


def test_unknown_kinds_and_variants_are_refused() -> None:
    with pytest.raises(ValueError, match="unknown gray kind"):
        run_episode("teleport", W.CLASSIC, 0)
    with pytest.raises(ValueError, match="unknown variant"):
        run_episode("bulk_export", "loud", 0)


# ── EV-08: bot gray kinds ────────────────────────────────────────────────────────────────
def run_bot(
    kind: str, variant: str, role: str = "ci_bot", seed: int = 5, *, initializes: bool = True
) -> tuple:
    org = W.build_org(seed, public_repos=True)
    spec = W.Spec(f"{role}-000", role, BOT_TEAM, 0)
    teams = (BOT_TEAM,) if role == "ci_bot" else ()
    habits = W.BotHabits(role, "mcp/1.2.0", BOT_POOL, initializes, teams)
    em = W.Emitter(random.Random(seed), W.Profile(), resp_rng=random.Random(seed))
    ep = W.episode_id(kind, spec.aid, 0, variant)
    W.bot_gray_episode(em, spec, org, WORKDAY, kind, ep, habits, random.Random(seed))
    return org, habits, em.rows


def repo_team(org: W.Org, asset: str) -> int | None:
    name = asset.removeprefix(f"{W.MIGRATED_NAMESPACE}/")
    return next(r.team for r in org.repos if r.name == name)


@pytest.mark.parametrize("role", ["ci_bot", "triage_bot", "report_bot"])
def test_bot_token_reuse_variants(role: str) -> None:
    _, habits, classic = run_bot(W.BOT_TOKEN_REUSE, W.CLASSIC, role)
    assert all(r[8].split("/")[0] in W.HUMAN_CLIENTS for r in classic)
    assert all(net16(r[7]) in W.HOME_POOL for r in classic)
    _, habits, plain = run_bot(W.BOT_TOKEN_REUSE, W.PLAIN, role)
    assert all(r[8] == habits.client and net16(r[7]) in habits.networks for r in plain)
    lo, hi = W.BOT_USUAL_HOURS[role]
    first = min(r[0] for r in plain if r[1] == "tools/call")
    assert lo <= (first % W.DAY) / W.HOUR <= hi
    assert {r[3] for r in plain if r[1] == "tools/call"} <= set(W.PERSON_LIKE_TOOLS)


def test_bot_scope_creep_variants() -> None:
    org, habits, classic = run_bot(W.BOT_SCOPE_CREEP, W.CLASSIC)
    calls = [r for r in classic if r[1] == "tools/call"]
    assert calls and all(repo_team(org, r[4]) not in (None, BOT_TEAM) for r in calls)
    assert all(net16(r[7]) not in habits.networks for r in classic)
    assert len({r[2] for r in classic}) == 1
    org, habits, plain = run_bot(W.BOT_SCOPE_CREEP, W.PLAIN)
    calls = [r for r in plain if r[1] == "tools/call"]
    days = {int(r[0] // W.DAY) for r in calls}
    assert len(days) > 1  # creeping over days, a few jobs at a time
    assert all(repo_team(org, r[4]) not in (None, BOT_TEAM) for r in calls)
    assert all(net16(r[7]) in habits.networks and r[8] == habits.client for r in plain)


def test_bot_misconfigured_writer_variants() -> None:
    _, _, classic = run_bot(W.BOT_MISCONFIGURED_WRITER, W.CLASSIC)
    assert len({r[2] for r in classic}) == 1 and len(classic) >= 200
    assert {r[3] for r in classic} == {"update_issue"} and len({r[4] for r in classic}) == 1
    _, habits, plain = run_bot(W.BOT_MISCONFIGURED_WRITER, W.PLAIN)
    calls = [r for r in plain if r[1] == "tools/call"]
    assert len(calls) >= 60 and len({r[4] for r in calls}) == 1
    per_session = defaultdict(int)
    for r in calls:
        per_session[r[2]] += 1
    assert max(per_session.values()) <= MAX_PLAIN_JOB_CALLS
    assert all(net16(r[7]) in habits.networks for r in plain)


PLAIN_BOT_CASES = [
    (W.BOT_TOKEN_REUSE, "ci_bot"),
    (W.BOT_TOKEN_REUSE, "triage_bot"),
    (W.BOT_TOKEN_REUSE, "report_bot"),
    (W.BOT_SCOPE_CREEP, "ci_bot"),
    (W.BOT_MISCONFIGURED_WRITER, "ci_bot"),
    (W.BOT_MISCONFIGURED_WRITER, "triage_bot"),
]


@pytest.mark.parametrize("initializes", [True, False])
@pytest.mark.parametrize(("kind", "role"), PLAIN_BOT_CASES)
def test_plain_bot_sessions_initialize_exactly_when_the_bot_does(
    kind: str, role: str, initializes: bool
) -> None:
    """Each plain session opens as the bot's jobs do: initialize half a second before its
    first call when the bot sends one, nothing for a stateless bot."""
    _, _, rows = run_bot(kind, W.PLAIN, role, initializes=initializes)
    groups = sessions(rows)
    assert groups
    for rs in groups.values():
        lead = [(first_call(rs) - W.BOT_INITIALIZE_LEAD_S, "initialize")]
        assert housekeeping(rs) == (lead if initializes else [])


def test_plain_stuck_loop_opens_like_the_bots_jobs() -> None:
    """The plain stuck CI loop sends initialize exactly when the bot's own jobs do (checked on
    CI bots of both habits) and keeps its jittered gaps."""
    org = W.build_org(5, public_repos=True)
    habits_seen = set()
    for idx in LOOP_BOTS:
        spec = W.Spec(f"ci_bot-{idx:03d}", "ci_bot", 0, idx)
        ep = W.episode_id(W.BOT_LOOP, spec.aid, 0, W.PLAIN)
        rows = W.gen_bot(spec, org, 5, WORKDAY, W.Profile(), options=W.V5_OPTIONS, loop_episode=ep)
        ordinary = sessions([r for r in rows if not r[12]])
        initializes = any(r[1] == "initialize" for rs in ordinary.values() for r in rs)
        habits_seen.add(initializes)
        (loop,) = sessions([r for r in rows if r[12] == ep]).values()
        lead = [(first_call(loop) - W.BOT_INITIALIZE_LEAD_S, "initialize")]
        assert housekeeping(loop) == (lead if initializes else [])
        gaps = {round(b[0] - a[0], 6) for a, b in zip(loop[1:], loop[2:]) if a[1] == b[1]}
        assert len(gaps) > 1  # not v1-v4's exact one second
    assert habits_seen == {True, False}


def test_unknown_bot_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown bot gray kind"):
        run_bot("bot_teleport", W.CLASSIC)


def test_plain_bot_episodes_look_ordinary_in_the_world(v5_world: tuple) -> None:
    world, roles, _ = v5_world
    checked = 0
    for aid, rows in world.items():
        if roles[aid] in W.ROLE_TOOLS:
            continue
        ordinary = [r for r in rows if not r[12]]
        nets, clients = {net16(r[7]) for r in ordinary}, {r[8] for r in ordinary}
        for r in rows:
            if r[12] and W.parse_episode(r[12]).variant == W.PLAIN:
                assert net16(r[7]) in nets and r[8] in clients
                checked += 1
    assert checked  # the fixture world has plain bot episodes
