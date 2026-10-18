"""Per-agent behavioral baseline: what is normal for this persona on this server.

No ML, no benchmark: a baseline is built from a persona's own observed calls
(:class:`mcp_security.call_scoring.score.ScoredCall`) — which tools it uses and
the highest asset sensitivity it has touched, plus its typical session size for
burst detection. A new call is scored by how far it deviates from that history,
never by comparison to a labeled ground truth.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass

from mcp_security.call_scoring.score import ScoredCall
from mcp_security.param_scoring.combine import BANDS

# Session call counts more than this many standard deviations above the
# persona's own mean are flagged as an abnormal burst.
BURST_Z_THRESHOLD = 2.0

# No baseline / not enough history to judge deviation: `"low"` is the honest
# answer (no signal), never a fabricated escalation.
_NO_SIGNAL_BAND = BANDS[0]


@dataclass(frozen=True)
class AgentBaseline:
    """One persona's observed-normal profile on one server."""

    key: str  # f"{persona}@{server}"
    known_tools: frozenset[str]
    max_sensitivity: int
    mean_calls_per_session: float
    stdev_calls_per_session: float
    n_sessions: int


def _baseline_key(persona: str, server: str) -> str:
    return f"{persona}@{server}"


def build_baselines(calls: list[ScoredCall]) -> dict[str, AgentBaseline]:
    """Build one :class:`AgentBaseline` per (persona, server) seen in ``calls``.

    Groups by ``run_id`` to size sessions, then by ``(persona, server)`` for the
    profile. Calls with no ``persona`` are ignored (nothing to baseline).
    """
    session_calls: dict[tuple[str, str, str], list[ScoredCall]] = defaultdict(list)
    for call in calls:
        if not call.persona:
            continue
        session_calls[(call.persona, call.server, call.run_id)].append(call)

    by_persona_server: dict[tuple[str, str], list[list[ScoredCall]]] = defaultdict(list)
    for (persona, server, _run_id), session in session_calls.items():
        by_persona_server[(persona, server)].append(session)

    baselines: dict[str, AgentBaseline] = {}
    for (persona, server), sessions in by_persona_server.items():
        tools: set[str] = set()
        max_sensitivity = 0
        sizes: list[int] = []
        for session in sessions:
            sizes.append(len(session))
            for call in session:
                tools.add(call.tool)
                if call.sensitivity is not None:
                    max_sensitivity = max(max_sensitivity, call.sensitivity)
        mean_size = statistics.fmean(sizes)
        stdev_size = statistics.pstdev(sizes) if len(sizes) > 1 else 0.0
        key = _baseline_key(persona, server)
        baselines[key] = AgentBaseline(
            key=key,
            known_tools=frozenset(tools),
            max_sensitivity=max_sensitivity,
            mean_calls_per_session=mean_size,
            stdev_calls_per_session=stdev_size,
            n_sessions=len(sessions),
        )
    return baselines


def score_deviation(
    call: ScoredCall,
    baseline: AgentBaseline | None,
    session_size: int | None = None,
) -> tuple[str, str]:
    """Score one call's deviation from its persona's baseline.

    Returns ``(band, reason)``. ``band`` is one of :data:`mcp_security.param_scoring
    .combine.BANDS`; ``"low"`` means no anomaly detected (or no baseline exists
    to judge against — an honest non-signal, never a fabricated escalation).
    """
    if baseline is None:
        return _NO_SIGNAL_BAND, "no baseline for this persona/server"

    if call.tool not in baseline.known_tools:
        return "high", f"tool '{call.tool}' never used by this persona before"

    if call.sensitivity is not None and call.sensitivity > baseline.max_sensitivity:
        delta = call.sensitivity - baseline.max_sensitivity
        band = "critical" if delta >= 2 else "high"
        return band, (
            f"asset sensitivity {call.sensitivity} exceeds this persona's prior "
            f"max of {baseline.max_sensitivity}"
        )

    if session_size is not None and baseline.stdev_calls_per_session > 0:
        z = (session_size - baseline.mean_calls_per_session) / baseline.stdev_calls_per_session
        if z > BURST_Z_THRESHOLD:
            return "medium", (
                f"session size {session_size} is {z:.1f} std devs above this "
                f"persona's mean of {baseline.mean_calls_per_session:.1f}"
            )

    return _NO_SIGNAL_BAND, "consistent with persona baseline"
