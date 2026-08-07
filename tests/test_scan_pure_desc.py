"""Tests for the tools+description-only registry builder (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_security.static_scoring.registry import ToolSpec
from mcp_security.static_scoring.server_profiles import profile_for
from scripts.scan_pure_desc import build_pure_registry


def test_registry_comes_only_from_catalog_and_profile():
    profile = profile_for("calendar:real")
    tools = [ToolSpec("delete-event", "Delete a calendar event.")]
    registry = build_pure_registry(profile, tools, "calendar")
    # Assets are exactly the profile table rows — no store, no generation.
    assert len(registry.assets) == 16
    by_id = {a.asset_id: a for a in registry.assets}
    # Contents + Why become the description the LLM sees for the asset.
    assert "event = one entry" in by_id["personal"].description
    assert "deletion is the sharp edge" in by_id["personal"].description
    # Spec flags become tags.
    assert "flag:hub" in by_id["connected-account-config"].tags
    assert "flag:self-sufficient" in by_id["connected-account-config"].tags
    assert "flag:metadata-only" in by_id["free-busy-availability"].tags
    assert by_id["personal"].tags == ()
    # The description carried into every prompt is the full profile text.
    assert registry.description == profile.text
    # Baseline app purpose comes from the Expected use paragraph.
    assert "Scheduling assistance" in registry.apps["expected-use"]


def test_scheme_transforms_preserve_sensitivity_and_toggle_flags():
    from mcp_security.static_scoring.server_profiles import (
        parse_asset_rows,
        profile_for,
        strip_profile_flags,
        terse_profile,
    )

    full = profile_for("calendar:real").text
    rows_full = {r.asset_id: r for r in parse_asset_rows(full)}
    # hub/self-sufficient present on the auth config in the full profile.
    assert "hub" in rows_full["connected-account-config"].flags

    noflags = strip_profile_flags(full)
    rows_nf = {r.asset_id: r for r in parse_asset_rows(noflags)}
    assert rows_nf["connected-account-config"].flags == ()  # flags gone
    assert rows_nf["connected-account-config"].sensitivity == 5  # sensitivity kept

    terse = terse_profile(full)
    rows_t = {r.asset_id: r for r in parse_asset_rows(terse)}
    assert set(rows_t) == set(rows_full)  # every asset survives
    assert rows_t["connected-account-config"].sensitivity == 5
    assert "hub" in rows_t["connected-account-config"].flags  # terse KEEPS flags
    assert "**Company.**" not in terse  # prose dropped
