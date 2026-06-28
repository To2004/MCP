"""Per-tool parameter rubric: which inputs carry magnitude, and their cutoffs.

The rubric is produced by the LLM (see :mod:`.derive`) following
``docs/standards/parameter-scoring.md`` and is then applied deterministically. A
:class:`ToolRubric` has one :class:`ParamRubric` per magnitude-bearing parameter;
each maps a parameter's *value* to a band via ascending :class:`Cutoff` thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .combine import BANDS

# How to read a parameter's magnitude from a call's arguments.
EXTRACTORS = ("number", "list_length", "parsed_limit", "boolean")


@dataclass(frozen=True)
class Cutoff:
    """A lower bound and the band that applies at or above it."""

    min: float
    band: str


@dataclass(frozen=True)
class ParamRubric:
    """Scoring rule for one magnitude-bearing input parameter."""

    name: str
    base_rank: str
    extract: str = "number"
    cutoffs: tuple[Cutoff, ...] = ()
    when_true: str | None = None  # band when a boolean parameter is true
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_rank": self.base_rank,
            "extract": self.extract,
            "cutoffs": [{"min": c.min, "band": c.band} for c in self.cutoffs],
            "when_true": self.when_true,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> ParamRubric:
        cutoffs = tuple(
            Cutoff(float(c["min"]), str(c["band"]))
            for c in raw.get("cutoffs", [])
            if str(c.get("band")) in BANDS and _is_number(c.get("min"))
        )
        return cls(
            name=str(raw.get("name", "")),
            base_rank=str(raw.get("base_rank", "low")),
            extract=str(raw.get("extract", "number")),
            cutoffs=tuple(sorted(cutoffs, key=lambda c: c.min)),
            when_true=raw.get("when_true") or None,
            reasoning=str(raw.get("reasoning", "")),
        )


@dataclass(frozen=True)
class ToolRubric:
    """All magnitude-bearing parameters for one tool."""

    tool_name: str
    parameters: tuple[ParamRubric, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {"tool_name": self.tool_name, "parameters": [p.to_dict() for p in self.parameters]}

    @classmethod
    def from_dict(cls, raw: dict) -> ToolRubric:
        return cls(
            tool_name=str(raw.get("tool_name", "")),
            parameters=tuple(ParamRubric.from_dict(p) for p in raw.get("parameters", [])),
        )


def _is_number(value: object) -> bool:
    try:
        float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True


def value_band(value: float, cutoffs: tuple[Cutoff, ...]) -> str:
    """Band a numeric value: the band of the highest cutoff it meets or exceeds.

    Below the smallest cutoff (or with no cutoffs) the value is ``low``.
    """
    band = "low"
    for cutoff in sorted(cutoffs, key=lambda c: c.min):
        if value >= cutoff.min:
            band = cutoff.band
    return band
