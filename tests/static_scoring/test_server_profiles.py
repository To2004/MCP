"""Tests for the organizational-profile reader.

The profiles are the *input* to a desc-mode scan, so a silent parse failure would
produce a scan that looks normal but was scored without its description. These
tests pin the parse and the two failure modes that must be loud.
"""

from __future__ import annotations

import pytest

from mcp_security.static_scoring.server_profiles import (
    PROFILE_DOC,
    ProfileNotFoundError,
    load_profiles,
    profile_for,
)

# The 13 servers the LLM scanner can reach, plus the 5 deterministic finance scans.
_EXPECTED_SERVERS = {
    "fs:fintech_fs",
    "fs:medical_clinic_fs",
    "fs:corp_filesystem",
    "fs:law_firm_fs",
    "fs:media_studio_fs",
    "github:real",
    "github:cbg",
    "slack:real",
    "slack:cbg",
    "sqlite:devops_sqlite",
    "sqlite:cbg_sqlite",
    "calendar:real",
    "calendar:cbg",
    "maverick-mcp",
    "finance-tools-mcp",
    "openbb-platform",
    "sec-edgar-mcp",
    "yfinance",
}


def test_every_scanned_server_has_a_profile():
    profiles = load_profiles()
    assert {p.server for p in profiles.values()} == _EXPECTED_SERVERS


def test_profiles_carry_a_length_tier_and_real_text():
    for profile in load_profiles().values():
        assert profile.tier in {"XS", "S", "M", "L", "XL"}, profile.name
        # The length experiment only means something if the tiers differ in size.
        assert profile.word_count >= 30, profile.name
        # Every profile must state a CIA ordering — that is the judgement the
        # desc-mode scan reads in place of a scored sensitivity primitive.
        assert any(order in profile.text for order in ("> A", "> C", "> I", "≈")), profile.name


def test_tiers_are_ordered_by_length_within_kind():
    """Within each server kind, a higher tier means strictly more prose.

    The doc's stated design is that tiers are spread *within* each kind so
    length is comparable against a near-identical tool surface. The comparison
    uses ``word_count``, which counts PROSE only: the per-asset ``| Asset |
    Sens. |`` tables added for the profile-sensitivity (ult) mode are a
    structured scoring input, not part of the length dose — and once M-tier
    sections carry mandatory tables, a *global* strict ordering across kinds is
    no longer attainable (prose lengths interleave across kinds by a few words).
    """
    order = ["XS", "S", "M", "L", "XL"]
    by_kind: dict[str, list[tuple[int, int]]] = {}
    for profile in load_profiles().values():
        kind = profile.server.split(":")[0] if ":" in profile.server else profile.server
        by_kind.setdefault(kind, []).append((order.index(profile.tier), profile.word_count))
    for kind, entries in by_kind.items():
        ranked = sorted(entries)
        for (t1, w1), (t2, w2) in zip(ranked, ranked[1:], strict=False):
            assert t1 != t2, (kind, "two profiles share a tier — no dose contrast")
            assert w1 < w2, (kind, order[t1], w1, order[t2], w2)


def test_lookup_by_server_id_alias_and_section_name():
    by_id = profile_for("fs:corp_filesystem")
    by_alias = profile_for("fs:corp")  # short name used by some scan drivers
    by_name = profile_for("fs_corp_filesystem")
    assert by_id == by_alias == by_name


def test_unknown_server_raises_rather_than_returning_empty():
    with pytest.raises(ProfileNotFoundError):
        profile_for("fs:does_not_exist")


def test_missing_document_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profiles(tmp_path / "nope.md")


def test_document_is_where_the_loader_expects():
    assert PROFILE_DOC.exists()


# --- per-asset sensitivity tables (profile-sens / ult mode) -------------------
from mcp_security.static_scoring.server_profiles import (  # noqa: E402
    ProfileAssetTableError,
    missing_asset_rows,
    parse_asset_table,
)

_TOY_TABLE = """Some prose first.

| Asset | Sens. | C | I | A | Why |
|---|---|---|---|---|---|
| `/` | 5 | H | H | M | Root scope. |
| `sensitive/security/` | 5 | H | H | L | Security scope. |
| `README.md` | 1 | L | L | L | Public. |
| plain-id | 3 | M | M | L | No backticks. |

Trailing prose."""


def test_parse_asset_table_keeps_ids_verbatim():
    table = parse_asset_table(_TOY_TABLE)
    assert table == {"/": 5, "sensitive/security/": 5, "README.md": 1, "plain-id": 3}


def test_parse_asset_table_failures_are_loud():
    with pytest.raises(ProfileAssetTableError):
        parse_asset_table("no table here at all")
    with pytest.raises(ProfileAssetTableError):
        parse_asset_table("| Asset | Sens. |\n|---|---|\n| `a` | high |")  # non-integer
    with pytest.raises(ProfileAssetTableError):
        parse_asset_table("| Asset | Sens. |\n|---|---|\n| `a` | 7 |")  # out of range
    with pytest.raises(ProfileAssetTableError):
        parse_asset_table("| Asset | Sens. |\n|---|---|\n| `a` | 2 |\n| `a` | 3 |")  # dup


def test_missing_asset_rows_sorted():
    assert missing_asset_rows({"a": 1}, ["c", "a", "b"]) == ["b", "c"]


def test_real_doc_tables_cover_ult_servers():
    # The four ult-mode servers must carry a parsable per-asset table.
    for server in ("calendar:real", "slack:real", "github:real", "fs:corp_filesystem"):
        table = profile_for(server).asset_sensitivity
        assert len(table) >= 15, server
        assert all(1 <= v <= 5 for v in table.values()), server
    # Tricky ids round-trip exactly.
    fs = profile_for("fs:corp_filesystem").asset_sensitivity
    assert fs["/"] == 5 and fs["sensitive/security/"] == 5 and fs["README.md"] == 1
    slack = profile_for("slack:real").asset_sensitivity
    assert slack["usergroup-membership"] == slack["user-group-membership"]
