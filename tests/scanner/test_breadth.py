"""Breadth classification: structure from the schema, meaning from the model."""

from __future__ import annotations

import pytest

from mcp_security.scanner import breadth
from mcp_security.scanner.breadth import (
    classify_breadth,
    classify_structural,
    classify_tool_breadth,
)
from mcp_security.static_scoring.registry import ToolSpec

_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {"type": "array", "maxItems": 50},
        "mode": {"enum": ["fast", "slow"]},
        "perPage": {"type": "integer", "maximum": 100, "default": 30},
        "timeMax": {"type": "string"},
        "branch": {"type": "string"},
    },
}


def _tool(schema: dict = _SCHEMA) -> ToolSpec:
    return ToolSpec(name="push_files", description="Push files", input_schema=schema)


def _kinds(entry: dict) -> dict[str, str]:
    return {i["name"]: i["kind"] for i in entry["inputs"]}


def test_array_is_a_count_with_its_declared_ceiling() -> None:
    """An array's length is breadth, and ``maxItems`` is a ceiling the schema states."""
    entry = classify_structural("files", _SCHEMA["properties"]["files"])
    assert entry["kind"] == "count"
    assert entry["ceiling"] == 50


def test_enum_is_never_a_quantity() -> None:
    assert classify_structural("mode", _SCHEMA["properties"]["mode"])["kind"] == "none"


def test_declared_default_is_captured() -> None:
    """The default is what applies when a caller omits the argument, so the runtime needs it."""
    assert classify_structural("perPage", _SCHEMA["properties"]["perPage"])["default"] == 30


def test_unclassified_reads_as_not_a_quantity() -> None:
    """Nothing answered yet -> ``none``, with the gap recorded in ``source`` not ``kind``."""
    entry = classify_structural("timeMax", {"type": "string"})
    assert entry["kind"] == "none", "the runtime must be able to act on this directly"
    assert entry["source"] == "unclassified", "and still know nobody decided it"
    assert classify_structural("perPage", {"type": "integer"})["source"] == "unclassified"


def test_settled_structure_is_marked_as_such() -> None:
    """An enum or array was decided, not defaulted, and says so."""
    assert classify_structural("mode", _SCHEMA["properties"]["mode"])["source"] == "schema"
    assert classify_structural("files", _SCHEMA["properties"]["files"])["source"] == "schema"


def test_structural_pass_reads_no_parameter_name() -> None:
    """Identical schemas must classify identically however the parameter is named.

    Name-based rules had made ``timeMax`` a magnitude (it contains "max") and
    ``calendarId`` a range ("calendar" contains "end"); this pins that behaviour out.
    """
    schema = {"type": "string"}
    seen = {(classify_structural(name, schema)["kind"], classify_structural(name, schema)["source"])
            for name in ("timeMax", "calendarId", "account", "count", "anything")}
    assert seen == {("none", "unclassified")}


def test_llm_off_leaves_the_gap_visible() -> None:
    entry = [i for i in classify_tool_breadth(_tool())["inputs"] if i["name"] == "timeMax"][0]
    assert (entry["kind"], entry["source"]) == ("none", "unclassified")


def test_every_parameter_is_asked_about_and_structure_wins_on_kind(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The model grades reach for all inputs; the schema still owns ``kind`` where it knows.

    Asking only about schema-ambiguous inputs left arrays — whose length *is* the fan-out —
    with no reach grade at all.
    """
    asked: list[str] = []

    def fake(prompt: str, **_: object) -> dict:
        asked.append(prompt)
        return {"inputs": [
            {"name": "files", "kind": "count", "breadth": 2, "why": "several paths"},
            {"name": "mode", "kind": "none", "breadth": 5, "why": "a mode switch"},
            {"name": "perPage", "kind": "magnitude", "breadth": 4, "why": "rows in one repo"},
            {"name": "timeMax", "kind": "range", "breadth": 4, "why": "window in one repo"},
            {"name": "branch", "kind": "none", "breadth": 3, "why": "names a whole branch"}]}

    monkeypatch.setattr(breadth, "query_ollama", fake)
    entries = {i["name"]: i for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]}
    listed = {line.split(" ")[1] for line in asked[0].splitlines()
              if line.startswith("- ") and "(declared type:" in line}
    assert listed == set(_SCHEMA["properties"]), "every parameter is graded for reach"
    assert entries["files"]["breadth"] == 2, "arrays get a reach grade too"
    assert entries["files"]["kind"] == "count", "an array's length is a count regardless"
    assert entries["files"]["source"] == "schema+llm"


def test_partial_model_reply_is_rejected_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reply that misses a parameter is discarded, never merged half-way."""
    monkeypatch.setattr(breadth, "query_ollama", lambda *_a, **_k: {
        "inputs": [{"name": "perPage", "kind": "magnitude", "breadth": 4}]})
    entry = [i for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]
             if i["name"] == "timeMax"][0]
    assert entry["source"] == "unclassified"


