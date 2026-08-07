"""Runtime asset binding: which register asset does a given call actually touch?

The static arms answer "how risky is this tool"; a gate has to answer "which
asset is this call working on", and the answer lives in the call's arguments.
This package turns ``(tool, arguments)`` into a set of policy-register asset ids.

**No model runs here.** A gate decides in front of the server, on the call path,
so every mechanism is deterministic Python — dictionary lookup, regex, and
IDF-weighted token overlap. The scanner's LLM stages run at design time and
reach this package only as artifacts already on disk (the policy register, the
operation ladder). A resolution is reproducible, costs no tokens, and cannot be
moved by anything an attacker writes into an argument.

**Nothing here is written per server.** The container key, the tool that
enumerates containers, and the organization's own email domains are all
discovered from observed traffic (:mod:`discovery`), validated against the
policy register, and never named in code. The same module resolves a server kind
it has never seen.

See ``README.md`` in this directory for the method and the experiment it backs.
"""

from .discovery import Binding, Discovery, discover, discover_org_domains
from .resolver import AssetHit, AssetResolver, Level, Resolution, worst_severity

__all__ = [
    "AssetHit",
    "AssetResolver",
    "Binding",
    "Discovery",
    "Level",
    "Resolution",
    "discover",
    "discover_org_domains",
    "worst_severity",
]
