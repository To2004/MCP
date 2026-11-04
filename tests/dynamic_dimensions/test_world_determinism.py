"""EV-01: a v5 world is a pure function of (seed, profile, calendar, options) under any
``PYTHONHASHSEED``, and a v4 world is today's world, bit for bit.

The v4 pins were recorded with the pre-v5 ``normal_org_world.py`` (SHA-256 ``abdee621...``,
restored from the pre-v5 backup into a scratch folder) under ``PYTHONHASHSEED=0``: the
new module in v4 mode must give the same digests. Every world here is a development or
synthetic world.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path, run_python

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

#: build_world(31, 7) (main profile, v4) by the pre-v5 code, PYTHONHASHSEED=0: 1,748,200 rows.
#: The legacy roster gives 21 bots and 10 dev hires: no regular people, no on-call night.
PRE_V5_DIGEST_31_7_MAIN = "9bbb3d9f8ac8c5d1957813b2b782e727f075096727c87847320001c2d9f6cb3a"
#: build_world(45, 7), same way: 1,946,548 rows. 14 regular people besides the 21 bots and 10
#: hires (dev, lead, sre and pm), so it pins day-0 people of every role and an SRE's on-call
#: nights (240 incident rows), which the 31-agent world never draws.
PRE_V5_DIGEST_45_7_MAIN = "847790a8ca65463e1023cac205ec1f0136e469c8e7e32ac8bf9bb3241842130f"
LEGACY_PINS = {(31, 7): PRE_V5_DIGEST_31_7_MAIN, (45, 7): PRE_V5_DIGEST_45_7_MAIN}
#: stable_hash pins: a change to the hash would silently move every v5 world
STABLE_HASH_PINS = {
    ("dev-001", 3, "t3-svc0"): 15762701038387241907,
    ("x",): 5395104992458594383,
    (): 16476032584258269876,
    (7, "churn"): 13770846612666293938,
}
HASH_SEEDS = ("1", "2")
SMALL_AGENTS, SMALL_SEED = 12, 3

V5_DIGESTS_CODE = f"""
import normal_org_world as W
from dataclasses import replace
w, r, _ = W.build_world({SMALL_AGENTS}, {SMALL_SEED}, world_version="v5")
print(W.world_digest(w, r))
options = replace(W.V5_OPTIONS, churn_per_year=0.3)
calendar = W.seeded_calendar({SMALL_SEED})
w, r, _ = W.build_world({SMALL_AGENTS}, {SMALL_SEED}, calendar=calendar, options=options)
print(W.world_digest(w, r))
print(W.stable_hash("dev-001", 3, "t3-svc0"))
"""
SALTED_DIGEST_CODE = f"""
import normal_org_world as W
from dataclasses import replace
options = replace(W.V5_OPTIONS, stable_order=False)
w, r, _ = W.build_world({SMALL_AGENTS}, {SMALL_SEED}, options=options)
print(W.world_digest(w, r))
"""
LEGACY_DIGEST_CODE = """
import normal_org_world as W
w, r, _ = W.build_world({n_agents}, {seed})
print(W.world_digest(w, r))
"""


@pytest.mark.parametrize(("parts", "value"), list(STABLE_HASH_PINS.items()))
def test_stable_hash_is_pinned(parts: tuple, value: int) -> None:
    assert W.stable_hash(*parts) == value


def test_stable_hash_is_part_a_formula() -> None:
    digest = hashlib.blake2b(b"dev-001|3|t3-svc0", digest_size=8).digest()
    assert W.stable_hash("dev-001", 3, "t3-svc0") == int.from_bytes(digest, "big")
    assert 0.0 <= W.stable_unit("a", 1) < 1.0
    assert W.stable_rng("a").random() == W.stable_rng("a").random()


def test_v5_world_does_not_depend_on_the_hash_seed() -> None:
    """Two interpreters with different salts build the same v5 worlds, with today's calendar
    and with a drawn calendar plus churn, and agree on stable_hash."""
    outputs = [run_python(V5_DIGESTS_CODE, seed).splitlines() for seed in HASH_SEEDS]
    assert outputs[0] == outputs[1]
    assert len(outputs[0]) == 3
    assert outputs[0][0] != outputs[0][1]  # the calendar and churn did change the world
    assert int(outputs[0][2]) == STABLE_HASH_PINS[("dev-001", 3, "t3-svc0")]


def test_salted_order_does_depend_on_the_hash_seed() -> None:
    """Without the stable order the same world moves with the salt: EV-01 is what fixes it."""
    digests = {run_python(SALTED_DIGEST_CODE, seed) for seed in HASH_SEEDS}
    assert len(digests) == 2


@pytest.mark.parametrize(("n_agents", "seed"), list(LEGACY_PINS))
def test_v4_world_is_the_pre_v5_world(n_agents: int, seed: int) -> None:
    """The legacy world, as dump_vectors.py and normal_org_sim.py build it, is unchanged."""
    code = LEGACY_DIGEST_CODE.format(n_agents=n_agents, seed=seed)
    assert run_python(code, "0") == LEGACY_PINS[(n_agents, seed)]


def test_world_versions_select_the_switches() -> None:
    assert W.options_for(W.WORLD_V4) == W.LEGACY_OPTIONS == W.WorldOptions()
    assert W.options_for(W.WORLD_V5) == W.V5_OPTIONS
    with pytest.raises(ValueError, match="unknown world_version"):
        W.options_for("v3")
    with pytest.raises(ValueError, match="not both"):
        W.build_world(SMALL_AGENTS, SMALL_SEED, world_version="v5", options=W.V5_OPTIONS)


@pytest.mark.parametrize(
    "bad",
    [
        {"churn_per_year": -0.1},
        {"churn_per_year": 1.5},
        {"bot_gray_rate": -1.0},
        {"plain_share": 1.2},
        {"toxic_flow": True, "public_repos": False},
    ],
)
def test_world_options_reject_bad_values(bad: dict) -> None:
    with pytest.raises(ValueError):
        W.WorldOptions(**bad)


def test_world_digest_sees_every_change() -> None:
    world = {"b": [(1.5, "tools/call", "s")], "a": [(0.25, "initialize", None)]}
    base = W.world_digest(world, {"a": "dev", "b": "ci_bot"})
    assert base == W.world_digest(dict(reversed(world.items())), {"a": "dev", "b": "ci_bot"})
    moved = {**world, "b": [(1.5000000001, "tools/call", "s")]}
    assert W.world_digest(moved, {"a": "dev", "b": "ci_bot"}) != base
    assert W.world_digest(world, {"a": "pm", "b": "ci_bot"}) != base
    assert W.world_digest(world) != base


def test_extended_rows_leave_the_other_columns_alone() -> None:
    """Response sizes come from their own generator: the first 13 columns are the same world
    with or without them."""
    plain_rows = replace(W.V5_OPTIONS, extended_rows=False)
    a, ra, _ = W.build_world(SMALL_AGENTS, SMALL_SEED, options=plain_rows)
    b, rb, _ = W.build_world(SMALL_AGENTS, SMALL_SEED, options=W.V5_OPTIONS)
    assert ra == rb
    assert {aid: [r[: len(W.ROW)] for r in rows] for aid, rows in b.items()} == a
    assert all(len(r) == len(W.ROW) for rows in a.values() for r in rows)
    assert all(len(r) == len(W.ROW_V5) for rows in b.values() for r in rows)
    assert W.row_names(plain_rows) == W.ROW and W.row_names(W.V5_OPTIONS) == W.ROW_V5
