"""CIA as the interaction term between the asset axis and the tool axis.

The static formula ``sens x blast x impact`` is three MAIN EFFECTS: in log space
they simply add, so no factor can express "this action type is expensive *on this
particular asset*". Adding CIA as a fourth factor therefore changes the scale and
not the shape — which is what the v1 ``cia`` arm measured (impact = base + C + I
+ A, score_max 150: calendar's `high` band went 8 -> 25 and nothing re-ranked).

CIA is not a magnitude. It is two statements about *kind*:

* the **asset** side — which axis carries the loss, from the policy register's
  ``CIA`` cell (``I>A>C`` on an infra repo, ``C>I>A`` on an exec channel);
* the **tool** side — which axis one call actually violates, from the atomic-op
  classification already computed for every scan (``READ`` violates C; ``DELETE``
  violates I and A).

Used as a **selector** the two combine into the interaction the formula lacks:
an asset no longer has one sensitivity, it has one per facet, and a cell is
priced with the facet the tool actually violates.

    sens_eff(asset, tool) = max over facets the tool violates of sens_facet(asset)

The decay is anchored at the top — the leading axis keeps the asset's full
sensitivity and every axis below it is discounted — so this rule can **only lower
a cell, never raise one**. That is the design property that makes it a
discriminator rather than an inflator, and it is what the v1 arm got wrong.

Worked example (github, sensitivity 4 for both assets):

===================  ==========  ==============  ==============
asset                loss axis   READ  (C)       WRITE (I)
===================  ==========  ==============  ==============
``ml-research``      ``C>I>A``   4 (unchanged)   3 (discounted)
``infra-config``     ``I>A>C``   2 (discounted)  4 (unchanged)
===================  ==========  ==============  ==============

Today both rows read 4/4: reading the infrastructure repository is priced with
the same asset value as merging into it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FACETS = ("C", "I", "A")

# Which CIA objectives one atomic operation violates. Grounded in the repo's own
# vocabulary: the `CIA_FLAGS_TASK` prompt ("a pure read violates only C; a write
# violates I; a delete violates I and A") and the side-effect columns of
# docs/standards/mcp-primitive-operations.csv.
#
# BROADCAST carries C as well as I because the message leaves the system: it both
# discloses whatever it quotes and speaks in the organization's voice. EXECUTE is
# unbounded, so it violates all three.
OP_FACETS: dict[str, tuple[str, ...]] = {
    "PING": (),
    "LIST": ("C",),
    "METADATA": ("C",),
    "SEARCH": ("C",),
    "READ": ("C",),
    "COPY": ("C",),
    "CREATE": ("I",),
    "WRITE": ("I",),
    "MODIFY": ("I",),
    "MOVE": ("I",),
    "SCHEMA_MODIFY": ("I", "A"),
    "OVERWRITE": ("I", "A"),
    "DELETE": ("I", "A"),
    "BROADCAST": ("C", "I"),
    "EXECUTE": ("C", "I", "A"),
    "AUTHENTICATE": ("C", "I"),
    "CONFIGURE": ("I", "A"),
    "SUBSCRIBE": ("C",),
    "FETCH": ("C",),
}
# An unclassified operation must not silently become harmless: assume it can
# violate anything, which selects the asset's leading (highest) facet.
_UNKNOWN_OP_FACETS = FACETS


class LossAxisError(ValueError):
    """Raised when a register's CIA cell cannot be read as an ordering."""


@dataclass(frozen=True)
class FacetVerdict:
    """One cell's effective sensitivity and the reasoning that produced it."""

    sensitivity: int
    facet: str | None  # the facet that selected it; None when nothing is violated
    violated: tuple[str, ...]
    per_facet: dict[str, int]
    reason: str


