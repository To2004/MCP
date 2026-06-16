"""CLI: scan connected MCP servers and print a ranked asset table per server.

Usage:
    python -m mcp_security.scanner [--root PATH] [--kind KIND] [--server NAME]
        [--out report.md] [--by-file] [--no-llm] [--no-web] [--timeout SECS]

With no ``--root``, the scanner reads every server configured in ``~/.claude.json``
(global + all projects). For each server it enumerates the assets it can reach and
prints a ``Rank | Name | Risk Level | Reasoning`` table, ranked with the shared
sensitivity anchors plus the local LLM (Ollama / Qwen2.5). ``--no-llm`` restricts
to anchored rows; ``--no-web`` disables the GitHub/npm fallback for unreachable
servers.
"""

from __future__ import annotations

import argparse
import logging
import sys
import urllib.parse

import requests

from .config_reader import ConnectionSpec, read_configured_servers, spec_from_root
from .enumerator import enumerate_assets
from .ranker import RankedAsset, rank_inventory
from .resolver import resolve

logger = logging.getLogger(__name__)

NPM_REGISTRY = "https://registry.npmjs.org"


def npm_fetcher(identifier: str) -> str | None:
    """Fetch a package README from the npm registry. Returns None on any failure.

    Only handles npm-style identifiers; GitHub/other are left to the LLM-theorise
    path. Best-effort and network-dependent by design.
    """
    pkg = identifier.strip()
    if "/" in pkg and not pkg.startswith("@"):
        # e.g. "github/github-mcp-server" — not an npm package.
        return None
    try:
        resp = requests.get(f"{NPM_REGISTRY}/{urllib.parse.quote(pkg, safe='@/')}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.debug("npm fetch failed for %s: %s", pkg, exc)
        return None
    return data.get("readme") or None


def _format_table(server: str, rows: list[RankedAsset], header: str) -> str:
    lines = [f"## {server}", "", header, "", "| Rank | Name | Risk Level | Reasoning |", "|---|---|---|---|"]
    for r in rows:
        suffix = "" if r.source == "enumerated" else f" _({r.source})_"
        lines.append(f"| {r.rank} | `{r.name}` | {r.risk_level} | {r.reasoning}{suffix} |")
    return "\n".join(lines)


def _scan_one(
    spec: ConnectionSpec, *, use_llm: bool, use_web: bool, by_file: bool = False
) -> tuple[list[RankedAsset], str]:
    inv = enumerate_assets(spec, by_file=by_file)
    if inv.is_empty and use_web:
        inv = resolve(spec, npm_fetcher if use_web else None)
    rows = rank_inventory(inv, use_llm=use_llm)
    roots = ", ".join(spec.roots) if spec.roots else (spec.url or spec.command or "n/a")
    header = (
        f"_kind={spec.kind} · scope={spec.scope} · source={inv.source} · "
        f"target={roots} · {len(rows)} assets_"
        + (f" · note: {inv.note}" if inv.note else "")
    )
    return rows, header


def _resolve_targets(args: argparse.Namespace) -> list[ConnectionSpec]:
    if args.root:
        return [spec_from_root(args.root, kind=args.kind)]
    specs = read_configured_servers()
    if args.server:
        specs = [s for s in specs if s.name == args.server]
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp_security.scanner", description=__doc__)
    parser.add_argument("--root", help="scan a local path directly (no config lookup)")
    parser.add_argument(
        "--kind",
        default="filesystem",
        choices=["filesystem", "sqlite", "slack", "github", "other"],
        help="asset kind for --root (default: filesystem)",
    )
    parser.add_argument("--server", help="only scan the configured server with this name")
    parser.add_argument("--out", help="also write the report to this markdown file")
    parser.add_argument("--by-file", action="store_true", help="(filesystem) list files, not types")
    parser.add_argument("--no-llm", action="store_true", help="anchored ranking only, no LLM")
    parser.add_argument("--no-web", action="store_true", help="skip the web/theorise fallback")
    parser.add_argument("--timeout", type=float, default=20.0, help="per-server connect timeout")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    targets = _resolve_targets(args)
    if not targets:
        print("No MCP servers found. Use --root PATH to scan a local store directly.", file=sys.stderr)
        return 1

    blocks: list[str] = [f"# MCP Asset Scan\n\n_{len(targets)} server(s) targeted_"]
    for spec in targets:
        rows, header = _scan_one(
            spec, use_llm=not args.no_llm, use_web=not args.no_web, by_file=args.by_file
        )
        blocks.append(_format_table(spec.name, rows, header))

    report = "\n\n".join(blocks) + "\n"
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"\nWrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
