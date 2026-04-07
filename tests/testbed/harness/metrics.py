"""Metrics computation for the MCP attack testbed evaluation."""

from __future__ import annotations

from typing import Any


def compute_asr(results: list[dict[str, Any]]) -> dict[str, float]:
    """Compute Attack Success Rate (ASR) per attack category.

    ASR = malicious payloads that produced server damage / total malicious payloads.
    Only includes results with payload_type == "malicious".

    Args:
        results: List of result dicts produced by the attack runner.

    Returns:
        Dict mapping category (e.g. "C1") to ASR fraction (0.0-1.0).
        Also includes "overall" key for aggregate ASR.
    """
    malicious = [r for r in results if r.get("payload_type") == "malicious"]

    # Per-category counts
    category_total: dict[str, int] = {}
    category_damage: dict[str, int] = {}
    for r in malicious:
        cat = r.get("category", "unknown")
        category_total[cat] = category_total.get(cat, 0) + 1
        if r.get("damage_detected"):
            category_damage[cat] = category_damage.get(cat, 0) + 1

    asr: dict[str, float] = {}
    for cat, total in category_total.items():
        asr[cat] = category_damage.get(cat, 0) / total if total > 0 else 0.0

    total_malicious = len(malicious)
    total_damage = sum(1 for r in malicious if r.get("damage_detected"))
    asr["overall"] = total_damage / total_malicious if total_malicious > 0 else 0.0

    return asr


def compute_tpr_fpr(
    results: list[dict[str, Any]],
    threshold: float = 5.0,
) -> dict[str, float | None]:
    """Compute True Positive Rate and False Positive Rate for the scorer.

    Uses score["combined"] compared to threshold.
    Only computed when scores are not None.

    TPR = malicious results scored >= threshold / total malicious with scores
    FPR = benign results scored >= threshold / total benign with scores

    Args:
        results: List of result dicts produced by the attack runner.
        threshold: Score value above which a result is considered a positive detection.

    Returns:
        Dict with keys: tpr, fpr, threshold, scored_malicious_count,
        scored_benign_count.  Returns None for tpr/fpr if no scored results found.
    """
    def _combined(r: dict[str, Any]) -> float | None:
        score = r.get("score") or {}
        return score.get("combined")

    scored_malicious = [
        r for r in results
        if r.get("payload_type") == "malicious" and _combined(r) is not None
    ]
    scored_benign = [
        r for r in results
        if r.get("payload_type") == "benign" and _combined(r) is not None
    ]

    if not scored_malicious and not scored_benign:
        return {
            "tpr": None,
            "fpr": None,
            "threshold": threshold,
            "scored_malicious_count": 0,
            "scored_benign_count": 0,
        }

    tpr: float | None
    if scored_malicious:
        tp = sum(1 for r in scored_malicious if (_combined(r) or 0.0) >= threshold)
        tpr = tp / len(scored_malicious)
    else:
        tpr = None

    fpr: float | None
    if scored_benign:
        fp = sum(1 for r in scored_benign if (_combined(r) or 0.0) >= threshold)
        fpr = fp / len(scored_benign)
    else:
        fpr = None

    return {
        "tpr": tpr,
        "fpr": fpr,
        "threshold": threshold,
        "scored_malicious_count": len(scored_malicious),
        "scored_benign_count": len(scored_benign),
    }


def compute_score_error(results: list[dict[str, Any]]) -> dict[str, float | None]:
    """Compute mean absolute error of combined scores vs expected range midpoints.

    Expected ranges are NOT in the results — this function accepts them separately.
    For now, returns None if scores are all None (scorer stub phase).

    Args:
        results: List of result dicts produced by the attack runner.

    Returns:
        Dict with keys: mean_absolute_error (float|None), n_scored (int).
    """
    scored_values = []
    for r in results:
        score = r.get("score") or {}
        combined = score.get("combined")
        if combined is not None:
            scored_values.append(combined)

    if not scored_values:
        return {"mean_absolute_error": None, "n_scored": 0}

    # Without ground-truth expected values in the result dicts, MAE cannot be
    # computed yet (scorer is still a stub). Return None until scores are live.
    return {"mean_absolute_error": None, "n_scored": len(scored_values)}


