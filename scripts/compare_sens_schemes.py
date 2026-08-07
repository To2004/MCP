"""Grade each policy-scheme arm's derived sensitivity against the org's held-out numbers.

The three ``_real`` servers are the only ones where an inventory-grade profile
(``docs/mcp-tools/server-profiles.md``) states a per-asset sensitivity. That table
is never shown to the scanner: the policy document the scanner reads carries
classification classes and recognition rules but no numbers. So the profile table
is a held-out answer key, and the question this script answers is whether the
derived number lands on it -- once per sensitivity prompt scheme.

Arms compared (all identical except the asset-sensitivity prompt):

* ``nacombo``  -- our own register-shaped scheme (the baseline)
* ``sensiso``  -- ISO/IEC 27001 A.5.12 classification criteria
* ``sensnist`` -- FIPS 199 / SP 800-60 impact triple with a high-water mark
* ``senscis``  -- a coarse CIS-style scheme the arm must refine

Run:  uv run python scripts/compare_sens_schemes.py
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring.server_profiles import profile_for  # noqa: E402

V5 = REPO_ROOT / "reports" / "experiments" / "v5"
ARMS = {
    "nacombo": "our register scheme (baseline)",
    "sensiso": "ISO/IEC 27001 A.5.12",
    "sensnist": "FIPS 199 / SP 800-60",
    "senscis": "CIS-style coarse scheme",
}
SERVERS = {
    "calendar_real": "calendar:real",
    "github_real": "github:real",
    "slack_real": "slack:real",
}


def held_out_numbers(server: str) -> dict[str, int]:
    """The org's own per-asset sensitivity, from the inventory-grade profile."""
    return dict(profile_for(server).asset_sensitivity)


def grade(derived: dict[str, int], truth: dict[str, int]) -> dict[str, float] | None:
    """Exact / within-one / MAE / bias over the assets both sides name."""
    shared = sorted(set(derived) & set(truth))
    if not shared:
        return None
    diffs = [derived[a] - truth[a] for a in shared]
    return {
        "n": len(shared),
        "exact": 100 * sum(1 for d in diffs if d == 0) / len(diffs),
        "within1": 100 * sum(1 for d in diffs if abs(d) <= 1) / len(diffs),
        "mae": sum(abs(d) for d in diffs) / len(diffs),
        "bias": sum(diffs) / len(diffs),
        "derived_mean": st.mean(derived[a] for a in shared),
        "truth_mean": st.mean(truth[a] for a in shared),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None, help="also write a markdown report here")
    args = parser.parse_args(argv)

    lines: list[str] = []
    emit = lambda s="": (print(s), lines.append(s))  # noqa: E731

    emit(
        f"{'arm':<10}{'server':<16}{'n':>4}{'exact':>8}{'within1':>9}{'MAE':>7}{'bias':>7}"
        f"{'derived':>9}{'org':>7}"
    )
    pooled: dict[str, list[tuple[int, int]]] = {}
    for arm in ARMS:
        arm_dir = V5 / f"five_level_v2_policy_v5r_{arm}"
        for stem, server in SERVERS.items():
            path = arm_dir / f"{stem}.json"
            if not path.exists():
                emit(f"{arm:<10}{stem:<16}   (not finished)")
                continue
            derived = json.loads(path.read_text(encoding="utf-8"))["asset_sensitivity"]
            truth = held_out_numbers(server)
            g = grade(derived, truth)
            if g is None:
                emit(f"{arm:<10}{stem:<16}   (no shared asset ids)")
                continue
            for asset in set(derived) & set(truth):
                pooled.setdefault(arm, []).append((derived[asset], truth[asset]))
            emit(
                f"{arm:<10}{stem:<16}{g['n']:>4}{g['exact']:>7.0f}%{g['within1']:>8.0f}%"
                f"{g['mae']:>7.2f}{g['bias']:>+7.2f}{g['derived_mean']:>9.2f}{g['truth_mean']:>7.2f}"
            )

    emit()
    emit(f"{'arm':<10}{'scheme':<28}{'n':>4}{'exact':>8}{'within1':>9}{'MAE':>7}{'bias':>7}")
    for arm, label in ARMS.items():
        pairs = pooled.get(arm)
        if not pairs:
            emit(f"{arm:<10}{label:<28}   (incomplete)")
            continue
        diffs = [d - t for d, t in pairs]
        emit(
            f"{arm:<10}{label:<28}{len(diffs):>4}"
            f"{100 * sum(1 for x in diffs if x == 0) / len(diffs):>7.0f}%"
            f"{100 * sum(1 for x in diffs if abs(x) <= 1) / len(diffs):>8.0f}%"
            f"{sum(abs(x) for x in diffs) / len(diffs):>7.2f}"
            f"{sum(diffs) / len(diffs):>+7.2f}"
        )

    if args.out:
        args.out.write_text("```\n" + "\n".join(lines) + "\n```\n", encoding="utf-8")
        print(f"\nwrote {args.out.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
