"""The v12 policy-slice builder returns only the rows that name the tool."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from policy_context import OWN_POLICY, POLICY_SECTIONS, policy_for_tool  # noqa: E402


def test_slice_contains_only_rows_naming_the_tool():
    policy = policy_for_tool("github", "get_file_contents")
    assert policy["assets_this_tool_can_reach"]
    assert all(r["asset"] for r in policy["assets_this_tool_can_reach"])
    assert any("path" in r["arguments"] for r in policy["special_value_rules"])
    assert any("repo" in r["arguments"] for r in policy["baseline"])


def test_tool_with_no_rows_still_gets_org_context():
    policy = policy_for_tool("calendar", "get-current-time")
    assert policy["org_context"]
    assert policy["assets_this_tool_can_reach"] == []
    assert policy["baseline"] == []


def test_calendar_register_is_read_from_the_template():
    assets = policy_for_tool("calendar", "list-events")["assets_this_tool_can_reach"]
    assert any(a["asset"] == "aurora-exec" for a in assets)


def test_unknown_server_raises():
    with pytest.raises(KeyError):
        policy_for_tool("sqlite", "read_query")


def test_every_policy_server_has_a_section():
    assert set(POLICY_SECTIONS) == {"github", "slack", "calendar", "filesystem", "github_remote"}


def test_a_server_with_its_own_policy_file_reads_that_file():
    for server, (policy_file, _levels) in OWN_POLICY.items():
        assert f"## {POLICY_SECTIONS[server]}" in policy_file.read_text(encoding="utf-8")
    remote = policy_for_tool("github_remote", "search_code")
    assert any("query" in row["arguments"] for row in remote["baseline"])  # remote arg name


def test_importance_keeps_only_when_both_questions_say_it_matters():
    from derive_input_labels import importance_rows

    def ans(affects, rank):
        return {"affects_asset": affects, "rank": rank, "effect": "which" if affects else "none",
                "reason": f"{affects}-{rank}"}

    facts = {"repo": {}, "currency": {}, "sort": {}, "limit": {}, "unanswered": {}}
    votes = [
        {"repo": ans(True, 5), "currency": ans(True, 2), "sort": ans(False, 4), "limit": ans(True, 3)},
        {"repo": ans(True, 4), "currency": ans(True, 2), "sort": ans(False, 1), "limit": ans(True, 2)},
        {"repo": ans(False, 4), "currency": ans(True, 3), "sort": ans(False, 1), "limit": ans(True, 4)},
        None]  # a failed pass is ignored
    rows = {r["path"]: r for r in importance_rows(facts, votes)}
    assert rows["repo"]["important"] and rows["repo"]["rank"] == 4.0
    assert not rows["currency"]["important"]  # affects an asset, but median rank 2
    assert not rows["sort"]["important"]      # rank 4 once, but affects no asset
    assert rows["limit"]["important"] and rows["limit"]["rank"] == 3.0
    assert rows["unanswered"]["important"] and rows["unanswered"]["decided_by"] == "default"


def test_reask_only_sends_inputs_no_pass_answered(monkeypatch):
    import derive_input_labels as d

    sent = {}

    def fake_answers(template, tool, inputs, policy, props, seed, batch_size):
        sent.update(inputs)
        return {k: {"affects_asset": False, "rank": 1, "effect": "none", "reason": "r"} for k in inputs}

    monkeypatch.setattr(d, "_answers", fake_answers)
    facts = {"a": {}, "b": {}, "c": {}}
    votes = [{"a": {}}, None, {"b": {}}]
    got = d._reask("t", {"tool_name": "x"}, facts, votes, {}, {})
    assert set(sent) == {"c"} and set(got) == {"c"}
    assert d._reask("t", {"tool_name": "x"}, {"a": {}}, votes, {}, {}) is None


def test_match_ignores_list_markers():
    from derive_input_labels import _match

    keys = {"account": {}, "fields": {}, "fields[]": {}}
    assert _match("account", keys) == "account"
    assert _match("account[]", keys) == "account"  # the model's spelling of a list-or-value
    assert _match("fields[]", keys) == "fields[]"  # exact match wins
    assert _match("timeZone", keys) is None


def test_policy_named_inputs_are_found_with_or_without_list_markers():
    from derive_input_labels import policy_named

    facts = {"calendarId": {}, "timeMin": {}, "timeMax": {}, "attendees[].email": {}, "summary": {}}
    policy = {"special_value_rules": [{"arguments": "`attendees[].email`"}],
              "baseline": [{"arguments": "`calendarId` + `timeMin` + `timeMax`"}]}
    assert policy_named(policy, facts) == {"calendarId", "timeMin", "timeMax", "attendees[].email"}
    assert policy_named({}, facts) == set()


def test_policy_named_inputs_from_the_real_policy():
    from derive_input_labels import policy_named
    from policy_context import policy_for_tool

    named = policy_named(policy_for_tool("calendar", "list-events"),
                         {"calendarId": {}, "timeMin": {}, "timeMax": {}, "timeZone": {}})
    assert {"timeMin", "timeMax"} <= named and "timeZone" not in named


def test_v13_org_slice_has_the_policy_rows_and_the_whole_register():
    from policy_context import org_for_tool, register_assets

    org = org_for_tool("github", "get_file_contents")
    assert set(org) == {"org_context", "normal_workflow", "assets_this_tool_can_reach",
                        "special_value_rules", "baseline", "other_assets_of_the_organization"}
    assert all(isinstance(a["scanned_level"], int) for a in org["assets_this_tool_can_reach"])
    assert any(".env" in r["rule"] for r in org["special_value_rules"])
    reached = {a["asset"] for a in org["assets_this_tool_can_reach"]}
    others = {a["asset"] for a in org["other_assets_of_the_organization"]}
    assert not reached & others and reached | others == set(register_assets("github"))
    assert org_for_tool("sqlite", "read_query") == {} and register_assets("sqlite") == {}


def test_the_filesystem_catalog_reads_the_corp_share_policy():
    from policy_context import org_for_tool, register_assets

    org = org_for_tool("filesystem", "read_file")
    assert {a["asset"] for a in org["assets_this_tool_can_reach"]} >= {"security-keys",
                                                                       "payroll-records"}
    assert any("key material" in r["rule"] for r in org["special_value_rules"])
    assert register_assets("filesystem")["security-keys"] == 5
