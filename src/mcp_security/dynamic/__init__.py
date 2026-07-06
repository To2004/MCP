"""Dynamic (runtime) scoring: agent-log behavioral signal, fused with the static band.

See :doc:`/project/dynamic-scoring-design` for the model. Static scoring
(:mod:`mcp_security.call_scoring`) answers "how bad would this call be"; this
package answers "how abnormal is this call, from this agent, in this session" —
from captured logs, not a benchmark — and fuses the two via
:func:`mcp_security.dynamic.combine.score_session`.
"""

from .baseline import AgentBaseline, build_baselines, score_deviation
from .combine import DynamicVerdict, score_session
from .sequence import score_sequence

__all__ = [
    "AgentBaseline",
    "build_baselines",
    "score_deviation",
    "DynamicVerdict",
    "score_session",
    "score_sequence",
]
