"""Score the v5 (policy-grade) arm against the organization and against v4.

Two questions, one report:

1. **Did the scanner recover the organization's own severities from policy text
   alone?** The v5 arm never sees a number: it classifies each register row
   against the classification policy and maps the class onto 1-5. The per-asset
   table in ``docs/mcp-tools/server-profiles.md`` is the held-out ground truth.
   Reported as mean absolute error, exact-match rate and within-one rate.

2. **What moved between v4 and v5?** Same tools, same asset ids, same blast
   rubric and the same deterministic assembly — so a difference is attributable
   to the two things that changed: where sensitivity came from, and whether tool
   impact was decided by rules or by the model.

Writes ``EVALUATION.md``, ``evaluation.json``, ``sensitivity_comparison.csv``,
``impact_comparison.csv`` and the cross-server ``ALL_SERVERS_summary.*`` into the
v5 experiment directory.

Run:  uv run python scripts/evaluate_policy_v5.py
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring.server_profiles import (  # noqa: E402
    parse_asset_table,
    profile_for,
)

V5_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5"
V4_DIR = REPO_ROOT / "reports" / "experiments" / "v4" / "five_level_v2_pure_v4"

STEM_TO_SERVER = {
    "calendar_real": "calendar:real",
    "github_real": "github:real",
    "slack_real": "slack:real",
}
BANDS = ("low", "medium", "high", "critical", "na")


def load_table(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ground_truth(server: str) -> dict[str, int]:
    """The organization's own per-asset sensitivity — never shown to the v5 scan."""
    return parse_asset_table(profile_for(server).text)


def sensitivity_stats(derived: dict[str, int], truth: dict[str, int]) -> dict:
    """MAE / exact / within-1 over the assets both tables cover."""
    shared = [asset for asset in derived if asset in truth]
    if not shared:
        return {"n": 0, "mae": None, "exact": None, "within_1": None}
    errors = [abs(derived[asset] - truth[asset]) for asset in shared]
    return {
        "n": len(shared),
        "mae": round(sum(errors) / len(errors), 3),
        "exact": round(sum(1 for e in errors if e == 0) / len(errors), 3),
        "within_1": round(sum(1 for e in errors if e <= 1) / len(errors), 3),
        "uncovered_assets": sorted(set(derived) - set(truth)),
    }


def score_sum(table: dict) -> float:
    """Σ of every scored cell — the server's total priced risk."""
    return round(
        sum(
            value
            for row in table["cells"].values()
            for value in row.values()
            if value is not None
        ),
        2,
    )


def blast_comparison(v5: dict, v4: dict | None) -> dict | None:
    """How many (tool, asset) blast cells moved between the arms, and which way.

    Both arms score the same tool and asset ids with the same rubric, so a moved
    cell is the model reading the same pair differently once the asset came from
    the policy register rather than the profile table. v4 measured 23-35 cells of
    run-to-run movement on this stage, so a count in that range is noise rather
    than a finding.
    """
    if v4 is None:
        return None
    shared = [key for key in v5["blast_radius"] if key in v4["blast_radius"]]
    moved = [(key, v4["blast_radius"][key], v5["blast_radius"][key]) for key in shared]
    changed = [item for item in moved if item[1] != item[2]]
    return {
        "cells": len(shared),
        "differing": len(changed),
        "became_na": sum(1 for _, a, b in changed if b is None and a is not None),
        "left_na": sum(1 for _, a, b in changed if a is None and b is not None),
        "raised": sum(1 for _, a, b in changed if a is not None and b is not None and b > a),
        "lowered": sum(1 for _, a, b in changed if a is not None and b is not None and b < a),
    }


def impact_rows(v5: dict, v4: dict | None) -> list[dict]:
    """Per-tool impact, its v5 provenance, and the v4 model's answer beside it."""
    sources = v5.get("tool_impact_source", {})
    statics = v5.get("static_impacts", {})
    rows = []
    for tool, impact in sorted(v5["tool_impact"].items()):
        record = statics.get(tool, {})
        rows.append(
            {
                "tool": tool,
                "v5_impact": impact,
                "v5_source": sources.get(tool, "llm"),
                "v5_static_confidence": record.get("confidence"),
                "v5_evidence": "; ".join(record.get("evidence", [])),
                "v4_impact": (v4 or {}).get("tool_impact", {}).get(tool),
            }
        )
    return rows


