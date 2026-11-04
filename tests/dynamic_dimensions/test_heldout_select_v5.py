"""Tests for the development selection rule (heldout/select_v5.py, spec 6.2).

The fixture table is synthetic: six development worlds, v4, cfg0, three argued switches,
cfg4 and two tune candidates, with numbers chosen so that each rule clause decides a case.
"""

from __future__ import annotations

import dataclasses
import json
import math

import numpy as np
import pytest

from reports.experiments.dynamic_dimensions.heldout import heldout_stats as hs
from reports.experiments.dynamic_dimensions.heldout import select_v5 as sv

WORLDS = tuple(f"dev_w{i}" for i in range(6))
DAYS = 10_000  # benign agent-days per world
EPISODES = {"paced_export": 5, "overfetch": 5, "rare_kind": 2}  # rare_kind: 12 < 20 pooled
LIST_EPISODES = 10
RULE = sv.SelectionRule(delta=0.02, delta_kind=0.05, delta_list=0.05, b=500)
B7, RF11, AI8 = "usual_quantile", "habit_after_established", "reply_volume"
HOLD, TOP = "record_hold_days", "leave_top_identity_out"


def _worlds(
    pauc: float,
    *,
    alerts: int = 50,
    x3: int = 100,
    caught: dict[str, int] | None = None,
    listed: float = 6.0,
    runtime: float = 120.0,
) -> tuple[sv.WorldMetrics, ...]:
    kinds = {"paced_export": 3, "overfetch": 2, "rare_kind": 1} | (caught or {})
    return tuple(
        sv.WorldMetrics(
            world=w,
            pauc=pauc,
            benign_days=DAYS,
            benign_alerts=alerts,
            benign_alerts_x3=x3,
            kind_episodes=dict(EPISODES),
            kind_caught=dict(kinds),
            list_episodes=LIST_EPISODES,
            list_caught=listed,
            runtime_s=runtime,
        )
        for w in WORLDS
    )


def _table(**changes: sv.Candidate) -> list[sv.Candidate]:
    base = {
        "v4": sv.Candidate("v4", sv.REFERENCE, 30, worlds=_worlds(0.40, listed=5.0, runtime=100)),
        "cfg0": sv.Candidate("cfg0", sv.CORE, 40, worlds=_worlds(0.50)),
        "cfg1": sv.Candidate(
            "cfg1",
            sv.ARGUED,
            41,
            switches=(B7,),
            targets=("paced_export",),
            worlds=_worlds(0.51, caught={"paced_export": 4}),
        ),
        "cfg2": sv.Candidate(
            "cfg2", sv.ARGUED, 41, switches=(RF11,), targets=("overfetch",), worlds=_worlds(0.45)
        ),
        "cfg3": sv.Candidate(
            "cfg3",
            sv.ARGUED,
            41,
            switches=(AI8,),
            targets=("overfetch",),
            worlds=_worlds(0.70, x3=200, caught={"overfetch": 4}),  # x3 +1 point: over the cap
        ),
        "cfg4": sv.Candidate("cfg4", sv.COMBINED, 41, switches=(B7,), worlds=_worlds(0.515)),
        "cfg5": sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=_worlds(0.60)),
        "cfg6": sv.Candidate("cfg6", sv.TUNE, 44, switches=(B7, TOP), worlds=_worlds(0.55)),
    }
    base.update(changes)
    return list(base.values())


def test_selects_the_best_admissible_candidate() -> None:
    sel = sv.select(_table(), RULE)
    assert sel.chosen == "cfg5"
    assert sel.admitted == (B7,)
    assert sel.tied == ("cfg5",)


def test_argued_switches_need_objective_target_gain_and_admissibility() -> None:
    sel = sv.select(_table(), RULE)
    assert sel.switches[B7].admitted
    assert not sel.switches[RF11].admitted  # objective 0.45 < 0.50 - delta
    assert any("objective" in r for r in sel.switches[RF11].reasons)
    assert any("target overfetch" in r for r in sel.switches[RF11].reasons)
    assert not sel.switches[AI8].admitted  # over the cumulative x3 cap
    assert any("x3" in r for r in sel.switches[AI8].reasons)