def parse_loss_axis(cia: str) -> dict[str, int]:
    """Read a register ``CIA`` cell into ``{facet: rank}``, rank 0 = leads.

    Accepts the orderings the policy document actually uses — ``C>I>A``,
    ``I≈C>A`` (a tie), ``A>I>C``, ``none``/empty — and the profile document's
    ``C:H I:M A:L`` letter grades. Facets the cell omits rank last.
    """
    text = (cia or "").strip()
    if not text or text.lower() in {"none", "-", "—", "n/a"}:
        return dict.fromkeys(FACETS, 0)  # no stated axis: every facet leads

    grades = dict(re.findall(r"\b([CIA])\s*:\s*([HML])\b", text.upper()))
    if grades:  # profile-style "C:H I:M A:L"
        order = {"H": 0, "M": 1, "L": 2}
        return {facet: order.get(grades.get(facet, "L"), 2) for facet in FACETS}

    ranks: dict[str, int] = {}
    for rank, group in enumerate(re.split(r"[>»]", text.upper())):
        # A group must be CIA letters joined by tie/space separators and nothing
        # else. Without this, prose ("mostly integrity") would donate stray C/I/A
        # characters and parse into a confident, wrong ordering.
        if not re.fullmatch(r"[\sCIA≈~=,/·]*", group):
            raise LossAxisError(
                f"unreadable CIA cell {cia!r}: {group.strip()!r} is not an ordering of "
                "C/I/A — expected e.g. 'C>I>A', 'I≈C>A' or 'C:H I:M A:L'"
            )
        letters = [ch for ch in group if ch in FACETS]  # "I≈C" -> both at this rank
        for letter in letters:
            ranks.setdefault(letter, rank)
    if not ranks:
        raise LossAxisError(f"unreadable CIA cell {cia!r}: expected e.g. 'C>I>A' or 'C:H I:M A:L'")
    trailing = max(ranks.values()) + 1
    return {facet: ranks.get(facet, trailing) for facet in FACETS}


def facet_sensitivity(sensitivity: int, cia: str, *, floor: int = 1, step: int = 1) -> dict[str, int]:
    """Split one 1-5 sensitivity into a per-facet triple, anchored at the top.

    The leading axis keeps the asset's full sensitivity; each rank below it is
    discounted by ``step``, never below ``floor``. Anchoring at the top is what
    makes the rule incapable of raising a cell.
    """
    ranks = parse_loss_axis(cia)
    return {facet: max(floor, sensitivity - step * rank) for facet, rank in ranks.items()}


def violated_facets(atomic_ops) -> tuple[str, ...]:
    """The CIA objectives a tool's atomic operations can violate, de-duplicated."""
    if not atomic_ops:
        return _UNKNOWN_OP_FACETS
    seen: list[str] = []
    for op in atomic_ops:
        for facet in OP_FACETS.get(str(op).upper(), _UNKNOWN_OP_FACETS):
            if facet not in seen:
                seen.append(facet)
    return tuple(facet for facet in FACETS if facet in seen)


def effective_sensitivity(
    sensitivity: int, cia: str, atomic_ops, *, floor: int = 1, step: int = 1
) -> FacetVerdict:
    """The sensitivity that applies to ONE (tool, asset) pair.

    Selects the highest-valued facet among those the tool actually violates. A
    tool that violates nothing (a ping) selects the asset's lowest facet — it
    still reaches the asset, it just cannot damage any objective.
    """
    per_facet = facet_sensitivity(sensitivity, cia, floor=floor, step=step)
    violated = violated_facets(atomic_ops)
    if not violated:
        facet = min(per_facet, key=lambda f: per_facet[f])
        return FacetVerdict(
            sensitivity=per_facet[facet],
            facet=None,
            violated=(),
            per_facet=per_facet,
            reason="tool violates no CIA objective; priced at the asset's lowest facet",
        )
    facet = max(violated, key=lambda f: per_facet[f])
    return FacetVerdict(
        sensitivity=per_facet[facet],
        facet=facet,
        violated=violated,
        per_facet=per_facet,
        reason=(
            f"violates {'+'.join(violated)}; asset's loss axis {cia or 'unstated'} "
            f"prices {facet} at {per_facet[facet]} (of {sensitivity})"
        ),
    )


__all__ = [
    "FACETS",
    "OP_FACETS",
    "FacetVerdict",
    "LossAxisError",
    "effective_sensitivity",
    "facet_sensitivity",
    "parse_loss_axis",
    "violated_facets",
]
