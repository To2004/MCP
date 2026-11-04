"""EV-07: the bytes of ``result.content`` each simulated call returns (Read volume and
over-fetching need them). Synthetic sizes; EV-26 measures real ones.
"""

from __future__ import annotations

import random
import statistics
from collections import defaultdict

import pytest

from tests.dynamic_dimensions.world_support import ensure_sim_on_path

ensure_sim_on_path()

import normal_org_world as W  # noqa: E402

N_SAMPLES = 2_000
OVERFETCH_RATIO = 3.0  # EV-07's test: at least 3x the usual list_issues response
ENVELOPE = W.RESPONSE_ENVELOPE_BYTES


def samples(tool: str, *, overfetch: bool = False, seed: int = 0) -> list[int]:
    rng = random.Random(seed)
    return [W.response_size(tool, rng, overfetch=overfetch) for _ in range(N_SAMPLES)]


@pytest.mark.parametrize("tool", sorted(W.CATALOG))
def test_every_tool_has_a_response_model(tool: str) -> None:
    sizes = samples(tool)
    assert min(sizes) >= ENVELOPE
    if W.CATALOG[tool][0] == "write":
        assert max(sizes) <= ENVELOPE + W.WRITE_ECHO_BYTES[1]
        assert min(sizes) >= ENVELOPE + W.WRITE_ECHO_BYTES[0]
    else:
        assert statistics.median(sizes) > ENVELOPE  # a read returns something


def test_file_contents_are_capped_at_one_megabyte() -> None:
    assert max(samples("get_file_contents")) <= ENVELOPE + W.MAX_FILE_BYTES


def test_a_page_never_exceeds_its_page_size() -> None:
    item_bytes, _ = W.LIST_RESPONSES["list_issues"]
    jitter_cap = 4.0  # exp(SIZE_JITTER_SIGMA * 5.5): beyond any of 2,000 draws
    biggest_normal = max(samples("list_issues"))
    biggest_overfetch = max(samples("list_issues", overfetch=True))
    assert biggest_normal <= ENVELOPE + W.DEFAULT_PER_PAGE * item_bytes * jitter_cap
    assert biggest_overfetch <= ENVELOPE + W.OVERFETCH_PER_PAGE * item_bytes * jitter_cap


def test_overfetch_returns_at_least_three_times_the_usual_page() -> None:
    usual = statistics.median(samples("list_issues", seed=1))
    over = statistics.median(samples("list_issues", overfetch=True, seed=2))
    assert over >= OVERFETCH_RATIO * usual


def test_overfetch_changes_only_lists() -> None:
    a, b = random.Random(5), random.Random(5)
    assert W.response_size("get_issue", a, overfetch=True) == W.response_size("get_issue", b)


def test_unknown_tool_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown tool"):
        W.response_size("delete_everything", random.Random(0))


def test_v5_rows_carry_resp_exposure_and_owner(v5_world: tuple) -> None:
    """Every organisation repository, a migrated one too, is owned by the organisation; only
    the classic toxic flow names another owner (a person's own account)."""
    world, _, _ = v5_world
    exposures = {W.EXPOSURE_PUBLIC, W.EXPOSURE_INTERNAL, W.EXPOSURE_PRIVATE}
    migrated = personal = 0
    for rows in world.values():
        for r in rows:
            assert len(r) == len(W.ROW_V5)
            resp, exposure, owner = r[W.RESP_COLUMN], r[W.EXPOSURE_COLUMN], r[W.OWNER_COLUMN]
            if r[1] != "tools/call":
                assert (resp, exposure, owner) == (0, None, None)
            elif r[4] is None:
                assert resp >= ENVELOPE and exposure is None and owner is None
            else:
                assert resp >= ENVELOPE and exposure in exposures
                if owner.startswith(W.PERSONAL_OWNER_PREFIX):
                    episode = W.parse_episode(r[12])
                    assert (episode.kind, episode.variant) == (W.TOXIC_FLOW, W.CLASSIC)
                    personal += 1
                else:
                    assert owner == W.ORG_OWNER
                    migrated += r[4].startswith(f"{W.MIGRATED_NAMESPACE}/")
    assert migrated and personal  # both cases occur in the fixture world


def test_overfetch_episodes_dwarf_the_agents_usual_list(v5_world: tuple) -> None:
    """Every over-fetch episode's median list_issues response is at least 3x the same agent's
    ordinary list_issues median (the request size alone could not show it)."""
    world, _, _ = v5_world
    checked = 0
    for rows in world.values():
        usual = [r[W.RESP_COLUMN] for r in rows if r[3] == "list_issues" and not r[12]]
        episodes: dict[str, list[int]] = defaultdict(list)
        for r in rows:
            if r[12] and W.parse_episode(r[12]).kind == "overfetch":
                episodes[r[12]].append(r[W.RESP_COLUMN])
        for sizes in episodes.values():
            assert statistics.median(sizes) >= OVERFETCH_RATIO * statistics.median(usual)
            checked += 1
    assert checked >= 2  # the fixture world holds several over-fetch episodes
