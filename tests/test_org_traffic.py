"""The org traffic model: that its shape is heavy-tailed and its arguments are realistic.

The corpora this replaces drew tools uniformly, which silently disabled the likelihood
factor — ``L`` asks whether a tool is unusual, and under a uniform draw none is. These pin
the properties that make a corpus able to exercise the runtime at all, so a future edit
that flattens the distribution fails here rather than showing up as a scorer that looks
well-behaved on traffic incapable of moving it.
"""

from __future__ import annotations

import collections
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "dynamic_design"))

from org_traffic import (  # noqa: E402
    PROFILES,
    build_args,
    sample_call,
    tool_marginal,
    write_tools,
)

SERVERS = tuple(PROFILES)

STATE = {
    "owner": "acme",
    "repos": ["alpha", "beta", "gamma"],
    "write_repo": "scratch",
    "paths": {"alpha": ["src/main.py", "README.md"]},
    "issues": {"alpha": [1, 2, 7], "scratch": [1, 2]},
    "pulls": {"alpha": [10, 11]},
}


def _draw(n: int = 20_000, seed: int = 7) -> collections.Counter:
    rng = random.Random(seed)
    return collections.Counter(sample_call(rng, STATE).tool for _ in range(n))


# ------------------------------------------------------------------------------- shape


def test_the_volume_weights_are_a_distribution() -> None:
    assert sum(PROFILES['github'].volume.values()) == 1.0
    for persona, tools in PROFILES['github'].tools.items():
        assert abs(sum(tools.values()) - 1.0) < 1e-9, f"{persona} weights must sum to 1"


def test_every_tool_a_persona_uses_is_reachable() -> None:
    """A tool nobody can draw would make its rarity unmeasurable rather than high."""
    assert set(tool_marginal()) == {t for tools in PROFILES['github'].tools.values() for t in tools}


def test_the_distribution_is_heavy_tailed_not_uniform() -> None:
    """The whole point: some tools must be genuinely rare for L to have anything to say."""
    marginal = tool_marginal()
    assert max(marginal.values()) / min(marginal.values()) > 20, "too flat to exercise L"
    ranked = sorted(marginal.values(), reverse=True)
    assert sum(ranked[:3]) > 0.40, "no dominant head"
    assert sum(ranked[-5:]) < 0.05, "no rare tail"


def test_sampling_reproduces_the_declared_marginal() -> None:
    drawn = _draw()
    total = sum(drawn.values())
    for tool, expected in tool_marginal().items():
        assert abs(drawn[tool] / total - expected) < 0.01, f"{tool} drifted from its weight"


def test_sampling_is_deterministic_for_a_seed() -> None:
    assert _draw(2_000, seed=3) == _draw(2_000, seed=3)


# --------------------------------------------------------------------------- arguments


def test_writes_are_routed_to_the_write_repository() -> None:
    """Live runs execute these for real, so they must not touch an unrelated repository."""
    rng = random.Random(11)
    for tool in write_tools('github') - {"create_repository", "fork_repository"}:
        args = build_args(rng, tool, STATE)
        assert args.get("repo") == STATE["write_repo"], f"{tool} escaped the scratch repo"


def test_page_sizes_are_not_uniform() -> None:
    """A uniform page size makes every value equally ordinary and flattens B's quartiles."""
    rng = random.Random(5)
    sizes = collections.Counter(
        build_args(rng, "list_commits", STATE)["perPage"] for _ in range(5_000))
    assert sizes.most_common(1)[0][0] == 30, "the API default should dominate"
    assert sizes[30] / sum(sizes.values()) > 0.45
    assert sizes[1] / sum(sizes.values()) < 0.10, "the narrowest value must stay rare"


def test_arguments_name_things_that_exist() -> None:
    rng = random.Random(13)
    for _ in range(500):
        call = sample_call(rng, STATE)
        if "repo" in call.args and call.args["repo"] != STATE["write_repo"]:
            assert call.args["repo"] in STATE["repos"]
        if "issue_number" in call.args:
            assert isinstance(call.args["issue_number"], int)


def test_a_missing_state_entry_falls_back_rather_than_raising() -> None:
    """Live probing may find a repository with no issues; that must not stop the run."""
    bare = {"owner": "acme", "repos": ["solo"], "write_repo": "solo"}
    rng = random.Random(2)
    for _ in range(200):
        assert sample_call(rng, bare).tool
