"""Tests for the deterministic scan renderers (markdown + CSV export)."""

from __future__ import annotations

from mcp_security.scanner.render import matrix_csv, matrix_rows, scan_to_markdown

# A minimal two-tool x two-asset table whose scores are exactly sensitivity*blast*impact.
_TABLE = {
    "server": "demo:server",
    "server_kind": "filesystem",
    "tool_impact": {"read_file": 1, "delete_file": 3},
    "asset_sensitivity": {"public": 1, "secrets": 5},
    "blast_radius": {
        "read_file|public": 4,
        "read_file|secrets": 1,
        "delete_file|public": 2,
        "delete_file|secrets": 2,
    },
    "cells": {
        "public": {"read_file": 4, "delete_file": 6},
        "secrets": {"read_file": 5, "delete_file": 30},
    },
    "bands": {
        "public": {"read_file": "low", "delete_file": "medium"},
        "secrets": {"read_file": "medium", "delete_file": "high"},
    },
}


def test_matrix_rows_exposes_the_primitives_behind_each_score():
    rows = {(r["asset"], r["tool"]): r for r in matrix_rows(_TABLE)}
    assert len(rows) == 4
    cell = rows[("secrets", "delete_file")]
    # score must equal sensitivity * blast * impact so the calculation is auditable.
    assert cell["sensitivity"] * cell["blast"] * cell["impact"] == int(cell["score"])
    assert cell["band"] == "high"


def test_matrix_csv_header_and_calculation_columns():
    lines = matrix_csv(_TABLE).strip().splitlines()
    assert lines[0] == "asset,tool,sensitivity,blast,impact,score,band"
    assert len(lines) == 1 + 4  # header + one row per (asset, tool)
    assert "secrets,delete_file,5,2,3,30,high" in lines


def test_markdown_matrix_shows_calculation_in_place():
    md = scan_to_markdown("demo:server", "filesystem", _TABLE)
    assert "sensitivity×blast×impact" in md
    assert "30 (5×2×3)" in md


def test_markdown_has_blast_radius_coverage_matrix():
    md = scan_to_markdown("demo:server", "filesystem", _TABLE)
    assert "## Blast radius (coverage · 1–5)" in md
    # the blast matrix shows the model's coverage value per (asset, tool)
    assert "coverage, not severity" in md
