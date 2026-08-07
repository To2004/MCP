"""Tests for runtime asset binding.

The fixtures deliberately describe an invented server kind — a "vault" holding
"drawers" — so a test passing here proves the discovery generalizes rather than
recognizing the three servers the corpus happens to contain.
"""

from __future__ import annotations

import json

import pytest

from mcp_security.binding import AssetResolver, Level, discover
from mcp_security.binding.catalog import ToolSpec
from mcp_security.binding.identifiers import (
    canonical_id,
    identifier_candidates,
    describes_call_target,
    describes_egress,
    normalize_key,
    token_similarity,
)
from mcp_security.static_scoring.server_policies import PolicyAssetRow


def row(asset_id: str, description: str, *tools: str) -> PolicyAssetRow:
    return PolicyAssetRow(
        asset_id=asset_id, description=description, tools=tuple(tools), flags=(), cia=""
    )


VAULT_REGISTER = [
    row("finance-drawer", "Ledgers and payment runs", "list-drawers", "read-item", "put-item"),
    row("legal-drawer", "Contracts under negotiation", "list-drawers", "read-item", "put-item"),
    row("archive-drawer", "Retired records kept for audit", "list-drawers", "read-item"),
    row("item-records", "What a put or delete targets", "put-item"),
    row("courier-dispatch", "Parcels leaving the building, unrecallable", "put-item"),
    # Two rows one verb separates by mode, not by container. The view carries
    # the metadata-only flag; the thing it describes does not.
    PolicyAssetRow(
        asset_id="key-directory",
        description="The list of issued keys",
        tools=("manage-keys",),
        flags=("metadata-only",),
        cia="",
    ),
    row("key-config", "Which keys are issued and what they open", "manage-keys"),
]

#: The vendor catalog for the invented server. ``put-item`` declares a recipient
#: parameter, so the absence of an outside address there is informative;
#: ``discard-item`` declares none, so its egress asset can never be ruled out.
VAULT_CATALOG = {
    "read-item": ToolSpec("read-item", "Read one item from a drawer", {
        "properties": {"drawerId": {"type": "string"}, "itemId": {"type": "string"}}}),
    "put-item": ToolSpec("put-item", "Store an item, optionally couriering a copy", {
        "properties": {"drawerId": {"type": "string"}, "body": {"type": "string"},
                       "recipients": {"type": "array", "items": {"type": "string"}}}}),
    "discard-item": ToolSpec("discard-item", "Discard an item", {
        "properties": {"drawerId": {"type": "string"}, "itemId": {"type": "string"}}}),
    "list-drawers": ToolSpec("list-drawers", "List all drawers", {"properties": {}}),
    "manage-keys": ToolSpec(
        "manage-keys",
        "Manage vault keys. Actions: 'list' (show issued keys), "
        "'issue' (authorise a new key), 'revoke' (withdraw a key).",
        {"properties": {"action": {"type": "string", "enum": ["list", "issue", "revoke"]}}},
    ),
}


def call(tool: str, args: dict, output: str = "", asset: str = "") -> dict:
    return {"tool": tool, "args": json.dumps(args), "output": output, "asset": asset}


def vault_calls() -> list[dict]:
    """Traffic against three drawers, addressed by an opaque handle."""
    listing = (
        'ID,Name\n"D-8801","finance-drawer"\n"D-8802","legal-drawer"\n"D-8803","archive-drawer"'
    )
    calls = [call("list-drawers", {}, listing) for _ in range(4)]
    # Outputs carry the organization's own addresses, which is how the org
    # domain is discovered — without them nothing counts as "inside".
    for handle, body in (
        ("D-8801", "payment run ledger reconciliation, filed by clerk@org.example"),
        ("D-8802", "contract negotiation redline, counsel@org.example"),
        ("D-8803", "retired record audit retention, archivist@org.example"),
    ):
        for index in range(12):
            calls.append(call("read-item", {"drawerId": handle, "itemId": f"i{index}"}, body))
        # A container is what the whole surface operates on, so more than one
        # verb takes it — the property discovery relies on to tell a container
        # key from a filter.
        for index in range(4):
            calls.append(
                call("put-item", {"drawerId": handle, "body": f"entry {index}"}, "stored", body)
            )
    return calls


