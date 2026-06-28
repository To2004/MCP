"""Static, pre-runtime MCP scanner.

The scanner understands a server's tools and assets **before** the server runs —
it never connects to a live MCP. Tools come from the server's own saved
``tools/list`` (``reports/tool_lists/<kind>.json``, captured once per MCP); assets
come from the on-disk store the server fronts. The LLM understanding stage then
derives every risk primitive in strict (LLM-only) mode, so nothing is hardcoded and
no design-time table is read. The output is a scan artifact the call ranker scores
observed calls against.
"""

from .render import scan_to_markdown
from .scan import ScanResult, build_registry, scan_server, write_scan
from .tool_list import load_tool_list

__all__ = [
    "ScanResult",
    "build_registry",
    "scan_server",
    "write_scan",
    "scan_to_markdown",
    "load_tool_list",
]
