"""B10 (I7): the per-platform egress table in gateway/egress/: entries marked verified or
UNVERIFIED, strict ranges that never overlap, and no invented range."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_security.behaviour import BehaviourConfig
from mcp_security.gateway.egress.table import (
    DEFAULT_EGRESS_TABLE,
    EGRESS_UNVERIFIED,
    EGRESS_VERIFIED,
    EgressPlatform,
    EgressTable,
    is_platform_network,
    load_egress_table,
    platform_network,
)

REPO = Path(__file__).resolve().parents[2]
SHIPPED_TABLE = REPO / "src" / "mcp_security" / "gateway" / "egress" / "platform_egress.json"
ANTHROPIC_OUTBOUND = "160.79.104.0/21"
VERIFIED = {
    "label": "platform-a",
    "status": EGRESS_VERIFIED,
    "cidrs": ["192.0.2.0/24"],
    "source": "https://example.org/egress",
    "checked": "2026-10-26",
}


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


def _table(*platforms: dict, use_unverified: bool = False) -> dict:
    return {"version": 1, "use_unverified": use_unverified, "platforms": list(platforms)}


def test_the_shipped_table_lists_only_the_checked_range() -> None:
    table = load_egress_table(SHIPPED_TABLE)
    assert table.shared_networks() == (("anthropic", ANTHROPIC_OUTBOUND),)
    anthropic = next(p for p in table.platforms if p.label == "anthropic")
    assert anthropic.status == EGRESS_VERIFIED and anthropic.source.startswith("https://")
    placeholders = [p for p in table.platforms if p.status == EGRESS_UNVERIFIED]
    assert placeholders and all(p.cidrs == () for p in placeholders)  # no invented ranges
    assert set(table.unverified) == {p.label for p in placeholders}
    BehaviourConfig(shared_networks=table.shared_networks())  # the engine accepts the pairs
    assert DEFAULT_EGRESS_TABLE.resolve() == SHIPPED_TABLE.resolve()
    assert load_egress_table() == table


def test_unverified_ranges_count_only_when_the_table_opts_in(tmp_path: Path) -> None:
    unchecked = {"label": "platform-b", "status": EGRESS_UNVERIFIED, "cidrs": ["198.51.100.0/24"]}
    off = load_egress_table(_write(tmp_path, "off.json", _table(VERIFIED, unchecked)))
    on = load_egress_table(
        _write(tmp_path, "on.json", _table(VERIFIED, unchecked, use_unverified=True))
    )
    assert off.shared_networks() == (("platform-a", "192.0.2.0/24"),)
    assert on.shared_networks() == (
        ("platform-a", "192.0.2.0/24"),
        ("platform-b", "198.51.100.0/24"),
    )
    assert off.unverified == on.unverified == ("platform-b",)


@pytest.mark.parametrize(
    "change",
    [
        {"cidrs": []},  # verified without a range
        {"source": None},  # verified without a source
        {"source": "ftp://example.org"},
        {"checked": "yesterday"},
        {"checked": None},
        {"cidrs": ["192.0.2.1/24"]},  # host bits set: a typo
        {"cidrs": ["not-a-cidr"]},
        {"cidrs": [3232235520]},
        {"status": "probably"},
        {"label": "Has Spaces"},
        {"label": ""},
    ],
)
def test_a_bad_egress_entry_is_refused(tmp_path: Path, change: dict) -> None:
    with pytest.raises(ValueError):
        load_egress_table(_write(tmp_path, "t.json", _table({**VERIFIED, **change})))


@pytest.mark.parametrize(
    "data",
    [
        {"version": 2, "platforms": []},
        {"version": 1, "platforms": {"a": 1}},
        {"version": 1, "platforms": [{**VERIFIED, "colour": "blue"}]},
        {"version": 1, "platforms": [{**VERIFIED, "cidrs": "192.0.2.0/24"}]},
        {"version": 1, "platforms": [VERIFIED, VERIFIED]},  # a label twice
        {"version": 1, "platforms": [], "use_unverified": "yes"},
        {"version": 1, "platforms": [], "use_unverifed": True},  # a typo is not ignored
    ],
)
def test_a_bad_egress_table_is_refused(tmp_path: Path, data: dict) -> None:
    with pytest.raises(ValueError):
        load_egress_table(_write(tmp_path, "t.json", data))


def test_ranges_in_use_may_not_overlap_across_platforms() -> None:
    inner = EgressPlatform(**{**VERIFIED, "label": "platform-b", "cidrs": ("192.0.2.128/25",)})
    outer = EgressPlatform(**{**VERIFIED, "cidrs": ("192.0.2.0/24",)})
    with pytest.raises(ValueError, match="overlap"):
        EgressTable((outer, inner))
    v6 = EgressPlatform(**{**VERIFIED, "label": "platform-c", "cidrs": ("2001:db8::/32",)})
    assert len(EgressTable((outer, v6)).shared_networks()) == 2
    parked = EgressPlatform("platform-d", EGRESS_UNVERIFIED, ("192.0.2.0/26",))
    EgressTable((outer, parked))  # not in use: no conflict
    with pytest.raises(ValueError, match="overlap"):
        EgressTable((outer, parked), use_unverified=True)


def test_platform_networks_are_named_with_their_prefix() -> None:
    assert platform_network("anthropic") == "platform:anthropic"
    assert is_platform_network("platform:anthropic")
    assert not is_platform_network("160.79.0.0/16")
    assert not is_platform_network(None)
    assert EgressPlatform(**{**VERIFIED, "cidrs": ("192.0.2.0/24",)}).network == (
        "platform:platform-a"
    )
