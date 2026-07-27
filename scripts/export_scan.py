"""Statically export a scan artifact to JSON + CSV + Markdown -- no LLM.

The LLM already ran when the scan was produced; this script only re-emits an
existing ``reports/scan/<server>.json`` (or any scan artifact) in three formats,
each surfacing the score together with its ``sensitivity×blast×impact``
calculation. Fully deterministic -- pure rendering, no model call::

    uv run python scripts/export_scan.py reports/all_scans_v6/real/calendar_real.json \\
        --out-dir reports/exports

Writes ``<stem>.json`` (pretty), ``<stem>.md`` (matrix with the calculation in
place) and ``<stem>_matrix.csv`` (tidy: asset,tool,sensitivity,blast,impact,
score,band) for each input.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp_security.scanner.render import matrix_csv, scan_to_markdown


def export(scan_json: Path, out_dir: Path) -> list[Path]:
    """Emit ``scan_json`` as json+md+csv into ``out_dir``; return the written paths."""
    table = json.loads(scan_json.read_text(encoding="utf-8"))
    server = table.get("server", scan_json.stem)
    kind = table.get("server_kind") or table.get("mcp_kind", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = scan_json.stem

    written: list[Path] = []
    json_path = out_dir / f"{stem}.json"
    if json_path.resolve() != scan_json.resolve():
        json_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    written.append(json_path)

    md_path = out_dir / f"{stem}.md"
    md_path.write_text(scan_to_markdown(server, kind, table), encoding="utf-8")
    written.append(md_path)

    csv_path = out_dir / f"{stem}_matrix.csv"
    csv_path.write_text(matrix_csv(table), encoding="utf-8")
    written.append(csv_path)
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scans", type=Path, nargs="+", help="scan JSON artifact(s)")
    parser.add_argument("--out-dir", type=Path, required=True, help="destination directory")
    args = parser.parse_args(argv)
    for scan in args.scans:
        for path in export(scan, args.out_dir):
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
