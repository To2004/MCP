"""Experiment `rowfix`: per-asset row-consistency repair of blast radius.

Motivation: blast is scored one (tool, asset) pair at a time, so the model never
sees that its own row is internally inconsistent — e.g. on the personal calendar
it gave delete-event (impact 5) blast 1 / score 20 while list-events (impact 3)
got blast 2 / score 24: destroying an item outranked by browsing. This pass
shows the model the WHOLE row for one asset — every scored tool with its impact,
blast, and total — and asks it to repair only the cells whose blast is
inconsistent with the rest of the row.

Deterministic guardrails: only blast may change; repairs are clamped to 1-5;
repairs to unknown tools or N/A cells are dropped; unrepaired rows pass through
untouched; every applied repair is recorded with the model's justification.
Scores and bands are recomputed with the baseline formula and ``band_label``.

Run on a GPU node (LLM-only, ~1 call per asset):
    python scripts/row_consistency_repair.py
    (reads reports/experiments/v1/five_level_v2_fs, writes
     reports/experiments/v1/five_level_v2_rowfix)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.pipeline import LIKELIHOOD, band_label

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_fs"
OUT_DIR = REPO_ROOT / "reports" / "experiments" / "v1" / "five_level_v2_rowfix"
SERVERS = ("calendar_real", "slack_real", "fs_corp")

REPAIR_TASK = """You are a security reviewer auditing ONE ROW of an MCP misuse-scoring
matrix: every tool's decision against a single asset class. The domain was inferred
from the server's registry; trust it.

INFERRED DOMAIN PROFILE:
{domain_profile}

Each cell was scored in isolation as score = sensitivity x blast x impact, where
impact (1-5: liveness/metadata/read/write/destroy) is the KIND of action and blast
(1-5) is the REACH of one call across the asset's items, subjects, and dependents.
Scored one at a time, cells can end up inconsistent AS A SET. Audit the row against
these ordering principles:
- P1: on the same asset, destroying or overwriting content (impact 5) should not end
  with a LOWER total score than merely listing metadata or reading a narrow slice
  (impact 2-3), unless the destructive call genuinely reaches far less.
- P2: among tools of the SAME impact tier, one whose single call reaches more of the
  asset (bulk, recursive, "all"-scoped) must have blast >= a narrower tool's.
- P3: blast prices reach ONLY — reach counts the subjects and dependents who feel
  the effect (attendees, members, consumers), not just raw item counts; a silent,
  hard-to-notice effect reaches at least as far as a visible one.
- P4: do NOT inflate for importance alone — the asset's value is already priced by
  sensitivity. A genuinely pinpoint, easily-recovered touch may keep blast 1.
Repair the MINIMUM number of cells: identify cells whose blast is inconsistent with
the rest of the row under P1-P4 and give each a corrected blast (1-5) with a
one-line justification naming the principle. If the row is already consistent,
return an empty repairs list. Never change impact or sensitivity; never repair a
tool not shown in the row. Output ONLY valid JSON, no prose, no fences.

Asset (sensitivity {sensitivity}): {asset_id}

Row — every tool scored against this asset:
{row_json}

