"""v5 origin values (I7): keyed pseudonyms of the network and client values (PS10), which
leave every design's verdicts unchanged, and the missing-client value that the gateway
and the engine must spell alike (B2, E11)."""

from __future__ import annotations

import json
import re

import pytest

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message
from mcp_security.behaviour.engine import (
    CLIENT,
    DESIGNS,
    NETWORK,
    NEW_CLIENT,
    NEW_NETWORK,
    V5,
    client_family,
    network_of,
)
from mcp_security.gateway.config import LOG_ORIGIN_NETWORK_PSEUDONYM, LOG_ORIGIN_RAW
from mcp_security.gateway.egress.table import platform_network
from mcp_security.gateway.oauth import (
    APP_PSEUDONYM,
    CLIENT_PSEUDONYM,
    NETWORK_PSEUDONYM,
    NO_CLIENT,
    PSEUDONYM_DOMAIN_SEPARATOR,
    ClientPair,
    client_pair,
    logged_origin,
    pseudonymous_client,
    pseudonymous_client_name,
    pseudonymous_network,
)
from mcp_security.gateway.pseudonym import Pseudonymizer

APP_A = "agent-app-a"  # a synthetic agent application
KEY = Pseudonymizer(b"test-origin-key")
OTHER_KEY = Pseudonymizer(b"another-origin-key")
DAY_S, HOUR_S = 86_400.0, 3_600.0
T0 = 1_780_000_000.0
DOTTED_SLASH16 = r"\d+\.\d+\.\d+\.\d+/16"


# ── PS10 ────────────────────────────────────────────────────────────────────────────────


def test_network_pseudonyms_keep_equality_and_hide_the_value() -> None:
    net = "10.20.0.0/16"
    first, again = pseudonymous_network(net, KEY), pseudonymous_network(net, KEY)
    assert first == again and first.startswith(NETWORK_PSEUDONYM)
    assert "10.20" not in first
    assert pseudonymous_network("10.21.0.0/16", KEY) != first
    assert pseudonymous_network(net, OTHER_KEY) != first  # keyed
    assert pseudonymous_network(first, KEY) == first  # a pseudonymised log re-scored offline
    label = platform_network("anthropic")
    assert pseudonymous_network(label, KEY) == label  # platforms stay readable
    assert pseudonymous_network(None, KEY) is None


def test_origin_pseudonyms_are_domain_separated_by_kind() -> None:
    # PS10: the keyed hash covers the kind's prefix and a separator, so one text never gets
    # the same pseudonym as a network and as an app or client name
    text = "10.20.0.0/16"
    hidden = pseudonymous_network(text, KEY)
    suffix = hidden.removeprefix(NETWORK_PSEUDONYM)
    assert suffix == KEY.of(f"{NETWORK_PSEUDONYM}{PSEUDONYM_DOMAIN_SEPARATOR}{text}")
    assert suffix not in (KEY.of(text), KEY.of(f"{NETWORK_PSEUDONYM}{text}"))
    pair = pseudonymous_client(ClientPair(text, text), KEY)
    others = {pair.app.removeprefix(APP_PSEUDONYM), pair.family.removeprefix(CLIENT_PSEUDONYM)}
    assert len(others | {suffix}) == 3


def test_origin_pseudonyms_refuse_to_work_unkeyed() -> None:
    with pytest.raises(ValueError, match="key"):
        pseudonymous_network("10.20.0.0/16", Pseudonymizer())
    with pytest.raises(ValueError, match="key"):
        pseudonymous_client(ClientPair(APP_A, "cursor"), Pseudonymizer())


def test_client_pseudonyms_keep_the_pair_shape() -> None:
    pair = pseudonymous_client(ClientPair(APP_A, "cursor"), KEY)
    assert pair.app != APP_A and pair.family != "cursor"
    assert pseudonymous_client(ClientPair(APP_A, "cursor"), KEY) == pair
    assert pseudonymous_client(ClientPair(None, NO_CLIENT), KEY) == ClientPair(None, NO_CLIENT)
    name = pseudonymous_client_name("Cursor/1.4", KEY)
    assert name == pseudonymous_client_name("cursor/2.0", KEY)
    assert client_family(name) == name  # the engine keeps it as it is
    assert pseudonymous_client_name(None, KEY) is None


