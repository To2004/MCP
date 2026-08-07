"""Atomic-operation tool scanner (v2) — a third, independent impact method.

Parses each MCP tool into the SET of atomic operations it performs, then derives
its 1-5 impact tier as the maximum over that set. Runs alongside, and shares no
pattern table with, `static_scoring.static_impact` (prose tier patterns) and the
LLM impact stage.

The base 13-operation taxonomy and the `mcp_security.atomic_ops` package that
consumes it are left untouched; this package extends the taxonomy in its own csv.
"""

from .scanner import AtomicVerdict, classify, classify_all
from .taxonomy import AtomicOpSpec, ladder_tier, load_taxonomy, op_names, severity

__all__ = [
    "AtomicOpSpec",
    "AtomicVerdict",
    "classify",
    "classify_all",
    "ladder_tier",
    "load_taxonomy",
    "op_names",
    "severity",
]
