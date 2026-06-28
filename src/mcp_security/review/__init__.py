"""Independent LLM reviewers for the scan-and-rank pipeline.

Components that close the scientific loop:

* :mod:`.verify` — a **deterministic correctness verifier** that re-derives every
  published artifact (scan formula, band counts, ranked-call faithfulness, leakage
  paths) with no LLM. The hard gate: did the pipeline actually produce what it claims?
* :mod:`.judge` — an independent **methodology judge** that audits the pipeline for
  data leakage, hardcoded scores, mistakes, and scientific validity (one verdict per
  claim), plus a **results-quality verdict** over the measured outcomes.
* :mod:`.advisor` — a **results advisor** that reads the scan accuracy and ranked
  calls and proposes concrete next steps.

``verify`` needs no model; the LLM modes use the local LLM only (Qwen2.5 via Ollama)
and write markdown to ``reports/review/``. They are evaluators: nothing in the
scanner or ranker imports them.
"""

from .advisor import advise
from .judge import judge_results, run_audit
from .verify import run_verification

__all__ = ["run_audit", "advise", "judge_results", "run_verification"]
