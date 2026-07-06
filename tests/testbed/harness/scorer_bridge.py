"""Bridge to the src/mcp_security/ scorer for the live attack testbed.

Wires the framework's real dynamic judge stage
(:mod:`mcp_security.dynamic.judge`) as the ``dynamic`` score: it needs only the
tool name and its arguments, which every call site here already has.
``static`` needs a scan artifact (``reports/scan/<server>.json``) for the
specific live server profile under attack, and no profile-to-scan mapping
exists yet, so it stays ``None`` rather than fabricate a number -- the same
rule ``call_scoring`` already follows (a call is only scored against real
evidence). ``combined`` needs both, so it stays ``None`` too until that mapping
exists.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from mcp_security.dynamic.judge import judge_call  # noqa: E402


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
    judged = judge_call(tool_name, arguments)
    if judged is None:
        return {
            "static": None,
            "dynamic": None,
            "combined": None,
            "note": (
                "dynamic judge returned no verdict (Ollama unreachable, or the "
                "response was not a usable band); static needs a scan artifact "
                "for this server profile, not yet wired"
            ),
        }
    band, reason = judged
    return {
        "static": None,
        "dynamic": band,
        "combined": None,
        "note": f"dynamic only ({reason}); static needs a scan artifact for this server profile",
    }
