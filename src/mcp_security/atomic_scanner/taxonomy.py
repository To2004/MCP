"""The extended atomic-operation taxonomy (v2).

The 13 base rows are carried over **verbatim** from
``presentations/heatmap_byhand/csv/atomic_operations.csv`` — same rank, same
severity, same reasoning. Nothing was removed or renumbered; that file and the
``mcp_security.atomic_ops`` package it feeds are untouched.

Nine rows were added (``origin=added``) for operations the base set has no name
for, drawn from where each idea already exists:

* ``TRANSACT`` — money movement is its own kind of irreversible; the base set
  covers destruction and disclosure but not settlement.
* ``PUBLISH`` — deploy/release/merge. The base ``BROADCAST`` is about sending
  *data* to people; publishing makes *state* live.
* ``ACCESS_CHANGE`` / ``MEMBERSHIP`` — the authorization axis. Both are
  recoverable in both directions, which is exactly why neither is ``DELETE``
  (removing a member is not destroying them).
* ``CONFIGURE`` — settings that govern later behaviour, not the data itself.
* ``INTERACT`` — browser/UI automation, where the effect lands in a system that
  is not ours (the puppeteer family).
* ``BUILD`` — train/compile/generate a persistent artifact.
* ``STATE_TOGGLE`` — mark-read/star/pin: a write that changes no content, which
  the base set would have to call ``MODIFY`` (severity 3) or ``METADATA``
  (a read).
* ``NO_EFFECT`` — liveness/echo/clock. The base set starts at ``LIST``, so a
  ping had nowhere to go.

The new ``ladder_tier`` column maps each op onto the 1-5 tool-impact ladder the
rest of the framework uses, so the two scales stay explicit rather than being
silently equated: severity ranks *attacker value*, the ladder ranks *what one
call does*. They are close but not identical — ``OVERWRITE`` is severity 4 and
ladder 5, because a full overwrite has no in-system undo.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

TAXONOMY_CSV = Path(__file__).resolve().parent / "data" / "atomic_operations_v2.csv"


@dataclass(frozen=True)
class AtomicOpSpec:
    """One row of the extended taxonomy."""

    rank: int
    name: str
    severity: int
    severity_label: str
    ladder_tier: int
    origin: str
    reasoning: str


@lru_cache(maxsize=None)
def load_taxonomy(csv_path: Path | None = None) -> dict[str, AtomicOpSpec]:
    """Op name -> spec, read from the v2 csv."""
    path = Path(csv_path or TAXONOMY_CSV)
    if not path.exists():
        raise FileNotFoundError(f"atomic taxonomy csv not found: {path}")
    ops: dict[str, AtomicOpSpec] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if not row.get("rank"):
                continue
            name = row["atomic_op"].strip().upper()
            ops[name] = AtomicOpSpec(
                rank=int(row["rank"]),
                name=name,
                severity=int(row["severity"]),
                severity_label=row["severity_label"].strip(),
                ladder_tier=int(row["ladder_tier"]),
                origin=row["origin"].strip(),
                reasoning=row["reasoning"].strip(),
            )
    if not ops:
        raise ValueError(f"no rows in {path}")
    return ops


def ladder_tier(op: str) -> int:
    """The 1-5 impact tier one atomic operation implies."""
    return load_taxonomy()[op.upper()].ladder_tier


def severity(op: str) -> int:
    """The taxonomy's own 0-5 severity rank for one atomic operation."""
    return load_taxonomy()[op.upper()].severity


def op_names() -> frozenset[str]:
    """Every operation name the taxonomy defines."""
    return frozenset(load_taxonomy())
