"""Unit tests for the hand-rolled metrics in scripts/eval_metrics.py.

Each metric is checked against a value computable by hand so a refactor that
silently breaks the math is caught.
"""

from __future__ import annotations

import math

from scripts.eval_metrics import (
    band_distribution,
    best_f1,
    binary_at_threshold,
    detection_by_class,
    ordinal_mae,
    quadratic_weighted_kappa,
    recall_at_fpr,
    roc_auc,
    spearman_rho,
    wilson_ci,
)


def test_qwk_perfect_agreement_is_one():
    assert quadratic_weighted_kappa([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0


def test_qwk_penalises_far_misses_more_than_near():
    near = quadratic_weighted_kappa([1, 1, 4, 4], [2, 1, 3, 4])
    far = quadratic_weighted_kappa([1, 1, 4, 4], [4, 1, 1, 4])
    assert near is not None and far is not None
    assert near > far  # an off-by-one beats an off-by-three


def test_qwk_undefined_when_no_expected_disagreement():
    # Both raters constant -> marginals give zero expected disagreement.
    assert quadratic_weighted_kappa([2, 2, 2], [2, 2, 2]) is None


def test_ordinal_mae():
    assert ordinal_mae([1, 2, 3], [1, 3, 3]) == 1 / 3


def test_spearman_monotone_and_reverse():
    assert math.isclose(spearman_rho([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
    assert math.isclose(spearman_rho([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)


def test_wilson_ci_known_value():
    lo, hi = wilson_ci(9, 10)
    assert math.isclose(lo, 0.5958, abs_tol=1e-3)
    assert math.isclose(hi, 0.9821, abs_tol=1e-3)


def test_wilson_ci_zero_n():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_roc_auc_perfect_and_chance_and_ties():
    assert roc_auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0
    assert roc_auc([1, 2, 3, 4], [1, 0, 1, 0]) == 0.25
    assert roc_auc([2, 2, 2, 2], [1, 1, 0, 0]) == 0.5  # all tied -> chance


def test_roc_auc_undefined_single_class():
    assert roc_auc([1, 2, 3], [1, 1, 1]) is None


def test_band_distribution_over_block():
    d = band_distribution(["low", "low", "high", "critical", "medium"])
    assert d["n"] == 5
    assert math.isclose(d["over_block"], 0.4)  # 2 of 5 are high|critical


def test_binary_at_threshold_counts():
    r = binary_at_threshold([1, 2, 3, 4], [0, 0, 1, 1], threshold=3)
    assert (r["tp"], r["fp"], r["tn"], r["fn"]) == (2, 0, 2, 0)
    assert r["errors"] == 0
    assert r["f1"] == 1.0


def test_best_f1_finds_perfect_cut():
    r = best_f1([1, 2, 3, 4], [0, 0, 1, 1])
    assert r["f1"] == 1.0
    assert r["threshold"] == 3


def test_recall_at_fpr_zero_keeps_only_clean_separation():
    # Separable: at FPR=0 we can still catch both positives (threshold 3).
    r = recall_at_fpr([1, 2, 3, 4], [0, 0, 1, 1], max_fpr=0.0)
    assert r["recall"] == 1.0 and r["fpr"] == 0.0
    # Overlapping: a positive sits below a negative, so FPR=0 costs recall.
    r2 = recall_at_fpr([3, 4, 3, 2], [0, 0, 1, 1], max_fpr=0.0)
    assert r2["fpr"] == 0.0 and r2["recall"] < 1.0


def test_detection_by_class():
    scores = [4, 2, 3, 1]
    classes = ["ATT-1", "ATT-1", "ATT-2", None]
    labels = [1, 1, 1, 0]  # last is benign, ignored
    d = detection_by_class(scores, classes, labels, threshold=3)
    assert d["ATT-1"] == (1, 2)  # one of two ATT-1 attacks caught at >=3
    assert d["ATT-2"] == (1, 1)
