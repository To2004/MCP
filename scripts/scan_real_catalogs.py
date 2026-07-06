"""Scan the REAL captured MCP tool catalogs into risk matrices.

The stock scanner ignores ``--tool-list`` for declarative kinds (github/slack/
calendar) and uses the small demo tool set. This script instead feeds the real
catalogs captured live (``reports/tool_lists/<kind>_real.json`` — GitHub 26,
Calendar 13, Slack 16 tools) into the same LLM pipeline, paired with the
registry's asset scopes, and writes ``reports/scan/<kind>_real.json`` (+ .md).

LLM-only (Qwen via Ollama), so run on a GPU node. ``--no-llm`` builds the
deterministic offline baseline for a plumbing smoke test only.

Run (GPU):  python scripts/scan_real_catalogs.py
Smoke:      python scripts/scan_real_catalogs.py --no-llm
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp_security.scanner.render import scan_to_markdown
from mcp_security.scanner.scan import ScanResult, write_scan
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring import registry as reg
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import ServerRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

# kind -> (real catalog file, demo registry loader for asset scopes)
TARGETS = {
    "github": (TOOL_LISTS / "github_real.json", reg.load_github_registry),
    "calendar": (TOOL_LISTS / "calendar_real.json", reg.load_calendar_registry),
    "slack": (TOOL_LISTS / "slack_real.json", reg.load_slack_registry),
}


def scan_one(kind: str, catalog: Path, loader, *, use_llm: bool, version: str) -> ScanResult:
    """Scan one real catalog: real tools x the kind's asset scopes."""
    tools = load_tool_list(kind, path=catalog)
    base = loader()  # demo/representative asset scopes for this kind
    registry = ServerRegistry(
        server=f"{kind}:real", kind=kind, tools=tools, assets=base.assets, apps=base.apps
    )
    table = build_static_table(registry, use_llm=use_llm, strict=use_llm, version=version)
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = kind
    return ScanResult(server=registry.server, kind=kind, table=table)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default="scan-real-2026-07-06")
    args = parser.parse_args(argv)

    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    rc = 0
    for kind, (catalog, loader) in TARGETS.items():
        if not catalog.exists():
            print(f"[skip] no real catalog for {kind}: {catalog}")
            continue
        try:
            result = scan_one(
                kind, catalog, loader, use_llm=not args.no_llm, version=args.version_tag
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {kind}: {exc}")
            rc = 1
            continue
        path = write_scan(result)
        md = REPO_ROOT / "reports" / "scan" / f"{kind}_real.md"
        md.write_text(scan_to_markdown(result.server, kind, result.table), encoding="utf-8")
        print(f"[ok] {kind}: {result.n_tools} tools x {result.n_assets} assets -> {path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