def test_a_failed_switch_ships_off_even_with_the_best_objective() -> None:
    sel = sv.select(_table(), RULE)
    check = sel.checks["cfg3"]
    assert check.objective == pytest.approx(0.70)
    assert not check.admissible and not check.eligible
    assert sel.chosen != "cfg3"


def test_ties_within_delta_go_to_fewer_constants() -> None:
    table = _table(
        cfg5=sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=_worlds(0.600)),
        cfg6=sv.Candidate("cfg6", sv.TUNE, 42, switches=(B7, TOP), worlds=_worlds(0.585)),
    )
    sel = sv.select(table, RULE)
    assert sel.tied == ("cfg5", "cfg6")
    assert sel.chosen == "cfg6"


def test_the_quiet_bound_excludes_a_candidate() -> None:
    noisy = sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=_worlds(0.6, alerts=150))
    sel = sv.select(_table(cfg5=noisy), RULE)
    assert not sel.checks["cfg5"].admissible
    assert sel.checks["cfg5"].quiet_upper == pytest.approx(0.015)
    assert sel.chosen == "cfg6"


@pytest.mark.parametrize(("x3", "admissible"), [(140, True), (160, False)])
def test_the_cumulative_x3_cap_is_half_a_point_over_cfg0(x3: int, admissible: bool) -> None:
    cand = sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=_worlds(0.6, x3=x3))
    sel = sv.select(_table(cfg5=cand), RULE)
    assert sel.checks["cfg5"].admissible is admissible


def test_per_kind_recall_counts_only_kinds_with_twenty_episodes() -> None:
    lost_rare = _worlds(0.6, caught={"rare_kind": 0})  # 12 episodes: not checked
    lost_paced = _worlds(0.6, caught={"paced_export": 2})  # 3/5 -> 2/5: a 0.2 drop
    ok = sv.select(_table(cfg5=dataclasses.replace(_table()[6], worlds=lost_rare)), RULE)
    assert ok.checks["cfg5"].admissible
    bad = sv.select(_table(cfg5=dataclasses.replace(_table()[6], worlds=lost_paced)), RULE)
    assert not bad.checks["cfg5"].admissible
    assert any("paced_export" in r for r in bad.checks["cfg5"].reasons)


def test_list_catch_is_measured_against_the_better_of_v4_and_cfg4() -> None:
    cfg4 = sv.Candidate("cfg4", sv.COMBINED, 41, switches=(B7,), worlds=_worlds(0.515, listed=8))
    low = dataclasses.replace(_table()[6], worlds=_worlds(0.6, listed=7.0))  # 0.70 < 0.80 - 0.05
    sel = sv.select(_table(cfg4=cfg4, cfg5=low), RULE)
    assert not sel.checks["cfg5"].admissible
    assert any("list" in r for r in sel.checks["cfg5"].reasons)


def test_runtime_and_tests_are_constraints() -> None:
    slow = dataclasses.replace(_table()[6], worlds=_worlds(0.6, runtime=201.0))
    failing = dataclasses.replace(_table()[6], tests_pass=False)
    assert not sv.select(_table(cfg5=slow), RULE).checks["cfg5"].admissible
    assert not sv.select(_table(cfg5=failing), RULE).checks["cfg5"].admissible


def test_cfg4_must_carry_exactly_the_admitted_switches() -> None:
    wrong = sv.Candidate("cfg4", sv.COMBINED, 41, switches=(B7, RF11), worlds=_worlds(0.5))
    with pytest.raises(ValueError, match="re-run"):
        sv.select(_table(cfg4=wrong), RULE)


