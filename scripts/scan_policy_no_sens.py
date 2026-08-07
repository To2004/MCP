"""Scan the filesystem tenants with POLICY-grade org context (``five_level_v2_policy``).

The realistic-disclosure variant of ``scripts/scan_desc_no_sens.py``. Same scoring
(``five_level_v2_desc``: the org description rides in front of every stage and the
asset-sensitivity primitive is removed, score = blast x impact), but the description
comes from ``docs/mcp-tools/server-policies.md`` — the data-classification policy
and agent acceptable-use rules an organization can actually hand to an integrator —
instead of the full per-asset severity inventory in ``server-profiles.md``, which
real organizations decline to release.

Targets are the 11 servers with a policy section: the 5 filesystem tenants (an
identical 14-tool surface where only the organization changes, so any score
movement between orgs is attributable to the policy text alone) plus the demo and
real catalogs for github, slack and calendar.

Output goes to a NEW directory (``reports/experiments/staticscanner/no_sens/``);
existing artifacts are skipped unless ``--overwrite`` is passed, so neither the
desc-mode results nor a resumed run's completed work are ever clobbered.

Run (GPU):  python scripts/scan_policy_no_sens.py
Smoke:      python scripts/scan_policy_no_sens.py --no-llm --only fs_corp_filesystem
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_security.scanner.atomic_flags import enrich_scan
from mcp_security.scanner.render import matrix_csv, scan_to_markdown
from mcp_security.scanner.scan import (
    ScanResult,
    attach_profile,
    augment_with_generated_assets,
    scan_server,
)
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring import registry as reg
from mcp_security.static_scoring.pipeline import build_static_table
from mcp_security.static_scoring.registry import ServerRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO = REPO_ROOT / "demo"
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"
POLICY_DOC = REPO_ROOT / "docs" / "mcp-tools" / "server-policies.md"
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "staticscanner" / "no_sens"

# Scoring is identical to the desc experiment; only the description document differs,
# which the artifact records via `description_source`.
IMPACT_MODE = "five_level_v2_desc"


@dataclass(frozen=True)
class Target:
    """One server to scan under the policy description.

    ``root`` is the on-disk store for filesystem tenants; ``catalog`` is a captured
    ``tools/list`` for the real vendor catalogs. Neither is set for a declarative
    demo server whose tools come from the registry.
    """

    stem: str  # output file stem, matching the policy-doc section name
    kind: str
    server: str  # server id — the key used to look up the org policy
    root: Path | None = None
    catalog: Path | None = None


# The 11 servers with a policy section, in the order of docs/mcp-tools/server-policies.md.
TARGETS: tuple[Target, ...] = (
    # 5 filesystem tenants — identical 14-tool surface, different organization.
    Target("fs_fintech_fs", "filesystem", "fs:fintech_fs", root=DEMO / "fintech_fs"),
    Target("fs_medical_clinic_fs", "filesystem", "fs:medical_clinic_fs",
           root=DEMO / "medical_clinic_fs"),
    Target("fs_corp_filesystem", "filesystem", "fs:corp_filesystem",
           root=DEMO / "corp_filesystem"),
    Target("fs_law_firm_fs", "filesystem", "fs:law_firm_fs", root=DEMO / "law_firm_fs"),
    Target("fs_media_studio_fs", "filesystem", "fs:media_studio_fs",
           root=DEMO / "media_studio_fs"),
    # source code / messaging / calendar — real vendor catalogs and demo catalogs.
    Target("github_real", "github", "github:real", catalog=TOOL_LISTS / "github_real.json"),
    Target("github_cbg", "github", "github:cbg"),
    Target("slack_real", "slack", "slack:real", catalog=TOOL_LISTS / "slack_real.json"),
    Target("slack_cbg", "slack", "slack:cbg"),
    Target("calendar_real", "calendar", "calendar:real",
           catalog=TOOL_LISTS / "calendar_real.json"),
    Target("calendar_cbg", "calendar", "calendar:cbg"),
)

_DECLARATIVE_LOADERS = {
    "github": reg.load_github_registry,
    "slack": reg.load_slack_registry,
    "calendar": reg.load_calendar_registry,
}


def scan_catalog_target(
    target: Target, *, use_llm: bool, version: str, impact_mode: str = IMPACT_MODE
) -> ScanResult:
    """Scan a vendor/demo catalog with the policy document as its org description."""
    base = _DECLARATIVE_LOADERS[target.kind]()
    registry = ServerRegistry(
        server=target.server,
        kind=target.kind,
        tools=load_tool_list(target.kind, path=target.catalog),
        assets=base.assets,
        apps=base.apps,
        description=attach_profile(target.server, profile_doc=POLICY_DOC),
    )
    n_generated = augment_with_generated_assets(registry, use_llm=use_llm)
    logging.info("asset-gen: %s -> %d generated asset(s)", target.server, n_generated)
    table = build_static_table(
        registry, use_llm=use_llm, strict=use_llm, version=version, impact_mode=impact_mode
    )
    table["provenance"] = "llm-scan" if use_llm else "offline-baseline"
    table["server_kind"] = target.kind
    enrich_scan(table, registry.tools, use_llm=use_llm)
    return ScanResult(server=registry.server, kind=target.kind, table=table)


def scan_policy_target(
    target: Target, *, use_llm: bool, version: str, impact_mode: str = IMPACT_MODE
) -> ScanResult:
    """Scan one target with the policy document as its org description.

    Captured vendor catalogs go through :func:`scan_catalog_target`; everything
    else (filesystem tenants and declarative demo servers) goes through
    :func:`scan_server`, which builds demo tools from the declarative registry.
    ``impact_mode`` selects the scoring arm: the default drops the sensitivity
    primitive; ``five_level_v2_na`` keeps it (policy-derived sensitivity).
    """
    if target.catalog is not None:
        return scan_catalog_target(
            target, use_llm=use_llm, version=version, impact_mode=impact_mode
        )
    return scan_server(
        target.kind,
        root=target.root,
        server=target.server,
        by_file=target.kind == "filesystem",
        use_llm=use_llm,
        version=version,
        impact_mode=impact_mode,
        gen_assets=True,
        use_profile=True,
        profile_doc=POLICY_DOC,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default="scan-five_level_v2_policy")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--only", default=None,
        help="comma-separated output stems to scan (default: all 11)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="re-scan targets whose artifact already exists (default: skip them, so "
             "a resumed run never destroys completed work)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    selected = [t for t in TARGETS if wanted is None or t.stem in wanted]
    if wanted:
        unknown = wanted - {t.stem for t in TARGETS}
        if unknown:
            print(f"[FAIL] unknown target(s): {sorted(unknown)}")
            return 1

    rc = 0
    for target in selected:
        out_json = args.out_dir / f"{target.stem}.json"
        if out_json.exists() and not args.overwrite:
            print(f"[skip] {target.stem}: already scanned ({out_json}); --overwrite to redo")
            continue
        missing = next(
            (p for p in (target.root, target.catalog) if p is not None and not p.exists()), None
        )
        if missing:
            print(f"[skip] {target.stem}: missing input {missing}")
            continue
        try:
            result = scan_policy_target(target, use_llm=not args.no_llm, version=args.version_tag)
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        # Record which description document produced this artifact — the impact_mode
        # string alone cannot distinguish policy-grade from inventory-grade context.
        result.table["description_source"] = str(POLICY_DOC.relative_to(REPO_ROOT))
        out_json.write_text(json.dumps(result.table, indent=2), encoding="utf-8")
        (args.out_dir / f"{target.stem}.md").write_text(
            scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
        )
        (args.out_dir / f"{target.stem}_matrix.csv").write_text(
            matrix_csv(result.table), encoding="utf-8"
        )
        dist = result.table.get("band_distribution", {})
        print(f"[ok] {target.stem} ({result.server}): {result.n_tools} tools x "
              f"{result.n_assets} assets | score_max {result.table.get('score_max')} "
              f"| bands {dist} -> {out_json}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
