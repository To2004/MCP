"""Tests for the run statistics report's grouping helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import input_level_stats as s  # noqa: E402


def test_program_reasons_are_told_from_model_reasons():
    assert s.drop_reason("fewer than five possible values; decided by the program") == (
        "Fewer than five possible values", "program")
    assert s.drop_reason("a record number: the policy cannot tell one from another; decided "
                         "by the program")[1] == "program"
    assert s.drop_reason("The title is a label next to the main content.") == (
        "A label next to the main content", "model")
    assert s.drop_reason("The event ID is a record inside the chosen calendar.")[0] == (
        "A record inside an asset another input picked")
    assert s.drop_reason("something else entirely") == s.OTHER_REASON


def test_input_names_and_level_sources():
    assert s.input_name("events[].attendees[].email") == "email"
    assert s.level_source({"kind": "register", "assets": {"a": 1}}).startswith("scan")
    assert s.level_source({"kind": "register"}).startswith("agent")
    assert s.level_source({"kind": "email"}).startswith("policy")
    assert s.level_source({"kind": "ranges"}) == "agent"
