"""Discrimination test: does the dynamic signal separate benign from adversarial sessions?

There is no external per-session ground truth for "this agent is malicious" (see
``reports/severity_eval/SUMMARY.md`` for why one barely exists). Instead the
labels come from the synthetic testbed by construction
(``scripts/make_dynamic_testbed.py``): a session's ``run_id`` prefix says whether
it is ``benign`` or an ``insider``/``external`` attack.

The claim under test is deliberately relative, not absolute: *does adding the
dynamic signal (baseline + sequence) separate benign from adversarial sessions
better than the static band alone?* We therefore score every session twice —
static-only and static⊗dynamic — and report both, so the delta is the dynamic
side's contribution and nothing is hidden.

Run (after make_dynamic_testbed.py)::

    uv run python scripts/evaluate_dynamic.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from mcp_security.call_scoring.loader import load_calls
from mcp_security.call_scoring.score import ScoredCall, score_call
from mcp_security.call_scoring.tables import load_scan
from mcp_security.dynamic.baseline import build_baselines
from mcp_security.dynamic.combine import score_session
from mcp_security.param_scoring.combine import BAND_RANK

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
SESSIONS_DIR = REPO_ROOT / "logs" / "proxy" / "sessions"
OUT_DIR = REPO_ROOT / "reports" / "dynamic_eval"

# A session is "flagged" if its riskiest call reaches at least the threshold band.
# We report at both: static over-flags ordinary reads to "high", so clean
# benign/adversarial separation only appears at the "critical" threshold, which
# the read-then-exfil sequence reaches but benign reads do not.
THRESHOLDS = {"high": BAND_RANK["high"], "critical": BAND_RANK["critical"]}


def _label(run_id: str) -> str:
    """benign_* -> 'benign'; misuse_* -> 'misuse'; insider_*/external_* -> 'adversarial'.

    Misuse (accidental-insider mistakes) is its own class: it influences assets
    but carries no attack intent, so we neither treat it as clean baseline nor
    as an attack — we report where its score lands relative to the other two.
    """
    if run_id.startswith("benign"):
        return "benign"
    if run_id.startswith("misuse"):
        return "misuse"
    return "adversarial"


def _band_rank(band: str) -> int:
    return BAND_RANK.get(band, 0)


@dataclass
class SessionScore:
    server: str
    run_id: str
    label: str
    static_rank: int
    combined_rank: int


def _score_server(stem: str) -> list[SessionScore]:
    """Score every session in one server's testbed, static-only and combined."""
    scan_path = SCAN_DIR / f"{stem}.json"
    calls_path = SESSIONS_DIR / f"dyn_{stem}" / "calls.csv"
    if not scan_path.exists() or not calls_path.exists():
        return []

    table = load_scan(scan_path)
    scored: list[ScoredCall] = [score_call(c, table) for c in load_calls(calls_path)]

    by_run: dict[str, list[ScoredCall]] = defaultdict(list)
    for call in scored:
        by_run[call.run_id].append(call)

    # Baselines are built from BENIGN sessions only — you never learn "normal"
    # from the attacks you are trying to catch.
    benign_calls = [c for c in scored if _label(c.run_id) == "benign"]
    baselines = build_baselines(benign_calls)

    results: list[SessionScore] = []
    for run_id, session_calls in by_run.items():
        static_rank = max((_band_rank(c.final_band) for c in session_calls), default=0)
        verdicts = score_session(session_calls, baselines)
        combined_rank = max((_band_rank(v.final_band) for v in verdicts), default=0)
        results.append(SessionScore(stem, run_id, _label(run_id), static_rank, combined_rank))
    return results


def _metrics(scores: list[SessionScore]) -> dict:
    """Recall on adversarial, fall-out on benign, and mean session rank, per scorer.

    Reported at every threshold in :data:`THRESHOLDS`; ``mean_rank`` and the
    dynamic-only-catch count are threshold-independent (mean_rank) or reported
    per threshold (catches).
    """
    adversarial = [s for s in scores if s.label == "adversarial"]
    benign = [s for s in scores if s.label == "benign"]
    misuse = [s for s in scores if s.label == "misuse"]

    def rate(field: str, subset: list[SessionScore], threshold: int) -> float:
        if not subset:
            return 0.0
        return sum(1 for s in subset if getattr(s, field) >= threshold) / len(subset)

    def mean_rank(field: str, subset: list[SessionScore]) -> float:
        return sum(getattr(s, field) for s in subset) / len(subset) if subset else 0.0

    per_threshold: dict[str, dict] = {}
    for name, threshold in THRESHOLDS.items():
        per_threshold[name] = {
            "static": {
                "recall_adversarial": rate("static_rank", adversarial, threshold),
                "fallout_benign": rate("static_rank", benign, threshold),
                "flag_misuse": rate("static_rank", misuse, threshold),
            },
            "combined": {
                "recall_adversarial": rate("combined_rank", adversarial, threshold),
                "fallout_benign": rate("combined_rank", benign, threshold),
                "flag_misuse": rate("combined_rank", misuse, threshold),
            },
            "adversarial_caught_only_by_dynamic": sum(
                1 for s in adversarial if s.static_rank < threshold <= s.combined_rank
            ),
        }

    return {
        "n_benign": len(benign),
        "n_misuse": len(misuse),
        "n_adversarial": len(adversarial),
        "mean_rank": {
            "static_adversarial": mean_rank("static_rank", adversarial),
            "static_benign": mean_rank("static_rank", benign),
            "static_misuse": mean_rank("static_rank", misuse),
            "combined_adversarial": mean_rank("combined_rank", adversarial),
            "combined_benign": mean_rank("combined_rank", benign),
            "combined_misuse": mean_rank("combined_rank", misuse),
        },
        "thresholds": per_threshold,
    }


