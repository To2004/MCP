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

# Status labels for calls that do not resolve to a precomputed table cell. They
# are deliberately NOT risk bands: the tables band each cell with domain
# reasoning that cannot be reconstructed from the numeric score alone, so a call
# we cannot resolve is reported as a status, never given a fabricated band.
STATUS_UNRESOLVED = "unresolved"
STATUS_INVALID = "invalid"

# Ordering used when sorting: real risk bands rank above the non-scored statuses.
BAND_ORDER = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    STATUS_UNRESOLVED: 1,
    STATUS_INVALID: 0,
}


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
        """Return the precomputed ``(score, band)`` for an (asset, tool) cell.

        The band is taken verbatim from the table's ``bands`` matrix — it is the
        design-time judgement and is never recomputed from the score.
        """
        row = self.cells.get(asset)
        if row is None or tool not in row:
            return None
        return row[tool], self.bands[asset][tool]


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
