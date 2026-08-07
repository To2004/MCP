"""Scan the four real servers under the ``five_level_v2_ult`` rubric.

The "ultimate" mode combines the winners of the blast-radius experiments and
their judge-panel reviews:

1. **Org description everywhere** (from the desc experiment): each server's
   profile from ``docs/mcp-tools/server-profiles.md`` fronts every LLM stage.
2. **Sensitivity from the org's own table** — the profile's per-asset
   ``| Asset | Sens. | C | I | A | Why |`` rows are the sensitivity primitive:
   logged, deterministic, challengeable. No LLM sensitivity stage runs, and a
   registry asset without a row aborts the scan
   (:class:`~mcp_security.static_scoring.pipeline.ProfileCoverageError`).
3. **Gated blast floor** (the floor-gated experiment, folded into assembly):
   mutations (impact >= 4) on sens-4/5 assets are floored to blast 3/4; the
   model's verbatim blast is preserved as ``blast_radius_raw``.
4. **Alias-twin pass**: a tool whose description says "DEPRECATED: Use X" gets,
   per asset, the max blast of itself and X (closes read_file vs read_text_file
   arbitrage).
5. **band_label_v5**: the 5-level ladder's deterministic band floors,
   sensitivity-aware (destruction never low; wallpaper never critical).

Formula: sensitivity x blast x impact, score_max 125.

Run (GPU):  python scripts/scan_ultimate.py
Pre-flight: python scripts/scan_ultimate.py --check-profiles
Smoke:      python scripts/scan_ultimate.py --no-llm --only fs_corp_filesystem
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from mcp_security.scanner.render import matrix_csv, scan_to_markdown
from mcp_security.static_scoring.server_profiles import (
    missing_asset_rows,
    profile_for,
)

from scan_desc_no_sens import TARGETS as DESC_TARGETS
from scan_desc_no_sens import Target, _missing_input, scan_target

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v2" / "five_level_v2_ult"

IMPACT_MODE = "five_level_v2_ult"
# Ablation arms (see pipeline._ULT_VARIANT_OPTIONS): each varies one prompt-
# context lever over the same profile-sensitivity machinery.
MODES = (
    "five_level_v2_ult",
    "five_level_v2_ult_tools",  # full tool registry in every impact/blast prompt
    "five_level_v2_ult_leanimp",  # org description withheld from the impact stage
    "five_level_v2_ult_struct",  # structured-only profile view (table + CIA line)
)
# The four real servers (user-selected scope), reusing the desc driver's targets.
_ULT_STEMS = ("calendar_real", "slack_real", "github_real", "fs_corp_filesystem")
TARGETS: tuple[Target, ...] = tuple(t for t in DESC_TARGETS if t.stem in _ULT_STEMS)


def check_profiles(targets: tuple[Target, ...]) -> int:
    """Pre-flight: every target has a parsable table covering its curated assets.

    Generated homing assets are only known at scan time (the pipeline enforces
    them); this check catches missing CURATED rows before a GPU job is spent.
    Coverage is checked against the last known asset list in any existing scan
    artifact for the stem (desc experiment), falling back to table-only parse.
    """
    rc = 0
    known_ids_dir = REPO_ROOT / "reports" / "experiments" / "v2" / "five_level_v2_desc"
    for target in targets:
        try:
            table = profile_for(target.server).asset_sensitivity
        except Exception as exc:  # noqa: BLE001 -- report and continue to next target
            print(f"[FAIL] {target.stem}: {exc}")
            rc = 1
            continue
        prior = known_ids_dir / f"{target.stem}.json"
        if prior.exists():
            ids = json.loads(prior.read_text(encoding="utf-8")).get("asset_ids", [])
            missing = missing_asset_rows(table, ids)
            if missing:
                print(f"[FAIL] {target.stem}: table lacks rows for known assets: {missing}")
                rc = 1
                continue
        print(f"[ok] {target.stem}: {len(table)} asset rows parsed")
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument(
        "--impact-mode",
        default=IMPACT_MODE,
        choices=MODES,
        help="ult arm to scan (default: the base five_level_v2_ult)",
    )
    parser.add_argument("--version-tag", default=None, help="default: scan-<impact-mode>")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="default: reports/experiments/<impact-mode>",
    )
    parser.add_argument(
        "--only", default=None, help="comma-separated output stems to scan (default: all 4)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="re-scan targets whose artifact already exists (default: skip them)",
    )
    parser.add_argument(
        "--check-profiles",
        action="store_true",
        help="only verify the org profiles' asset tables parse and cover known assets",
    )
    args = parser.parse_args(argv)
    version_tag = args.version_tag or f"scan-{args.impact_mode}"
    out_dir = args.out_dir or (REPO_ROOT / "reports" / "experiments" / "v2" / args.impact_mode)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    selected = tuple(t for t in TARGETS if wanted is None or t.stem in wanted)
    if wanted:
        unknown = wanted - {t.stem for t in TARGETS}
        if unknown:
            print(f"[FAIL] unknown target(s): {sorted(unknown)}; choose from {_ULT_STEMS}")
            return 1

    # Pre-flight always runs; --check-profiles stops after it.
    rc = check_profiles(selected)
    if args.check_profiles:
        return rc
    if rc:
        print("[FAIL] profile pre-flight failed; fix the tables before scanning")
        return rc

    out_dir.mkdir(parents=True, exist_ok=True)
    for target in selected:
        out_json = out_dir / f"{target.stem}.json"
        if out_json.exists() and not args.overwrite:
            print(f"[skip] {target.stem}: already scanned ({out_json}); --overwrite to redo")
            continue
        missing = _missing_input(target)
        if missing:
            print(f"[skip] {target.stem}: missing input {missing}")
            continue
        try:
            result = scan_target(
                target,
                use_llm=not args.no_llm,
                version=version_tag,
                impact_mode=args.impact_mode,
            )
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        out_json.write_text(json.dumps(result.table, indent=2), encoding="utf-8")
        (out_dir / f"{target.stem}.md").write_text(
            scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
        )
        (out_dir / f"{target.stem}_matrix.csv").write_text(
            matrix_csv(result.table), encoding="utf-8"
        )
        table = result.table
        print(
            f"[ok] {target.stem} ({result.server}): {result.n_tools} tools x "
            f"{result.n_assets} assets | score_max {table.get('score_max')} "
            f"| floored {table.get('blast_floor', {}).get('raised_cells')} "
            f"| alias fixups {len(table.get('alias_fixups', []))} "
            f"| bands {table.get('band_distribution', {})} -> {out_json}"
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
