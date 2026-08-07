"""Pure scans: the tool list and the org profile are the ONLY scanner inputs.

The realistic deployment scenario — and, per the project's decision, the shape
the "ultimate" configuration is measured in: a gateway scoring an MCP server it
cannot open. No file tree walk, no demo asset scopes, no LLM-generated homing
assets. Everything the scan knows comes from exactly two documents per server:

1. the captured tool catalog (``tools/list`` — name, description, parameters), and
2. the organization's written profile (spec v1: prose header + per-asset table
   with Sens., C/I/A, Contents grammar, judgement flags).

The ASSET REGISTRY is built from the profile's table rows: ``Contents`` + ``Why``
become the asset description, the spec flags become tags, and the Sens. column is
the sensitivity primitive. The behavioral baseline's app purpose comes from the
profile's "Expected organizational use" paragraph.

``--impact-mode`` selects the scoring arm (all share the profile-sens machinery):
    five_level_v2_ult          v3 base: bulk rules + sens/impact floors
    five_level_v2_ult_imponly  impact stage sees the profile PROSE only (no table)
    five_level_v2_ult_nodom    no inferred-domain stage; description-only preamble

After each scan the driver reports tools with NO scored asset (all-N/A rows) —
on a calendar, events are the central asset, so an all-N/A tool means the
profile's asset decomposition missed something.

Run (GPU):  python scripts/scan_pure_desc.py [--impact-mode ...] [--only calendar_real]
Smoke:      python scripts/scan_pure_desc.py --no-llm --only calendar_real
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass, replace
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import matrix_csv, scan_to_markdown
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import AssetSpec, ServerRegistry, ToolSpec
from mcp_security.static_scoring.server_profiles import (
    ServerProfile,
    expected_use,
    parse_asset_rows,
    profile_for,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

MODES = (
    "five_level_v2_ult",
    "five_level_v2_ult_imponly",
    "five_level_v2_ult_nodom",
    "five_level_v2_ult_tools",  # rich: full tool registry in every prompt
    "five_level_v2_v4",  # v4: short standards-grounded prompts
    "five_level_v2_v4_static",  # v4 + deterministic (no-LLM) tool impact
)
# Output dir suffix per mode: reports/experiments/v3/five_level_v2_pure_<suffix>.
_MODE_SUFFIX = {
    "five_level_v2_ult": "v3",
    "five_level_v2_ult_imponly": "imponly",
    "five_level_v2_ult_nodom": "nodom",
    "five_level_v2_ult_tools": "rich",
    "five_level_v2_v4": "v4",
    "five_level_v2_v4_static": "v4static",
}
# Description-scheme transforms applied to the profile text BEFORE the registry is
# built (so both the preamble and the asset descriptions reflect the scheme):
#   full    -> the profile verbatim (default)
#   noflags -> the six judgement flags stripped from Contents
#   terse   -> the minimum skeleton: fact line + Asset/Sens/shape+flags table
from mcp_security.static_scoring import server_profiles as _sp  # noqa: E402

SCHEMES = {
    "full": lambda text: text,
    "noflags": _sp.strip_profile_flags,
    "terse": _sp.terse_profile,
}
APP_ID = "expected-use"


@dataclass(frozen=True)
class Target:
    stem: str
    kind: str
    server: str
    catalog: Path


TARGETS: tuple[Target, ...] = (
    Target("calendar_real", "calendar", "calendar:real", TOOL_LISTS / "calendar_real.json"),
    Target("slack_real", "slack", "slack:real", TOOL_LISTS / "slack_real.json"),
    Target("github_real", "github", "github:real", TOOL_LISTS / "github_real.json"),
    Target(
        "fs_corp_filesystem", "filesystem", "fs:corp_filesystem", TOOL_LISTS / "filesystem.json"
    ),
    Target("sqlite_cbg_sqlite", "sqlite", "sqlite:cbg_sqlite", TOOL_LISTS / "sqlite.json"),
)


def build_pure_registry(profile: ServerProfile, tools: list[ToolSpec], kind: str) -> ServerRegistry:
    """A ServerRegistry whose every field comes from the catalog or the profile."""
    assets = [
        AssetSpec(
            asset_id=row.asset_id,
            description=" ".join(part for part in (row.contents, row.why) if part).strip(),
            tags=tuple(f"flag:{flag}" for flag in row.flags),
        )
        for row in parse_asset_rows(profile.text)
    ]
    purpose = expected_use(profile.text)
    return ServerRegistry(
        server=profile.server,
        kind=kind,
        tools=tools,
        assets=assets,
        apps={APP_ID: purpose} if purpose else {},
        description=profile.text,
    )


def uncovered_tools(table: dict) -> list[str]:
    """Tools whose every (tool, asset) cell is N/A — no asset claims them."""
    out = []
    for tool in table["tool_impact"]:
        if all(
            table["blast_radius"].get(f"{tool}|{asset}") is None for asset in table["asset_ids"]
        ):
            out.append(tool)
    return sorted(out)


def scan_one(target: Target, *, impact_mode: str, scheme: str, use_llm: bool, version: str) -> dict:
    raw = profile_for(target.server)
    profile = replace(raw, text=SCHEMES[scheme](raw.text))  # apply the scheme transform
    tools = load_tool_list(target.kind, path=target.catalog)
    registry = build_pure_registry(profile, tools, target.kind)
    print(
        f"[pure] {target.stem} (scheme={scheme}): {len(tools)} tools (catalog) + "
        f"{len(registry.assets)} assets (profile table) — no store, no generated assets"
    )
    table = build_static_table(
        registry, use_llm=use_llm, strict=use_llm, version=version, impact_mode=impact_mode
    )
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = target.kind
    table["registry_source"] = "tool_catalog+org_profile_only"
    table["desc_scheme"] = scheme
    table["catalog_sha256"] = hashlib.sha256(target.catalog.read_bytes()).hexdigest()
    table["uncovered_tools"] = uncovered_tools(table)
    enrich_scan(table, registry.tools, use_llm=use_llm)
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--impact-mode", default="five_level_v2_ult", choices=MODES)
    parser.add_argument(
        "--scheme",
        default="full",
        choices=list(SCHEMES),
        help="description scheme transform (default: full)",
    )
    parser.add_argument("--version-tag", default=None, help="default: scan-pure-<mode>")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="default: reports/experiments/v3/five_level_v2_pure_<suffix>",
    )
    parser.add_argument(
        "--only", default=None, help="comma-separated stems (default: all 4 servers)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="re-scan stems whose artifact already exists"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    suffix = _MODE_SUFFIX[args.impact_mode]
    if args.scheme != "full":  # scheme arms get their own directory
        suffix = args.scheme
    gen = "v4" if args.impact_mode.startswith("five_level_v2_v4") else "v3"
    out_dir = args.out_dir or (
        REPO_ROOT / "reports" / "experiments" / gen / f"five_level_v2_pure_{suffix}"
    )
    version = args.version_tag or f"scan-pure-{args.impact_mode}-{args.scheme}"
    out_dir.mkdir(parents=True, exist_ok=True)

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    selected = [t for t in TARGETS if wanted is None or t.stem in wanted]
    if wanted:
        unknown = wanted - {t.stem for t in TARGETS}
        if unknown:
            print(
                f"[FAIL] unknown stems {sorted(unknown)}; choose from {[t.stem for t in TARGETS]}"
            )
            return 1

    rc = 0
    for target in selected:
        out_json = out_dir / f"{target.stem}.json"
        if out_json.exists() and not args.overwrite:
            print(f"[skip] {target.stem}: already scanned; --overwrite to redo")
            continue
        if not target.catalog.exists():
            print(f"[skip] {target.stem}: missing catalog {target.catalog}")
            continue
        try:
            table = scan_one(
                target,
                impact_mode=args.impact_mode,
                scheme=args.scheme,
                use_llm=not args.no_llm,
                version=version,
            )
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        out_json.write_text(json.dumps(table, indent=2), encoding="utf-8")
        (out_dir / f"{target.stem}.md").write_text(
            scan_to_markdown(target.server, target.kind, table), encoding="utf-8"
        )
        (out_dir / f"{target.stem}_matrix.csv").write_text(matrix_csv(table), encoding="utf-8")
        uncovered = table["uncovered_tools"]
        print(
            f"[ok] {target.stem} ({args.impact_mode}): score_max {table['score_max']} "
            f"| floored {table['blast_floor'].get('raised_cells')} "
            f"| bulk fixups {len(table.get('bulk_fixups', []))} "
            f"| uncovered tools {uncovered if uncovered else 'NONE'} "
            f"| bands {table['band_distribution']} -> {out_json}"
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