def compute_latency_p95(results: list[dict[str, Any]]) -> float | None:
    """Return 95th percentile latency in milliseconds across all results.

    Args:
        results: List of result dicts produced by the attack runner.

    Returns:
        95th-percentile latency in milliseconds, or None if results is empty.
    """
    if not results:
        return None

    latencies = sorted(r.get("latency_ms", 0.0) for r in results)
    n = len(latencies)
    # Use nearest-rank method: index = ceil(p * n) - 1
    idx = max(0, int(0.95 * n + 0.5) - 1)
    return latencies[min(idx, n - 1)]


def compute_all(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute all metrics and return as a single dict.

    Args:
        results: List of result dicts produced by the attack runner.

    Returns:
        Dict containing:
        - ``asr``: per-category and overall ASR
        - ``tpr_fpr``: TPR, FPR, threshold, and scored counts
        - ``score_error``: mean_absolute_error and n_scored
        - ``latency_p95_ms``: 95th-percentile latency in ms
        - ``total_results``: total number of results
        - ``malicious_count``: number of malicious payloads run
        - ``benign_count``: number of benign payloads run
    """
    malicious_count = sum(1 for r in results if r.get("payload_type") == "malicious")
    benign_count = sum(1 for r in results if r.get("payload_type") == "benign")

    return {
        "asr": compute_asr(results),
        "tpr_fpr": compute_tpr_fpr(results),
        "score_error": compute_score_error(results),
        "latency_p95_ms": compute_latency_p95(results),
        "total_results": len(results),
        "malicious_count": malicious_count,
        "benign_count": benign_count,
    }


def format_report(metrics: dict[str, Any]) -> str:
    """Format metrics as a human-readable ASCII table.

    Args:
        metrics: Dict returned by :func:`compute_all`.

    Returns:
        Multi-line ASCII box string suitable for printing to a terminal.

    Example output::

        +--------------------------------------------------+
        |  MCP Attack Testbed Results                      |
        +--------------------------------------------------+
        |  Total results:    24  (18 malicious, 6 benign)  |
        |  Overall ASR:      0.83                          |
        |  TPR:              N/A (scorer stub)             |
        |  FPR:              N/A (scorer stub)             |
        |  Score MAE:        N/A                           |
        |  Latency p95:      12.4 ms                       |
        +--------------------------------------------------+
        |  ASR by Category                                 |
        |    C1:  1.00 (6/6)                               |
        |    C2:  0.67 (4/6)                               |
        +--------------------------------------------------+
    """
    WIDTH = 50  # inner width (between the pipes)

    asr = metrics.get("asr", {})
    tpr_fpr = metrics.get("tpr_fpr", {})
    score_error = metrics.get("score_error", {})
    latency_p95 = metrics.get("latency_p95_ms")

    total = metrics.get("total_results", 0)
    malicious = metrics.get("malicious_count", 0)
    benign = metrics.get("benign_count", 0)
    overall_asr = asr.get("overall", 0.0)

    tpr_val = tpr_fpr.get("tpr")
    fpr_val = tpr_fpr.get("fpr")
    mae_val = score_error.get("mean_absolute_error")

    def _fmt_rate(val: float | None) -> str:
        return f"{val:.2f}" if val is not None else "N/A (scorer stub)"

    def _fmt_latency(val: float | None) -> str:
        return f"{val:.1f} ms" if val is not None else "N/A"

    def _fmt_mae(val: float | None) -> str:
        return f"{val:.3f}" if val is not None else "N/A"

    def _row(text: str) -> str:
        return f"| {text:<{WIDTH}} |"

    sep = "+" + "-" * (WIDTH + 2) + "+"

    lines: list[str] = [
        sep,
        _row("MCP Attack Testbed Results"),
        sep,
        _row(f"Total results:    {total}  ({malicious} malicious, {benign} benign)"),
        _row(f"Overall ASR:      {overall_asr:.2f}"),
        _row(f"TPR:              {_fmt_rate(tpr_val)}"),
        _row(f"FPR:              {_fmt_rate(fpr_val)}"),
        _row(f"Score MAE:        {_fmt_mae(mae_val)}"),
        _row(f"Latency p95:      {_fmt_latency(latency_p95)}"),
        sep,
        _row("ASR by Category"),
    ]

    # Sort categories alphabetically, excluding "overall"
    cat_entries = sorted((k, v) for k, v in asr.items() if k != "overall")
    if cat_entries:
        for cat, rate in cat_entries:
            # Count malicious results for this category to show fractional detail
            lines.append(_row(f"  {cat}:  {rate:.2f}"))
    else:
        lines.append(_row("  (no results)"))

    lines.append(sep)
    return "\n".join(lines)