class TestIdentifiers:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("calendarId", "calendarid"), ("channel_id", "channelid"), ("repo", "repo")],
    )
    def test_normalize_key_folds_spelling(self, raw: str, expected: str) -> None:
        assert normalize_key(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("abc123@group.calendar.google.com", "abc123"),
            ("#vireo-safety-pv", "vireo-safety-pv"),
            # Path structure is identity and must survive: two files can share a
            # basename and be different assets.
            ("sensitive/hr/payroll.csv", "sensitive/hr/payroll.csv"),
        ],
    )
    def test_canonical_id_strips_only_decoration(self, raw: str, expected: str) -> None:
        assert canonical_id(raw) == expected

    def test_identifier_candidates_serve_prefixes_and_hierarchies(self) -> None:
        """An owner prefix is dropped from the front; a hierarchy from the back."""
        qualified = identifier_candidates("To2004/helios-scada-gateway")
        assert "helios-scada-gateway" in qualified
        assert qualified[0] == "to2004/helios-scada-gateway"
        nested = identifier_candidates("sensitive/hr/payroll.csv")
        assert nested[0] == "sensitive/hr/payroll.csv"
        assert "sensitive/hr" in nested and "sensitive" in nested

    def test_token_similarity_is_symmetric_and_bounded(self) -> None:
        assert token_similarity("vireo-trial-ops", "vireo-trial-ops") == 1.0
        assert 0.0 < token_similarity("trial-ops", "vireo-trial-ops") < 1.0
        assert token_similarity("holidays", "color-catalog") == 0.0

    def test_call_target_rows_are_recognized(self) -> None:
        assert describes_call_target("What a create/update/delete targets")
        assert not describes_call_target("Officers' calendar: board sessions")

    def test_boundary_nouns_alone_are_not_egress(self) -> None:
        assert describes_egress("Mail leaving the org under its identity")
        assert describes_egress("Repositories created outside the org boundary")
        assert not describes_egress("systems inside the CIP electronic security perimeter")


class TestDiscovery:
    def test_finds_the_container_key_without_being_told(self) -> None:
        found = discover(vault_calls(), VAULT_REGISTER)
        assert found.container_keys == ("drawerid",)
        assert "list-drawers" in found.listing_tools

    def test_binds_every_handle_to_its_register_row(self) -> None:
        found = discover(vault_calls(), VAULT_REGISTER)
        assert {cid: b.asset_id for cid, b in found.bindings.items()} == {
            "d-8801": "finance-drawer",
            "d-8802": "legal-drawer",
            "d-8803": "archive-drawer",
        }

    def test_rejects_a_per_call_identifier(self) -> None:
        found = discover(vault_calls(), VAULT_REGISTER)
        assert "itemid" not in found.container_keys
        assert any(key == "itemid" for key, _ in found.rejected)

    def test_rejects_a_free_text_argument(self) -> None:
        calls = vault_calls() + [
            call("read-item", {"drawerId": "D-8801", "note": f"please fetch record {n}"})
            for n in range(30)
        ]
        found = discover(calls, VAULT_REGISTER)
        assert "note" not in found.container_keys

    def test_never_catalogs_a_call_target_row(self) -> None:
        found = discover(vault_calls(), VAULT_REGISTER)
        assert "item-records" not in found.asset_ids


