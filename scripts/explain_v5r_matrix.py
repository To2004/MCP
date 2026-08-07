"""Explain a v5r scan cell by cell: what each asset is, what each tool does, why each score.

Generates ``<stem>_EXPLAINED.md`` per server from the artifact plus the policy
register. Four sections:

1. **Assets** — the register description beside **an independent reading** of
   what the asset is and what depends on it, plus the derived sensitivity.
2. **Tools** — the impact tier beside **an independently expected tier**, so a
   divergence is visible, plus who decided it and why.
3. **Where the floor moved a cell** — every cell whose blast the deterministic
   floor raised, with the model's own number beside it. This is where blast stops
   being the model's judgement.
4. **Row inconsistencies** — the same asset scored by comparable tools that
   disagree by more than one blast tier, and any read that reaches further than a
   write on the same asset. These are the cells worth arguing about.

Run:  uv run python scripts/explain_v5r_matrix.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r"

# Tools that read the same substance of an asset should not differ wildly in
# reach. Grouped by what they operate on, not by name.
READ_FAMILIES = {
    "channel message content": (
        "conversations_history",
        "conversations_replies",
        "conversations_search_messages",
    ),
    "event content": ("get-event", "list-events", "search-events"),
    "repository file content": ("get_file_contents", "search_code"),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _annotations():
    """The assistant's independent readings, or empty dicts if absent."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from v5r_annotations import ASSET_READING, EXPECTED_IMPACT, TOOL_READING
    except ImportError:  # the report still renders without them
        return {}, {}, {}
    return ASSET_READING, TOOL_READING, EXPECTED_IMPACT


def asset_section(table: dict, register: dict[str, dict], readings: dict[str, str]) -> list[str]:
    sens = table.get("asset_sensitivity", {})
    flags = table.get("asset_flags", {})
    blast = table["blast_radius"]
    out = [
        "## Assets — the register, and a second reading of it",
        "",
        "`Sens.` is **derived** by the model from the organization's policy classes;",
        "the policy states no numbers. `Flags` come from the register and are what a",
        "tier-5 blast must cite.",
        "",
        "**What the register says** is the organization's own one-line description —",
        "the exact text the sensitivity stage classified. **A second reading** is the",
        "assistant's independent account of the same asset, written to answer the",
        "question blast radius needs and an id never tells you: *what depends on this?*",
        "Where the two diverge, the register is what scored; the second reading is what",
        "a reviewer might argue for.",
        "",
    ]
    for asset in sorted(table["asset_ids"], key=lambda a: (-sens.get(a, 0), a)):
        row = register.get(asset, {})
        reached = sorted(
            tool for tool in table["tool_impact"] if blast.get(f"{tool}|{asset}") is not None
        )
        flag_text = ", ".join(f"`{f}`" for f in flags.get(asset, [])) or "—"
        out += [
            f"### `{asset}` — derived sensitivity **{sens.get(asset, '—')}**, flags {flag_text}",
            "",
            f"- **What the register says:** {row.get('description', '—')}",
            f"- **A second reading:** {readings.get(asset) or '*not annotated*'}",
            f"- **Loss axis (register):** {row.get('cia') or '—'}",
            "- **Tools that reach it:** "
            + (", ".join(f"`{t}`" for t in reached) if reached else "*none — whole row N/A*"),
            "",
        ]
    return out


