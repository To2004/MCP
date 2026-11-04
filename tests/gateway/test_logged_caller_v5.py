"""v5 caller keys offline (I7; B1, DEP-6): the key the live gateway gave a call, rebuilt
from its log line for an offline re-score and the v5 migration replay. A line written by
v5's gateway carries the key; an older one is rebuilt per agent (D5)."""

from __future__ import annotations

import pytest

from mcp_security.gateway.config import (
    ANONYMOUS,
    BASELINE_AGENT,
    BASELINE_KEYS,
    BASELINE_USER,
    BASELINE_USER_APP,
    Identity,
)
from mcp_security.gateway.oauth import (
    baseline_caller,
    baseline_key_of,
    identity_from_claims,
    logged_baseline_caller,
    reported_key,
)
from mcp_security.gateway.wire_log import TO_SERVER, Exchange, LogPolicy, SessionBook, build_record
from tests.gateway.tokens import ISSUER

PERSON = "person-0001"  # synthetic directory ids and apps: no real identities
APP_A, APP_B = "agent-app-a", "agent-app-b"
ENTRA_OID = "00000000-0000-4000-8000-000000000001"
ADDRESS, OTHER_ADDRESS = "198.51.100.7", "198.51.100.8"  # documentation range (RFC 5737)
CLIENT_INFO = "claude-code/2.1.0"


def _claims(**extra: object) -> dict[str, object]:
    return {"iss": ISSUER, "sub": PERSON, "client_id": APP_A, **extra}


# ── DEP-6: the same caller key offline, from the log line ───────────────────────────────


def _exchange(identity: Identity, address: str = ADDRESS, **v5: object) -> Exchange:
    """The exchange the proxy builds for one call (``_exchange`` in proxy.py)."""
    return Exchange(
        route="github",
        agent=identity.agent,
        session=None,
        http_method="POST",
        client_address=address,
        client_info=CLIENT_INFO,
        user=identity.user,
        app=identity.app,
        agent_id=identity.id,
        auth=identity.auth,
        issuer=identity.issuer,
        **v5,
    )


def _line(exchange: Exchange, v5: bool) -> dict:
    """The request line the gateway writes for ``exchange``; v5's fields only with ``v5``."""
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "t"}}
    return build_record(exchange, SessionBook(), TO_SERVER, None, call, LogPolicy(v5=v5))


def _live(mode: str, identity: Identity, address: str = ADDRESS) -> str | None:
    """The key the live gateway gives the call (plan, "Identity per agent", J3)."""
    reported = reported_key(CLIENT_INFO, address) if identity.id is None else None
    return baseline_caller(mode, identity.key, identity.baseline_key, reported)


@pytest.mark.parametrize("mode", BASELINE_KEYS)
@pytest.mark.parametrize("signed_in", [True, False])
def test_an_old_log_line_gives_the_live_key(mode: str, signed_in: bool) -> None:
    identity = identity_from_claims(_claims()) if signed_in else ANONYMOUS
    old = _line(_exchange(identity), v5=False)
    assert "gateway.baseline_key" not in old
    assert logged_baseline_caller(old, mode) == _live(mode, identity)
    live = _live(mode, identity)
    assert logged_baseline_caller(_line(_exchange(identity, baseline_key=live), True), mode) == live


def test_the_migration_keeps_unsigned_agents_apart_and_v4_as_it_was() -> None:
    first = _line(_exchange(ANONYMOUS), v5=False)
    second = _line(_exchange(ANONYMOUS, OTHER_ADDRESS), v5=False)
    keys = {logged_baseline_caller(line, BASELINE_AGENT) for line in (first, second)}
    assert keys == {reported_key(CLIENT_INFO, ADDRESS), reported_key(CLIENT_INFO, OTHER_ADDRESS)}
    assert logged_baseline_caller(first, BASELINE_USER_APP) == "anonymous"  # v1-v4: unchanged
    # a v5 line re-scored by v1-v4 keeps the v1-v4 key, whatever the line logged
    v5_line = _line(_exchange(ANONYMOUS, baseline_key="reported-key"), v5=True)
    assert logged_baseline_caller(v5_line, BASELINE_USER_APP) == "anonymous"


def test_an_old_line_rebuilds_the_per_person_key_only_from_sub() -> None:
    by_sub = identity_from_claims(_claims(client_id=APP_B))
    old = _line(_exchange(by_sub), v5=False)
    assert logged_baseline_caller(old, BASELINE_USER) == baseline_key_of(ISSUER, PERSON)
    assert logged_baseline_caller(old, BASELINE_USER) == by_sub.baseline_key  # as a v5 line
    # oid was never logged: an old line under an oid route keeps the agent key, and only a
    # v5 line, which logs the key the live gateway used, gives the per-person one
    assert logged_baseline_caller(old, BASELINE_USER, user_claim="oid") == by_sub.key
    by_oid = identity_from_claims(_claims(client_id=APP_B, oid=ENTRA_OID), user_claim="oid")
    v5_line = _line(_exchange(by_oid, baseline_key=by_oid.baseline_key), v5=True)
    assert logged_baseline_caller(v5_line, BASELINE_USER, "oid") == baseline_key_of(
        ISSUER, ENTRA_OID
    )
    with pytest.raises(ValueError):
        logged_baseline_caller(old, "everyone")
