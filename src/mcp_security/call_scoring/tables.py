"""Load the scanner's risk matrices and expose per-call lookups.

A captured call is scored against the matrix the **scanner** produced for that
server — a *scan artifact* under ``reports/scan/<server>.json``, freshly derived
by the LLM from the scanned tools and assets. These artifacts have the same shape
as a static table (the three primitives, the ``cells`` matrix, the ``bands``
matrix), so one observed ``(tool, asset)`` can be scored by lookup into the
scan.

This module deliberately does **not** read the committed design-time tables under
``reports/samples`` or ``reports/evaluation``: those are ground truth for grading
the scanner, never an input to scoring.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_DIR = REPO_ROOT / "reports" / "scan"

# Status labels for calls that do not resolve to a scanned cell. They are
# deliberately NOT risk bands: the scan bands each cell with the model's domain
# reasoning, so a call we cannot resolve is reported as a status, never given a
# fabricated band.
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
    """One server's scanned risk matrix, indexed for call scoring."""

    name: str
    server: str
    mcp_kind: str
    # The registry kind (filesystem/sqlite/slack/calendar/github), recorded by the
    # scanner. Authoritative for resolver dispatch; "" for older scans (fall back
    # to the inferred ``mcp_kind`` then).
    server_kind: str
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
        """Return the scanned ``(score, band)`` for an (asset, tool) cell.

        The band is taken verbatim from the scan's ``bands`` matrix — it is the
        model's judgement and is never recomputed from the score.
        """
        row = self.cells.get(asset)
        if row is None or tool not in row:
            return None
        return row[tool], self.bands[asset][tool]


def table_from_dict(name: str, raw: dict) -> StaticTable:
    """Wrap a scan-artifact dict (or any same-shaped table) as a StaticTable."""
    return StaticTable(
        name=name,
        server=raw.get("server", name),
        mcp_kind=raw.get("mcp_kind", "unknown"),
        server_kind=raw.get("server_kind", ""),
        tool_impact=dict(raw.get("tool_impact", {})),
        asset_sensitivity=dict(raw.get("asset_sensitivity", {})),
        blast_radius=dict(raw.get("blast_radius", {})),
        cells=raw.get("cells", {}),
        bands=raw.get("bands", {}),
        band_thresholds=raw.get("band_thresholds", {"low": 6, "medium": 18, "high": 36}),
    )


def load_scan(path: Path) -> StaticTable:
    """Load a single scan artifact (``reports/scan/<server>.json``)."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return table_from_dict(path.stem, raw)


def load_scans(scan_dir: Path = SCAN_DIR) -> dict[str, StaticTable]:
    """Load every scan artifact in ``scan_dir``, keyed by its filename stem.

    Returns an empty mapping (with a warning) when no scans exist yet — the
    scanner must be run first, which needs the local LLM. ``*_params.json`` files
    (parameter rubrics) are skipped here; load them with :func:`load_param_rubrics`.
    """
    if not scan_dir.exists():
        logger.warning("no scan directory %s — run `python -m mcp_security.scanner` first", scan_dir)
        return {}
    scans = {
        p.stem: load_scan(p)
        for p in sorted(scan_dir.glob("*.json"))
        if not p.stem.endswith("_params")
    }
    if not scans:
        logger.warning("no scan artifacts in %s — run the scanner first", scan_dir)
    return scans


def load_param_rubrics(scan_dir: Path = SCAN_DIR) -> dict[str, dict]:
    """Load parameter rubrics, keyed by scan stem -> {tool_name: ToolRubric}.

    Reads ``<server>_params.json`` artifacts (produced by
    ``python -m mcp_security.param_scoring``). Returns an empty mapping if none
    exist, in which case call scoring simply skips the parameter dimension.
    """
    from mcp_security.param_scoring.rubric import ToolRubric

    rubrics: dict[str, dict] = {}
    if not scan_dir.exists():
        return rubrics
    for path in sorted(scan_dir.glob("*_params.json")):
        stem = path.stem[: -len("_params")]
        raw = json.loads(path.read_text(encoding="utf-8"))
        rubrics[stem] = {
            tool: ToolRubric.from_dict(r) for tool, r in raw.get("rubrics", {}).items()
        }
    return rubrics