def tool_section(table: dict, readings: dict[str, str], expected: dict[str, int]) -> list[str]:
    sources = table.get("tool_impact_source", {})
    statics = table.get("static_impacts", {})
    impacts = table["tool_impact"]
    disagree = [t for t in impacts if t in expected and expected[t] != impacts[t]]
    out = [
        "## Tools — the scan's tier, and an independently expected one",
        "",
        "`Scan` is what this run scored. `Expected` is the assistant's own tier for the",
        "same tool, assigned from its description and parameters — so **Δ** is a",
        "disagreement between two readings of the same declaration, not a bug report.",
        "",
        "`By` is **rules** where the deterministic ladder had evidence and **model**",
        "where it abstained; on an abstention `Def.` is the tier the rules would have",
        "defaulted to.",
        "",
        f"**{len(disagree)} of {len(impacts)} tools disagree.**",
        "",
        "| Tool | Scan | Exp. | Δ | By | Def. | What one call does, and who is different afterwards |",
        "|---|--:|--:|:-:|---|--:|---|",
    ]
    for tool, impact in sorted(impacts.items()):
        record = statics.get(tool, {})
        by = "model" if sources.get(tool) == "llm_fallback" else "rules"
        default = record.get("static_would_have_said", "")
        mine = expected.get(tool)
        delta = "—" if mine is None or mine == impact else f"**{mine - impact:+d}**"
        reading = (readings.get(tool) or "*not annotated*").replace("|", "\\|")
        out.append(
            f"| `{tool}` | {impact} | {mine if mine is not None else '—'} | {delta} | "
            f"{by} | {default} | {reading} |"
        )
    out += ["", "### Why the scan said what it did, where the two disagree", ""]
    if not disagree:
        out.append("*The two readings agree on every tool.*")
    for tool in sorted(disagree):
        record = statics.get(tool, {})
        by = "the model" if sources.get(tool) == "llm_fallback" else "the rules"
        why = record.get("llm_reasoning") if by == "the model" else "; ".join(record.get("evidence", []))
        why = (why or "—").replace("\n", " ")
        out.append(
            f"- **`{tool}`** — scan {impacts[tool]}, expected {expected[tool]}. "
            f"{by.capitalize()} said: {why}"
        )
    return [*out, ""]


def floor_section(table: dict) -> list[str]:
    sens = table.get("asset_sensitivity", {})
    impacts = table["tool_impact"]
    raw, final = table.get("blast_radius_raw", {}), table["blast_radius"]
    moved = [
        (key, raw[key], final[key])
        for key in final
        if raw.get(key) is not None and final.get(key) is not None and final[key] > raw[key]
    ]
    out = [
        "## Where the deterministic floor moved a cell",
        "",
        f"{len(moved)} of {sum(1 for v in final.values() if v is not None)} scored cells.",
        "In each of these the score you see is **not** the model's reach judgement —",
        "the floor overrode it because of the asset's sensitivity or the tool's impact.",
        "",
    ]
    if not moved:
        return [*out, "*No cell was raised.*", ""]
    out += ["| Cell | Model said | Raised to | Sens. | Impact | Which rule |", "|---|--:|--:|--:|--:|---|"]
    for key, before, after in sorted(moved, key=lambda m: -(m[2] - m[1])):
        tool, asset = key.split("|", 1)
        s, i = sens.get(asset, 0), impacts[tool]
        rule = f"sens {s} → blast ≥ {after}" if s >= 4 and after > before else f"impact {i} → blast ≥ 3"
        out.append(f"| `{tool}` × `{asset}` | {before} | {after} | {s} | {i} | {rule} |")
    return [*out, ""]


