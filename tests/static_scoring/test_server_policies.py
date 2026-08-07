"""Tests for the policy-grade description document (server-policies.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_security.scanner.scan import build_registry
from mcp_security.static_scoring.server_profiles import (
    ProfileAssetTableError,
    ProfileNotFoundError,
    expected_use,
    load_profiles,
    profile_for,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_DOC = REPO_ROOT / "docs" / "mcp-tools" / "server-policies.md"
DEMO = REPO_ROOT / "demo"

POLICY_SERVERS = (
    "fs:fintech_fs",
    "fs:medical_clinic_fs",
    "fs:corp_filesystem",
    "fs:law_firm_fs",
    "fs:media_studio_fs",
    "github:real",
    "github:cbg",
    "slack:real",
    "slack:cbg",
    "calendar:real",
    "calendar:cbg",
    # SQL: added when the filesystem/sql/finance corpus was scanned.
    "sqlite:cbg_sqlite",
    # Finance servers: third-party catalogs scanned live, added with the v5 arm.
    "maverick-mcp",
    "finance-tools-mcp",
    "openbb-platform",
    "sec-edgar-mcp",
    "yfinance",
    # Live-provisioned organizations: one org per real vendor catalog, three
    # domains, with registers whose asset ids exist for real.
    "github:helios",
    "slack:vireo",
    "calendar:aurora",
)


def test_policy_doc_defines_every_registered_server():
    profiles = load_profiles(POLICY_DOC)
    assert {p.server for p in profiles.values()} == set(POLICY_SERVERS)


@pytest.mark.parametrize("server", POLICY_SERVERS)
def test_policy_sections_are_policy_shaped(server: str):
    profile = profile_for(server, doc=POLICY_DOC)
    # Policy-grade disclosure: expected use is stated, but the per-asset
    # sensitivity inventory is deliberately absent — real orgs withhold it.
    assert expected_use(profile.text), f"{server}: no Expected use paragraph"
    with pytest.raises(ProfileAssetTableError):
        _ = profile.asset_sensitivity
    # The section must carry actual policy prose, not just the fact line.
    assert profile.word_count > 40


def test_policy_and_profile_docs_are_distinct_texts():
    policy = profile_for("fs:fintech_fs", doc=POLICY_DOC)
    inventory = profile_for("fs:fintech_fs")
    assert policy.text != inventory.text
    # The inventory-grade profile keeps its table; the policy variant never has one.
    assert inventory.asset_sensitivity  # parses fine on the default document


def test_policy_doc_missing_server_raises():
    # The sqlite servers have no policy section (yet) — lookups must fail loudly.
    with pytest.raises(ProfileNotFoundError):
        profile_for("sqlite:devops_sqlite", doc=POLICY_DOC)


def test_build_registry_attaches_policy_description():
    registry = build_registry(
        "filesystem",
        root=DEMO / "corp_filesystem",
        server="fs:corp_filesystem",
        by_file=True,
        use_profile=True,
        profile_doc=POLICY_DOC,
    )
    assert "Data classification policy" in registry.description
    # And the default document is still what use_profile attaches without the override.
    default = build_registry(
        "filesystem",
        root=DEMO / "corp_filesystem",
        server="fs:corp_filesystem",
        by_file=True,
        use_profile=True,
    )
    assert default.description != registry.description
