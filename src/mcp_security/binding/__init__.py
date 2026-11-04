"""Runtime asset binding: which register asset does a given call actually touch?

The static arms answer "how risky is this tool"; a gate has to answer "which
asset is this call working on", and the answer lives in the call's arguments.
This package turns ``(tool, arguments)`` into a set of policy-register asset ids.

**No model runs here.** A gate decides in front of the server, on the call path,
so every mechanism is deterministic Python — dictionary lookup, regex, and
IDF-weighted token overlap. The scanner's LLM stages run at design time and
reach this package only as artifacts already on disk (the policy register, the
operation ladder). A resolution is reproducible and costs no tokens. When the
scan marks each tool's target inputs (``tool_targets``, AI-3), free text cannot
change either asset; only the target inputs' own values can. Without them the
priced asset's match reads every argument string, as it always has (v1-v4).

**Two assets per call (AI-1).** The *priced asset* (:mod:`scoring`) is the worst
register asset the target inputs do not rule out, and sets R_static. The
*touched asset* (:mod:`touched_asset`) is the container the target inputs name,
with its registered sensitivity and exposure, or a keyed pseudonym, or none; it
is what the behaviour engine's history holds (v5).

**Nothing here is written per server.** The container key, the tool that
enumerates containers, and the organization's own email domains are all
discovered from observed traffic (:mod:`discovery`), validated against the
policy register, and never named in code. The same module resolves a server kind
it has never seen.

See ``README.md`` in this directory for the method and the experiment it backs.
"""

from .discovery import Binding, Discovery, discover, discover_org_domains
from .resolver import AssetHit, AssetResolver, Level, Resolution, worst_severity
from .scoring import CallScore, ContainerSpec, MatrixScorer, TargetSpec, parse_tool_targets
from .touched_asset import (
    AssetRegister,
    Container,
    OperationKey,
    OperationSpec,
    Touched,
    TouchedAssetLookup,
    operation_key,
    parse_tool_operations,
)

__all__ = [
    "AssetHit",
    "AssetRegister",
    "AssetResolver",
    "Binding",
    "CallScore",
    "Container",
    "ContainerSpec",
    "Discovery",
    "Level",
    "MatrixScorer",
    "OperationKey",
    "OperationSpec",
    "Resolution",
    "TargetSpec",
    "Touched",
    "TouchedAssetLookup",
    "discover",
    "discover_org_domains",
    "operation_key",
    "parse_tool_operations",
    "parse_tool_targets",
    "worst_severity",
]
