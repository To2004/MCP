"""Tests for the demo registry loaders and the combined runner."""

from __future__ import annotations

from mcp_security.static_scoring import DEMO_SERVERS, build_static_table
from mcp_security.static_scoring.registry import (
    load_filesystem_registry,
    load_slack_registry,
)


def test_all_demo_servers_load_and_score_offline():
    # Every registered demo must build a registry and score without a model.
    for name, loader in DEMO_SERVERS.items():
        registry = loader()
        assert registry.tools, f"{name} has no tools"
        assert registry.assets, f"{name} has no assets"
        table = build_static_table(registry, use_llm=False, version="t")
        assert table["cells"], f"{name} produced no cells"


def test_filesystem_demos_share_tool_registry():
    corp = load_filesystem_registry()
    law = DEMO_SERVERS["law_firm_fs"]()
    # Same server kind/tools, different asset corpus.
    assert {t.name for t in corp.tools} == {t.name for t in law.tools}
    assert {a.asset_id for a in corp.assets} != {a.asset_id for a in law.assets}


def test_sqlite_demo_reads_live_schema():
    corp_sql = DEMO_SERVERS["corp_sqlite"]()
    ids = {a.asset_id for a in corp_sql.assets}
    assert {"customers", "orders", "api_keys"} <= ids


def test_slack_is_a_distinct_kind_with_no_destructive_tools():
    slack = load_slack_registry()
    assert slack.kind == "slack"
    table = build_static_table(slack, use_llm=False, version="t")
    # Slack has no delete/clobber tool, so nothing reaches impact tier 3.
    assert max(table["tool_impact"].values()) <= 2
    # Posting is state-changing, not read-only.
    assert table["tool_impact"]["slack_post_message"] == 2


def test_private_channels_outrank_public_ones():
    slack = load_slack_registry()
    table = build_static_table(slack, use_llm=False, version="t")
    assert table["asset_sensitivity"]["hr-internal"] > table["asset_sensitivity"]["random"]


# --- take2: per-file full-path filesystem assets ---------------------------
def test_take2_assets_are_full_paths_not_extensions():
    from mcp_security.static_scoring.registry import DEMO_SERVERS_TAKE2

    reg = DEMO_SERVERS_TAKE2["medical_clinic_fs"]()
    ids = {a.asset_id for a in reg.assets}
    # take2 ids are paths, not ".txt"/".png" buckets.
    assert any("patients/" in i and i.endswith(".txt") for i in ids)
    assert ".txt" not in ids


def test_take2_surfaces_phi_that_take1_hides():
    from mcp_security.static_scoring.registry import DEMO_SERVERS, DEMO_SERVERS_TAKE2

    t1 = build_static_table(DEMO_SERVERS["medical_clinic_fs"](), use_llm=False, version="t1")
    t2 = build_static_table(DEMO_SERVERS_TAKE2["medical_clinic_fs"](), use_llm=False, version="t2")

    def n_critical(table: dict) -> int:
        return sum(b == "critical" for row in table["bands"].values() for b in row.values())

    # take1 buckets everything into .txt/.png and finds no critical PHI; take2 does.
    assert n_critical(t1) == 0
    assert n_critical(t2) > 0
    # A specific patient record is now its own, highly sensitive asset.
    sens = t2["asset_sensitivity"]
    assert sens["patients/alice_johnson/medical_history.txt"] >= 4


# --- mutable-state assets: everything the write tools can change ------------
def test_declarative_registries_include_mutable_state_assets():
    from mcp_security.static_scoring.registry import (
        load_calendar_registry,
        load_github_registry,
    )

    expected = {
        load_slack_registry: {"channel-messages", "message-reactions", "read-markers"},
        load_calendar_registry: {"event-records", "event-attendee-lists", "rsvp-state"},
        load_github_registry: {"branch-heads", "pull-requests-and-reviews", "org-external-copies"},
    }
    for loader, ids in expected.items():
        registry = loader()
        asset_ids = {a.asset_id for a in registry.assets}
        assert ids <= asset_ids, f"{registry.server} missing mutable-state assets"
        # Mutable-state assets are tagged so consumers can tell them from scopes.
        tagged = {a.asset_id for a in registry.assets if "kind:mutable-state" in a.tags}
        assert ids <= tagged


def test_mutable_state_assets_score_offline():
    # The offline baseline must score the new asset classes without crashing and
    # produce a full (tool x asset) matrix over them.
    slack = load_slack_registry()
    table = build_static_table(slack, use_llm=False, version="t")
    assert "channel-messages" in table["asset_sensitivity"]
    # Cells are keyed asset -> {tool: score}; the new asset gets a full tool row.
    assert set(table["cells"]["channel-messages"]) == set(table["tool_impact"])


# Every tool must have at least one asset it affects (reads or mutates). This
# mapping is the audit record: adding a tool without extending it fails here.
_TOOL_AFFECTS = {
    "slack": {
        "slack_list_channels": "channel-directory",
        "slack_get_channel_history": "channel-messages",
        "slack_get_thread_replies": "channel-messages",
        "slack_get_users": "user-directory",
        "slack_get_user_profile": "user-directory",
        "slack_post_message": "channel-messages",
        "slack_reply_to_thread": "channel-messages",
        "slack_add_reaction": "message-reactions",
    },
    "calendar": {
        "list_calendars": "calendar-directory",
        "list_events": "event-records",
        "list_week": "event-records",
        "get_event": "event-records",
        "find_free_slot": "free-busy-availability",
        "access_contacts": "contacts",
        "create_event": "event-records",
        "update_event": "event-attendee-lists",
        "send_email_invite": "outbound-invite-email",
        "delete_event": "event-records",
        "delete_all_events": "event-records",
    },
    "github": {
        "search_repositories": "repository-catalog",
        "get_file_contents": "branch-heads",
        "list_commits": "branch-heads",
        "get_issue": "issues-and-comments",
        "create_issue": "issues-and-comments",
        "create_or_update_file": "branch-heads",
        "push_files": "branch-heads",
        "delete_file": "branch-heads",
        "create_pull_request": "pull-requests-and-reviews",
        "merge_pull_request": "pull-requests-and-reviews",
        "fork_repository": "org-external-copies",
    },
}


def test_every_declarative_tool_has_an_affected_asset():
    from mcp_security.static_scoring.registry import (
        load_calendar_registry,
        load_github_registry,
    )

    loaders = {
        "slack": load_slack_registry,
        "calendar": load_calendar_registry,
        "github": load_github_registry,
    }
    for kind, loader in loaders.items():
        registry = loader()
        mapping = _TOOL_AFFECTS[kind]
        asset_ids = {a.asset_id for a in registry.assets}
        for tool in registry.tools:
            assert tool.name in mapping, f"{kind}: tool {tool.name} has no affected-asset entry"
            affected = mapping[tool.name]
            assert affected in asset_ids, f"{kind}: {tool.name} -> {affected} not in assets"
