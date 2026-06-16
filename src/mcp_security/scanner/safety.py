"""Read-only safety gate for live tool invocation during enumeration.

The scanner only ever *enumerates* an asset store — it must never mutate it.
Before calling any tool on a live server, we classify the tool with the existing
``atomic_ops.toollist_rules`` engine and refuse anything whose atomic operations
fall outside the read-only set. This is the single chokepoint every enumerator
routes through.
"""

from __future__ import annotations

from mcp_security.atomic_ops.toollist_rules import classify_from_toollist

# LIST / SEARCH / METADATA are the severity<=2 enumeration ops. READ is excluded
# on purpose: we list and stat assets, we do not read their contents.
READ_ONLY_OPS: frozenset[str] = frozenset({"LIST", "SEARCH", "METADATA"})


def is_read_only(tool_name: str, description: str = "", input_schema: dict | None = None) -> bool:
    """True only if every atomic op the tool maps to is read-only.

    A tool with no recognised atomic op is treated as **not** read-only — we
    fail closed rather than risk invoking something unclassified.
    """
    hits = classify_from_toollist(tool_name, description, input_schema or {})
    ops = {hit.atomic_op for hit in hits}
    if not ops:
        return False
    return ops <= READ_ONLY_OPS
