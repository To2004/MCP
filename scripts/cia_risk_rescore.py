"""v6 — re-score the v5 matrices with the CIA-native score.

Runs offline from the v5 artifacts: no model call, no GPU, nothing random, so
every difference is the scoring rule and not LLM variance.

The score is the framework's own ``sensitivity x blast x impact`` on 0-125, kept
as the primary output. What changes is that it is computed **once per security
objective** and collapsed by the high-water mark::

    score_f = S x B_f x I_f     for each objective f the call can violate
    score   = max(existing score, score_C, score_I, score_A)

INVARIANT: the result is never below the cell's existing score. Sensitivity and
coverage are the unchanged v5 numbers and sensitivity is NOT split per objective
(a ranking is not a magnitude). The only thing CIA changes is per-objective
impact, used as a lower bound, which is what stops "destruction > modification >
disclosure" being hard-coded into the scale.

Emits, per server, a ``<stem>.md`` in the same shape as the v1-v5 scan reports,
plus a cross-server design-and-results document and the raw cells as CSV.

Run:  uv run python scripts/cia_risk_rescore.py
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring.cia_risk import (  # noqa: E402
    FORMULA,
    OP_IMPACT,
    SCORE_MAX,
    control_for,
    score_cell,
)

V5_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5"
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v6" / "cia_loss_vector"
STEMS = ("calendar_real", "github_real", "slack_real")
BANDS = ("low", "medium", "high", "critical")
BAND_MARK = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

# Cells the v5 product demonstrably mis-ranks: exfiltration paths priced below a
# mutation on the same asset, each named as a top risk in its own org's policy.
WITNESS_CELLS = {
    "github_real": [
        ("get_file_contents", "infra-config", "reads credential-shaped content"),
        ("merge_pull_request", "infra-config", "the mutation it is priced against"),
    ],
    "slack_real": [
        ("conversations_history", "incident-response", "reads pasted credentials"),
        ("conversations_add_message", "incident-response", "the mutation it is priced against"),
    ],
}

V6_RULES = [
    f"score = {FORMULA}, range 0-{SCORE_MAX}",
    "**INVARIANT: a cell is never scored below its existing value.** CIA is evidence "
    "added to the framework's judgement, not a re-weighting of it — so nothing the "
    "existing scale prices correctly can move down",
    "sensitivity floor: an asset the org rates 5 never scores below 50, and one rated 4 "
    "never below 25 — a crown jewel is not a routine cell just because the verb is a "
    "listing. Mirrors the pipeline's existing gated blast floor, one factor over",
    "sensitivity is NOT split per objective. `C>I>A` says disclosure hurts most on this "
    "asset; it does not say integrity loss is a tier cheaper. The loss axis breaks ties "
    "between objectives and routes the control, nothing more",
    "per-objective impact replaces the 1-5 action ladder as a LOWER BOUND: a READ is "
    "I_C=5 (a total confidentiality loss) and I_I=0, while writes and deletes keep their "
    "existing tiers — so only under-priced reads move",
    "self-sufficient assets: for CONFIDENTIALITY only, and only for content-returning "
    "ops, one item is the whole loss so B_C is treated as 5",
    "escape (CVSS subsequent system): assets flagged hub/self-sufficient/population gain "
    "25% on the driving objective at coverage >= 4, capped at the scale max",
    "the driving objective is kept and selects the control: C -> deny, I -> confirm, "
    "A -> throttle",
    "bands are the v5 thresholds on the score (low <17, medium 17-49, high 50-99, "
    "critical >=100), so the two arms are directly comparable",
]


def band_for(score: float) -> str:
    """The v5 band thresholds applied to a score, so both arms label alike."""
    if score >= 100:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 17:
        return "medium"
    return "low"


def load(stem: str, v5_dir: Path) -> tuple[dict, dict[str, dict]]:
    table = json.loads((v5_dir / f"{stem}.json").read_text(encoding="utf-8"))
    register = {
        row["asset"]: row
        for row in csv.DictReader(
            (v5_dir / "inputs" / f"{stem}.register.csv").read_text(encoding="utf-8").splitlines()
        )
    }
    return table, register


def rescore(table: dict, register: dict[str, dict]) -> list[dict]:
    """One row per scored cell, the v5 score beside the v6 one."""
    sens = table["asset_sensitivity"]
    atomic = table.get("tool_atomic_ops", {})
    rows: list[dict] = []
    for asset in table["asset_ids"]:
        entry = register.get(asset, {})
        axis = entry.get("cia", "")
        flags = tuple(f for f in (entry.get("flags") or "").split() if f)
        for tool in table["tool_impact"]:
            blast = table["blast_radius"].get(f"{tool}|{asset}")
            risk = score_cell(
                sens[asset],
                axis,
                (atomic.get(tool) or {}).get("atomic_ops") or [],
                blast,
                table["cells"][asset][tool],
                flags=flags,
            )
            if risk is None:
                continue
            driver = risk.driver
            rows.append(
                {
                    "asset": asset,
                    "tool": tool,
                    "loss_axis": axis or "(unstated)",
                    "flags": " ".join(flags),
                    "violates": "+".join(risk.violated),
                    "blast": blast,
                    "sens_asset": sens[asset],
                    "S": risk.sensitivity,
                    "I_C": risk.impact["C"],
                    "I_I": risk.impact["I"],
                    "I_A": risk.impact["A"],
                    "score_C": risk.per_objective["C"],
                    "score_I": risk.per_objective["I"],
                    "score_A": risk.per_objective["A"],
                    "driver": driver or "",
                    "score_v6": risk.score,
                    "band_v6": band_for(risk.score),
                    "raised_by_cia": risk.raised,
                    "floored_by_sensitivity": risk.floored,
                    "workings": (
                        f"{risk.sensitivity}×{risk.coverage[driver]}×{risk.impact[driver]}"
                        if driver
                        else "existing score"
                    ),
                    "control": control_for(risk),
                    "score_v5": table["cells"][asset][tool],
                    "band_v5": table["bands"][asset][tool],
                    "delta": round(risk.score - table["cells"][asset][tool], 2),
                }
            )
    return rows


def spearman(pairs: list[tuple[float, float]]) -> float | None:
    """Rank correlation with average ranks for ties (scores are heavily tied)."""
    if len(pairs) < 2:
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            average = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = average
            i = j + 1
        return out

    xs, ys = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    var_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    return round(cov / (var_x * var_y), 4) if var_x and var_y else None


def witnesses(stem: str, rows: list[dict]) -> list[dict]:
    index = {(r["tool"], r["asset"]): r for r in rows}
    out = []
    for tool, asset, note in WITNESS_CELLS.get(stem, []):
        row = index.get((tool, asset))
        if row is None:
            continue
        out.append(
            {
                "cell": f"`{tool}` × `{asset}`",
                "what it is": note,
                "v5 score": row["score_v5"],
                "v6 score": row["score_v6"],
                "workings": f"{row['driver']}: {row['workings']}" if row["driver"] else "",
                "control": row["control"].split(" — ")[0],
            }
        )
    return out


def evaluate(stem: str, v5_dir: Path) -> dict:
    table, register = load(stem, v5_dir)
    rows = rescore(table, register)
    return {
        "stem": stem,
        "server": table["server"],
        "scored_cells": len(rows),
        "score_sum_v5": round(sum(r["score_v5"] for r in rows), 1),
        "score_sum_v6": round(sum(r["score_v6"] for r in rows), 1),
        "peak_v5": max((r["score_v5"] for r in rows), default=0),
        "peak_v6": max((r["score_v6"] for r in rows), default=0),
        "bands_v5": {b: sum(1 for r in rows if r["band_v5"] == b) for b in BANDS},
        "bands_v6": {b: sum(1 for r in rows if r["band_v6"] == b) for b in BANDS},
        "drivers": dict(Counter(r["driver"] or "none" for r in rows)),
        "spearman": spearman([(r["score_v5"], r["score_v6"]) for r in rows]),
        "cells_raised": sum(1 for r in rows if r["delta"] > 0),
        "cells_lowered": sum(1 for r in rows if r["delta"] < 0),
        "_rows": rows,
        "_witnesses": witnesses(stem, rows),
        "_table": table,
    }


def _md(rows: list[dict], columns: list[str]) -> str:
    head = "| " + " | ".join(columns) + " |"
    rule = "|" + "".join(" --- |" for _ in columns)
    body = [
        "| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in columns) + " |"
        for r in rows
    ]
    return "\n".join([head, rule, *body])


def render_server_markdown(table: dict, rows: list[dict]) -> str:
    """One server's report, in the same shape as the v1-v5 `<stem>.md` scans."""
    by_cell = {(r["asset"], r["tool"]): r for r in rows}
    tools = list(table["tool_impact"])
    assets = table["asset_ids"]
    atomic = table.get("tool_atomic_ops", {})
    counts = Counter(r["band_v6"] for r in rows)
    na = len(assets) * len(tools) - len(rows)
    peak = max((r["score_v6"] for r in rows), default=0)

    out = [
        f"# Scan — {table['server']} · CIA-native score",
        "",
        f"_kind={table.get('server_kind', table.get('mcp_kind', ''))} · "
        f"scoring=cia_loss_vector · source={table.get('impact_mode')} artifacts · "
        f"score_max={SCORE_MAX} · bands={{'low': {counts['low']}, "
        f"'medium': {counts['medium']}, 'high': {counts['high']}, "
        f"'critical': {counts['critical']}, 'na': {na}}}_",
        "",
        f"`score = {FORMULA}` — the same three factors as v5, computed **per security "
        "objective** and collapsed by the high-water mark. Sensitivity and coverage are "
        "the unchanged v5 numbers; the 1–5 action ladder is replaced by per-objective "
        "impact. Every cell carries the objective that drove it, and that objective "
        "selects the control.",
        "",
        "## Scoring rules applied",
        "",
        *[f"- {rule}" for rule in V6_RULES],
        "",
        "## Tool impact per objective",
        "",
        "_How completely one call violates each objective; 0 means it cannot touch that "
        "objective at all. Replaces the single 1–5 impact number._",
        "",
        "| tool | atomic ops | I_C | I_I | I_A |",
        "| --- | --- | --- | --- | --- |",
    ]
    for tool in tools:
        sample = next((r for r in rows if r["tool"] == tool), None)
        if sample is None:
            continue
        ops = (atomic.get(tool) or {}).get("atomic_ops") or []
        out.append(
            f"| `{tool}` | {', '.join(ops) or '—'} | {sample['I_C']} | {sample['I_I']} "
            f"| {sample['I_A']} |"
        )

    out += [
        "",
        "## Asset sensitivity per objective",
        "",
        "_Unchanged from the v5 scan and NOT split per objective — a loss-axis ranking is "
        "not a magnitude. The axis breaks ties between objectives and routes the control._",
        "",
        "| asset | sensitivity | loss axis | flags |",
        "| --- | --- | --- | --- |",
    ]
    seen: set[str] = set()
    for asset in assets:
        row = next((r for r in rows if r["asset"] == asset), None)
        if row is None or asset in seen:
            continue
        seen.add(asset)
        out.append(
            f"| `{asset}` | {row['sens_asset']} | {row['loss_axis']} "
            f"| {row['flags'] or '—'} |"
        )

    out += [
        "",
        "## Risk matrix (score · driver)",
        "",
        f"_Each cell shows `score (driver: S×B×I)`; range 0–{SCORE_MAX}, peak here {peak}. "
        "Colour is by score on the v5 thresholds: 🟢 <17 · 🟡 17–49 · 🟠 50–99 · 🔴 ≥100._",
        "",
        "| asset \\ tool | " + " | ".join(tools) + " |",
        "|" + "".join(" --- |" for _ in range(len(tools) + 1)),
    ]
    for asset in assets:
        cells = []
        for tool in tools:
            row = by_cell.get((asset, tool))
            if row is None:
                cells.append("N/A")
            elif not row["driver"]:
                cells.append("0")
            else:
                cells.append(
                    f"{row['score_v6']} ({row['driver']}: {row['workings']}) "
                    f"{BAND_MARK[row['band_v6']]}"
                )
        out.append(f"| `{asset}` | " + " | ".join(cells) + " |")

    out += [
        "",
        "## Per-objective scores",
        "",
        "_The vector behind each cell, before the high-water mark. A zero means the tool "
        "cannot violate that objective at all. Top 25 by score._",
        "",
        "| asset | tool | score_C | score_I | score_A | → score | driver |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| `{r['asset']}` | `{r['tool']}` | {r['score_C']} | {r['score_I']} "
            f"| {r['score_A']} | **{r['score_v6']}** | {r['driver']} |"
            for r in sorted(rows, key=lambda r: -r["score_v6"])[:25]
        ],
        "",
        "## Blast radius (coverage · 1–5)",
        "",
        "_Unchanged from the v5 scan: what fraction of the asset ONE call reaches. Used as "
        "B in the score, per objective._",
        "",
        "| asset \\ tool | " + " | ".join(tools) + " |",
        "|" + "".join(" --- |" for _ in range(len(tools) + 1)),
    ]
    for asset in assets:
        cells = [
            "N/A"
            if table["blast_radius"].get(f"{tool}|{asset}") is None
            else str(table["blast_radius"][f"{tool}|{asset}"])
            for tool in tools
        ]
        out.append(f"| `{asset}` | " + " | ".join(cells) + " |")

    controls: dict[str, list[dict]] = {}
    for r in rows:
        if r["score_v6"] >= 50:
            controls.setdefault(r["control"].split(" — ")[0], []).append(r)
    why = {
        "deny": "disclosure cannot be undone, so approval buys nothing",
        "require human confirmation": "recoverable only if a restore path exists",
        "throttle": "availability loss is usually transient",
    }
    out += [
        "",
        "## Controls implied",
        "",
        "_The driving objective selects the control, which a bare number cannot do. Cells "
        "scoring ≥ 50._",
        "",
        "| control | cells | why |",
        "| --- | --- | --- |",
        *[
            f"| **{control}** | {len(items)} | {why.get(control, '')} |"
            for control, items in sorted(controls.items(), key=lambda kv: -len(kv[1]))
        ],
    ]

    moved = sorted((r for r in rows if r["delta"] != 0), key=lambda r: -abs(r["delta"]))
    out += [
        "",
        f"## Biggest changes from the v5 product ({len(moved)} of {len(rows)} cells moved)",
        "",
        "| asset | tool | driver | v5 | v6 | Δ | workings |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| `{r['asset']}` | `{r['tool']}` | {r['driver'] or '—'} | {r['score_v5']} "
            f"| **{r['score_v6']}** {BAND_MARK[r['band_v6']]} | {r['delta']:+g} "
            f"| {r['workings']} |"
            for r in moved[:30]
        ],
        "",
        f"_Top 30 by absolute change; {len(moved)} moved in total._",
        "",
    ]
    return "\n".join(out)


