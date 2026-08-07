"""Tests for the deterministic (no-LLM) tool-impact ladder."""

from __future__ import annotations

from mcp_security.static_scoring import static_impact
from mcp_security.static_scoring.registry import ToolSpec


def _impact(name: str, description: str = "", **kw) -> int:
    return static_impact.classify(ToolSpec(name, description, **kw)).tool_impact


def test_ladder_tiers():
    assert _impact("get-current-time", "Get the current date and time.") == 1
    assert _impact("list-calendars", "List all available calendars") == 2
    assert _impact("get-event", "Get details of a specific event by ID.") == 3
    assert _impact("create-event", "Create a new calendar event.") == 4
    assert _impact("delete-event", "Delete a calendar event.") == 5


def test_annotation_ceiling_read_only_cannot_write():
    # A declared read-only tool cannot exceed tier 3 even if its text says delete.
    assert _impact("audit_view", "View the delete history of a table", read_only_hint=True) <= 3


def test_ambiguous_words_only_count_in_the_name():
    # "notify" in prose ABOUT groups must not make a listing tool a notifier.
    assert (
        _impact(
            "usergroups_list",
            "List all user groups in the workspace. Groups are mention groups like "
            "@engineering that notify all members.",
        )
        == 2
    )
    # "email" as a SEARCH FIELD is not sending email.
    assert _impact("users_search", "Search for users by name, email, or display name.") == 3
    # but the same word IN THE NAME is the action.
    assert _impact("send_email", "Deliver a message to a recipient.") == 5


def test_separator_normalisation():
    # "push_files" must match the push verb despite the underscore: tier 4 is the
    # verb firing (the no-evidence default would be 3). See the push/force-push
    # split in test_push_is_a_write_but_force_push_is_not.
    assert _impact("push_files", "Push multiple files to a repository in one commit") == 4


def test_return_shape_caps_do_not_touch_mutations():
    # A read whose payload is availability metadata caps at 2 despite "query".
    assert _impact("get-freebusy", "Query free/busy information for calendars.") == 2
    # A DELETE that merely mentions metadata is still 5 — caps never lower a mutation.
    assert _impact("purge_metadata", "Permanently delete all metadata records.") == 5


def test_bulk_does_not_add_a_tier():
    """v4: the "bulk drops a safety -> +1 tier" rule was removed on request.

    A bulk variant is still FLAGGED (is_bulk) and the pipeline's bulk-twin pass
    still enforces impact(bulk) >= impact(singular), but the tier is no longer
    bumped for skipping a safety.
    """
    singular = _impact("create-event", "Create a new calendar event.")
    verdict = static_impact.classify(
        ToolSpec(
            "create-events",
            "Create multiple calendar events in bulk. Skips conflict and duplicate "
            "detection for speed.",
        )
    )
    assert singular == 4
    assert verdict.tool_impact == 4  # same tier as the singular, no +1
    assert verdict.is_bulk is True


def test_create_or_overwrite_is_irreversible():
    assert _impact("create_or_update_file", "Create or update a single file in a repo") == 5


def test_evidence_is_recorded():
    v = static_impact.classify(ToolSpec("delete-event", "Delete a calendar event."))
    assert v.evidence and any("tier-5" in e for e in v.evidence)
    assert "deterministic ladder" in v.reasoning


def test_negated_verbs_are_not_capabilities():
    """Descriptions embed instructions TO THE MODEL; a prohibition is not a capability.

    Real case: sec-edgar's read-only `get_company_info` says "NEVER add external
    information", which made a bare verb match score it as a tier-4 write.
    """
    assert (
        _impact(
            "get_company_info",
            "Get detailed information about a company from SEC records. "
            "CRITICAL INSTRUCTIONS: ONLY use data returned from SEC records. "
            "NEVER add external information.",
        )
        == 3
    )
    # The same verb, un-negated and in the name, is still a capability.
    assert _impact("add_issue_comment", "Add a comment to an issue") == 4


def _spec(name, description="", params=None, **kw):
    t = ToolSpec(name, description, **kw)
    if params is not None:
        t.input_schema = {"properties": params}
    return t


