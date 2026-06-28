"""Diagnose where the framework's severity scorer disagrees with ground truth.

Produces the "what went wrong" view for ``ours`` against the AgentTrust ground
truth: a 5x5 confusion matrix, the signed bias per category and per source (does it
over- or under-score?), the obfuscation effect (clean vs adversarial-bypass set), and
the worst individual disagreements (|error| >= 2) with the offending action text — so
the failure modes are concrete, not just an aggregate number.

Run:  uv run python scripts/analyze_severity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from agenttrust_loader import SEVERITY_NAME, Scenario, load_all, load_source  # noqa: E402
from score_severity import ours  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "severity_analysis.md"


def _confusion(scen: list[Scenario]) -> list[list[int]]:
    mat = [[0] * 5 for _ in range(5)]  # rows = GT, cols = ours
    for s in scen:
        mat[s.severity][ours(s)] += 1
    return mat


def _confusion_md(mat: list[list[int]]) -> list[str]:
    head = "| GT \\ ours | " + " | ".join(SEVERITY_NAME[c] for c in range(5)) + " |"
    sep = "| --- |" + " --- |" * 5
    lines = [head, sep]
    for g in range(5):
        row = " | ".join(str(mat[g][c]) for c in range(5))
        lines.append(f"| **{SEVERITY_NAME[g]}** | {row} |")
    return lines


def _bias_by(scen: list[Scenario], key) -> list[str]:
    groups: dict[str, list[int]] = {}
    for s in scen:
        groups.setdefault(key(s), []).append(ours(s) - s.severity)
    lines = ["| group | n | mean signed error | direction |", "| --- | --- | --- | --- |"]
    for g, errs in sorted(groups.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        mean = sum(errs) / len(errs)
        direction = "over-scores" if mean > 0.2 else "under-scores" if mean < -0.2 else "calibrated"
        lines.append(f"| {g} | {len(errs)} | {mean:+.2f} | {direction} |")
    return lines


def _worst(scen: list[Scenario], n: int = 15) -> list[str]:
    rows = []
    for s in scen:
        err = ours(s) - s.severity
        if abs(err) >= 2:
            rows.append((abs(err), err, s))
    rows.sort(key=lambda r: -r[0])
    lines = ["| source | GT | ours | action |", "| --- | --- | --- | --- |"]
    for _, err, s in rows[:n]:
        snippet = (s.raw_content or s.description)[:60].replace("|", "\\|")
        arrow = "↑over" if err > 0 else "↓under"
        lines.append(f"| {s.source} | {SEVERITY_NAME[s.severity]} | "
                     f"{SEVERITY_NAME[ours(s)]} ({arrow}) | `{snippet}` |")
    return lines, len(rows)


def main() -> None:
    all_scen = load_all()
    internal = load_source("agenttrust_internal")
    independent = load_source("agenttrust_independent")  # obfuscated bypasses

    def mae(scen):
        return sum(abs(ours(s) - s.severity) for s in scen) / len(scen) if scen else 0.0

    out = [
        "# Problem analysis: where the framework's severity scorer fails", "",
        "Diagnostics for `ours` (the framework's static rubric: "
        "Impact×Sensitivity×Irreversibility + band map) against the graded ground truth.",
        "",
        "## Confusion matrix (external pooled, rows = ground truth, cols = ours)", "",
        *_confusion_md(_confusion([s for s in all_scen if s.source != "mcp_native"])),
        "",
        "A scorer that agreed perfectly would be diagonal. Mass below the diagonal = "
        "**under-scoring** (calling risky actions safe); above = over-scoring.",
        "",
        "## Signed bias by category (mean of ours−GT)", "",
        *_bias_by([s for s in all_scen if s.source != "mcp_native"], lambda s: s.category),
        "",
        "## Signed bias by source", "",
        *_bias_by(all_scen, lambda s: s.source),
        "",
        "## Obfuscation effect (the sharpest failure)", "",
        f"- clean scenarios (agenttrust_internal): MAE **{mae(internal):.2f}**",
        f"- obfuscated bypasses (agenttrust_independent): MAE **{mae(independent):.2f}**",
        "",
        "The independent set hides intent behind shell tricks "
        "(`CMD=rm; ARGS='-rf /'; $CMD $ARGS`, base64, variable expansion). The static "
        "feature extractor cannot normalize these, so destructive actions read as benign "
        "— the rank correlation there goes *negative*. This is the clearest argument for "
        "a semantic / LLM normalization stage ahead of the rubric.",
        "",
    ]
    worst_lines, n_worst = _worst(all_scen)
    out += [f"## Worst disagreements ({n_worst} scenarios off by ≥2 bands; top 15)", "",
            *worst_lines, ""]

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
