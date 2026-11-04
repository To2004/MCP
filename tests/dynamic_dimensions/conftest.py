"""Fixtures for the simulator tests: the simulator importable, and one small v5 world built
once per session (24 agents, seed 18: 13 gray kinds, 7 of them in both variants, three
over-fetch episodes, a plain stuck CI loop and a report bot's plain token reuse)."""

from __future__ import annotations

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

SMALL_AGENTS, SMALL_SEED = 24, 18


@pytest.fixture(scope="session")
def v5_world() -> tuple[dict, dict, W.Org]:
    """``build_world(24, 18, world_version="v5")``."""
    return W.build_world(SMALL_AGENTS, SMALL_SEED, world_version=W.WORLD_V5)
