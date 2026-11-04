"""INF-4: a policy file holds only the fields its design uses; v1-v4 files never change.

``golden/policy_v*.json`` are the bytes ``config_to_json`` wrote before v5, in the CLI's
format (``indent=1``). They were recorded before ``policy.py`` changed, and must stay
byte-identical, so the digests of deployed v4 policy files do not move.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_security.behaviour import BehaviourConfig, v5_switches_off
from mcp_security.behaviour.engine import DERIVED_FIELDS, DESIGN_VALUES
from mcp_security.behaviour.policy import config_from_json, config_to_json

GOLDEN = Path(__file__).parent / "golden"
LEARNED_V4 = BehaviourConfig(
    design="v4",
    burst_per_minute=14,
    request_limit_bytes=9_000,
    request_limit_by_tool={"write_file": 40_000, "comment": 3_000},
    many_assets_per_hour=11,
    requires_before={
        "merge_pr": frozenset({"review_pr", "approve"}),
        "deploy": frozenset({"plan"}),
    },
)
CASES = [
    ("policy_v1.json", BehaviourConfig(design="v1")),
    ("policy_v2.json", BehaviourConfig(design="v2")),
    ("policy_v3.json", BehaviourConfig(design="v3")),
    ("policy_v4.json", BehaviourConfig(design="v4")),
    ("policy_v4_learned.json", LEARNED_V4),
]


def _file_text(config: BehaviourConfig) -> str:
    """What ``python -m mcp_security.behaviour.policy`` writes for ``config``."""
    return json.dumps(config_to_json(config), indent=1)


@pytest.mark.parametrize(("name", "config"), CASES)
def test_a_v1_to_v4_policy_file_is_byte_identical_to_the_pre_v5_one(name, config) -> None:
    assert _file_text(config) == (GOLDEN / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(("name", "config"), CASES)
def test_a_pre_v5_policy_file_loads_back_to_the_same_config(name, config) -> None:
    assert config_from_json(json.loads((GOLDEN / name).read_text(encoding="utf-8"))) == config


# ── v5 ────────────────────────────────────────────────────────────────────────────────────
def _round_trip(config: BehaviourConfig) -> BehaviourConfig:
    return config_from_json(json.loads(_file_text(config)))


@pytest.mark.parametrize(
    "config",
    [
        BehaviourConfig(design="v5"),
        v5_switches_off(),
        BehaviourConfig(
            design="v5",
            usual_quantile=None,
            alert_alpha=0.025,
            budget_shares=(0.4, 0.3, 0.3),
            requires_before={"m": frozenset("r")},
        ),
    ],
    ids=["defaults", "switches-off", "tuned"],
)
def test_a_v5_policy_round_trips(config: BehaviourConfig) -> None:
    assert _round_trip(config) == config


def test_a_v5_policy_file_holds_every_v5_field_but_the_derived_and_a_v4_file_none() -> None:
    v5 = config_to_json(BehaviourConfig(design="v5"))
    v4 = config_to_json(BehaviourConfig(design="v4"))
    assert set(DESIGN_VALUES) - DERIVED_FIELDS <= set(v5)
    assert not DERIVED_FIELDS & set(v5)  # they follow alert_alpha, which the file holds
    assert not set(DESIGN_VALUES) & set(v4)
    assert v5["budget_shares"] == (1 / 3, 1 / 3, 1 / 3)  # a tuple; JSON writes it as a list


def test_the_legacy_fixes_set_on_v4_are_written_and_read_back() -> None:
    v41 = BehaviourConfig(design="v4", legacy_fixes=True)
    assert config_to_json(v41)["legacy_fixes"] is True
    assert _round_trip(v41) == v41


def test_a_v5_switch_in_a_v4_policy_file_is_refused() -> None:
    with pytest.raises(ValueError, match="v5 switch"):
        config_from_json({"design": "v4", "calibration": "commonness"})


def test_a_v5_policy_file_with_only_its_design_takes_the_v5_defaults() -> None:
    assert config_from_json({"design": "v5"}) == BehaviourConfig(design="v5")
