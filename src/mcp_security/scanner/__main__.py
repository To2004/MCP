"""CLI: statically scan an MCP server (before it runs) and write a scan artifact.

Usage::

    python -m mcp_security.scanner --kind filesystem
    python -m mcp_security.scanner --kind filesystem --root demo/law_firm_fs --by-file
    python -m mcp_security.scanner --kind sqlite --root demo/cbg_sqlite/cbg.db

Tools are read from the Excel catalog (``docs/mcp-tools/xlsx/<kind>_tools.xlsx``)
and assets from the on-disk store; the LLM (Ollama / Qwen2.5) then derives every
risk primitive in strict, LLM-only mode. The scan is written to
``reports/scan/<server>.json`` (and optionally markdown via ``--out``). There is
no live-MCP connection and no checked-in risk table is read.

``--no-llm`` runs the deterministic baseline for offline smoke checks only; a real
scan needs the model.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from mcp_security.static_scoring.pipeline import LLMUnavailableError

from .render import scan_to_markdown
from .scan import DEFAULT_SCAN_DIR, scan_server, write_scan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp_security.scanner", description=__doc__)
    parser.add_argument(
        "--kind", default="filesystem",
        choices=["filesystem", "sqlite", "slack", "calendar", "github"],
        help="server kind: selects the tool catalog and asset enumerator",
    )
    parser.add_argument("--root", type=Path, help="on-disk store (filesystem dir / sqlite db)")
    parser.add_argument("--server", help="override the scanned server's name")
    parser.add_argument("--by-file", action="store_true", help="(filesystem) per-file assets")
    parser.add_argument("--tool-list", type=Path, help="explicit saved tools/list json (overrides kind)")
    parser.add_argument("--out", type=Path, help="also write a markdown view to this file")
    parser.add_argument(
        "--scan-dir", type=Path, default=DEFAULT_SCAN_DIR, help="where to write the scan artifact"
    )
    parser.add_argument("--no-llm", action="store_true", help="deterministic baseline (offline only)")
    parser.add_argument("--version-tag", default="scan-0000-00-00", help="version stamp")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        result = scan_server(
            args.kind,
            root=args.root,
            server=args.server,
            by_file=args.by_file,
            tool_list=args.tool_list,
            use_llm=not args.no_llm,
            version=args.version_tag,
        )
    except LLMUnavailableError as exc:
        print(f"scan aborted: {exc}", file=sys.stderr)
        print("The scanner is LLM-only; start Ollama/Qwen or run on a GPU node.", file=sys.stderr)
        return 2

    path = write_scan(result, args.scan_dir)
    print(f"Scanned {result.server}: {result.n_tools} tools x {result.n_assets} assets")
    print(f"Wrote scan artifact: {path}")
    if args.out:
        args.out.write_text(scan_to_markdown(result.server, result.kind, result.table), "utf-8")
        print(f"Wrote markdown: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
