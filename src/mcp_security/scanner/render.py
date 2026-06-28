"""Render a scan artifact (or static table) as human-readable markdown."""

from __future__ import annotations

_BAND_MARK = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


def _matrix(table: dict) -> list[str]:
    cells = table.get("cells", {})
    bands = table.get("bands", {})
    if not cells:
        return ["_No cells._"]
    tools = list(next(iter(cells.values())).keys())
    lines = [
        "| asset \\ tool | " + " | ".join(tools) + " |",
        "|" + " --- |" * (len(tools) + 1),
    ]
    for asset, row in cells.items():
        brow = bands.get(asset, {})
        rendered = [f"{row[t]:g} {_BAND_MARK.get(brow.get(t, ''), '')}".strip() for t in tools]
        lines.append(f"| `{asset}` | " + " | ".join(rendered) + " |")
    return lines


def scan_to_markdown(server: str, kind: str, table: dict) -> str:
    """A self-contained markdown view of one scan's risk matrix and primitives."""
    profile = table.get("inferred_profile", {})
    dist = table.get("band_distribution", {})
    lines = [
        f"# Scan — {server}",
        "",
        f"_kind={kind} · provenance={table.get('provenance', 'live-scan')} · "
        f"model_reviewed={table.get('model_reviewed', '')} · bands={dist}_",
        "",
        "Risk derived live by the LLM from the scanned tools and assets — no "
        "checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.",
        "",
        "## Inferred domain profile",
        "",
    ]
    for key in ("mcp_kind", "asset_meaning", "blast_radius_meaning", "worked_example"):
        if profile.get(key):
            lines.append(f"- **{key}**: {profile[key]}")
    lines += ["", "## Tool impact", "", "| tool | impact |", "| --- | --- |"]
    lines += [f"| `{t}` | {v} |" for t, v in table.get("tool_impact", {}).items()]
    lines += ["", "## Asset sensitivity", "", "| asset | sensitivity |", "| --- | --- |"]
    lines += [f"| `{a}` | {v} |" for a, v in table.get("asset_sensitivity", {}).items()]
    lines += ["", "## Risk matrix (score · band)", ""]
    lines += _matrix(table)
    lines.append("")
    return "\n".join(lines)
