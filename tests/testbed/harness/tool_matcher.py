"""Match MCP tools to attack templates using keyword-based rules."""

import json
from pathlib import Path
from typing import Any

from mcp.types import Tool


TEMPLATES_DIR = Path(__file__).parent.parent / "attack_templates"


def load_templates() -> list[dict[str, Any]]:
    """Load all attack templates from the attack_templates directory.

    Returns:
        List of parsed template dicts, sorted by filename.
    """
    templates = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        templates.append(json.loads(path.read_text()))
    return templates


def match(
    tools: list[Tool],
    templates: list[dict[str, Any]],
) -> list[tuple[Tool, dict[str, Any]]]:
    """Return (tool, template) pairs where the tool matches the template's match_rules.

    A tool matches a template if any keyword in ``match_rules.tool_name_contains``
    appears in the tool's name (case-insensitive).  The wildcard ``"*"`` matches
    every tool regardless of name.

    Args:
        tools: List of MCP :class:`~mcp.types.Tool` objects from ``tools/list``.
        templates: List of loaded attack template dicts.

    Returns:
        List of ``(tool, template)`` pairs to test.  A single tool may appear
        multiple times if it matches more than one template.
    """
    primary = [t for t in templates if not t.get("fallback_only")]
    fallback = [t for t in templates if t.get("fallback_only")]

    matches = []
    for tool in tools:
        tool_matches = []
        for template in primary:
            keywords = template.get("match_rules", {}).get("tool_name_contains", [])
            if "*" in keywords or any(kw.lower() in tool.name.lower() for kw in keywords):
                tool_matches.append((tool, template))
        if tool_matches:
            matches.extend(tool_matches)
        else:
            # No primary template matched — apply fallback templates
            for template in fallback:
                matches.append((tool, template))
    return matches


def describe_matches(matches: list[tuple[Tool, dict[str, Any]]]) -> str:
    """Return a human-readable summary of matched (tool, template) pairs.

    Args:
        matches: Output from :func:`match`.

    Returns:
        A multi-line string listing each match, or a short message when the
        list is empty.
    """
    if not matches:
        return "No tool-template matches found."
    lines = [f"Found {len(matches)} matches:"]
    for tool, template in matches:
        lines.append(f"  {tool.name!r} \u2192 {template['id']} ({template['category']})")
    return "\n".join(lines)
