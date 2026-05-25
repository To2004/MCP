"""Shared rule data types and atomic-op identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    """How strongly a rule asserts the atomic-op tag."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


ATOMIC_OPS: frozenset[str] = frozenset(
    {
        "EXECUTE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "BROADCAST",
        "WRITE",
        "MODIFY",
        "MOVE",
        "CREATE",
        "READ",
        "SEARCH",
        "METADATA",
        "LIST",
    }
)


@dataclass(frozen=True)
class RuleHit:
    """Result of one rule matching against a tool."""

    rule_id: str
    atomic_op: str
    confidence: Confidence
    matched_on: str
