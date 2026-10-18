"""CIA as a dynamic misuse signal: is this call attacking what the org protects?

The other dynamic signals ask about the *agent*: does this persona normally call
this tool (:mod:`.baseline`), is this ordering suspicious (:mod:`.sequence`), does
a reviewer object (:mod:`.judge`). None of them ask about the *objective*.

This one does, with a single rule::

    the call violates the objective the organization named as this asset's
    primary loss  ->  escalate

Two calls on the same asset with the same static band are then separated by
whether they attack what the org said it cares about. Reading an executive
channel attacks confidentiality, which is what that channel is for protecting;
marking it read does not. The static matrix cannot tell them apart, because
sensitivity is one number per asset and the tool axis never consults it.

Both inputs already exist and cost nothing at runtime:

* the **objective a call violates** — from the atomic-op classification
  (:mod:`mcp_security.static_scoring.cia_facets`), a table lookup;
* the **objective an asset protects** — the leading axis of the policy register's
  ``CIA`` cell (``C>I>A`` -> C), parsed once per server at load.

Like every dynamic signal it can only ever raise a band
(:func:`mcp_security.param_scoring.combine.escalate` takes the max), so a call
that is off-axis is left exactly where the static scan put it.
"""

from __future__ import annotations

from mcp_security.static_scoring.cia_facets import (
    FACETS,
    LossAxisError,
    parse_loss_axis,
    violated_facets,
)
from mcp_security.static_scoring.server_policies import parse_asset_register, policy_for

# The band a call earns for attacking an asset's primary loss objective. `high`
# rather than `critical`: this signal says "the wrong objective for this asset",
# which is a reason to look, not on its own a reason to page someone.
ON_AXIS_BAND = "high"
OFF_AXIS_BAND = "low"


def leading_facet(cia_cell: str) -> str | None:
    """The objective an asset protects first, or ``None`` when it states no order.

    ``I≈C>A`` is a genuine tie; both count as leading, and the caller treats a
    call touching either as on-axis. An unreadable cell degrades to ``None`` (no
    signal) rather than raising — a malformed policy row must not take down a
    runtime scoring path.
    """
    try:
        ranks = parse_loss_axis(cia_cell)
    except LossAxisError:
        return None
    if len({ranks[facet] for facet in FACETS}) == 1:
        return None  # every facet ranked equally: the cell states no priority
    return min(FACETS, key=lambda facet: ranks[facet])


def leading_facets(cia_cell: str) -> frozenset[str]:
    """Every objective sharing the top rank (handles the ``I≈C>A`` tie)."""
    try:
        ranks = parse_loss_axis(cia_cell)
    except LossAxisError:
        return frozenset()
    if len({ranks[facet] for facet in FACETS}) == 1:
        return frozenset()
    top = min(ranks.values())
    return frozenset(facet for facet in FACETS if ranks[facet] == top)


def load_asset_axes(server: str) -> dict[str, frozenset[str]]:
    """``{asset_id: leading objectives}`` for one server, from its policy register.

    Returns ``{}`` when the server has no policy section, which disables the
    signal for it rather than guessing.
    """
    try:
        policy = policy_for(server)
        rows = parse_asset_register(policy.text)
    except Exception:  # noqa: BLE001 -- a missing//malformed policy disables the signal
        return {}
    return {row.asset_id: leading_facets(row.cia) for row in rows}


def score_cia(
    call,
    asset_axes: dict[str, frozenset[str]],
    tool_ops: dict[str, list[str]],
) -> tuple[str, str]:
    """Band + reason for one call: does it attack this asset's primary loss?

    ``asset_axes`` comes from :func:`load_asset_axes`; ``tool_ops`` maps a tool
    name to its atomic ops (the ``tool_atomic_ops`` block of the server's scan
    artifact). Anything unknown yields ``low`` with a stated reason — the signal
    abstains rather than inventing an escalation.
    """
    if not call.asset:
        return OFF_AXIS_BAND, "no asset on this call"
    leading = asset_axes.get(call.asset)
    if not leading:
        return OFF_AXIS_BAND, f"{call.asset}: policy states no loss priority"
    ops = tool_ops.get(call.tool)
    if ops is None:
        return OFF_AXIS_BAND, f"{call.tool}: no atomic-op classification"
    violated = violated_facets(ops)
    hit = sorted(leading & set(violated))
    if hit:
        return ON_AXIS_BAND, (
            f"violates {'+'.join(hit)} — the objective {call.asset} protects first "
            f"({'/'.join(sorted(leading))})"
        )
    return OFF_AXIS_BAND, (
        f"violates {'+'.join(violated) or 'nothing'}; {call.asset} protects "
        f"{'/'.join(sorted(leading))}"
    )


__all__ = ["ON_AXIS_BAND", "OFF_AXIS_BAND", "leading_facet", "leading_facets",
           "load_asset_axes", "score_cia"]
