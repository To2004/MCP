"""E4 (v5): the caller's own session, a run of his calls ended by an idle gap.

Design v4 measures Session duration from the MCP protocol session: minutes since the session
id was first seen. A protocol session's lifetime is set by the host application (some hosts
open a fresh session for every call, and stateless servers mint none), so v4's dimension
measured the client, not the caller. Design v5 measures the caller's own timing instead::

    a call at ts starts a new session  <=>  there was no earlier call, or
                                            ts - (his last call) > idle_gap_s   (G = 30 min)
    session_start <- ts on a new session;  last_call <- max(last_call, ts)
    Session duration = (ts - session_start) / 60   minutes, never negative

The engine key stays ``session_length``; only its definition changes. The state is per
caller (not a protocol-session map), so junk session ids, session eviction and restarts
cannot reset it; a restart longer than G ends the session, which is what the server saw.

Everything here is pure: :func:`advance` returns the session a call belongs to and never
changes its input, so the engine can score a call (``score``) and keep the new session only
when it commits the call (``commit``, ARG-1). Call it on scored calls only (AI-10's
``tools/call``, ``resources/read`` and ``prompts/get``); housekeeping messages never move
the session (E12).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MINUTE_S = 60.0
IDLE_GAP_S = 30 * MINUTE_S  # E4: G, equal to engine.IDLE_GAP_S (the config's v5 default)


@dataclass(frozen=True)
class OwnSession:
    """One run of a caller's calls: when it began and when his latest call in it came."""

    start: float
    last_call: float

    def minutes_at(self, ts: float) -> float:
        """Session duration at ``ts``: minutes since the run began (0 for a late message
        stamped before the run's start)."""
        return max(0.0, ts - self.start) / MINUTE_S

    def to_json(self) -> list[float]:
        """``[start, last_call]``, JSON-safe, for the engine's snapshot."""
        return [self.start, self.last_call]

    @classmethod
    def from_json(cls, data: list[float] | None) -> OwnSession | None:
        """A saved session back; None for a caller saved without one (a v4 snapshot)."""
        if data is None:
            return None
        start, last_call = data
        return cls(float(start), float(last_call))


def check_idle_gap(idle_gap_s: float) -> None:
    """``ValueError`` unless the idle gap is a positive, finite number of seconds."""
    if isinstance(idle_gap_s, bool) or not (
        isinstance(idle_gap_s, int | float) and math.isfinite(idle_gap_s) and idle_gap_s > 0
    ):
        raise ValueError(f"idle_gap_s must be a positive number of seconds, not {idle_gap_s!r}")


def continues(previous: OwnSession | None, ts: float, idle_gap_s: float = IDLE_GAP_S) -> bool:
    """Whether a call at ``ts`` belongs to ``previous``: there is one, and the idle time since
    its latest call is at most the gap (a gap of exactly ``idle_gap_s`` still continues it)."""
    check_idle_gap(idle_gap_s)
    return previous is not None and ts - previous.last_call <= idle_gap_s


def advance(previous: OwnSession | None, ts: float, idle_gap_s: float = IDLE_GAP_S) -> OwnSession:
    """The caller's session after a call at ``ts``: ``previous`` extended, or a new one.

    A late message (stamped before the latest call) stays in the run and never moves its
    latest call back. ``previous`` is not changed."""
    check_idle_gap(idle_gap_s)
    if not math.isfinite(ts):
        raise ValueError(f"ts must be a finite timestamp, not {ts!r}")
    if previous is not None and continues(previous, ts, idle_gap_s):
        return OwnSession(previous.start, max(previous.last_call, ts))
    return OwnSession(ts, ts)
