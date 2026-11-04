"""Tests for scripts/call_distributions.py: shape statistics and the corpus loaders."""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import call_distributions as cd  # noqa: E402


def test_rank_shares_sorted_and_normalised():
    shares = cd.rank_shares(Counter({"a": 1, "b": 6, "c": 3}))
    assert list(shares) == [0.6, 0.3, 0.1]
    with pytest.raises(ValueError):
        cd.rank_shares(Counter())


def test_concentration_counts_tools_for_80_percent_and_catalog_use():
    result = cd.concentration(np.array([0.5, 0.25, 0.15, 0.1]), catalog_size=10)
    assert result["top1"] == 0.5 and result["top3"] == pytest.approx(0.9)
    assert result["tools_for_80pct"] == 3
    assert result["tools_used"] == 4 and result["catalog_size"] == 10


def test_rank_curve_tells_geometric_from_zipf():
    ranks = np.arange(1, 21)
    geometric = 0.5**ranks
    zipf = ranks**-1.5
    assert cd.fit_rank_curve(geometric / geometric.sum())["better"] == "geometric"
    fit = cd.fit_rank_curve(zipf / zipf.sum())
    assert fit["better"] == "zipf" and fit["zipf_exponent"] == pytest.approx(1.5)


def test_fit_shapes_picks_lognormal_for_lognormal_data():
    rng = np.random.default_rng(1)
    values = rng.lognormal(mean=1.0, sigma=1.0, size=5000)
    assert cd.fit_shapes(values, rng)["best"] == "lognorm"


def test_hill_tail_index_recovers_a_pareto_exponent():
    rng = np.random.default_rng(2)
    values = rng.pareto(1.5, size=200_000) + 1
    assert cd.hill_tail_index(values) == pytest.approx(1.5, abs=0.15)


def test_ccdf_starts_at_one_and_never_rises():
    points = cd.ccdf_points(np.array([1.0, 2, 2, 5, 100]))
    probabilities = [p for _, p in points]
    assert probabilities[0] == 1.0
    assert all(b <= a for a, b in zip(probabilities, probabilities[1:], strict=False))


def test_top_share_of_the_largest_values():
    assert cd.top_share(np.array([1.0, 1, 1, 97]), 0.25) == pytest.approx(0.97)


def test_hour_of_week_starts_monday_midnight_utc():
    monday = datetime(2024, 10, 14, 0, 30, tzinfo=timezone.utc).timestamp()
    sunday = datetime(2024, 10, 20, 23, 30, tzinfo=timezone.utc).timestamp()
    counts = cd.hour_of_week_counts(np.array([monday, sunday]))
    assert counts[0] == 1 and counts[167] == 1 and counts.sum() == 2


def test_session_gaps_sort_each_session():
    gaps = cd.session_gaps({"a": [5.0, 1.0, 3.0], "b": [9.0]})
    assert sorted(gaps) == [2.0, 2.0]


def test_tool_mix_counts_failures_only_on_labelled_calls(tmp_path: Path):
    path = tmp_path / "c.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["tool", "status"])
        writer.writeheader()
        for tool, status in [
            ("a", "ok"),
            ("a", "error:tool"),
            ("b", "TIMEOUT"),
            ("b", "skipped:not-executed"),
            ("c", "OK"),
        ]:
            writer.writerow({"tool": tool, "status": status})
    corpus = cd.load_tool_mix(path, "x", "persona corpus")
    assert corpus.tool_counts == Counter({"a": 2, "b": 2, "c": 1})
    assert corpus.failures == 2 and corpus.labelled_calls == 4


def _trace(trace_id: str, stamps: list[float]) -> dict:
    return {
        "trace_id": trace_id,
        "events": [
            {
                "server": "filesystem",
                "tool": "read_file",
                "timestamp": str(t),
                "result_chars": "10",
                "success": "True",
            }
            for t in stamps
        ],
    }


def test_mcphunt_runs_with_the_same_id_stay_apart_per_model(tmp_path: Path):
    traces, catalogs = tmp_path / "traces", tmp_path / "catalogs"
    traces.mkdir()
    (catalogs / "filesystem").mkdir(parents=True)
    (catalogs / "filesystem" / "mcphunt_filesystem.json").write_text(
        json.dumps({"tools": [{"name": "read_file"}, {"name": "write_file"}]})
    )
    (catalogs / "filesystem" / "mcphunt_filesystem.cells.json").write_text("{}")
    (traces / "model_a.json").write_text(json.dumps({"traces": [_trace("t1", [0.0, 1.0])]}))
    (traces / "model_b.json").write_text(json.dumps({"traces": [_trace("t1", [500.0, 503.0])]}))
    corpus = cd.load_mcphunt(traces, catalogs)
    assert sorted(corpus.gaps_s) == [1.0, 3.0]  # no 499 s gap across the two models
    assert corpus.catalog_size == 2 and list(corpus.session_lengths) == [2.0, 2.0]
    assert corpus.failures == 0 and corpus.labelled_calls == 4


def test_world2_keeps_only_tool_calls_per_agent_session(tmp_path: Path):
    path = tmp_path / "w.csv.gz"
    rows = [
        ("0", "a", "s1", "initialize", ""),
        ("1", "a", "s1", "tools/call", "x"),
        ("4", "a", "s1", "tools/call", "y"),
        ("2", "b", "s1", "tools/call", "x"),
    ]
    with gzip.open(path, "wt", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ts", "agent", "session", "method", "tool"])
        writer.writerows(rows)
    corpus = cd.load_world2(path, "github")
    assert corpus.tool_counts == Counter({"x": 2, "y": 1})
    assert sorted(corpus.session_lengths) == [1.0, 2.0] and list(corpus.gaps_s) == [3.0]
    assert corpus.hour_of_week[0] == 3  # world2 starts on a Monday at 00:00 UTC
