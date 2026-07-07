"""Compare the scanner's bands to the hand-made Excel heatmaps.

Reads the three hand-authored risk matrices in
``presentations/heatmap_byhand/xlsx/`` (filesystem, sqlite, slack) — each a
(asset-row) × (tool-column) grid of bands — and grades the scanner's scans
against them on the cells that map, reporting exact and within-one-band
agreement plus the band distributions.

Alignment is best-effort and honest about its limits: filesystem reduces to
(filetype, tool) worst band; sqlite to (table, tool) worst band; slack compares
per-tool worst band (the heatmap's asset categories don't map 1:1 to channels).
Tool names are normalised across the heatmap's and the scanner's spellings.

Run:  python scripts/compare_vs_heatmap_xlsx.py [--scan-dir reports/scan]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
XLSX = REPO / "presentations" / "heatmap_byhand" / "xlsx"
RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# Heatmap tool spelling -> scanner tool spelling (per kind).
_FS_TOOLMAP = {
    "read_file": "read_file", "write_file": "write_file", "edit_file": "edit_file",
    "create_dir": "create_directory", "list_dir": "list_directory",
    "move_file": "move_file", "search": "search_files", "get_file_info": "get_file_info",
}


def _norm(band: object) -> str | None:
    if band is None:
        return None
    b = str(band).strip().lower()
    if b in RANK:
        return b
    if b in {"n/a", "na", ""}:
        return None
    return None


def _worst(a: str | None, b: str | None) -> str | None:
    if a is None:
        return b
    if b is None:
        return a
    return a if RANK[a] >= RANK[b] else b


def _load_matrix(path: Path, sheet: str, asset_cols: int, label_col: int) -> dict[tuple[str, str], str]:
    """Parse a heatmap sheet -> {(asset_label, heatmap_tool): worst band}.

    ``asset_cols`` = number of leading asset-describing columns (rest are tools);
    ``label_col`` = which of those columns is the alignment key (0-based), e.g.
    filetype for filesystem, table name for sqlite. Blank keys inherit the row
    above (merged-cell style).
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    tools = [str(h).strip() for h in rows[0][asset_cols:] if h]
    out: dict[tuple[str, str], str] = {}
    last_label = ""
    for row in rows[1:]:
        raw = row[label_col] if label_col < len(row) else None
        label = (str(raw).strip() if raw else "") or last_label
        last_label = label
        if not label:
            continue
        for j, tool in enumerate(tools):
            band = _norm(row[asset_cols + j]) if asset_cols + j < len(row) else None
            if band is not None:
                key = (label.lower(), tool)
                out[key] = _worst(out.get(key), band)
    return out


def _ext(asset: str) -> str:
    a = asset.replace("\\", "/").lower()
    return "." + a.rsplit(".", 1)[-1] if "." in a.rsplit("/", 1)[-1] else "(noext)"


def _scanner_fs_by_filetype(scan_dir: Path) -> dict[tuple[str, str], str]:
    """Worst scanner band per (filetype, tool) across all filesystem demo scans."""
    out: dict[tuple[str, str], str] = {}
    for p in scan_dir.glob("fs_*.json"):
        d = json.loads(p.read_text())
        for asset, row in d.get("bands", {}).items():
            ft = _ext(asset)
            for tool, band in row.items():
                b = _norm(band)
                if b:
                    out[(ft, tool)] = _worst(out.get((ft, tool)), b)
    return out


def _scanner_cells(scan_dir: Path, stem: str) -> dict[tuple[str, str], str]:
    p = scan_dir / f"{stem}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    return {
        (asset.lower(), tool): _norm(band)
        for asset, row in d.get("bands", {}).items()
        for tool, band in row.items()
        if _norm(band)
    }


def _tool_worst(cells: dict[tuple[str, str], str]) -> dict[str, str]:
    """Collapse {(asset, tool): band} to {tool: worst band across assets}."""
    out: dict[str, str] = {}
    for (_asset, tool), band in cells.items():
        out[tool] = _worst(out.get(tool), band)
    return out


def _agree(human: dict, scanner: dict, toolmap: dict[str, str]) -> tuple[int, int, int, list]:
    """Exact, within-1, total over cells present in both (after tool mapping)."""
    exact = within = total = 0
    diffs = []
    for (asset, htool), hband in human.items():
        stool = toolmap.get(htool, htool)
        sband = scanner.get((asset, stool))
        if sband is None:
            continue
        total += 1
        if hband == sband:
            exact += 1
        if abs(RANK[hband] - RANK[sband]) <= 1:
            within += 1
        elif len(diffs) < 6:
            diffs.append(f"{asset}×{htool}: human={hband} scanner={sband}")
    return exact, within, total, diffs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-dir", type=Path, default=REPO / "reports" / "scan")
    args = ap.parse_args()
    sd = args.scan_dir

    print(f"# Scanner vs hand-made heatmaps  (scan-dir: {sd})\n")

    # --- filesystem: (filetype, tool) ---  label_col=1 (Filetype)
    fs = _load_matrix(XLSX / "risk_ranking_filesystemMCP (2).xlsx", "mcp_combined_risk", 2, 1)
    e, w, t, diffs = _agree(fs, _scanner_fs_by_filetype(sd), _FS_TOOLMAP)
    print("## Filesystem  (by filetype × tool)")
    print(f"- mapped cells: {t} | exact {e}/{t} ({(e/t if t else 0):.0%}) | within-1 {w}/{t} ({(w/t if t else 0):.0%})")
    for d in diffs:
        print(f"  - {d}")

    # --- sqlite: (table, tool) ---  label_col=0 (Table)
    sq = _load_matrix(XLSX / "mcp_sqlite_risk_rankings (1).xlsx", "mcp_combined_risk_sqlite", 2, 0)
    e, w, t, diffs = _agree(sq, _scanner_cells(sd, "sqlite_cbg_sqlite"), {})
    print("\n## SQLite  (by table × tool)")
    print(f"- mapped cells: {t} | exact {e}/{t} ({(e/t if t else 0):.0%}) | within-1 {w}/{t} ({(w/t if t else 0):.0%})")
    for d in diffs:
        print(f"  - {d}")

    # --- slack: per-tool worst band (asset categories don't map 1:1 to channels) ---
    sl = _load_matrix(XLSX / "risk_ranking_slackMCP_formatted (2).xlsx", "T3_All_Together", 3, 2)
    human_tool = _tool_worst(sl)
    scan_tool = _tool_worst(_scanner_cells(sd, "slack_cbg"))
    print("\n## Slack  (per-tool worst band — human vs scanner)")
    print("| tool | human | scanner |")
    print("| --- | --- | --- |")
    e = t = 0
    for tool in sorted(human_tool):
        s = scan_tool.get(tool)
        if s is None:
            continue
        t += 1
        e += human_tool[tool] == s
        print(f"| {tool} | {human_tool[tool]} | {s} |")
    if t:
        print(f"\n- per-tool exact agreement: {e}/{t} ({e/t:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
