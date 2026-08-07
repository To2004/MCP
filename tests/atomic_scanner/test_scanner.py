"""Tests for the atomic-operation tool scanner (v2)."""

from __future__ import annotations

from mcp_security.atomic_scanner import classify, ladder_tier, load_taxonomy, op_names
from mcp_security.static_scoring.registry import ToolSpec


def _ops(name: str, description: str = "", **kw) -> set[str]:
    return classify(ToolSpec(name, description, **kw)).operations


def _tier(name: str, description: str = "", **kw) -> int:
    return classify(ToolSpec(name, description, **kw)).tool_impact


def test_taxonomy_keeps_the_base_rows_verbatim():
    """The 13 base operations must survive unchanged — same rank, same severity."""
    taxonomy = load_taxonomy()
    base = {name: spec for name, spec in taxonomy.items() if spec.origin == "base"}
    assert len(base) == 13
    assert base["EXECUTE"].rank == 1 and base["EXECUTE"].severity == 5
    assert base["DELETE"].rank == 2 and base["DELETE"].severity == 5
    assert base["LIST"].rank == 13 and base["LIST"].severity == 1
    assert len(taxonomy) > 13, "the extension should add operations, not replace them"


def test_every_op_has_a_ladder_tier_in_range():
    for name in op_names():
        assert 1 <= ladder_tier(name) <= 5


def test_name_is_parsed_as_verb_plus_object():
    assert _ops("github_create_pull_request", "Create a new PR") == {"CREATE"}
    assert _ops("slack_list_channels", "Lists channels") == {"LIST"}
    assert _ops("delete_event", "Delete an event") == {"DELETE"}
    assert _tier("delete_event", "Delete an event") == 5


def test_a_late_noun_is_the_object_not_the_act():
    """`list_commits` lists; it does not commit. `journal_trade_review` reviews a
    journal entry; it does not place a trade."""
    assert "WRITE" not in _ops("list_commits", "Get list of commits of a branch")
    assert _ops("list_branches", "Lists all branches in a repository") == {"LIST"}
    assert "TRANSACT" not in _ops("journal_trade_review", "Return details for a trade entry")
    # ...but the same word FIRST is the act
    assert _ops("commit_changes", "Commit the staged changes") == {"WRITE"}
    assert "TRANSACT" in _ops("trade_execute", "Place the trade")


def test_generic_verbs_defer_to_a_specific_operation():
    """`get` names no operation of its own; the object does."""
    assert _ops("get_file_info", "Get info about a file") == {"METADATA"}
    assert _ops("get_current_time", "Get the current time") == {"NO_EFFECT"}
    # nothing more specific -> the generic read stands
    assert _ops("get_stock_price", "Get the current stock price") == {"READ"}


def test_run_is_execution_only_over_a_command():
    assert _tier("run_query", "Run the SQL query") == 5
    assert _tier("run_backtest", "Run a backtest of the strategy") == 3


def test_readonly_hint_removes_write_operations():
    """A read-only tool cannot perform a write, whatever it is called."""
    verdict = classify(ToolSpec("update_cache", "Updates the cached view.", read_only_hint=True))
    assert "MODIFY" in verdict.dropped_by_readonly
    assert verdict.tool_impact <= 3


def test_write_prefix_implies_overwrite():
    """The convention the original toollist rules encode: write_* replaces."""
    assert "OVERWRITE" in _ops("write_file", "Write content to a file")
    assert _tier("write_file", "Write content to a file") == 5


def test_unrecognised_tool_defaults_to_read():
    verdict = classify(ToolSpec("zorble_thing", "Does something unspecified."))
    assert verdict.operations == {"READ"}
    assert verdict.source == "default"


def test_operations_are_a_set_not_just_a_maximum():
    """The set is the point: a tool that reads AND deletes is worth seeing."""
    verdict = classify(ToolSpec("read_and_purge", "Reads then purges the queue."))
    assert {"READ", "DELETE"} <= verdict.operations
    assert verdict.max_op == "DELETE"
    assert verdict.tool_impact == 5
