"""Load the design-time static risk tables and expose per-call lookups.

A static table (one per MCP server kind) is the output of
:mod:`mcp_security.static_scoring`: it carries the three scoring primitives
(tool impact, asset sensitivity, per-pair blast radius), the multiplied
``cells`` matrix, and the pre-banded ``bands`` matrix. This module loads the
committed bundle (``reports/samples/all_static_tables.json``) and wraps each
table so a single observed call ``(tool, asset)`` can be scored by lookup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLES_BUNDLE = REPO_ROOT / "reports" / "samples" / "all_static_tables.json"

# The static-scoring formula, reproduced for fallback scoring of pairs that are
# not present in a table's precomputed ``cells`` matrix.
LIKELIHOOD = 1.0

# Ordering used when comparing or sorting band labels.
BAND_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def band_for_score(score: float, thresholds: dict[str, float]) -> str:
    """Map a numeric score to a band using a table's ``band_thresholds``.

    Used only for fallback (computed) scores; pairs found in a table's ``cells``
    matrix carry their own pre-banded label, which is preferred.
    """
    if score >= thresholds["high"]:
        return "critical"
    if score >= thresholds["medium"]:
        return "high"
    if score >= thresholds["low"]:
        return "medium"
    return "low"


@dataclass(frozen=True)
class StaticTable:
    """One server kind's design-time risk table, indexed for call scoring."""

    name: str
    server: str
    mcp_kind: str
    tool_impact: dict[str, int]
    asset_sensitivity: dict[str, int]
    blast_radius: dict[str, int]  # "tool|asset" -> 0..4
    cells: dict[str, dict[str, float]]  # asset -> tool -> score
    bands: dict[str, dict[str, str]]  # asset -> tool -> band label
    band_thresholds: dict[str, float]

    @property
    def assets(self) -> list[str]:
        return list(self.asset_sensitivity)

    def has_tool(self, tool: str) -> bool:
        return tool in self.tool_impact

    def cell(self, tool: str, asset: str) -> tuple[float, str] | None:
        """Return ``(score, band)`` for a precomputed (asset, tool) cell."""
        row = self.cells.get(asset)
        if row is None or tool not in row:
            return None
        return row[tool], self.bands[asset][tool]

    def blast(self, tool: str, asset: str) -> int | None:
        return self.blast_radius.get(f"{tool}|{asset}")

    def worst_blast(self, tool: str) -> int:
        """Highest blast radius this tool reaches across any asset (worst case)."""
        vals = [v for k, v in self.blast_radius.items() if k.startswith(f"{tool}|")]
        return max(vals) if vals else 0

    def compute(self, tool: str, sensitivity: int, blast: int) -> tuple[float, str]:
        """Score a pair not present in ``cells`` via the static-scoring formula."""
        score = sensitivity * blast * LIKELIHOOD * self.tool_impact.get(tool, 0)
        return score, band_for_score(score, self.band_thresholds)


def _table_from_dict(name: str, raw: dict) -> StaticTable:
    return StaticTable(
        name=name,
        server=raw.get("server", name),
        mcp_kind=raw.get("mcp_kind", "unknown"),
        tool_impact=dict(raw.get("tool_impact", {})),
        asset_sensitivity=dict(raw.get("asset_sensitivity", {})),
        blast_radius=dict(raw.get("blast_radius", {})),
        cells=raw.get("cells", {}),
        bands=raw.get("bands", {}),
        band_thresholds=raw.get("band_thresholds", {"low": 6, "medium": 18, "high": 36}),
    )


def load_tables(bundle: Path = TABLES_BUNDLE) -> dict[str, StaticTable]:
    """Load every static table from the committed bundle, keyed by table name."""
    data = json.loads(bundle.read_text(encoding="utf-8"))
    return {name: _table_from_dict(name, raw) for name, raw in data["tables"].items()}
