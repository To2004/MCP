"""Score one captured call against a server's scanned risk matrix.

A call is scored only when it resolves to a scanned ``(tool, asset)`` cell; that
score and band come straight from the scan. Calls that cannot be resolved are
reported with an honest status, never a fabricated score:

* ``invalid`` — the tool is absent from the scan's tool set (typically a typo or
  non-existent tool, e.g. ``drop_table``). A misconfiguration signal.
* ``unresolved`` — a known tool whose target asset is not a scanned cell: a
  directory/enumeration op with no single file asset, a no-argument call, or an
  extension/file the scan never enumerated.

When a per-tool **parameter rubric** is supplied, the call's input-parameter risk
(see :mod:`mcp_security.param_scoring`) is computed and **escalates** the resolved
(tool, asset) band into ``final_band`` — a large/bulk parameter can raise a call's
risk above the inherent cell risk.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcp_security.param_scoring import score_call_params
from mcp_security.param_scoring.rubric import ToolRubric

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
    persona: str
    server: str
    asset: str | None
    tool_impact: int | None
    sensitivity: int | None
    score: float | None
    band: str
    scorable: bool
    reason: str
    # Input-parameter dimension (None when no rubric/magnitude parameter applied).
    param_band: str | None
    param_top: str | None
    final_band: str
    args_raw: str

    @classmethod
    def _of(cls, call: Call, table: StaticTable, param, **overrides) -> ScoredCall:
        band = overrides.get("band", STATUS_UNRESOLVED)
        scorable = overrides.get("scorable", False)
        # The parameter risk escalates a resolved band; for unscored statuses the
        # final band is the status itself (no inherent band to escalate).
        final_band = param.combined_with(band) if scorable else band
        base = {
            "source": call.source,
            "run_id": call.run_id,
            "index": call.index,
            "tool": call.tool,
            "category": call.category,
            "persona": call.persona,
            "server": table.name,
            "asset": None,
            "tool_impact": table.tool_impact.get(call.tool),
            "sensitivity": None,
            "score": None,
            "band": STATUS_UNRESOLVED,
            "scorable": False,
            "reason": "",
            "param_band": param.band,
            "param_top": param.top_param,
            "final_band": final_band,
            "args_raw": call.args_raw,
        }
        base.update(overrides)
        return cls(**base)


def score_call(
    call: Call, table: StaticTable, rubric: ToolRubric | None = None
) -> ScoredCall:
    """Score a call against ``table``; never raises and never fabricates.

    ``rubric`` is the call's tool's parameter rubric; when given, the call's
    parameter risk escalates the resolved band into ``final_band``.
    """
    param = score_call_params(call.args, rubric) if rubric is not None else _NO_PARAM

    if not table.has_tool(call.tool):
        return ScoredCall._of(
            call, table, param,
            band=STATUS_INVALID,
            reason="unknown tool (likely misconfiguration)",
        )

    resolved = resolve_asset(call, table)
    if resolved.resolved and resolved.asset is not None:
        cell = table.cell(call.tool, resolved.asset)
        if cell is not None:
            score, band = cell
            return ScoredCall._of(
                call, table, param,
                asset=resolved.asset,
                sensitivity=resolved.sensitivity,
                score=score,
                band=band,
                scorable=True,
                reason=f"scanned cell: {call.tool} x {resolved.asset} ({resolved.basis})",
            )

    return ScoredCall._of(call, table, param, reason=resolved.basis)


# Sentinel parameter score used when no rubric is supplied (no parameter signal).
from mcp_security.param_scoring.apply import ParamScore  # noqa: E402

_NO_PARAM = ParamScore(band=None, top_param=None, details=())
