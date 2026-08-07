"""Attribute the score gap between two scan arms to impact vs blast.

Two arms that agree on almost every tool impact can still produce different risk
matrices, because a cell is ``sensitivity x blast x impact`` and the deterministic
passes (impact-keyed floors, roofs, bulk dominance) couple the two axes. This
script separates the causes by swapping one input at a time:

    A  arm-A impact + arm-A blast      (arm A as published)
    B  arm-B impact + arm-B blast      (arm B as published)
    C  arm-B impact + arm-A blast      (only impact swapped)
    D  arm-A impact + arm-B blast      (only blast swapped)

A->C isolates the impact axis; A->D isolates the blast axis. Everything is
replayed from the stored artifacts — no model call.

    uv run python scripts/decompose_arm_gap.py
    uv run python scripts/decompose_arm_gap.py --arm-a five_level_v2_pure_v4_bulkclause
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scan_pure_desc import SCHEMES, TARGETS, build_pure_registry  # noqa: E402

from mcp_security.scanner.tool_list import load_tool_list  # noqa: E402
from mcp_security.static_scoring import pipeline as P  # noqa: E402
from mcp_security.static_scoring.server_profiles import profile_for  # noqa: E402

EXP = REPO_ROOT / "reports" / "experiments" / "v4"
IMPACT_MODE = "five_level_v2_v4_static"  # assembly is identical across the arms


def _assemble(registry, impacts: dict, blast_raw: dict, meta: dict) -> dict:
    """Run the pipeline's deterministic assembly on a given (impact, blast) pair."""
    P.StaticScorer.infer_domain = lambda self: dict(meta["inferred_profile"])
    P.StaticScorer.build_baselines = lambda self: dict(meta["baselines"])
    P.StaticScorer.score_tools = lambda self: dict(impacts)
    P.StaticScorer.score_blast = lambda self, sensitivity: dict(blast_raw)  # noqa: ARG005
    return P.build_static_table(
        registry, use_llm=False, strict=False, version="decompose", impact_mode=IMPACT_MODE
    )


def _total(table: dict) -> float:
    return sum(v for row in table["cells"].values() for v in row.values() if v is not None)


def _fmt(table: dict) -> str:
    b = table["band_distribution"]
    return (
        f"Σ{_total(table):7.0f}  low {b.get('low', 0):3d} med {b.get('medium', 0):3d} "
        f"high {b.get('high', 0):3d} crit {b.get('critical', 0):3d}"
    )


def decompose(stem: str, arm_a: str, arm_b: str) -> None:
    a = json.loads((EXP / arm_a / f"{stem}.json").read_text(encoding="utf-8"))
    b = json.loads((EXP / arm_b / f"{stem}.json").read_text(encoding="utf-8"))
    target = next(t for t in TARGETS if t.stem == stem)

    raw = profile_for(target.server)
    profile = replace(raw, text=SCHEMES[a.get("desc_scheme", "full")](raw.text))
    registry = build_pure_registry(
        profile, load_tool_list(target.kind, path=target.catalog), target.kind
    )

    ia, ib = a["tool_impact_raw"], b["tool_impact_raw"]
    ba, bb = a["blast_radius_raw"], b["blast_radius_raw"]
    combos = {
        f"A  {arm_a}": _assemble(registry, ia, ba, a),
        f"B  {arm_b}": _assemble(registry, ib, bb, b),
        "C  B-impact + A-blast (impact swapped)": _assemble(registry, ib, ba, a),
        "D  A-impact + B-blast (blast swapped)": _assemble(registry, ia, bb, a),
    }
    print(f"\n{stem}")
    for label, table in combos.items():
        print(f"  {label:42s} {_fmt(table)}")
    ta, tb = _total(combos[f"A  {arm_a}"]), _total(combos[f"B  {arm_b}"])
    tc, td = (
        _total(combos["C  B-impact + A-blast (impact swapped)"]),
        _total(combos["D  A-impact + B-blast (blast swapped)"]),
    )
    gap = tb - ta
    print(
        f"  {'total gap B-A':42s} {gap:+8.0f}   "
        f"impact alone {tc - ta:+7.0f}   blast alone {td - ta:+7.0f}   "
        f"interaction {gap - (tc - ta) - (td - ta):+7.0f}"
    )
    n_i = sum(1 for k in ia if ib.get(k) != ia[k])
    n_b = sum(1 for k in ba if k in bb and ba[k] != bb[k])
    print(f"  {'inputs differing':42s} impacts {n_i}/{len(ia)}   blast cells {n_b}/{len(ba)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-a", default="five_level_v2_pure_v4_bulkclause")
    parser.add_argument("--arm-b", default="five_level_v2_pure_v4static")
    parser.add_argument("--only", default=None, help="comma-separated stems")
    args = parser.parse_args(argv)

    wanted = {s.strip() for s in args.only.split(",")} if args.only else None
    for target in TARGETS:
        if wanted and target.stem not in wanted:
            continue
        if not all(
            (EXP / arm / f"{target.stem}.json").exists() for arm in (args.arm_a, args.arm_b)
        ):
            print(f"[skip] {target.stem}: missing in one arm")
            continue
        decompose(target.stem, args.arm_a, args.arm_b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
