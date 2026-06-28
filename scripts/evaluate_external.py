"""Grade every risk scorer as an attack detector on external MCP benchmarks.

This replaces the team's own hand-authored heatmaps with third-party ground truth:
the labeled calls of MCPSecBench / MCP-SafetyBench / MSB (see ``bench_loader``). Each
scorer's per-call risk is treated as a detector of ATTACK and graded the way the
guardrail papers do — AUC, best-F1 operating point, and recall at a fixed
false-positive budget — overall, per benchmark, and per attack class.

Scorers come from two places:
* the deterministic, no-GPU baselines in ``score_baselines`` (cvss, aivss, keyword,
  majority, random); and
* any external score files dropped in ``reports/evaluation/bench_scores/<name>.json``
  (a JSON list aligned to ``bench_loader`` order, or an ``{idx: score}`` map). The
  GPU stage writes the framework's own scores and the LLM-judge scores there, so this
  report grows to the full head-to-head without changing this script.

Run:  uv run python scripts/evaluate_external.py
"""

from __future__ import annotations

import json
from pathlib import Path

import eval_metrics as m
from bench_loader import BenchCall, load_benchcalls
from score_baselines import score_all

REPO_ROOT = Path(__file__).resolve().parents[1]
SCORES_DIR = REPO_ROOT / "reports" / "evaluation" / "bench_scores"
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "external_benchmark.md"
OUT_JSON = REPO_ROOT / "reports" / "evaluation" / "external_benchmark.json"

FPR_BUDGET = 0.10  # benign set is small (~59); 10% is the tightest meaningful budget


def _load_external_scores(n: int) -> dict[str, list[float]]:
    """Extra scorers from reports/evaluation/bench_scores/*.json (Phase-B outputs)."""
    out: dict[str, list[float]] = {}
    if not SCORES_DIR.exists():
        return out
    for path in sorted(SCORES_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            scores = [float(raw.get(str(i), raw.get(i, 0.0))) for i in range(n)]
        else:
            scores = [float(x) for x in raw]
        if len(scores) == n:
            out[path.stem] = scores
    return out


def _subset(calls: list[BenchCall], scores: list[float], label_attr: str):
    """Aligned (scores, labels) over calls that carry the requested label."""
    ss, yy, cls = [], [], []
    for c, s in zip(calls, scores, strict=True):
        y = getattr(c, label_attr)
        if y is None:
            continue
        ss.append(s)
        yy.append(y)
        cls.append(c.attack_class)
    return ss, yy, cls


def _metrics(scores: list[float], labels: list[int], classes: list[str | None]) -> dict:
    auc = m.roc_auc(scores, labels)
    f1 = m.best_f1(scores, labels)
    raf = m.recall_at_fpr(scores, labels, FPR_BUDGET)
    det = m.detection_by_class(scores, classes, labels, f1["threshold"])
    n = len(labels)
    npos = sum(labels)
    return {
        "n": n, "n_pos": npos, "n_neg": n - npos,
        "auc": auc,
        "f1": f1["f1"], "precision": f1["precision"], "recall": f1["recall"],
        "f1_threshold": f1["threshold"],
        "recall_at_fpr": raf["recall"], "fpr_budget": FPR_BUDGET, "raf_fpr": raf["fpr"],
        "by_class": det,
    }


def _fmt(x, pct=False):
    if x is None:
        return "—"
    return f"{100*x:.0f}%" if pct else f"{x:.2f}"


def _table(title: str, rows: dict[str, dict]) -> str:
    order = sorted(rows, key=lambda k: (rows[k]["auc"] if rows[k]["auc"] is not None else -1),
                   reverse=True)
    lines = [f"### {title}", "",
             "| scorer | AUC | recall@10%FPR |",
             "| --- | --- | --- |"]
    for k in order:
        r = rows[k]
        lines.append(f"| {k} | {_fmt(r['auc'])} | {_fmt(r['recall_at_fpr'], pct=True)} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    calls = load_benchcalls()
    scorers = {**score_all(calls), **_load_external_scores(len(calls))}

    result: dict[str, dict] = {"fpr_budget": FPR_BUDGET, "tasks": {}}
    # Primary task: ATTACK vs VALID. Secondary: flag ATTACK|BAD_TOOL|BAD_PARAMS vs VALID.
    blocks = []
    for label_attr, label_name in (("label_attack", "ATTACK vs VALID"),
                                   ("label_flag", "flag-worthy vs VALID")):
        per_scorer = {}
        for name, scores in scorers.items():
            ss, yy, cls = _subset(calls, scores, label_attr)
            per_scorer[name] = _metrics(ss, yy, cls)
        result["tasks"][label_attr] = per_scorer
        npos = per_scorer[next(iter(per_scorer))]["n_pos"]
        nneg = per_scorer[next(iter(per_scorer))]["n_neg"]
        blocks.append(_table(f"{label_name}  ({npos} positive / {nneg} VALID)", per_scorer))

    # Per-benchmark AUC on the primary task.
    benches = sorted({c.bench for c in calls})
    per_bench = {b: {} for b in benches}
    for name, scores in scorers.items():
        for b in benches:
            ss, yy, _ = _subset([c for c in calls if c.bench == b],
                                [s for c, s in zip(calls, scores, strict=True) if c.bench == b],
                                "label_attack")
            per_bench[b][name] = m.roc_auc(ss, yy)
    result["per_bench_auc"] = per_bench

    pb_lines = ["### Per-benchmark AUC (ATTACK vs VALID)", "",
                "| scorer | " + " | ".join(benches) + " |",
                "| --- |" + " --- |" * len(benches)]
    for name in scorers:
        pb_lines.append(f"| {name} | "
                        + " | ".join(_fmt(per_bench[b][name]) for b in benches) + " |")
    pb_lines.append("")

    out = [
        "# External-benchmark detection: risk scorers as attack detectors", "",
        f"Ground truth: {len(calls)} labeled calls from the third-party benchmarks "
        "MCPSecBench, MCP-SafetyBench, and MSB (same threat model: the MCP server is the "
        "protected asset; calls flow client→server). Each scorer's per-call risk is graded "
        "as a detector of ATTACK. We report **AUC** (threshold-free ranking quality) and "
        "**recall@10%FPR** (attacks caught at a tight false-positive budget) — the two "
        "metrics that discriminate here; single-threshold F1 collapses to the no-skill "
        "‘flag everything’ point for scorers that do not separate, so it is kept only in "
        "the JSON. Capability-only frameworks (CVSS, AIVSS) score the *tool* and cannot see "
        "the argument where the attack lives; content/context-aware scorers can.", "",
        *blocks,
        "\n".join(pb_lines),
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("\n".join(out))
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)} and {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
