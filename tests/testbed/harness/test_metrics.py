"""Unit tests for metrics.py pure functions.

These tests do NOT require a live server, MCP SDK, or network access.
All inputs are hand-crafted result dicts.
"""

from __future__ import annotations

from tests.testbed.harness.metrics import (
    compute_all,
    compute_asr,
    compute_latency_p95,
    compute_score_error,
    compute_tpr_fpr,
    format_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    payload_type: str = "malicious",
    category: str = "C1",
    damage_detected: bool = False,
    combined_score: float | None = None,
    latency_ms: float = 10.0,
) -> dict:
    """Return a minimal result dict for testing."""
    return {
        "server": "test",
        "template_id": "test_template",
        "category": category,
        "tool": "test_tool",
        "payload_label": "test_label",
        "payload_type": payload_type,
        "args": {},
        "response_snippet": "",
        "damage_detected": damage_detected,
        "error": None,
        "score": {"static": None, "dynamic": None, "combined": combined_score, "note": "stub"},
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# compute_asr
# ---------------------------------------------------------------------------


def test_asr_basic() -> None:
    """Half of C1 malicious payloads cause damage — ASR should be 0.5."""
    results = [
        {"payload_type": "malicious", "category": "C1", "damage_detected": True, "score": {}, "latency_ms": 10},
        {"payload_type": "malicious", "category": "C1", "damage_detected": False, "score": {}, "latency_ms": 10},
        {"payload_type": "benign", "category": "C1", "damage_detected": False, "score": {}, "latency_ms": 5},
    ]
    asr = compute_asr(results)
    assert asr["C1"] == 0.5
    assert asr["overall"] == 0.5


def test_asr_empty() -> None:
    """Empty results produce overall ASR of 0.0."""
    assert compute_asr([])["overall"] == 0.0


def test_asr_all_damage() -> None:
    """All malicious payloads cause damage — ASR should be 1.0."""
    results = [_make_result(damage_detected=True) for _ in range(4)]
    asr = compute_asr(results)
    assert asr["overall"] == 1.0


def test_asr_no_damage() -> None:
    """No malicious payloads cause damage — ASR should be 0.0."""
    results = [_make_result(damage_detected=False) for _ in range(3)]
    asr = compute_asr(results)
    assert asr["overall"] == 0.0


def test_asr_multiple_categories() -> None:
    """ASR is computed independently per category."""
    results = [
        _make_result(category="C1", damage_detected=True),
        _make_result(category="C1", damage_detected=True),
        _make_result(category="C2", damage_detected=False),
        _make_result(category="C2", damage_detected=False),
    ]
    asr = compute_asr(results)
    assert asr["C1"] == 1.0
    assert asr["C2"] == 0.0
    assert asr["overall"] == 0.5


def test_asr_benign_excluded() -> None:
    """Benign results do not affect ASR calculation."""
    results = [
        _make_result(payload_type="malicious", damage_detected=True),
        _make_result(payload_type="benign", damage_detected=False),
        _make_result(payload_type="benign", damage_detected=True),  # should be ignored
    ]
    asr = compute_asr(results)
    assert asr["overall"] == 1.0


def test_asr_only_benign() -> None:
    """Only benign results — no malicious — should give overall 0.0."""
    results = [_make_result(payload_type="benign", damage_detected=False)]
    asr = compute_asr(results)
    assert asr["overall"] == 0.0
    assert "benign" not in asr  # benign category is not a malicious category key


# ---------------------------------------------------------------------------
# compute_tpr_fpr
# ---------------------------------------------------------------------------


def test_tpr_fpr_with_scores() -> None:
    """Standard TPR/FPR calculation with a mix of scored results."""
    results = [
        {"payload_type": "malicious", "score": {"combined": 8.0}, "damage_detected": True, "category": "C1", "latency_ms": 1},
        {"payload_type": "malicious", "score": {"combined": 3.0}, "damage_detected": False, "category": "C1", "latency_ms": 1},
        {"payload_type": "benign", "score": {"combined": 2.0}, "damage_detected": False, "category": "C1", "latency_ms": 1},
    ]
    metrics = compute_tpr_fpr(results, threshold=5.0)
    assert metrics["tpr"] == 0.5  # 1 of 2 malicious above threshold
    assert metrics["fpr"] == 0.0  # 0 of 1 benign above threshold


def test_tpr_fpr_no_scores() -> None:
    """When all combined scores are None, tpr and fpr should be None."""
    results = [
        {"payload_type": "malicious", "score": {"combined": None}, "damage_detected": True, "category": "C1", "latency_ms": 1},
    ]
    metrics = compute_tpr_fpr(results)
    assert metrics["tpr"] is None


def test_tpr_fpr_all_above_threshold() -> None:
    """All malicious scored above threshold — TPR should be 1.0."""
    results = [
        _make_result(payload_type="malicious", combined_score=9.0),
        _make_result(payload_type="malicious", combined_score=7.0),
        _make_result(payload_type="benign", combined_score=1.0),
    ]
    m = compute_tpr_fpr(results, threshold=5.0)
    assert m["tpr"] == 1.0
    assert m["fpr"] == 0.0


def test_tpr_fpr_fpr_nonzero() -> None:
    """Benign result scored above threshold — FPR should be > 0."""
    results = [
        _make_result(payload_type="malicious", combined_score=8.0),
        _make_result(payload_type="benign", combined_score=7.0),
    ]
    m = compute_tpr_fpr(results, threshold=5.0)
    assert m["fpr"] == 1.0


def test_tpr_fpr_threshold_returned() -> None:
    """Threshold value is echoed back in the returned dict."""
    m = compute_tpr_fpr([], threshold=3.5)
    assert m["threshold"] == 3.5


def test_tpr_fpr_counts() -> None:
    """scored_malicious_count and scored_benign_count are correct."""
    results = [
        _make_result(payload_type="malicious", combined_score=6.0),
        _make_result(payload_type="malicious", combined_score=None),
        _make_result(payload_type="benign", combined_score=2.0),
    ]
    m = compute_tpr_fpr(results, threshold=5.0)
    assert m["scored_malicious_count"] == 1
    assert m["scored_benign_count"] == 1


# ---------------------------------------------------------------------------
# compute_score_error
# ---------------------------------------------------------------------------


def test_score_error_all_none() -> None:
    """No scored results — MAE should be None and n_scored 0."""
    results = [_make_result(combined_score=None)]
    err = compute_score_error(results)
    assert err["mean_absolute_error"] is None
    assert err["n_scored"] == 0


def test_score_error_with_scores() -> None:
    """Scored results are counted even though MAE is None (scorer stub phase)."""
    results = [
        _make_result(combined_score=7.0),
        _make_result(combined_score=3.0),
    ]
    err = compute_score_error(results)
    # MAE is None until expected ranges are wired in
    assert err["mean_absolute_error"] is None
    assert err["n_scored"] == 2


def test_score_error_empty() -> None:
    """Empty results — n_scored should be 0."""
    assert compute_score_error([])["n_scored"] == 0


# ---------------------------------------------------------------------------
# compute_latency_p95
# ---------------------------------------------------------------------------


def test_latency_p95() -> None:
    """95th percentile of 1-100 ms should be approximately 95 ms."""
    results = [
        {"latency_ms": float(i), "payload_type": "malicious", "score": {}, "damage_detected": False, "category": "C1"}
        for i in range(1, 101)
    ]
    p95 = compute_latency_p95(results)
    assert p95 is not None
    assert 94.0 <= p95 <= 96.0


def test_latency_empty() -> None:
    """Empty results should return None."""
    assert compute_latency_p95([]) is None


def test_latency_single() -> None:
    """Single result — p95 equals that result's latency."""
    results = [_make_result(latency_ms=42.0)]
    assert compute_latency_p95(results) == 42.0


def test_latency_all_same() -> None:
    """All latencies equal — p95 should equal that value."""
    results = [_make_result(latency_ms=10.0) for _ in range(10)]
    assert compute_latency_p95(results) == 10.0


# ---------------------------------------------------------------------------
# compute_all
# ---------------------------------------------------------------------------


def test_compute_all_counts() -> None:
    """compute_all reports correct total, malicious, and benign counts."""
    results = [
        _make_result(payload_type="malicious"),
        _make_result(payload_type="malicious"),
        _make_result(payload_type="benign"),
    ]
    m = compute_all(results)
    assert m["total_results"] == 3
    assert m["malicious_count"] == 2
    assert m["benign_count"] == 1


def test_compute_all_keys_present() -> None:
    """compute_all always returns all expected top-level keys."""
    m = compute_all([])
    for key in ("asr", "tpr_fpr", "score_error", "latency_p95_ms", "total_results", "malicious_count", "benign_count"):
        assert key in m, f"missing key: {key}"


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


def test_format_report_contains_asr() -> None:
    """format_report output mentions ASR and the category name."""
    metrics = compute_all([
        {"payload_type": "malicious", "category": "C1", "damage_detected": True, "score": {"combined": None}, "latency_ms": 10},
    ])
    report = format_report(metrics)
    assert "ASR" in report
    assert "C1" in report


def test_format_report_is_string() -> None:
    """format_report always returns a string."""
    assert isinstance(format_report(compute_all([])), str)


def test_format_report_overall_asr_shown() -> None:
    """format_report includes the overall ASR value."""
    metrics = compute_all([
        _make_result(damage_detected=True),
        _make_result(damage_detected=False),
    ])
    report = format_report(metrics)
    assert "0.50" in report


def test_format_report_latency_shown() -> None:
    """format_report includes the p95 latency value."""
    metrics = compute_all([_make_result(latency_ms=20.0)])
    report = format_report(metrics)
    assert "20.0 ms" in report


def test_format_report_no_results() -> None:
    """format_report handles empty results without crashing."""
    report = format_report(compute_all([]))
    assert "0" in report  # total results line
