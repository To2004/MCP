"""Backfill existing scans with atomic-op flags + input rankings (no LLM).

The scanner now adds ``tool_atomic_ops`` and ``tool_input_ranking`` to every new
scan (see :mod:`mcp_security.scanner.atomic_flags`). This script retro-fits the
same two fields onto scan artifacts that were produced before, by re-reading each
server's tool catalog (real catalogs from ``reports/tool_lists/*_real.json``,
declarative demos from their registry, filesystem/sqlite demos from their saved
tool lists). It never touches the LLM-derived risk matrix — purely additive.

Run:  python scripts/enrich_scans_atomic.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring import registry as reg
from mcp_security.static_scoring.registry import ToolSpec

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

_DECLARATIVE_DEMO = {
    "github_cbg": reg.load_github_registry,
    "slack_cbg": reg.load_slack_registry,
    "calendar_cbg": reg.load_calendar_registry,
}


def _tools_for(stem: str) -> list[ToolSpec] | None:
    """Recover the ToolSpec list for a scan stem, or None if the source is unknown."""
    if stem.endswith("_real"):
        kind = stem[: -len("_real")]
        path = TOOL_LISTS / f"{stem}.json"
        return load_tool_list(kind, path=path) if path.exists() else None
    if stem in _DECLARATIVE_DEMO:
        return _DECLARATIVE_DEMO[stem]().tools
    if stem.startswith("fs_"):
        return load_tool_list("filesystem")
    if stem.startswith("sqlite_"):
        return load_tool_list("sqlite")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--llm", action="store_true",
        help="rank tool inputs with the LLM (needs Ollama/GPU); default is the rule heuristic",
    )
    args = parser.parse_args(argv)

    enriched = 0
    for path in sorted(SCAN_DIR.glob("*.json")):
        if path.stem.endswith("_params"):
            continue
        tools = _tools_for(path.stem)
        if not tools:
            print(f"[skip] {path.stem}: no tool source")
            continue
        table = json.loads(path.read_text(encoding="utf-8"))
        enrich_scan(table, tools, use_llm=args.llm)
        path.write_text(json.dumps(table, indent=2), encoding="utf-8")
        n_ops = sum(1 for v in table["tool_atomic_ops"].values() if v["atomic_ops"])
        srcs = {v["source"] for v in table["tool_input_ranking"].values()}
        enriched += 1
        print(f"[ok] {path.stem}: {n_ops}/{len(tools)} atomic ops; input-rank source={sorted(srcs)}")
    print(f"\nEnriched {enriched} scans.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
