"""DEP-3 (core): a route's learned state survives a restart as a snapshot plus a log-tail replay.

At each route rollover the gateway writes the route scorer's whole state
(``RouteScorer.state``) to one JSON snapshot. The snapshot also names the last log line it
includes: the line's byte offset, its line number and its SHA-256, which is the digest that
the next line's ``gateway.prev_sha256`` carries (``log_file``). On start, :func:`restore_route`
does four things:

1. it loads the snapshot and checks that it was taken under this scorer's profile
   (:func:`scorer_profile`);
2. it checks that the snapshot's line is still where it was;
3. it checks the hash chain from there to the end of the log;
4. it replays every line after it through the ``RouteScorer`` calls that the live gateway
   made when it wrote that line.

The calls, per line:

- a ``tools/call`` request: :meth:`RouteScorer.score`;
- any other request: :meth:`RouteScorer.observe`;
- the reply to ``initialize`` that carried a message and the new session id:
  :meth:`RouteScorer.session_initialized` (the proxy reads a session only from a reply that
  carried a message, ``proxy._answered``);
- a ``behaviour_fold`` or ``policy_switched`` line (LOG-1): :meth:`RouteScorer.apply_notice`.

``score.py`` re-scores a log with the same calls, read from the same fields
(``framework.behaviour_fields``), in the same order. Until J3 aligns it (Batch 2) it differs in
three ways: it stops at the log's last ``tools/call``, it replays no LOG-1 line, and it also
opens a session on a bodiless reply. A restarted gateway therefore holds the state that the
live gateway held, and an offline re-score reaches that state up to the log's last call: live
equals offline after a restart. With no snapshot, the whole log is replayed (the migration
bootstrap's path, DEP-6).

Core scope (spec 2.9, 4.3; plan, Batch 1): one JSON snapshot per route, written atomically once
per route day. There is no SQLite store and no log rotation.

The replay cannot make everything equal. Where it cannot, it says so:

- **State that ``RouteScorer.state`` does not carry.** The behaviour engine's snapshot leaves
  open protocol sessions out (``BehaviourEngine.snapshot``). A session open across the
  snapshot's rollover therefore continues as a new session after a restart. The replay
  compares each replayed call with the decision the live gateway logged for it, and reports a
  difference (``ReplayReport.differing``); it never hides one. The E14 read ledger (Batch 2)
  is in no route's state either.
- **Calls whose arguments were not logged** (``log_bodies: none``). They cannot be scored
  offline, and ``score.py`` skips them too. They are counted (``calls_without_body``).
- **A torn line** (a line that is not a JSON object). It is skipped, as ``read_log`` skips
  it, and counted (``ReplayReport.torn``). A kill mid-write tears a line the gateway had not
  scored yet: it writes a line before it scores it. A write that failed for another reason
  (``MessageLog`` reports the ``OSError`` and goes on) can tear a line whose call the
  gateway then scored; that call is missing from the replay.
- **v5's reply-side calls** (``RouteScorer.reply`` and ``commit``, ARG-1 and AI-8). The proxy
  makes none yet; they join the calls above when it does (Batch 2).

A line edited, inserted or deleted after the snapshot's line breaks the hash chain. The restore
then names the line, as ``log_file verify`` does, and loads nothing (:class:`ChainBroken`).
Lines before the snapshot's line are not checked here, since their state comes from the
snapshot: ``log_file verify`` finds an edit there. The restore sees one only when it moves or
changes the snapshot's own line (:class:`AnchorMismatch`).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from mcp_security.behaviour.clock import DEFAULT_ZONE, check_day_start, local_day, zone
from mcp_security.behaviour.engine import UTC_DAY_START_HOUR
from mcp_security.behaviour.policy import config_to_json
from mcp_security.gateway.config import baseline_mode
from mcp_security.gateway.framework import RouteScorer, behaviour_fields
from mcp_security.gateway.log_file import CHAIN_FIELD, V1_KEYS, line_digest
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.gateway.wire_log import (
    BEHAVIOUR_FOLD,
    CALL_METHOD,
    FROM_GATEWAY,
    INIT_METHOD,
    POLICY_SWITCHED,
    TO_AGENT,
    TO_SERVER,
)

#: /2 adds the scorer profile and the anchor's line number; a /1 snapshot is refused.
SNAPSHOT_FORMAT = "gateway-state-snapshot/2"
PARTIAL_SUFFIX = ".partial"  # a snapshot is written here first, then renamed over the old one
NEWLINE = b"\n"
LINE_END = b"\r\n"  # stripped from a line before its digest, as ``log_file.verify_chain`` does
TAIL_CHUNK = 65_536  # bytes read at a time when looking for a log's last line
COUNT_CHUNK = 1 << 20  # bytes read at a time when counting lines
DECISION_FIELD = "gateway.decision"
NOTICE_FIELD = "gateway.notice"
EXCHANGE_FIELD = "gateway.exchange_id"
REQUEST_ID_FIELD = "jsonrpc.request.id"
MESSAGE_BYTES_FIELD = "gateway.message_bytes"
#: The gateway adds the artifact digests to a decision after scoring it (``proxy._decide``).
ARTIFACTS_FIELD = "artifacts"
#: Wall-clock time of one score: never the same twice, so never compared.
TIMING_FIELDS = frozenset({"score_us"})
#: LOG-1 lines that change the scorer when replayed (spec 2.9): the route clock's fold and the
#: switch to a re-learned policy. ``flag_surge`` only reports and is not replayed.
REPLAYED_NOTICES = frozenset({BEHAVIOUR_FOLD, POLICY_SWITCHED})
#: A fixed text whose pseudonym tells two pseudonym keys apart (:func:`scorer_profile`).
PSEUDONYM_PROBE = "gateway-state-snapshot: pseudonym key check"
#: What ``RouteScorer.load_state`` raises on a state of the wrong shape.
LOAD_ERRORS = (KeyError, TypeError, ValueError, AttributeError, IndexError)

#: What one log line is to the scorer (:func:`event_kind`).
CALL = "call"  # a tools/call request with its arguments: scored
CALL_WITHOUT_BODY = "call_without_body"  # a tools/call whose arguments were not logged
REQUEST = "request"  # any other request: observed
SESSION_OPENED = "session_opened"  # the reply to initialize that carries the new session id
NOTICE = "notice"  # a LOG-1 line the scorer replays
OTHER = "other"  # decisions, replies, notices: nothing for the scorer
EVENTS = frozenset({CALL, REQUEST, SESSION_OPENED, NOTICE})


class ReplayError(ValueError):
    """A snapshot or a log that a restore cannot use as it is."""


class SnapshotError(ReplayError):
    """The snapshot cannot be read or stored faithfully, it was taken under another scorer
    profile (:class:`ProfileMismatch`), or its state does not load."""


class ProfileMismatch(SnapshotError):
    """The snapshot was taken under another scorer profile (:func:`scorer_profile`).
    ``fields`` names the parts of the profile that differ."""

    def __init__(self, fields: tuple[str, ...], detail: str) -> None:
        super().__init__(f"snapshot does not match the route scorer ({detail})")
        self.fields = fields


class AnchorMismatch(ReplayError):
    """The snapshot's last line is not in the log where the snapshot found it: the log was
    truncated, replaced or edited before that line."""


class ChainBroken(ReplayError):
    """The hash chain breaks after the snapshot's last line. ``lines`` are the line numbers
    (from 1) that ``log_file verify`` would name, torn lines excepted."""

    def __init__(self, path: Path, lines: tuple[int, ...]) -> None:
        shown = ", ".join(map(str, lines))
        super().__init__(f"{path}: hash chain broken at line(s) {shown}; nothing was loaded")
        self.lines = lines


class ReplayFailed(ReplayError):
    """A replayed line could not be applied: a scorer call that the live gateway does not
    catch either raised on it (``session_initialized``, ``apply_notice``), or a line the
    scorer needs has no timestamp. ``line`` is its number (from 1)."""

    def __init__(self, path: Path, line: int, reason: str) -> None:
        super().__init__(f"{path}: line {line}: {reason}; the scorer holds the lines before it")
        self.line = line


@dataclass(frozen=True)
class LogAnchor:
    """The last log line a snapshot includes: where the line starts in the file, in bytes;
    the SHA-256 of its bytes, newline excluded (``log_file.line_digest``); and its line
    number from 1, as ``log_file verify`` counts lines (None: not counted).
    ``SnapshotError`` for a field of the wrong type."""

    offset: int
    sha256: str
    line: int | None = None

    def __post_init__(self) -> None:
        valid = (
            _is_int(self.offset)
            and self.offset >= 0
            and isinstance(self.sha256, str)
            and (self.line is None or (_is_int(self.line) and self.line >= 1))
        )
        if not valid:
            raise SnapshotError(f"malformed log anchor: {self!r}")

    def to_json(self) -> dict:
        """The anchor as the snapshot file stores it."""
        return {"offset": self.offset, "sha256": self.sha256, "line": self.line}

    @classmethod
    def from_json(cls, data: object) -> LogAnchor:
        """An anchor from :meth:`to_json` output; ``SnapshotError`` if it is malformed."""
        if not isinstance(data, dict):
            raise SnapshotError(f"malformed log anchor: {data!r}")
        return cls(data.get("offset"), data.get("sha256"), data.get("line"))


@dataclass(frozen=True)
class Snapshot:
    """One route's state at a rollover, and the log line it reaches to.

    ``profile`` is what the state was learned under (:func:`scorer_profile`). ``last_ts`` is
    the newest scorer event the state includes, which sets the route day the snapshot closes
    (:attr:`day`) on the keeper's clock (``zone``, ``day_start_hour``). ``anchor`` is None
    when the log had no line yet. ``SnapshotError`` for a field of the wrong type."""

    profile: dict
    zone: str
    day_start_hour: float
    last_ts: float | None
    anchor: LogAnchor | None
    state: dict

    def __post_init__(self) -> None:
        profile = self.profile
        named = isinstance(profile, dict) and all(
            isinstance(profile.get(name), str) for name in ("route", "design")
        )
        problems = [
            name
            for name, ok in (
                ("profile", named),
                ("zone and day_start_hour", _clock_ok(self.zone, self.day_start_hour)),
                ("last_ts", self.last_ts is None or _is_number(self.last_ts)),
                ("anchor", self.anchor is None or isinstance(self.anchor, LogAnchor)),
                ("state", isinstance(self.state, dict)),
            )
            if not ok
        ]
        if problems:
            raise SnapshotError(f"malformed snapshot: {', '.join(problems)}")

    @property
    def route(self) -> str:
        """The route the snapshot was taken on."""
        return self.profile["route"]

    @property
    def design(self) -> str:
        """The behaviour design its state was learned with."""
        return self.profile["design"]

    @property
    def day(self) -> int | None:
        """The route day of the newest event the state includes (None: no event yet)."""
        if self.last_ts is None:
            return None
        return local_day(self.last_ts, self.zone, self.day_start_hour)

    def to_json(self) -> dict:
        """The snapshot as its file stores it."""
        return {
            "format": SNAPSHOT_FORMAT,
            "profile": self.profile,
            "zone": self.zone,
            "day_start_hour": self.day_start_hour,
            "last_ts": self.last_ts,
            "day": self.day,
            "anchor": self.anchor.to_json() if self.anchor else None,
            "state": self.state,
        }

    @classmethod
    def from_json(cls, data: object) -> Snapshot:
        """A snapshot from :meth:`to_json` output; ``SnapshotError`` for another format or a
        malformed field."""
        if not isinstance(data, dict) or data.get("format") != SNAPSHOT_FORMAT:
            found = data.get("format") if isinstance(data, dict) else type(data).__name__
            raise SnapshotError(f"not a {SNAPSHOT_FORMAT} snapshot (found {found!r})")
        try:
            anchor = data["anchor"]
            return cls(
                profile=data["profile"],
                zone=data["zone"],
                day_start_hour=data["day_start_hour"],
                last_ts=data["last_ts"],
                anchor=LogAnchor.from_json(anchor) if anchor is not None else None,
                state=data["state"],
            )
        except KeyError as exc:
            raise SnapshotError(f"malformed snapshot: no {exc}") from exc


def scorer_profile(scorer: RouteScorer, state: dict | None = None) -> dict:
    """What a route scorer's state was learned under, besides the log. A snapshot restores
    only into a scorer with the same profile; for any other, replay the whole log.

    - ``route``, ``design``, ``history`` (the runtime factor's scope: one history per route
      or per caller, from ``routes.json``);
    - ``artifacts``: the digests of the scan, breadth, rules and behaviour policy;
    - ``behaviour_config``: the SHA-256 of the behaviour config in effect, which also covers
      the code's defaults and a route's override of its policy (B9d's ``route_zone``);
    - ``state_layout``: the state's format (:func:`state_layout`);
    - ``inputs``: the ``routes.json`` fields the scorer reads (Batch 2: B1's baseline key, B9d's
      zone and zone map, B10's egress table), whether it has an E14 ledger, and the pseudonym
      of :data:`PSEUDONYM_PROBE` under its pseudonym key (equal keys give equal values; it
      shows no more of the key than any pseudonym in the log does).

    ``state`` is ``scorer.state()`` when the caller already has it. The profile is returned as
    JSON gives it back."""
    config, upstream = scorer.behaviour.config, scorer.upstream
    profile = {
        "route": scorer.route,
        "design": config.design,
        "history": scorer.history,
        "artifacts": dict(scorer.artifacts.digests),
        "behaviour_config": _json_digest(config_to_json(config)),
        "state_layout": state_layout(scorer.state() if state is None else state),
        "inputs": {
            "baseline_key": baseline_mode(upstream, config.design),
            "route_zone": upstream.route_zone if upstream else None,
            "zone_map": upstream.zone_map if upstream else None,
            "shared_egress": upstream.shared_egress if upstream else None,
            "ledger": scorer.ledger is not None,
            "pseudonyms": _pseudonym_check(scorer.pseudonymizer),
        },
    }
    return json.loads(json.dumps(profile))


def state_layout(state: dict) -> dict:
    """A state's format: its ``RouteScorer`` state version and the behaviour engine's
    sections. Code that writes another layout cannot load the state faithfully."""
    behaviour = state.get("behaviour")
    return {
        "version": state.get("version"),
        "behaviour": sorted(behaviour) if isinstance(behaviour, dict) else None,
    }


@dataclass(frozen=True)
class ReplayedCall:
    """One ``tools/call`` the replay scored: its line, and the decision the scorer gave.
    ``tool`` is the name as the agent sent it: a string, unless the agent sent another JSON
    value."""

    line: int
    ts: float
    tool: object
    caller: str | None
    decision: dict


@dataclass(frozen=True)
class ReplayReport:
    """What a replay did and what it could not make equal.

    Line numbers count from 1, as ``log_file verify`` counts them.

    - ``snapshot``: the snapshot file loaded; None when the whole log was replayed.
    - ``first_line``: the first line replayed (the line after the snapshot's).
    - ``lines``: JSON-object lines read after the snapshot's line (torn lines are in ``torn``).
    - ``events``: ``RouteScorer`` calls made.
    - ``calls_without_body``: tools/call lines whose arguments were not logged.
    - ``torn``: lines that are not JSON objects, skipped (writes cut short).
    - ``broken``: chain breaks; empty unless the replay ran with ``strict=False``.
    - ``errors``: lines whose ``score`` or ``observe`` raised; the replay went on, as the
      live gateway did.
    - ``checked``: replayed calls compared with the decision the live gateway logged.
    - ``differing``: decision lines the replay did not reproduce.
    - ``last_ts``: the newest event the scorer now includes.
    - ``end``: the log's last line when the replay ended, numbered (None: an empty log). A
      resumed :class:`RolloverSnapshots` numbers its next anchor from it (``base``).
    - ``calls``: every scored call, only with ``keep_calls``.
    """

    snapshot: Path | None
    first_line: int
    lines: int = 0
    events: int = 0
    calls_without_body: int = 0
    torn: tuple[int, ...] = ()
    broken: tuple[int, ...] = ()
    errors: tuple[int, ...] = ()
    checked: int = 0
    differing: tuple[int, ...] = ()
    last_ts: float | None = None
    end: LogAnchor | None = None
    calls: tuple[ReplayedCall, ...] = field(default=(), repr=False)


# ── one log line, applied to the scorer ───────────────────────────────────────────────────


def event_kind(record: dict) -> str:
    """What a log record is to the scorer: :data:`CALL`, :data:`CALL_WITHOUT_BODY`,
    :data:`REQUEST`, :data:`SESSION_OPENED`, :data:`NOTICE` or :data:`OTHER`. The reading of
    ``score.py``'s ``pair_calls`` and its behaviour events, except that a reply opens a
    session only when it carried a message, as live (:func:`_has_body`)."""
    direction, method = record.get("gateway.direction"), _method(record)
    if direction == TO_SERVER and method == CALL_METHOD:
        return CALL if isinstance(record.get("message"), dict) else CALL_WITHOUT_BODY
    if direction == TO_SERVER and method:
        return REQUEST
    if (
        direction == TO_AGENT
        and method == INIT_METHOD
        and record.get("mcp.session.id")
        and _has_body(record)
    ):
        return SESSION_OPENED
    if record.get(NOTICE_FIELD) in REPLAYED_NOTICES:
        return NOTICE
    return OTHER


def apply_record(scorer: RouteScorer, record: dict) -> dict | None:
    """Feed one log record to ``scorer`` with the call the live gateway made when it wrote
    the line: the decision for a ``tools/call`` request with its arguments, else None.

    It raises whatever the scorer raises. The live gateway logs an error from ``score`` as
    the call's decision and one from ``observe`` as a notice, and goes on
    (``proxy._decide``, ``proxy._observe``); :func:`replay_log` does the same."""
    kind, ts = event_kind(record), record["ts"]
    if kind == CALL:
        fields = behaviour_fields(record)
        caller = fields.pop("caller")
        params = record["message"].get("params") or {}
        args = params.get("arguments") or {}  # params not an object: the proxy fails here too
        tool = params.get("name") or record.get("gen_ai.tool.name")
        return scorer.score(tool, args, ts, caller, **fields)
    if kind == REQUEST:
        scorer.observe(_method(record), ts, **behaviour_fields(record))
    elif kind == SESSION_OPENED:
        caller = behaviour_fields(record)["caller"]
        scorer.session_initialized(caller, record["mcp.session.id"], ts)
    elif kind == NOTICE:
        scorer.apply_notice(record)
    return None


def _method(record: dict) -> str | None:
    """The line's method: its field, else the message's own (``score.py``'s reading)."""
    message = record.get("message")
    return record.get("mcp.method.name") or (
        message.get("method") if isinstance(message, dict) else None
    )


def _has_body(record: dict) -> bool:
    """Whether a reply line carried a message. The proxy reads the session opened by
    ``initialize`` only from such a reply (``proxy._answered``), never from a bodiless line
    (a 202, an empty body), which still names ``initialize`` when the agent sent it with
    ``"id": null``. A line without its body (``log_bodies``) still has its size."""
    if isinstance(record.get("message"), dict):
        return True
    size = record.get(MESSAGE_BYTES_FIELD)
    return _is_int(size) and size > 0


def _call_tool(record: dict) -> object:
    """A tools/call line's tool: the message's name, else the line's field (``score.py``)."""
    message = record.get("message")
    params = message.get("params") if isinstance(message, dict) else None
    name = params.get("name") if isinstance(params, dict) else None
    return name or record.get("gen_ai.tool.name")


# ── snapshots ─────────────────────────────────────────────────────────────────────────────


def log_anchor(log_path: Path, base: LogAnchor | None = None) -> LogAnchor | None:
    """The anchor for a snapshot taken now: the log's last line, where it starts, its digest
    and its number; None for a missing or empty log.

    ``base`` is an earlier anchor in the same log (the last one taken, or a restore's
    ``ReplayReport.end``). While its line is still where it was, the number is counted from
    it, reading only the bytes after it; otherwise it is counted from the start of the log.
    A torn last line is a valid anchor: the next line the gateway writes chains to it as it
    is."""
    found = _last_line(log_path)
    if found is None:
        return None
    offset, line = found
    with log_path.open("rb") as handle:
        number = _line_number(handle, offset, base)
    return LogAnchor(offset, line_digest(line), number)


def take_snapshot(
    scorer: RouteScorer,
    anchor: LogAnchor | None,
    last_ts: float | None,
    zone_name: str = DEFAULT_ZONE,
    day_start_hour: float = UTC_DAY_START_HOUR,
) -> Snapshot:
    """``scorer``'s state now, anchored at ``anchor``: every scorer event at or before that
    line must already be in the state, and none after it. Inline scoring holds this between
    two requests; background scoring must take the snapshot in its queue, with the anchor
    read when the snapshot was queued.

    ``SnapshotError`` when the state has a key JSON would store as a string
    (:func:`_check_keys`): the restored state would then not be the live one."""
    state = scorer.state()
    _check_keys(state)
    profile = scorer_profile(scorer, state)
    return Snapshot(profile, zone_name, day_start_hour, last_ts, anchor, state)


def write_snapshot(path: Path, snapshot: Snapshot) -> None:
    """Write ``snapshot`` to ``path`` atomically and durably: a crash leaves the old file or
    the new one, never a part of either, and no partial file is left behind. ``OSError`` if
    it cannot be written or its rename cannot be made durable; ``path`` then holds a whole
    snapshot, the old one or the new one."""
    text = json.dumps(snapshot.to_json())  # fails, if it does, before any file is touched
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + PARTIAL_SUFFIX)
    try:
        with partial.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        partial.replace(path)
    except OSError:
        partial.unlink(missing_ok=True)
        raise
    _fsync_path(path.parent)  # the rename itself survives a crash


def read_snapshot(path: Path) -> Snapshot:
    """The snapshot in ``path``; ``SnapshotError`` if it cannot be read or is not one."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SnapshotError(f"{path}: cannot read the snapshot: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"{path}: not a JSON snapshot: {exc}") from exc
    try:
        return Snapshot.from_json(data)
    except SnapshotError as exc:
        raise SnapshotError(f"{path}: {exc}") from exc


class RolloverSnapshots:
    """When to snapshot one route, and the writing of it: once per route day, at the first
    scorer event after the route's rollover.

    The route day is the route clock's (``clock.local_day``): from ``day_start_hour`` to the
    next in ``zone_name``. That is 04:00 in the route's zone for v5 (CAL-7, B9) and midnight
    UTC for v1-v4 (:meth:`for_scorer` reads both from the scorer's behaviour policy). The
    gateway, before it logs a request whose line will reach the scorer::

        if keeper.crossed(ts):
            keeper.take(scorer, keeper.anchor())
        keeper.seen(ts)

    Background scoring queues the snapshot behind the events already queued, with what it
    reads when it queues it: ``anchor, last = keeper.anchor(), keeper.last_ts``, and later
    ``keeper.take(scorer, anchor, last)``.

    After a restart, resume from the restore's report: ``last_ts=report.last_ts`` and
    ``base=report.end``. ``log_path`` is the route's log: :meth:`anchor` reads it, and
    :meth:`take` makes it durable before the snapshot. ``path`` must not be the route's
    ``state_file``, which ``proxy.save_state`` overwrites with raw state.
    """

    def __init__(
        self,
        path: Path,
        zone_name: str = DEFAULT_ZONE,
        day_start_hour: float = UTC_DAY_START_HOUR,
        last_ts: float | None = None,
        *,
        log_path: Path | None = None,
        base: LogAnchor | None = None,
    ) -> None:
        zone(zone_name)  # ValueError for an unknown zone
        check_day_start(day_start_hour)
        if last_ts is not None and not _is_number(last_ts):
            raise ValueError(f"last_ts must be a number or None, not {last_ts!r}")
        self.path = path
        self.zone = zone_name
        self.day_start_hour = day_start_hour
        self.last_ts = last_ts
        self.log_path = log_path
        self.base = base  # the last anchor read: the next one is numbered from it

    @classmethod
    def for_scorer(
        cls,
        scorer: RouteScorer,
        path: Path,
        last_ts: float | None = None,
        *,
        log_path: Path | None = None,
        base: LogAnchor | None = None,
    ) -> RolloverSnapshots:
        """A keeper on the route clock of ``scorer``'s behaviour policy."""
        config = scorer.behaviour.config
        return cls(
            path, config.route_zone, config.day_start_hour, last_ts, log_path=log_path, base=base
        )

    def day(self, ts: float) -> int:
        """The route day ``ts`` falls on."""
        return local_day(ts, self.zone, self.day_start_hour)

    def crossed(self, ts: float) -> bool:
        """Whether an event at ``ts`` is the first after a rollover: it falls on a later route
        day than the newest event seen. Never before the first event."""
        return self.last_ts is not None and self.day(ts) > self.day(self.last_ts)

    def seen(self, ts: float) -> None:
        """Note a scorer event at ``ts`` (an older ``ts`` changes nothing)."""
        if self.last_ts is None or ts > self.last_ts:
            self.last_ts = ts

    def anchor(self) -> LogAnchor | None:
        """The anchor for a snapshot taken now (:func:`log_anchor` of ``log_path``), numbered
        from the last anchor read, which it then replaces. ``ValueError`` without a
        ``log_path``."""
        if self.log_path is None:
            raise ValueError("this keeper has no log_path to read an anchor from")
        found = log_anchor(self.log_path, self.base)
        if found is not None:
            self.base = found
        return found

    def take(
        self, scorer: RouteScorer, anchor: LogAnchor | None, last_ts: float | None = None
    ) -> Snapshot:
        """Snapshot ``scorer`` now, anchored at ``anchor``, and write it over the route's
        previous snapshot. ``last_ts`` is the newest event the state includes: by default the
        newest seen; a queued snapshot passes the value read when it was queued. With a
        ``log_path``, the log is made durable first, so a snapshot never reaches past the log
        on disk. ``OSError`` if either cannot be written (:func:`write_snapshot`), and
        ``SnapshotError`` if the state cannot be stored faithfully, which leaves the old
        snapshot."""
        newest = self.last_ts if last_ts is None else last_ts
        snapshot = take_snapshot(scorer, anchor, newest, self.zone, self.day_start_hour)
        if self.log_path is not None and anchor is not None:
            _fsync_path(self.log_path)
        write_snapshot(self.path, snapshot)
        return snapshot


# ── restore and replay ────────────────────────────────────────────────────────────────────


def restore_route(
    scorer: RouteScorer,
    log_path: Path,
    snapshot_path: Path | None = None,
    *,
    strict: bool = True,
    keep_calls: bool = False,
) -> ReplayReport:
    """Bring a freshly built ``scorer`` to where the route's log ends: load the snapshot,
    then replay the log after its line. Without a snapshot file, replay the whole log; with
    neither, do nothing.

    Every error is a :class:`ReplayError`. After one, build a fresh scorer for what follows:

    - ``SnapshotError``: the snapshot cannot be read, it was taken under another profile
      (``ProfileMismatch``, :func:`scorer_profile`), or its state does not load. Replay the
      whole log into the fresh scorer (:func:`replay_log`): that is the offline re-score of
      the log.
    - ``AnchorMismatch``: the log no longer holds the snapshot's line where it was. It was
      truncated (a crash before the log reached the disk), replaced, or edited before that
      line. Do the same: a strict whole-log replay equals an offline re-score of the log as
      it is now, and raises ``ChainBroken`` if a line in it was edited.
    - ``ChainBroken``: a line after the snapshot's was edited, inserted or deleted (only with
      ``strict``). The operator decides: replay with ``strict=False``, which lists the broken
      lines in ``ReplayReport.broken``, or leave the route unscored.
    - ``ReplayFailed``: a replayed line could not be applied.

    An unreadable or mismatched snapshot, ``AnchorMismatch`` and ``ChainBroken`` leave
    ``scorer`` as it was. A state that does not load (``SnapshotError``) and ``ReplayFailed``
    leave part of it in ``scorer``. ``OSError`` if the log cannot be read.
    """
    if snapshot_path is None or not snapshot_path.exists():
        return replay_log(scorer, log_path, strict=strict, keep_calls=keep_calls)
    snapshot = read_snapshot(snapshot_path)
    _check_compatible(snapshot, scorer)
    tail = _check_tail(log_path, snapshot.anchor, strict)
    _load_state(scorer, snapshot, snapshot_path)
    return _replay_tail(scorer, log_path, tail, snapshot_path, snapshot.last_ts, keep_calls)


def replay_log(
    scorer: RouteScorer,
    log_path: Path,
    *,
    after: LogAnchor | None = None,
    strict: bool = True,
    keep_calls: bool = False,
) -> ReplayReport:
    """Replay every line of the log after ``after`` (None: from the first line) through
    ``scorer``, after checking their hash chain. Loads no state: from the first line this is
    the clean run that a restart must equal. A missing log replays nothing. Raises
    ``AnchorMismatch`` or ``ChainBroken`` (as :func:`restore_route`) before any replay, and
    ``ReplayFailed`` during it."""
    tail = _check_tail(log_path, after, strict)
    return _replay_tail(scorer, log_path, tail, None, None, keep_calls)


@dataclass(frozen=True)
class _Tail:
    """Where the replay starts and what the chain check found."""

    offset: int  # byte offset of the first line after the anchor
    stop: int  # byte offset where the chain check stopped: the replay reads no further
    first_line: int
    torn: tuple[int, ...]
    broken: tuple[int, ...]
    end: LogAnchor | None  # the log's last line, numbered


def _check_compatible(snapshot: Snapshot, scorer: RouteScorer) -> None:
    """``ProfileMismatch`` unless the snapshot was taken under ``scorer``'s profile."""
    expected, found = scorer_profile(scorer), snapshot.profile
    differ = tuple(
        name
        for name in sorted(expected.keys() | found.keys())
        if expected.get(name) != found.get(name)
    )
    if differ:
        detail = "; ".join(
            f"{n}: snapshot {found.get(n)!r}, scorer {expected.get(n)!r}" for n in differ
        )
        raise ProfileMismatch(differ, detail)


def _load_state(scorer: RouteScorer, snapshot: Snapshot, path: Path) -> None:
    """Load the snapshot's state; ``SnapshotError`` if it does not load."""
    try:
        scorer.load_state(snapshot.state)
    except LOAD_ERRORS as exc:
        raise SnapshotError(
            f"{path}: the snapshot's state does not load ({type(exc).__name__}: {exc}); the "
            "scorer holds part of it"
        ) from exc


def _check_tail(log_path: Path, anchor: LogAnchor | None, strict: bool) -> _Tail:
    """Find the anchor and check the hash chain from there to the end of the log. A missing
    log has nothing to replay, unless a snapshot reaches to a line in it."""
    if not log_path.exists():
        if anchor is None:
            return _Tail(0, 0, 1, (), (), None)
        raise AnchorMismatch(f"{log_path}: missing; the snapshot reaches to a line in it")
    with log_path.open("rb") as handle:
        offset, numbered = _after_anchor(handle, log_path, anchor)
        first_line = numbered.line + 1 if numbered else 1
        handle.seek(offset)
        torn, broken, end, stop = _chain_breaks(handle, offset, first_line, numbered)
    if broken and strict:
        raise ChainBroken(log_path, broken)
    return _Tail(offset, stop, first_line, torn, broken, end)


def _after_anchor(
    handle: BinaryIO, log_path: Path, anchor: LogAnchor | None
) -> tuple[int, LogAnchor | None]:
    """Byte offset of the first line after ``anchor``, and the anchor with its line number.
    ``AnchorMismatch`` if the anchor's line is not at its offset."""
    if anchor is None:
        return 0, None
    if not _holds(handle, anchor):
        number = anchor.line if anchor.line is not None else _line_number(handle, anchor.offset)
        raise AnchorMismatch(
            f"{log_path}: line {number} (byte {anchor.offset}) is not the line the snapshot "
            "reaches to: the log was truncated, replaced or edited before it"
        )
    after = handle.tell()
    if anchor.line is not None:
        return after, anchor
    return after, LogAnchor(anchor.offset, anchor.sha256, _line_number(handle, anchor.offset))


def _chain_breaks(
    handle: BinaryIO, start: int, first_line: int, anchor: LogAnchor | None
) -> tuple[tuple[int, ...], tuple[int, ...], LogAnchor | None, int]:
    """(torn lines, broken lines, the last line, the byte offset reached) from ``handle``'s
    position (byte ``start``) to the end.

    The rules are ``log_file.verify_chain``'s, from the anchor on: after an anchor every
    line must carry the digest of the line before it. One exception: a line that is not a
    JSON object is torn, not broken. The gateway chains its next line to a torn line as it
    is, so a torn line in the middle is still checked, through the line after it."""
    torn: list[int] = []
    broken: list[int] = []
    previous = anchor.sha256 if anchor else None
    chained = anchor is not None
    last: tuple[int, str, int] | None = None  # (offset, digest, number) of the last line
    offset = start
    for number, raw in enumerate(handle, start=first_line):
        at, offset = offset, offset + len(raw)
        line = raw.rstrip(LINE_END)
        if not line:
            continue
        record = _parse(line)
        if record is None:
            torn.append(number)
        else:
            claimed = record.get(CHAIN_FIELD)
            if chained and claimed != previous:
                broken.append(number)
            elif not chained and claimed and previous is not None and claimed != previous:
                broken.append(number)
            chained = chained or claimed is not None
        previous = line_digest(line)
        last = (at, previous, number)
    end = LogAnchor(*last) if last else anchor
    return tuple(torn), tuple(broken), end, offset


def _replay_tail(
    scorer: RouteScorer,
    log_path: Path,
    tail: _Tail,
    snapshot_path: Path | None,
    last_ts: float | None,
    keep_calls: bool,
) -> ReplayReport:
    """Apply every record after the anchor to ``scorer``, in log order."""
    digests = dict(scorer.artifacts.digests)
    #: (exchange id, request id) -> the replayed decisions not yet matched, oldest first: a
    #: batch can repeat an id, and background scoring logs its decisions after all its requests
    pending: dict[tuple, deque[dict]] = {}
    calls: list[ReplayedCall] = []
    differing: list[int] = []
    errors: list[int] = []
    lines = events = without_body = checked = 0
    for number, record in _records(log_path, tail):
        lines += 1
        kind = event_kind(record)
        if kind == CALL_WITHOUT_BODY:
            without_body += 1
        if kind not in EVENTS:
            if _is_decision(record):
                outcome = _check_decision(record, pending, digests)
                checked += outcome is not None
                if outcome is False:
                    differing.append(number)
            continue
        ts = record.get("ts")
        if not _is_number(ts):
            raise ReplayFailed(log_path, number, f"a {kind} line without a timestamp")
        events += 1
        last_ts = ts if last_ts is None else max(last_ts, ts)
        try:
            decision = apply_record(scorer, record)
        except Exception as exc:
            # session_initialized is not caught live either; apply_notice is replay's own
            if kind not in (CALL, REQUEST):
                raise ReplayFailed(log_path, number, f"{type(exc).__name__}: {exc}") from exc
            # mirrors proxy._decide and proxy._observe: a scorer error is logged, never fatal
            errors.append(number)
            decision = {"error": f"{type(exc).__name__}: {exc}"} if kind == CALL else None
        if decision is None:
            continue
        if (key := _decision_key(record)) is not None:
            pending.setdefault(key, deque()).append(decision)
        if keep_calls:
            caller = behaviour_fields(record)["caller"]
            calls.append(ReplayedCall(number, ts, _call_tool(record), caller, decision))
    return ReplayReport(
        snapshot=snapshot_path,
        first_line=tail.first_line,
        lines=lines,
        events=events,
        calls_without_body=without_body,
        torn=tail.torn,
        broken=tail.broken,
        errors=tuple(errors),
        checked=checked,
        differing=tuple(differing),
        last_ts=last_ts,
        end=tail.end,
        calls=tuple(calls),
    )


def _records(log_path: Path, tail: _Tail) -> Iterator[tuple[int, dict]]:
    """(line number, record) for every JSON-object line the chain check covered, v1 keys
    renamed as ``log_file.read_log`` renames them; torn lines are skipped. A line written
    after the check is not read. A missing log has none.

    The chain check (:func:`_chain_breaks`) parsed these lines already. They are parsed again
    rather than kept: a strict restore refuses before it changes the scorer, and without a
    snapshot the tail is the whole log."""
    if not log_path.exists():
        return
    with log_path.open("rb") as handle:
        handle.seek(tail.offset)
        offset = tail.offset
        for number, raw in enumerate(handle, start=tail.first_line):
            offset += len(raw)
            if offset > tail.stop:
                return
            line = raw.rstrip(LINE_END)
            record = _parse(line) if line else None
            if record is None:
                continue
            if "schema" not in record:
                record = {V1_KEYS.get(k, k): v for k, v in record.items()}
            yield number, record


def _is_decision(record: dict) -> bool:
    return record.get("gateway.direction") == FROM_GATEWAY and DECISION_FIELD in record


def _decision_key(record: dict) -> tuple | None:
    """Which decision line belongs to a request: its exchange and JSON-RPC id."""
    exchange, request_id = record.get(EXCHANGE_FIELD), record.get(REQUEST_ID_FIELD)
    if exchange is None or request_id is None:
        return None
    return exchange, request_id


def _check_decision(record: dict, pending: dict[tuple, deque[dict]], digests: dict) -> bool | None:
    """Whether the replay reproduced a logged decision; None when it cannot say: the call was
    not replayed (before the anchor, or without its arguments) or was scored with other
    artifacts than the scorer's. Decisions with the same key pair in log order."""
    key = _decision_key(record)
    queue = pending.get(key) if key is not None else None
    if not queue:
        return None
    replayed = queue.popleft()
    if not queue:
        del pending[key]
    logged = record[DECISION_FIELD]
    if not isinstance(logged, dict) or logged.get(ARTIFACTS_FIELD) != digests:
        return None
    return _comparable(logged) == _comparable(replayed)


def _comparable(decision: dict) -> dict:
    """A decision as JSON would carry it, without timing and the artifacts' digests."""
    kept = {k: v for k, v in decision.items() if k not in TIMING_FIELDS and k != ARTIFACTS_FIELD}
    return json.loads(json.dumps(kept, default=str))


def _parse(line: bytes) -> dict | None:
    """A line's record; None if it is not a JSON object (a torn write)."""
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return record if isinstance(record, dict) else None


# ── small helpers ─────────────────────────────────────────────────────────────────────────


def _check_keys(value: object, where: tuple = ()) -> None:
    """``SnapshotError`` naming the first dict key in ``value`` that is not a string. JSON
    stores such a key as a string, so the state read back would not be the state saved: an
    agent's tools/call with ``"name": 7`` is counted under 7 live and under "7" after a
    restore."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                shown = "/".join(map(str, (*where, key)))
                raise SnapshotError(
                    f"the state has the key {key!r} at {shown}, which JSON stores as a string: "
                    "a restore would not equal the live state"
                )
            if isinstance(item, (dict, list, tuple)):
                _check_keys(item, (*where, key))
    elif isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (dict, list, tuple)):
                _check_keys(item, where)


def _pseudonym_check(pseudonymizer: Pseudonymizer | None) -> str | None:
    """The pseudonym of :data:`PSEUDONYM_PROBE` under the scorer's key; None: no key set up."""
    return None if pseudonymizer is None else pseudonymizer.of(PSEUDONYM_PROBE)


def _json_digest(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    """A finite int or float, and not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _clock_ok(zone_name: object, day_start_hour: object) -> bool:
    """Whether ``zone_name`` is a known IANA zone and ``day_start_hour`` an hour in [0, 24)."""
    if not (isinstance(zone_name, str) and _is_number(day_start_hour)):
        return False
    try:
        zone(zone_name)
        check_day_start(day_start_hour)
    except ValueError:
        return False
    return True


def _holds(handle: BinaryIO, anchor: LogAnchor) -> bool:
    """Whether ``anchor``'s line is still at its offset; leaves ``handle`` after that line."""
    handle.seek(anchor.offset)
    line = handle.readline()
    return bool(line) and line_digest(line.rstrip(LINE_END)) == anchor.sha256


def _line_number(handle: BinaryIO, offset: int, base: LogAnchor | None = None) -> int:
    """The number (from 1) of the line that starts at ``offset``: counted from ``base`` while
    its line still holds and starts no later, else from the start of the file."""
    if base is not None and base.line is not None and base.offset <= offset:
        if _holds(handle, base):
            return base.line + _count_newlines(handle, base.offset, offset)
    return _count_newlines(handle, 0, offset) + 1


def _count_newlines(handle: BinaryIO, start: int, end: int) -> int:
    """Newlines in the bytes from ``start`` to ``end``."""
    handle.seek(start)
    count, left = 0, end - start
    while left > 0:
        chunk = handle.read(min(COUNT_CHUNK, left))
        if not chunk:
            break
        count += chunk.count(NEWLINE)
        left -= len(chunk)
    return count


def _last_line(path: Path) -> tuple[int, bytes] | None:
    """(byte offset where it starts, bytes without its newline) of a file's last non-empty
    line; None for a missing file or one with no line."""
    if not path.exists():
        return None
    with path.open("rb") as handle:
        position = handle.seek(0, os.SEEK_END)
        tail = b""
        while position > 0:
            step = min(TAIL_CHUNK, position)
            position -= step
            handle.seek(position)
            tail = handle.read(step) + tail
            body = tail.rstrip(LINE_END)
            cut = body.rfind(NEWLINE)
            if cut >= 0:
                return position + cut + 1, body[cut + 1 :]
        body = tail.rstrip(LINE_END)
        return (0, body) if body else None


def _fsync_path(path: Path) -> None:
    """Flush a file, or a directory's entries, to disk (POSIX; elsewhere, nothing)."""
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
