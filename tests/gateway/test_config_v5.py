"""v5 route config (I7): B1 baseline mode (per agent, D5), DEP-8 routes without sign-in, B9d zone
maps, a route's B10 egress table (the table itself: test_egress_table.py), PS7 gate names, PS9
audit header, PS10 origin settings, and unchanged v4 digests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from ipaddress import ip_address, ip_network
from pathlib import Path

import httpx
import pytest

from mcp_security.behaviour import BehaviourConfig
from mcp_security.behaviour.engine import DESIGNS, V4, V5, network_of
from mcp_security.gateway.config import (
    BASELINE_AGENT,
    BASELINE_USER,
    BASELINE_USER_APP,
    LOG_ORIGIN_NETWORK_PSEUDONYM,
    GatewayConfig,
    OAuthConfig,
    Upstream,
    audit_headers,
    baseline_mode,
    check_origin_key,
    digest_view,
    gate_fields,
    load_config,
    load_zone_map,
    route_egress_table,
    route_shared_networks,
    route_zone_directory,
    with_audit_header,
    without_header,
)
from mcp_security.gateway.egress.table import (
    EGRESS_VERIFIED,
    EgressTable,
    load_egress_table,
    platform_network,
)

REPO = Path(__file__).resolve().parents[2]
EXAMPLE_ROUTES = REPO / "src" / "mcp_security" / "gateway" / "routes.example.json"
SHIPPED_TABLE = REPO / "src" / "mcp_security" / "gateway" / "egress" / "platform_egress.json"
URL = "http://upstream/mcp"
KEY_ENV = "GATEWAY_LOG_KEY"
VERIFIED = {
    "label": "platform-a",
    "status": EGRESS_VERIFIED,
    "cidrs": ["192.0.2.0/24"],
    "source": "https://example.org/egress",
    "checked": "2026-10-26",
}


def _route(**fields: object) -> Upstream:
    return Upstream(name="github", url=URL, **fields)


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


def _table(*platforms: dict, use_unverified: bool = False) -> dict:
    return {"version": 1, "use_unverified": use_unverified, "platforms": list(platforms)}


# ── B1 and DEP-8 (revised 2026-10-27, D5: history per agent) ────────────────────────────


def test_the_baseline_mode_defaults_by_design_and_a_route_can_set_it() -> None:
    assert baseline_mode(_route(), V5) == BASELINE_AGENT
    assert baseline_mode(None, V5) == BASELINE_AGENT
    for design in (d for d in DESIGNS if d != V5):
        assert baseline_mode(_route(), design) == BASELINE_USER_APP
    assert baseline_mode(_route(baseline_key=BASELINE_USER), V5) == BASELINE_USER  # opt-in
    assert baseline_mode(_route(baseline_key=BASELINE_USER), V4) == BASELINE_USER
    assert baseline_mode(_route(baseline_key=BASELINE_USER_APP), V5) == BASELINE_USER_APP


def test_a_v5_route_without_sign_in_needs_no_switch() -> None:
    # DEP-8's refusal of unsigned v5 routes is gone: they run, keyed per reported agent
    assert "allow_anonymous_v5" not in {field.name for field in fields(Upstream)}
    with pytest.raises(TypeError):
        _route(allow_anonymous_v5=True)


def test_an_unknown_baseline_mode_is_refused() -> None:
    with pytest.raises(ValueError, match="baseline_key"):
        _route(baseline_key="person")


@pytest.mark.parametrize(
    "claim",
    ["client_id", "azp", "appid", "cid", "iss", "tid", "sid", "roles", "groups", "scp", "", None],
)
def test_a_user_claim_that_names_no_person_is_refused(claim: object) -> None:
    # appid / cid name the app (Entra v1 / Okta); tid merges a tenant; sid splits by session
    with pytest.raises(ValueError, match="user_claim"):
        OAuthConfig(issuer="i", jwks_uri="j", public_url="p", user_claim=claim)
    with pytest.raises(ValueError, match="zone_claim"):
        OAuthConfig(issuer="i", jwks_uri="j", public_url="p", zone_claim="")


@pytest.mark.parametrize("claim", ["sub", "oid", "upn", "email"])
def test_a_user_claim_that_names_a_person_is_accepted(claim: str) -> None:
    oauth = OAuthConfig(issuer="i", jwks_uri="j", public_url="p", user_claim=claim)
    assert oauth.user_claim == claim


# ── B9d ─────────────────────────────────────────────────────────────────────────────────


def test_a_zone_map_loads_and_names_zones(tmp_path: Path) -> None:
    path = _write(tmp_path, "z.json", {"version": 1, "users": {"p-1": "Asia/Kolkata"}})
    directory = load_zone_map(path)
    assert directory.zone_of("p-1") == "Asia/Kolkata"
    assert directory.zone_of("p-2") is None and directory.zone_of(None) is None
    with pytest.raises(TypeError):
        directory.zones["p-2"] = "UTC"  # read-only
    assert route_zone_directory(_route(zone_map=str(path))).zone_of("p-1") == "Asia/Kolkata"
    assert route_zone_directory(_route()) is None


@pytest.mark.parametrize(
    "data",
    [
        {"version": 2, "users": {}},
        {"users": {}},
        {"version": 1, "users": ["p-1"]},
        {"version": 1, "users": {"p-1": "Mars/Base"}},
        {"version": 1, "users": {"p-1": 5}},
        {"version": 1, "users": {"": "UTC"}},
        ["not", "a", "map"],
    ],
)
def test_a_bad_zone_map_is_refused(tmp_path: Path, data: object) -> None:
    with pytest.raises(ValueError):
        load_zone_map(_write(tmp_path, "z.json", data))


# ── B10 ─────────────────────────────────────────────────────────────────────────────────


def test_a_route_without_a_table_shares_no_network() -> None:
    assert route_shared_networks(_route()) == ()
    assert route_shared_networks(None) == ()
    assert route_egress_table(_route()) is None and route_egress_table(None) is None
    pairs = route_shared_networks(_route(shared_egress=str(SHIPPED_TABLE)))
    assert any(ip_address("160.79.105.7") in ip_network(cidr) for _, cidr in pairs)


def test_a_routes_egress_table_carries_the_digest_of_the_file_it_read(tmp_path: Path) -> None:
    # B10: a raw-origin route's offline re-score recomputes networks from this file
    path = _write(tmp_path, "t.json", _table(VERIFIED))
    table = route_egress_table(_route(shared_egress=str(path)))
    assert table.digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert table.shared_networks() == route_shared_networks(_route(shared_egress=str(path)))
    spaced = tmp_path / "spaced.json"
    spaced.write_text(json.dumps(_table(VERIFIED), indent=2))
    same_ranges = load_egress_table(spaced)
    assert same_ranges == table and same_ranges.digest != table.digest  # bytes, not meaning
    widened = {**VERIFIED, "cidrs": ["192.0.2.0/23"]}
    assert load_egress_table(_write(tmp_path, "w.json", _table(widened))).digest != table.digest
    assert EgressTable().digest is None  # built in code: no file


def test_the_engine_and_the_gateway_spell_a_platform_network_alike() -> None:
    # B10 drift guard: once the engine maps a shared range (J1), it uses the gateway's value
    pairs = load_egress_table(SHIPPED_TABLE).shared_networks()
    plain = network_of("160.79.105.7", BehaviourConfig(design=V5))
    mapped = network_of("160.79.105.7", BehaviourConfig(design=V5, shared_networks=pairs))
    assert mapped in (plain, platform_network("anthropic"))


def test_the_example_routes_file_loads_with_its_egress_table() -> None:
    config = load_config(EXAMPLE_ROUTES, environ={})
    github = config.upstreams["github"]
    assert (REPO / github.shared_egress).resolve() == SHIPPED_TABLE.resolve()
    assert load_egress_table(REPO / github.shared_egress).shared_networks()


# ── PS7, PS9, PS10 ──────────────────────────────────────────────────────────────────────


def test_the_legacy_gate_fields_carry_their_pre_v5_names() -> None:
    assert gate_fields(12.5, 1.25) == {
        "gate_risk": 12.5,
        "gate_factor": 1.25,
        "risk": 12.5,
        "factor": 1.25,
    }
    assert _route().legacy_gate is True and _route(legacy_gate=False).legacy_gate is False


def test_the_audit_header_carries_the_exchange_id_only_when_set() -> None:
    assert audit_headers(_route(), "ex-1") == {}
    assert audit_headers(_route(upstream_audit_header="X-Gateway-Exchange"), "ex-1") == {
        "X-Gateway-Exchange": "ex-1"
    }


def test_the_callers_own_audit_header_never_reaches_the_upstream() -> None:
    # PS9: an agent that sends the header itself must not name the exchange the upstream joins
    route = _route(upstream_audit_header="X-Gateway-Exchange")
    sent = {"x-gateway-exchange": "forged", "X-GATEWAY-EXCHANGE": "forged-2", "accept": "*/*"}
    headers = with_audit_header(sent, route, "ex-1")
    assert headers == {"accept": "*/*", "X-Gateway-Exchange": "ex-1"}
    assert httpx.Headers(headers).get_list("x-gateway-exchange") == ["ex-1"]  # on the wire
    assert sent["x-gateway-exchange"] == "forged"  # the caller's headers are not changed
    assert with_audit_header(sent, _route(), "ex-1") == sent  # no audit header: as sent
    # the same rule for any field the gateway sets itself, such as a route's key header
    assert without_header({"x-api-key": "forged", "accept": "*/*"}, "X-Api-Key") == {
        "accept": "*/*"
    }


@pytest.mark.parametrize(
    "header",
    [
        "Authorization",
        "cookie",
        "Mcp-Session-Id",
        "X-Api-Key",  # the route's key header
        "Content-Encoding",
        "Content-Type",
        "Accept",
        "Accept-Language",
        "TE",
        "Upgrade",
        "Keep-Alive",
        "Trailer",
        "Proxy-Connection",
        "Last-Event-ID",
        "X-Forwarded-For",
        "Forwarded",
        "X-Real-IP",
        "Via",
        "Host",
        "Origin",
        "User-Agent",
        "If-Match",
        "Expect",
        "Range",
        "Sec-Fetch-Mode",
        "bad header",
        "",
    ],
)
def test_a_reserved_or_malformed_audit_header_is_refused(header: str) -> None:
    with pytest.raises(ValueError, match="upstream_audit_header"):
        _route(key_header="X-Api-Key", upstream_audit_header=header)


@pytest.mark.parametrize("header", ["X-Gateway-Exchange", "X-Request-Id", "Gateway-Exchange"])
def test_a_free_audit_header_is_accepted(header: str) -> None:
    assert _route(upstream_audit_header=header).upstream_audit_header == header


@pytest.mark.parametrize(
    "fields",
    [
        {"legacy_gate": 0},
        {"pseudonymize_origin": "yes"},
        {"fail_closed_unparsed": None},
        {"zone_map": ""},
        {"shared_egress": 3},
        {"route_zone": 5},  # not a TypeError from the zone database
        {"route_zone": ["UTC"]},
        {"log_origin": LOG_ORIGIN_NETWORK_PSEUDONYM},  # the engine would not see the pseudonym
    ],
)
def test_a_bad_v5_route_field_is_refused(fields: dict) -> None:
    with pytest.raises(ValueError):
        _route(**fields)


def test_a_pseudonymised_log_origin_needs_pseudonymised_origins() -> None:
    route = _route(pseudonymize_origin=True, log_origin=LOG_ORIGIN_NETWORK_PSEUDONYM)
    assert route.log_origin == LOG_ORIGIN_NETWORK_PSEUDONYM


def test_pseudonymised_origins_refuse_to_start_without_a_key(tmp_path: Path) -> None:
    routes = _write(
        tmp_path,
        "routes.json",
        {"upstreams": {"github": {"url": URL, "pseudonymize_origin": True}}},
    )
    with pytest.raises(ValueError, match=KEY_ENV):
        load_config(routes, environ={})
    with pytest.raises(ValueError, match=KEY_ENV):
        load_config(routes, environ={KEY_ENV: ""})
    assert load_config(routes, environ={KEY_ENV: "k"}).upstreams["github"].pseudonymize_origin
    plain = GatewayConfig(upstreams={"github": _route()})
    check_origin_key(plain, environ={})  # nothing to key: no error
    # a reader that never pseudonymises (catalog.py) may skip the check
    unchecked = load_config(routes, environ={}, check_keys=False)
    assert unchecked.upstreams["github"].pseudonymize_origin


def test_v5_fields_at_their_defaults_leave_the_digest_view_alone() -> None:
    explicit = _route(
        legacy_gate=True,
        pseudonymize_origin=False,
        fail_closed_unparsed=False,
    )
    assert digest_view(explicit) == digest_view(_route())
    assert "shared_egress" in digest_view(_route(shared_egress=str(SHIPPED_TABLE)))
