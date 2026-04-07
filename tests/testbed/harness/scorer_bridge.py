"""Bridge to the src/mcp_security/ scorer. Returns stubs until scorer is built."""

from __future__ import annotations

from typing import Any


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
    # TODO: replace with real scorer once src/mcp_security/scorer.py is built
    return {
        "static": None,
        "dynamic": None,
        "combined": None,
        "note": "scorer not yet built",
    }
