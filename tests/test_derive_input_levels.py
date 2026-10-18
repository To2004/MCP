"""v13 one-step runner: answers become rows, re-asks fix only what failed."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import derive_input_levels as d  # noqa: E402

FIVE_RANGES = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
    {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
    {"min": 50, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
    {"min": 500, "max": None, "level": 5}]}
THREE_RANGES = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
    {"min": None, "max": 50, "level": 2}, {"min": 50, "max": 100, "level": 3},
    {"min": 100, "max": None, "level": 4}]}
PATHS = frozenset({"limit", "sort"})


def test_a_null_answer_drops_the_input():
    row, problems = d.judge_row({"rule": None, "reason": "presentation"}, "sort", PATHS, {})
    assert row == {"path": "sort", "status": "null", "important": False, "effect": None,
                   "reason": "presentation"} and problems == []


def test_a_rule_missing_levels_is_sent_back():
    row, problems = d.judge_row({"rule": THREE_RANGES, "reason": "r"}, "limit", PATHS, {})
    assert row is None and "[1, 5]" in problems[0]
    row, problems = d.judge_row({"rule": FIVE_RANGES, "reason": "r"}, "limit", PATHS, {})
    assert row["status"] == "rule" and row["important"] and problems == []


def test_choices_counts_booleans_and_enums():
    assert d.choices({"type": ["boolean"]}) == 2
    assert d.choices({"type": ["string"], "enum": ["a", "b", "c"]}) == 3
    assert d.choices({"type": ["integer"]}) is None


def test_reask_sends_only_failed_inputs_with_their_problems(monkeypatch, tmp_path):
    sent = []
    replies = iter([
        {"inputs": [{"path": "limit", "rule": THREE_RANGES, "reason": "r"},
                    {"path": "sort", "rule": None, "reason": "presentation"}]},
        {"inputs": [{"path": "limit", "rule": FIVE_RANGES, "reason": "r"}]},
    ])

    def fake_query(prompt, options=None, **kwargs):
        sent.append(prompt)
        return next(replies)

    monkeypatch.setattr(d, "query_ollama", fake_query)
    facts = {"limit": {"type": ["integer"]}, "sort": {"type": ["string"]}}
    decided, problems = d.levels_for_tool("{tool_json}{inputs_json}{context_inputs_json}{policy_json}",
                                          {"tool_name": "list"}, facts, {}, facts, tmp_path)
    assert decided["limit"]["status"] == "rule" and decided["sort"]["status"] == "null"
    assert problems == {} and len(sent) == 2
    assert "problems_last_time" in sent[1] and sent[1].count('"sort"') == 1  # context only
    assert "your_last_rule" in sent[1]  # a re-ask repairs the rule written last time
    assert "rule as written" not in sent[1]


def test_rows_mark_broken_and_unanswered_inputs():
    facts = {"a": {"type": ["boolean"]}, "b": {}, "c": {}}
    decided = {"a": {"path": "a", "status": "null", "important": False, "reason": "switch"}}
    failed = {"b": ["levels [1] missing", 'rule as written: {"kind": "keywords"}']}
    rows = {r["path"]: r for r in d.tool_rows(facts, decided, failed)}
    assert rows["a"]["choices"] == 2
    assert rows["b"]["status"] == "broken" and rows["b"]["important"]
    assert rows["b"]["reason"].endswith("levels [1] missing")
    assert rows["b"]["last_rule"] == '{"kind": "keywords"}'
    assert rows["c"]["status"] == "unanswered" and not rows["c"]["important"]


def test_switches_are_decided_without_asking(monkeypatch, tmp_path):
    sent = []

    def fake_query(prompt, options=None, **kwargs):
        sent.append(prompt)
        return {"inputs": [{"path": "limit", "effect": "how_much", "rule": FIVE_RANGES,
                            "reason": "r"}]}

    monkeypatch.setattr(d, "query_ollama", fake_query)
    facts = {"limit": {"type": ["integer"]}, "private": {"type": ["boolean"]},
             "mode": {"type": ["string"], "enum": ["a", "b", "c"]}}
    decided, _ = d.levels_for_tool("{tool_json}{inputs_json}{context_inputs_json}{policy_json}",
                                   {"tool_name": "t"}, facts, {}, facts, tmp_path)
    assert decided["private"]["status"] == decided["mode"]["status"] == "null"
    assert decided["limit"]["effect"] == "how_much" and len(sent) == 1


def test_level_hint_names_the_levels_name_words_must_add():
    org = {"org_context": "x"}
    hinted = d.with_level_hint(org, {"a": 1, "b": 4, "c": 5})
    assert hinted["asset_levels"] == [1, 4, 5] and hinted["name_words_needed_for"] == [2, 3]
    assert d.with_level_hint({}, {}) == {}


def test_an_asset_name_rule_uses_the_whole_register_and_drops_guessed_words():
    register = {"helios-public-site": 1, "branch-directory": 2, "issue-records": 3,
                "helios-ot-runbooks": 4, "helios-scada-gateway": 5}
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["admin"], "level": 1}, {"contains": ["finance"], "level": 5}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "repo", frozenset({"repo"}),
                                register)
    assert problems == [] and row["rule"]["groups"] == [] and row["rule"]["assets"] == register


def test_a_text_rule_needs_levels_1_to_4_and_gets_the_credential_words():
    rule = {"kind": "keywords", "default": 3, "groups": [
        {"contains": ["readme"], "level": 1}, {"contains": ["docs"], "level": 2},
        {"contains": ["src"], "level": 3}, {"contains": ["deploy"], "level": 4}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "path", frozenset({"path"}), {})
    assert problems == [] and row["rule"]["groups"][-1]["added_by"] == "program"


def test_a_reask_leaves_out_the_programs_additions():
    rule = {"kind": "keywords", "default": 3, "groups": [{"contains": ["docs"], "level": 1}]}
    _, problems = d.judge_row({"rule": rule, "reason": "r"}, "path", frozenset({"path"}), {})
    note = d._repair_note(problems)
    assert note["your_last_rule"]["groups"] == rule["groups"]


def test_placeholders_from_the_prompt_are_rejected():
    rule = {"kind": "keywords", "default": 3, "groups": [
        {"contains": ["<safest words>"], "level": 1}, {"contains": ["draft"], "level": 2},
        {"contains": ["notes"], "level": 3}, {"contains": ["salary"], "level": 4},
        {"contains": ["secret"], "level": 5}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "q", frozenset({"q"}), {})
    assert row is None and "placeholders" in problems[0]
    assert d.placeholder_problems(None) == []


def test_read_windows_are_paired_by_name_and_need_span_hours():
    facts = {"timeMin": {}, "timeMax": {}, "filter_date_after": {}, "filter_date_before": {},
             "start": {}, "end": {}, "filter_users_from": {}}
    pairs = d.window_pairs(facts)
    assert pairs == {"timeMin": "timeMax", "timeMax": "timeMin",
                     "filter_date_after": "filter_date_before",
                     "filter_date_before": "filter_date_after"}  # an event's start/end is not
    span = {"kind": "ranges", "measure": "span_hours", "with": "timeMax", "ranges": []}
    assert d.window_problems(span, "timeMax") == []
    assert d.window_problems({**span, "measure": "hours_from_now"}, "timeMax")
    assert d.window_problems(FIVE_RANGES, None) == []


def test_a_reask_is_told_which_name_words_were_dropped_and_why():
    assets = {"helios-public-site": 1, "helios-grid-infra-config": 4, "helios-scada-gateway": 5}
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["grid"], "level": 2}, {"contains": ["tools"], "level": 3}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "repo", frozenset({"repo"}), assets)
    assert row is None
    assert any("[2]" in p for p in problems)
    assert any("name word grid at level 2 was dropped" in p for p in problems)
    assert problems[-1].startswith("rule as written: ") and '"grid"' not in problems[-1]


def test_malformed_groups_are_reported_not_raised():
    # model replies are untrusted: a group with no level or a non-list must not crash a run
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["docs"]}, {"contains": "tools", "level": 2}, "junk"]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "repo", frozenset({"repo"}),
                                {"helios-scada-gateway": 5})
    assert row is None and problems


def test_an_override_only_raises_an_asset_of_the_register():
    register = {"aurora-team": 3, "aurora-crew-roster": 3, "aurora-exec": 5, "holidays": 1,
                "calendar-records": 2, "event-records": 4}
    base = {"kind": "register", "groups": [], "default": 3}
    for overrides, ok in (([{"asset": "aurora-crew-roster", "level": 5}], True),
                          ([{"asset": "<asset name>", "level": 5}], False),
                          ([{"asset": "aurora-exec", "level": 2}], False)):
        row, problems = d.judge_row({"rule": {**base, "overrides": overrides}, "reason": "r"},
                                    "calendarId", frozenset({"calendarId"}), register)
        assert (row is not None) == ok, problems


def test_an_input_the_policy_calls_risky_when_left_out_needs_a_high_when_absent():
    org = {"special_value_rules": [{"arguments": "`search_query` with no `filter_in_channel`",
                                    "rule": "crosses the blind boundary", "gates_asset": "x"}]}
    facts = {"search_query": {}, "filter_in_channel": {}}
    left_out = d.left_out_in_policy(org, facts)
    assert left_out == {"filter_in_channel": "crosses the blind boundary"}
    register = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
    rule = {"kind": "register", "groups": [], "default": 3}
    paths = frozenset(facts)
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "filter_in_channel", paths,
                                register, left_out=left_out["filter_in_channel"])
    assert row is None and "when_absent" in problems[0]
    row, _ = d.judge_row({"rule": rule, "when_absent": 4, "reason": "r"}, "filter_in_channel",
                         paths, register, left_out=left_out["filter_in_channel"])
    assert row is not None and row["when_absent"] == 4
    row, problems = d.judge_row({"rule": None, "reason": "r"}, "filter_in_channel", paths,
                                register, left_out=left_out["filter_in_channel"])
    assert row is None and "needs a rule" in problems[0]


def test_placeholders_copied_without_brackets_are_rejected():
    phrases = d.placeholder_phrases('{"contains": ["<safest words>"]}')
    assert phrases == {"safest words"}
    dots = {"kind": "keywords", "default": 3, "groups": [{"contains": ["..."], "level": 1}]}
    assert d.placeholder_problems(dots)
    rule = {"kind": "keywords", "default": 3, "groups": [
        {"contains": ["safest words"], "level": 1}, {"contains": ["draft"], "level": 2},
        {"contains": ["notes"], "level": 3}, {"contains": ["salary"], "level": 4}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "q", frozenset({"q"}), {},
                                phrases=phrases)
    assert row is None and "placeholders" in problems[0]


def test_a_server_without_a_policy_keeps_a_rule_whose_override_names_nothing():
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["public"], "level": 1}, {"contains": ["docs"], "level": 2},
        {"contains": ["data"], "level": 3}, {"contains": ["private"], "level": 4},
        {"contains": ["secure"], "level": 5}], "overrides": [{"asset": "top-secret-data", "level": 5}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "path", frozenset({"path"}), {})
    assert problems == [] and "overrides" not in row["rule"]


def test_every_call_is_logged_with_its_prompt_and_reply(tmp_path):
    path = d.log_call("the prompt", {"inputs": []}, "read_file-levels", 0, tmp_path)
    saved = json.loads(path.read_text())
    assert saved["prompt"] == "the prompt" and saved["reply"] == {"inputs": []}
    assert saved["round"] == 1 and path.parent.name == "calls"


def test_paging_email_and_switches_are_decided_without_asking():
    assert d.decided_by_program("cursor", {"type": ["string"]})["status"] == "null"
    assert d.decided_by_program("page_token", {"type": ["string"]})["status"] == "null"
    assert d.decided_by_program("timeZone", {"type": ["string"]})["status"] == "null"
    email = d.decided_by_program("attendees[].email", {"type": ["string"]})
    assert email["rule"] == {"kind": "email"} and email["status"] == "rule"
    assert d.decided_by_program("private", {"type": ["boolean"]})["status"] == "null"
    assert d.decided_by_program("limit", {"type": ["integer"]}) is None


def test_an_invented_value_is_sent_back():
    fact = {"description": "Allowed values: 'mpim', 'im', 'public_channel', 'private_channel'"}
    rule = {"kind": "values", "default": 3, "values": [
        {"value": "mpim", "level": 4}, {"value": "im", "level": 3},
        {"value": "public_channel", "level": 2}, {"value": "private_channel", "level": 5},
        {"value": "other_type", "level": 1}]}
    assert "other_type" in d.invented_values(rule, fact)[0]
    assert d.invented_values(rule, {"enum": ["mpim", "im", "public_channel", "private_channel",
                                             "other_type"]}) == []


def test_levels_outside_the_schema_bounds_cannot_count():
    rule = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 30, "level": 2},
        {"min": 30, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
        {"min": 500, "max": None, "level": 5}]}
    assert "[5]" in d.unreachable_levels(rule, {"minimum": 1, "maximum": 100})[0]  # 100 is still 4
    assert d.unreachable_levels(rule, {"minimum": 1, "maximum": None}) == []


def test_a_batch_sees_the_inputs_of_the_other_batches(monkeypatch, tmp_path):
    sent = []

    def fake_query(prompt, options=None, **kwargs):
        sent.append(prompt)
        return {"inputs": []}

    monkeypatch.setattr(d, "query_ollama", fake_query)
    monkeypatch.setattr(d, "_BATCH", 1)
    monkeypatch.setattr(d, "_ROUNDS", 1)
    facts = {"query": {"type": ["string"], "description": "the search text"},
             "channel": {"type": ["string"], "description": "the channel"}}
    d.levels_for_tool("{tool_json}{inputs_json}{context_inputs_json}{policy_json}",
                      {"tool_name": "search"}, facts, {}, facts, tmp_path)
    assert all("the search text" in s and "the channel" in s for s in sent)


def test_a_rule_row_keeps_the_schema_default():
    facts = {"limit": {"type": ["integer"], "default": 20}}
    rows = d.tool_rows(facts, {"limit": {"path": "limit", "status": "rule", "rule": FIVE_RANGES,
                                         "important": True}}, {})
    assert rows[0]["schema_default"] == 20


def test_a_values_rule_with_fewer_than_five_values_becomes_no_rule():
    rule = {"kind": "values", "default": 3, "values": [
        {"value": "mpim", "level": 3}, {"value": "im", "level": 4},
        {"value": "public_channel", "level": 2}, {"value": "private_channel", "level": 5}]}
    row, problems = d.judge_row({"rule": rule, "reason": "r"}, "channel_types",
                                frozenset({"channel_types"}), {})
    assert problems == [] and row["status"] == "null"


def test_identifiers_are_recognised_by_their_last_word():
    for path in ("channel_id", "calendarId", "pull_number", "calendars[].id", "events[].eventId"):
        assert d.is_identifier(path), path
    for path in ("valid", "grid", "limit", "identity", "numberOfDays"):
        assert not d.is_identifier(path), path


def test_a_record_number_is_dropped_without_asking_unless_the_policy_names_it():
    fact = {"type": ["integer"], "description": "The pull request number"}
    row = d.decided_by_program("pull_number", fact)
    assert row["status"] == "null" and "record number" in row["reason"]
    assert d.decided_by_program("pull_number", fact, frozenset({"pull_number"})) is None
    assert d.decided_by_program("channel_id", {"type": ["string"]}) is None


def test_an_id_keeps_a_rule_only_as_a_lookup_in_the_register():
    register = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
    paths = frozenset({"eventId", "channel_id"})
    sized = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
        {"min": 50, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
        {"min": 500, "max": None, "level": 5}]}
    row, problems = d.judge_row({"rule": sized, "reason": "r"}, "eventId", paths, register)
    assert row["status"] == "null" and "id" in row["reason"] and problems == []
    lookup = {"kind": "register", "groups": [], "default": 3}
    row, _ = d.judge_row({"rule": lookup, "reason": "r"}, "channel_id", paths, register)
    assert row["status"] == "rule"
    row, _ = d.judge_row({"rule": lookup, "reason": "r"}, "channel_id", paths, {})
    assert row["status"] == "null"  # no policy: no register to look the id up in
    row, _ = d.judge_row({"rule": sized, "reason": "r"}, "eventId", paths, register,
                         policy_named=True)
    assert row["status"] == "rule"


def test_left_out_is_at_most_ordinary_unless_the_policy_calls_it_risky():
    register = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
    rule = {"kind": "register", "groups": [], "default": 3}
    paths = frozenset({"account"})
    row, _ = d.judge_row({"rule": rule, "when_absent": 5, "reason": "r"}, "account", paths,
                         register)
    assert row["when_absent"] == 3
    row, _ = d.judge_row({"rule": rule, "when_absent": 5, "reason": "r"}, "account", paths,
                         register, left_out="a search with no account crosses the boundary")
    assert row["when_absent"] == 5


def test_overrides_on_a_rule_that_is_not_an_asset_name_rule_are_ignored():
    rule = {"kind": "ranges", "measure": "value", "default": 3, "overrides": [None], "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
        {"min": 50, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
        {"min": 500, "max": None, "level": 5}]}
    assert d.override_problems(rule, {"a": 1}) == []
