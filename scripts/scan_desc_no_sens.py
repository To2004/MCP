"""Scan every LLM-scannable MCP server under the ``five_level_v2_desc`` rubric.

Two changes versus the ``five_level_v2_na`` runs in
``reports/experiments/v1/five_level_v2_fs/``:

1. **The organization's written description is read first.** Each server's profile
   from ``docs/mcp-tools/server-profiles.md`` (owning company, expected agent use,
   per-asset severity and CIA emphasis) is put in front of *every* scoring stage —
   domain inference, tool impact, blast radius and baselines.
2. **Asset sensitivity is removed.** No sensitivity primitive is scored; the cell
   is ``blast x impact`` (score_max 25) and bands come from
   :func:`~mcp_security.static_scoring.pipeline.band_label_no_sens`. How much an
   asset is worth comes from the description instead of a derived 1-5 number.

Targets are the 13 servers the LLM scanner can reach: 5 filesystem tenants, 2
sqlite databases, and the demo + real catalogs for github, slack and calendar.
The 5 finance servers are deterministic-only scans (no asset matrix), so they are
out of scope here — see ``scripts/scan_finance.py``.

Output goes to a NEW directory (``reports/experiments/v2/five_level_v2_desc/``) and
the script refuses to clobber an existing artifact unless ``--overwrite`` is
passed, so previous experiments stay intact.

Run (GPU):  python scripts/scan_desc_no_sens.py
Smoke:      python scripts/scan_desc_no_sens.py --no-llm --only fs_corp_filesystem
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
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v2" / "five_level_v2_desc"

IMPACT_MODE = "five_level_v2_desc"


@dataclass(frozen=True)
class Target:
    """One server to scan: how to build its registry and what to call the output.

    ``root`` is the on-disk store for disk-backed kinds; ``catalog`` is a captured
    ``tools/list`` for the real vendor catalogs. Exactly one of them is set, or
    neither for a declarative demo server whose tools come from the registry.
    """

    stem: str  # output file stem, matching the profile-doc section name
    kind: str
    server: str  # server id — also the key used to look up the org profile
    root: Path | None = None
    catalog: Path | None = None
    by_file: bool = False


# The 13 LLM-scannable servers, in the order of docs/mcp-tools/server-profiles.md.
TARGETS: tuple[Target, ...] = (
    # 5 filesystem tenants — identical 14-tool surface, different organization.
    Target("fs_fintech_fs", "filesystem", "fs:fintech_fs", root=DEMO / "fintech_fs", by_file=True),
    Target("fs_medical_clinic_fs", "filesystem", "fs:medical_clinic_fs",
           root=DEMO / "medical_clinic_fs", by_file=True),
    Target("fs_corp_filesystem", "filesystem", "fs:corp_filesystem",
           root=DEMO / "corp_filesystem", by_file=True),
    Target("fs_law_firm_fs", "filesystem", "fs:law_firm_fs",
           root=DEMO / "law_firm_fs", by_file=True),
    Target("fs_media_studio_fs", "filesystem", "fs:media_studio_fs",
           root=DEMO / "media_studio_fs", by_file=True),
    # source code / messaging / calendar — real vendor catalogs and demo catalogs.
    Target("github_real", "github", "github:real", catalog=TOOL_LISTS / "github_real.json"),
    Target("github_cbg", "github", "github:cbg"),
    Target("slack_real", "slack", "slack:real", catalog=TOOL_LISTS / "slack_real.json"),
    Target("slack_cbg", "slack", "slack:cbg"),
    Target("calendar_real", "calendar", "calendar:real",
           catalog=TOOL_LISTS / "calendar_real.json"),
    Target("calendar_cbg", "calendar", "calendar:cbg"),
    # 2 sqlite databases.
    Target("sqlite_devops_sqlite", "sqlite", "sqlite:devops_sqlite",
           root=DEMO / "devops_sqlite" / "devops.db"),
    Target("sqlite_cbg_sqlite", "sqlite", "sqlite:cbg_sqlite",
           root=DEMO / "cbg_sqlite" / "cbg.db"),
)

_DECLARATIVE_LOADERS = {
    "github": reg.load_github_registry,
    "slack": reg.load_slack_registry,
    "calendar": reg.load_calendar_registry,
}


def scan_catalog_target(
    target: Target, *, use_llm: bool, version: str, impact_mode: str = IMPACT_MODE
) -> ScanResult:
    """Scan a captured vendor catalog (real tools x the kind's asset scopes)."""
    base = _DECLARATIVE_LOADERS[target.kind]()
    registry = ServerRegistry(
        server=target.server,
        kind=target.kind,
        tools=load_tool_list(target.kind, path=target.catalog),
        assets=base.assets,
        apps=base.apps,
        description=attach_profile(target.server),
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


def scan_target(
    target: Target, *, use_llm: bool, version: str, impact_mode: str = IMPACT_MODE
) -> ScanResult:
    """Scan one target with the org profile attached (description-driven modes)."""
    if target.catalog is not None:
        return scan_catalog_target(
            target, use_llm=use_llm, version=version, impact_mode=impact_mode
        )
    return scan_server(
        target.kind,
        root=target.root,
        server=target.server,
        by_file=target.by_file,
        use_llm=use_llm,
        version=version,
        impact_mode=impact_mode,
        gen_assets=True,
        use_profile=True,
    )


def _missing_input(target: Target) -> str | None:
    """The missing input path for ``target``, or None when it is scannable."""
    for path in (target.root, target.catalog):
        if path is not None and not path.exists():
            return str(path)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default=f"scan-{IMPACT_MODE}")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--only", default=None,
        help="comma-separated output stems to scan (default: all 13)",
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
        missing = _missing_input(target)
        if missing:
            print(f"[skip] {target.stem}: missing input {missing}")
            continue
        try:
            result = scan_target(target, use_llm=not args.no_llm, version=args.version_tag)
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        # Write under the profile-doc stem so artifacts line up 1:1 with the profiles.
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
