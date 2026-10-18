"""Tests for the program's design-time repairs of a model's rule (v13)."""

from mcp_security.input_rules import (
    CREDENTIAL_WORDS,
    evaluate_input,
    levels_covered,
    rule_problems,
    with_credential_words,
    with_register_assets,
)

REGISTER = {"helios-public-site": 1, "helios-ot-runbooks": 4, "helios-scada-gateway": 5}


def test_register_rule_carries_the_policy_register_and_keeps_words_only_where_needed():
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["docs"], "level": 1}, {"contains": ["tools"], "level": 2},
        {"contains": ["infra"], "level": 3}, "junk"]}
    fixed = with_register_assets(rule, REGISTER)
    assert fixed["assets"] == REGISTER
    assert fixed["groups"] == [{"contains": ["tools"], "level": 2},
                               {"contains": ["infra"], "level": 3}]
    assert levels_covered(fixed) == {1, 2, 3, 4, 5}
    assert with_register_assets(rule, {}) is rule
    assert with_register_assets({"kind": "keywords", "groups": []}, REGISTER)["kind"] == "keywords"


def test_a_register_rule_looks_up_its_own_table_at_run_time():
    rule = with_register_assets({"kind": "register", "groups": [], "default": 3}, REGISTER)
    row = {"path": "repo", "rule": rule}
    assert evaluate_input(row, {"repo": "helios-scada-gateway"}).level == 5
    assert evaluate_input(row, {"repo": "helios-public-site"}).level == 1
    assert evaluate_input(row, {"repo": "unlisted"}).level == 3


def test_a_bad_register_table_is_a_problem():
    rule = {"kind": "register", "groups": [], "default": 3, "assets": {"x": 9}}
    assert any("assets" in p for p in rule_problems({"rule": rule}, frozenset({"repo"})))


def test_text_rules_rate_credentials_at_5_once():
    rule = {"kind": "keywords", "default": 3, "groups": [{"contains": ["readme"], "level": 1}]}
    fixed = with_credential_words(with_credential_words(rule))
    assert sum(g.get("added_by") == "program" for g in fixed["groups"]) == 1
    row = {"path": "path", "rule": fixed}
    for path in ("deploy/.env", "keys/id_rsa", "home/.ssh/config", "notes/DB_PASSWORD.txt"):
        assert evaluate_input(row, {"path": path}).level == 5, path
    assert evaluate_input(row, {"path": "README.md"}).level == 1
    assert "password" in CREDENTIAL_WORDS


def test_credential_words_skip_other_kinds_and_named_registers():
    ranges = {"kind": "ranges", "measure": "value", "ranges": [], "default": 3}
    assert with_credential_words(ranges) is ranges
    named = {"kind": "register", "groups": [], "default": 3, "assets": REGISTER}
    assert with_credential_words(named) is named
    unnamed = {"kind": "register", "groups": [], "default": 3}
    assert with_credential_words(unnamed)["groups"][-1]["level"] == 5
    broken = {"kind": "keywords", "groups": "x", "default": 3}
    assert with_credential_words(broken) is broken


def test_without_a_policy_an_override_is_dropped_and_the_rule_kept():
    rule = {"kind": "register", "default": 3, "groups": [{"contains": ["docs"], "level": 1}],
            "overrides": [{"asset": "top-secret-data", "level": 5}]}
    fixed = with_register_assets(rule, {})
    assert "overrides" not in fixed and fixed["groups"] == rule["groups"]
