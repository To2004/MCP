"""Score one captured call against a server's static risk table.

A call is scored only when it resolves to a precomputed ``(tool, asset)`` cell;
that score and band come straight from the design-time table. Calls that cannot
be resolved are reported with an honest status, never a fabricated score:

* ``invalid`` — the tool is absent from the table's registry (typically a typo
  or non-existent tool, e.g. ``drop_table``). A misconfiguration signal.
* ``unresolved`` — a known tool whose target asset is not a cell in the table:
  a directory/enumeration op with no single file asset, a no-argument call, or
  an extension/table the design-time table never enumerated. The ``reason``
  records which, so the table can be extended where it matters.
"""

from __future__ import annotations

from dataclasses import dataclass

from .loader import Call
from .resolve import resolve_asset
from .tables import STATUS_INVALID, STATUS_UNRESOLVED, StaticTable


@dataclass(frozen=True)
class ScoredCall:
    """A captured call with its risk score and band, or an honest status."""

    source: str
    run_id: str
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

    @classmethod
    def _of(cls, call: Call, table: StaticTable, **overrides) -> ScoredCall:
        base = {
            "source": call.source,
            "run_id": call.run_id,
            "index": call.index,
            "tool": call.tool,
            "category": call.category,
            "server": table.name,
            "asset": None,
            "tool_impact": table.tool_impact.get(call.tool),
            "sensitivity": None,
            "score": None,
            "band": STATUS_UNRESOLVED,
            "scorable": False,
            "reason": "",
            "args_raw": call.args_raw,
        }
        base.update(overrides)
        return cls(**base)


def score_call(call: Call, table: StaticTable) -> ScoredCall:
    """Score a single call against ``table``; never raises and never fabricates."""
    if not table.has_tool(call.tool):
        return ScoredCall._of(
            call,
            table,
            band=STATUS_INVALID,
            reason="unknown tool (likely misconfiguration)",
        )

    resolved = resolve_asset(call, table)
    if resolved.resolved and resolved.asset is not None:
        cell = table.cell(call.tool, resolved.asset)
        if cell is not None:
            score, band = cell
            return ScoredCall._of(
                call,
                table,
                asset=resolved.asset,
                sensitivity=resolved.sensitivity,
                score=score,
                band=band,
                scorable=True,
                reason=f"static cell: {call.tool} x {resolved.asset} ({resolved.basis})",
            )

    return ScoredCall._of(call, table, reason=resolved.basis)
