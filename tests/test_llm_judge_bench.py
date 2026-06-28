"""Offline tests for the LLM-judge parse logic (no model contacted)."""

from __future__ import annotations

from scripts.llm_judge_bench import parse_verdict


def test_parse_verdict_uses_risk_when_valid():
    assert parse_verdict({"attack": True, "risk": 4}) == 4.0
    assert parse_verdict({"attack": False, "risk": 1}) == 1.0


def test_parse_verdict_clamps_to_bool_when_risk_out_of_range():
    assert parse_verdict({"attack": True, "risk": 9}) == 3.0
    assert parse_verdict({"attack": False}) == 1.0


def test_parse_verdict_neutral_on_garbage():
    assert parse_verdict(None) == 2.0
    assert parse_verdict({}) == 2.0
    assert parse_verdict({"foo": "bar"}) == 2.0
