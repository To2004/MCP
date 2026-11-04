"""v5 caller identity (I7): the per-agent baseline key and the opt-in per-person key (B1, D5),
the Client pair (B2, E11) and the caller's zone with its fallback share (B9d). The same keys
offline: test_logged_caller_v5.py; origin pseudonyms (PS10): test_origin_values_v5.py."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mcp_security.gateway.config import (
    ANONYMOUS,
    BASELINE_AGENT,
    BASELINE_USER,
    BASELINE_USER_APP,
    OAuthConfig,
    load_zone_map,
)
from mcp_security.gateway.oauth import (
    FALLBACK_USER_CLAIM,
    NO_CLIENT,
    ZONE_FROM_CLAIM,
    ZONE_FROM_MAP,
    ZONE_FROM_ROUTE,
    ClientPair,
    LatestPerCaller,
    TokenVerifier,
    UserClaimReport,
    ZoneResolver,
    baseline_caller,
    baseline_key_of,
    client_pair,
    identity_from_claims,
    reported_key,
    user_claim_fell_back,
    zone_from_claims,
)
from tests.gateway.tokens import ISSUER, OAUTH, ROUTE, SIGNING_KEY, FixedKeys, mint

PERSON = "person-0001"  # synthetic directory ids and apps: no real identities
OTHER_PERSON = "person-0002"
APP_A, APP_B = "agent-app-a", "agent-app-b"
ENTRA_OID = "00000000-0000-4000-8000-000000000001"
ADDRESS, OTHER_ADDRESS = "198.51.100.7", "198.51.100.8"  # documentation range (RFC 5737)
CLIENT_INFO = "claude-code/2.1.0"


def _claims(**extra: object) -> dict[str, object]:
    return {"iss": ISSUER, "sub": PERSON, "client_id": APP_A, **extra}


def _verifier(**changes: object) -> TokenVerifier:
    config = OAuthConfig(
        issuer=OAUTH.issuer, jwks_uri=OAUTH.jwks_uri, public_url=OAUTH.public_url, **changes
    )
    return TokenVerifier(config, FixedKeys(SIGNING_KEY))


# ── B1 ──────────────────────────────────────────────────────────────────────────────────


def test_two_client_ids_give_one_user() -> None:
    verifier = _verifier()
    a = verifier.verify(mint(sub=PERSON, client_id=APP_A), ROUTE)
    b = verifier.verify(mint(sub=PERSON, client_id=APP_B), ROUTE)
    assert a.id != b.id  # session owners stay per (issuer, app, user)
    assert a.baseline_key == b.baseline_key == baseline_key_of(ISSUER, PERSON)
    assert (a.person, a.baseline_source) == (PERSON, "sub")
    other = verifier.verify(mint(sub=OTHER_PERSON, client_id=APP_A), ROUTE)
    assert other.baseline_key != a.baseline_key


def test_the_baseline_key_is_sha256_of_issuer_and_person() -> None:
    expected = hashlib.sha256(f"{ISSUER}|{PERSON}".encode()).hexdigest()[:12]
    assert baseline_key_of(ISSUER, PERSON) == expected
    assert baseline_key_of("https://other-idp.example", PERSON) != expected  # iss stays in


def test_an_entra_style_token_needs_the_oid_claim() -> None:
    # Entra: sub is pairwise per application; oid is the same across applications.
    a = _claims(sub="pairwise-for-app-a", client_id=APP_A, oid=ENTRA_OID)
    b = _claims(sub="pairwise-for-app-b", client_id=APP_B, oid=ENTRA_OID)
    by_oid = [identity_from_claims(c, user_claim="oid") for c in (a, b)]
    by_sub = [identity_from_claims(c) for c in (a, b)]
    assert by_oid[0].baseline_key == by_oid[1].baseline_key
    assert {i.baseline_source for i in by_oid} == {"oid"}
    assert by_sub[0].baseline_key != by_sub[1].baseline_key


def test_the_verifier_reads_the_routes_user_claim() -> None:
    verifier = _verifier(user_claim="oid")
    a = verifier.verify(mint(sub="pairwise-a", client_id=APP_A, oid=ENTRA_OID), ROUTE)
    b = verifier.verify(mint(sub="pairwise-b", client_id=APP_B, oid=ENTRA_OID), ROUTE)
    assert a.baseline_key == b.baseline_key == baseline_key_of(ISSUER, ENTRA_OID)


def test_a_client_credentials_token_has_a_stable_baseline() -> None:
    first = identity_from_claims(_claims(sub=APP_A, client_id=APP_A, jti="t-1"))
    second = identity_from_claims(_claims(sub=APP_A, client_id=APP_A, jti="t-2"))
    assert first.baseline_key == second.baseline_key == baseline_key_of(ISSUER, APP_A)


@pytest.mark.parametrize("missing", [None, "", True, {"nested": 1}])
def test_a_missing_user_claim_falls_back_to_sub_and_says_so(missing: object) -> None:
    claims = _claims() if missing is None else _claims(oid=missing)
    identity = identity_from_claims(claims, user_claim="oid")
    assert identity.baseline_source == FALLBACK_USER_CLAIM
    assert identity.baseline_key == baseline_key_of(ISSUER, PERSON)
    assert user_claim_fell_back(identity, "oid")


def test_a_numeric_user_claim_names_the_person() -> None:
    identity = identity_from_claims(_claims(oid=12345), user_claim="oid")
    assert (identity.person, identity.baseline_source) == ("12345", "oid")
    assert identity.baseline_key == baseline_key_of(ISSUER, "12345")
    assert not user_claim_fell_back(identity, "oid")


def test_user_claim_fallbacks_are_counted_for_the_route() -> None:
    # B1, opt-in "user" mode: a token without the claim keys its caller by a per-app sub
    report = UserClaimReport("oid")
    with_oid = identity_from_claims(_claims(oid=ENTRA_OID), user_claim="oid")
    without = identity_from_claims(_claims(client_id=APP_B), user_claim="oid")
    assert report.observe(with_oid) is False
    assert report.observe(without) is True
    assert report.observe(without) is True  # one caller counts once
    assert report.observe(ANONYMOUS) is False  # without sign-in: no claim, not counted
    assert report.report() == {
        "user_claim": "oid",
        "user_claim_callers": 2,
        "user_claim_fallback_share": pytest.approx(0.5),
    }
    report.observe(with_oid, caller=without.key)  # his latest state counts
    assert report.report()["user_claim_fallback_share"] == pytest.approx(0.0)
    sub_route = identity_from_claims(_claims())
    assert not user_claim_fell_back(sub_route, "sub")  # a sub route never falls back
    assert UserClaimReport().report()["user_claim_fallback_share"] == 0.0


def test_the_v4_identity_fields_are_unchanged() -> None:
    identity = identity_from_claims(_claims(act={"sub": "actor-1"}, scope="a b", jti="j"))
    agent_id = hashlib.sha256(f"{ISSUER}|{APP_A}|{PERSON}".encode()).hexdigest()[:12]
    assert (identity.agent, identity.user, identity.app, identity.id) == (
        APP_A,
        PERSON,
        APP_A,
        agent_id,
    )
    assert (identity.scopes, identity.token_id, identity.actors) == (("a", "b"), "j", ("actor-1",))


def test_the_baseline_caller_follows_the_mode() -> None:
    identity = identity_from_claims(_claims())
    user_key, agent_key = identity.baseline_key, identity.key
    assert baseline_caller(BASELINE_USER, agent_key, user_key) == user_key
    assert baseline_caller(BASELINE_USER_APP, agent_key, user_key) == agent_key
    assert baseline_caller(BASELINE_USER, agent_key, None) == agent_key  # a pre-v5 log line
    assert baseline_caller(BASELINE_USER, ANONYMOUS.key, ANONYMOUS.baseline_key) == "anonymous"
    with pytest.raises(ValueError):
        baseline_caller("everyone", agent_key, user_key)


# ── B1 per agent (revised 2026-10-27, D5): no user ids, at most an agent id ─────────────


def test_v5_keeps_a_signed_in_agent_under_its_agent_key() -> None:
    identity = identity_from_claims(_claims())
    assert baseline_caller(BASELINE_AGENT, identity.key, identity.baseline_key) == identity.key


def test_v5_keeps_a_caller_without_sign_in_under_its_reported_name_and_address() -> None:
    reported = reported_key("claude-code/2.1.0", "198.51.100.7")
    assert baseline_caller(BASELINE_AGENT, ANONYMOUS.key, None, reported) == reported
    assert reported != ANONYMOUS.key and len(reported) == len(identity_from_claims(_claims()).key)
    # v1-v4 and the opt-in per-person mode keep every unsigned caller in "anonymous"
    assert baseline_caller(BASELINE_USER_APP, ANONYMOUS.key, None, reported) == "anonymous"
    assert baseline_caller(BASELINE_USER, ANONYMOUS.key, None, reported) == "anonymous"


def test_a_reported_key_survives_an_upgrade_but_not_a_new_name_or_machine() -> None:
    first = reported_key("claude-code/2.1.0", "198.51.100.7")
    assert reported_key("Claude-Code/2.2.0", "198.51.100.7") == first  # version, case
    assert reported_key("cursor/1.0", "198.51.100.7") != first  # another program
    assert reported_key("claude-code/2.1.0", "198.51.100.8") != first  # another machine
    assert reported_key(None, "198.51.100.7") == reported_key("", "198.51.100.7")  # no name
    assert reported_key(None, "198.51.100.7") != first


def test_a_reported_key_counts_an_ipv6_caller_by_its_64() -> None:
    first = reported_key("agent/1", "2001:db8:1:2::10")
    assert reported_key("agent/1", "2001:db8:1:2:aaaa:bbbb:cccc:dddd") == first  # same /64
    assert reported_key("agent/1", "2001:db8:1:3::10") != first  # another /64
    mapped = reported_key("agent/1", "::ffff:198.51.100.7")
    assert mapped == reported_key("agent/1", "198.51.100.7")  # an IPv4-mapped address


def test_a_reported_key_never_equals_a_signed_in_agent_key() -> None:
    identity = identity_from_claims(_claims())
    text = f"{ISSUER}|{identity.app}|{identity.user}"
    assert reported_key(text, None) != identity.key
    assert reported_key(None, None) == reported_key("", "")  # no name, no address: one key


# ── B2, E11 ─────────────────────────────────────────────────────────────────────────────


def test_the_client_pair_is_the_authenticated_app_and_the_client_family() -> None:
    assert client_pair(APP_A, (), "Cursor/1.4.2") == ClientPair(APP_A, "cursor")
    assert client_pair(APP_A, ["actor-svc", "outer"], "cursor/1.0") == ClientPair(
        "actor-svc", "cursor"
    )
    assert client_pair(APP_A, None, None) == ClientPair(APP_A, NO_CLIENT)
    assert client_pair(None, (), "") == ClientPair(None, NO_CLIENT)  # no token, no name


def test_a_borrowed_token_with_a_new_client_info_is_a_new_value() -> None:
    usual = client_pair(APP_A, (), "claude-code/2.0.1")
    assert client_pair(APP_A, (), "claude-code/2.1.0") == usual  # a version bump is not new
    assert client_pair(APP_A, (), "evil-cli/0.1") != usual
    assert client_pair(APP_A, (), None) != usual  # dropping the name is itself new
    assert client_pair(APP_B, (), "claude-code/2.0.1") != usual


# ── B9d ─────────────────────────────────────────────────────────────────────────────────


def _zone_map(tmp_path: Path, users: dict[str, str]) -> Path:
    path = tmp_path / "zones.json"
    path.write_text(json.dumps({"version": 1, "users": users}))
    return path


def test_the_zone_comes_from_the_map_then_the_claim_then_the_route(tmp_path: Path) -> None:
    directory = load_zone_map(_zone_map(tmp_path, {PERSON: "Australia/Sydney"}))
    resolver = ZoneResolver("Europe/Berlin", directory)
    assert resolver.resolve("k1", PERSON, "America/Chicago") == (
        resolver.resolve("k1", PERSON, None)
    )
    assert resolver.resolve("k1", PERSON, "America/Chicago").source == ZONE_FROM_MAP
    claim = resolver.resolve("k2", OTHER_PERSON, "America/Chicago")
    assert (claim.zone, claim.source) == ("America/Chicago", ZONE_FROM_CLAIM)
    fallback = resolver.resolve("k3", OTHER_PERSON, "Not/AZone")
    assert (fallback.zone, fallback.source) == ("Europe/Berlin", ZONE_FROM_ROUTE)


def test_the_share_of_callers_on_the_fallback_zone_is_reported(tmp_path: Path) -> None:
    directory = load_zone_map(_zone_map(tmp_path, {PERSON: "Asia/Tokyo"}))
    resolver = ZoneResolver(directory=directory)
    assert resolver.fallback_share() == 0.0
    resolver.resolve("k1", PERSON)
    resolver.resolve("k2", "p2", "America/Denver")
    resolver.resolve("k3", "p3")
    resolver.resolve("k4", "p4")
    resolver.resolve("k4", "p4")  # one caller counts once
    resolver.resolve(None, "p5")  # no caller key: not counted
    assert resolver.fallback_share() == pytest.approx(2 / 4)
    assert resolver.report() == {
        "zone_callers": 4,
        "zone_fallback_share": pytest.approx(0.5),
        "zone_sources": {ZONE_FROM_MAP: 1, ZONE_FROM_CLAIM: 1, ZONE_FROM_ROUTE: 2},
    }
    resolver.resolve("k3", "p3", "America/Denver")  # his latest source counts
    assert resolver.fallback_share() == pytest.approx(1 / 4)


def test_the_fallback_count_is_bounded() -> None:
    resolver = ZoneResolver(max_callers=3)
    for i in range(10):
        resolver.resolve(f"k{i}")
    assert resolver.report()["zone_callers"] == 3
    with pytest.raises(ValueError):
        ZoneResolver(max_callers=0)
    with pytest.raises(ValueError):
        ZoneResolver("Mars/Base")
    with pytest.raises(ValueError):
        ZoneResolver(5)


def test_the_report_tally_forgets_the_stalest_caller_first() -> None:
    tally = LatestPerCaller(max_callers=3)
    for caller in ("k0", "k1", "k2"):
        tally.record(caller, ZONE_FROM_ROUTE)
    tally.record("k0", ZONE_FROM_MAP)  # seen again: now the most recent
    tally.record("k3", ZONE_FROM_ROUTE)
    assert "k1" not in tally  # the stalest left
    assert all(caller in tally for caller in ("k0", "k2", "k3"))
    assert tally.counts() == {ZONE_FROM_MAP: 1, ZONE_FROM_ROUTE: 2}
    assert tally.share(ZONE_FROM_MAP) == pytest.approx(1 / 3)
    with pytest.raises(ValueError):
        LatestPerCaller(max_callers=0)


def test_the_zone_report_counts_agents_by_default() -> None:
    # D5: the report's callers are the baseline callers, agents by default, not persons
    resolver = ZoneResolver()
    for app in (APP_A, APP_B):  # one person, two agents
        resolver.resolve_identity(identity_from_claims(_claims(client_id=app)))
    assert resolver.report()["zone_callers"] == 2
    resolver.resolve_identity(ANONYMOUS, caller=reported_key(CLIENT_INFO, ADDRESS))
    assert resolver.report()["zone_callers"] == 3


def test_the_zone_claim_is_read_only_when_configured_and_valid() -> None:
    claims = _claims(zoneinfo="America/Chicago")
    assert zone_from_claims(claims, "zoneinfo") == "America/Chicago"
    assert zone_from_claims(claims, None) is None
    assert zone_from_claims(_claims(zoneinfo="Mars/Base"), "zoneinfo") is None
    assert zone_from_claims(_claims(zoneinfo="../../etc/passwd"), "zoneinfo") is None
    assert zone_from_claims(_claims(zoneinfo=7), "zoneinfo") is None
    identity = identity_from_claims(claims, zone_claim="zoneinfo")
    assert identity.zone == "America/Chicago"
    choice = ZoneResolver().resolve_identity(identity)
    assert (choice.zone, choice.source) == ("America/Chicago", ZONE_FROM_CLAIM)
