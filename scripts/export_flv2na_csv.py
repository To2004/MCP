"""Export every five_level_v2_na scan into one long-form CSV, joined with the tool
and asset DESCRIPTIONS the scores were derived from.

The scan artifacts store scores keyed by tool name / asset id but not the free-text
descriptions. Those are reconstructed deterministically from the same sources the
scan used: the real tool catalogs (github/slack/calendar), the filesystem/sqlite
tool sets, and each kind's base asset registry. Assets that were auto-generated at
scan time (``--gen-assets``, to home an otherwise-uncovered tool) are not persisted
with a description, so they are labelled as such.

One row per (server, asset, tool) cell -- the full risk matrix in tidy form,
including N/A cells. Columns: server, mcp_kind, asset, asset_sensitivity,
asset_description, tool, tool_impact, tool_description, blast_radius, blast_escape,
cell_score, band.

Run:  python scripts/export_flv2na_csv.py [--out reports/experiments/v1/five_level_v2_fs/all_scores.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring import registry as reg

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_fs"
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"
GENERATED_DESC = "(auto-generated asset to home an uncovered tool; description not persisted)"

# Severity is derived from the SCORE magnitude (fraction of score_max), NOT from the
# scan's stored `band_label`, which is hardcoded to the old 1-3 impact scale and so
# mis-labels 1-5 cells (a read=impact-3 gets its "irreversible" floor). Score-magnitude
# is correct at any scale and monotonic with the number, which is all a label needs.
_SEVERITY_CUTS = ((0.60, "critical"), (0.35, "high"), (0.15, "medium"), (0.0, "low"))


def severity_of(score: float | None, score_max: int) -> str:
    """Score-magnitude severity label; 'na' for an unscored (N/A) cell."""
    if score is None or not score_max:
        return "na"
    frac = score / score_max
    for cutoff, band in _SEVERITY_CUTS:
        if frac >= cutoff:
            return band
    return "low"

# scan file -> (kind, how to load its real tools, how to load its base assets).
# Declarative kinds read the REAL captured catalog for tools and the loader's base
# asset scopes; disk kinds read both from their loader.
SERVERS: list[tuple[str, str]] = [
    ("fs_corp.json", "filesystem"),
    ("sqlite_cbg.json", "sqlite"),
    ("github_real.json", "github"),
    ("slack_real.json", "slack"),
    ("calendar_real.json", "calendar"),
]


def _tool_descriptions(kind: str) -> dict[str, str]:
    """Map tool_name -> description, from the exact source the scan used."""
    if kind == "filesystem":
        tools = reg.load_filesystem_registry(REPO_ROOT / "demo" / "corp_filesystem").tools
    elif kind == "sqlite":
        tools = reg.load_sqlite_registry(REPO_ROOT / "demo" / "cbg_sqlite" / "cbg.db").tools
    else:  # declarative real catalog
        tools = load_tool_list(kind, path=TOOL_LISTS / f"{kind}_real.json")
    return {t.name: (t.description or "").strip() for t in tools}


def _asset_descriptions(kind: str) -> dict[str, str]:
    """Map asset_id -> description for the BASE (non-generated) assets."""
    if kind == "filesystem":
        assets = reg.load_filesystem_registry(
            REPO_ROOT / "demo" / "corp_filesystem", by_file=True
        ).assets
    elif kind == "sqlite":
        assets = reg.load_sqlite_registry(REPO_ROOT / "demo" / "cbg_sqlite" / "cbg.db").assets
    elif kind == "github":
        assets = reg.load_github_registry().assets
    elif kind == "slack":
        assets = reg.load_slack_registry().assets
    elif kind == "calendar":
        assets = reg.load_calendar_registry().assets
    else:
        raise ValueError(f"unknown kind {kind!r}")
    return {a.asset_id: (a.description or "").strip() for a in assets}


def _rows_for(scan_path: Path, kind: str) -> list[dict]:
    """One dict per (asset, tool) cell in this scan, joined with descriptions."""
    data = json.loads(scan_path.read_text(encoding="utf-8"))
    tool_desc = _tool_descriptions(kind)
    asset_desc = _asset_descriptions(kind)
    impacts = data["tool_impact"]
    sens = data["asset_sensitivity"]
    blast = data["blast_radius"]
    escape = data.get("blast_escape", {})
    cells = data["cells"]
    server = data["server"]
    mcp_kind = data.get("mcp_kind", kind)
    rows: list[dict] = []
    for asset_id, tool_row in cells.items():
        for tool_name, score in tool_row.items():
            key = f"{tool_name}|{asset_id}"
            rows.append(
                {
                    "server": server,
                    "mcp_kind": mcp_kind,
                    "asset": asset_id,
                    "asset_sensitivity": sens.get(asset_id),
                    "asset_description": asset_desc.get(asset_id, GENERATED_DESC),
                    "tool": tool_name,
                    "tool_impact": impacts.get(tool_name),
                    "tool_description": tool_desc.get(tool_name, ""),
                    "blast_radius": blast.get(key),
                    "blast_escape": escape.get(key, "none"),
                    "cell_score": score,
                }
            )
    return rows


FIELDNAMES = [
    "server", "mcp_kind", "asset", "asset_sensitivity", "asset_description",
    "tool", "tool_impact", "tool_description", "blast_radius", "blast_escape",
    "cell_score",
]


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write one long-form CSV (per-cell rows) to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=EXP_DIR / "all_scores.csv")
    parser.add_argument(
        "--per-mcp-dir", type=Path, default=EXP_DIR,
        help="also write one CSV per MCP server into this directory (as <stem>_scores.csv)",
    )
    args = parser.parse_args(argv)

    all_rows: list[dict] = []
    for fname, kind in SERVERS:
        path = EXP_DIR / fname
        if not path.exists():
            print(f"[skip] missing scan: {path}")
            continue
        rows = _rows_for(path, kind)
        all_rows.extend(rows)
        n_gen = sum(1 for r in rows if r["asset_description"] == GENERATED_DESC)
        # One CSV per MCP, alongside the combined file (fs_corp_scores.csv, ...).
        per_path = args.per_mcp_dir / f"{path.stem}_scores.csv"
        _write_csv(per_path, rows)
        print(f"[ok] {kind}: {len(rows)} cells ({n_gen} on generated assets) -> {per_path}")

    _write_csv(args.out, all_rows)
    print(f"[done] combined {len(all_rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