def test_invented_parameter_name_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """The model may label the names it was given and no others."""
    monkeypatch.setattr(breadth, "query_ollama", lambda *_a, **_k: {"inputs": [
        {"name": "perPage", "kind": "magnitude", "breadth": 4},
        {"name": "timeMax", "kind": "range", "breadth": 4},
        {"name": "invented", "kind": "count", "breadth": 2}]})
    entry = [i for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]
             if i["name"] == "perPage"][0]
    assert entry["source"] == "unclassified"


def test_unreachable_model_degrades_to_unresolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """No model, no guess — the runtime imputes rather than the scan inventing a kind."""
    monkeypatch.setattr(breadth, "query_ollama", lambda *_a, **_k: None)
    entry = [i for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]
             if i["name"] == "timeMax"][0]
    assert entry["source"] == "unclassified"


def test_no_threshold_is_ever_emitted() -> None:
    """Breadth says which argument is a quantity; how large is large is the runtime's job."""
    for entry in classify_tool_breadth(_tool())["inputs"]:
        assert "critical_trigger" not in entry
        assert "threshold" not in entry


def test_classify_breadth_covers_every_tool() -> None:
    tools = [_tool(), ToolSpec(name="noargs", description="", input_schema={})]
    result = classify_breadth(tools)
    assert set(result) == {"push_files", "noargs"}
    assert result["noargs"]["inputs"] == []


def test_breadth_is_judged_independently_of_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    """An identifier has no size but still decides which stored thing is opened."""
    monkeypatch.setattr(breadth, "query_ollama", lambda *_a, **_k: {"inputs": [
            {"name": "files", "kind": "count", "breadth": 2, "why": "several paths"},
            {"name": "mode", "kind": "none", "breadth": 5, "why": "a mode switch"},
            {"name": "perPage", "kind": "magnitude", "breadth": 4, "why": "rows in one repo"},
            {"name": "timeMax", "kind": "range", "breadth": 4, "why": "window in one repo"},
            {"name": "branch", "kind": "none", "breadth": 3, "why": "names a whole branch"}]})
    got = {i["name"]: (i["kind"], i["breadth"])
           for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]}
    assert got["branch"] == ("none", 3), "no quantity to read, but it opens a container"
    assert got["perPage"] == ("magnitude", 4)
    assert got["mode"] == ("none", 5), "an enum settled by schema still gets a reach grade"


def test_an_out_of_range_breadth_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(breadth, "query_ollama", lambda *_a, **_k: {"inputs": [
        {"name": "perPage", "kind": "magnitude", "breadth": 9},
        {"name": "timeMax", "kind": "range", "breadth": 4},
        {"name": "branch", "kind": "none", "breadth": 3}]})
    entry = [i for i in classify_tool_breadth(_tool(), use_llm=True)["inputs"]
             if i["name"] == "perPage"][0]
    assert entry["source"] == "unclassified"


def test_a_rejected_reply_is_retried_once(monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: D401
    """Rejections are formatting failures, and formatting failures retry well.

    Measured over 270 tools, every unresolved input traced to a whole-reply rejection —
    none to a model that had looked and hesitated.
    """
    calls = {"n": 0}

    def flaky(*_a: object, **_k: object) -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"inputs": [{"name": "perPage", "kind": "magnitude",
                                "breadth": 4}]}  # incomplete
        return {"inputs": [
            {"name": "files", "kind": "count", "breadth": 2, "why": "several paths"},
            {"name": "mode", "kind": "none", "breadth": 5, "why": "a mode switch"},
            {"name": "perPage", "kind": "magnitude", "breadth": 4, "why": "rows in one repo"},
            {"name": "timeMax", "kind": "range", "breadth": 4, "why": "window in one repo"},
            {"name": "branch", "kind": "none", "breadth": 3, "why": "names a whole branch"}]}

    monkeypatch.setattr(breadth, "query_ollama", flaky)
    assert _kinds(classify_tool_breadth(_tool(), use_llm=True))["timeMax"] == "range"
    assert calls["n"] == 2


def test_no_ordering_and_no_pointwise_risk_score_are_emitted() -> None:
    """The model scores each parameter against fixed anchors and orders nothing.

    v1 asked for a listwise ordering; measured over 24 tools it agreed with itself at
    Kendall tau 0.538 when the inputs were presented in reverse, and went negative on the
    largest tools. Nothing here depends on where a parameter sat in the prompt.
    """
    for entry in classify_tool_breadth(_tool())["inputs"]:
        assert "rank" not in entry
        assert "risk" not in entry
        assert "targets" not in entry
