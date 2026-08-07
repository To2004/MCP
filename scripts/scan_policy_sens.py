"""Derive per-asset sensitivity FROM the org policy (``five_level_v2_policy_sens``).

The policy experiment's sensitivity arm: the scan runs the normal
``five_level_v2_na`` scoring — the asset-sensitivity stage IS scored by the LLM —
but the registry carries ``docs/mcp-tools/server-policies.md`` as its org
description, so every stage (including sensitivity) sees the org's classification
policy, asset register, and recognition rules. The org supplies no numbers; the
model classifies each asset against the policy and maps the class's
adverse-impact language onto the rubric's 1-5 scale.

Comparison targets (see ``scripts/compare_policy_sensitivity.py``):

- no-context baseline: ``reports/experiments/v1/five_level_v2_fs/`` — same
  scoring mode, no org description at all;
- org ground truth: the per-asset table in ``docs/mcp-tools/server-profiles.md``.

Output goes to ``reports/experiments/staticscanner/``; existing artifacts are
skipped unless ``--overwrite`` is passed.

Run (GPU):  python scripts/scan_policy_sens.py --only calendar_real
Smoke:      python scripts/scan_policy_sens.py --no-llm --only calendar_real
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_security.scanner.render import matrix_csv, scan_to_markdown  # noqa: E402

from scripts.scan_policy_no_sens import POLICY_DOC, TARGETS, scan_policy_target  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "staticscanner"

IMPACT_MODE = "five_level_v2_na"  # sensitivity IS scored; the policy rides in every prompt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default="scan-five_level_v2_policy_sens")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--only", default=None,
        help="comma-separated output stems to scan (default: all 11 policy-doc servers)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="re-scan targets whose artifact already exists (default: skip them)",
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
            result = scan_policy_target(
                target, use_llm=not args.no_llm, version=args.version_tag,
                impact_mode=IMPACT_MODE,
            )
        except Exception as exc:  # noqa: BLE001 -- report which server failed, keep going
            print(f"[FAIL] {target.stem} ({target.server}): {exc}")
            rc = 1
            continue
        result.table["description_source"] = str(POLICY_DOC.relative_to(REPO_ROOT))
        out_json.write_text(json.dumps(result.table, indent=2), encoding="utf-8")
        (args.out_dir / f"{target.stem}.md").write_text(
            scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
        )
        (args.out_dir / f"{target.stem}_matrix.csv").write_text(
            matrix_csv(result.table), encoding="utf-8"
        )
        sens = result.table.get("asset_sensitivity", {})
        print(f"[ok] {target.stem} ({result.server}): {result.n_tools} tools x "
              f"{result.n_assets} assets | sens scored: {len(sens)} assets "
              f"| bands {result.table.get('band_distribution')} -> {out_json}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
