"""The HTTP layer read with care, and the routes file read strictly."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from mcp_security.gateway.config import Identity, identity_of, load_config
from mcp_security.gateway.http_wire import client_behind, decode_header_value, parse_networks

PROXIES = parse_networks(["127.0.0.1/32", "10.0.0.0/8"])


@pytest.mark.parametrize(
    ("peer", "forwarded", "client"),
    [
        ("127.0.0.1", "203.0.113.9, 10.0.0.1", "203.0.113.9"),  # through two trusted proxies
        ("127.0.0.1", "198.51.100.1, 203.0.113.9", "203.0.113.9"),  # left of it: client's claim
        ("198.51.100.7", "203.0.113.9", "198.51.100.7"),  # peer is no proxy: header ignored
        ("127.0.0.1", "garbage, 10.0.0.1", "10.0.0.1"),  # an unreadable hop stops the walk
        ("127.0.0.1", None, "127.0.0.1"),
    ],
)
def test_the_client_is_the_nearest_hop_no_trusted_proxy_vouches_for(
    peer: str, forwarded: str | None, client: str
) -> None:
    assert client_behind(peer, forwarded, PROXIES) == client


def test_a_trusted_proxy_entry_that_is_not_an_address_fails_loudly() -> None:
    with pytest.raises(ValueError):
        parse_networks(["not-an-ip"])


def test_mcp_name_base64_sentinel_is_decoded_and_a_fake_one_kept() -> None:
    encoded = "=?base64?" + base64.b64encode("ציון".encode()).decode() + "?="
    assert decode_header_value(encoded) == "ציון"
    assert decode_header_value("=?base64?***?=") == "=?base64?***?="
    assert decode_header_value("get_weather") == "get_weather"


def test_an_agents_entry_can_name_the_user_and_app_or_just_the_agent() -> None:
    assert identity_of("alice") == Identity("alice")
    assert identity_of({"agent": "ci", "user": "u-1", "app": "ci-bot"}) == Identity(
        "ci", "u-1", "ci-bot"
    )
    with pytest.raises(ValueError, match="needs an 'agent'"):
        identity_of({"user": "u-1"})
    with pytest.raises(ValueError, match="unknown keys"):
        identity_of({"agent": "ci", "email": "x@y"})


def test_the_routes_file_reads_the_new_logging_settings(tmp_path: Path) -> None:
    routes = {
        "trusted_proxies": ["127.0.0.1"],
        "hash_key_env": "MY_LOG_KEY",
        "agents": {"ab": {"agent": "ci", "user": "u-1"}},
        "upstreams": {"gh": {"url": "https://x", "log_bodies": "requests", "importance": "i.json"}},
    }
    path = tmp_path / "routes.json"
    path.write_text(json.dumps(routes))

    config = load_config(path)

    assert config.trusted_proxies == ("127.0.0.1",)
    assert config.hash_key_env == "MY_LOG_KEY"
    assert (config.upstreams["gh"].log_bodies, config.upstreams["gh"].importance) == (
        "requests",
        "i.json",
    )


def test_a_route_with_an_unknown_body_policy_fails_loudly(tmp_path: Path) -> None:
    path = tmp_path / "routes.json"
    path.write_text(json.dumps({"upstreams": {"gh": {"url": "https://x", "log_bodies": "some"}}}))
    with pytest.raises(ValueError, match="log_bodies"):
        load_config(path)
