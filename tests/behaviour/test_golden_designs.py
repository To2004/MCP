"""INF-1: designs v1-v4 give exactly their recorded verdicts on the seeded stream.

The stream and the recorder live in ``golden_stream.py``; the recorded verdicts in
``golden/engine_v*.json.gz``. Every v5 change keeps v1-v4 bit-identical (legacy fixes only
under ``legacy_fixes``), so this pin must hold after every batch. The rounded rows are
compared everywhere, message by message; the exact digests (``float.hex``) on the platform
they were recorded on.
"""

from __future__ import annotations

from collections import Counter
from ipaddress import ip_address

import pytest

from mcp_security.behaviour import BehaviourEngine
from tests.behaviour.golden_stream import (
    BOT,
    DAY_S,
    IPV6_ADDRESSES,
    NOT_AN_IP,
    ODD_CLIENTS,
    PINNED_DESIGNS,
    POLICY,
    PROMPT_GET,
    RESOURCE_READ,
    VERSIONLESS_CLIENT,
    build_stream,
    exact_digest,
    golden_config,
    load_golden,
    restarted,
    restore_index,
    stream_digest,
    this_platform,
    verdict_row,
    verdicts,
)

MIN_CALLERS = 6
MIN_DAYS = 25
IPV6 = 6


@pytest.fixture(scope="module")
def stream():
    return build_stream()


def test_the_fixture_covers_what_the_v5_changes_touch(stream) -> None:
    calls = [m for m in stream if m.method == "tools/call"]
    guarded = set(POLICY["requires_before"])
    assert len({m.agent for m in stream}) >= MIN_CALLERS + 1 and BOT in {m.agent for m in stream}
    assert len({int((m.ts - stream[0].ts) // DAY_S) for m in stream}) >= MIN_DAYS
    assert {m.operation for m in calls} == {"read", "write"}
    assert {m.sensitivity for m in calls} >= {None, 1, 2, 3, 4, 5}
    assert any(m.session is None and m.tool in guarded for m in calls)  # E1
    assert any(m.session is None for m in calls) and any(m.session for m in calls)  # E2
    assert any(b.ts < a.ts for a, b in zip(stream, stream[1:]))  # the late message (RF9)


def test_the_fixture_covers_the_inputs_later_batches_rewrite(stream) -> None:
    methods = {m.method for m in stream}
    assert {RESOURCE_READ, PROMPT_GET} <= methods  # AI-10
    addresses = {m.address for m in stream if m.address}
    assert set(IPV6_ADDRESSES) <= addresses and NOT_AN_IP in addresses  # B10
    assert len({ip_address(a).exploded[:14] for a in IPV6_ADDRESSES}) == len(IPV6_ADDRESSES)
    assert all(ip_address(a).version == IPV6 for a in IPV6_ADDRESSES)
    clients = {m.client for m in stream if m.method == "tools/call"}
    assert {*ODD_CLIENTS, VERSIONLESS_CLIENT} <= clients  # B2, E11
    assert 0 < restore_index(stream) < len(stream)


def test_the_fixture_records_one_callers_first_use_twice() -> None:
    engine = BehaviourEngine(golden_config("v4"))
    for message in build_stream():
        engine.observe(message)
    uses = Counter(agent for _, agent in engine.first_uses.by_value[("asset", "repo-shared")])
    assert uses["dave"] == 2 and uses["carol"] == 1


def _same_platform(golden: dict) -> bool:
    return golden["recorded_on"] == this_platform()


@pytest.mark.parametrize("design", PINNED_DESIGNS)
def test_a_pinned_design_gives_its_recorded_verdicts(stream, design: str) -> None:
    golden = load_golden(design)
    assert golden["stream_sha256"] == stream_digest(stream), "the fixture itself changed"
    observed, snapshot = verdicts(golden_config(design), stream)
    got = [verdict_row(v) for v in observed]
    assert len(got) == golden["messages"]
    for index, (now, then) in enumerate(zip(got, golden["verdicts"], strict=True)):
        assert now == then, f"{design}: verdict {index} ({stream[index]}) changed"
    assert snapshot == golden["snapshot_sha256"], f"{design}: what the engine learned changed"
    if _same_platform(golden):
        assert exact_digest(observed) == golden["exact_sha256"], f"{design}: not bit-identical"


@pytest.mark.parametrize("design", PINNED_DESIGNS)
def test_a_pinned_design_gives_its_recorded_verdicts_after_a_restart(stream, design: str) -> None:
    golden = load_golden(design)["restore"]
    assert golden["at"] == restore_index(stream)
    after = restarted(golden_config(design), stream)
    for index, (now, then) in enumerate(
        zip([verdict_row(v) for v in after], golden["verdicts"], strict=True)
    ):
        assert now == then, f"{design}: verdict {golden['at'] + index} after the restart changed"
    if _same_platform(load_golden(design)):
        assert exact_digest(after) == golden["exact_sha256"], f"{design}: not bit-identical"


@pytest.mark.parametrize("design", PINNED_DESIGNS)
def test_the_exact_pin_was_recorded_here_or_is_skipped(design: str) -> None:
    golden = load_golden(design)
    if not _same_platform(golden):
        pytest.skip(f"exact digests recorded on {golden['recorded_on']}, not {this_platform()}")
    assert golden["exact_sha256"] and golden["restore"]["exact_sha256"]
