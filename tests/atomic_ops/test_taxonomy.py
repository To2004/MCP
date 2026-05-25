"""Tests for the atomic-op taxonomy loader."""

from pathlib import Path

import pytest

from mcp_security.atomic_ops.taxonomy import AtomicOp, load_taxonomy

TAXONOMY_CSV = (
    Path(__file__).resolve().parents[2]
    / "presentations"
    / "heatmap_byhand"
    / "csv"
    / "atomic_operations.csv"
)


def test_load_taxonomy_returns_thirteen_ops():
    ops = load_taxonomy(TAXONOMY_CSV)
    assert len(ops) >= 13


def test_load_taxonomy_first_op_is_execute_critical():
    ops = load_taxonomy(TAXONOMY_CSV)
    first = ops[0]
    assert first.name == "EXECUTE"
    assert first.severity == 5
    assert first.severity_label == "Critical"


def test_load_taxonomy_rank_one_through_thirteen_present():
    ops = load_taxonomy(TAXONOMY_CSV)
    ranks = {op.rank for op in ops}
    for r in range(1, 14):
        assert r in ranks


def test_load_taxonomy_returns_dataclass():
    ops = load_taxonomy(TAXONOMY_CSV)
    assert isinstance(ops[0], AtomicOp)


def test_load_taxonomy_severity_in_range():
    ops = load_taxonomy(TAXONOMY_CSV)
    for op in ops:
        assert 1 <= op.severity <= 5


def test_load_taxonomy_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_taxonomy(tmp_path / "nonexistent.csv")