def test_cfg9_is_scored_only_when_d3_is_c() -> None:
    cfg9 = sv.Candidate("cfg9", sv.WATCH_ONLY, 41, switches=(B7,), worlds=_worlds(0.52))
    with pytest.raises(ValueError, match="D3"):
        sv.select([*_table(), cfg9], RULE)
    sel = sv.select([*_table(), cfg9], dataclasses.replace(RULE, d3="c"))
    assert "cfg9" in sel.checks


def test_no_admissible_candidate_raises() -> None:
    loud = {
        c.name: dataclasses.replace(c, worlds=_worlds(0.6, alerts=500))
        for c in _table()
        if c.name != "v4"
    }
    loud["cfg4"] = dataclasses.replace(loud["cfg4"], switches=())  # nothing gets admitted
    with pytest.raises(sv.NoAdmissibleCandidate):
        sv.select(_table(**loud), RULE)


def test_every_candidate_must_share_the_worlds() -> None:
    short = dataclasses.replace(_table()[6], worlds=_worlds(0.6)[:5])
    with pytest.raises(ValueError, match="same development worlds"):
        sv.select(_table(cfg5=short), RULE)


def test_derived_margins_are_1_64_paired_world_ses() -> None:
    rng = np.random.default_rng(12)
    core = dataclasses.replace(
        _table()[1],
        worlds=tuple(
            dataclasses.replace(
                w, pauc=0.5 + 0.05 * rng.normal(), list_caught=float(rng.integers(4, 9))
            )
            for w in _worlds(0.5)
        ),
    )
    reference = _table()[0]
    margins = sv.derive_margins(core, reference, b=800, seed=5)
    counts = hs.bootstrap_counts(len(WORLDS), 800, 5)
    se = hs.paired_world_bootstrap(
        [w.pauc for w in core.worlds], [w.pauc for w in reference.worlds], counts=counts
    ).se
    assert margins.delta == pytest.approx(sv.MARGIN_Z * se)
    assert margins.delta > 0 and margins.delta_list > 0
    assert set(margins.delta_kind) == set(EPISODES)


def test_a_rule_must_fix_its_margins_unless_it_opts_in() -> None:
    with pytest.raises(ValueError, match="hashed rule"):
        sv.SelectionRule(b=300)  # margins left None, no opt-in
    with pytest.raises(ValueError, match="margins_from"):
        dataclasses.replace(RULE, margins_from="table")
    opted = sv.SelectionRule(b=300, margins_from=sv.MARGINS_FROM_TABLE)
    sel = sv.select(_table(), opted)
    assert sel.margins.source.startswith("derived")
    assert any("derived" in n for n in sel.notes)
    fixed = sv.select(_table(), RULE)
    assert fixed.margins.source == "fixed in the rule"
    assert sv.rule_digest(RULE) != sv.rule_digest(
        dataclasses.replace(RULE, margins_from=sv.MARGINS_FROM_TABLE)
    )


def _with_solo_kind(c: sv.Candidate) -> sv.Candidate:
    """The candidate with a kind "solo" of 24 episodes, all in the first world."""
    worlds = []
    for i, w in enumerate(c.worlds):
        kinds = dict(w.kind_episodes) | {"solo": 24 if i == 0 else 0}
        caught = dict(w.kind_caught) | {"solo": 12 if i == 0 else 0}
        worlds.append(dataclasses.replace(w, kind_episodes=kinds, kind_caught=caught))
    return dataclasses.replace(c, worlds=tuple(worlds))


def test_a_kind_seen_in_one_world_gets_the_stated_fallback_margin() -> None:
    table = [_with_solo_kind(c) for c in _table()]
    margins = sv.derive_margins(table[1], table[0], b=300)
    assert margins.fallback_kinds == ("solo",) and "solo" in margins.source
    assert margins.delta_kind["solo"] == pytest.approx(sv.MARGIN_Z * 0.5 * math.sqrt(2 / 24))
    sel = sv.select(table, sv.SelectionRule(b=300, margins_from=sv.MARGINS_FROM_TABLE))
    assert sel.margins.fallback_kinds == ("solo",) and "solo" in sel.margins.delta_kind


