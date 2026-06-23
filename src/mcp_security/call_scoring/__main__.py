"""CLI: score the captured call corpus and write the ranked output.

Usage::

    uv run python -m mcp_security.call_scoring [--output PATH]
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .corpus import DEFAULT_OUTPUT, score_corpus, summarize, write_ranked_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score captured MCP tool calls by risk.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the ranked CSV (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable info logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    scored = score_corpus()
    output = write_ranked_csv(scored, args.output)
    print(summarize(scored))
    print(f"\nRanked CSV written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