def render_overview(results: list[dict]) -> str:
    out = [
        "# CIA-native scoring — design and results",
        "",
        f"`score = {FORMULA}`, range 0–{SCORE_MAX}.",
        "",
        "The framework's own three factors, kept — and kept as a **number**. What changes",
        "is that the score is computed once per security objective and collapsed by the",
        "high-water mark, with the driving objective retained.",
        "",
        "Generated by `scripts/cia_risk_rescore.py` — offline, no model call, no GPU, so",
        "every difference from v5 is the scoring rule and not LLM variance. Do not",
        "hand-edit.",
        "",
        "## Design principles",
        "",
        "**P1 · CIA is additive evidence, never a discount.** A cell is never scored below",
        "its existing value. This module exists to surface risk the ladder under-prices, not",
        "to re-weight risk the framework already prices correctly. Enforced in code, not by",
        "convention.",
        "",
        "**P2 · A ranking is not a magnitude.** An earlier version split sensitivity by the",
        "register's loss axis (`C>I>A` at 4 -> `C=4, I=3, A=2`) and multiplied that by a",
        "per-objective impact. Both are discounts and they compounded: `create-events` on the",
        "`executive` calendar fell 64 -> 36 because integrity happened to rank second on an",
        "asset the organization calls a crown jewel. `C>I>A` says disclosure hurts most here;",
        "it does not say integrity loss is a tier cheaper. Sensitivity is no longer split —",
        "the axis breaks ties between objectives and routes the control, nothing more.",
        "",
        "**P2b · The action says WHICH objective, the asset says HOW MUCH.** The 1–5 ladder",
        "(`metadata < read < write < delete`) hard-codes *destruction > modification >",
        "disclosure*. Because reads cap at 3 and writes start at 4, no read can outrank a",
        "write on the same asset at the same coverage — whatever the asset holds.",
        "Per-objective impact is used as a LOWER BOUND: a READ becomes `I_C=5`, while writes",
        "and deletes keep their existing tiers, so only under-priced reads move.",
        "",
        "**P3 · Collapse with the high-water mark, never a sum.** FIPS 199's rule for exactly",
        "this: a per-objective categorization becomes one level by taking the maximum.",
        "Summing would say two moderate losses equal one severe one.",
        "",
        "**P4 · Keep the driver, because it selects the control.** C-loss cannot be undone →",
        "deny. I-loss is recoverable with a restore path → confirm. A-loss is transient →",
        "throttle. A bare number cannot produce this at any precision.",
        "",
        "**P5 · Only the organization may sanction an escalation.** The register's `Flags`",
        "are the only escape route: `self-sufficient` means one item is the whole",
        "confidentiality loss, `hub` means other systems depend on it.",
        "",
        "**Grounding:** CVSS v4.0 scores impact as a CIA triple (VC/VI/VA), not one metric;",
        "FIPS 199 collapses per-objective categorization with the high-water mark.",
        "",
        "## Totals",
        "",
        _md(
            [
                {
                    "server": r["stem"],
                    "cells": r["scored_cells"],
                    "Σ v5": r["score_sum_v5"],
                    "Σ v6": r["score_sum_v6"],
                    "peak v5": r["peak_v5"],
                    "peak v6": r["peak_v6"],
                    "raised": r["cells_raised"],
                    "lowered": r["cells_lowered"],
                    "Spearman ρ": r["spearman"],
                }
                for r in results
            ],
            [
                "server", "cells", "Σ v5", "Σ v6", "peak v5", "peak v6", "raised",
                "lowered", "Spearman ρ",
            ],
        ),
        "",
        "## The cells the product mis-ranks",
        "",
        "Exfiltration paths priced *below* a mutation on the same asset, because reads cap",
        "at impact 3 while writes start at 4. Each is named as a top risk in its own",
        "organization's policy.",
        "",
    ]
    for r in results:
        if r["_witnesses"]:
            out += [
                f"**{r['stem']}**",
                "",
                _md(
                    r["_witnesses"],
                    ["cell", "what it is", "v5 score", "v6 score", "workings", "control"],
                ),
                "",
            ]
    out += [
        "## Band distribution",
        "",
        _md(
            [
                {"server": r["stem"], "arm": arm, **counts}
                for r in results
                for arm, counts in (("v5", r["bands_v5"]), ("v6", r["bands_v6"]))
            ],
            ["server", "arm", *BANDS],
        ),
        "",
        "## Loss profile",
        "",
        "Which objective drives risk on each server — free with the high-water mark, and",
        "impossible with a single scalar.",
        "",
        _md(
            [
                {
                    "server": r["stem"],
                    "driven by C": r["drivers"].get("C", 0),
                    "driven by I": r["drivers"].get("I", 0),
                    "driven by A": r["drivers"].get("A", 0),
                }
                for r in results
            ],
            ["server", "driven by C", "driven by I", "driven by A"],
        ),
        "",
        "## Per-objective impact table",
        "",
        "How completely each atomic operation violates each objective. Blank = cannot touch",
        "that objective.",
        "",
        "| operation | I_C | I_I | I_A |",
        "| --- | --- | --- | --- |",
        *[
            f"| `{op}` | {vals.get('C', '')} | {vals.get('I', '')} | {vals.get('A', '')} |"
            for op, vals in OP_IMPACT.items()
        ],
        "",
        "## Per-server reports",
        "",
        *[f"- [`{r['stem']}.md`]({r['stem']}.md)" for r in results],
        "",
        "## How to falsify this",
        "",
        "```bash",
        "uv run python scripts/evaluate_dynamic.py",
        "```",
        "",
        "Prediction: exfiltration-shaped malicious sessions separate from benign **more**",
        "than under v5, because that is the class the old ladder structurally under-prices.",
        "If separation does not improve, this is cosmetic and should be dropped.",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v5-dir", type=Path, default=V5_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = [evaluate(stem, args.v5_dir) for stem in STEMS]

    (args.out_dir / "DESIGN_AND_RESULTS.md").write_text(render_overview(results), encoding="utf-8")
    (args.out_dir / "results.json").write_text(
        json.dumps(
            [{k: v for k, v in r.items() if not k.startswith("_")} for r in results], indent=2
        ),
        encoding="utf-8",
    )
    for result in results:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(result["_rows"][0]))
        writer.writeheader()
        writer.writerows(result["_rows"])
        (args.out_dir / f"{result['stem']}_cells.csv").write_text(
            buffer.getvalue(), encoding="utf-8"
        )
        (args.out_dir / f"{result['stem']}.md").write_text(
            render_server_markdown(result["_table"], result["_rows"]), encoding="utf-8"
        )
        print(
            f"[ok] {result['stem']}: {result['scored_cells']} cells | "
            f"Σ {result['score_sum_v5']} -> {result['score_sum_v6']} | "
            f"peak {result['peak_v5']} -> {result['peak_v6']} | "
            f"raised {result['cells_raised']} lowered {result['cells_lowered']} | "
            f"ρ {result['spearman']}"
        )
    print(f"\nwrote <stem>.md, DESIGN_AND_RESULTS.md, results.json and CSVs to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