def test_parameter_signals_are_recorded_as_capability_flags():
    """Over-privilege lives in the INPUTS — recorded even when the tier is modest."""
    v = static_impact.classify(
        _spec(
            "run_report",
            "Generate a report.",
            {
                "sql": {"type": "string"},
                "path": {"type": "string"},
                "recursive": {"type": "boolean"},
                "send_updates": {"type": "string"},
            },
        )
    )
    kinds = " ".join(v.capability_flags)
    assert "raw-query" in kinds and "outbound" in kinds and "recursive" in kinds
    assert "unconstrained" in kinds  # no enum/pattern/format on sql or path


def test_parameters_never_move_the_tier():
    """A parameter says what the caller COULD pass; what any call DOES pass is a
    runtime fact. Impact stays a statement about the declared action, so the
    command/query parameter is flagged and nothing else."""
    plain = _impact("run_report", "Generate a report.")
    with_cmd = static_impact.classify(
        _spec("run_report", "Generate a report.", {"script": {"type": "string"}})
    )
    with_sql = static_impact.classify(
        _spec(
            "write_query", "Run an INSERT, UPDATE, or DELETE query.", {"query": {"type": "string"}}
        )
    )
    assert plain == 3
    assert with_cmd.tool_impact == 3  # flagged, not promoted
    assert any("raw-command" in f for f in with_cmd.capability_flags)
    assert with_sql.tool_impact == 5  # from the VERBS in its text, not the param
    assert any("raw-query" in f for f in with_sql.capability_flags)


def test_read_query_stays_a_content_read():
    """Arbitrary SELECT is wide REACH (blast radius), not a higher action tier."""
    read = static_impact.classify(
        _spec(
            "read_query",
            "Run a read-only SELECT query. Returns up to 100 rows.",
            {"query": {"type": "string"}},
        )
    )
    assert read.tool_impact == 3
    assert any("raw-query" in f for f in read.capability_flags)


def test_param_patterns_are_full_name_anchored():
    """An unanchored alternation matched "cc" inside "a(cc)ount", turning every
    calendar read into an outbound-messaging tool. Names must match in full."""
    v = static_impact.classify(
        _spec("list-calendars", "List all available calendars", {"account": {"type": "string"}})
    )
    assert v.tool_impact == 2
    assert not any("outbound" in f for f in v.capability_flags)


def test_constrained_parameter_is_not_flagged_unconstrained():
    v = static_impact.classify(
        _spec(
            "read_doc",
            "Read a document.",
            {"path": {"type": "string", "enum": ["a.md", "b.md"]}},
            read_only_hint=True,
        )
    )
    assert not any("unconstrained" in f for f in v.capability_flags)


def test_open_world_hint_is_not_used_here():
    """Boundary crossing moved to the DYNAMIC stage. Whether a call actually
    leaves the system depends on the arguments, not on the declaration, so the
    hint neither raises the tier nor appears as a static flag."""
    assert (
        _impact(
            "share_doc",
            "Share a document with a collaborator.",
            read_only_hint=False,
            open_world_hint=True,
        )
        == 4
    )
    v = static_impact.classify(
        ToolSpec("fetch_page", "Fetch a web page.", read_only_hint=True, open_world_hint=True)
    )
    assert v.tool_impact == 3
    assert not any("open-world" in f for f in v.capability_flags)


def test_generic_verb_does_not_beat_a_stated_metadata_return():
    """`get`/`search` mean "something comes back", not WHAT. When the description
    states its return shape and that shape is identifiers, the object wins."""
    assert (
        _impact(
            "search_files",
            "Recursively search for files matching a pattern. "
            "Returns full paths to all matching items.",
            read_only_hint=True,
        )
        == 2
    )
    assert (
        _impact(
            "directory_tree",
            "Get a recursive tree view of files and directories as a JSON structure. "
            "Each entry includes 'name', 'type' (file/directory), and 'children'.",
            read_only_hint=True,
        )
        == 2
    )


def test_a_stated_return_of_substance_stays_a_content_read():
    """The same machinery must not lower a tool that returns the substance."""
    assert _impact("get_file", "Get a file. Returns the file contents as text.") == 3
    # ...nor one whose "Returns:" block is an argument doc, not a prose shape.
    assert (
        _impact(
            "get_key_metrics",
            "Get key financial metrics for a company.\nReturns:\n  "
            "Dictionary containing list of metric values and counts",
        )
        == 3
    )


