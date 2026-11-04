"""DEP-3 (core): a snapshot at the route rollover plus a log-tail replay restores a route.

The traffic is the INF-3 golden log (``golden/github.jsonl``): five days of synthetic callers
with sessions, sessionless bot calls, a burst and a sweep, recorded by the gateway itself.
Every number here is a development-world check, not a paper number. Callers are told apart by
their agent key (``behaviour_fields``), never by a user id: deployments have none (D5).

A simulated live gateway (:class:`_Live`) writes that traffic through ``MessageLog``, scores
each line as the proxy does, logs its own decisions, and snapshots at each route rollover.
It is then killed mid-write, leaving a torn line. The restarted scorer must hold the state of
a clean replay of the same log, and after it goes on, every decision it logged must be
reproduced by an offline re-score of the whole log. An edited, inserted or deleted line after
the snapshot must be caught by the hash chain, as ``log_file verify`` catches it. A snapshot
taken under another scorer profile, or one that is malformed, is refused with a
``ReplayError``, before the scorer changes where the module promises it.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine
from mcp_security.behaviour.engine import replace_config
from mcp_security.behaviour.policy import config_to_json
from mcp_security.gateway import score, state_replay
from mcp_security.gateway.config import Upstream
from mcp_security.gateway.framework import RouteScorer, behaviour_fields, load_artifacts
from mcp_security.gateway.log_file import (
    CHAIN_FIELD,
    V1_KEYS,
    MessageLog,
    last_line,
    line_digest,
    read_log,
    verify_chain,
)
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.state_replay import (
    CALL,
    EVENTS,
    OTHER,
    SESSION_OPENED,
    SNAPSHOT_FORMAT,
    AnchorMismatch,
    ChainBroken,
    LogAnchor,
    ProfileMismatch,
    ReplayError,
    ReplayFailed,
    RolloverSnapshots,
    SnapshotError,
    apply_record,
    event_kind,
    log_anchor,
    read_snapshot,
    replay_log,
    restore_route,
    take_snapshot,
    write_snapshot,
)
from mcp_security.gateway.wire_log import (
    BEHAVIOUR_FOLD,
    CALL_METHOD,
    FLAG_SURGE,
    FROM_GATEWAY,
    INIT_METHOD,
    POLICY_SWITCHED,
    SCHEMA,
    TO_AGENT,
    TO_SERVER,
    Exchange,
    SessionBook,
    build_record,
    requests_in,
)
from tests.gateway.golden_log import (
    BREADTH_NAME,
    GOLDEN_DIR,
    KIND,
    LOG_NAME,
    POLICY,
    POLICY_NAME,
    ROUTE,
    SCAN_NAME,
    START,
)

DAY_S, HOUR_S = 86_400.0, 3_600.0
KILL_AT_S = START + 3.5 * DAY_S  # the kill: midday on the fourth day, after three rollovers
TIMING = "score_us"
GOLDEN_POLICY = GOLDEN_DIR / POLICY_NAME
GOLDEN_LOG = GOLDEN_DIR / LOG_NAME
LOG_FILE = f"{ROUTE}.jsonl"
#: The golden policy's explicit settings, carried into the v5 policy the same tests run on.
GOLDEN_SETTINGS = (
    "warmup_calls",
    "burst_per_minute",
    "request_limit_bytes",
    "request_limit_by_tool",
    "many_assets_per_hour",
    "requires_before",
)
DECISION_KEYS = (
    "schema",
    "ts",
    "gateway.route",
    "gateway.exchange_id",
    "gateway.agent_id",
    "gateway.agent",
    "mcp.session.id",
    "jsonrpc.request.id",
)
V1_NAMES = {new: old for old, new in V1_KEYS.items()}  # gateway-log/3 key -> its v1 name


# ── fixtures and the simulated gateway ────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def golden_records() -> list[dict]:
    """The golden log's records, unchained (the simulated gateway chains its own lines)."""
    records = read_log(GOLDEN_LOG)
    return [{k: v for k, v in r.items() if k != CHAIN_FIELD} for r in records]