def _render_markdown(per_server: dict[str, dict], overall: dict) -> str:
    mr = overall["mean_rank"]
    lines = [
        "# Dynamic scoring — benign vs adversarial discrimination",
        "",
        "Self-generated discrimination test (no external benchmark exists for this",
        "task). Labels come from the synthetic testbed by construction; each session",
        "is scored **static-only** and **static⊗dynamic**, so the delta is exactly",
        "what the dynamic signal (baseline + sequence) adds. `recall` = fraction of",
        "adversarial sessions flagged; `fall-out` = fraction of benign sessions",
        "flagged (lower is better).",
        "",
        "A session's score is its riskiest call's band. Results are shown at two",
        "flag thresholds: **high** and **critical**. Static over-flags ordinary reads",
        "to *high*, so benign fall-out is high there; the read-then-exfil **sequence**",
        "signal reaches *critical*, where benign sessions rarely land — that is where",
        "the dynamic signal creates clean separation.",
        "",
        f"Session mean band-rank (low=1 … critical=4): adversarial "
        f"{mr['static_adversarial']:.2f}→{mr['combined_adversarial']:.2f} "
        f"(static→combined), misuse {mr['static_misuse']:.2f}→{mr['combined_misuse']:.2f}, "
        f"benign {mr['static_benign']:.2f}→{mr['combined_benign']:.2f}. Misuse "
        "(accidental-insider mistakes) is expected to land between benign and "
        "adversarial — it touches assets but carries no attack sequence.",
        "",
    ]
    for name, thr in overall["thresholds"].items():
        lines += [
            f"## Overall — flag threshold: {name}",
            "",
            "| scorer | recall (adversarial) | flagged (misuse) | fall-out (benign) |",
            "| --- | --- | --- | --- |",
            f"| static | {thr['static']['recall_adversarial']:.0%} | "
            f"{thr['static']['flag_misuse']:.0%} | {thr['static']['fallout_benign']:.0%} |",
            f"| combined | {thr['combined']['recall_adversarial']:.0%} | "
            f"{thr['combined']['flag_misuse']:.0%} | {thr['combined']['fallout_benign']:.0%} |",
            "",
            f"Adversarial sessions caught **only** by the dynamic signal "
            f"(static < {name} ≤ combined): {thr['adversarial_caught_only_by_dynamic']} "
            f"of {overall['n_adversarial']}.",
            "",
        ]
    lines += [
        "## Per server (critical threshold)",
        "",
        "| server | n benign | n adv | static recall | combined recall | benign fall-out | dynamic-only catches |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for stem, m in sorted(per_server.items()):
        crit = m["thresholds"]["critical"]
        lines.append(
            f"| {stem} | {m['n_benign']} | {m['n_adversarial']} | "
            f"{crit['static']['recall_adversarial']:.0%} | "
            f"{crit['combined']['recall_adversarial']:.0%} | "
            f"{crit['combined']['fallout_benign']:.0%} | "
            f"{crit['adversarial_caught_only_by_dynamic']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    all_scores: list[SessionScore] = []
    per_server: dict[str, dict] = {}
    for stem in sorted(p.name[len("dyn_") :] for p in SESSIONS_DIR.glob("dyn_*")):
        scores = _score_server(stem)
        if not scores:
            continue
        all_scores.extend(scores)
        per_server[stem] = _metrics(scores)

    if not all_scores:
        print("No testbed sessions found. Run scripts/make_dynamic_testbed.py first.")
        return 1

    overall = _metrics(all_scores)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "discrimination.json").write_text(
        json.dumps({"overall": overall, "per_server": per_server}, indent=2),
        encoding="utf-8",
    )
    summary = _render_markdown(per_server, overall)
    (OUT_DIR / "SUMMARY.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"\nWritten to {OUT_DIR}/SUMMARY.md and discrimination.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
