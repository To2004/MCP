"""Full LLM static scan of a finance MCP (asset x tool risk matrix), no shortcuts.

The lightweight ``scan_finance.py`` produces tool-only verb severities with no
asset dimension. This runner instead feeds a finance server's saved ``tools/list``
plus an explicit ASSET MODEL (defined here, since finance has no on-disk store or
declarative registry) into the same strict, LLM-only pipeline the real scanner
uses -- so it yields the full ``cells``/``bands``/``blast``/``sensitivity`` matrix,
the blast-consistency check, and the atomic-op / input-ranking enrichment.

Assets are the protected things each server reaches. For a read-only market-data
server they are mostly PUBLIC (a good test that sensitivity does not over-inflate);
for a trading/portfolio server they include holdings, orders and credentials.

    python scripts/scan_finance_full.py --server finance_tools --out-dir reports/scan
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import matrix_csv, scan_to_markdown
from mcp_security.scanner.scan import ScanResult, write_scan
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring.pipeline import LLMUnavailableError, build_static_table
from mcp_security.static_scoring.registry import AssetSpec, ServerRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_LIST_DIR = REPO_ROOT / "reports" / "scan_finance" / "tool_lists"

# Asset models per finance server. asset_id + a content-rich description (the
# sensitivity stage reads the description) + tags the fallback heuristics key on.
_FINANCE_ASSETS: dict[str, list[AssetSpec]] = {
    # Read-only market-data server: everything it returns is public reference data;
    # the only crown jewel is the upstream API keys the server itself holds.
    "finance_tools": [
        AssetSpec("equity_market_data",
                  "Public equity prices, financial statements, holders, insider filings.",
                  tags=("public", "market_data")),
        AssetSpec("macro_economic_data",
                  "Public FRED macroeconomic series and search.", tags=("public",)),
        AssetSpec("news_and_sentiment",
                  "Public news feeds, CNBC feed, social-media sentiment, fear/greed index.",
                  tags=("public",)),
        AssetSpec("options_data",
                  "Public options-chain and derivatives reference data.", tags=("public",)),
        AssetSpec("server_api_credentials",
                  "Upstream API keys/tokens the server holds to call FRED and data vendors.",
                  tags=("secret", "credentials")),
    ],
    # Trading/portfolio/screening server: real, mutable, money-adjacent assets.
    "maverick": [
        AssetSpec("market_data",
                  "Public quotes, technical indicators and chart analysis.",
                  tags=("public", "market_data")),
        AssetSpec("watchlists",
                  "A user's saved watchlists and screening preferences.", tags=("internal",)),
        AssetSpec("screening_results",
                  "Generated stock-screening and strategy recommendation output.",
                  tags=("internal",)),
        AssetSpec("portfolio_positions",
                  "The user's actual portfolio holdings, cost basis and risk exposure.",
                  tags=("restricted", "financial", "pii")),
        AssetSpec("account_and_orders",
                  "Brokerage account state and order placement/cancellation — moves real money.",
                  tags=("money", "financial", "crown_jewel")),
        AssetSpec("server_api_credentials",
                  "Upstream data/broker API keys and tokens the server holds.",
                  tags=("secret", "credentials")),
    ],
}

_FINANCE_APPS: dict[str, dict[str, str]] = {
    "finance_tools": {
        "research_agent": "Agent pulling market data and news for equity research",
    },
    "maverick": {
        "screening_agent": "Agent running screens and technical analysis for ideas",
        "portfolio_agent": "Agent managing the user's portfolio positions and orders",
    },
}


def build_finance_registry(server: str, tool_list: Path | None) -> ServerRegistry:
    """Assemble a finance :class:`ServerRegistry` from a saved tools/list + asset model."""
    if server not in _FINANCE_ASSETS:
        raise ValueError(f"no asset model for finance server {server!r}; "
                         f"known: {sorted(_FINANCE_ASSETS)}")
    path = tool_list or (TOOL_LIST_DIR / f"{server}.json")
    tools = load_tool_list(server, path=path)
    return ServerRegistry(
        server=f"finance:{server}",
        kind="finance",
        tools=tools,
        assets=_FINANCE_ASSETS[server],
        apps=_FINANCE_APPS.get(server, {}),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, choices=sorted(_FINANCE_ASSETS))
    parser.add_argument("--tool-list", type=Path, help="override saved tools/list path")
    # Finance scans live in their own dir, NOT reports/scan/ (which the verifier
    # guards: every artifact there must match a captured tools/list under
    # reports/tool_lists/, which finance servers do not have).
    parser.add_argument("--scan-dir", type=Path, default=REPO_ROOT / "reports" / "scan_finance_full")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "reports" / "scan_finance_full")
    parser.add_argument("--version-tag", default="scan-finance-stage3")
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke only)")
    args = parser.parse_args(argv)

    registry = build_finance_registry(args.server, args.tool_list)
    use_llm = not args.no_llm
    print(f"scanning {registry.server}: {len(registry.tools)} tools x "
          f"{len(registry.assets)} assets (strict={use_llm})", flush=True)
    try:
        table = build_static_table(registry, use_llm=use_llm, strict=use_llm,
                                   version=args.version_tag)
    except LLMUnavailableError as exc:
        print(f"scan aborted: {exc}", file=sys.stderr)
        return 2
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = "finance"
    enrich_scan(table, registry.tools, use_llm=use_llm)

    result = ScanResult(server=registry.server, kind="finance", table=table)
    scan_path = write_scan(result, args.scan_dir)
    print(f"wrote scan artifact: {scan_path}", flush=True)

    stem = scan_path.stem
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"{stem}.md").write_text(
        scan_to_markdown(registry.server, "finance", table), encoding="utf-8")
    (args.out_dir / f"{stem}_matrix.csv").write_text(matrix_csv(table), encoding="utf-8")
    print(f"band_distribution: {table['band_distribution']}", flush=True)
    flagged = table.get("blast_consistency", {}).get("flagged", [])
    print(f"blast-drift flags: {len(flagged)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
