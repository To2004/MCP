"""Tests for the v5r operation-type ladder (`classify_by_operation`).

The v4/v5 ladder is tested in ``test_static_impact.py`` and must keep passing —
this file only covers what the rewrite changed.
"""

from __future__ import annotations

from mcp_security.static_scoring import static_impact
from mcp_security.static_scoring.registry import ToolSpec


def _tier(name: str, description: str = "", **kw) -> int:
    return static_impact.classify_by_operation(ToolSpec(name, description, **kw)).tool_impact


def _verdict(name: str, description: str = "", **kw):
    return static_impact.classify_by_operation(ToolSpec(name, description, **kw))


# --- the ladder -------------------------------------------------------------


def test_ladder_by_operation():
    assert _tier("get-current-time", "Get the current date and time.") == 1
    assert _tier("list-calendars", "List all available calendars") == 2
    assert _tier("get-event", "Get the full details of one event.") == 3
    assert _tier("create-event", "Create a calendar event.") == 4  # ordinary write
    assert _tier("post_reply", "Add a reply to a thread.") == 3  # limited write
    assert _tier("write_file", "Overwrite the entire contents of a file.") == 4
    assert _tier("delete-event", "Delete a calendar event.") == 5


def test_a_limited_write_shares_tier_three_with_a_content_read():
    # PATCH semantics: a bounded amount, the rest of the item untouched.
    read = _tier("get_file_contents", "Get the contents of a file.")
    write = _tier("add_issue_comment", "Add a comment to an existing issue.")
    assert read == write == 3


def test_a_write_is_ordinary_unless_it_states_a_limit():
    # The default is the ordinary write (PUT / CVSS total loss for that item).
    assert _tier("create_record", "Create a record in the table.") == 4
    assert _tier("write_file", "Overwrite the contents of a file.") == 4
    # ...and drops only where the declaration bounds the amount written.
    assert _tier("update_record", "Append a note to one record.") == 3
    assert _tier("set_field", "Set one field on the record.") == 3


def test_breadth_is_not_an_impact_signal():
    # HOW MANY items a call reaches is coverage — blast radius scores it. The
    # impact ladder is silent on it, so a bulk variant is the same OPERATION as
    # its singular: both land on the ordinary-write tier, neither is promoted.
    assert _tier("update_record", "Update the record.") == 4
    assert _tier("update_records", "Update every record in the table.") == 4
    assert _tier("write_many", "Write multiple files in bulk.") == 4
    # A limited write stays limited however many items it is pointed at.
    assert _tier("append_one", "Append a line.") == 3
    assert _tier("append_many", "Append a line to every file in bulk.") == 3


def test_an_array_parameter_is_not_breadth():
    # An array of attendees on create-event is one event, not many. Bulk variants
    # are handled by the assembly's bulk-twin pass instead.
    tool = ToolSpec(
        "create-event",
        "Create a calendar event.",
        input_schema={"properties": {"attendees": {"type": "array"}}},
    )
    verdict = static_impact.classify_by_operation(tool)
    assert verdict.tool_impact == 4
    assert verdict.is_bulk is True  # still recorded, just not a tier promotion


# --- what left the ladder ---------------------------------------------------


def test_no_annotation_ceiling():
    # A server claiming read-only while describing a delete does not get to cap
    # its own score: the description wins and the contradiction is recorded.
    verdict = _verdict("cleanup", "Delete every expired record.", read_only_hint=True)
    assert verdict.tool_impact == 5
    assert verdict.annotation_bound is None
    assert any("CONTRADICTED" in e for e in verdict.evidence)


def test_destructive_hint_does_not_raise_the_tier():
    plain = _tier("update_row", "Update one row.")
    hinted = _tier("update_row", "Update one row.", destructive_hint=True)
    assert plain == hinted == 4


def test_an_outbound_send_is_a_write_not_a_removal():
    # The channel is not the operation: sending creates a message, so it lands on
    # a write tier rather than on removal.
    assert _tier("send_email_invite", "Send an email invitation to an attendee.") in (3, 4)
    assert _tier("post_message", "Post a message to a channel.") in (3, 4)
    assert _tier("send_email_invite", "Send an email invitation.") != 5


# --- the general rules that replaced the per-tool special cases --------------


def test_generic_read_verb_is_not_evidence_of_content():
    # Replaces the three-branch "object decides" rule written for directory_tree.
    assert _tier("directory_tree", "Get a recursive tree view listing names and types.") == 2
    assert _tier("get_pull_request_status", "Get the status of a pull request.") == 2
    # A specific read verb still reaches content.
    assert _tier("read_file", "Read the contents of a file.") == 3


def test_longest_match_wins_over_a_word_inside_it():
    # Replaces nothing — this case used to need a rigid `mark (as )?read` pattern.
    verdict = _verdict("conversations_mark", "Mark a channel or DM as read.")
    assert verdict.tool_impact == 2
    assert any("longer phrase" in e for e in verdict.evidence)


def test_a_multi_word_phrase_is_matched_across_the_description():
    # "mark" alone is ambiguous and name-only; the phrase is not.
    assert _tier("conversations_mark", "Marks all messages as read.") == 2


def test_liveness_probe_must_be_named_one():
    assert _tier("healthcheck", "Report whether the service is up.") == 1
    assert _tier("get_server_version", "Return the running version.") == 1
    # A tool merely REPORTING health is not itself a probe — it is named for what
    # it returns, so it stays metadata. Name-only scoping is what draws the line.
    assert _tier("get_status", "Get server health and version.") == 2
    # ...and prose about capabilities does not make a read a ping.
    assert _tier("list_tools", "List the tools and their capabilities.") == 2


# --- the abstention that v5's hand-off keys on ------------------------------


def test_no_verb_evidence_abstains_with_low_confidence():
    verdict = _verdict("frobnicate", "Applies the configured transformation.")
    assert verdict.confidence == 0.35
    assert any("no verb evidence" in e for e in verdict.evidence)


def test_verb_evidence_reports_full_confidence():
    assert _verdict("delete_file", "Delete a file.").confidence == 0.8


def test_a_write_that_states_no_limit_abstains():
    # Tier 4 here is the DEFAULT, not a finding: the declaration never says
    # whether the amount written is bounded, so the model decides.
    verdict = _verdict("create_issue", "Create an issue in a repository.")
    assert verdict.tool_impact == 4
    assert verdict.confidence == 0.35
    assert any("(unsure)" in e for e in verdict.evidence)
    # Bulk wording does not rescue it — breadth is not what this tier asks about.
    assert _verdict("push_files", "Push multiple files in one commit.").confidence == 0.35


def test_a_limited_write_is_confident():
    verdict = _verdict("append_note", "Append a note, leaving the rest intact.")
    assert verdict.tool_impact == 3
    assert verdict.confidence == 0.8


def test_a_replacing_write_is_confident():
    verdict = _verdict("write_file", "Overwrite the file contents.")
    assert verdict.tool_impact == 4
    assert verdict.confidence == 0.8


def test_classify_all_by_operation_covers_every_tool():
    tools = [ToolSpec("a", "Read a file."), ToolSpec("b", "Delete a file.")]
    out = static_impact.classify_all_by_operation(tools)
    assert set(out) == {"a", "b"}
    assert out["b"].tool_impact == 5
