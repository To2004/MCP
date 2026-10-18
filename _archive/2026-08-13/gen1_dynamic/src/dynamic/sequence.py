"""Session-level sequence risk: what static and baseline scoring can't see per-call.

A "read a sensitive asset, then send it somewhere" sequence is critical even
when each call is individually medium. Static scoring is per-cell; the
per-agent baseline (:mod:`.baseline`) is per-call. This module is the one
signal that looks at a session's call *order*.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcp_security.call_scoring.score import ScoredCall
from mcp_security.param_scoring.combine import BANDS

# How many calls after a sensitive read an outbound-looking call still counts
# as part of the same read-then-send sequence.
SEQUENCE_WINDOW = 5

# A read is "sensitive" once its resolved asset sensitivity reaches this rank
# (asset_sensitivity is 1..5 in scan artifacts; see reports/scan/*.json).
SENSITIVE_READ_THRESHOLD = 4

_READ_HINTS = ("read", "get", "list", "describe", "search")
_OUTBOUND_HINTS = (
    "write", "send", "post", "share", "export", "mail", "publish", "push",
    "upload", "invite", "merge", "delete", "move", "create",
)

_NO_SIGNAL_BAND = BANDS[0]


def _is_read_like(tool: str) -> bool:
    lowered = tool.lower()
    return any(hint in lowered for hint in _READ_HINTS)


def _is_outbound_like(tool: str) -> bool:
    lowered = tool.lower()
    return any(hint in lowered for hint in _OUTBOUND_HINTS)


@dataclass(frozen=True)
class SequenceVerdict:
    """One call's sequence-risk verdict within its session."""

    band: str
    reason: str


def score_sequence(session_calls: list[ScoredCall]) -> list[SequenceVerdict]:
    """Score every call in one ordered session for read-then-send risk.

    ``session_calls`` must already be in call order (same ``run_id``). Returns
    one :class:`SequenceVerdict` per input call, same order.
    """
    verdicts: list[SequenceVerdict] = []
    last_sensitive_read_index: int | None = None
    last_sensitive_read_asset: str | None = None

    for index, call in enumerate(session_calls):
        is_sensitive_read = _is_read_like(call.tool) and (
            call.sensitivity is not None and call.sensitivity >= SENSITIVE_READ_THRESHOLD
        )
        if is_sensitive_read:
            last_sensitive_read_index = index
            last_sensitive_read_asset = call.asset
            verdicts.append(SequenceVerdict(_NO_SIGNAL_BAND, "sensitive read (tracked for sequence risk)"))
            continue

        in_window = (
            last_sensitive_read_index is not None
            and index - last_sensitive_read_index <= SEQUENCE_WINDOW
        )
        if in_window and _is_outbound_like(call.tool):
            verdicts.append(
                SequenceVerdict(
                    "critical",
                    f"outbound-looking call '{call.tool}' within {index - last_sensitive_read_index} "
                    f"calls of reading sensitive asset '{last_sensitive_read_asset}'",
                )
            )
            continue

        verdicts.append(SequenceVerdict(_NO_SIGNAL_BAND, "no sequence pattern matched"))

    return verdicts