@pytest.fixture(params=["v4", "v5"])
def policy(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """The route's behaviour policy file: the golden v4 one, or the same settings in v5."""
    return GOLDEN_POLICY if request.param == "v4" else _v5_policy(tmp_path)


def _v5_policy(directory: Path, name: str = "behaviour_policy_v5.json", **overrides) -> Path:
    """A v5 behaviour policy with the golden policy's settings, plus ``overrides``."""
    settings = {n: getattr(POLICY, n) for n in GOLDEN_SETTINGS} | overrides
    path = directory / name
    path.write_text(json.dumps(config_to_json(BehaviourConfig(design="v5", **settings))))
    return path


def _scorer(policy: Path, scan: Path = GOLDEN_DIR / SCAN_NAME, **options) -> RouteScorer:
    """The golden route's scorer; ``options`` go to ``RouteScorer`` (history, upstream...)."""
    artifacts = load_artifacts(
        ROUTE, str(scan), str(GOLDEN_DIR / BREADTH_NAME), None, KIND, str(policy)
    )
    return RouteScorer(options.pop("route", ROUTE), artifacts, **options)


def _state(scorer: RouteScorer) -> str:
    """The scorer's whole state, canonical, so two states compare as text."""
    return json.dumps(scorer.state(), sort_keys=True)


def _untimed(decision: dict) -> dict:
    return {k: v for k, v in decision.items() if k != TIMING}


def _kill_index(records: list[dict]) -> int:
    """The first scorer event at or after the kill time."""
    return next(
        i for i, r in enumerate(records) if r["ts"] >= KILL_AT_S and event_kind(r) in EVENTS
    )


def _lines(path: Path) -> list[bytes]:
    return path.read_bytes().splitlines()


def _numbered_right(path: Path, anchor: LogAnchor) -> bool:
    """Whether ``anchor`` gives its line the number ``log_file verify`` gives it."""
    lines = path.read_bytes().split(b"\n")
    offset = sum(len(line) + 1 for line in lines[: anchor.line - 1])
    digest = line_digest(lines[anchor.line - 1].rstrip(b"\r"))
    return offset == anchor.offset and digest == anchor.sha256


class _Live:
    """The live gateway's order of work, without HTTP: snapshot at a rollover, log the line,
    score it, log the decision. Decision lines in the input are dropped: it writes its own."""

    def __init__(self, log_dir: Path, scorer: RouteScorer, keeper: RolloverSnapshots) -> None:
        self.log, self.path = MessageLog(log_dir), log_dir / LOG_FILE
        self.scorer, self.keeper = scorer, keeper
        self.decisions: list[dict] = []
        self.snapshots = 0

    def feed(self, record: dict) -> None:
        if "gateway.decision" in record:
            return
        kind, ts = event_kind(record), record["ts"]
        if kind in EVENTS:
            if self.keeper.crossed(ts):
                self.keeper.take(self.scorer, self.keeper.anchor())
                self.snapshots += 1
            self.keeper.seen(ts)
        self.log.write(ROUTE, record)
        decision = apply_record(self.scorer, record)
        if kind == CALL:
            self.decisions.append(decision)
            digests = self.scorer.artifacts.digests
            self.log.write(ROUTE, _decision_line(record, decision, digests))

    def kill(self, record: dict) -> int:
        """Die while writing ``record``: half its line reaches the file. Its line number."""
        self.log.close()
        last, _ = last_line(self.path)
        line = json.dumps({**record, CHAIN_FIELD: line_digest(last)}, ensure_ascii=False)
        torn_at = len(_lines(self.path)) + 1
        with self.path.open("ab") as handle:
            handle.write(line.encode()[: len(line) // 2])
        return torn_at

    def close(self) -> None:
        self.log.close()


def _decision_line(request: dict, decision: dict, digests: dict) -> dict:
    """The decision line the proxy writes after scoring ``request`` (``decision_record``)."""
    tool = (request["message"].get("params") or {}).get("name")
    return {
        **{k: request[k] for k in DECISION_KEYS if k in request},
        "gateway.direction": FROM_GATEWAY,
        "mcp.method.name": CALL_METHOD,
        "gen_ai.tool.name": tool,
        "gateway.decision": {**decision, "artifacts": digests},
    }


def _run_live(records: list[dict], log_dir: Path, scorer: RouteScorer, keeper_path: Path) -> _Live:
    keeper = RolloverSnapshots.for_scorer(scorer, keeper_path, log_path=log_dir / LOG_FILE)
    live = _Live(log_dir, scorer, keeper)
    for record in records:
        live.feed(record)
    return live


def _write_log(directory: Path, records: list[dict]) -> Path:
    """``records`` written as the gateway writes them (chained); the log's path."""
    log = MessageLog(directory)
    for record in records:
        log.write(ROUTE, record)
    log.close()
    return directory / LOG_FILE


# ── restart equals a clean run ────────────────────────────────────────────────────────────


def test_restart_after_a_kill_equals_a_clean_run(
    golden_records: list[dict], policy: Path, tmp_path: Path
) -> None:
    logs, snap_path = tmp_path / "logs", tmp_path / "state" / f"{ROUTE}.snapshot.json"
    log_path = logs / LOG_FILE
    kill = _kill_index(golden_records)
    live = _run_live(golden_records[:kill], logs, _scorer(policy), snap_path)
    torn_at = live.kill(golden_records[kill])
    keeper = RolloverSnapshots.for_scorer(live.scorer, snap_path)
    days = {keeper.day(r["ts"]) for r in golden_records[:kill] if event_kind(r) in EVENTS}
    assert live.snapshots == len(days) - 1 >= 3  # one per rollover before the kill

    snapshot = read_snapshot(snap_path)
    assert snapshot.day == keeper.day(golden_records[kill]["ts"]) - 1  # the day before the kill
    assert snapshot.design == live.scorer.behaviour.config.design
    assert _numbered_right(log_path, snapshot.anchor)  # counted on from the last anchor

    restarted = _scorer(policy)
    report = restore_route(restarted, log_path, snap_path)
    assert report.snapshot == snap_path and report.first_line == snapshot.anchor.line + 1
    assert report.torn == (torn_at,) and report.broken == () and report.errors == ()
    assert report.checked > 0 and report.differing == ()  # the tail's logged decisions hold
    assert report.end == log_anchor(log_path) and report.end.line == torn_at
    at_kill = _scorer(policy)
    replay_log(at_kill, log_path)
    assert _state(restarted) == _state(at_kill)

    resumed = RolloverSnapshots.for_scorer(
        restarted, snap_path, report.last_ts, log_path=log_path, base=report.end
    )
    after = _Live(logs, restarted, resumed)
    for record in golden_records[kill + 1 :]:
        after.feed(record)
    after.close()
    assert after.snapshots >= 1 and _numbered_right(log_path, read_snapshot(snap_path).anchor)

    clean = _scorer(policy)
    offline = replay_log(clean, log_path, keep_calls=True)
    logged = live.decisions + after.decisions
    assert offline.torn == (torn_at,) and offline.differing == ()
    assert offline.checked == len(logged)  # every decision the gateway logged was re-checked
    assert [_untimed(c.decision) for c in offline.calls] == [_untimed(d) for d in logged]
    assert _state(restarted) == _state(clean)
    assert verify_chain(log_path) == [torn_at]  # the restart chained on from the torn line


def test_replay_makes_the_calls_score_py_makes(policy: Path) -> None:
    """A full replay of the golden log gives the rows ``score.py`` gives and ends in the state
    ``score.py``'s scorer ends in. ``score.py`` observes the other requests on its own, so a
    replay that skipped them would end elsewhere. With the policy the log was recorded with,
    every decision the gateway logged is also reproduced."""
    replayed = _scorer(policy)
    report = replay_log(replayed, GOLDEN_LOG, keep_calls=True)
    records = read_log(GOLDEN_LOG)
    offline = _scorer(policy)
    rows = score.score_calls(score.pair_calls(records), offline, records)
    scored = [row for row in rows if TIMING in row]
    assert len(report.calls) == len(scored) > 0
    for call, row in zip(report.calls, scored, strict=True):
        assert {k: row[k] for k in _untimed(call.decision)} == _untimed(call.decision)
    last_call = max(i for i, r in enumerate(records) if event_kind(r) == CALL)
    assert not [r for r in records[last_call + 1 :] if event_kind(r) in EVENTS]  # where it stops
    assert _state(replayed) == _state(offline)
    recorded_with = policy == GOLDEN_POLICY  # else the logged decisions name other artifacts
    assert report.checked == (len(scored) if recorded_with else 0) and report.differing == ()


def test_a_missing_snapshot_replays_the_whole_log(tmp_path: Path) -> None:
    restarted, clean = _scorer(GOLDEN_POLICY), _scorer(GOLDEN_POLICY)
    report = restore_route(restarted, GOLDEN_LOG, tmp_path / "none.json")
    replay_log(clean, GOLDEN_LOG)
    assert report.snapshot is None and report.first_line == 1
    assert _state(restarted) == _state(clean) != _state(_scorer(GOLDEN_POLICY))
    nothing = restore_route(_scorer(GOLDEN_POLICY), tmp_path / "no.jsonl", tmp_path / "none.json")
    assert nothing.events == 0 and nothing.last_ts is None and nothing.end is None


def test_a_restore_with_nothing_after_the_snapshot_keeps_its_clock(tmp_path: Path) -> None:
    """A snapshot of the log's last line: nothing to replay, and the keeper resumes from the
    snapshot's newest event."""
    scorer = _scorer(GOLDEN_POLICY)
    replay_log(scorer, GOLDEN_LOG)
    anchor, snap_path = log_anchor(GOLDEN_LOG), tmp_path / "snapshot.json"
    write_snapshot(snap_path, take_snapshot(scorer, anchor, 1_780_600_000.0))
    restarted = _scorer(GOLDEN_POLICY)
    report = restore_route(restarted, GOLDEN_LOG, snap_path)
    assert (report.lines, report.events, report.last_ts) == (0, 0, 1_780_600_000.0)
    assert report.end == anchor and report.first_line == anchor.line + 1
    assert _state(restarted) == _state(scorer)


def test_a_snapshot_missing_state_is_reported_not_hidden(
    golden_records: list[dict], tmp_path: Path
) -> None:
    """A snapshot that lost what the route learned replays the tail to other decisions than
    the gateway logged; the report names those lines."""
    logs, snap_path = tmp_path / "logs", tmp_path / "snapshot.json"
    kill = _kill_index(golden_records)
    _run_live(golden_records[:kill], logs, _scorer(GOLDEN_POLICY), snap_path).close()
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    data["state"] = _scorer(GOLDEN_POLICY).state()  # as if nothing had been learned
    snap_path.write_text(json.dumps(data), encoding="utf-8")
    report = restore_route(_scorer(GOLDEN_POLICY), logs / LOG_FILE, snap_path)
    lines = _lines(logs / LOG_FILE)
    assert report.differing
    assert all(b'"gateway.decision"' in lines[n - 1] for n in report.differing)
    assert all(n >= report.first_line for n in report.differing)


# ── a session open across the snapshot (J1 owns the gap) ──────────────────────────────────


def _rollover_inside_a_session(records: list[dict]) -> tuple[float, float, float]:
    """The first agent session with two calls on the fourth day (agents are told apart by
    ``behaviour_fields``, D5): the hour between its first two calls, and those two times."""
    day3 = START + 3 * DAY_S
    sessions: dict[tuple, list[float]] = {}
    for record in records:
        if event_kind(record) == CALL and record["ts"] >= day3:
            fields = behaviour_fields(record)
            if fields["session"]:
                sessions.setdefault((fields["caller"], fields["session"]), []).append(record["ts"])
    first, second = next(times[:2] for times in sessions.values() if len(times) >= 2)
    return ((first + second) / 2 - day3) / HOUR_S, first, second


def _live_with_the_rollover_in_a_session(
    records: list[dict], policy: Path, directory: Path
) -> tuple[_Live, Path, Path]:
    """The live gateway up to the kill time, its snapshots taken at an hour that falls inside
    an agent's session; the live gateway, its log and its snapshot."""
    logs, snap_path = directory / "logs", directory / "snapshot.json"
    hour, first, second = _rollover_inside_a_session(records)
    keeper = RolloverSnapshots(snap_path, "UTC", hour, log_path=logs / LOG_FILE)
    live = _Live(logs, _scorer(policy), keeper)
    for record in records[: _kill_index(records)]:
        live.feed(record)
    live.close()
    assert first <= read_snapshot(snap_path).last_ts < second  # the snapshot fell inside it
    return live, logs / LOG_FILE, snap_path


def test_a_session_open_across_the_snapshot_is_reported(
    golden_records: list[dict], tmp_path: Path
) -> None:
    """The behaviour engine's snapshot leaves open sessions out (J1 adds them). Whatever the
    restart gets wrong, the report names exactly the decisions that differ from a clean run,
    and no other."""
    _, log_path, snap_path = _live_with_the_rollover_in_a_session(
        golden_records, GOLDEN_POLICY, tmp_path
    )
    report = restore_route(_scorer(GOLDEN_POLICY), log_path, snap_path, keep_calls=True)
    clean = {
        c.line: c.decision
        for c in replay_log(_scorer(GOLDEN_POLICY), log_path, keep_calls=True).calls
    }
    # _Live logs each decision on the line after its request
    unequal = {c.line + 1 for c in report.calls if _untimed(c.decision) != _untimed(clean[c.line])}
    assert report.checked == len(report.calls) > 0
    assert set(report.differing) == unequal


@pytest.mark.xfail(strict=True, reason="J1: BehaviourEngine.snapshot leaves open sessions out")
def test_a_session_open_across_the_snapshot_restarts_exactly(
    golden_records: list[dict], policy: Path, tmp_path: Path
) -> None:
    """The restart must equal a run that never stopped, also inside an open session. Today
    the agent's next calls get a Missing handshake flag after the restart; this test passes,
    and so fails as an unexpected pass, once J1 carries open sessions in the snapshot."""
    live, log_path, snap_path = _live_with_the_rollover_in_a_session(
        golden_records, policy, tmp_path
    )
    restarted = _scorer(policy)
    report = restore_route(restarted, log_path, snap_path)
    resumed = RolloverSnapshots.for_scorer(
        restarted, tmp_path / "next.json", report.last_ts, log_path=log_path, base=report.end
    )
    after = _Live(log_path.parent, restarted, resumed)
    for record in golden_records[_kill_index(golden_records) :]:
        after.feed(record)
    after.close()
    clean = _scorer(policy)
    offline = replay_log(clean, log_path, keep_calls=True)
    logged = live.decisions + after.decisions
    assert report.differing == ()
    assert [_untimed(c.decision) for c in offline.calls] == [_untimed(d) for d in logged]
    assert _state(restarted) == _state(clean)


# ── the calls the replay makes ────────────────────────────────────────────────────────────


def _line(ts: float, direction: str, method: str | None = None, **fields: object) -> dict:
    """A minimal gateway-log/3 line from one agent."""
    record = {
        "schema": SCHEMA,
        "ts": ts,
        "gateway.route": ROUTE,
        "gateway.direction": direction,
        "gateway.agent_id": "agent-1",
        "gateway.exchange_id": f"x{ts:g}",
        **fields,
    }
    return record | ({"mcp.method.name": method} if method else {})


def _spy(scorer: RouteScorer, monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, object]]:
    """Record every scorer call the replay makes, with what tells it apart."""
    made: list[tuple[str, object]] = []
    labels: dict[str, Callable[..., object]] = {
        "observe": lambda method, *_, **__: method,
        "session_initialized": lambda caller, session, *_, **__: session,
        "score": lambda tool, *_, **__: tool,
        "apply_notice": lambda record: record["gateway.notice"],
    }
    for name, label in labels.items():
        real = getattr(scorer, name)

        def spy(*args, _name=name, _real=real, _label=label, **kwargs):
            made.append((_name, _label(*args, **kwargs)))
            return _real(*args, **kwargs)

        monkeypatch.setattr(scorer, name, spy)
    return made


def test_the_replay_makes_the_live_calls_in_log_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Requests are observed, the reply that opened a session marks it, calls are scored and
    LOG-1 folds and policy switches are applied, each in log order. A surge notice changes
    nothing, and nor does a bodiless reply that names initialize."""
    initialize = {"jsonrpc": "2.0", "id": 1, "method": INIT_METHOD, "params": {}}
    call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": CALL_METHOD,
        "params": {"name": "get_file_contents", "arguments": {"owner": "acme", "repo": "repo-a"}},
    }
    records = [
        _line(1.0, TO_SERVER, INIT_METHOD, message=initialize),
        _line(2.0, TO_AGENT, INIT_METHOD, **{"mcp.session.id": "s1", "gateway.message_bytes": 40}),
        _line(3.0, TO_SERVER, "tools/list", **{"mcp.session.id": "s1"}),
        _line(4.0, FROM_GATEWAY, **{"gateway.notice": BEHAVIOUR_FOLD}),
        _line(5.0, TO_SERVER, CALL_METHOD, message=call, **{"mcp.session.id": "s1"}),
        _line(6.0, FROM_GATEWAY, **{"gateway.notice": FLAG_SURGE}),
        _line(7.0, FROM_GATEWAY, **{"gateway.notice": POLICY_SWITCHED}),
        _line(8.0, TO_AGENT, INIT_METHOD, **{"mcp.session.id": "s2", "gateway.message_bytes": 0}),
    ]
    scorer = _scorer(GOLDEN_POLICY)
    made = _spy(scorer, monkeypatch)
    report = replay_log(scorer, _write_log(tmp_path, records))
    assert made == [
        ("observe", INIT_METHOD),
        ("session_initialized", "s1"),
        ("observe", "tools/list"),
        ("apply_notice", BEHAVIOUR_FOLD),
        ("score", "get_file_contents"),
        ("apply_notice", POLICY_SWITCHED),
    ]
    assert (report.lines, report.events, report.last_ts) == (len(records), len(made), 7.0)


def test_a_bodiless_reply_to_initialize_opens_no_session() -> None:
    """The proxy reads the session ``initialize`` opened only from a reply that carried a
    message (``_answered``). A bodiless reply line still names initialize when the agent sent
    it with ``"id": null``: the replay must not open a session the live gateway never saw."""
    request = {"jsonrpc": "2.0", "id": None, "method": INIT_METHOD, "params": {}}
    exchange = Exchange(
        route=ROUTE,
        agent="agent",
        session="s-1",
        http_method="POST",
        agent_id="agent-1",
        requests=requests_in([request]),
    )
    book = SessionBook()
    bodiless = build_record(exchange, book, TO_AGENT, 202, None)
    assert bodiless["mcp.method.name"] == INIT_METHOD and bodiless["mcp.session.id"]
    assert event_kind(bodiless) == OTHER
    reply = {"jsonrpc": "2.0", "id": None, "result": {"protocolVersion": "2025-06-18"}}
    answered = build_record(exchange, book, TO_AGENT, 200, reply)
    assert event_kind(answered) == SESSION_OPENED
    body_not_kept = {k: v for k, v in answered.items() if k != "message"}  # log_bodies
    assert event_kind(body_not_kept) == SESSION_OPENED


def test_a_v1_log_replays_as_score_py_reads_it(golden_records: list[dict], tmp_path: Path) -> None:
    """Lines written before ``schema`` used other key names; the replay renames them as
    ``read_log`` does, so it scores a v1 log as ``score.py`` does."""
    v1 = [{V1_NAMES.get(k, k): v for k, v in r.items() if k != "schema"} for r in golden_records]
    assert all(r.get("gateway.direction") is None for r in v1)  # the names really are v1's
    log_path = _write_log(tmp_path, v1)
    replayed = _scorer(GOLDEN_POLICY)
    report = replay_log(replayed, log_path, keep_calls=True)
    records = read_log(log_path)
    offline = _scorer(GOLDEN_POLICY)
    rows = [
        r for r in score.score_calls(score.pair_calls(records), offline, records) if TIMING in r
    ]
    assert report.events == sum(event_kind(r) in EVENTS for r in records) > 0
    assert [_untimed(c.decision) for c in report.calls] == [
        {k: row[k] for k in _untimed(c.decision)} for c, row in zip(report.calls, rows, strict=True)
    ]
    assert report.checked == len(rows) and report.differing == ()
    assert _state(replayed) == _state(offline)


def test_repeated_request_ids_pair_with_their_decisions_in_order(
    golden_records: list[dict], tmp_path: Path
) -> None:
    """A batch can repeat a request id, and background scoring logs both decisions after both
    requests: each decision still pairs with its own call."""
    tools = ("get_file_contents", "merge_pull_request")
    batch = [
        {**r, "gateway.exchange_id": "batch", "jsonrpc.request.id": "7"}
        for r in (next(r for r in golden_records if _call_of(r) == tool) for tool in tools)
    ]
    live = _scorer(GOLDEN_POLICY)
    decisions = [apply_record(live, request) for request in batch]
    assert _untimed(decisions[0]) != _untimed(decisions[1])  # a mis-pairing would show
    digests = live.artifacts.digests
    lines = batch + [_decision_line(r, d, digests) for r, d in zip(batch, decisions, strict=True)]
    report = replay_log(_scorer(GOLDEN_POLICY), _write_log(tmp_path, lines))
    assert report.checked == 2 and report.differing == ()


def _call_of(record: dict) -> str | None:
    """The tool of a scored tools/call line, else None."""
    return record["message"]["params"]["name"] if event_kind(record) == CALL else None


# ── the hash chain ────────────────────────────────────────────────────────────────────────


def _edit(lines: list[bytes], at: int) -> list[bytes]:
    record = json.loads(lines[at])
    record["gateway.agent"] = "mallory"  # the chain field is kept: only a value changes
    return lines[:at] + [json.dumps(record, ensure_ascii=False).encode()] + lines[at + 1 :]


def _delete(lines: list[bytes], at: int) -> list[bytes]:
    return lines[:at] + lines[at + 1 :]


def _insert(lines: list[bytes], at: int) -> list[bytes]:
    forged = {**json.loads(lines[at]), CHAIN_FIELD: line_digest(lines[at - 1])}
    return lines[:at] + [json.dumps(forged, ensure_ascii=False).encode()] + lines[at:]


#: (tamper, where the chain breaks, counted in lines from the tampered one's index): an
#: edited line breaks at the line after it; after a deleted line, the line that moved up; an
#: inserted copy chains correctly, so the original line after it breaks.
TAMPERS = [(_edit, 2), (_delete, 1), (_insert, 2)]


def _live_until_the_kill(records: list[dict], directory: Path, **options) -> tuple[Path, Path]:
    """The live gateway up to the kill time with the golden v4 policy: its log and snapshot."""
    logs, snap_path = directory / "logs", directory / "snapshot.json"
    scorer = _scorer(GOLDEN_POLICY, **options)
    _run_live(records[: _kill_index(records)], logs, scorer, snap_path).close()
    return logs / LOG_FILE, snap_path


@pytest.mark.parametrize(("tamper", "breaks_at"), TAMPERS, ids=["edit", "delete", "insert"])
def test_a_tampered_tail_line_is_caught_by_the_chain(
    golden_records: list[dict], tmp_path: Path, tamper, breaks_at: int
) -> None:
    log_path, snap_path = _live_until_the_kill(golden_records, tmp_path)
    anchor = read_snapshot(snap_path).anchor
    lines = _lines(log_path)
    at = anchor.line + 1  # the second line after the snapshot's, as an index
    log_path.write_bytes(b"\n".join(tamper(lines, at)) + b"\n")

    named = tuple(verify_chain(log_path))
    assert named == (at + breaks_at,)  # log_file verify names it
    scorer = _scorer(GOLDEN_POLICY)
    with pytest.raises(ChainBroken) as caught:
        restore_route(scorer, log_path, snap_path)
    assert caught.value.lines == named
    assert _state(scorer) == _state(_scorer(GOLDEN_POLICY))  # nothing was loaded
    lenient = restore_route(_scorer(GOLDEN_POLICY), log_path, snap_path, strict=False)
    assert lenient.broken == named


def test_an_edited_snapshot_line_is_refused(golden_records: list[dict], tmp_path: Path) -> None:
    log_path, snap_path = _live_until_the_kill(golden_records, tmp_path)
    anchor = read_snapshot(snap_path).anchor
    data = log_path.read_bytes()
    log_path.write_bytes(data[: anchor.offset] + data[anchor.offset :].replace(b"{", b"{ ", 1))
    with pytest.raises(AnchorMismatch, match=f"line {anchor.line} "):
        restore_route(_scorer(GOLDEN_POLICY), log_path, snap_path)
    log_path.write_bytes(data[: anchor.offset])  # cut before the anchor
    with pytest.raises(AnchorMismatch):
        restore_route(_scorer(GOLDEN_POLICY), log_path, snap_path)
    log_path.unlink()
    with pytest.raises(AnchorMismatch):
        restore_route(_scorer(GOLDEN_POLICY), log_path, snap_path)


# ── what a snapshot must match ────────────────────────────────────────────────────────────


def _rescanned(directory: Path) -> Path:
    """The golden scan, byte for byte another file: the same cells under another digest."""
    path = directory / "scan.json"
    path.write_text((GOLDEN_DIR / SCAN_NAME).read_text(encoding="utf-8") + "\n")
    return path


def _other_zone(directory: Path) -> RouteScorer:
    """A v5 scorer whose route overrides the policy's zone (B9d): the same artifacts, another
    behaviour config in effect."""
    scorer = _scorer(_v5_policy(directory))
    scorer.behaviour = BehaviourEngine(
        replace_config(scorer.behaviour.config, route_zone="Europe/Berlin")
    )
    return scorer


def _upstream(**fields: object) -> Upstream:
    return Upstream(name=ROUTE, url="http://upstream.invalid/mcp", **fields)


class _NoReads:
    """An E14 read ledger that remembers nothing (``framework.ReadLedger``)."""

    def note_read(self, *args: object, **kwargs: object) -> None:
        """Forget the read."""

    def reads_since(self, caller: str, since: float) -> list:
        """No read was kept."""
        return []


#: name -> (the scorer that took the snapshot, the scorer restoring it, the fields that differ)
PROFILE_CASES: dict[
    str, tuple[Callable[[Path], RouteScorer], Callable[[Path], RouteScorer], tuple[str, ...]]
] = {
    "scan": (
        lambda d: _scorer(GOLDEN_POLICY),
        lambda d: _scorer(GOLDEN_POLICY, scan=_rescanned(d)),
        ("artifacts",),
    ),
    "route": (
        lambda d: _scorer(GOLDEN_POLICY),
        lambda d: _scorer(GOLDEN_POLICY, route="github-mirror"),
        ("route",),
    ),
    "history": (
        lambda d: _scorer(GOLDEN_POLICY, history="caller"),
        lambda d: _scorer(GOLDEN_POLICY),
        ("history",),
    ),
    "behaviour config": (
        lambda d: _scorer(_v5_policy(d)),
        _other_zone,
        ("behaviour_config",),
    ),
    "baseline key": (
        lambda d: _scorer(GOLDEN_POLICY, upstream=_upstream(baseline_key="user")),
        lambda d: _scorer(GOLDEN_POLICY, upstream=_upstream()),
        ("inputs",),
    ),
    "pseudonym key": (
        lambda d: _scorer(GOLDEN_POLICY, pseudonymizer=Pseudonymizer(b"key-one")),
        lambda d: _scorer(GOLDEN_POLICY, pseudonymizer=Pseudonymizer(b"key-two")),
        ("inputs",),
    ),
    "read ledger": (
        lambda d: _scorer(GOLDEN_POLICY, ledger=_NoReads()),
        lambda d: _scorer(GOLDEN_POLICY),
        ("inputs",),
    ),
}


@pytest.mark.parametrize("case", list(PROFILE_CASES))
def test_a_snapshot_under_another_profile_is_refused(case: str, tmp_path: Path) -> None:
    """A state learned under another route, history, scan, behaviour config or routes.json
    input is not the state an offline re-score with this scorer reaches: the restore refuses
    it and loads nothing."""
    took, restores, fields = PROFILE_CASES[case]
    learned = took(tmp_path)
    replay_log(learned, GOLDEN_LOG)
    path = tmp_path / "snapshot.json"
    write_snapshot(path, take_snapshot(learned, None, None))
    scorer = restores(tmp_path)
    fresh = _state(scorer)
    with pytest.raises(ProfileMismatch) as caught:
        restore_route(scorer, GOLDEN_LOG, path)
    assert caught.value.fields == fields
    assert _state(scorer) == fresh


def test_a_snapshot_of_another_design_or_state_layout_is_refused(tmp_path: Path) -> None:
    v4 = _scorer(GOLDEN_POLICY)
    replay_log(v4, GOLDEN_LOG)
    path = tmp_path / "snapshot.json"
    write_snapshot(path, take_snapshot(v4, None, None))
    with pytest.raises(ProfileMismatch, match="design") as caught:
        restore_route(_scorer(_v5_policy(tmp_path)), GOLDEN_LOG, path)
    assert "design" in caught.value.fields
    data = json.loads(path.read_text(encoding="utf-8"))
    data["profile"]["state_layout"]["behaviour"].append("sessions")  # code with another layout
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProfileMismatch) as caught:
        restore_route(_scorer(GOLDEN_POLICY), GOLDEN_LOG, path)
    assert caught.value.fields == ("state_layout",)


# ── malformed snapshots and failing lines: always a ReplayError ───────────────────────────


#: name -> how a valid snapshot file is spoilt; each is refused before the scorer changes
SPOILT = {
    "state is a list": lambda d: d | {"state": []},
    "state is a string": lambda d: d | {"state": "x"},
    "last_ts is text": lambda d: d | {"last_ts": "yesterday"},
    "last_ts is a bool": lambda d: d | {"last_ts": True},
    "last_ts is not finite": lambda d: d | {"last_ts": float("nan")},
    "unknown zone": lambda d: d | {"zone": "Mars/Olympus"},
    "hour out of range": lambda d: d | {"day_start_hour": 25},
    "negative anchor": lambda d: d | {"anchor": {"offset": -1, "sha256": "ab", "line": 1}},
    "line zero": lambda d: d | {"anchor": {"offset": 0, "sha256": "ab", "line": 0}},
    "anchor is text": lambda d: d | {"anchor": "line 12"},
    "profile without a route": lambda d: d | {"profile": {"design": "v4"}},
    "no state": lambda d: {k: v for k, v in d.items() if k != "state"},
    "format 1": lambda d: d | {"format": "gateway-state-snapshot/1"},
}


@pytest.mark.parametrize("spoil", list(SPOILT))
def test_a_malformed_snapshot_is_refused_before_the_scorer_changes(
    spoil: str, tmp_path: Path
) -> None:
    scorer = _scorer(GOLDEN_POLICY)
    replay_log(scorer, GOLDEN_LOG)
    path = tmp_path / "snapshot.json"
    write_snapshot(path, take_snapshot(scorer, log_anchor(GOLDEN_LOG), 1_780_600_000.0))
    data = SPOILT[spoil](json.loads(path.read_text(encoding="utf-8")))
    path.write_text(json.dumps(data), encoding="utf-8")
    restarted = _scorer(GOLDEN_POLICY)
    fresh = _state(restarted)
    with pytest.raises(SnapshotError):
        restore_route(restarted, GOLDEN_LOG, path)
    assert _state(restarted) == fresh


def test_a_state_that_does_not_load_is_a_snapshot_error(tmp_path: Path) -> None:
    """A snapshot whose state an engine cannot load (an agent without his fields, as after
    an engine upgrade that added some) is a ``SnapshotError`` naming the cause."""
    scorer = _scorer(GOLDEN_POLICY)
    replay_log(scorer, GOLDEN_LOG)
    path = tmp_path / "snapshot.json"
    write_snapshot(path, take_snapshot(scorer, log_anchor(GOLDEN_LOG), None))
    data = json.loads(path.read_text(encoding="utf-8"))
    data["state"]["behaviour"]["agents"]["agent-without-fields"] = {}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SnapshotError, match="does not load") as caught:
        restore_route(_scorer(GOLDEN_POLICY), GOLDEN_LOG, path)
    assert isinstance(caught.value.__cause__, KeyError)
    unreadable = tmp_path / "a-directory.json"
    unreadable.mkdir()
    with pytest.raises(SnapshotError, match="cannot read"):
        restore_route(_scorer(GOLDEN_POLICY), GOLDEN_LOG, unreadable)


def test_every_restore_error_is_a_replay_error() -> None:
    """The gateway catches ``ReplayError`` alone around a restore and falls back on it."""
    errors = (SnapshotError, ProfileMismatch, AnchorMismatch, ChainBroken, ReplayFailed)
    assert all(issubclass(error, ReplayError) for error in errors)


def test_a_scorer_error_is_reported_and_the_replay_goes_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scorer = _scorer(GOLDEN_POLICY)
    real = scorer.score

    def fails_on_merges(tool: str, *args: object, **kwargs: object) -> dict:
        if tool == "merge_pull_request":
            raise RuntimeError("boom")
        return real(tool, *args, **kwargs)

    monkeypatch.setattr(scorer, "score", fails_on_merges)
    report = replay_log(scorer, GOLDEN_LOG, keep_calls=True)
    merges = [c for c in report.calls if c.tool == "merge_pull_request"]
    assert merges and report.errors == tuple(c.line for c in merges)
    assert all(c.decision == {"error": "RuntimeError: boom"} for c in merges)
    # the gateway logged real decisions for them, on the line after each request
    assert {c.line + 1 for c in merges} <= set(report.differing)

    def no_sessions(*args: object) -> None:
        raise RuntimeError("not caught live either")

    monkeypatch.setattr(scorer, "session_initialized", no_sessions)
    opened = next(
        n for n, r in enumerate(read_log(GOLDEN_LOG), 1) if event_kind(r) == SESSION_OPENED
    )
    with pytest.raises(ReplayFailed, match="not caught live either") as caught:
        replay_log(scorer, GOLDEN_LOG)
    assert caught.value.line == opened and isinstance(caught.value.__cause__, RuntimeError)


def test_a_notice_or_line_the_scorer_cannot_take_fails_with_its_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fold = _line(2.0, FROM_GATEWAY, **{"gateway.notice": BEHAVIOUR_FOLD})
    log_path = _write_log(tmp_path / "fold", [_line(1.0, TO_SERVER, "ping"), fold])
    scorer = _scorer(GOLDEN_POLICY)

    def refuses(record: dict) -> None:
        raise ValueError("references digest differs")

    monkeypatch.setattr(scorer, "apply_notice", refuses)
    with pytest.raises(ReplayFailed, match="references digest differs") as caught:
        replay_log(scorer, log_path)
    assert caught.value.line == 2
    timeless = {k: v for k, v in _line(3.0, TO_SERVER, "ping").items() if k != "ts"}
    log_path = _write_log(tmp_path / "timeless", [_line(1.0, TO_SERVER, "ping"), timeless])
    with pytest.raises(ReplayFailed, match="timestamp") as caught:
        replay_log(_scorer(GOLDEN_POLICY), log_path)
    assert caught.value.line == 2


# ── snapshots, anchors and the route clock ────────────────────────────────────────────────


def test_snapshot_file_round_trip(tmp_path: Path) -> None:
    scorer = _scorer(GOLDEN_POLICY)
    replay_log(scorer, GOLDEN_LOG)
    path = tmp_path / "state" / "snapshot.json"
    anchor = LogAnchor(12, "ab" * 32, 2)
    taken = take_snapshot(scorer, anchor, 1_780_300_000.0, "Europe/Berlin", 4.0)
    write_snapshot(path, taken)
    # the state holds tuples, which JSON gives back as lists: compare the JSON forms
    assert read_snapshot(path).to_json() == json.loads(json.dumps(taken.to_json()))
    assert read_snapshot(path).to_json()["format"] == SNAPSHOT_FORMAT
    assert read_snapshot(path).anchor == anchor and read_snapshot(path).day == taken.day
    assert not list(path.parent.glob("*.partial"))
    loaded = _scorer(GOLDEN_POLICY)
    loaded.load_state(read_snapshot(path).state)
    assert _state(loaded) == _state(scorer)
    for garbage in (b"{not json", b"\xff\xfe binary"):
        path.write_bytes(garbage)
        with pytest.raises(SnapshotError):
            read_snapshot(path)
    path.write_text(json.dumps({"format": "other/1"}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="other/1"):
        read_snapshot(path)


def test_a_failed_write_keeps_the_old_snapshot_and_leaves_no_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scorer, path = _scorer(GOLDEN_POLICY), tmp_path / "snapshot.json"
    write_snapshot(path, take_snapshot(scorer, None, None))
    old = path.read_bytes()
    replay_log(scorer, GOLDEN_LOG)
    newer = take_snapshot(scorer, None, 1_780_600_000.0)

    def disk_full(descriptor: int) -> None:
        raise OSError(28, "No space left on device")

    with monkeypatch.context() as patched:
        patched.setattr(os, "fsync", disk_full)
        with pytest.raises(OSError, match="No space"):
            write_snapshot(path, newer)
    assert path.read_bytes() == old and not list(tmp_path.glob("*.partial"))
    with pytest.raises(TypeError):  # a set is not JSON: nothing is written at all
        write_snapshot(path, replace(newer, state={"agents": {1, 2}}))
    assert path.read_bytes() == old and not list(tmp_path.glob("*.partial"))


def test_a_state_json_would_change_is_never_snapshotted(
    golden_records: list[dict], tmp_path: Path
) -> None:
    """A tools/call named 7 is counted under the int 7 live; JSON would read it back as "7",
    and the restored scorer would count the next such call apart from the first. The
    snapshot is refused instead, and the old one stays (J3 can stop such names earlier)."""
    request = next(r for r in golden_records if event_kind(r) == CALL)
    params = {"name": 7, "arguments": {}}
    odd = {**request, "message": {**request["message"], "params": params}}
    scorer = _scorer(GOLDEN_POLICY)
    keeper = RolloverSnapshots(tmp_path / "snapshot.json")
    keeper.take(scorer, None)
    old = keeper.path.read_bytes()
    apply_record(scorer, odd)
    with pytest.raises(SnapshotError, match="7"):
        keeper.take(scorer, None)
    assert keeper.path.read_bytes() == old


def test_log_anchor_names_the_line_the_next_one_chains_to(tmp_path: Path) -> None:
    path = tmp_path / LOG_FILE
    assert log_anchor(path) is None
    log = MessageLog(tmp_path)
    for i in range(3):
        log.write(ROUTE, {"ts": float(i), "n": i})
    anchor = log_anchor(path)
    log.write(ROUTE, {"ts": 3.0, "n": 3})
    log.close()
    lines = _lines(path)
    assert anchor == LogAnchor(len(lines[0]) + len(lines[1]) + 2, line_digest(lines[2]), 3)
    assert json.loads(lines[3])[CHAIN_FIELD] == anchor.sha256
    later = LogAnchor(anchor.offset + len(lines[2]) + 1, line_digest(lines[3]), 4)
    assert log_anchor(path, base=anchor) == later
    # counted on from the base, not from the start of the log, while the base holds
    assert log_anchor(path, base=replace(anchor, line=10)) == replace(later, line=11)
    stale = replace(anchor, sha256="0" * 64, line=10)  # its line is not there: not trusted
    assert log_anchor(path, base=stale) == later
    torn = b'{"ts": 4.0, "n"'
    with path.open("ab") as handle:  # a torn last line is the anchor as it is
        handle.write(torn)
    expected = LogAnchor(path.stat().st_size - len(torn), line_digest(torn), 5)
    assert log_anchor(path, base=later) == log_anchor(path) == expected
    keeper = RolloverSnapshots(tmp_path / "snapshot.json", log_path=path, base=anchor)
    assert keeper.anchor() == expected and keeper.base == expected
    with pytest.raises(ValueError, match="log_path"):
        RolloverSnapshots(tmp_path / "snapshot.json").anchor()


def _utc(day: int, hour: float) -> float:
    return datetime(2026, 6, 1 + day, tzinfo=timezone.utc).timestamp() + hour * HOUR_S


def test_the_rollover_follows_the_route_clock(tmp_path: Path) -> None:
    v4 = RolloverSnapshots(tmp_path / "s.json")  # midnight UTC
    assert (v4.zone, v4.day_start_hour) == ("UTC", 0.0)
    assert not v4.crossed(_utc(0, 23.9))  # nothing seen yet: nothing to close
    v4.seen(_utc(0, 23.9))
    assert v4.crossed(_utc(1, 0.0))
    v4.seen(_utc(0, 1.0))  # an older event changes nothing
    assert v4.last_ts == _utc(0, 23.9)
    v4_route = RolloverSnapshots.for_scorer(_scorer(GOLDEN_POLICY), tmp_path / "s.json")
    assert (v4_route.zone, v4_route.day_start_hour) == ("UTC", 0.0)

    v5 = RolloverSnapshots.for_scorer(_scorer(_v5_policy(tmp_path)), tmp_path / "s.json")
    assert (v5.zone, v5.day_start_hour) == ("UTC", 4.0)
    v5.seen(_utc(0, 5.0))
    assert not v5.crossed(_utc(1, 3.99))  # 03:59 still belongs to the day before
    assert v5.crossed(_utc(1, 4.0)) and v5.crossed(_utc(3, 12.0))

    new_york = _v5_policy(tmp_path, "new_york.json", route_zone="America/New_York")
    east = RolloverSnapshots.for_scorer(_scorer(new_york), tmp_path / "s.json", _utc(0, 9.0))
    assert (east.zone, east.day_start_hour) == ("America/New_York", 4.0)
    assert not east.crossed(_utc(1, 7.99))  # 03:59 in New York (EDT, UTC-4)
    assert east.crossed(_utc(1, 8.0))
    with pytest.raises(ValueError):
        RolloverSnapshots(tmp_path / "s.json", "Mars/Olympus")


def test_a_queued_snapshot_keeps_the_newest_event_read_when_queued(tmp_path: Path) -> None:
    """Background scoring takes the snapshot later, after newer events were seen: it passes
    the newest event read when it queued it."""
    scorer = _scorer(GOLDEN_POLICY)
    keeper = RolloverSnapshots(tmp_path / "snapshot.json", last_ts=_utc(0, 23.0))
    queued = keeper.last_ts
    keeper.seen(_utc(1, 0.5))  # logged before the queued snapshot runs
    assert keeper.take(scorer, None, queued).last_ts == queued
    assert read_snapshot(keeper.path).day == keeper.day(queued)
    assert keeper.take(scorer, None).last_ts == _utc(1, 0.5)  # inline: the newest seen


@pytest.mark.skipif(os.name != "posix", reason="fsync of a directory is POSIX")
def test_take_makes_the_log_durable_before_the_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A snapshot must never reach past the log on disk: after a power loss, its line would be
    missing and the restore would have to replay the whole log."""
    log_path = _write_log(tmp_path / "logs", [{"ts": 1.0, "n": 1}])
    synced: list[int] = []
    real = os.fsync

    def recorded(descriptor: int) -> None:
        synced.append(os.fstat(descriptor).st_ino)
        real(descriptor)

    monkeypatch.setattr(os, "fsync", recorded)
    keeper = RolloverSnapshots(tmp_path / "snapshot.json", log_path=log_path)
    keeper.take(_scorer(GOLDEN_POLICY), keeper.anchor())
    assert synced[0] == log_path.stat().st_ino
    assert keeper.path.stat().st_ino in synced[1:]  # the snapshot, then its directory entry
    assert synced[-1] == keeper.path.parent.stat().st_ino


# ── what cannot be replayed is counted ────────────────────────────────────────────────────


def test_a_line_written_after_the_chain_check_is_not_replayed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The replay reads only what the chain check covered, even if the log grows between."""
    log_path = _write_log(tmp_path, [_line(1.0, TO_SERVER, "ping")])
    checked = state_replay._check_tail

    def check_then_grow(*args: object) -> object:
        tail = checked(*args)
        with log_path.open("a", encoding="utf-8") as handle:  # unchained: never checked
            handle.write(json.dumps(_line(2.0, TO_SERVER, "ping")) + "\n")
        return tail

    monkeypatch.setattr(state_replay, "_check_tail", check_then_grow)
    report = replay_log(_scorer(GOLDEN_POLICY), log_path)
    assert (report.lines, report.events, report.last_ts) == (1, 1, 1.0)


def test_calls_without_their_arguments_are_counted(
    golden_records: list[dict], tmp_path: Path
) -> None:
    """``log_bodies: none``: a call's arguments are not in the log, so it cannot be scored
    offline (``score.py`` skips it too)."""
    records = [
        {k: v for k, v in r.items() if k != "message"} if event_kind(r) == CALL else r
        for r in golden_records
    ]
    calls = sum(event_kind(r) == CALL for r in golden_records)
    report = replay_log(_scorer(GOLDEN_POLICY), _write_log(tmp_path, records))
    assert report.calls_without_body == calls > 0 and report.checked == 0
