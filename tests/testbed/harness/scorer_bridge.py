"""Bridge to the src/mcp_security/ scorer for the live attack testbed.

Returns no score at present. The bridge previously wired the Gen-1 dynamic LLM
judge stage, which was archived with the rest of that package
(``_archive/2026-08-13/gen1_dynamic/``) when the runtime layer was rebuilt around
the multiplicative design in ``docs/project/dynamic-layer-formula.md``. Rather
than fabricate a number, every field stays ``None`` until the Gen-2 scorer is
wired here -- the same rule ``call_scoring`` already follows (a call is only
scored against real evidence).

``static`` additionally needs a scan artifact (``reports/scan/<server>.json``)
for the specific live server profile under attack, and no profile-to-scan
mapping exists yet.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

_NOT_WIRED = (
    "no scorer wired: the Gen-1 dynamic judge was archived, and the Gen-2 "
    "runtime layer is not yet importable from src/; static also needs a scan "
    "artifact for this server profile"
)


def score(
    tool_name: str,
    arguments: dict[str, Any],
    description: str,
    response_text: str,
) -> dict[str, Any]:
    """Score a tool invocation request.

    Args:
        tool_name: The MCP tool that was called.
        arguments: The arguments passed to the tool.
        description: The tool's description from tools/list.
        response_text: The raw text content of the tool's response.

    Returns:
        Dict with keys: static (float|None), dynamic (float|None),
        combined (float|None), note (str).
    """
    return {"static": None, "dynamic": None, "combined": None, "note": _NOT_WIRED}
