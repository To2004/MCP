"""Export the design-time static risk tables as evaluation-only markdown.

The static tables in ``reports/samples/all_static_tables*.json`` were the project's
hand-reviewed "anchoring" tables. They are **ground truth for grading the scanner,
never an input to it** — the scanner derives its own scores live from the scanned
tools/assets. This script renders each table as human-readable markdown under
``reports/evaluation/`` and copies the source JSON beside it as the raw reference.

Run::

    python scripts/export_eval_tables.py            # all_static_tables.json (take1)
    python scripts/export_eval_tables.py --take2     # all_static_tables_take2.json
    python scripts/export_eval_tables.py --src path/to/tables.json --out reports/evaluation
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "reports" / "evaluation"
SAMPLES = REPO_ROOT / "reports" / "samples"

_BAND_MARK = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


def _fmt_cell(score: float, band: str) -> str:
    """One matrix cell: score plus a band marker, e.g. ``3.0 🟢``."""
    mark = _BAND_MARK.get(band, "")
    return f"{score:g} {mark}".strip()


def _matrix_md(table: dict) -> list[str]:
    """Render the (asset × tool) cells+bands matrix as a markdown table."""
    cells = table.get("cells", {})
    bands = table.get("bands", {})
    if not cells:
        return ["_No cells._"]
    tools = list(next(iter(cells.values())).keys())
    header = "| asset \\ tool | " + " | ".join(tools) + " |"
    sep = "|" + " --- |" * (len(tools) + 1)
    lines = [header, sep]
    for asset, row in cells.items():
        brow = bands.get(asset, {})
        rendered = [_fmt_cell(row[t], brow.get(t, "")) for t in tools]
        lines.append(f"| `{asset}` | " + " | ".join(rendered) + " |")
    return lines


def _kv_table(title: str, mapping: dict, key_h: str, val_h: str) -> list[str]:
    """Render a flat {key: value} mapping as a two-column markdown table."""
    lines = [f"### {title}", "", f"| {key_h} | {val_h} |", "| --- | --- |"]
    for key, val in mapping.items():
        lines.append(f"| `{key}` | {val} |")
    lines.append("")
    return lines


def table_to_markdown(name: str, table: dict) -> str:
    """Render one server's static table as a self-contained markdown document."""
    profile = table.get("inferred_profile", {})
    dist = table.get("band_distribution", {})
    xcheck = table.get("crosscheck_summary", {})
    lines: list[str] = [
        f"# Evaluation ground truth — {name}",
        "",
        "> Design-time reviewed risk table. **Used only to grade the scanner's "
        "output; the scanner never reads this file.**",
        "",
        "## Server",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| name | {name} |",
        f"| server | {table.get('server', '')} |",
        f"| mcp_kind | {table.get('mcp_kind', '')} |",
        f"| version | {table.get('version', '')} |",
        f"| model_reviewed | {table.get('model_reviewed', '')} |",
        f"| formula | `{table.get('formula', '')}` |",
        f"| band_distribution | {dist} |",
        f"| judge_ran | {xcheck.get('judge_ran', '')} |",
        f"| judge_overrides | {xcheck.get('overridden', '')} |",
        "",
        "## Inferred domain profile",
        "",
    ]
    for key in ("mcp_kind", "asset_meaning", "blast_radius_meaning", "worked_example"):
        if profile.get(key):
            lines.append(f"- **{key}**: {profile[key]}")
    for key in ("dangerous_classes", "irreversible_actions"):
        vals = profile.get(key) or []
        if vals:
            lines.append(f"- **{key}**: {', '.join(str(v) for v in vals)}")
    lines += ["", *_kv_table("Tool impact (1 read · 2 recoverable · 3 destructive)",
                             table.get("tool_impact", {}), "tool", "impact")]
    lines += _kv_table("Asset sensitivity (1 low – 5 crown-jewel)",
                       table.get("asset_sensitivity", {}), "asset", "sensitivity")
    lines += ["## Risk matrix (score · band)", "",
              "Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical", ""]
    lines += _matrix_md(table)
    lines.append("")
    return "\n".join(lines)


def _index_md(data: dict, src_name: str) -> str:
    """Render the cross-server index as the evaluation README."""
    lines = [
        "# Evaluation ground truth",
        "",
        f"Rendered from `{src_name}` by `scripts/export_eval_tables.py`.",
        "",
        "These design-time, judge-reviewed risk tables are the **reference the "
        "scanner is graded against** (see `scripts/evaluate_scanner.py`). They are "
        "**not** an input to the scanner and must not be used for training.",
        "",
        "| Server | Kind | Worst band | Tools | Assets | Critical cells | Judge overrides |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in data.get("index", []):
        crit = ", ".join(entry.get("critical_cells", [])) or "—"
        lines.append(
            f"| [{entry['name']}]({entry['name']}.md) | {entry.get('kind', '')} | "
            f"{entry.get('worst_band', '')} | {entry.get('n_tools', '')} | "
            f"{entry.get('n_assets', '')} | {crit} | {entry.get('overridden', '')} |"
        )
    totals = data.get("totals", {})
    lines += ["", f"**Totals:** {totals}", ""]
    return "\n".join(lines)


def export(src: Path, out: Path) -> list[Path]:
    """Render every table in ``src`` to markdown under ``out``; return written paths."""
    data = json.loads(src.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    index_path = out / "README.md"
    index_path.write_text(_index_md(data, src.name), encoding="utf-8")
    written.append(index_path)

    for name, table in data.get("tables", {}).items():
        path = out / f"{name}.md"
        path.write_text(table_to_markdown(name, table), encoding="utf-8")
        written.append(path)

    # Keep the source JSON beside the markdown as the raw evaluation reference.
    raw = out / "raw" / src.name
    raw.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, raw)
    written.append(raw)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--take2", action="store_true", help="use the take2 (per-file) tables")
    parser.add_argument("--src", type=Path, help="explicit source JSON (overrides --take2)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    args = parser.parse_args()

    src = args.src or (
        SAMPLES / ("all_static_tables_take2.json" if args.take2 else "all_static_tables.json")
    )
    out = args.out.resolve()
    written = export(src, out)
    print(f"Wrote {len(written)} files to {out} from {src.name}:")
    for path in written:
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        print(f"  {rel}")


if __name__ == "__main__":
    main()
