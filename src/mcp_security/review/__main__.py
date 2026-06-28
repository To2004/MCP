"""CLI for the reviewers.

    python -m mcp_security.review verify   # deterministic correctness -> correctness_verification.md
    python -m mcp_security.review judge     # methodology audit (LLM)   -> methodology_audit.md
    python -m mcp_security.review results   # results-quality verdict (LLM) -> results_verdict.md
    python -m mcp_security.review advise    # results advice (LLM)      -> results_advice.md
    python -m mcp_security.review all        # all of the above

``verify`` is deterministic and needs no model. The LLM modes (judge/results/advise)
need the local LLM (Ollama / Qwen2.5); run them on a GPU node
(`scripts/review_on_gpu.sbatch`). ``all`` runs verify first and reports a non-zero
exit code if any deterministic check fails — a hard gate on correctness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import advisor, critics, judge
from .verify import run_verification, to_markdown as verify_to_markdown

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "reports" / "review"


def _write(name: str, md: str, payload: object) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    (OUT_DIR / f"{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_verify() -> int:
    checks = run_verification()
    _write("correctness_verification", verify_to_markdown(checks),
           [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in checks])
    failed = [c.name for c in checks if not c.ok]
    print(f"Correctness verification: {len(checks) - len(failed)}/{len(checks)} pass"
          + (f" — FAILED: {failed}" if failed else "")
          + f" -> {OUT_DIR / 'correctness_verification.md'}")
    return 1 if failed else 0


def _run_judge() -> int:
    records = judge.run_audit()
    _write("methodology_audit", judge.to_markdown(records), records)
    bad = [r for r in records if r["verdict"] in ("fail", "concern")]
    print(f"Methodology audit: {len(records)} claims, {len(bad)} concern/fail "
          f"-> {OUT_DIR / 'methodology_audit.md'}")
    return 0


def _run_results() -> int:
    verdict = judge.judge_results()
    _write("results_verdict", judge.results_to_markdown(verdict), verdict)
    print(f"Results-quality verdict: {verdict.get('verdict')} "
          f"({verdict.get('result_quality')}) -> {OUT_DIR / 'results_verdict.md'}")
    return 0


def _run_advise() -> int:
    assessment = advisor.advise()
    _write("results_advice", advisor.to_markdown(assessment), assessment)
    print(f"Results advice -> {OUT_DIR / 'results_advice.md'}")
    return 0


def _run_critics() -> int:
    records = critics.run_panel()
    _write("critic_panel", critics.to_markdown(records), records)
    n = sum(len(r.get("critiques", [])) for r in records)
    print(f"Persona-critic panel: {len(records)} critics, {n} critiques "
          f"-> {OUT_DIR / 'critic_panel.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline verifier + LLM reviewers.")
    parser.add_argument("mode",
                        choices=["verify", "judge", "results", "advise", "critics", "all"],
                        help="which reviewer to run")
    args = parser.parse_args(argv)
    rc = 0
    if args.mode in ("verify", "all"):
        rc |= _run_verify()
    if args.mode in ("judge", "all"):
        rc |= _run_judge()
    if args.mode in ("results", "all"):
        rc |= _run_results()
    if args.mode in ("advise", "all"):
        rc |= _run_advise()
    if args.mode in ("critics", "all"):
        rc |= _run_critics()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