def test_the_logged_origin_follows_log_origin() -> None:
    assert logged_origin(LOG_ORIGIN_RAW, "10.20.3.4", "net:abc") == "10.20.3.4"
    assert logged_origin(LOG_ORIGIN_NETWORK_PSEUDONYM, "10.20.3.4", "net:abc") == "net:abc"
    with pytest.raises(ValueError):
        logged_origin("hashed", "10.20.3.4", "net:abc")


def _stream() -> list[tuple[float, str, str, str, str]]:
    """Three synthetic callers over 30 days: mostly their usual network and client, with a
    few new ones, so the origin dimensions take part. (ts, agent, tool, address, client)."""
    usual = {
        "caller-a": ("10.1.2.3", "cursor/1.0"),
        "caller-b": ("10.2.9.9", "claude-code/2.0"),
        "caller-c": ("160.79.105.7", "vscode/1.9"),  # inside the Anthropic range
    }
    rows = []
    for day in range(30):
        for i, (agent, (address, client)) in enumerate(usual.items()):
            for call in range(6):
                ts = T0 + day * DAY_S + (9 + i) * HOUR_S + call * 300.0
                odd = day in (20, 27) and call == 3
                rows.append(
                    (
                        ts,
                        agent,
                        "get_file_contents" if call % 2 else "list_commits",
                        f"10.{50 + day}.0.1" if odd else address,
                        "evil-cli/0.1" if odd and i == 0 else client,
                    )
                )
    return sorted(rows)


def test_the_engine_reads_a_missing_client_name_as_the_gateways_none() -> None:
    # E11 drift guard: a family that arrives as None is the engine's "(none)" (J1), the value
    # the gateway sends as NO_CLIENT, so a late None must not look like a new client
    config = BehaviourConfig(design=V5)
    mixed, steady = BehaviourEngine(config), BehaviourEngine(config)
    rows = _stream()
    late = len(rows) - len(rows) // 10
    for i, (ts, agent, tool, address, _) in enumerate(rows):
        common = {"ts": ts, "agent": agent, "method": "tools/call", "session": None}
        common |= {"tool": tool, "address": address, "client": None, "app": APP_A}
        family = None if i >= late and i % 2 else NO_CLIENT
        assert mixed.observe(Message(**common, client_family=family)) == steady.observe(
            Message(**common, client_family=NO_CLIENT)
        )


@pytest.mark.parametrize("design", DESIGNS)
def test_every_designs_verdicts_are_identical_on_pseudonymised_origins(design: str) -> None:
    config = BehaviourConfig(design=design)
    raw, hidden = BehaviourEngine(config), BehaviourEngine(config)
    raw_verdicts, hidden_verdicts = [], []
    for ts, agent, tool, address, client in _stream():
        pair = client_pair(APP_A, (), client)
        hidden_pair = pseudonymous_client(pair, KEY)
        common = {"ts": ts, "agent": agent, "method": "tools/call", "session": None, "tool": tool}
        raw_verdicts.append(
            raw.observe(
                Message(
                    **common,
                    address=address,
                    client=client,
                    app=pair.app,
                    client_family=pair.family,
                )
            )
        )
        hidden_verdicts.append(
            hidden.observe(
                Message(
                    **common,
                    address=pseudonymous_network(network_of(address, config), KEY),
                    client=pseudonymous_client_name(client, KEY),
                    app=hidden_pair.app,
                    client_family=hidden_pair.family,
                )
            )
        )
    assert hidden_verdicts == raw_verdicts
    origin = {NETWORK, CLIENT, NEW_NETWORK, NEW_CLIENT}
    assert any(origin & set(v.scores) for v in raw_verdicts)  # the origin took part
    snapshot = json.dumps(hidden.snapshot(), default=str)
    assert re.search(DOTTED_SLASH16, json.dumps(raw.snapshot(), default=str))
    assert not re.search(DOTTED_SLASH16, snapshot)  # no raw /16 is saved
