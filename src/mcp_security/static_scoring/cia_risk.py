"""CIA-native misuse score: additive evidence over the existing score, never a discount.

The framework's score stays ``sensitivity x blast x impact`` on 0-125 and stays the
primary output. CIA adds one thing the scale is blind to — **which objective a call
attacks, and how completely it attacks that objective** — and it is allowed to
raise a cell for it. It is never allowed to lower one::

    score_f = S x B_f x I_f          for each objective f the call can violate
    score   = max(v5_score, score_C, score_I, score_A)
    driver  = the objective that set it (or the existing score, if that won)

THE INVARIANT: ``score >= v5_score`` for every cell, by construction. This module
exists to surface risk the ladder under-prices, not to re-weight risk the
framework already prices correctly.

Why the invariant is not optional
---------------------------------
An earlier version split the asset's sensitivity by its register loss axis —
``C>I>A`` at sensitivity 4 became ``C=4, I=3, A=2`` — and then multiplied that by a
per-objective impact. Both are discounts, and on a mutation they compounded:
``create-events`` on the ``executive`` calendar fell from 64 to 36 because
integrity happened to rank second on an asset the organization calls a crown
jewel.

That was the same error the multiplicative score is criticised for: **treating an
ordinal ranking as a magnitude.** `C>I>A` says disclosure hurts most here. It does
not say integrity loss is a tier cheaper. An asset is as valuable as it is on
every objective it holds value on, so ``S`` is not split at all — the loss axis is
used only to break ties between objectives and to route the control.

What CIA still changes
----------------------
Per-objective impact replaces the single 1-5 action ladder *as a lower bound*.
The ladder (``metadata < read < write < delete``) hard-codes *destruction >
modification > disclosure*: reads cap at 3 while writes start at 4, so no read can
outrank a write on the same asset at the same coverage, whatever the asset holds.
Here a READ is ``I_C = 5`` — a **total** confidentiality violation — and ``I_I =
0``. Whether that matters is decided by the asset's own sensitivity, which is
where the judgement belongs. Mutations keep their existing values, so nothing
sensible moves down.

Grounding: CVSS v4.0 scores impact as a CIA triple (VC/VI/VA) rather than one
metric; FIPS 199 collapses a per-objective categorization with the high-water
mark, never a sum.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .cia_facets import FACETS, parse_loss_axis, violated_facets

# How completely one call violates each objective, per atomic operation. 0/absent
# means the operation cannot touch that objective at all.
#
# Calibrated against the framework's own ladder so a mutation never loses value:
# a write keeps 4 ("reversible write"), a delete keeps 5, an unrecallable send
# keeps 5. The only values that move UP are the reads, which is the whole point —
# a read of the substance is a total loss of confidentiality, not "a 3".
OP_IMPACT: dict[str, dict[str, int]] = {
    "PING": {},
    # Reads: what comes back decides how total the disclosure is.
    "METADATA": {"C": 2},  # about-ness only: names, sizes, state
    "LIST": {"C": 2},
    "SUBSCRIBE": {"C": 3},
    "SEARCH": {"C": 4},  # content drawn from across the asset
    "READ": {"C": 5},  # the substance itself, in full
    "FETCH": {"C": 5},
    "COPY": {"C": 5, "I": 4},  # a second data path outside the original's controls
    # Writes: unchanged from the ladder's own tiers.
    "CREATE": {"I": 4},
    "WRITE": {"I": 4},
    "MODIFY": {"I": 4},
    "MOVE": {"I": 4, "A": 3},
    "SCHEMA_MODIFY": {"I": 5, "A": 4},
    "OVERWRITE": {"I": 5, "A": 3},
    "DELETE": {"I": 5, "A": 5},
    # Boundary-crossing and execution.
    "BROADCAST": {"C": 4, "I": 5},  # discloses what it quotes; unrecallable once sent
    "AUTHENTICATE": {"C": 5, "I": 4},
    "CONFIGURE": {"I": 5, "A": 4},
    "EXECUTE": {"C": 5, "I": 5, "A": 5},
}
# An unclassified operation must not silently become harmless.
_UNKNOWN_OP_IMPACT = {"C": 3, "I": 3, "A": 3}

# Operations that return the SUBSTANCE of what they touch. Only these can realise
# a `self-sufficient` asset's confidentiality loss in one call: a credential leaks
# by being read — not by being listed, and not by posting into the channel it sits
# in. BROADCAST is deliberately absent.
_CONTENT_RETURNING_OPS = frozenset({"READ", "SEARCH", "COPY", "FETCH", "EXECUTE"})

# CVSS v4.0 "Subsequent System Impact": the consequence does not stay inside the
# asset. Sanctioned by the organization through the register's Flags.
_ESCAPE_FLAGS = frozenset({"hub", "self-sufficient", "population"})

SCORE_MAX = 125

# SENSITIVITY FLOOR: touching a crown jewel is consequential whatever the verb.
#
# Without this, an asset's value can be diluted away by the other two factors: a
# metadata listing on a sensitivity-5 asset scores 5 x 4 x 2 = 40 and sits in the
# middle of the matrix, below sensitivity-4 cells at 100. The product treats the
# three factors as freely exchangeable, so a low impact cancels a high
# sensitivity -- but an organization that calls an asset a crown jewel is not
# saying "unless the call is a listing".
#
# The floor applies only where the tool ACTUALLY acts on the asset (an N/A pair is
# never floored) and only raises, so it composes with the module invariant. It
# mirrors the gated blast floor already in the pipeline (`ULT_FLOORS`), which
# makes the same argument one factor over.
SENSITIVITY_FLOOR = {5: 50, 4: 25}

FORMULA = "max(existing score, sensitivity floor, max over C/I/A of S x B_f x I_f)"


@dataclass(frozen=True)
class CellRisk:
    """One cell's score, the objective that drove it, and the vector behind it."""

    score: int
    driver: str | None  # the objective that set the score; None if the base score won
    raised: bool  # did CIA lift this cell above its existing score?
    floored: bool  # did the asset's sensitivity floor set it?
    base_score: float  # the score CIA was applied on top of
    per_objective: dict[str, int]
    sensitivity: int
    coverage: dict[str, int]
    impact: dict[str, int]
    violated: tuple[str, ...]
    reason: str
    evidence: list[str] = field(default_factory=list)


