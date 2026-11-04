"""Tests for seed derivation and the family ranges (heldout/heldout_world_spec.py, EV-15)."""

from __future__ import annotations

import hashlib

import pytest

from reports.experiments.dynamic_dimensions.heldout import heldout_world_spec as ws

SHA = "0123456789abcdef0123456789abcdef01234567"  # a fixture commit, not a real one
BEACON = "beefcafe" * 16  # a fixture beacon value: 128 hex digits
SALT = "public-dev-salt-fixture"


def _attempt0(text: str, modulus: int) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest(), "big") % modulus


def test_seed_follows_the_preregistered_formula() -> None:
    seed = ws.derive_seed(SHA, "W3", ws.TEST, 7, beacon=BEACON)
    assert seed == _attempt0(f"{SHA}|{BEACON}|W3|test|7", ws.SEED_MODULUS)
    dev = ws.derive_seed(SALT, "W3", ws.DEV, 2)
    assert dev == _attempt0(f"{SALT}|W3|dev|2", ws.SEED_MODULUS)


def test_seed_is_a_pure_function_of_its_arguments() -> None:
    args = (SHA, "W2", ws.CALIBRATION, 3)
    first = ws.derive_seed(*args, beacon=BEACON)
    assert ws.derive_seed(*args, beacon=BEACON) == first
    others = {
        ws.derive_seed("f" * 40, "W2", ws.CALIBRATION, 3, beacon=BEACON),
        ws.derive_seed(SHA, "W2", ws.CALIBRATION, 3, beacon="00" * 64),
        ws.derive_seed(SHA, "W5", ws.CALIBRATION, 3, beacon=BEACON),
        ws.derive_seed(SHA, "W2", ws.TEST, 3, beacon=BEACON),
        ws.derive_seed(SHA, "W2", ws.CALIBRATION, 4, beacon=BEACON),
    }
    assert first not in others and len(others) == 5


def test_a_burnt_value_is_redrawn() -> None:
    modulus = 42  # small, so attempt 0 lands on a burnt seed for some index
    index = next(
        i
        for i in range(10_000)
        if _attempt0(f"{SHA}|{BEACON}|W1|test|{i}", modulus) in ws.BURNT_SEEDS
    )
    seed = ws.derive_seed(SHA, "W1", ws.TEST, index, beacon=BEACON, modulus=modulus)
    base = f"{SHA}|{BEACON}|W1|test|{index}"
    redraws = (_attempt0(f"{base}|{k}", modulus) for k in range(1, 100))
    assert seed == next(v for v in redraws if v not in ws.BURNT_SEEDS)


def test_a_seed_plan_never_repeats_or_burns_even_under_collisions() -> None:
    plan = ws.seed_plan(SHA, BEACON, modulus=600)  # 320 seeds in 600 values: many collisions
    seeds = [s for group in plan.values() for s in group]
    assert len(seeds) == 8 * (10 + 30)
    assert len(set(seeds)) == len(seeds)
    assert not set(seeds) & ws.BURNT_SEEDS


def test_held_out_seeds_avoid_the_dev_seeds() -> None:
    dev = ws.dev_seeds(SALT, modulus=500)
    used = [s for group in dev.values() for s in group]
    assert set(f for f, _ in dev) == set(ws.DEV_FAMILIES) and len(used) == 35
    plan = ws.seed_plan(SHA, BEACON, used=used, modulus=500)
    held_out = {s for group in plan.values() for s in group}
    assert not held_out & set(used)


def test_the_beacon_and_the_salt_are_enforced() -> None:
    with pytest.raises(ValueError, match="beacon"):
        ws.derive_seed(SHA, "W1", ws.TEST, 0)
    with pytest.raises(ValueError, match="salt"):
        ws.derive_seed(SALT, "W2", ws.DEV, 0, beacon=BEACON)
    with pytest.raises(ValueError, match="dev pool"):
        ws.derive_seed(SALT, "W1", ws.DEV, 0)
    with pytest.raises(ValueError, match="hex"):
        ws.derive_seed("not-a-sha", "W1", ws.TEST, 0, beacon=BEACON)
    with pytest.raises(ValueError):
        ws.derive_seed(SHA, "W9", ws.TEST, 0, beacon=BEACON)


def test_one_commit_and_one_pulse_give_one_seed_set() -> None:
    # Case and surrounding space cannot re-roll a seed (R2-12) ...
    seed = ws.derive_seed(SHA, "W1", ws.TEST, 0, beacon=BEACON)
    assert ws.derive_seed(SHA.upper(), "W1", ws.TEST, 0, beacon=BEACON) == seed
    assert ws.derive_seed(f" {SHA}\n", "W1", ws.TEST, 0, beacon=BEACON.upper()) == seed
    # ... and other lengths are refused rather than hashed.
    for short in (SHA[:7], SHA[:12], SHA + "0"):
        with pytest.raises(ValueError, match="40 hex digits"):
            ws.derive_seed(short, "W1", ws.TEST, 0, beacon=BEACON)
    for beacon in (BEACON[:64], BEACON + "00", "z" * ws.BEACON_HEX):
        with pytest.raises(ValueError, match="128 hex digits"):
            ws.derive_seed(SHA, "W1", ws.TEST, 0, beacon=beacon)
    assert ws.canonical_hex(" AB ", 2, "x") == "ab"


def test_world_specs_are_deterministic_and_follow_their_family() -> None:
    spec = ws.world_spec("W4", ws.TEST, 0, 123)
    assert spec == ws.world_spec("W4", ws.TEST, 0, 123)
    assert spec.era == "mixed" and 0.2 <= spec.modern_share <= 0.8
    assert ws.world_spec("W3", ws.TEST, 0, 1).era == "modern"
    assert ws.world_spec("W6", ws.TEST, 0, 1).n_days == ws.LONG_HORIZON_DAYS
    assert ws.world_spec("W7", ws.TEST, 0, 1).routes == ("github", "slack")
    assert 0.10 <= ws.world_spec("W8", ws.TEST, 0, 1).churn_per_year <= 0.30
    assert [ws.world_spec("W1", ws.TEST, i, 5).profile for i in range(3)] == list(ws.PROFILES)
    common = ws.world_spec("W5", ws.TEST, 0, 9)
    assert common.calendar == "random" and common.inputs == "gateway"
    assert common.plain_gray_share == 0.5 and common.toxic_flow and common.public_repos


def test_w2_sizes_span_the_range_with_a_small_route_stratum() -> None:
    sizes = [ws.world_spec("W2", ws.TEST, i, 1_000 + i).n_agents for i in range(200)]
    assert min(sizes) >= 5 and max(sizes) <= 800
    assert 0.15 < sum(s <= 30 for s in sizes) / len(sizes) < 0.45


def test_plan_worlds_and_family_size() -> None:
    plan = ws.seed_plan(SHA, BEACON, {ws.CALIBRATION: 2}, families=("W1", "W2"))
    worlds = ws.plan_worlds(plan)
    assert [(w.family, w.pool, w.index) for w in worlds] == [
        ("W1", "calibration", 0),
        ("W1", "calibration", 1),
        ("W2", "calibration", 0),
        ("W2", "calibration", 1),
    ]
    assert ws.family_size(0.0, 0.2) == 30
    assert ws.family_size(1.0, 0.2) == 97  # ceil((1.96 / 0.2)^2) = ceil(96.04)
