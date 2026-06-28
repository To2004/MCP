"""Grade each risk scorer's severity against the AgentTrust ground truth.

This is the risk-scoring comparison the framework actually wants: not "did it detect
an attack?" but "does its 0--4 severity agree with the reference severity?", measured
the way graded scores are compared---rank correlation (Spearman), magnitude- and
chance-corrected agreement (quadratic-weighted Cohen's kappa), mean absolute error,
and exact / within-one-band agreement---overall and per operation category, against
the same 300 AgentTrust scenarios for every scorer (ours, CVSS, NIST, DREAD, OWASP,
and floors). External score files in ``reports/evaluation/sev_scores/<name>.json``
(e.g. the LLM judge) are picked up automatically.

Run:  uv run python scripts/evaluate_severity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import eval_metrics as m

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from agenttrust_loader import (  # noqa: E402
    EXTERNAL_SOURCES,
    SOURCES,
    Scenario,
    load_all,
    load_source,
)
from score_severity import score_all  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SCORES_DIR = REPO_ROOT / "reports" / "evaluation" / "sev_scores"
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "severity_benchmark.md"
OUT_JSON = REPO_ROOT / "reports" / "evaluation" / "severity_benchmark.json"


def _external(n: int) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    if not SCORES_DIR.exists():
        return out
    for path in sorted(SCORES_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        vals = ([int(round(float(raw.get(str(i), raw.get(i, 0))))) for i in range(n)]
                if isinstance(raw, dict) else [int(round(float(x))) for x in raw])
        if len(vals) == n:
            out[path.stem] = vals
    return out


def _metrics(pred: list[int], gt: list[int]) -> dict:
    n = len(gt)
    exact = sum(1 for a, b in zip(pred, gt, strict=True) if a == b) / n
    within1 = sum(1 for a, b in zip(pred, gt, strict=True) if abs(a - b) <= 1) / n
    return {
        "spearman": m.spearman_rho(pred, gt),
        # qwk over a 1..5 scale (severities are 0..4 -> shift by 1).
        "qwk": m.quadratic_weighted_kappa([p + 1 for p in pred], [g + 1 for g in gt], k=5),
        "mae": m.ordinal_mae(pred, gt),
        "exact": exact,
        "within1": within1,
    }


def _fmt(x, pct=False):
    if x is None:
        return "—"
    return f"{100*x:.0f}%" if pct else f"{x:+.2f}"


def _table(title: str, rows: dict[str, dict]) -> str:
    order = sorted(rows, key=lambda k: (rows[k]["spearman"] if rows[k]["spearman"] is not None else -9),
                   reverse=True)
    lines = [f"### {title}", "",
             "| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |",
             "| --- | --- | --- | --- | --- | --- |"]
    for k in order:
        r = rows[k]
        bold = "**" if k == "ours" else ""
        lines.append(f"| {bold}{k}{bold} | {_fmt(r['spearman'])} | {_fmt(r['qwk'])} | "
                     f"{_fmt(r['mae'])} | {_fmt(r['within1'], pct=True)} | "
                     f"{_fmt(r['exact'], pct=True)} |")
    lines.append("")
    return "\n".join(lines)


def _eval_set(scen: list[Scenario]) -> dict[str, dict]:
    gt = [s.severity for s in scen]
    scorers = {**score_all(scen), **_external(len(scen))}
    return {name: _metrics(pred, gt) for name, pred in scorers.items()}


def main() -> None:
    # Per-source results + an external-only pooled set + an all-pooled set.
    sets: dict[str, list[Scenario]] = {n: load_source(n) for n in SOURCES if load_source(n)}
    external = [s for n in EXTERNAL_SOURCES for s in sets.get(n, [])]
    sets["external (pooled)"] = external
    sets["all (pooled)"] = load_all()

    results = {name: _eval_set(scen) for name, scen in sets.items() if scen}

    out = [
        "# Severity-agreement benchmark: risk scorers vs. graded ground truth", "",
        "Each scorer maps the same extracted action features to a 0–4 severity "
        "(none..critical) through its own logic; we grade it against the reference "
        "severity by rank correlation (Spearman ρ), magnitude-/chance-corrected "
        "agreement (quadratic-weighted Cohen's κ), mean absolute band error (MAE), and "
        "within-one / exact agreement. This is a risk-*scoring* comparison, not attack "
        "detection. AgentTrust sources are external (third-party); `mcp_native` is an "
        "author-created MCP-specific set (secondary).", "",
    ]
    headline = "external (pooled)"
    out.append(_table(f"HEADLINE — {headline} ({len(sets[headline])} scenarios)",
                      results[headline]))
    for name in [*SOURCES, "all (pooled)"]:
        if name in results and name != headline:
            out.append(_table(f"{name} ({len(sets[name])} scenarios)", results[name]))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"sizes": {k: len(v) for k, v in sets.items()}, "results": results},
                   indent=2, default=str), encoding="utf-8")
    print("\n".join(out))
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)} and {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