def test_container_must_be_the_object_not_the_scope():
    """A catalog of containers is metadata; a content search merely SCOPED to a
    container is not. "search_code across repositories" must stay a content read."""
    assert _impact("search_repositories", "Search for GitHub repositories") == 2
    assert _impact("search_code", "Search for code across GitHub repositories") == 3
    # singular container in the name is a dataset named after one, not a catalog
    assert _impact("get_economic_calendar", "Get upcoming economic events and indicators.") == 3


def test_named_listing_beats_a_generic_verb():
    """A tool NAMED list_x declares its own return shape."""
    assert _impact("list_commits", "Get list of commits of a branch in a GitHub repository") == 2
    # but a listing of substance is still a content read
    assert _impact("get_file_contents", "Get the contents of a file") == 3


def test_empty_is_only_destructive_as_a_verb():
    """ "a children array which may be empty" fired tier 5 on a read-only listing."""
    assert _impact("list_dir", "Returns a children array which may be empty.") == 3
    assert _impact("empty_trash", "Empty the trash folder permanently.") == 5


def test_push_is_a_write_but_force_push_is_not():
    """A push APPENDS commits — the history survives and `revert` undoes it from
    inside the system. Only the history-rewriting variant is irreversible."""
    assert _impact("push_files", "Push multiple files to a repository in a single commit") == 4
    assert _impact("force_push", "Force-push a branch, rewriting its history") == 5
    assert _impact("git_push_force", "Push with --force to overwrite the remote branch") == 5
    # the rest of the publish family is unaffected
    assert _impact("merge_pr", "Merge a pull request") == 5
    assert _impact("deploy_app", "Deploy the application to production") == 5


def test_analyze_matches_both_spellings():
    """The pattern was `analyz?se` — it matched "analyse" and "analyzse" but never
    "analyze", so every analysis tool fell through to the no-evidence default."""
    for name in ("analyze_trend", "analyse_trend", "sentiment_analysis"):
        v = static_impact.classify(ToolSpec(name, "Analyze the data and report."))
        assert v.tool_impact == 3
        assert v.confidence > 0.5, f"{name} still has no verb evidence"


def test_verbs_from_the_reference_servers():
    """Vocabulary the finance and live corpora never exercised."""
    # firing off a run IS execution
    assert _impact("actions_run_trigger", "Triggers a GitHub Actions workflow run.") == 5
    # bringing a thing into existence
    assert _impact("git_init", "Initialises a new git repository in the given path.") == 4
    assert _impact("install_skill", "Install a skill into a directory provider.") == 4
    assert _impact("train_ml_predictor", "Train an ML predictor model for trading signals.") == 4
    # browser automation acts on a live page; navigating only reads
    assert _impact("puppeteer_click", "Clicks an element identified by a CSS selector.") == 4
    assert _impact("puppeteer_fill", "Fills a form input with a value.") == 4
    assert _impact("puppeteer_navigate", "Navigates the browser to a URL.") == 3
    # arithmetic on no asset at all
    assert _impact("convert_time", "Converts a time from one IANA timezone to another.") == 1


def test_trigger_is_name_scoped():
    """ "triggers a notification" in prose must not make a read an execution."""
    assert _impact("get_alerts", "Returns alerts. Saving one triggers a notification.") == 3


def test_money_and_send_verbs_need_their_object():
    """Three tier-5 words that are nouns far more often than verbs in real
    catalogs: "walk-forward analysis", "add a trade to the journal", "share float"."""
    assert _impact("walk_forward_analysis", "Perform walk-forward analysis of a strategy.") == 3
    assert _impact("forward_message", "Forward a message to another channel") == 5
    assert _impact("journal_add_trade", "Add an open trade to the journal.") == 4
    assert _impact("journal_trade_review", "Return full details for a trade entry by ID.") == 3
    assert _impact("execute_trade", "Execute a trade on the brokerage account") == 5
    assert _impact("equity_share_statistics", "Get data about share float for a company.") == 3
    assert _impact("share_document", "Share a document with a collaborator") == 4
