"""CLI: rank the captured call corpus against the scanner's matrices.

Usage::

    uv run python -m mcp_security.call_scoring [--output PATH] [--markdown PATH]

Reads the scan artifacts under ``reports/scan/`` (produced by
``python -m mcp_security.scanner``) and scores every captured session's calls
against them. Run the scanner first — it is LLM-only, so there is nothing to
score against until a scan exists.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .corpus import (
    DEFAULT_OUTPUT,
    DEFAULT_OUTPUT_MD,
    score_corpus,
    summarize,
    write_ranked_csv,
    write_ranked_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank captured MCP tool calls by scanned risk.")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Where to write the ranked CSV (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--markdown", type=Path, default=DEFAULT_OUTPUT_MD,
        help=f"Where to write the ranked markdown (default: {DEFAULT_OUTPUT_MD}).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable info logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    scored = score_corpus()
    if not scored:
        print("No calls scored. Run `python -m mcp_security.scanner` to produce a scan first.")
        return 1
    csv_path = write_ranked_csv(scored, args.output)
    md_path = write_ranked_markdown(scored, args.markdown)
    print(summarize(scored))
    print(f"\nRanked CSV written to {csv_path}")
    print(f"Ranked markdown written to {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
