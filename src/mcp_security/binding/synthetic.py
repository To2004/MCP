"""Generate one well-formed call per ``(tool, asset)`` the register homes.

The live corpus exercises whatever the personas happened to do: some register
cells get hundreds of calls, most get none. That measures a traffic distribution,
not a method. This module fills the matrix instead — every tool crossed with
every asset that tool can reach, several variants each — so a failure is
attributable to a *cell* rather than hidden by volume elsewhere.

Calls are built from the vendor's own input schema, so an argument exists only
because the tool declares it, and takes the shape the schema says. The generator
never consults the resolver: it decides what a call touches by *construction*
(this call names that container; this call carries an outside address), and the
resolver has to recover it from the arguments alone.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from mcp_security.static_scoring.server_policies import PolicyAssetRow

from .catalog import ToolSpec
from .identifiers import describes_egress, name_tokens, normalize_key

#: Parameter-name words meaning "a person", not "a container".
_RECIPIENT_WORDS = frozenset(
    {"attendee", "attendees", "recipient", "recipients", "email", "invitee", "participant",
     "participants", "user", "users", "member", "members"}
)
#: Parameter-name words meaning "a moment in time".
_TIME_WORDS = frozenset(
    {"time", "times", "date", "start", "end", "min", "max", "since", "until", "before",
     "after", "ts", "timestamp", "timemin", "timemax", "timezone"}
)
#: Parameter-name words meaning "free text to search for".
_QUERY_WORDS = frozenset({"query", "search", "filter", "q", "term", "keyword", "keywords"})

def _words(name: str, description: str = "") -> set[str]:
    """The word set of a parameter name, plus its description when one is given."""
    return set(name_tokens(name)) | set(name_tokens(description))

#: A domain that is not the organization's, used when a variant has to make an
#: egress asset genuinely in play rather than merely reachable.
OUTSIDE_DOMAIN = "external-counterparty.example"


@dataclass(frozen=True)
class SyntheticCall:
    """One generated call, plus the asset it was built to touch."""

    server: str
    tool: str
    args: dict
    #: The asset this call was constructed to reach. Ground truth by construction.
    target_asset: str
    #: Which construction made it so, for reading a failure without re-deriving it.
    shape: str
    variant: int = 0


@dataclass
class _Fixture:
    """Deterministic value pools, so a run reproduces exactly."""

    container_ids: dict[str, str]
    org_domain: str
    rng: random.Random = field(default_factory=lambda: random.Random(20260805))


def _resolve_branch(spec: dict) -> dict:
    """Collapse a ``anyOf``/``oneOf`` schema to its first concrete branch."""
    for key in ("anyOf", "oneOf", "allOf"):
        branches = spec.get(key)
        if branches:
            return _resolve_branch(branches[0]) | {
                k: v for k, v in spec.items() if k not in {"anyOf", "oneOf", "allOf"}
            }
    return spec


def _scalar_for(
    name: str, spec: dict, fixture: _Fixture, *, outside: bool, variant: int = 0
) -> object:
    """A plausible value for one parameter, driven by its schema and its name."""
    spec = _resolve_branch(spec)
    enum = spec.get("enum")
    if enum:
        # Round-robin rather than always the first value, so a tool that
        # separates its assets by mode gets every mode exercised.
        return enum[variant % len(enum)]
    kind = spec.get("type", "string")
    if kind in {"number", "integer"}:
        return 10
    if kind == "boolean":
        return False
    words = _words(name, str(spec.get("description", "")))
    if words & _RECIPIENT_WORDS:
        domain = OUTSIDE_DOMAIN if outside else fixture.org_domain
        return f"person@{domain}"
    if set(name_tokens(name)) & _TIME_WORDS:
        return "2026-09-01T00:00:00Z"
    if words & _QUERY_WORDS:
        return "status"
    return "value"


def _build_args(
    tool: ToolSpec,
    container_key: str | None,
    container_id: str | None,
    fixture: _Fixture,
    *,
    optional_share: float,
    outside: bool,
    variant: int = 0,
) -> dict:
    """Arguments for one call: every required parameter, some optional ones.

    When the call is built to reach an egress asset, any recipient parameter is
    forced in: a call that is supposed to send mail outside the organization has
    to actually name someone outside, or it is not that call.
    """
    args: dict = {}
    # A tool with no container parameter is still scoped by its caller, who
    # writes the identifier into whatever free-text argument the tool does
    # take: ``sql="SELECT * FROM api_keys"``, ``q="repo:acme/api password"``.
    # Reproducing that is what makes such a cell a fair test rather than an
    # unscoped call nobody would send.
    declares_container = any(
        container_key is not None and normalize_key(n) == container_key
        for n in tool.properties
    )
    embed_into = (
        None
        if declares_container or container_id is None
        else _free_text_parameter(tool)
    )
    for name, spec in tool.properties.items():
        normalized = normalize_key(name)
        is_container = container_key is not None and normalized == container_key
        recipient = bool(_words(name, str(spec.get("description", ""))) & _RECIPIENT_WORDS)
        if not is_container and name not in tool.required:
            if not (outside and recipient) and fixture.rng.random() > optional_share:
                continue
        if is_container:
            if container_id is None:
                continue
            resolved = _resolve_branch(spec)
            args[name] = (
                [container_id] if resolved.get("type") == "array" else container_id
            )
            continue
        value = _scalar_for(name, spec, fixture, outside=outside, variant=variant)
        if name == embed_into and container_id is not None:
            value = f"{value} {container_id}"
        resolved = _resolve_branch(spec)
        args[name] = [value] if resolved.get("type") == "array" else value
    if embed_into and embed_into not in args and container_id is not None:
        args[embed_into] = f"{_scalar_for(embed_into, tool.properties[embed_into], fixture, outside=outside)} {container_id}"
    return args


def _free_text_parameter(tool: ToolSpec) -> str | None:
    """The parameter a caller would write a scope into: required, string, free text."""
    for name, spec in tool.properties.items():
        resolved = _resolve_branch(spec)
        if resolved.get("type", "string") != "string" or resolved.get("enum"):
            continue
        own = set(name_tokens(name))
        if own & _TIME_WORDS or own & _RECIPIENT_WORDS:
            continue
        if name in tool.required or own & _QUERY_WORDS or "sql" in own:
            return name
    return None


def generate(
    server: str,
    rows: list[PolicyAssetRow],
    tools: dict[str, ToolSpec],
    container_ids: dict[str, str],
    container_key: str,
    *,
    org_domain: str = "org.example",
    variants: int = 10,
) -> list[SyntheticCall]:
    """One batch of calls per ``(tool, asset)`` cell the register homes.

    ``container_key`` and ``container_ids`` are the given key table: which
    parameter carries a container identifier, and what each identifier means.
    Both are inputs — the premise of this harness is that the keys are known, so
    nothing here has to infer a parameter name, and no parameter name for any
    particular server appears in this module.

    Assets absent from ``container_ids`` are not containers,
    so a call targeting one still has to name *some* container to be well formed;
    the generator picks one the same tool reaches, which is what an agent would
    do and what makes the cell a fair test.
    """
    fixture = _Fixture(container_ids=container_ids, org_domain=org_domain)
    by_asset = {row.asset_id: row for row in rows}
    reach: dict[str, list[str]] = {}
    for row in rows:
        for tool_name in row.tools:
            reach.setdefault(tool_name, []).append(row.asset_id)

    calls: list[SyntheticCall] = []
    for row in rows:
        for tool_name in row.tools:
            tool = tools.get(tool_name)
            if tool is None:
                continue
            siblings = [a for a in reach.get(tool_name, ()) if a in container_ids]
            egress = describes_egress(by_asset[row.asset_id].description)
            for variant in range(variants):
                if row.asset_id in container_ids:
                    container_id = container_ids[row.asset_id]
                    shape = "names its own container"
                elif siblings:
                    container_id = container_ids[siblings[variant % len(siblings)]]
                    shape = "names a sibling container; target is a facet"
                else:
                    container_id = None
                    shape = "no container exists for this tool"
                calls.append(
                    SyntheticCall(
                        server=server,
                        tool=tool_name,
                        args=_build_args(
                            tool,
                            normalize_key(container_key),
                            container_id,
                            fixture,
                            optional_share=0.25 + 0.75 * (variant % 4) / 3,
                            outside=egress,
                            variant=variant,
                        ),
                        target_asset=row.asset_id,
                        shape=shape + (" + outside recipient" if egress else ""),
                        variant=variant,
                    )
                )
    return calls


__all__ = ["OUTSIDE_DOMAIN", "SyntheticCall", "generate"]
