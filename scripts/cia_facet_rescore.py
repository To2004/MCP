"""v6 experiment A — re-price the v5 matrices with CIA as a facet selector.

Runs entirely OFFLINE from the v5 artifacts: no model call, no GPU, nothing
random. Every input it needs is already recorded — the derived
``asset_sensitivity``, the assembled ``blast_radius``, the ``tool_impact``, and
the ``tool_atomic_ops`` classification — plus each asset's loss axis from the
policy register. That isolation is the point: any difference measured here is
attributable to the CIA rule alone, with zero LLM variance mixed in.

The rule (see :mod:`mcp_security.static_scoring.cia_facets`)::

    sens_eff(asset, tool) = max over facets the tool violates of sens_facet(asset)
    cell                  = sens_eff x blast x impact

Because the per-facet split is anchored at the asset's leading axis, the rule can
only lower a cell. The experiment asks whether lowering the *right* cells buys
discrimination — specifically whether a read and a write on the same asset stop
being priced by the same asset value.

What it reports:

* Σ score and band movement (the inflation check — v1's CIA arm failed here);
* **axis separation**: per asset, the mean cell score of confidentiality-only
  operations against that of integrity/availability ones, before and after. On an
  integrity-led asset that gap should open up;
* rank correlation of all scored cells, so "did the ordering actually change?"
  is answered with a number rather than an impression;
* the largest movers, and the three per-facet matrices (risk_C / risk_I / risk_A).

Run:  uv run python scripts/cia_facet_rescore.py
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

from mcp_security.static_scoring.cia_facets import (  # noqa: E402
    FACETS,
    effective_sensitivity,
    facet_sensitivity,
)
from mcp_security.static_scoring.pipeline import band_label_v5  # noqa: E402

V5_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5"
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v6" / "cia_facet_rescore"
STEMS = ("calendar_real", "github_real", "slack_real")
BANDS = ("low", "medium", "high", "critical", "na")


def load_inputs(stem: str, v5_dir: Path) -> tuple[dict, dict[str, str]]:
    """The v5 artifact and ``{asset_id: loss axis}`` from its input register."""
    table = json.loads((v5_dir / f"{stem}.json").read_text(encoding="utf-8"))
    register = {
        row["asset"]: row.get("cia", "")
        for row in csv.DictReader(
            (v5_dir / "inputs" / f"{stem}.register.csv").read_text(encoding="utf-8").splitlines()
        )
    }
    return table, register


def spearman(pairs: list[tuple[float, float]]) -> float | None:
    """Rank correlation, implemented here to avoid a scipy dependency.

    Average ranks are used for ties, which matters: score distributions on these
    matrices are heavily tied (many cells share a value), and integer ranking
    would understate the correlation.
    """
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


def rescore(table: dict, register: dict[str, str]) -> dict:
    """Re-price every scored cell with the facet-selected sensitivity."""
    sens = table["asset_sensitivity"]
    impacts = table["tool_impact"]
    atomic = table.get("tool_atomic_ops", {})
    cells_v5, cells_v6 = table["cells"], {}
    bands_v6: dict[str, dict[str, str]] = {}
    per_facet_cells = {facet: {} for facet in FACETS}
    rows: list[dict] = []

    for asset in table["asset_ids"]:
        axis = register.get(asset, "")
        facet_sens = facet_sensitivity(sens[asset], axis)
        cells_v6[asset] = {}
        bands_v6[asset] = {}
        for facet in FACETS:
            per_facet_cells[facet][asset] = {}
        for tool in impacts:
            blast = table["blast_radius"].get(f"{tool}|{asset}")
            ops = (atomic.get(tool) or {}).get("atomic_ops") or []
            verdict = effective_sensitivity(sens[asset], axis, ops)
            if blast is None:  # N/A cell — the tool does not act on this asset
                cells_v6[asset][tool] = None
                bands_v6[asset][tool] = "na"
                for facet in FACETS:
                    per_facet_cells[facet][asset][tool] = None
                continue
            impact = impacts[tool]
            cells_v6[asset][tool] = round(verdict.sensitivity * blast * impact, 2)
            bands_v6[asset][tool] = band_label_v5(verdict.sensitivity, blast, impact)
            # The three planes: what a loss of THIS objective would cost here,
            # scored only where the tool can actually violate it.
            for facet in FACETS:
                per_facet_cells[facet][asset][tool] = (
                    round(facet_sens[facet] * blast * impact, 2)
                    if facet in verdict.violated
                    else None
                )
            rows.append(
                {
                    "asset": asset,
                    "tool": tool,
                    "loss_axis": axis,
                    "atomic_ops": "+".join(ops),
                    "violates": "+".join(verdict.violated),
                    "sens_v5": sens[asset],
                    "sens_facet": verdict.sensitivity,
                    "selected_facet": verdict.facet or "",
                    "blast": blast,
                    "impact": impact,
                    "cell_v5": cells_v5[asset][tool],
                    "cell_v6": cells_v6[asset][tool],
                    "delta": round(cells_v6[asset][tool] - cells_v5[asset][tool], 2),
                }
            )
    return {"cells": cells_v6, "bands": bands_v6, "per_facet": per_facet_cells, "rows": rows}


def axis_separation(rows: list[dict]) -> dict:
    """Do C-only operations separate from I/A ones, per asset, after the rule?

    The discrimination the experiment is actually testing. For each asset, the
    mean scored cell of confidentiality-only tools is compared with the mean of
    tools that touch integrity or availability — before and after. An
    integrity-led asset should see reads fall away from writes; a
    confidentiality-led asset should see the opposite.
    """
    by_asset: dict[str, dict] = {}
    for row in rows:
        entry = by_asset.setdefault(
            row["asset"], {"axis": row["loss_axis"], "c": [], "ia": [], "c6": [], "ia6": []}
        )
        confidentiality_only = row["violates"] == "C"
        entry["c" if confidentiality_only else "ia"].append(row["cell_v5"])
        entry["c6" if confidentiality_only else "ia6"].append(row["cell_v6"])

    def mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    out = {}
    for asset, entry in by_asset.items():
        before_c, before_ia = mean(entry["c"]), mean(entry["ia"])
        after_c, after_ia = mean(entry["c6"]), mean(entry["ia6"])
        gap_before = (
            None if before_c is None or before_ia is None else round(before_ia - before_c, 2)
        )
        gap_after = None if after_c is None or after_ia is None else round(after_ia - after_c, 2)
        # Which way SHOULD the gap move? The org's stated leading axis decides.
        # An integrity- or availability-led asset should push confidentiality-only
        # operations down and away from mutations (gap widens); a
        # confidentiality-led asset should pull mutations down toward reads (gap
        # narrows). Measuring |gap| alone scores the second case as a failure when
        # it is the rule behaving correctly.
        # SIGNED movement, not |gap|: on a confidentiality-led asset the gap
        # (mean_IA - mean_C) should fall, and falling past zero is an overshoot in
        # the right direction, not a failure. Reading incident history really can
        # outrank posting to it.
        leads_c = (entry["axis"] or "").strip().upper().startswith("C")
        expected = "narrow" if leads_c else "widen"
        aligned = None
        if gap_before is not None and gap_after is not None and gap_before != gap_after:
            moved_up = gap_after > gap_before
            aligned = moved_up == (expected == "widen")
        out[asset] = {
            "loss_axis": entry["axis"],
            "expected": expected,
            "mean_C_only_v5": before_c,
            "mean_IA_v5": before_ia,
            "gap_v5": gap_before,
            "mean_C_only_v6": after_c,
            "mean_IA_v6": after_ia,
            "gap_v6": gap_after,
            "axis_aligned": aligned,
        }
    return out


def band_counts(bands: dict[str, dict[str, str]]) -> dict[str, int]:
    counts = dict.fromkeys(BANDS, 0)
    for row in bands.values():
        for band in row.values():
            counts[band] = counts.get(band, 0) + 1
    return counts


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def matrix_csv(cells: dict[str, dict[str, float | None]], tools: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["asset", *tools])
    for asset, row in cells.items():
        writer.writerow([asset, *("" if row[t] is None else row[t] for t in tools)])
    return buffer.getvalue()


def evaluate(stem: str, v5_dir: Path, out_dir: Path) -> dict:
    table, register = load_inputs(stem, v5_dir)
    result = rescore(table, register)
    rows = result["rows"]
    tools = list(table["tool_impact"])

    sum_v5 = round(sum(r["cell_v5"] for r in rows), 2)
    sum_v6 = round(sum(r["cell_v6"] for r in rows), 2)
    moved = [r for r in rows if r["delta"] != 0]
    write_csv(out_dir / f"{stem}_cells.csv", rows)
    for facet in FACETS:
        (out_dir / f"{stem}_risk_{facet}.csv").write_text(
            matrix_csv(result["per_facet"][facet], tools), encoding="utf-8"
        )
    separation = axis_separation(rows)
    aligned = [a for a, s in separation.items() if s["axis_aligned"]]

    return {
        "stem": stem,
        "server": table["server"],
        "scored_cells": len(rows),
        "cells_moved": len(moved),
        "score_sum_v5": sum_v5,
        "score_sum_v6": sum_v6,
        "score_delta_pct": round(100 * (sum_v6 - sum_v5) / sum_v5, 1) if sum_v5 else None,
        "any_cell_raised": any(r["delta"] > 0 for r in rows),
        "bands_v5": {b: table["band_distribution"].get(b, 0) for b in BANDS},
        "bands_v6": band_counts(result["bands"]),
        "spearman": spearman([(r["cell_v5"], r["cell_v6"]) for r in rows]),
        "assets_axis_aligned": len(aligned),
        "assets_compared": sum(1 for s in separation.values() if s["axis_aligned"] is not None),
        "_separation": separation,
        "_top_movers": sorted(moved, key=lambda r: r["delta"])[:12],
    }


def render_markdown(results: list[dict]) -> str:
    def table(rows: list[dict], columns: list[str]) -> str:
        head = "| " + " | ".join(columns) + " |"
        rule = "|" + "|".join("---" for _ in columns) + "|"
        body = [
            "| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in columns) + " |"
            for r in rows
        ]
        return "\n".join([head, rule, *body])

    out = [
        "# v6 · experiment A — CIA as a facet selector",
        "",
        "Re-prices the v5 matrices offline. The sensitivity of a cell is no longer the",
        "asset's single number but the number of the **facet the tool actually violates**,",
        "with the per-facet split anchored at the asset's leading axis. No model call is",
        "involved, so every difference below is the CIA rule and nothing else.",
        "",
        "Generated by `scripts/cia_facet_rescore.py` — do not hand-edit.",
        "",
        "## 1 · Inflation check",
        "",
        "The v1 CIA arm failed here: adding C/I/A as points raised calendar's `high` band",
        "from 8 to 25 cells. Anchoring at the leading axis makes raising a cell",
        "structurally impossible — `any cell raised` must read `False`.",
        "",
        table(
            [
                {
                    "server": r["stem"],
                    "Σ v5": r["score_sum_v5"],
                    "Σ v6": r["score_sum_v6"],
                    "change": f"{r['score_delta_pct']}%",
                    "any cell raised": r["any_cell_raised"],
                    "cells moved": f"{r['cells_moved']}/{r['scored_cells']}",
                }
                for r in results
            ],
            ["server", "Σ v5", "Σ v6", "change", "any cell raised", "cells moved"],
        ),
        "",
        "## 2 · Did the ordering change?",
        "",
        "A gate consumes the ranking, not the absolute numbers. Spearman ρ of 1.0 would",
        "mean the rule rescaled the matrix and re-ranked nothing — the v1 failure mode.",
        "",
        table(
            [
                {
                    "server": r["stem"],
                    "cells": r["scored_cells"],
                    "Spearman ρ (v5 vs v6)": r["spearman"],
                }
                for r in results
            ],
            ["server", "cells", "Spearman ρ (v5 vs v6)"],
        ),
        "",
        "## 3 · Axis separation — the effect being bought",
        "",
        "Per asset, the mean scored cell of confidentiality-only operations against the",
        "mean of operations touching integrity or availability. On an integrity-led asset",
        "the gap should open; on a confidentiality-led one it should close or invert.",
        "",
        table(
            [
                {
                    "server": r["stem"],
                    "assets compared": r["assets_compared"],
                    "moved as the axis predicts": r["assets_axis_aligned"],
                }
                for r in results
            ],
            ["server", "assets compared", "moved as the axis predicts"],
        ),
        "",
        "## 4 · Band movement",
        "",
        table(
            [
                {"server": r["stem"], "arm": arm, **counts}
                for r in results
                for arm, counts in (("v5", r["bands_v5"]), ("v6", r["bands_v6"]))
            ],
            ["server", "arm", *BANDS],
        ),
        "",
    ]
    for r in results:
        out += [
            f"## {r['stem']} — largest reductions",
            "",
            table(
                r["_top_movers"],
                [
                    "asset",
                    "tool",
                    "loss_axis",
                    "violates",
                    "sens_v5",
                    "sens_facet",
                    "cell_v5",
                    "cell_v6",
                    "delta",
                ],
            ),
            "",
            f"### {r['stem']} — axis separation per asset",
            "",
            table(
                [
                    {"asset": asset, **stats}
                    for asset, stats in sorted(
                        r["_separation"].items(),
                        key=lambda kv: (kv[1]["gap_v6"] is None, -(kv[1]["gap_v6"] or 0)),
                    )
                ],
                [
                    "asset",
                    "loss_axis",
                    "mean_C_only_v5",
                    "mean_IA_v5",
                    "gap_v5",
                    "mean_C_only_v6",
                    "mean_IA_v6",
                    "gap_v6",
                    "expected",
                    "axis_aligned",
                ],
            ),
            "",
        ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v5-dir", type=Path, default=V5_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = [evaluate(stem, args.v5_dir, args.out_dir) for stem in STEMS]

    (args.out_dir / "RESULTS.md").write_text(render_markdown(results), encoding="utf-8")
    (args.out_dir / "results.json").write_text(
        json.dumps(
            [{k: v for k, v in r.items() if not k.startswith("_")} for r in results], indent=2
        ),
        encoding="utf-8",
    )
    write_csv(
        args.out_dir / "ALL_SERVERS_summary.csv",
        [
            {
                "server": r["stem"],
                "scored_cells": r["scored_cells"],
                "cells_moved": r["cells_moved"],
                "score_sum_v5": r["score_sum_v5"],
                "score_sum_v6": r["score_sum_v6"],
                "score_delta_pct": r["score_delta_pct"],
                "any_cell_raised": r["any_cell_raised"],
                "spearman": r["spearman"],
                "assets_compared": r["assets_compared"],
                "assets_axis_aligned": r["assets_axis_aligned"],
                **{f"v6_band_{b}": r["bands_v6"][b] for b in BANDS},
            }
            for r in results
        ],
    )
    for r in results:
        print(
            f"[ok] {r['stem']}: Σ {r['score_sum_v5']} -> {r['score_sum_v6']} "
            f"({r['score_delta_pct']}%) | moved {r['cells_moved']}/{r['scored_cells']} "
            f"| raised any: {r['any_cell_raised']} | ρ {r['spearman']} "
            f"| axis-aligned on {r['assets_axis_aligned']}/{r['assets_compared']} assets"
        )
    print(f"\nwrote RESULTS.md, results.json and per-server CSVs to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
