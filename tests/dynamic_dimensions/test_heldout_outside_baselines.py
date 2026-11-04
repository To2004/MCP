"""Tests for the EV-22 outside baselines (heldout/outside_baselines.py), on synthetic calls."""

from __future__ import annotations

import math

import numpy as np
import pytest

from reports.experiments.dynamic_dimensions.heldout import combiner_family as cf
from reports.experiments.dynamic_dimensions.heldout import heldout_metrics as hm
from reports.experiments.dynamic_dimensions.heldout import outside_baselines as ob

DAY_S = 86_400.0
FIT_WINDOW = (90, 134)


def _table(rows: list[tuple]) -> ob.CallTable:
    """rows: (agent, day, second of day, hour, tool, asset, is_write, sensitivity, r_static)."""
    cols = list(zip(*rows, strict=True))
    agent, day, sec, hour, tool, asset, write, sens, r_static = cols
    n = len(rows)
    return ob.CallTable(
        agent=np.array(agent),
        day=np.array(day),
        ts=np.array(day, float) * DAY_S + np.array(sec, float),
        hour=np.array(hour),
        tool=np.array(tool),
        asset=np.array(asset),
        is_write=np.array(write, bool),
        network=np.array(["10.0.0.0/16"] * n),
        client=np.array(["app|cursor"] * n),
        sensitivity=np.array(sens),
        r_static=np.array(r_static, float),
    )


