"""E6 and E8 (v5): Missing handshake for legacy MCP, over each caller's started sessions.

Missing handshake (engine key ``protocol_skip``) is legacy-only and watch-only in v5: it
orders the review list but can never alert alone (spec 2.2 row 15; the modern-era definition
was cut). It is raised for a legacy-era scored call with no ``initialize`` behind it, from a
caller who normally sends one::

    raised  <=> era = legacy and warm and normally(caller) and not started(session)
    started(None) = false   (a sessionless call counts: E6's switch handshake_legacy_sessionless;
                            an empty id "" is no id, so it is sessionless too)
    started(id)   <=> the server assigned ``id`` to this caller in reply to his initialize,
                      and he used it within session_ttl_s
    normally(caller) <=> n >= 3 and 2 * ok >= n, counted once per own session (E4) at its
                      first legacy call, ok <=> that call's session was started

So a caller on a stateless legacy server (never a session) never "normally initializes" and
is never raised; a caller who always initializes and then sends a sessionless call is.

E8, the legacy session state: a session is stored only when the server assigned it in its
reply to ``initialize`` (:func:`session_started`); an id the caller merely presents is
"not started" and leaves no state. Sessions are kept per caller, at most
``max_sessions_per_caller`` (64), least recently used dropped first, so junk ids from one
caller can never evict another's. A session unused for ``session_ttl_s`` (7 days) is
forgotten, and snapshots keep only live sessions.

Pure checks and explicit updates, for the engine's score/commit split (ARG-1)::

    finding = check(state, era=..., session=..., ts=..., warm=..., rules=...)
    commit(state, era=..., session=..., ts=..., run_start=..., rules=...)  # once accepted
"""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_security.behaviour.engine import BehaviourConfig

DAY_S = 86_400.0
#: The protocol era of a call (E3), equal to ``engine.LEGACY_ERA`` (this module cannot
#: import the engine, which imports it). Any other era, or none, is never checked.
LEGACY_ERA = "legacy"
NORMALLY_INITIALIZES_AFTER = 3  # own sessions counted before "he normally initializes" holds
MAX_SESSIONS_PER_CALLER = 64  # E8
SESSION_TTL_S = 7 * DAY_S  # E8: refreshed on every use
HANDSHAKE_STRENGTH = 1  # a yes/no flag: every raise is equally strong (organisation-priced)

#: Why a call was raised (for ``Verdict.notes``).
SESSIONLESS_NOTE = "missing handshake (legacy: sessionless call)"
NOT_STARTED_NOTE = "missing handshake (legacy: session never initialized)"


@dataclass(frozen=True)
class HandshakeRules:
    """The settings: E8's quota and TTL (None: no quota, no TTL), v4's "normally" count, and
    E6's switch for sessionless calls (off: they are neither counted nor raised)."""

    max_sessions: int | None = MAX_SESSIONS_PER_CALLER
    session_ttl_s: float | None = SESSION_TTL_S
    normally_after: int = NORMALLY_INITIALIZES_AFTER
    sessionless_counts: bool = True

    def __post_init__(self) -> None:
        if self.max_sessions is not None and (
            isinstance(self.max_sessions, bool)
            or not isinstance(self.max_sessions, int)
            or self.max_sessions <= 0
        ):
            raise ValueError(
                f"max_sessions must be a positive integer or None: {self.max_sessions!r}"
            )
        ttl = self.session_ttl_s
        if ttl is not None and (
            isinstance(ttl, bool)
            or not isinstance(ttl, int | float)
            or not math.isfinite(ttl)
            or ttl <= 0
        ):
            raise ValueError(f"session_ttl_s must be positive seconds or None, not {ttl!r}")
        if (
            isinstance(self.normally_after, bool)
            or not isinstance(self.normally_after, int)
            or (self.normally_after <= 0)
        ):
            raise ValueError(f"normally_after must be a positive integer: {self.normally_after!r}")

    @classmethod
    def from_config(cls, config: BehaviourConfig) -> HandshakeRules:
        """The rules of a behaviour config (v5: ``max_sessions_per_caller``,
        ``session_ttl_s``, ``normally_initializes_after``, ``handshake_legacy_sessionless``)."""
        return cls(
            max_sessions=config.max_sessions_per_caller,
            session_ttl_s=config.session_ttl_s,
            normally_after=config.normally_initializes_after,
            sessionless_counts=config.handshake_legacy_sessionless,
        )


@dataclass(frozen=True)
class HandshakeFinding:
    """The check's answer for one call: raised or not, and why (a ``Verdict.notes`` text)."""

    raised: bool = False
    note: str | None = None

    @property
    def strength(self) -> int | None:
        """The flag's strength when raised (always :data:`HANDSHAKE_STRENGTH`)."""
        return HANDSHAKE_STRENGTH if self.raised else None


