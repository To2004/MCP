"""v5 — the policy-grade scan: the organization supplies NO sensitivity numbers.

The final static arm. Everything the scanner knows comes from exactly two
documents per server:

1. the captured tool catalog (``tools/list`` — name, description, parameters), and
2. the organization's **policy** section (``docs/mcp-tools/server-policies.md``,
   spec ``docs/standards/mcp-policy-spec.md``): a data-classification table
   stating adverse impact per class, an asset register (asset · description ·
   tools · flags · CIA), recognition rules with a fail-closed default, operation
   limits, expected use and loss priorities — **and no 1-5 anywhere**.

The ASSET REGISTRY is built from the register rows: ``Description`` becomes the
asset description, ``Tools`` becomes ``tool:<name>`` tags (the exact tool×asset
homing the blast stage scores against), ``Flags`` becomes ``flag:<name>`` tags
(the escape routes a tier-5 blast must cite).

How v5 differs from v4 (``scripts/scan_pure_desc.py --impact-mode
five_level_v2_v4``), which read the inventory-grade profile instead:

===============  =====================================  =============================
stage            v4                                     v5
===============  =====================================  =============================
org context      server-profiles.md (per-asset Sens.)   server-policies.md (no numbers)
sensitivity      read off the org's table               LLM classifies vs the policy,
                                                        then maps the class onto 1-5
tool impact      LLM (v4 prompt), or all-static arm     deterministic ladder, LLM only
                                                        where the ladder abstains
blast radius     v4 rubric + full context + siblings    same, retargeted at the register
assembly         bulk/alias/floor/roof, band_label_v5    identical
===============  =====================================  =============================

The profile document's numbers are never shown to this scan — they are the
GROUND TRUTH the derived sensitivities are scored against afterwards
(``scripts/evaluate_policy_v5.py``).

Run (GPU):  python scripts/scan_policy_v5.py [--only calendar_real]
Smoke:      python scripts/scan_policy_v5.py --no-llm --only calendar_real
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import matrix_csv, scan_to_markdown
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import AssetSpec, ServerRegistry, ToolSpec
from mcp_security.static_scoring.server_policies import (
    POLICY_DOC,
    PolicyAssetRow,
    parse_asset_register,
    policy_for,
    unknown_register_tools,
    unmapped_tools,
)
from mcp_security.static_scoring.server_profiles import expected_use

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5"

IMPACT_MODE = "five_level_v2_v5"
APP_ID = "expected-use"

# Arms this driver can run. v5r is the prompt/rule rewrite: impact by operation
# type (scoped writes share tier 3 with content reads), no open-world in the
# ladder, no annotation ceiling, a three-field domain stage and a blast rubric
# with the single-tool discipline lines removed.
MODES = {
    "five_level_v2_v5": REPO_ROOT / "reports/experiments/v5/five_level_v2_policy_v5",
    "five_level_v2_v5r": REPO_ROOT / "reports/experiments/v5/five_level_v2_policy_v5r",
}


@dataclass(frozen=True)
class Target:
    """One server to scan: its policy section, its catalog, its output stem."""

    stem: str
    kind: str
    server: str
    catalog: Path


TARGETS: tuple[Target, ...] = (
    Target("calendar_real", "calendar", "calendar:real", TOOL_LISTS / "calendar_real.json"),
    Target("github_real", "github", "github:real", TOOL_LISTS / "github_real.json"),
    Target("slack_real", "slack", "slack:real", TOOL_LISTS / "slack_real.json"),
    # Live-provisioned organizations: the same three vendor catalogs, but the
    # policy is written against a real deployment that was probed rather than
    # assumed — so its operation limits record what the platform actually does
    # and does not enforce. See reports/live_run/orgs_2026-07-29/.
    Target("calendar_aurora", "calendar", "calendar:aurora", TOOL_LISTS / "calendar_real.json"),
    Target("github_helios", "github", "github:helios", TOOL_LISTS / "github_real.json"),
    Target("slack_vireo", "slack", "slack:vireo", TOOL_LISTS / "slack_real.json"),
)


def build_policy_registry(
    server: str, kind: str, policy_text: str, tools: list[ToolSpec]
) -> tuple[ServerRegistry, list[PolicyAssetRow]]:
    """A ServerRegistry whose every field comes from the catalog or the policy."""
    rows = parse_asset_register(policy_text)
    assets = [
        AssetSpec(
            asset_id=row.asset_id,
            description=(
                f"{row.description} (loss axis: {row.cia})" if row.cia else row.description
            ),
            tags=(
                tuple(f"flag:{flag}" for flag in row.flags)
                + tuple(f"tool:{tool}" for tool in row.tools)
            ),
        )
        for row in rows
    ]
    purpose = expected_use(policy_text)
    registry = ServerRegistry(
        server=server,
        kind=kind,
        tools=tools,
        assets=assets,
        apps={APP_ID: purpose} if purpose else {},
        description=policy_text,
    )
    return registry, rows


def uncovered_tools(table: dict) -> list[str]:
    """Tools whose every (tool, asset) cell came back N/A — no asset claims them."""
    return sorted(
        tool
        for tool in table["tool_impact"]
        if all(table["blast_radius"].get(f"{tool}|{asset}") is None for asset in table["asset_ids"])
    )


def scan_one(target: Target, *, use_llm: bool, version: str, impact_mode: str = IMPACT_MODE) -> dict:
    """Scan one server against its policy section and return the static table."""
    policy = policy_for(target.server)
    tools = load_tool_list(target.kind, path=target.catalog)
    registry, rows = build_policy_registry(target.server, target.kind, policy.text, tools)
    tool_names = [tool.name for tool in tools]
    stray = unknown_register_tools(rows, tool_names)
    if stray:
        raise ValueError(
            f"{target.server}: the policy's asset register names {len(stray)} tool(s) the "
            f"server does not advertise: {stray}. Fix the register's Tools cells in "
            f"{POLICY_DOC.name} — a wrong homing silently mis-scores blast."
        )
    unmapped = unmapped_tools(rows, tool_names)
    print(
        f"[v5] {target.stem}: {len(tools)} tools (catalog) + {len(registry.assets)} assets "
        f"(policy register) — no numbers from the org"
        + (f" | tools with no register row: {unmapped}" if unmapped else "")
    )
    table = build_static_table(
        registry, use_llm=use_llm, strict=use_llm, version=version, impact_mode=impact_mode
    )
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = target.kind
    table["registry_source"] = "tool_catalog+org_policy_only"
    table["description_source"] = str(POLICY_DOC.relative_to(REPO_ROOT))
    table["catalog_sha256"] = hashlib.sha256(target.catalog.read_bytes()).hexdigest()
    table["policy_register_unmapped_tools"] = unmapped
    table["uncovered_tools"] = uncovered_tools(table)
    enrich_scan(table, registry.tools, use_llm=use_llm)
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument(
        "--impact-mode", default=IMPACT_MODE, choices=list(MODES),
        help="v5 = the original policy arm; v5r = the rewritten prompts and rules",
    )
    parser.add_argument("--version-tag", default=None, help="default: scan-<impact-mode>")
    parser.add_argument("--out-dir", type=Path, default=None, help="default: per-mode dir")
    parser.add_argument(
        "--only", default=None, help="comma-separated stems (default: all 3 servers)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="re-scan stems whose artifact already exists"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.out_dir = args.out_dir or MODES[args.impact_mode]
    args.version_tag = args.version_tag or f"scan-{args.impact_mode}"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    selected = [t for t in TARGETS if wanted is None or t.stem in wanted]
    if wanted:
        unknown = wanted - {t.stem for t in TARGETS}
        if unknown:
            print(f"[FAIL] unknown stems {sorted(unknown)}; choose from {[t.stem for t in TARGETS]}")
            return 1

    rc = 0
    for target in selected:
        out_json = args.out_dir / f"{target.stem}.json"
        if out_json.exists() and not args.overwrite:
            print(f"[skip] {target.stem}: already scanned; --overwrite to redo")
            continue
        if not target.catalog.exists():
            print(f"[skip] {target.stem}: missing catalog {target.catalog}")
            continue
        try:
            table = scan_one(
                target,
                use_llm=not args.no_llm,
                version=args.version_tag,
                impact_mode=args.impact_mode,
            )
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        out_json.write_text(json.dumps(table, indent=2), encoding="utf-8")
        (args.out_dir / f"{target.stem}.md").write_text(
            scan_to_markdown(target.server, target.kind, table), encoding="utf-8"
        )
        (args.out_dir / f"{target.stem}_matrix.csv").write_text(matrix_csv(table), encoding="utf-8")
        sources = table.get("tool_impact_source", {})
        n_llm = sum(1 for src in sources.values() if src == "llm_fallback")
        print(
            f"[ok] {target.stem}: score_max {table['score_max']} "
            f"| impact static {len(sources) - n_llm}/{len(sources)}, llm fallback {n_llm} "
            f"| floored {table['blast_floor'].get('raised_cells')} "
            f"| capped {table['blast_roof'].get('capped_cells')} "
            f"| bands {table['band_distribution']} -> {out_json}"
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
