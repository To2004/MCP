"""Emit the L3 asset-table skeleton for a server, per the MCP Server Profile Spec.

Step 1 of the spec's authoring loop (``docs/standards/mcp-profile-spec.md``): walk
the server's store, enumerate its assets, and print a
``| Asset | Sens. | C | I | A | Contents | Why |`` table with the two columns only
the machine can know already filled in —

* **Asset** — the enumerated id, verbatim, so it always matches what the scan
  resolves and the coverage check never fails on a typo.
* **Contents** — the shape and the facts: a table's real column names, a file's
  extension, a directory's file count and extensions, a channel's scope.

The judgement columns come out as ``?`` for a human to fill: sensitivity, the CIA
letters, the ``Why`` sentence, and the flags that enumeration cannot know
(``self-sufficient``, ``population``, ``completeness-is-the-asset``,
``metadata-only``, ``hub``, ``public``).

This exists so an organization never hand-types asset ids or column lists — the
source of drift the spec is built to avoid.

Usage:
    python scripts/emit_profile_skeleton.py --kind sqlite --root demo/devops_sqlite/devops.db
    python scripts/emit_profile_skeleton.py --kind filesystem --root demo/fintech_fs --by-file
    python scripts/emit_profile_skeleton.py --kind slack --server slack:real \
        --tool-list reports/tool_lists/slack_real.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp_security.scanner.scan import build_registry
from mcp_security.static_scoring.registry import AssetSpec

REPO_ROOT = Path(__file__).resolve().parents[1]

# The judgement cells a human must supply; the spec's flags go in Contents.
_TODO = "?"
_HEADER = "| Asset | Sens. | C | I | A | Contents | Why |"
_SEPARATOR = "|---|---|---|---|---|---|---|"


def contents_cell(asset: AssetSpec, kind: str) -> str:
    """Render the spec's ``Contents`` grammar for one enumerated asset.

    Emits the shape token plus the facts the store actually yields, then a
    ``· ?`` placeholder where the author adds meaning and flags. Never guesses a
    flag: whether one row is self-sufficient or the whole set is the asset is
    exactly the judgement this column asks a human for.
    """
    tags = list(asset.tags)
    columns = [t.removeprefix("column:") for t in tags if t.startswith("column:")]
    exts = sorted({t.removeprefix("ext:") for t in tags if t.startswith("ext:")})

    if columns:  # sqlite table
        return f"table · columns: {', '.join(columns)} · row = ? · ?"
    if "directory" in tags or asset.asset_id.endswith("/"):
        ext_note = f" (ext: {', '.join(exts)})" if exts else ""
        # The registry's own description already carries the file count.
        return f"directory · {asset.description}{ext_note} · scope of {asset.asset_id} · ?"
    if exts:  # a single file
        return f"file · ext:{exts[0]} · ?"
    if kind == "slack":
        return "channel · members: ? · message = one post · ?"
    if kind == "calendar":
        return "calendar · event = one entry · ?"
    if kind == "github":
        return "repository · ? · ?"
    # asset-gen homing assets and anything else the loaders leave untagged.
    return f"surface · {asset.description or 'reach of the tool that homes here'} · ?"


def skeleton(kind: str, assets: list[AssetSpec]) -> str:
    """The full markdown table for ``assets``."""
    rows = [
        f"| `{a.asset_id}` | {_TODO} | {_TODO} | {_TODO} | {_TODO} "
        f"| {contents_cell(a, kind)} | {_TODO} |"
        for a in assets
    ]
    return "\n".join([_HEADER, _SEPARATOR, *rows])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True,
                        choices=["filesystem", "sqlite", "slack", "calendar", "github"])
    parser.add_argument("--root", type=Path, default=None, help="on-disk store (filesystem/sqlite)")
    parser.add_argument("--server", default=None, help="server id (defaults to the kind's default)")
    parser.add_argument("--by-file", action="store_true", help="per-file + per-directory assets")
    parser.add_argument("--tool-list", type=Path, default=None,
                        help="captured tools/list, for --gen-assets parity on real catalogs")
    parser.add_argument("--gen-assets", action="store_true",
                        help="also list the homing assets the scan generates (needs an LLM; "
                             "without it the skeleton omits them and coverage will fail later)")
    args = parser.parse_args(argv)

    registry = build_registry(
        args.kind, root=args.root, server=args.server, by_file=args.by_file,
        tool_list=args.tool_list,
    )
    if args.gen_assets:
        from mcp_security.scanner.scan import augment_with_generated_assets

        augment_with_generated_assets(registry, use_llm=True)

    print(f"<!-- skeleton: {registry.server} ({args.kind}), "
          f"{len(registry.assets)} enumerated assets. Fill every ? -->")
    print(skeleton(args.kind, registry.assets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
