"""Fuse the static (tool, asset) band with the dynamic signals into one final band.

Reuses the framework's existing escalation arithmetic
(:func:`mcp_security.param_scoring.combine.escalate`): every dynamic signal can
only raise a call's risk above its static floor, never lower it — the same
rule already applied to parameter risk. See
:doc:`/project/dynamic-scoring-design` for why this composition, not a
weighted average, is the right one.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from mcp_security.call_scoring.score import ScoredCall
from mcp_security.param_scoring.combine import escalate

from .baseline import AgentBaseline, score_deviation
from .sequence import score_sequence

JudgeFn = Callable[[str, dict], "tuple[str, str] | None"]


@dataclass(frozen=True)
class DynamicVerdict:
    """One call's full scoring breakdown — every signal kept visible, not just the final band."""

    call: ScoredCall
    static_band: str
    baseline_band: str
    baseline_reason: str
    sequence_band: str
    sequence_reason: str
    judge_band: str | None
    judge_reason: str
    final_band: str


def score_session(
    session_calls: list[ScoredCall],
    baselines: dict[str, AgentBaseline],
    *,
    judge_fn: JudgeFn | None = None,
) -> list[DynamicVerdict]:
    """Score one ordered session's calls, combining static + all dynamic signals.

    ``session_calls`` must share one ``run_id`` and be in call order. ``judge_fn``
    is optional (e.g. :func:`mcp_security.dynamic.judge.judge_call`); when
    omitted, the LLM escalation stage is skipped entirely (never silently
    treated as "clean" — callers should record that it was skipped).
    """
    sequence_verdicts = score_sequence(session_calls)
    session_size = len(session_calls)
    verdicts: list[DynamicVerdict] = []

    for call, seq_verdict in zip(session_calls, sequence_verdicts):
        baseline = baselines.get(f"{call.persona}@{call.server}")
        baseline_band, baseline_reason = score_deviation(call, baseline, session_size)

        judge_band: str | None = None
        judge_reason = ""
        if judge_fn is not None:
            result = judge_fn(call.tool, _safe_args(call))
            if result is not None:
                judge_band, judge_reason = result

        static_band = call.final_band
        final_band = escalate(static_band, baseline_band)
        final_band = escalate(final_band, seq_verdict.band)
        if judge_band is not None:
            final_band = escalate(final_band, judge_band)

        verdicts.append(
            DynamicVerdict(
                call=call,
                static_band=static_band,
                baseline_band=baseline_band,
                baseline_reason=baseline_reason,
                sequence_band=seq_verdict.band,
                sequence_reason=seq_verdict.reason,
                judge_band=judge_band,
                judge_reason=judge_reason,
                final_band=final_band,
            )
        )

    return verdicts


def _safe_args(call: ScoredCall) -> dict:
    """Best-effort re-parse of a call's raw args for the judge stage (never raises)."""
    try:
        parsed = json.loads(call.args_raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
