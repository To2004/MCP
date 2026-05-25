"""CLI entrypoint: classify all known servers and write the xlsx heatmap.

Run with: ``uv run python -m mcp_security.atomic_ops.build_heatmap``
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .classifier import classify_server
from .server_catalog import KNOWN_SERVERS
from .xlsx_writer import write_heatmap

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = (
    REPO_ROOT
    / "presentations"
    / "atomic_op_classification"
    / "mcp_tools_atomic_ops.xlsx"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the MCP atomic-op heatmap")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Output xlsx path"
    )
    parser.add_argument(
        "--live", action="store_true", help="Attempt live MCP introspection"
    )
    parser.add_argument(
        "--server",
        action="append",
        default=None,
        help="Restrict to specific server names (repeatable)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    servers = KNOWN_SERVERS
    if args.server:
        wanted = set(args.server)
        servers = [s for s in KNOWN_SERVERS if s.name in wanted]
        if not servers:
            print(f"No known servers matched: {wanted}", file=sys.stderr)
            return 2

    classifications = []
    for s in servers:
        logging.info("classifying %s (%s)", s.name, s.tier)
        classifications.append(classify_server(s, prefer_live=args.live))

    write_heatmap(args.out, classifications)
    readme_rows = sum(len(c.readme_classifications) for c in classifications)
    tl_rows = sum(len(c.toollist_classifications) for c in classifications)
    print(
        f"Wrote {args.out} — {len(servers)} servers, "
        f"{readme_rows} README rows, {tl_rows} tool-list rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