def op_impact(atomic_ops) -> dict[str, int]:
    """Per-objective completeness for a tool: the max over its atomic operations."""
    if not atomic_ops:
        return dict(_UNKNOWN_OP_IMPACT)
    out: dict[str, int] = {}
    for op in atomic_ops:
        for facet, value in OP_IMPACT.get(str(op).upper(), _UNKNOWN_OP_IMPACT).items():
            out[facet] = max(out.get(facet, 0), value)
    return out


def score_cell(
    sensitivity: int,
    loss_axis: str,
    atomic_ops,
    blast: int | None,
    base_score: float,
    *,
    flags: tuple[str, ...] = (),
) -> CellRisk | None:
    """Score one (tool, asset) pair, or ``None`` when the pair is N/A.

    ``base_score`` is the cell's existing ``sens x blast x impact``. The result can
    only meet or exceed it — see the module invariant.
    """
    if blast is None:
        return None

    impacts = op_impact(atomic_ops)
    violated = tuple(f for f in FACETS if impacts.get(f, 0) > 0) or violated_facets(atomic_ops)
    coverage = max(1, min(5, int(blast)))
    escape = bool(set(flags) & _ESCAPE_FLAGS)
    returns_content = any(str(op).upper() in _CONTENT_RETURNING_OPS for op in (atomic_ops or []))

    evidence: list[str] = []
    per_coverage = dict.fromkeys(FACETS, coverage)
    if "self-sufficient" in flags and returns_content:
        per_coverage["C"] = 5
        evidence.append(
            f"B_C {coverage} -> 5 (asset is self-sufficient; one item disclosed is the "
            "entire confidentiality loss)"
        )

    ranks = parse_loss_axis(loss_axis)
    leading = {f for f in FACETS if ranks[f] == min(ranks.values())} if impacts else set()

    # THE ORGANIZATION'S JUDGEMENT IS NEVER ZEROED.
    #
    # An atomic op names a tool's PRIMARY verb, not everything the call touches.
    # `create-event` classifies as CREATE, so the chart alone gives it `I_C = 0` --
    # yet the calendar register says an event write reaches `contacts` precisely
    # through its attendee fields, and the org rates that asset on CONFIDENTIALITY.
    # Scoring the cell on integrity only would discard the org's stated reason for
    # the asset mattering at all, and would route the call to "confirm" when the
    # org's own policy says disclosure is the loss.
    #
    # So: on the objective(s) the organization puts at the top of this asset's loss
    # axis, impact falls back to the framework's existing tier rather than 0
    # whenever the tool acts on the asset at all. The chart REFINES the org's
    # judgement; it never overrides it.
    base_impact = round(base_score / (sensitivity * coverage)) if sensitivity and coverage else 0
    effective = dict(impacts)
    for facet in leading:
        if effective.get(facet, 0) < base_impact:
            effective[facet] = base_impact
            evidence.append(
                f"{facet}: the org ranks this asset's loss on {facet} first, so the tool's "
                f"existing impact tier {base_impact} applies rather than the chart's "
                f"{impacts.get(facet, 0)}"
            )

    per_objective = dict.fromkeys(FACETS, 0)
    for facet in FACETS:
        impact = effective.get(facet, 0)
        if impact:
            per_objective[facet] = sensitivity * per_coverage[facet] * impact
            evidence.append(
                f"{facet}: S={sensitivity} x B={per_coverage[facet]} x I={impact} "
                f"= {per_objective[facet]}"
            )

    # Ties are broken by the organization's stated loss axis, so a cell that is
    # equally an integrity and a confidentiality risk is reported as whichever the
    # org says it cares about -- which is what selects the control.
    driver = (
        max(FACETS, key=lambda f: (per_objective[f], -ranks[f]))
        if any(per_objective.values())
        else None
    )

    if driver and escape and per_coverage[driver] >= 4:
        raised_value = min(SCORE_MAX, round(per_objective[driver] * 1.25))
        if raised_value != per_objective[driver]:
            evidence.append(
                f"{driver}: {per_objective[driver]} -> {raised_value} (asset flagged "
                f"{'/'.join(sorted(set(flags) & _ESCAPE_FLAGS))}; consequences escape it)"
            )
            per_objective[driver] = raised_value

    cia_score = max(per_objective.values(), default=0)
    # The asset's own value sets a floor: a crown jewel is never a routine cell,
    # whatever the verb. Only applied where the tool acts on the asset at all.
    # ...but only when the call violates SOMETHING. A liveness check that touches no
    # objective is not "touching the crown jewel", and flooring it would price a
    # ping like a disclosure.
    floor = SENSITIVITY_FLOOR.get(sensitivity, 0) if cia_score > 0 else 0
    if floor and floor > max(round(base_score), cia_score):
        evidence.append(
            f"sensitivity floor: an asset at sensitivity {sensitivity} is never scored "
            f"below {floor}, whatever the operation"
        )
    # THE INVARIANT. CIA is evidence added to the existing judgement, so the cell
    # takes whichever is higher. A cell CIA has nothing to say about is untouched.
    score = int(max(round(base_score), cia_score, floor))
    raised = cia_score > round(base_score)
    floored = floor > max(round(base_score), cia_score)
    if not raised:
        evidence.append(f"existing score {round(base_score)} stands; CIA adds nothing here")
        driver = driver if cia_score == score else None

    reason = (
        f"{score} — driven by {driver}: S={sensitivity} x B={per_coverage[driver]} x "
        f"I_{driver}={effective.get(driver, 0)}"
        if raised and driver
        else f"{score} — the existing score stands"
    )
    return CellRisk(
        score=score,
        driver=driver,
        raised=raised,
        floored=floored,
        base_score=base_score,
        per_objective=per_objective,
        sensitivity=sensitivity,
        coverage=per_coverage,
        impact={f: effective.get(f, 0) for f in FACETS},
        violated=violated,
        reason=reason,
        evidence=evidence,
    )


# The control a score implies depends on WHICH objective drove it, because the
# objectives differ in whether the loss can be undone. This is what keeping the
# driver buys: a bare number can say how much, only a driver can say what to do.
CONTROL_BY_DRIVER = {
    "C": "deny — disclosure cannot be undone, so approval buys nothing",
    "I": "require human confirmation — recoverable only if a restore path exists",
    "A": "throttle — availability loss is usually transient",
    None: "existing control (CIA adds no reason here)",
}


def control_for(risk: CellRisk | None) -> str:
    """The control this cell implies, from its driving objective."""
    if risk is None or risk.driver is None:
        return CONTROL_BY_DRIVER[None]
    return CONTROL_BY_DRIVER[risk.driver]


__all__ = [
    "CONTROL_BY_DRIVER",
    "FORMULA",
    "SENSITIVITY_FLOOR",
    "OP_IMPACT",
    "SCORE_MAX",
    "CellRisk",
    "control_for",
    "op_impact",
    "score_cell",
]
