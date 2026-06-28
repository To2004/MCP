"""Input-parameter risk scoring.

A third risk dimension on top of the (tool, asset) scan: how much a call's input
*parameter values* ask for. The rules live in ``docs/standards/parameter-scoring.md``
(which also serves as the LLM prompt); the LLM derives a per-tool rubric (which
parameters carry magnitude, their base rank, and numeric cutoffs), and this package
applies that rubric to concrete calls deterministically and combines the result
with the (tool, asset) band.
"""

from .apply import ParamScore, score_call_params
from .combine import BAND_RANK, combine_avg, escalate
from .rubric import Cutoff, ParamRubric, ToolRubric, value_band

__all__ = [
    "Cutoff",
    "ParamRubric",
    "ToolRubric",
    "value_band",
    "BAND_RANK",
    "combine_avg",
    "escalate",
    "ParamScore",
    "score_call_params",
]
