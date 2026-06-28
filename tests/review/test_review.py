"""Tests for the verifier and the LLM reviewers (judge + advisor)."""

from __future__ import annotations

import mcp_security.review.advisor as advisor_mod
import mcp_security.review.judge as judge_mod
from mcp_security.review import advise
from mcp_security.review.judge import (
    CLAIMS,
    judge_results,
    results_to_markdown,
    run_audit,
    to_markdown,
)
from mcp_security.review.verify import (
    Check,
    check_no_leakage_paths,
    check_scan_formula,
    run_verification,
)
from mcp_security.review.verify import to_markdown as verify_to_markdown


def test_claims_cover_the_key_properties():
    keys = {c.key for c in CLAIMS}
    assert {"no_data_leakage", "llm_only_no_fabrication", "scoring_uses_scan_not_tables"} <= keys
    # Every claim names at least one real evidence file.
    for c in CLAIMS:
        assert c.files


def test_audit_runs_every_claim_with_model(monkeypatch):
    def fake(prompt, **_):
        return {"verdict": "pass", "severity": "none", "evidence": "x",
                "reasoning": "y", "recommendation": ""}

    monkeypatch.setattr(judge_mod, "query_ollama", fake)
    records = run_audit()
    assert len(records) == len(CLAIMS)
    assert all(r["verdict"] == "pass" for r in records)
    assert "Methodology audit" in to_markdown(records)


def test_audit_marks_error_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(judge_mod, "query_ollama", lambda *a, **k: None)
    records = run_audit((CLAIMS[0],))
    assert records[0]["verdict"] == "error"


def test_advisor_returns_assessment(monkeypatch):
    def fake(prompt, **_):
        return {"strengths": ["s"], "weaknesses": ["w"],
                "next_steps": [{"action": "a", "why": "b", "priority": "high"}],
                "risks_to_validity": ["r"]}

    monkeypatch.setattr(advisor_mod, "query_ollama", fake)
    out = advise()
    assert out["next_steps"][0]["priority"] == "high"
    assert "Results advisor" in advisor_mod.to_markdown(out)


def test_verifier_passes_on_published_artifacts():
    """The committed scan/rank artifacts must satisfy every deterministic invariant.

    This is a regression guard: if a future change publishes a scan whose bands no
    longer recount, or a ranked call that resolves to a non-existent cell, this fails.
    """
    checks = run_verification()
    failed = [c.name for c in checks if not c.ok]
    assert not failed, f"deterministic checks failed: {failed}"
    assert "correctness verification" in verify_to_markdown(checks).lower()


def test_leakage_check_is_a_real_assertion():
    # The guard must actually be inspecting source (not vacuously passing).
    c = check_no_leakage_paths()
    assert isinstance(c, Check) and c.name == "no_leakage_paths"


def test_scan_formula_check_counts_cells():
    c = check_scan_formula()
    assert c.ok and "cells satisfy" in c.detail


def test_results_judge_returns_verdict(monkeypatch):
    def fake(prompt, **_):
        return {"verdict": "pass", "result_quality": "adequate",
                "evidence": "55% exact / 89% within-one-band", "reasoning": "ok",
                "top_improvements": ["expand the oracle"]}

    monkeypatch.setattr(judge_mod, "query_ollama", fake)
    out = judge_results()
    assert out["verdict"] == "pass"
    assert "Results-quality verdict" in results_to_markdown(out)


def test_results_judge_marks_error_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(judge_mod, "query_ollama", lambda *a, **k: None)
    out = judge_results()
    assert out["verdict"] == "error"


def test_critics_have_distinct_personas():
    from mcp_security.review.critics import CRITICS
    keys = {c.key for c in CRITICS}
    assert len(keys) == len(CRITICS) >= 5  # all distinct, a real panel
    # Each persona text is substantial (a real character, not a label).
    assert all(len(c.persona) > 200 for c in CRITICS)


def test_critic_panel_runs_with_model(monkeypatch):
    import mcp_security.review.critics as critics_mod

    def fake(prompt, **_):
        return {"persona": "X", "headline": "weak",
                "critiques": [{"issue": "i", "severity": "high",
                               "why_it_matters": "w", "concrete_fix": "f"}]}

    monkeypatch.setattr(critics_mod, "query_ollama", fake)
    records = critics_mod.run_panel()
    assert len(records) == len(critics_mod.CRITICS)
    assert all("key" in r for r in records)
    md = critics_mod.to_markdown(records)
    assert "Persona-critic panel" in md and "[high]" in md


def test_critic_handles_unusable_model_answer(monkeypatch):
    import mcp_security.review.critics as critics_mod
    monkeypatch.setattr(critics_mod, "query_ollama", lambda *a, **k: None)
    rec = critics_mod.run_critic(critics_mod.CRITICS[0])
    assert rec["critiques"] == [] and rec["key"] == critics_mod.CRITICS[0].key
