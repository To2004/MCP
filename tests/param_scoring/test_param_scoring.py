"""Tests for input-parameter scoring: cutoffs, combine rules, application, derive."""

from __future__ import annotations

import mcp_security.param_scoring.derive as derive_mod
from mcp_security.param_scoring import (
    ToolRubric,
    combine_avg,
    escalate,
    score_call_params,
    value_band,
)
from mcp_security.param_scoring.rubric import Cutoff, ParamRubric

# The calendar "attendees" rubric from docs/standards/parameter-scoring.md.
_ATTENDEES = ParamRubric(
    name="attendees",
    base_rank="medium",
    extract="list_length",
    cutoffs=(Cutoff(3, "medium"), Cutoff(7, "high"), Cutoff(11, "high"), Cutoff(21, "critical")),
)


def test_value_band_cutoffs():
    assert value_band(2, _ATTENDEES.cutoffs) == "low"      # below smallest cutoff
    assert value_band(5, _ATTENDEES.cutoffs) == "medium"
    assert value_band(20, _ATTENDEES.cutoffs) == "high"
    assert value_band(50, _ATTENDEES.cutoffs) == "critical"


def test_combine_avg_matches_user_rule():
    # medium base + critical value -> high (the worked example).
    assert combine_avg("medium", "critical") == "high"
    assert combine_avg("low", "low") == "low"
    assert combine_avg("high", "critical") == "critical"
    assert combine_avg("medium", "medium") == "medium"


def test_escalate_takes_more_severe():
    assert escalate("medium", "high") == "high"
    assert escalate("critical", "low") == "critical"


def test_score_call_params_list_length():
    rubric = ToolRubric("create_event", (_ATTENDEES,))
    # 20 attendees -> value_band high -> param risk avg(medium, high) = high.
    score = score_call_params({"attendees": list(range(20))}, rubric)
    assert score.band == "high" and score.top_param == "attendees"


def test_score_call_params_number_and_no_match():
    rubric = ToolRubric("x", (ParamRubric("n", "high", "number", (Cutoff(10, "high"),)),))
    assert score_call_params({"n": 50}, rubric).band == "high"
    # Missing parameter -> no signal.
    assert score_call_params({}, rubric).band is None


def test_parsed_limit_unbounded_is_worst():
    rubric = ToolRubric(
        "read_query",
        (ParamRubric("query", "medium", "parsed_limit", (Cutoff(1000, "high"),)),),
    )
    # No LIMIT in the query -> unbounded -> hits the top cutoff band.
    bounded = score_call_params({"query": "SELECT * FROM t LIMIT 5"}, rubric)
    unbounded = score_call_params({"query": "SELECT * FROM t"}, rubric)
    assert bounded.band == "low" or bounded.details[0]["value_band"] == "low"
    assert unbounded.details[0]["value"] == "unbounded"


def test_boolean_param_uses_when_true():
    rubric = ToolRubric("rm", (ParamRubric("recursive", "high", "boolean", when_true="critical"),))
    assert score_call_params({"recursive": True}, rubric).band == "critical"
    assert score_call_params({"recursive": False}, rubric).band is None


def test_derive_parses_model_json(monkeypatch):
    def fake(prompt, **_):
        return {"tool_name": "create_event", "parameters": [
            {"name": "attendees", "base_rank": "medium", "extract": "list_length",
             "cutoffs": [{"min": 3, "band": "medium"}, {"min": 21, "band": "critical"}]}]}

    monkeypatch.setattr(derive_mod, "query_ollama", fake)
    from mcp_security.static_scoring.registry import ToolSpec

    rubric = derive_mod.derive_tool_rubric(ToolSpec("create_event", "Create a calendar event"))
    assert rubric.parameters[0].name == "attendees"
    assert rubric.parameters[0].cutoffs[-1].band == "critical"


def test_most_influential_round_trips():
    rubric = ToolRubric(
        "transfer_funds",
        (ParamRubric("amount", "high", "number", (Cutoff(10000, "critical"),)),),
        most_influential="amount",
    )
    restored = ToolRubric.from_dict(rubric.to_dict())
    assert restored.most_influential == "amount"


def test_most_influential_defaults_empty_on_old_rubric():
    # A rubric dict predating the field (no "most_influential" key) loads as "".
    restored = ToolRubric.from_dict({"tool_name": "x", "parameters": []})
    assert restored.most_influential == ""


def test_derive_parses_most_influential(monkeypatch):
    def fake(prompt, **_):
        return {
            "tool_name": "send_email_invite",
            "most_influential": "recipients",
            "parameters": [
                {"name": "recipients", "base_rank": "medium", "extract": "list_length",
                 "cutoffs": [{"min": 50, "band": "critical"}]}
            ],
        }

    monkeypatch.setattr(derive_mod, "query_ollama", fake)
    from mcp_security.static_scoring.registry import ToolSpec

    rubric = derive_mod.derive_tool_rubric(ToolSpec("send_email_invite", "Send an invite"))
    assert rubric.most_influential == "recipients"
