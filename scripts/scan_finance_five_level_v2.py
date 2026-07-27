"""Scan a captured finance MCP catalog under the five_level_v2_na rubric (LLM).

Parity run with ``scan_fs_five_level_v2.py`` / ``scan_real_catalogs.py``, but the
target is one of the live-captured finance servers (tool lists under
``reports/scan_finance/tool_lists/<kind>.json``). Finance has no hand-curated
asset registry, so — exactly like the fs run — every tool is homed on an
LLM-generated asset (``gen_assets``); the domain-inference stage then derives the
finance domain (asset meaning, dependency hubs, dangerous classes, irreversible
actions) from the tool registry alone.

The five_level_v2_na tool-impact ladder:
    1 = liveness / no-op   2 = metadata   3 = read/observe
    4 = write/modify       5 = delete/destroy (irreversible)
Blast is COVERAGE of the asset; the blast stage marks (tool, asset) pairs the
tool does not act on as N/A. LLM-only (Qwen via Ollama) -> run on a GPU node.

Run (GPU):  python scripts/scan_finance_five_level_v2.py --kind finance_tools
Smoke:      python scripts/scan_finance_five_level_v2.py --kind finance_tools --no-llm
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import scan_to_markdown
from mcp_security.scanner.scan import (
    ScanResult,
    augment_with_generated_assets,
    write_scan,
)
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import ServerRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_LIST_DIR = REPO_ROOT / "reports" / "scan_finance" / "tool_lists"
IMPACT_MODE = "five_level_v2_na"


def scan_finance(kind: str, *, use_llm: bool, version: str) -> ScanResult:
    """Scan one captured finance catalog: real tools x LLM-generated asset scopes."""
    catalog = TOOL_LIST_DIR / f"{kind}.json"
    tools = load_tool_list(kind, path=catalog)
    registry = ServerRegistry(server=f"finance:{kind}", kind=kind, tools=tools, assets=[], apps={})
    # No curated finance registry -> home every tool on a generated asset (fs-run parity).
    n_generated = augment_with_generated_assets(registry, use_llm=use_llm)
    logging.info("asset-gen: %s -> %d generated asset(s)", kind, n_generated)
    table = build_static_table(
        registry, use_llm=use_llm, strict=use_llm, version=version, impact_mode=IMPACT_MODE
    )
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = kind
    enrich_scan(table, registry.tools, use_llm=use_llm)  # atomic ops + input ranking
    return ScanResult(server=registry.server, kind=kind, table=table)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        default="finance_tools",
        choices=["finance_tools", "yahoo_finance", "sec_edgar", "openbb", "maverick"],
        help="which captured finance server to scan (default: finance_tools)",
    )
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default="scan-finance-five_level_v2_na")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "experiments" / "five_level_v2_finance",
        help="where to write <kind>.{json,md}",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    catalog = TOOL_LIST_DIR / f"{args.kind}.json"
    if not catalog.exists():
        print(f"[FAIL] no captured tool list for {args.kind}: {catalog}")
        return 1

    try:
        result = scan_finance(args.kind, use_llm=not args.no_llm, version=args.version_tag)
    except Exception as exc:  # noqa: BLE001 -- report which server failed, then exit non-zero
        print(f"[FAIL] finance:{args.kind}: {exc}")
        return 1

    path = write_scan(result, args.out_dir)
    (args.out_dir / f"{path.stem}.md").write_text(
        scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
    )
    print(
        f"[ok] {result.server} ({IMPACT_MODE}): {result.n_tools} tools x "
        f"{result.n_assets} assets -> {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