@dataclass
class HandshakeState:
    """One caller's legacy-handshake memory, saved in the engine's snapshot."""

    #: E8: started session id -> when he last used it, least recently used first
    sessions: OrderedDict[str, float] = field(default_factory=OrderedDict)
    seen: int = 0  # own sessions counted (n)
    initialized: int = 0  # ... whose first legacy call was in a started session (ok)
    counted_run: float | None = None  # the start of the own session counted last

    def to_json(self, now: float | None = None, ttl: float | None = SESSION_TTL_S) -> dict:
        """JSON-safe data for the engine's snapshot. With ``now``, sessions idle longer than
        ``ttl`` are left out (E8: only live sessions are saved)."""
        live = [
            [sid, last]
            for sid, last in self.sessions.items()
            if now is None or ttl is None or now - last <= ttl
        ]
        return {
            "sessions": live,
            "seen": self.seen,
            "initialized": self.initialized,
            "counted_run": self.counted_run,
        }

    @classmethod
    def from_json(cls, data: dict | None) -> HandshakeState:
        """Saved state back; empty for a caller saved without one (a v4 snapshot)."""
        if not data:
            return cls()
        return cls(
            sessions=OrderedDict((sid, float(last)) for sid, last in data.get("sessions", [])),
            seen=int(data.get("seen", 0)),
            initialized=int(data.get("initialized", 0)),
            counted_run=data.get("counted_run"),
        )


def session_started(
    state: HandshakeState, session: str | None, ts: float, rules: HandshakeRules
) -> None:
    """E8: the server assigned ``session`` to this caller in its reply to ``initialize``.
    Without an id (a stateless server) there is nothing to remember."""
    if not session:
        return
    state.sessions[session] = ts
    state.sessions.move_to_end(session)
    _evict(state, ts, rules)


def is_started(
    state: HandshakeState, session: str | None, ts: float, rules: HandshakeRules
) -> bool:
    """Whether ``session`` is one of the caller's live started sessions at ``ts`` (never
    for no id, None or "")."""
    if not session:
        return False
    last = state.sessions.get(session)
    if last is None:
        return False
    return rules.session_ttl_s is None or ts - last <= rules.session_ttl_s


def normally_initializes(state: HandshakeState, rules: HandshakeRules) -> bool:
    """At least ``normally_after`` own sessions counted, at least half of them started."""
    return state.seen >= rules.normally_after and 2 * state.initialized >= state.seen


def check(
    state: HandshakeState,
    *,
    era: str | None,
    session: str | None,
    ts: float,
    warm: bool,
    rules: HandshakeRules,
) -> HandshakeFinding:
    """E6 for one scored call, without changing ``state``. ``warm``: the caller is past his
    warm-up (the engine's rule). Only the legacy era is checked; an empty id is no id."""
    session = session or None
    if era != LEGACY_ERA or (session is None and not rules.sessionless_counts):
        return HandshakeFinding()
    if not warm or is_started(state, session, ts, rules):
        return HandshakeFinding()
    if not normally_initializes(state, rules):
        return HandshakeFinding()
    return HandshakeFinding(True, SESSIONLESS_NOTE if session is None else NOT_STARTED_NOTE)


def commit(
    state: HandshakeState,
    *,
    era: str | None,
    session: str | None,
    ts: float,
    run_start: float,
    rules: HandshakeRules,
) -> None:
    """Learn from an accepted scored call. ``run_start`` is the start of the caller's own
    session (E4's ``OwnSession.start``): its first legacy call counts toward "normally",
    once. A started session's use refreshes its TTL; an expired one is dropped. An empty id
    is no id."""
    session = session or None
    if era != LEGACY_ERA or (session is None and not rules.sessionless_counts):
        return
    started = is_started(state, session, ts, rules)
    if state.counted_run != run_start:
        state.counted_run = run_start
        state.seen += 1
        state.initialized += int(started)
    if started:
        state.sessions[session] = max(ts, state.sessions[session])
        state.sessions.move_to_end(session)
    elif session in state.sessions:
        del state.sessions[session]  # expired
    _evict(state, ts, rules)


def _evict(state: HandshakeState, ts: float, rules: HandshakeRules) -> None:
    """Drop sessions past their TTL, then the least recently used past the quota."""
    sessions = state.sessions
    if rules.session_ttl_s is not None:
        while sessions and ts - next(iter(sessions.values())) > rules.session_ttl_s:
            sessions.popitem(last=False)
    if rules.max_sessions is not None:
        while len(sessions) > rules.max_sessions:
            sessions.popitem(last=False)
