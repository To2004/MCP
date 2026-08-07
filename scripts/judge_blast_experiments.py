"""LLM-as-judge ranking of the blast-radius experiments.

An independent judge (same local model, blinded) re-derives BLAST RADIUS for
every cell the baseline scan scored, from the domain profile, the shared
five_level_v2 blast rules, and the (tool, asset) descriptions ALONE — it never
sees any experiment's answer, so agreement is anchor-free (the same protocol as
the evaluation-only judge in the pipeline). Each experiment is then graded by
how well its blast values agree with the judge's:

- exact agreement and within-1 agreement (percent of judged cells),
- MAE (mean absolute error vs the judged value),
- signed bias (experiment minus judge: negative = under-scores reach),

overall AND on two subsets: the OFFENDER cells that motivated the experiments
(mutating tools, impact >= 4, on sensitive assets, sensitivity >= 4, baseline
blast <= 2) and the complementary control cells — so a fix that inflates the
rest of the matrix is penalized where it over-shoots, not just rewarded where
it repairs.

Run on a GPU node (one judge call per scored baseline cell):
    python scripts/judge_blast_experiments.py
    (writes reports/experiments/five_level_v2_judge/judged_blast.csv
     and reports/experiments/blast_experiments_judged.md)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring import prompts

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = REPO_ROOT / "reports" / "experiments"
BASELINE_DIR = EXP_ROOT / "v1" / "five_level_v2_fs"
OUT_DIR = EXP_ROOT / "v1" / "five_level_v2_judge"
SERVERS = ("calendar_real", "slack_real", "fs_corp")

# experiment label -> (dir, file pattern). Baseline is graded too — the control.
EXPERIMENTS = {
    "baseline": ("v1/five_level_v2_fs", "{stem}.json"),
    "ctx": ("v1/five_level_v2_ctx", "{stem}.json"),
    "floor-plain": ("v1/five_level_v2_floor", "{stem}_plain.json"),
    "floor-gated": ("v1/five_level_v2_floor", "{stem}_gated.json"),
    "rowfix": ("v1/five_level_v2_rowfix", "{stem}.json"),
}


def load_descriptions(stem: str) -> tuple[dict[str, str], dict[str, str]]:
    """(tool -> description, asset -> description) from the baseline scores CSV."""
    tools: dict[str, str] = {}
    assets: dict[str, str] = {}
    with (BASELINE_DIR / f"{stem}_scores.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            tools.setdefault(row["tool"], row["tool_description"])
            assets.setdefault(row["asset"], row["asset_description"])
    return tools, assets


def is_offender(baseline: dict, tool: str, asset: str) -> bool:
    blast = baseline["blast_radius"].get(f"{tool}|{asset}")
    return (
        blast is not None
        and blast <= 2
        and baseline["tool_impact"][tool] >= 4
        and baseline["asset_sensitivity"][asset] >= 4
    )


def judge_cell(profile_json: str, tool_item: dict, asset_item: dict) -> int | None:
    """One blinded judge verdict: the correct blast for this pair, or None.

    None covers both an unusable model answer and a judged N/A (the judge deems
    the pair unaffected) — either way the cell is excluded from agreement.
    """
    prompt = (
        prompts.JUDGE_SYSTEM.format(
            domain_profile=profile_json, scoring_rules=prompts.BLAST_TASK_NA
        )
        + "\n\n"
        + prompts.JUDGE_USER.format(
            field_name="blast_radius",
            item_key=f"{tool_item['name']}|{asset_item['asset_id']}",
            item_json=json.dumps({"tool": tool_item, "asset": asset_item}, indent=2),
        )
    )
    result = query_ollama(prompt)
    if not isinstance(result, dict):
        return None
    try:
        value = int(result.get("judged_value"))
    except (TypeError, ValueError):
        return None
    return max(1, min(5, value))


def metrics(rows: list[dict], label: str, subset) -> dict | None:
    """Agreement of one experiment's blast with the judge over ``subset`` rows."""
    pairs = [
        (r[label], r["judged"])
        for r in rows
        if subset(r) and r["judged"] is not None and r.get(label) is not None
    ]
    if not pairs:
        return None
    n = len(pairs)
    return {
        "n": n,
        "exact": sum(1 for e, j in pairs if e == j) / n,
        "within1": sum(1 for e, j in pairs if abs(e - j) <= 1) / n,
        "mae": sum(abs(e - j) for e, j in pairs) / n,
        "bias": sum(e - j for e, j in pairs) / n,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--report", type=Path, default=EXP_ROOT / "v1" / "blast_experiments_judged.md"
    )
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    failed = 0
    for stem in SERVERS:
        baseline = json.loads((BASELINE_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        tool_desc, asset_desc = load_descriptions(stem)
        profile_json = json.dumps(baseline.get("inferred_profile", {}), indent=2)
        tables = {
            label: json.loads((EXP_ROOT / d / pat.format(stem=stem)).read_text(encoding="utf-8"))
            for label, (d, pat) in EXPERIMENTS.items()
            if (EXP_ROOT / d / pat.format(stem=stem)).exists()
        }
        for key, blast in baseline["blast_radius"].items():
            if blast is None:
                continue  # judge only cells the baseline scored
            tool, asset = key.split("|", 1)
            judged = judge_cell(
                profile_json,
                {"name": tool, "description": tool_desc.get(tool, "")},
                {
                    "asset_id": asset,
                    "description": asset_desc.get(asset, ""),
                    "sensitivity": baseline["asset_sensitivity"][asset],
                },
            )
            if judged is None:
                failed += 1
            row = {
                "server": baseline["server"],
                "tool": tool,
                "asset": asset,
                "offender": is_offender(baseline, tool, asset),
                "judged": judged,
            }
            for label, table in tables.items():
                row[label] = table["blast_radius"].get(key)  # ctx may be N/A here
            rows.append(row)
        print(f"[ok] {stem}: {sum(r['server'] == baseline['server'] for r in rows)} cells judged")

    with (args.out_dir / "judged_blast.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["server", "tool", "asset", "offender", "judged", *EXPERIMENTS]
        )
        writer.writeheader()
        writer.writerows(rows)

    judged_n = sum(1 for r in rows if r["judged"] is not None)
    lines = [
        "# LLM-as-judge — blast agreement per experiment",
        "",
        f"Blinded judge re-derived blast for {judged_n}/{len(rows)} scored baseline "
        f"cells ({failed} unusable/N-A verdicts). Experiments graded by agreement with "
        "the judge; bias < 0 means the experiment under-scores reach vs the judge.",
        "",
    ]
    subsets = [
        ("ALL scored cells", lambda r: True),
        ("OFFENDER cells (imp>=4, sens>=4, baseline blast<=2)", lambda r: r["offender"]),
        ("CONTROL cells (everything else)", lambda r: not r["offender"]),
    ]
    for title, subset in subsets:
        lines += [
            f"## {title}",
            "",
            "| experiment | n | exact | within ±1 | MAE | bias |",
            "|---|---|---|---|---|---|",
        ]
        for label in EXPERIMENTS:
            m = metrics(rows, label, subset)
            if m is None:
                lines.append(f"| {label} | 0 | - | - | - | - |")
            else:
                lines.append(
                    f"| {label} | {m['n']} | {m['exact']:.0%} | {m['within1']:.0%} "
                    f"| {m['mae']:.2f} | {m['bias']:+.2f} |"
                )
        lines.append("")
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[done] wrote {args.report}")
    return 1 if failed > len(rows) // 4 else 0  # loud when the judge mostly failed


if __name__ == "__main__":
    raise SystemExit(main())