def _synthetic_world(seed: int = 0, agents: int = 12, n_days: int = 150) -> ob.CallTable:
    rng = np.random.default_rng(seed)
    rows = []
    tools = [f"tool{i}" for i in range(6)]
    for a in range(agents):
        for d in range(n_days):
            if rng.random() < 0.3:
                continue
            for _ in range(int(rng.integers(1, 8))):
                sec = float(rng.uniform(8, 18) * 3600)
                rows.append(
                    (
                        f"agent{a}",
                        d,
                        sec,
                        int(sec // 3600),
                        tools[int(rng.integers(0, 6))],
                        f"repo{int(rng.integers(0, 10))}",
                        bool(rng.random() < 0.3),
                        int(rng.integers(1, 6)),
                        float(rng.uniform(1, 5)),
                    )
                )
    return _table(rows)


def test_agent_day_features_hand_counts() -> None:
    calls = _table(
        [
            ("a", 1, 100.0, 9, "t1", "x", True, 3, 2.0),
            ("a", 1, 200.0, 9, "t2", "y", False, 3, 2.0),
            ("a", 1, 300.0, 23, "t1", "x", False, 3, 2.0),
            ("a", 2, 100.0, 9, "t1", "z", False, 3, 2.0),
        ]
    )
    days = calls.agent_days()
    x = ob.agent_day_features(days, calls)
    # day 1: 3 calls, 1 write, 2 assets, 2 tools, new: t1 t2 x y + network + client = 6, 1 night
    assert x[0].tolist() == [3, 1, 2, 2, 6, 1]
    assert x[1].tolist() == [1, 0, 1, 1, 1, 0]  # only asset z is new


def test_static_only_and_guardian_rate() -> None:
    calls = _table(
        [
            ("a", 1, 0.0, 9, "t", "x", False, 1, 2.0),
            ("a", 1, 10.0, 9, "t", "x", False, 1, 4.0),
            ("a", 1, 59.0, 9, "t", "x", False, 1, 1.0),
            ("a", 1, 61.0, 9, "t", "x", False, 1, 1.0),
            ("a", 1, 200.0, 9, "t", "x", False, 1, 1.0),
            ("b", 1, 0.0, 9, "t", "x", False, 1, 3.0),
        ]
    )
    days = calls.agent_days()
    assert ob.static_only(days, calls.r_static).tolist() == [4.0, 3.0]
    assert ob.guardian_rate(days, calls.ts).tolist() == [3.0, 1.0]


def test_aegis_rarity_counts_only_earlier_days() -> None:
    calls = _table(
        [
            ("a", 1, 0.0, 9, "t1", "x", False, 3, 1.0),
            ("a", 1, 5.0, 9, "t1", "x", False, 3, 1.0),
            ("b", 2, 0.0, 9, "t1", "x", False, 3, 1.0),
            ("c", 2, 0.0, 9, "t2", "x", False, 3, 1.0),
        ]
    )
    days = calls.agent_days()
    out = ob.aegis_rarity(days, calls.tool, calls.sensitivity, calls.network)
    # day 2: t1 was seen twice of 2 earlier calls (rarity 0); t2 never: -log(1/3)
    assert out.tolist() == pytest.approx([0.0, 0.0, math.log(3)])


def test_praetor_counts_unseen_edges_and_contexts() -> None:
    calls = _table(
        [
            ("a", 0, 1.0, 9, "t1", "x", False, 1, 1.0),
            ("a", 0, 2.0, 9, "t2", "y", False, 1, 1.0),
            ("a", 0, 3.0, 9, "t1", "x", False, 1, 1.0),
            ("a", 50, 1.0, 9, "t1", "x", False, 1, 1.0),
            ("a", 50, 2.0, 9, "t3", "x", False, 1, 1.0),
            ("a", 50, 3.0, 9, "t1", "z", False, 1, 1.0),
        ]
    )
    days = calls.agent_days()
    out = ob.praetor_unseen(days, calls.agent, calls.tool, calls.asset)
    # day 50: unseen edges t3/x and t1/z; unseen contexts (t2,t1,t1), (t1,t1,t3), (t1,t3,t1)
    assert out.tolist() == [0.0, 5.0]


def test_per_agent_max_z_is_causal_and_floors_the_sd() -> None:
    days = hm.group_agent_days(["a"] * 4, [0, 1, 2, 3])
    x = np.array([[10.0], [10.0], [10.0], [15.0]])
    z = ob.per_agent_max_z(days, x)
    assert z.tolist() == [0.0, 0.0, 0.0, 5.0]  # sd 0 floored at 1
    later = x.copy()
    later[3] = 99.0
    assert ob.per_agent_max_z(days, later)[:3].tolist() == z[:3].tolist()
    window = ob.per_agent_max_z(days, np.array([[100.0], [10.0], [10.0], [15.0]]), history_days=2)
    assert window[3] == 5.0  # day 0 is outside [t - 2, t - 1]


def test_per_agent_max_z_divides_by_the_sd_when_it_exceeds_the_floor() -> None:
    days = hm.group_agent_days(["a"] * 3, [0, 1, 2])
    z = ob.per_agent_max_z(days, np.array([[8.0], [12.0], [14.0]]))
    assert z[2] == pytest.approx(2.0)  # mean 10, sd 2 > 1: |14 - 10| / 2


def test_guardian_window_is_half_open() -> None:
    calls = _table(
        [
            ("a", 1, 0.0, 9, "t", "x", False, 1, 1.0),
            ("a", 1, 60.0, 9, "t", "x", False, 1, 1.0),  # exactly one minute later
            ("a", 1, 130.0, 9, "t", "x", False, 1, 1.0),
        ]
    )
    # [0, 60) holds one call, not two: a call exactly one minute later starts a new window
    assert ob.guardian_rate(calls.agent_days(), calls.ts).tolist() == [1.0]


def test_isolation_forest_grid_is_chosen_by_the_objective_then_cost() -> None:
    objective = {point: 0.5 for point in ob.IFOREST_GRID}
    assert ob.choose_iforest_grid(objective) == (100, 256)  # all tied: the cheapest
    objective[(300, 1024)] = 0.6
    assert ob.choose_iforest_grid(objective) == (300, 1024)
    with pytest.raises(ValueError, match="exactly the grid"):
        ob.choose_iforest_grid({(100, 256): 0.5})
    with pytest.raises(ValueError, match="finite"):
        ob.choose_iforest_grid({point: float("nan") for point in ob.IFOREST_GRID})


def test_role_peer_group_robust_z() -> None:
    days = hm.group_agent_days(["a", "b", "c", "d"], [10, 10, 10, 100])
    x = np.array([[1.0], [2.0], [3.0], [12.0]])
    out = ob.role_peer_group(days, x, np.array(["dev"] * 4))
    # training: days <= 89 -> median 2, MAD 1, scale 1.4826
    assert out[3] == pytest.approx(10 / 1.4826)


def test_average_path_known_values() -> None:
    assert ob.average_path([0, 1, 2]).tolist() == [0.0, 0.0, 1.0]
    assert ob.average_path(256) == pytest.approx(
        2 * (math.log(255) + ob.EULER_GAMMA) - 2 * 255 / 256
    )


def test_isolation_forest_ranks_an_outlier_first() -> None:
    rng = np.random.default_rng(0)
    x = np.vstack([rng.normal(size=(300, 3)), [[8.0, 8.0, 8.0]]])
    forest = ob.IsolationForest(n_estimators=100, max_samples=128, seed=1).fit(x)
    scores = forest.score(x)
    assert int(np.argmax(scores)) == 300
    with pytest.raises(RuntimeError):
        ob.IsolationForest().score(x)


def test_isolation_forest_uses_no_scored_day_in_training() -> None:
    calls = _synthetic_world(seed=3)
    days = calls.agent_days()
    x = ob.agent_day_features(days, calls)
    base = ob.isolation_forest(days, x, n_estimators=50, max_samples=64)
    poisoned = x.copy()
    scored = days.day > ob.TRAIN_LAST_DAY
    poisoned[scored] *= 50.0
    after = ob.isolation_forest(days, poisoned, n_estimators=50, max_samples=64)
    assert np.array_equal(base[~scored], after[~scored])  # same forest
    assert after[scored].mean() > base[scored].mean()


def test_personal_day_calibration_known_ranks() -> None:
    days = hm.group_agent_days(["a"] * 4, [0, 1, 2, 3])
    out = ob.personal_day_calibration(days, np.array([1.0, 2.0, 3.0, 0.5]))
    # day 0: no past, p = 1; day 2: none of [1, 2] reaches 3, p = 1/3; day 3: all do, p = 1
    assert out.tolist() == pytest.approx([0.0, math.log(2), math.log(3), 0.0])


def test_org_calibration_ranks_against_earlier_days() -> None:
    days = hm.group_agent_days(["a", "b", "c", "d"], [1, 1, 2, 2])
    ev = cf.CallEvidence(
        np.array([[0.2], [0.4], [0.9], [0.3]]),
        np.full((4, 1), np.nan),
        ("d0",),
        ("G",),
        np.array([0.5]),
    )
    out = ob.org_calibration(days, ev)
    # day 2: 0.9 beats both day-1 maxima -> rank 1/3, q = 2/3; 0.3 -> rank 2/3, q = 4/3
    assert out[2] == pytest.approx(1 / (1 + 2 * (2 / 3)))
    assert out[3] == pytest.approx(1 / (1 + 2 * (4 / 3)))
    # day 1 has an empty pool: rank (1 + 0) / 1 = 1, so q = 2 and s1 = 0.2
    assert out[:2].tolist() == pytest.approx([0.2, 0.2])


@pytest.mark.parametrize("baseline", list(ob.baseline_names()))
def test_each_baseline_meets_its_alpha_on_the_calibration_pool(baseline: str) -> None:
    calls = _synthetic_world(seed=1)
    days = calls.agent_days()
    x = ob.agent_day_features(days, calls)
    rng = np.random.default_rng(2)
    q = np.clip(rng.random((days.n_calls, 2)), 1e-4, 1.0)
    ev = cf.CallEvidence(
        rng.random((days.n_calls, 2)),
        q,
        ("burst", "tool"),
        ("Red Flags", "Typical Footprint"),
        np.array([1 / 12, 1 / 12]),
    )
    role = np.where(np.char.endswith(days.agent.astype(str), "1"), "bot", "person")
    scores = {
        "static_only": lambda: ob.static_only(days, calls.r_static),
        "red_flags_only": lambda: ob.red_flags_only(days, ev),
        "per_agent_max_z": lambda: ob.per_agent_max_z(days, x),
        "isolation_forest": lambda: ob.isolation_forest(days, x, n_estimators=30, max_samples=64),
        "role_peer_group": lambda: ob.role_peer_group(days, x, role),
        "guardian_rate": lambda: ob.guardian_rate(days, calls.ts),
        "aegis_rarity": lambda: ob.aegis_rarity(days, calls.tool, calls.sensitivity, calls.network),
        "praetor_unseen": lambda: ob.praetor_unseen(days, calls.agent, calls.tool, calls.asset),
        "personal_day_calibration": lambda: ob.personal_day_calibration(
            days, hm.day_max(days, calls.r_static).score
        ),
        "org_calibration": lambda: ob.org_calibration(days, ev),
    }[baseline]()
    assert scores.shape == (days.n_days,)
    fit_days = hm.in_window(days.day, FIT_WINDOW)
    for alpha in hm.STATED_ALPHAS:
        fit = hm.fit_threshold(scores[fit_days], alpha)
        assert hm.at_or_above(scores[fit_days], fit).mean() <= alpha
