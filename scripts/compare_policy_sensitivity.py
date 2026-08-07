"""Compare policy-derived asset sensitivity against the baselines.

Three columns per asset:

- **org** — the organization's own 1-5 from the per-asset table in
  ``docs/mcp-tools/server-profiles.md`` (ground truth; never seen by either scan);
- **no-ctx** — the LLM's sensitivity with NO org context
  (``reports/experiments/v1/five_level_v2_fs/``, mode ``five_level_v2_na``);
- **policy** — the LLM's sensitivity with the policy document as context
  (``reports/experiments/staticscanner/``, same mode).

Reports per-asset values plus, for each arm vs the org ground truth: mean
absolute error, exact-match rate, and within-1 rate. The question: does
policy-grade context move the model's sensitivity toward the org's own
judgement, relative to no context at all?

Run:  python scripts/compare_policy_sensitivity.py --stem calendar_real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_security.static_scoring.server_profiles import profile_for  # noqa: E402

BASELINE_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_fs"
POLICY_DIR = REPO_ROOT / "reports" / "experiments" / "staticscanner"

# Scan stems whose profile-doc section name differs from the server id.
_STEM_TO_SERVER = {
    "fs_fintech_fs": "fs:fintech_fs",
    "fs_medical_clinic_fs": "fs:medical_clinic_fs",
    "fs_corp_filesystem": "fs:corp_filesystem",
    "fs_law_firm_fs": "fs:law_firm_fs",
    "fs_media_studio_fs": "fs:media_studio_fs",
    "github_real": "github:real",
    "github_cbg": "github:cbg",
    "slack_real": "slack:real",
    "slack_cbg": "slack:cbg",
    "calendar_real": "calendar:real",
    "calendar_cbg": "calendar:cbg",
}


def _load_sens(path: Path) -> dict[str, int]:
    table = json.loads(path.read_text(encoding="utf-8"))
    sens = table.get("asset_sensitivity") or {}
    if not sens:
        raise SystemExit(f"{path}: artifact carries no asset_sensitivity")
    return {k: int(v) for k, v in sens.items()}


def _stats(pred: dict[str, int], truth: dict[str, int]) -> tuple[float, float, float, int]:
    keys = [k for k in truth if k in pred]
    if not keys:
        return float("nan"), 0.0, 0.0, 0
    errs = [abs(pred[k] - truth[k]) for k in keys]
    mae = sum(errs) / len(errs)
    exact = sum(e == 0 for e in errs) / len(errs)
    within1 = sum(e <= 1 for e in errs) / len(errs)
    return mae, exact, within1, len(keys)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stem", default="calendar_real", help="scan stem to compare")
    parser.add_argument("--baseline-dir", type=Path, default=BASELINE_DIR)
    parser.add_argument("--policy-dir", type=Path, default=POLICY_DIR)
    args = parser.parse_args(argv)

    truth = profile_for(_STEM_TO_SERVER.get(args.stem, args.stem)).asset_sensitivity
    baseline = _load_sens(args.baseline_dir / f"{args.stem}.json")
    policy = _load_sens(args.policy_dir / f"{args.stem}.json")

    assets = sorted(set(truth) | set(baseline) | set(policy))
    print(f"asset sensitivity — {args.stem} (org = profile ground truth, never shown to a scan)\n")
    print(f"{'asset':34s} {'org':>4s} {'no-ctx':>7s} {'policy':>7s}")
    for a in assets:
        fmt = lambda d: str(d[a]) if a in d else "-"  # noqa: E731
        marks = ""
        if a in truth and a in policy and a in baseline:
            db, dp = abs(baseline[a] - truth[a]), abs(policy[a] - truth[a])
            marks = "  improved" if dp < db else ("  worse" if dp > db else "")
        print(f"{a:34s} {fmt(truth):>4s} {fmt(baseline):>7s} {fmt(policy):>7s}{marks}")

    print()
    for name, pred in (("no-ctx", baseline), ("policy", policy)):
        mae, exact, within1, n = _stats(pred, truth)
        print(f"{name:>7s} vs org: n={n}  MAE={mae:.2f}  exact={exact:.0%}  within-1={within1:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
