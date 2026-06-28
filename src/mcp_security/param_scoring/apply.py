"""Apply a tool's parameter rubric to a concrete call — deterministically.

Reads each magnitude-bearing parameter's value from the call arguments per its
``extract`` rule, bands the value against the cutoffs, averages with the
parameter's ``base_rank`` to get the parameter risk, and returns the most severe
parameter risk for the call. The LLM is not used here — only the rubric it
produced (see :mod:`.derive`).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .combine import combine_avg, escalate
from .rubric import ParamRubric, ToolRubric, value_band

_LIMIT_RE = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class ParamScore:
    """The parameter-risk verdict for one call."""

    band: str | None  # None when no magnitude parameter applied
    top_param: str | None
    details: tuple[dict, ...]

    def combined_with(self, tool_asset_band: str) -> str:
        """Escalate the (tool, asset) band by the parameter risk (never lower it)."""
        if self.band is None:
            return tool_asset_band
        return escalate(tool_asset_band, self.band)


def _extract_value(param: ParamRubric, args: dict) -> float | None:
    """Read the parameter's numeric magnitude from ``args``; None if absent."""
    if param.extract == "boolean":
        return None  # handled separately (band comes from when_true)
    raw = args.get(param.name)
    if param.extract == "list_length":
        return float(len(raw)) if isinstance(raw, (list, tuple)) else None
    if param.extract == "parsed_limit":
        # An explicit LIMIT bounds the rows; its absence means unbounded (worst).
        for key in (param.name, "query", "sql", "statement"):
            text = args.get(key)
            if isinstance(text, str) and text.strip():
                match = _LIMIT_RE.search(text)
                return float(match.group(1)) if match else math.inf
        return None
    # "number"
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw.strip())
        except ValueError:
            return None
    return None


def _param_risk(param: ParamRubric, args: dict) -> dict | None:
    """Compute one parameter's risk on this call, or None if it does not apply."""
    if param.extract == "boolean":
        if not args.get(param.name):
            return None
        vband = param.when_true or "high"
        value: float | str = True
    else:
        value_num = _extract_value(param, args)
        if value_num is None:
            return None
        vband = value_band(value_num, param.cutoffs)
        value = value_num
    risk = combine_avg(param.base_rank, vband)
    return {
        "param": param.name,
        "value": value if value != math.inf else "unbounded",
        "value_band": vband,
        "base_rank": param.base_rank,
        "risk": risk,
    }


_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def score_call_params(args: dict, rubric: ToolRubric) -> ParamScore:
    """Score a call's parameters; the call's parameter risk is the most severe."""
    details = [d for p in rubric.parameters if (d := _param_risk(p, args)) is not None]
    if not details:
        return ParamScore(band=None, top_param=None, details=())
    top = max(details, key=lambda d: _RANK.get(d["risk"], 0))
    return ParamScore(band=top["risk"], top_param=top["param"], details=tuple(details))
