"""Rank observed MCP tool calls against the scanner's risk matrices.

The static scanner (:mod:`mcp_security.scanner`) derives, per server, a matrix of
``(tool, asset) -> risk`` cells from the scanned tools and assets — before the
server runs and with no hardcoded table. This package consumes those *scan
artifacts* (``reports/scan/``) and applies them to *real captured calls* — the
normal/benign and misconfiguration traffic recorded under ``logs/proxy/`` — so
every call gets a risk score and band by lookup, with no LLM at scoring time.

The point is defensive: ranking normal traffic surfaces the inherently risky
(and misconfigured) calls a server should gate, even when nothing malicious is
happening. The committed design-time tables under ``reports/evaluation`` are used
only to grade the scanner, never to score calls.
"""

from .loader import Call, load_calls
from .resolve import ResolvedAsset, resolve_asset
from .score import ScoredCall, score_call
from .tables import StaticTable, load_scan, load_scans

__all__ = [
    "Call",
    "load_calls",
    "ResolvedAsset",
    "resolve_asset",
    "ScoredCall",
    "score_call",
    "StaticTable",
    "load_scan",
    "load_scans",
]