Return JSON:
{{"asset_id": str, "reasoning": str,
  "repairs": [{{"tool_name": str, "blast_radius": 1-5, "reason": str}}],
  "confidence": 0.0-1.0}}"""


def build_row(table: dict, asset: str) -> list[dict]:
    """The scored (non-N/A) cells of one asset row, in prompt form."""
    sens = table["asset_sensitivity"][asset]
    row = []
    for tool, impact in table["tool_impact"].items():
        blast = table["blast_radius"].get(f"{tool}|{asset}")
        if blast is None:
            continue
        row.append(
            {
                "tool_name": tool,
                "tool_impact": impact,
                "blast_radius": blast,
                "score": round(sens * blast * LIKELIHOOD * impact, 2),
            }
        )
    return row


def apply_repairs(table: dict, asset: str, repairs: list[dict]) -> list[dict]:
    """Clamp and apply one row's repairs to ``table['blast_radius']``.

    Returns the applied changes (tool, old, new, reason); invalid or no-op
    repairs are dropped silently — the guardrail, not the model, decides what
    is applicable.
    """
    applied = []
    for rep in repairs:
        tool = rep.get("tool_name")
        key = f"{tool}|{asset}"
        old = table["blast_radius"].get(key)
        if old is None:  # unknown tool or N/A cell — never invent a score
            continue
        try:
            new = max(1, min(5, int(rep.get("blast_radius"))))
        except (TypeError, ValueError):
            continue
        if new == old:
            continue
        table["blast_radius"][key] = new
        applied.append(
            {
                "tool": tool,
                "asset": asset,
                "old": old,
                "new": new,
                "reason": str(rep.get("reason", ""))[:300],
            }
        )
    return applied


def rebuild_cells(table: dict) -> None:
    """Recompute cells/bands/band_distribution from the (repaired) primitives."""
    cells: dict[str, dict[str, float | None]] = {}
    bands: dict[str, dict[str, str]] = {}
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0, "na": 0}
    for asset, s in table["asset_sensitivity"].items():
        crow: dict[str, float | None] = {}
        brow: dict[str, str] = {}
        for tool, i in table["tool_impact"].items():
            br = table["blast_radius"][f"{tool}|{asset}"]
            if br is None:
                crow[tool], brow[tool] = None, "na"
            else:
                crow[tool] = round(s * br * LIKELIHOOD * i, 2)
                brow[tool] = band_label(s, br, i)
            dist[brow[tool]] += 1
        cells[asset], bands[asset] = crow, brow
    table["cells"], table["bands"], table["band_distribution"] = cells, bands, dist


def repair_server(baseline: dict) -> tuple[dict, list[dict], int]:
    """Run the row audit over every asset; returns (table, changes, failed_rows)."""
    table = json.loads(json.dumps(baseline))  # deep copy; baseline stays pristine
    table["blast_radius_baseline"] = dict(baseline["blast_radius"])
    profile_json = json.dumps(baseline.get("inferred_profile", {}), indent=2)
    changes: list[dict] = []
    failed = 0
    for asset in table["asset_sensitivity"]:
        row = build_row(baseline, asset)
        if len(row) < 2:  # nothing to be inconsistent with
            continue
        prompt = REPAIR_TASK.format(
            domain_profile=profile_json,
            sensitivity=table["asset_sensitivity"][asset],
            asset_id=asset,
            row_json=json.dumps(row, indent=1),
        )
        result = query_ollama(prompt)
        if not isinstance(result, dict) or "repairs" not in result:
            failed += 1  # leave the row untouched — never fabricate a repair
            continue
        applied = apply_repairs(table, asset, result.get("repairs") or [])
        for change in applied:
            change["confidence"] = result.get("confidence")
        changes.extend(applied)
    rebuild_cells(table)
    table.update({"experiment": "rowfix", "rowfix_changes": changes, "rowfix_failed_rows": failed})
    return table, changes, failed


def _write_changes_csv(out: Path, stem: str, baseline: dict, changes: list[dict]) -> None:
    sens, impacts = baseline["asset_sensitivity"], baseline["tool_impact"]
    with (out / f"{stem}_changes.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "asset",
                "asset_sensitivity",
                "tool",
                "tool_impact",
                "blast_old",
                "blast_new",
                "score_old",
                "score_new",
                "band_old",
                "band_new",
                "reason",
            ]
        )
        for c in changes:
            s, i = sens[c["asset"]], impacts[c["tool"]]
            writer.writerow(
                [
                    c["asset"],
                    s,
                    c["tool"],
                    i,
                    c["old"],
                    c["new"],
                    round(s * c["old"] * i, 2),
                    round(s * c["new"] * i, 2),
                    band_label(s, c["old"], i),
                    band_label(s, c["new"], i),
                    c["reason"],
                ]
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=BASELINE_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary = [
        "# Experiment `rowfix` — per-asset row-consistency repair",
        "",
        f"Baseline: `{args.baseline_dir.name}`. One LLM audit per asset row; only "
        "inconsistent cells' blast repaired (guardrailed, minimum-change).",
        "",
        "| server | rows audited | rows failed | cells repaired | low | medium | high | critical | na |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    rc = 0
    for stem in SERVERS:
        src = args.baseline_dir / f"{stem}.json"
        if not src.exists():
            print(f"[skip] {src} missing")
            continue
        baseline = json.loads(src.read_text(encoding="utf-8"))
        table, changes, failed = repair_server(baseline)
        if failed:
            rc = 1  # partial repair — surface it loudly in the exit code
        (args.out_dir / f"{stem}.json").write_text(json.dumps(table, indent=2), encoding="utf-8")
        _write_changes_csv(args.out_dir, stem, baseline, changes)
        d = table["band_distribution"]
        n_rows = len(baseline["asset_sensitivity"])
        summary.append(
            f"| {baseline['server']} | {n_rows} | {failed} | {len(changes)} | {d['low']} "
            f"| {d['medium']} | {d['high']} | {d['critical']} | {d['na']} |"
        )
        print(f"[ok] {stem}: {len(changes)} cells repaired, {failed} rows failed")
    (args.out_dir / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"[done] wrote {args.out_dir}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