def sensitivity_rows(v5: dict, truth: dict[str, int], v4: dict | None) -> list[dict]:
    """Per-asset derived sensitivity against the org's number and v4's."""
    derived = v5.get("asset_sensitivity", {})
    v4_sens = (v4 or {}).get("asset_sensitivity", {})
    rows = []
    for asset in v5["asset_ids"]:
        org = truth.get(asset)
        got = derived.get(asset)
        rows.append(
            {
                "asset": asset,
                "org_truth": org,
                "v5_derived": got,
                "error": None if org is None or got is None else got - org,
                "v4_from_table": v4_sens.get(asset),
                # The artifact stores flags already stripped of their `flag:` prefix.
                "flags": ",".join(v5.get("asset_flags", {}).get(asset, [])),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _md_table(rows: list[dict], columns: list[str]) -> str:
    head = "| " + " | ".join(columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    body = [
        "| " + " | ".join("" if row.get(c) is None else str(row.get(c)) for c in columns) + " |"
        for row in rows
    ]
    return "\n".join([head, rule, *body])


def evaluate(stem: str, v5_dir: Path, v4_dir: Path) -> dict | None:
    """Everything measured for one server, or None when its v5 artifact is absent."""
    v5_path = v5_dir / f"{stem}.json"
    if not v5_path.exists():
        return None
    v5 = load_table(v5_path)
    v4_path = v4_dir / f"{stem}.json"
    v4 = load_table(v4_path) if v4_path.exists() else None
    truth = ground_truth(STEM_TO_SERVER[stem])

    sens_rows = sensitivity_rows(v5, truth, v4)
    imp_rows = impact_rows(v5, v4)
    sources = v5.get("tool_impact_source", {})
    impact_agree = [
        row for row in imp_rows if row["v4_impact"] is not None and row["v4_impact"] == row["v5_impact"]
    ]
    comparable = [row for row in imp_rows if row["v4_impact"] is not None]
    return {
        "stem": stem,
        "server": v5["server"],
        "n_tools": len(v5["tool_impact"]),
        "n_assets": len(v5["asset_ids"]),
        "sensitivity": sensitivity_stats(
            {k: v for k, v in v5.get("asset_sensitivity", {}).items()}, truth
        ),
        "impact_source": {
            "static_ladder": sum(1 for s in sources.values() if s == "static_ladder"),
            "llm_fallback": sum(1 for s in sources.values() if s == "llm_fallback"),
        },
        "impact_vs_v4": {
            "comparable": len(comparable),
            "agree": len(impact_agree),
            "disagree": [
                {"tool": r["tool"], "v5": r["v5_impact"], "v4": r["v4_impact"]}
                for r in comparable
                if r["v4_impact"] != r["v5_impact"]
            ],
        },
        "blast_vs_v4": blast_comparison(v5, v4),
        "bands_v5": {band: v5["band_distribution"].get(band, 0) for band in BANDS},
        "bands_v4": (
            {band: v4["band_distribution"].get(band, 0) for band in BANDS} if v4 else None
        ),
        "score_sum_v5": score_sum(v5),
        "score_sum_v4": score_sum(v4) if v4 else None,
        "blast_floor_raised": v5["blast_floor"].get("raised_cells"),
        "blast_roof_capped": v5["blast_roof"].get("capped_cells"),
        "uncovered_tools": v5.get("uncovered_tools", []),
        "unmapped_tools": v5.get("policy_register_unmapped_tools", []),
        "_sens_rows": sens_rows,
        "_impact_rows": imp_rows,
    }


def render_markdown(results: list[dict]) -> str:
    """The per-server EVALUATION.md body."""
    out = [
        "# v5 evaluation — did policy text alone recover the organization's severities?",
        "",
        "The v5 scan reads a policy that contains **no sensitivity number anywhere**. It",
        "classifies each asset-register row against the classification table and maps the",
        "class's adverse-impact language onto 1-5. The per-asset table in",
        "`docs/mcp-tools/server-profiles.md` is held out and used here as ground truth.",
        "",
        "Generated by `scripts/evaluate_policy_v5.py` — do not hand-edit.",
        "",
        "## Sensitivity accuracy vs the organization's own numbers",
        "",
        _md_table(
            [
                {
                    "server": r["stem"],
                    "assets": r["sensitivity"]["n"],
                    "MAE": r["sensitivity"]["mae"],
                    "exact": f"{(r['sensitivity']['exact'] or 0) * 100:.0f}%",
                    "within 1": f"{(r['sensitivity']['within_1'] or 0) * 100:.0f}%",
                }
                for r in results
            ],
            ["server", "assets", "MAE", "exact", "within 1"],
        ),
        "",
        "## Tool impact — who decided, and does it match v4's model?",
        "",
        _md_table(
            [
                {
                    "server": r["stem"],
                    "tools": r["n_tools"],
                    "static ladder": r["impact_source"]["static_ladder"],
                    "LLM fallback": r["impact_source"]["llm_fallback"],
                    "agree with v4": f"{r['impact_vs_v4']['agree']}/{r['impact_vs_v4']['comparable']}",
                }
                for r in results
            ],
            ["server", "tools", "static ladder", "LLM fallback", "agree with v4"],
        ),
        "",
        "## Blast radius — how many cells moved between the arms",
        "",
        "Same tool ids, same asset ids, same rubric and the same assembly. v4",
        "measured 23-35 cells of run-to-run movement on this stage with the prompt",
        "held fixed, so a count in that range is this stage's own variance rather",
        "than an effect of the policy inputs.",
        "",
        _md_table(
            [
                {
                    "server": r["stem"],
                    "cells": r["blast_vs_v4"]["cells"],
                    "differing": r["blast_vs_v4"]["differing"],
                    "raised": r["blast_vs_v4"]["raised"],
                    "lowered": r["blast_vs_v4"]["lowered"],
                    "became N/A": r["blast_vs_v4"]["became_na"],
                    "left N/A": r["blast_vs_v4"]["left_na"],
                }
                for r in results
                if r["blast_vs_v4"]
            ],
            ["server", "cells", "differing", "raised", "lowered", "became N/A", "left N/A"],
        ),
        "",
        "## Severity totals, v4 vs v5",
        "",
        _md_table(
            [
                {
                    "server": r["stem"],
                    "arm": arm,
                    **{band: (bands or {}).get(band, "") for band in BANDS},
                    "Σ score": total,
                }
                for r in results
                for arm, bands, total in (
                    ("v4 (inventory)", r["bands_v4"], r["score_sum_v4"]),
                    ("v5 (policy)", r["bands_v5"], r["score_sum_v5"]),
                )
                if bands is not None
            ],
            ["server", "arm", *BANDS, "Σ score"],
        ),
        "",
    ]
    for r in results:
        out += [
            f"## {r['stem']} — per-asset sensitivity",
            "",
            _md_table(
                r["_sens_rows"],
                ["asset", "org_truth", "v5_derived", "error", "v4_from_table", "flags"],
            ),
            "",
        ]
        misses = [row for row in r["_sens_rows"] if row["error"] not in (0, None)]
        if misses:
            out += [
                "Misses: "
                + ", ".join(
                    f"`{row['asset']}` {row['v5_derived']} vs {row['org_truth']}"
                    for row in misses
                ),
                "",
            ]
        disagreements = r["impact_vs_v4"]["disagree"]
        if disagreements:
            out += [
                f"### {r['stem']} — tool impact differing from v4",
                "",
                _md_table(disagreements, ["tool", "v5", "v4"]),
                "",
            ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v5-dir", type=Path, default=V5_DIR)
    parser.add_argument("--v4-dir", type=Path, default=V4_DIR)
    args = parser.parse_args(argv)

    results = [
        result
        for stem in STEM_TO_SERVER
        if (result := evaluate(stem, args.v5_dir, args.v4_dir)) is not None
    ]
    if not results:
        print(f"[FAIL] no v5 artifacts in {args.v5_dir}")
        return 1

    args.v5_dir.mkdir(parents=True, exist_ok=True)
    (args.v5_dir / "EVALUATION.md").write_text(render_markdown(results), encoding="utf-8")
    payload = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
    (args.v5_dir / "evaluation.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    write_csv(
        args.v5_dir / "sensitivity_comparison.csv",
        [{"server": r["stem"], **row} for r in results for row in r["_sens_rows"]],
    )
    write_csv(
        args.v5_dir / "impact_comparison.csv",
        [{"server": r["stem"], **row} for r in results for row in r["_impact_rows"]],
    )
    write_csv(
        args.v5_dir / "ALL_SERVERS_summary.csv",
        [
            {
                "server": r["stem"],
                "tools": r["n_tools"],
                "assets": r["n_assets"],
                "sens_mae": r["sensitivity"]["mae"],
                "sens_exact": r["sensitivity"]["exact"],
                "sens_within_1": r["sensitivity"]["within_1"],
                "impact_static": r["impact_source"]["static_ladder"],
                "impact_llm_fallback": r["impact_source"]["llm_fallback"],
                "impact_agree_v4": r["impact_vs_v4"]["agree"],
                "impact_comparable_v4": r["impact_vs_v4"]["comparable"],
                **{f"band_{b}": r["bands_v5"][b] for b in BANDS},
                "score_sum_v5": r["score_sum_v5"],
                "score_sum_v4": r["score_sum_v4"],
                "blast_floor_raised": r["blast_floor_raised"],
                "blast_roof_capped": r["blast_roof_capped"],
            }
            for r in results
        ],
    )
    for r in results:
        stats = r["sensitivity"]
        print(
            f"[ok] {r['stem']}: sens MAE {stats['mae']} | exact "
            f"{(stats['exact'] or 0) * 100:.0f}% | within-1 {(stats['within_1'] or 0) * 100:.0f}% "
            f"| impact static {r['impact_source']['static_ladder']}/{r['n_tools']} "
            f"| Σ v5 {r['score_sum_v5']} vs v4 {r['score_sum_v4']}"
        )
    print(f"\nwrote EVALUATION.md, evaluation.json and 3 CSVs to {args.v5_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