def test_the_quiet_constraint_reads_the_upper_bound_not_the_estimate() -> None:
    # Worlds at 0.2% and 2% (pooled 1.1%, below alpha + beta = 1.35%): the one-sided upper
    # world-bootstrap bound is above 1.35%, so the candidate is not quiet.
    spread = tuple(
        dataclasses.replace(w, benign_alerts=a)
        for w, a in zip(_worlds(0.6), [20, 200] * 3, strict=True)
    )
    cand = sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=spread)
    sel = sv.select(_table(cfg5=cand), RULE)
    estimate = sum(w.benign_alerts for w in spread) / sum(w.benign_days for w in spread)
    assert estimate < RULE.alpha + RULE.beta < sel.checks["cfg5"].quiet_upper
    assert not sel.checks["cfg5"].admissible and sel.chosen == "cfg6"


def test_the_quiet_bar_is_alpha_plus_beta() -> None:
    # 1.2% in every world: above alpha = 1%, within alpha + beta = 1.35%.
    cand = sv.Candidate("cfg5", sv.TUNE, 43, switches=(B7, HOLD), worlds=_worlds(0.6, alerts=120))
    sel = sv.select(_table(cfg5=cand), RULE)
    assert sel.checks["cfg5"].quiet_upper == pytest.approx(0.012)
    assert sel.checks["cfg5"].admissible and sel.chosen == "cfg5"


def test_the_objective_is_the_mean_world_pauc() -> None:
    worlds = tuple(
        dataclasses.replace(w, pauc=p)
        for w, p in zip(_worlds(0.5), [0.9, 0.5, 0.5, 0.5, 0.5, 0.5], strict=True)
    )
    assert sv.objective(dataclasses.replace(_table()[6], worlds=worlds)) == pytest.approx(3.4 / 6)


def test_every_candidate_must_see_the_same_episodes_and_targets() -> None:
    more = tuple(
        dataclasses.replace(w, kind_episodes={**w.kind_episodes, "paced_export": 6})
        for w in _worlds(0.6)
    )
    with pytest.raises(ValueError, match="same episodes"):
        sv.select(_table(cfg5=dataclasses.replace(_table()[6], worlds=more)), RULE)
    fewer_listed = tuple(dataclasses.replace(w, list_episodes=9) for w in _worlds(0.6))
    with pytest.raises(ValueError, match="same episodes"):
        sv.select(_table(cfg5=dataclasses.replace(_table()[6], worlds=fewer_listed)), RULE)
    unknown = dataclasses.replace(_table()[2], targets=("no_such_kind",))
    with pytest.raises(ValueError, match="targets kinds"):
        sv.select(_table(cfg1=unknown), RULE)


def test_rule_digest_and_candidates_file_round_trip(tmp_path) -> None:
    assert sv.rule_digest(RULE) == sv.rule_digest(dataclasses.replace(RULE))
    assert sv.rule_digest(RULE) != sv.rule_digest(dataclasses.replace(RULE, delta=0.03))
    table = _table()
    payload = {
        "rule": dataclasses.asdict(RULE),
        "candidates": [dataclasses.asdict(c) for c in table],
    }
    path = tmp_path / "v5_candidates.json"
    path.write_text(json.dumps(payload))
    rule, loaded = sv.load_candidates(path)
    assert rule == RULE
    assert sv.select(loaded, rule).chosen == sv.select(table, RULE).chosen


def test_margins_in_operational_units() -> None:
    # 0.05 recall on 200 episodes from 150 agents over 46 days.
    out = sv.catches_per_100_agent_months(0.05, 200, 150 * 46)
    assert out == pytest.approx(0.05 * 200 * 100 * 30 / 6_900)
