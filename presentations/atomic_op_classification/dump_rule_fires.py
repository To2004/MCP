"""Print a table of rule-fire counts across all known servers.

Usage (from repo root):
    uv run python presentations/atomic_op_classification/dump_rule_fires.py
    uv run python presentations/atomic_op_classification/dump_rule_fires.py --source readme
    uv run python presentations/atomic_op_classification/dump_rule_fires.py --source toollist
    uv run python presentations/atomic_op_classification/dump_rule_fires.py --server filesystem sqlite
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from mcp_security.atomic_ops.classifier import classify_server
from mcp_security.atomic_ops.server_catalog import KNOWN_SERVERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dump rule fire counts across servers")
    parser.add_argument(
        "--source",
        choices=["readme", "toollist", "both"],
        default="both",
        help="Which classification source to inspect (default: both)",
    )
    parser.add_argument(
        "--server",
        nargs="+",
        default=None,
        metavar="NAME",
        help="Restrict to specific server names",
    )
    args = parser.parse_args(argv)

    servers = KNOWN_SERVERS
    if args.server:
        wanted = set(args.server)
        servers = [s for s in KNOWN_SERVERS if s.name in wanted]
        if not servers:
            print(f"No known servers matched: {wanted}", file=sys.stderr)
            return 2

    readme_counts: Counter[str] = Counter()
    toollist_counts: Counter[str] = Counter()

    for s in servers:
        print(f"  classifying {s.name}...", file=sys.stderr)
        sc = classify_server(s)
        if args.source in ("readme", "both"):
            for ct in sc.readme_classifications:
                for rule_id in ct.rule_ids:
                    readme_counts[rule_id] += 1
        if args.source in ("toollist", "both"):
            for ct in sc.toollist_classifications:
                for rule_id in ct.rule_ids:
                    toollist_counts[rule_id] += 1

    all_rules = sorted(set(readme_counts) | set(toollist_counts))
    if not all_rules:
        print("No rules fired.", file=sys.stderr)
        return 0

    col_w = max(len(r) for r in all_rules) + 2
    print(f"\n{'rule_id':<{col_w}} {'readme_hits':>12} {'toollist_hits':>14}")
    print("-" * (col_w + 28))
    for rule_id in all_rules:
        rc = readme_counts.get(rule_id, 0)
        tc = toollist_counts.get(rule_id, 0)
        if args.source == "readme" and rc == 0:
            continue
        if args.source == "toollist" and tc == 0:
            continue
        print(f"{rule_id:<{col_w}} {rc:>12} {tc:>14}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
