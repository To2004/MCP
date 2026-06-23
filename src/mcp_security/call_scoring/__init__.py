"""Score observed MCP tool calls against the design-time static risk tables.

The static-scoring pipeline (:mod:`mcp_security.static_scoring`) produces, per
server kind, a table of ``(tool, asset) -> risk`` cells. This package consumes
those tables and applies them to *real captured calls* — the normal/benign and
misconfiguration traffic recorded under ``logs/proxy/`` — so every call gets a
risk score and band by lookup, with no LLM at scoring time.

The point is defensive: ranking normal traffic surfaces the inherently risky
(and misconfigured) calls that a server should gate, even when nothing malicious
is happening.
"""

from .loader import Call, load_calls
from .resolve import ResolvedAsset, resolve_asset
from .score import ScoredCall, score_call
from .tables import StaticTable, load_tables

__all__ = [
    "Call",
    "load_calls",
    "ResolvedAsset",
    "resolve_asset",
    "ScoredCall",
    "score_call",
    "StaticTable",
    "load_tables",
]