class TestResolver:
    @pytest.fixture
    def resolver(self) -> AssetResolver:
        found = discover(vault_calls(), VAULT_REGISTER)
        return AssetResolver(
            VAULT_REGISTER,
            found,
            {"read-item": "READ", "put-item": "CREATE", "list-drawers": "LIST",
             "manage-keys": ["WRITE"]},
            VAULT_CATALOG,
        )

    def test_tool_only_returns_every_candidate(self, resolver: AssetResolver) -> None:
        resolved = resolver.resolve("read-item", {"drawerId": "D-8801"}, Level.TOOL_ONLY)
        assert resolved.asset_ids == {"finance-drawer", "legal-drawer", "archive-drawer"}

    def test_catalog_narrows_to_the_named_container(self, resolver: AssetResolver) -> None:
        resolved = resolver.resolve("read-item", {"drawerId": "D-8802"}, Level.CATALOG)
        assert resolved.asset_ids == {"legal-drawer"}
        assert resolved.primary == "legal-drawer"

    def test_an_unnamed_container_is_a_fanout_not_a_guess(self, resolver: AssetResolver) -> None:
        resolved = resolver.resolve("read-item", {}, Level.CATALOG)
        assert resolved.fanout
        assert len(resolved.asset_ids) == 3

    def test_an_unknown_handle_falls_back_to_the_closure(self, resolver: AssetResolver) -> None:
        """An unbindable handle could name any container, so all of them are returned.

        Narrowing further would be a guess, and guessing low is exactly how a
        gate is walked past. The flag distinguishes this from a genuine fan-out.
        """
        resolved = resolver.resolve("read-item", {"drawerId": "D-9999"}, Level.CATALOG)
        assert resolved.unbound_containers == ("d-9999",)
        assert resolved.unresolved_container and not resolved.fanout
        assert resolved.asset_ids == {"finance-drawer", "legal-drawer", "archive-drawer"}

    def test_operation_drops_a_read_from_a_write_target_row(self, resolver: AssetResolver) -> None:
        write = resolver.resolve("put-item", {"drawerId": "D-8801"}, Level.OPERATION)
        assert "item-records" in write.asset_ids

    def test_egress_drops_when_the_tool_could_name_a_recipient_and_did_not(
        self, resolver: AssetResolver
    ) -> None:
        """``put-item`` declares ``recipients``, so naming none is informative."""
        inside = resolver.resolve(
            "put-item", {"drawerId": "D-8801", "recipients": ["clerk@org.example"]}, Level.EGRESS
        )
        assert "courier-dispatch" not in inside.asset_ids

    def test_egress_fires_on_an_address_outside_the_org(self, resolver: AssetResolver) -> None:
        outside = resolver.resolve(
            "put-item",
            {"drawerId": "D-8801", "recipients": ["someone@far-away.example"]},
            Level.EGRESS,
        )
        assert "courier-dispatch" in outside.asset_ids

    def test_egress_is_kept_when_the_tool_cannot_name_a_recipient(self) -> None:
        """A verb with no recipient parameter says nothing, so egress must stay in.

        Discarding an item may still courier a notice; the recipients live in
        stored state, not in the arguments. Ruling the asset out would be
        inventing evidence of safety.
        """
        register = VAULT_REGISTER + [
            row("courier-notice", "Notices leaving the building", "discard-item")
        ]
        found = discover(vault_calls(), register)
        resolver = AssetResolver(register, found, {"discard-item": ["DELETE"]}, VAULT_CATALOG)
        resolved = resolver.resolve("discard-item", {"drawerId": "D-8801"}, Level.EGRESS)
        assert "courier-notice" in resolved.asset_ids

    def test_a_documented_mode_names_the_primary_asset(self, resolver: AssetResolver) -> None:
        """The tool's own description separates two assets no container can.

        ``manage-keys`` documents ``'list' (show issued keys)`` against
        ``'issue' (authorise a new key)``; the register flags the directory
        ``metadata-only`` and the config not, so a reading mode leads with the
        view and a writing mode leads with the thing.
        """
        assert resolver.resolve("manage-keys", {"action": "list"}).primary == "key-directory"
        assert resolver.resolve("manage-keys", {"action": "issue"}).primary == "key-config"

    def test_an_identifier_written_inside_another_argument_still_binds(
        self, resolver: AssetResolver
    ) -> None:
        """A verb with no container parameter can still be scoped by its caller."""
        register = VAULT_REGISTER + [
            row("search-results", "What a search returns", "find-items")
        ]
        for entry in register:
            if entry.asset_id in {"finance-drawer", "legal-drawer"}:
                object.__setattr__(entry, "tools", (*entry.tools, "find-items"))
        found = discover(vault_calls(), VAULT_REGISTER)
        wide = AssetResolver(register, found, {"find-items": ["SEARCH"]}, VAULT_CATALOG)
        resolved = wide.resolve("find-items", {"q": "drawer:D-8802 unpaid"}, Level.CATALOG)
        assert "legal-drawer" in resolved.asset_ids

    def test_a_mode_ranks_but_never_removes(self, resolver: AssetResolver) -> None:
        """Both assets stay in play — listing keys also discloses what they open."""
        resolved = resolver.resolve("manage-keys", {"action": "list"})
        assert resolved.asset_ids == {"key-directory", "key-config"}

    def test_a_tool_reaching_nothing_resolves_to_nothing(self, resolver: AssetResolver) -> None:
        resolved = resolver.resolve("get-clock", {}, Level.EGRESS)
        assert not resolved.asset_ids
        assert resolved.notes