def consistency_section(table: dict) -> list[str]:
    blast = table["blast_radius"]
    impacts = table["tool_impact"]
    escapes = table.get("blast_escape", {})
    out = [
        "## Cells worth arguing about",
        "",
        "Two checks the rubric cannot enforce itself, because every cell is scored in",
        "its own model call.",
        "",
        "### Comparable tools disagreeing on the same asset",
        "",
        "Tools that read the same substance should not differ by more than one tier.",
        "",
    ]
    found = False
    for family, tools in READ_FAMILIES.items():
        present = [t for t in tools if t in impacts]
        if len(present) < 2:
            continue
        for asset in table["asset_ids"]:
            values = {t: blast.get(f"{t}|{asset}") for t in present}
            scored = {t: v for t, v in values.items() if v is not None}
            if len(scored) < 2 or max(scored.values()) - min(scored.values()) < 2:
                continue
            found = True
            detail = ", ".join(
                f"`{t}`={v}" + (f" (escape {escapes.get(f'{t}|{asset}')})" if escapes.get(f"{t}|{asset}", "none") != "none" else "")
                for t, v in scored.items()
            )
            out.append(f"- **{family}** on `{asset}`: {detail}")
    if not found:
        out.append("*No family disagrees by more than one tier.*")
    out += [
        "",
        "### A lower-impact call reaching further than a higher-impact one",
        "",
        "Impact and blast are independent by design, so this is not automatically",
        "wrong — but on the same asset it usually means one of the two cells is.",
        "Note tier 3 holds content reads *and* limited writes, so a 'lower-impact'",
        "call here may still be a write.",
        "",
    ]
    pairs = []
    for asset in table["asset_ids"]:
        reads = {
            t: blast[f"{t}|{asset}"]
            for t in impacts
            if impacts[t] <= 3 and blast.get(f"{t}|{asset}") is not None
        }
        writes = {
            t: blast[f"{t}|{asset}"]
            for t in impacts
            if impacts[t] >= 4 and blast.get(f"{t}|{asset}") is not None
        }
        if not reads or not writes:
            continue
        top_read, top_read_v = max(reads.items(), key=lambda kv: kv[1])
        low_write, low_write_v = min(writes.items(), key=lambda kv: kv[1])
        if top_read_v > low_write_v:
            pairs.append((asset, top_read, top_read_v, low_write, low_write_v))
    if pairs:
        out += [
            "| Asset | impact ≤3 call | blast | impact ≥4 call | blast |",
            "|---|---|--:|---|--:|",
        ]
        out += [f"| `{a}` | `{r}` | {rv} | `{w}` | {wv} |" for a, r, rv, w, wv in pairs]
    else:
        out.append("*No asset where a read out-reaches a write.*")
    return [*out, ""]


def render(stem: str, table: dict, register: dict[str, dict]) -> str:
    readings, tool_readings, expected = _annotations()
    sens = table.get("asset_sensitivity", {})
    header = [
        f"# `{stem}` — every asset, every tool, every score explained",
        "",
        f"**{table['server']}** · {len(table['tool_impact'])} tools × "
        f"{len(table['asset_ids'])} assets · "
        f"{sum(1 for v in table['blast_radius'].values() if v is not None)} scored cells, "
        f"{sum(1 for v in table['blast_radius'].values() if v is None)} N/A",
        "",
        f"`score = sensitivity × blast × impact`, max {table['score_max']}. "
        f"Sensitivity source: `{table['sensitivity_source']}`. "
        f"Peak derived sensitivity: {max(sens.values()) if sens else '—'}.",
        "",
        "Generated by `scripts/explain_v5r_matrix.py` — do not hand-edit.",
        "",
    ]
    return "\n".join(
        header
        + asset_section(table, register, readings)
        + tool_section(table, tool_readings, expected)
        + floor_section(table)
        + consistency_section(table)
    )


def main(argv: list[str] | None = None) -> int:
    import sys

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from mcp_security.static_scoring.server_policies import parse_asset_register, policy_for

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args(argv)

    paths = sorted(p for p in args.dir.glob("*.json") if p.stem != "evaluation")
    if not paths:
        print(f"[FAIL] no artifacts in {args.dir}")
        return 1
    for path in paths:
        table = load(path)
        if "blast_radius" not in table:
            continue
        rows = parse_asset_register(policy_for(table["server"]).text)
        register = {r.asset_id: {"description": r.description, "cia": r.cia} for r in rows}
        out = args.dir / f"{path.stem}_EXPLAINED.md"
        out.write_text(render(path.stem, table, register), encoding="utf-8")
        rel = out.resolve().relative_to(REPO_ROOT)
        print(f"[ok] {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
