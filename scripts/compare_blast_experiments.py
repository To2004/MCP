"""Compare the three blast-radius experiments against the five_level_v2_fs baseline.

Experiments (each a separate run over calendar_real / slack_real / fs_corp):
- ``five_level_v2_ctx``    — context-first blast: per-tool understanding stage
  injected into every blast decision (full LLM re-scan).
- ``five_level_v2_floor``  — deterministic sensitivity-coupled minimum blast
  (variants: plain, impact-gated).
- ``five_level_v2_rowfix`` — per-asset row-consistency repair over the baseline.

For every server the report shows the band distributions side by side and tracks
the OFFENDER cells that motivated the experiments: mutating tools (impact >= 4)
on sensitive assets (sensitivity >= 4) that the baseline priced at blast <= 2.

Run:  python scripts/compare_blast_experiments.py
      (writes reports/experiments/blast_experiments_comparison.md)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp_security.static_scoring.pipeline import band_label

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP_ROOT = REPO_ROOT / "reports" / "experiments"
SERVERS = ("calendar_real", "slack_real", "fs_corp")

# experiment label -> (dir name, file pattern relative to the server stem)
EXPERIMENTS = {
    "ctx": ("v1/five_level_v2_ctx", "{stem}.json"),
    "floor-plain": ("v1/five_level_v2_floor", "{stem}_plain.json"),
    "floor-gated": ("v1/five_level_v2_floor", "{stem}_gated.json"),
    "rowfix": ("v1/five_level_v2_rowfix", "{stem}.json"),
}


def load(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def offender_cells(baseline: dict) -> list[tuple[str, str]]:
    """(tool, asset) mutation cells the baseline priced as pinpoint on sensitive assets."""
    out = []
    for key, blast in baseline["blast_radius"].items():
        tool, asset = key.split("|", 1)
        if blast is None:
            continue
        if (
            baseline["tool_impact"][tool] >= 4
            and baseline["asset_sensitivity"][asset] >= 4
            and blast <= 2
        ):
            out.append((tool, asset))
    return out


def cell_view(table: dict, tool: str, asset: str) -> str:
    """Render one cell as ``blast/score/band`` in this experiment's table."""
    blast = table["blast_radius"].get(f"{tool}|{asset}")
    if blast is None:
        return "na"
    s, i = table["asset_sensitivity"][asset], table["tool_impact"][tool]
    score = table["cells"][asset][tool]
    return f"b{blast} → {score:g} {band_label(s, blast, i)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=EXP_ROOT / "v1" / "blast_experiments_comparison.md"
    )
    args = parser.parse_args(argv)

    lines = [
        "# Blast-radius experiments vs `five_level_v2_fs` baseline",
        "",
        "Offender cells = mutating tools (impact ≥ 4) on sensitive assets (sensitivity"
        " ≥ 4) that the baseline priced at blast ≤ 2 — the under-scored"
        " create/delete/write cells that motivated these experiments.",
        "",
    ]
    for stem in SERVERS:
        baseline = load(EXP_ROOT / "v1" / "five_level_v2_fs" / f"{stem}.json")
        if baseline is None:
            lines.append(f"## {stem}\n\n(baseline missing — skipped)\n")
            continue
        tables = {"baseline": baseline}
        for label, (dirname, pattern) in EXPERIMENTS.items():
            t = load(EXP_ROOT / dirname / pattern.format(stem=stem))
            if t is not None:
                tables[label] = t

        lines += [f"## {baseline['server']}", "", "### Band distribution", ""]
        labels = list(tables)
        lines.append("| experiment | low | medium | high | critical | na |")
        lines.append("|---|---|---|---|---|---|")
        for label in labels:
            d = tables[label]["band_distribution"]
            lines.append(
                f"| {label} | {d['low']} | {d['medium']} | {d['high']} "
                f"| {d['critical']} | {d['na']} |"
            )

        lines += ["", "### Offender cells (blast → score band per experiment)", ""]
        offenders = offender_cells(baseline)
        header = "| tool | asset | sens | imp | " + " | ".join(labels) + " |"
        lines.append(header)
        lines.append("|" + "---|" * (4 + len(labels)))
        for tool, asset in offenders:
            cells = " | ".join(cell_view(tables[label], tool, asset) for label in labels)
            lines.append(
                f"| {tool} | {asset} | {baseline['asset_sensitivity'][asset]} "
                f"| {baseline['tool_impact'][tool]} | {cells} |"
            )
        lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[done] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
