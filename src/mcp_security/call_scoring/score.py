"""Score one captured call against a server's static risk table.

Resolution outcomes:

* **unknown tool** — the tool is absent from the table's registry (typically a
  ``BAD_TOOL`` misconfiguration: a typo or a non-existent tool). Unscorable;
  flagged as an ``invalid`` band, which is itself a defensive signal.
* **resolved asset** — scored directly from the table's precomputed ``cells``
  matrix (exact score and band).
* **unresolved asset** — known tool but the target asset is not in the table
  (e.g. an extension the design-time table never enumerated). Scored as a
  worst-case floor: minimum sensitivity at the tool's highest blast radius.
"""

from __future__ import annotations

from dataclasses import dataclass

from .loader import Call
from .resolve import resolve_asset
from .tables import StaticTable

INVALID_BAND = "invalid"


@dataclass(frozen=True)
class ScoredCall:
    """A captured call with its risk score, band, and how it was derived."""

    source: str
    index: str
    tool: str
    category: str
    server: str
    asset: str | None
    tool_impact: int | None
    sensitivity: int | None
    score: float | None
    band: str
    scorable: bool
    reason: str
    args_raw: str


def score_call(call: Call, table: StaticTable) -> ScoredCall:
    """Score a single call against ``table``; never raises on bad input."""
    impact = table.tool_impact.get(call.tool)
    if impact is None:
        return ScoredCall(
            source=call.source,
            index=call.index,
            tool=call.tool,
            category=call.category,
            server=table.name,
            asset=None,
            tool_impact=None,
            sensitivity=None,
            score=None,
            band=INVALID_BAND,
            scorable=False,
            reason="unknown tool (likely misconfiguration)",
            args_raw=call.args_raw,
        )

    resolved = resolve_asset(call, table)
    if resolved.resolved and resolved.asset is not None:
        cell = table.cell(call.tool, resolved.asset)
        if cell is not None:
            score, band = cell
            reason = f"static cell: {call.tool} x {resolved.asset} ({resolved.basis})"
        else:
            score, band = table.compute(
                call.tool, resolved.sensitivity or 0, table.blast(call.tool, resolved.asset) or 0
            )
            reason = f"computed: {resolved.basis}"
        sensitivity = resolved.sensitivity
        asset = resolved.asset
    else:
        # Known tool, unknown asset: worst-case floor estimate.
        floor_sensitivity = min(table.asset_sensitivity.values(), default=1)
        score, band = table.compute(call.tool, floor_sensitivity, table.worst_blast(call.tool))
        sensitivity = floor_sensitivity
        asset = None
        reason = f"floor estimate ({resolved.basis})"

    return ScoredCall(
        source=call.source,
        index=call.index,
        tool=call.tool,
        category=call.category,
        server=table.name,
        asset=asset,
        tool_impact=impact,
        sensitivity=sensitivity,
        score=score,
        band=band,
        scorable=True,
        reason=reason,
        args_raw=call.args_raw,
    )
