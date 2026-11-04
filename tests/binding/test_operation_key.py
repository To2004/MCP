"""AI-7: operation keys ``tool:operation`` with a read or write label.

The tool and selector names follow the remote GitHub catalog
(``reports/experiments/gateway/github_remote/github_remote.json``).
"""

from __future__ import annotations

import pytest

from mcp_security.binding.touched_asset import (
    READ,
    WRITE,
    OperationKey,
    OperationSpec,
    operation_key,
    parse_tool_operations,
)

OPERATIONS = parse_tool_operations(
    {
        "issue_read": {
            "selector": "method",
            "ops": {"get": READ, "get_comments": READ, "get_labels": READ},
        },
        "issue_write": {
            "selector": "method",
            "ops": {"create": WRITE, "update": WRITE},
            "label": WRITE,
        },
        "pull_request_read": {"selector": "method", "ops": {"get": READ}},
        "add_issue_comment": {"label": WRITE},
    }
)
#: The scan's impact ladder for these tools (3 = read under today's rule, 4 = write).
IMPACT = {
    "issue_read": 3,
    "issue_write": 4,
    "pull_request_read": 3,
    "add_issue_comment": 3,
    "get_file_contents": 3,
}


def key_of(tool: str, args: dict, operations=OPERATIONS) -> OperationKey:
    return operation_key(tool, args, operations, IMPACT.get(tool))


def test_a_declared_operation_becomes_its_own_key_and_label() -> None:
    assert key_of("issue_read", {"method": "get"}) == OperationKey("issue_read:get", READ)
    assert key_of("issue_write", {"method": "create"}) == OperationKey("issue_write:create", WRITE)


@pytest.mark.parametrize(
    "args", [{"method": "delete_everything"}, {}, {"method": 3}, {"method": ["get"]}]
)
def test_an_undeclared_or_missing_value_is_one_unknown_key(args: dict) -> None:
    """``tool:?``: a value the scan did not declare never enters the history as text."""
    key = key_of("pull_request_read", args)
    assert key.key == "pull_request_read:?"
    assert key.label == READ  # no tool label: today's impact rule (3 is a read)
    assert key_of("issue_write", args) == OperationKey("issue_write:?", WRITE)  # tool label


def test_the_operations_label_overrides_the_tools_label_and_its_impact() -> None:
    operations = parse_tool_operations(
        {
            "ui_get": {"selector": "method", "ops": {"list": READ, "set": WRITE}, "label": WRITE},
        }
    )
    read = operation_key("ui_get", {"method": "list"}, operations, impact=5)
    assert read == OperationKey("ui_get:list", READ)
    assert operation_key("ui_get", {"method": "set"}, operations, impact=1).label == WRITE


def test_a_tool_without_a_selector_keeps_its_name() -> None:
    assert key_of("get_file_contents", {"method": "get"}) == OperationKey("get_file_contents", READ)


def test_a_comment_is_a_write_under_the_operation_labels_and_a_read_under_v4s_rule() -> None:
    assert key_of("add_issue_comment", {"body": "x"}).label == WRITE
    assert key_of("add_issue_comment", {"body": "x"}, operations={}).label == READ


def test_the_impact_rule_and_its_absence() -> None:
    assert operation_key("merge", {}, {}, impact=5).label == WRITE
    assert operation_key("merge", {}, {}, impact=4).label == WRITE
    assert operation_key("list", {}, {}, impact=None) == OperationKey("list", None)


def test_non_object_arguments_give_the_unknown_key() -> None:
    assert key_of("issue_read", "get").key == "issue_read:?"  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw",
    [
        ["issue_read"],
        {"t": "method"},
        {"t": {"selector": "method", "ops": ["get"]}},
        {"t": {"selector": "method", "ops": {"get": "delete"}}},
        {"t": {"ops": {"get": READ}}},
        {"t": {"label": "admin"}},
    ],
)
def test_malformed_operations_fail_at_load(raw: object) -> None:
    with pytest.raises(ValueError):
        parse_tool_operations(raw)  # type: ignore[arg-type]


def test_parse_accepts_specs_and_none() -> None:
    spec = OperationSpec("method", {"get": READ})
    assert parse_tool_operations({"t": spec}) == {"t": spec}
    assert parse_tool_operations(None) == {}
