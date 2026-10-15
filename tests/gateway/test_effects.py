"""Typed effect fields: a call's arguments read through the static scan's importance labels."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_security.gateway.effects import EffectMap, top_level
from mcp_security.gateway.pseudonym import Pseudonymizer

REMOTE_IMPORTANCE = Path(
    "reports/experiments/gateway/github_remote/inputs/github_remote.importance.json"
)
DAY = 86_400.0


def _argument(path: str, effect: str, important: bool = True) -> dict:
    return {"path": path, "effect": effect, "important": important}


@pytest.fixture
def effects(tmp_path: Path) -> EffectMap:
    importance = {
        "tools": [
            {
                "tool_name": "send",
                "arguments": [
                    _argument("repo", "which"),
                    _argument("limit", "how_much"),
                    _argument("to[]", "who"),
                    _argument("since", "when"),
                    _argument("until", "when"),
                    _argument("mode", "action"),
                    _argument("body", "carried"),
                    _argument("trace", "none"),
                    _argument("note", "which", important=False),
                ],
            }
        ]
    }
    path = tmp_path / "server.importance.json"
    path.write_text(json.dumps(importance))
    return EffectMap.load(path)


def test_only_important_inputs_with_an_effect_are_kept(effects: EffectMap) -> None:
    assert effects.tools["send"] == {
        "repo": "which",
        "limit": "how_much",
        "to": "who",  # "to[]" names the argument "to"
        "since": "when",
        "until": "when",
        "mode": "action",
        "body": "carried",
    }
    assert len(effects.digest) == 12


def test_a_call_becomes_typed_fields_and_never_shows_recipients_or_content(
    effects: EffectMap,
) -> None:
    args = {
        "repo": "acme/api",
        "limit": 50,
        "to": ["ann@x.org", "bob@x.org", "ann@x.org"],
        "since": "2026-01-01T00:00:00Z",
        "until": "2026-01-31",
        "mode": "draft",
        "body": "secret plan",
        "trace": "abc",
    }
    out = effects.extract("send", args, ts=0.0, pseudonyms=Pseudonymizer(b"k"))

    assert out["which"] == {"repo": "acme/api"}
    assert out["how_much"] == {"limit": 50}
    assert out["action"] == {"mode": "draft"}
    assert out["who_count"] == 3
    assert out["who"][0] == out["who"][2] != out["who"][1]  # same person, same pseudonym
    assert out["when_span_days"] == 30.0
    assert out["carried_bytes"] == len(b"secret plan")
    assert "ann@x.org" not in json.dumps(out) and "secret plan" not in json.dumps(out)


def test_one_date_is_measured_from_the_call_and_a_list_amount_is_its_length(
    effects: EffectMap,
) -> None:
    out = effects.extract(
        "send",
        {"since": {"dateTime": "1970-01-11T00:00:00"}, "limit": ["a", "b"]},
        ts=DAY,
        pseudonyms=Pseudonymizer(),
    )
    assert out == {"how_much": {"limit": 2}, "when_span_days": 9.0}


def test_comma_separated_recipients_count_one_each(effects: EffectMap) -> None:
    out = effects.extract("send", {"to": "a@x, b@x ,"}, ts=0.0, pseudonyms=Pseudonymizer())
    assert out["who_count"] == 2


def test_an_unlabelled_tool_or_unreadable_value_adds_nothing(effects: EffectMap) -> None:
    assert effects.extract("other", {"repo": "x"}, 0.0, Pseudonymizer()) == {}
    assert effects.extract("send", {"limit": True, "since": "soon"}, 0.0, Pseudonymizer()) == {}


def test_the_remote_github_scan_labels_load() -> None:
    effects = EffectMap.load(REMOTE_IMPORTANCE)
    assert effects.tools["list_commits"]["since"] == "when"
    assert effects.tools["issue_write"]["assignees"] == "who"
    assert top_level("a.b[0].c") == "a"
