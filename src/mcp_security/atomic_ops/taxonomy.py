"""Load the atomic-op taxonomy from atomic_operations.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AtomicOp:
    """One row of the atomic-op taxonomy."""

    rank: int
    name: str
    severity: int
    severity_label: str
    reasoning: str


def load_taxonomy(csv_path: Path) -> list[AtomicOp]:
    """Read atomic_operations.csv and return its rows as AtomicOp objects, ranked.

    The csv has columns: rank, atomic_op, severity, severity_label, reasoning.
    Rows are returned sorted by rank ascending.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Taxonomy csv not found: {csv_path}")

    ops: list[AtomicOp] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row.get("rank"):
                continue
            ops.append(
                AtomicOp(
                    rank=int(row["rank"]),
                    name=row["atomic_op"].strip().upper(),
                    severity=int(row["severity"]),
                    severity_label=row["severity_label"].strip(),
                    reasoning=row["reasoning"].strip(),
                )
            )
    ops.sort(key=lambda op: op.rank)
    return ops
