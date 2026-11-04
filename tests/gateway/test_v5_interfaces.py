"""v5's gateway interfaces (Batch 0): new route, sign-in and exchange fields, LOG-1 names, and
the ``RouteScorer`` constructor and stubs. All are inert: nothing the gateway writes moves."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from mcp_security.behaviour import BehaviourConfig
from mcp_security.behaviour.engine import ACCEPTED, MODERN_ERA, REJECTED
from mcp_security.behaviour.policy import config_to_json
from mcp_security.gateway import proxy
from mcp_security.gateway.config import (
    BASELINE_USER,
    DEFAULT_USER_CLAIM,
    LOG_ORIGIN_RAW,
    V5_ROUTE_FIELDS,
    OAuthConfig,
    Upstream,
    digest_view,
    load_config,
    oauth_of,
)
from mcp_security.gateway.framework import MAX_PENDING_CALLS, RouteScorer, load_artifacts
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import (
    BEHAVIOUR_FOLD,
    IDENTITY_STRENGTH_FIELD,
    LOG1_FIELDS,
    LOG1_NOTICES,
    POLICY_SWITCHED,
    TO_SERVER,
    CallFacts,
    Exchange,
    SessionBook,
    build_record,
)
from tests.gateway.golden_log import BREADTH_NAME, GOLDEN_DIR, KIND, POLICY, ROUTE, SCAN_NAME

UPSTREAM_URL = "http://upstream/mcp"
#: Every route field v5 adds, at its default: the gateway reads none of them yet.
V5_ROUTE_DEFAULTS = {
    "baseline_key": None,
    "zone_map": None,
    "route_zone": None,
    "shared_egress": None,
    "fail_closed_unparsed": False,
    "upstream_audit_header": None,
    "legacy_gate": True,  # PS7
    "pseudonymize_origin": False,  # PS10
    "log_origin": LOG_ORIGIN_RAW,  # PS10
}
#: A v4 route as a pre-v5 routes file names it, and the config_sha256 the pre-v5 gateway
#: wrote for it on its start and stop lines (recorded with the pre-v5 tree).
PRE_V5_ROUTE = {
    "name": "github",
    "url": UPSTREAM_URL,
    "scan": "s.json",
    "kind": "gh",
    "behaviour_policy": "p.json",
}
PRE_V5_CONFIG_DIGEST = "26369fd785e4"
DIGEST_CHARS = 12
V5_EXCHANGE_FIELDS = {"era": None, "protocol_issues": (), "reply_wire_bytes": None, "calls": {}}
CALLS = [
    ("get_file_contents", {"owner": "acme", "repo": "repo-a", "path": "README.md"}),
    ("list_commits", {"owner": "acme", "repo": "repo-c", "perPage": 30}),
    ("create_issue", {"owner": "acme", "repo": "repo-c", "title": "t", "body": "b"}),
]
#: Every v5 input the scorer's methods take, set: none may move a decision in Batch 0.
V5_CALL_INPUTS = {
    "era": MODERN_ERA,
    "app": "claude-code",
    "client_family": "claude-code",
    "zone": "Europe/Berlin",
    "arg_bytes": 321,
    "logical_call": "lc-1",
    "owner": "acme",
}
V5_OBSERVE_INPUTS = {k: v for k, v in V5_CALL_INPUTS.items() if k != "owner"}
V5_SESSION_INPUTS = {k: V5_CALL_INPUTS[k] for k in ("era", "app", "zone")}


class _Ledger:
    """An E14 ledger that remembers nothing: enough to show the scorer accepts one."""

    def note_read(
        self,
        caller: str,
        route: str,
        asset: str,
        sensitivity: int,
        ts: float,
        owner: str | None = None,
    ) -> None:
        """Forget the read."""

    def reads_since(
        self, caller: str, since: float
    ) -> list[tuple[float, str, str, int, str | None]]:
        """No reads."""
        return []


def _digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:DIGEST_CHARS]


def test_a_route_without_the_v5_fields_has_them_off() -> None:
    upstream = Upstream(name="github", url=UPSTREAM_URL)
    assert set(V5_ROUTE_FIELDS) == set(V5_ROUTE_DEFAULTS)
    assert {name: getattr(upstream, name) for name in V5_ROUTE_FIELDS} == V5_ROUTE_DEFAULTS
    oauth = OAuthConfig(issuer="https://idp", jwks_uri="https://idp/jwks", public_url="http://g")
    assert (oauth.user_claim, oauth.zone_claim) == (DEFAULT_USER_CLAIM, None)


def test_a_v4_routes_digest_view_is_its_pre_v5_config() -> None:
    upstream = Upstream(**PRE_V5_ROUTE)
    assert not set(V5_ROUTE_FIELDS) & set(digest_view(upstream))
    assert _digest(digest_view(upstream)) == PRE_V5_CONFIG_DIGEST


def test_a_v5_route_field_set_away_from_its_default_moves_the_digest() -> None:
    for name, value in (
        ("baseline_key", BASELINE_USER),
        ("legacy_gate", False),
        ("fail_closed_unparsed", True),
    ):
        view = digest_view(Upstream(**PRE_V5_ROUTE, **{name: value}))
        assert view[name] == value
        assert _digest(view) != PRE_V5_CONFIG_DIGEST


def test_the_gateway_writes_a_v4_routes_pre_v5_config_digest() -> None:
    assert proxy._config_digest(Upstream(**PRE_V5_ROUTE)) == PRE_V5_CONFIG_DIGEST


def test_a_routes_file_and_its_oauth_section_can_carry_the_v5_fields(tmp_path: Path) -> None:
    entry = {
        "url": UPSTREAM_URL,
        "baseline_key": BASELINE_USER,
        "route_zone": "Europe/Berlin",
        "zone_map": "zones.json",
        "shared_egress": "egress.json",
        "fail_closed_unparsed": True,
        "upstream_audit_header": "X-Caller",
    }
    oauth = {
        "issuer": "https://idp",
        "jwks_uri": "https://idp/jwks",
        "public_url": "http://g",
        "user_claim": "oid",
        "zone_claim": "zoneinfo",
    }
    routes = tmp_path / "routes.json"
    routes.write_text(json.dumps({"upstreams": {"github": entry}, "oauth": oauth}))
    config = load_config(routes)
    upstream = config.upstreams["github"]
    assert (upstream.baseline_key, upstream.route_zone) == (BASELINE_USER, "Europe/Berlin")
    assert (config.oauth.user_claim, config.oauth.zone_claim) == ("oid", "zoneinfo")


@pytest.mark.parametrize(
    "bad",
    [{"baseline_key": "everyone"}, {"route_zone": "Mars/Base"}, {"log_origin": "hashed"}],
)
def test_a_bad_v5_route_value_is_refused(bad: dict) -> None:
    with pytest.raises(ValueError):
        Upstream(name="github", url=UPSTREAM_URL, **bad)
    with pytest.raises(ValueError, match="unknown keys"):
        oauth_of({"issuer": "i", "jwks_uri": "j", "public_url": "p", "role_claim": "r"})


def test_the_exchange_v5_fields_start_empty_and_change_no_log_line() -> None:
    exchange = Exchange(route="github", agent="a", session=None, http_method="POST")
    assert {name: getattr(exchange, name) for name in V5_EXCHANGE_FIELDS} == V5_EXCHANGE_FIELDS
    assert set(V5_EXCHANGE_FIELDS) <= {f.name for f in fields(Exchange)}
    call = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "t", "arguments": {"a": 1}},
    }
    record = build_record(exchange, SessionBook(), TO_SERVER, None, call)
    assert not {*LOG1_FIELDS, IDENTITY_STRENGTH_FIELD} & set(record)


def test_the_exchange_keeps_the_call_facts_per_request_id() -> None:
    first, second = (
        CallFacts(arg_bytes=10, logical_call="a"),
        CallFacts(arg_bytes=99, outcome=REJECTED),
    )
    exchange = Exchange(
        route="github",
        agent="a",
        session=None,
        http_method="POST",
        calls={"1": first, '"x"': second},
    )
    assert exchange.call_facts({"id": 1}) == first  # a request and its reply share the id
    assert exchange.call_facts({"id": "x", "result": {}}) == second
    assert exchange.call_facts({"id": 2}) == CallFacts()
    assert CallFacts() == CallFacts(None, None, None, None)
    with pytest.raises(FrozenInstanceError):
        first.outcome = ACCEPTED  # type: ignore[misc]


def test_the_log1_names() -> None:
    assert LOG1_FIELDS == (
        "gateway.baseline_key",
        "gateway.zone",
        "gateway.protocol_era",
        "gateway.protocol_issues",
        "gateway.reply_wire_bytes",
        "gateway.logical_call",
        "gateway.outcome",
    )
    assert LOG1_NOTICES == ("behaviour_fold", "policy_switched", "flag_surge")
    assert IDENTITY_STRENGTH_FIELD == "gateway.identity_strength"


def _scorer(policy: Path, **kwargs: object) -> RouteScorer:
    artifacts = load_artifacts(
        ROUTE, str(GOLDEN_DIR / SCAN_NAME), str(GOLDEN_DIR / BREADTH_NAME), None, KIND, str(policy)
    )
    return RouteScorer(ROUTE, artifacts, **kwargs)


def _untimed(decision: dict) -> dict:
    return {k: v for k, v in decision.items() if k != "score_us"}


@pytest.mark.parametrize("design", ["v4", "v5"])
def test_the_route_scorer_stubs_and_v5_inputs_do_nothing(tmp_path: Path, design: str) -> None:
    policy = tmp_path / "policy.json"
    config = BehaviourConfig(design=design) if design == "v5" else POLICY
    policy.write_text(json.dumps(config_to_json(config)))
    route = Upstream(name=ROUTE, url=UPSTREAM_URL, route_zone="Europe/Berlin")
    stubbed = _scorer(policy, pseudonymizer=Pseudonymizer(b"k"), ledger=_Ledger(), upstream=route)
    plain = _scorer(policy)
    assert isinstance(stubbed.ledger, _Ledger) and stubbed.pseudonymizer.keyed
    assert stubbed.upstream is route and plain.upstream is None
    for i, (tool, args) in enumerate(CALLS * 4):
        ts, caller = 1_780_000_000.0 + 600.0 * i, f"c{i % 2}"
        stubbed.observe(
            "initialize", ts - 2, caller, "s1", "10.0.0.1", "cc/1", 90, **V5_OBSERVE_INPUTS
        )
        plain.observe("initialize", ts - 2, caller, "s1", "10.0.0.1", "cc/1", 90)
        stubbed.session_initialized(caller, "s1", ts - 1, **V5_SESSION_INPUTS)
        plain.session_initialized(caller, "s1", ts - 1)
        decision = stubbed.score(tool, args, ts, caller, session="s1", size=200, **V5_CALL_INPUTS)
        before = json.dumps(stubbed.state(), sort_keys=True)
        assert stubbed.reply(caller, "tools/call", tool, ts + 1, 5_000) is None
        assert (
            stubbed.score_read("resources/read", "repo://x", {}, ts + 2, caller, **V5_CALL_INPUTS)
            is None
        )
        assert stubbed.commit(V5_CALL_INPUTS["logical_call"], ACCEPTED) is None
        assert stubbed.commit("never-scored", REJECTED) is None
        assert stubbed.commit(None) is None
        for notice in (BEHAVIOUR_FOLD, POLICY_SWITCHED):
            assert stubbed.apply_notice({"gateway.notice": notice, "ts": ts + 3}) is None
        assert json.dumps(stubbed.state(), sort_keys=True) == before
        expected = plain.score(tool, args, ts, caller, session="s1", size=200)
        assert _untimed(decision) == _untimed(expected)
    assert stubbed.behaviour.snapshot() == plain.behaviour.snapshot()


def test_nothing_is_pending_commit_in_batch_0_and_the_bound_is_named(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(config_to_json(BehaviourConfig(design="v5"))))
    scorer = _scorer(policy)
    tool, args = CALLS[0]
    scorer.score(tool, args, 1_780_000_000.0, "c0", logical_call="lc-1")
    assert not scorer._pending and MAX_PENDING_CALLS > 0
