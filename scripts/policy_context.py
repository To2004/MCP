"""Policy rows for one tool, read from the abstract-template policies.

The v12 labelling prompt receives, per tool, only the slice of the organization's
policy that applies to it: the org context, the normal workflow, the register
assets the tool can reach, the special-value rules (Table 3) and the baseline
rows (Table 4) that name it. Source: ``docs/mcp-tools/server-policies-abstract.md``;
a section whose register lives in ``docs/standards/policy.md`` (the calendar
worked example) is read from there.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POLICIES_PATH = REPO / "docs" / "mcp-tools" / "server-policies-abstract.md"
TEMPLATE_PATH = REPO / "docs" / "standards" / "policy.md"

#: Catalog name (``mcp_catalogs.CATALOGS``) -> policy section heading.
POLICY_SECTIONS = {
    "github": "github_helios",
    "slack": "slack_vireo",
    "calendar": "calendar_aurora",
    "filesystem": "fs_corp_filesystem",
}

#: The v5 scan that scored every register asset 1-5. The abstract policy carries
#: no numbers by design; the levels a ``register`` rule returns come from here.
SCAN_DIR = REPO / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"

#: Catalogs with a policy file of their own (a static-scan policy, whose ``## Input policy``
#: section has the abstract-template shape) and their own scan's levels. The section name
#: is still listed in POLICY_SECTIONS, so the catalog counts as having a policy.
_GATEWAY = REPO / "reports" / "experiments" / "gateway"
OWN_POLICY = {
    "github_remote": (
        _GATEWAY / "github_remote" / "github_helios_remote.md",
        _GATEWAY / "github_remote" / "github_remote.cells.json",
    ),
}
POLICY_SECTIONS["github_remote"] = "Input policy"


def scanned_levels(server: str) -> dict[str, int]:
    """Asset id -> the 1-5 sensitivity the v5 scan gave it, for ``server``'s org."""
    path = (OWN_POLICY[server][1] if server in OWN_POLICY
            else SCAN_DIR / f"{POLICY_SECTIONS[server]}.json")
    scan = json.loads(path.read_text())
    return {asset: int(level) for asset, level in scan["asset_sensitivity"].items()}


def with_scanned_levels(policy: dict, server: str) -> dict:
    """``policy`` with each reachable asset's ``scanned_level`` added (stage 2 input)."""
    levels = scanned_levels(server)
    assets = [{**a, "scanned_level": levels.get(a["asset"])}
              for a in policy.get("assets_this_tool_can_reach", [])]
    return {**policy, "assets_this_tool_can_reach": assets}


def org_for_tool(server: str, tool_name: str) -> dict:
    """What v13 sends about the organization: everything its policy says that
    applies to this tool.

    That is its description, its normal workflow, the assets the tool can reach
    with their scanned level, the special-value rules and baseline rows that
    name the tool, and the rest of the asset register by name and level (an
    input that names an asset can name any of them). The model turns what the
    policy says into levels; numbers and cut-offs the policy does not give are
    its own. Empty for a server with no policy."""
    if server not in POLICY_SECTIONS:
        return {}
    policy = with_scanned_levels(policy_for_tool(server, tool_name), server)
    reached = {a["asset"] for a in policy["assets_this_tool_can_reach"]}
    others = [{"asset": asset, "scanned_level": level}
              for asset, level in sorted(scanned_levels(server).items()) if asset not in reached]
    return {**{key: policy[key] for key in (
        "org_context", "normal_workflow", "assets_this_tool_can_reach",
        "special_value_rules", "baseline")}, "other_assets_of_the_organization": others}


def register_assets(server: str) -> dict[str, int]:
    """Every asset of ``server``'s register with its scanned level; empty with no policy.

    The table a v13 ``register`` rule looks names up in, whatever the tool."""
    return scanned_levels(server) if server in POLICY_SECTIONS else {}


_TOOL_PATTERN = re.compile(r"`([^`]+)`")


def _section(text: str, heading: str) -> str:
    """Text of the ``## heading`` section, up to the next ``## `` heading."""
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if not match:
        raise ValueError(f"no '## {heading}' section")
    rest = text[match.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _code_block_after(text: str, heading_prefix: str) -> str:
    """First fenced block after a ``### <heading_prefix>`` heading, dedented."""
    match = re.search(rf"^### {re.escape(heading_prefix)}.*$", text, re.M)
    if not match:
        return ""
    block = re.search(r"```\n(.*?)```", text[match.end():], re.S)
    if not block:
        return ""
    return "\n".join(" ".join(line.split()) for line in block.group(1).splitlines()).strip()


def _table_after(text: str, heading_prefix: str) -> list[list[str]]:
    """Body rows of the first table after a ``### <heading_prefix>`` heading."""
    match = re.search(rf"^### {re.escape(heading_prefix)}.*$", text, re.M)
    if not match:
        return []
    rows: list[list[str]] = []
    started = False
    for line in text[match.end():].splitlines():
        if line.startswith("|"):
            started = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            rows.append(cells)
        elif started:
            break
        elif line.startswith("### "):
            break
    return rows[1:]  # drop the header row


def _tools_in(cell: str) -> set[str]:
    return set(_TOOL_PATTERN.findall(cell))


def policy_for_tool(server: str, tool_name: str) -> dict:
    """The slice of ``server``'s policy that applies to ``tool_name``.

    Raises ``KeyError`` for a server with no abstract-template policy, so a
    caller cannot silently run with an empty policy by mistake.
    """
    heading = POLICY_SECTIONS[server]
    source = OWN_POLICY[server][0] if server in OWN_POLICY else POLICIES_PATH
    section = _section(source.read_text(encoding="utf-8"), heading)

    register = _table_after(section, "Table 2")
    if not register:  # register is pointed to, not copied (calendar)
        worked = _section(TEMPLATE_PATH.read_text(encoding="utf-8"),
                          "Worked example — `calendar_aurora` (Google Calendar, Aurora Airways)")
        register = _table_after(worked, "Table 2")

    return {
        "org_context": _code_block_after(section, "Block 0"),
        "normal_workflow": _code_block_after(section, "Block 4"),
        "assets_this_tool_can_reach": [
            {"asset": row[0].strip("`"), "description": row[1]}
            for row in register if len(row) >= 3 and tool_name in _tools_in(row[2])
        ],
        "special_value_rules": [
            {"arguments": row[1], "rule": row[2], "gates_asset": row[3]}
            for row in _table_after(section, "Table 3")
            if len(row) >= 4 and tool_name in _tools_in(row[0])
        ],
        "baseline": [
            {"arguments": row[1], "normal": row[2], "unusual": row[3], "basis": row[4]}
            for row in _table_after(section, "Table 4")
            if len(row) >= 5 and tool_name in _tools_in(row[0])
        ],
    }
