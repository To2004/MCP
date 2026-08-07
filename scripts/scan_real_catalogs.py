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

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import scan_to_markdown
from mcp_security.scanner.scan import (
    ScanResult,
    augment_with_generated_assets,
    scan_server,
    write_scan,
)
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

# Disk-backed HELD-OUT servers for validation (kind, on-disk store root, server name).
# These were never iterated on while tuning the prompts, so they are a clean check.
DISK_TARGETS = [
    ("filesystem", REPO_ROOT / "demo" / "corp_filesystem", "fs:corp"),
    ("sqlite", REPO_ROOT / "demo" / "cbg_sqlite" / "cbg.db", "sqlite:cbg"),
]


def scan_one(
    kind: str, catalog: Path, loader, *, use_llm: bool, version: str, impact_mode: str,
    gen_assets: bool = False,
) -> ScanResult:
    """Scan one real catalog: real tools x the kind's asset scopes."""
    tools = load_tool_list(kind, path=catalog)
    base = loader()  # demo/representative asset scopes for this kind
    registry = ServerRegistry(
        server=f"{kind}:real", kind=kind, tools=tools, assets=base.assets, apps=base.apps
    )
    if gen_assets:  # home every tool on a concrete asset (parity with the fs run)
        n_generated = augment_with_generated_assets(registry, use_llm=use_llm)
        print(f"[asset-gen] {kind}: {n_generated} generated asset(s) added")
    table = build_static_table(
        registry, use_llm=use_llm, strict=use_llm, version=version, impact_mode=impact_mode
    )
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = kind
    # Atomic-op flags + input ranking (LLM ranking on a real scan) in the same pass.
    enrich_scan(table, registry.tools, use_llm=use_llm)
    return ScanResult(server=registry.server, kind=kind, table=table)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default="scan-real-2026-07-06")
    parser.add_argument(
        "--impact-mode", default="baseline",
        choices=["baseline", "five_level", "five_level_v2", "five_level_v2_na",
                 "cia", "hybrid", "hybrid_na", "five_level_v2_ctx"],
        help="tool-impact experiment: baseline (1-3), five_level (1-5), "
             "five_level_v2 (noop/meta/read/write/delete), five_level_v2_na "
             "(generalized 5-level + N/A cells), cia (base+CIA sum), or "
             "five_level_v2_ctx (_na + per-tool understanding fed into blast)",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=REPO_ROOT / "reports" / "scan",
        help="where to write <kind>_real.{json,md} (use a per-experiment dir)",
    )
    parser.add_argument(
        "--disk", action="store_true",
        help="also scan the disk-backed held-out servers (filesystem + sqlite)",
    )
    parser.add_argument(
        "--gen-assets", action="store_true",
        help="home every tool on a concrete asset (generate one where the registry "
             "leaves a tool uncovered) -- parity with the fs five_level_v2_na run",
    )
    parser.add_argument(
        "--kinds", default=None,
        help="comma-separated server kinds to scan (github,calendar,slack,filesystem,"
             "sqlite); default = all declarative (+ disk with --disk). A disk kind "
             "listed here is scanned even without --disk.",
    )
    args = parser.parse_args(argv)
    selected = {k.strip() for k in args.kinds.split(",")} if args.kinds else None

    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    def _write(result: ScanResult) -> None:
        path = write_scan(result, args.out_dir)
        (args.out_dir / f"{path.stem}.md").write_text(
            scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
        )
        print(f"[ok] {result.server} ({args.impact_mode}): {result.n_tools} tools x "
              f"{result.n_assets} assets -> {path}")

    rc = 0
    # 1) declarative real catalogs (github / calendar / slack).
    for kind, (catalog, loader) in TARGETS.items():
        if selected is not None and kind not in selected:
            continue
        if not catalog.exists():
            print(f"[skip] no real catalog for {kind}: {catalog}")
            continue
        try:
            _write(scan_one(kind, catalog, loader, use_llm=not args.no_llm,
                            version=args.version_tag, impact_mode=args.impact_mode,
                            gen_assets=args.gen_assets))
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {kind}: {exc}")
            rc = 1
    # 2) disk-backed held-out servers (filesystem + sqlite): with --disk, or when a
    #    disk kind is named in --kinds.
    run_disk = args.disk or (
        selected is not None and any(kind in selected for kind, _, _ in DISK_TARGETS)
    )
    if run_disk:
        for kind, root, name in DISK_TARGETS:
            if selected is not None and kind not in selected:
                continue
            if not root.exists():
                print(f"[skip] no store for {name}: {root}")
                continue
            try:
                _write(scan_server(kind, root=root, server=name, use_llm=not args.no_llm,
                                   version=args.version_tag, impact_mode=args.impact_mode,
                                   gen_assets=args.gen_assets))
            except Exception as exc:  # noqa: BLE001
                print(f"[FAIL] {name}: {exc}")
                rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
