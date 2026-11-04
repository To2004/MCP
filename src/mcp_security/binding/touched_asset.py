"""The touched asset and the operation key: what the behaviour engine compares (v5).

A call has two assets (AI-1). The **priced asset** is the worst register asset its target
inputs do not rule out; it sets R_static and stays in :mod:`scoring`. The **touched asset**
is the container the call's target inputs name, and it is what the engine's history holds:

- a register id, with its registered sensitivity and exposure, when the register vouches
  for the match: an exact canonical id, or one unique name match against containers the
  scan declares (AI-13);
- a keyed pseudonym ``c:<hmac>``, with no sensitivity, otherwise: the value names no
  register id, names several, only resembles a container the register merely inferred (a
  data-class row such as ``branch-heads`` can share a repository's words), or lives under
  an owner the deployment does not register (someone else's fork or mirror). A pseudonym
  never has a sensitivity, so it can never fire a floor;
- none, when the call gives no target value.

Only the scan-marked target inputs are read (AI-3), so free text cannot change either
asset; only the target inputs' own values can. A call that names several containers, such
as a fork's source and destination, returns them all (AI-12); the most sensitive one is
the primary. Exposure (public, internal or private) comes from the register or from the
deployment's list of registered repositories, and the owner from the owner input, as a
pseudonym ``o:<hmac>`` (EXP-1). The scan should declare a fork's destination as the
repository GitHub creates, ``{"inputs": ["organization", "repo"], "owner": "organization"}``;
with the deployment's owners known, a fork out of the organisation then names two
containers under two owners.

The operation key (AI-7) splits a tool that bundles operations behind a selector input,
such as ``issue_write`` with ``method`` create or update, into one key per operation, each
labelled read or write.

Everything here is a pure lookup: no model, no state, no traffic. The worst-case path the
gateway uses for v1-v4 is :class:`scoring.MatrixScorer` and is untouched by this module.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import NamedTuple, Protocol

from mcp_security.static_scoring.server_policies import PolicyAssetRow

from .identifiers import canonical_id, describes_call_target, identifier_candidates, name_coverage
from .scoring import NAME_MATCH_FLOOR, ContainerSpec, TargetSpec, parse_tool_targets

#: How a container was identified. Only NAMED carries a register id and a sensitivity.
NAMED, UNREGISTERED, AMBIGUOUS, NO_TARGET = "named", "unregistered", "ambiguous", "no-target"
#: How a NAMED container matched the register: by canonical id, or by one unique name.
EXACT, UNIQUE = "exact", "unique"
#: Exposure values, equal to ``behaviour.engine.PUBLIC``, ``INTERNAL`` and ``PRIVATE``.
PUBLIC, INTERNAL, PRIVATE = "public", "internal", "private"
EXPOSURES = (PUBLIC, INTERNAL, PRIVATE)
#: Operation labels, equal to ``behaviour.engine.READ`` and ``WRITE``.
READ, WRITE = "read", "write"
OPERATION_LABELS = (READ, WRITE)
#: The register flag that marks an asset as already published.
PUBLIC_FLAG = "public"
#: Registered sensitivity range (the scan's 1-5 ladder).
MIN_SENSITIVITY, MAX_SENSITIVITY = 1, 5
#: The scan's impact ladder: 4 = write, 5 = remove, 3 and below = read (framework.py's rule).
WRITE_IMPACT = 4
#: Pseudonym prefixes and length (spec AI-1: ``'c:' + HMAC_K(c)[:12]``).
CONTAINER_PREFIX, OWNER_PREFIX = "c:", "o:"
HANDLE_CHARS = 12
#: Joins the canonical target values of one container (``owner/repo``).
PATH_SEPARATOR = "/"
#: AI-7: ``tool:operation``, and the operation of a selector value the scan did not declare.
KEY_SEPARATOR, UNKNOWN_OPERATION = ":", "?"
#: AI-12: at most this many containers per call, and at most this many items read from one
#: list value, so a list-valued input cannot blow up a call's cost (DEP-7).
MAX_CONTAINERS_PER_CALL = 32
#: Scan fields read by :meth:`AssetRegister.from_scan` and :func:`parse_tool_operations`.
SENSITIVITY_FIELD, EXPOSURE_FIELD, CONTAINERS_FIELD = (
    "asset_sensitivity",
    "asset_exposure",
    "asset_containers",
)
SELECTOR_KEY, OPS_KEY, LABEL_KEY = "selector", "ops", "label"


class Pseudonyms(Protocol):
    """Anything that turns a value into a stable pseudonym, such as the gateway's
    ``Pseudonymizer`` (``gateway/pseudonym.py``), keyed by ``hash_key_env``."""

    @property
    def keyed(self) -> bool:
        """True when pseudonyms are keyed HMACs; False when they are plain hashes."""

    def of(self, value: str) -> str:
        """The pseudonym of ``value``; equal values give equal strings."""


# ── the register ────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AssetRegister:
    """What the touched-asset lookup knows about the organisation's assets.

    - ``sensitivity``: register id -> 1-5 (the scan's ``asset_sensitivity``);
    - ``exposure``: register id -> PUBLIC, INTERNAL or PRIVATE, where known;
    - ``containers``: the register ids that are standing containers a target value can
      name (not "what a call reaches" rows); None means every id in ``sensitivity``;
    - ``repositories``: the deployment's registered repositories, canonical container value
      (``owner/repo``) -> exposure, which also covers containers the register does not list;
    - ``owners``: the deployment's own owner values (an organisation, a workspace), to which
      the owner part of every registered repository is added. When any are known, a
      container under another owner never names a register asset; when none are, a
      register name names its asset under any owner;
    - ``containers_inferred``: True when ``containers`` was inferred from register rows that
      also hold data classes, because the scan declares none. A name match against such a
      set is a resemblance, not a naming, so only an exact id names an asset.
    """

    sensitivity: Mapping[str, int]
    exposure: Mapping[str, str] = field(default_factory=dict)
    containers: frozenset[str] | None = None
    repositories: Mapping[str, str] = field(default_factory=dict)
    owners: frozenset[str] = frozenset()
    containers_inferred: bool = False

    def __post_init__(self) -> None:
        for asset, level in self.sensitivity.items():
            if isinstance(level, bool) or not isinstance(level, int):
                raise ValueError(f"sensitivity of {asset!r} must be an int, not {level!r}")
            if not MIN_SENSITIVITY <= level <= MAX_SENSITIVITY:
                raise ValueError(f"sensitivity of {asset!r} is {level}, outside 1-5")
        for name, mapping in (("exposure", self.exposure), ("repositories", self.repositories)):
            bad = {k: v for k, v in mapping.items() if v not in EXPOSURES}
            if bad:
                raise ValueError(f"{name} values must be one of {EXPOSURES}: {bad}")
        containers = frozenset(self.sensitivity if self.containers is None else self.containers)
        unknown = containers - set(self.sensitivity)
        if unknown:
            raise ValueError(f"containers not in the register: {sorted(unknown)}")
        repositories = {canonical_id(k): v for k, v in self.repositories.items()}
        owners = _canonical_owners(self.owners) | {
            canonical_id(key.rsplit(PATH_SEPARATOR, 1)[0])
            for key in repositories
            if PATH_SEPARATOR in key
        }
        object.__setattr__(self, "sensitivity", MappingProxyType(dict(self.sensitivity)))
        object.__setattr__(self, "exposure", MappingProxyType(dict(self.exposure)))
        object.__setattr__(self, "containers", containers)
        object.__setattr__(self, "repositories", MappingProxyType(repositories))
        object.__setattr__(self, "owners", frozenset(owners))

    @classmethod
    def from_scan(
        cls,
        scan: Mapping[str, object],
        repositories: Mapping[str, str] | None = None,
        *,
        rows: Iterable[PolicyAssetRow] | None = None,
        owners: Iterable[str] = (),
    ) -> AssetRegister:
        """The register a scan artifact carries: ``asset_sensitivity``, and the optional
        ``asset_exposure`` and ``asset_containers`` fields (EXP-1).

        ``rows`` are the policy register's parsed rows. A row flagged ``public`` is PUBLIC
        unless the scan says otherwise. Without ``asset_containers`` the containers are
        inferred: the rows the scan gave a sensitivity, except those that describe what a
        call reaches ("What a ... targets"), or every id when no rows are given. Give the
        rows whenever the scan lacks the field, since every id includes those rows.
        """
        sensitivity = dict(scan.get(SENSITIVITY_FIELD) or {})
        rows = None if rows is None else list(rows)
        exposure = (
            {} if rows is None else {r.asset_id: PUBLIC for r in rows if PUBLIC_FLAG in r.flags}
        )
        exposure.update(scan.get(EXPOSURE_FIELD) or {})
        declared = scan.get(CONTAINERS_FIELD)
        if declared is not None:
            containers: frozenset[str] | None = frozenset(declared)
        elif rows is not None:
            containers = frozenset(
                r.asset_id
                for r in rows
                if r.asset_id in sensitivity and not describes_call_target(r.description)
            )
        else:
            containers = None
        return cls(
            sensitivity=sensitivity,
            exposure=exposure,
            containers=containers,
            repositories=dict(repositories or {}),
            owners=_canonical_owners(owners),
            containers_inferred=declared is None,
        )

    @classmethod
    def from_rows(
        cls,
        rows: Iterable[PolicyAssetRow],
        sensitivity: Mapping[str, int],
        repositories: Mapping[str, str] | None = None,
        *,
        owners: Iterable[str] = (),
    ) -> AssetRegister:
        """The register from the policy's parsed rows plus the scan's sensitivities: a scan
        without ``asset_containers`` (see :meth:`from_scan`). The containers are inferred,
        since the rows still mix standing containers with data classes."""
        return cls.from_scan(
            {SENSITIVITY_FIELD: dict(sensitivity)}, repositories, rows=rows, owners=owners
        )


def _canonical_owners(owners: Iterable[str]) -> frozenset[str]:
    """Owner values in canonical form; raises ValueError on a bare string or an empty name."""
    if isinstance(owners, (str, bytes)):
        raise ValueError(f"owners must be a collection of names, not {owners!r}")
    owners = list(owners)
    canonical = frozenset(canonical_id(o) if isinstance(o, str) else "" for o in owners)
    if "" in canonical:
        raise ValueError(f"every owner must be a non-empty name, not {owners!r}")
    return canonical


# ── the result ──────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Container:
    """One container a call names.

    ``asset`` is a register id when ``basis`` is NAMED, else a ``c:`` pseudonym. Only a
    NAMED container has a ``sensitivity``. ``match`` says how it was named (EXACT or
    UNIQUE). ``candidates`` lists, for audit, the register ids an AMBIGUOUS value matched,
    or the one id an UNREGISTERED value only resembled (a name match against inferred
    containers).
    """

    asset: str
    basis: str
    sensitivity: int | None = None
    exposure: str | None = None
    owner: str | None = None
    match: str | None = None
    candidates: tuple[str, ...] = ()

    @property
    def floor_eligible(self) -> bool:
        """A floor may fire only on a match the register vouches for (AI-13)."""
        return self.basis == NAMED


@dataclass(frozen=True)
class Touched:
    """Every container one call names, the primary first (AI-12). Empty: no target value.

    Build it with :meth:`from_containers`, which puts the most sensitive container first.
    """

    containers: tuple[Container, ...] = ()

    @classmethod
    def from_containers(cls, containers: Iterable[Container]) -> Touched:
        """Order the containers: the most sensitive first (the first named on a tie),
        then the rest in the order the call named them."""
        ordered = list(containers)
        if not ordered:
            return cls()
        primary = max(range(len(ordered)), key=lambda i: (ordered[i].sensitivity or 0, -i))
        return cls((ordered[primary], *ordered[:primary], *ordered[primary + 1 :]))

    @property
    def primary(self) -> Container | None:
        """The container asset rarity and the floors look at: the most sensitive one."""
        return self.containers[0] if self.containers else None

    @property
    def asset(self) -> str | None:
        """The primary's register id or pseudonym; None without a target value."""
        return self.primary.asset if self.primary else None

    @property
    def sensitivity(self) -> int | None:
        """The primary's registered sensitivity; None unless it was NAMED."""
        return self.primary.sensitivity if self.primary else None

    @property
    def exposure(self) -> str | None:
        """The primary's exposure, where known."""
        return self.primary.exposure if self.primary else None

    @property
    def owner(self) -> str | None:
        """The primary's owner pseudonym, where the scan marks an owner input. The other
        containers' owners, such as a fork destination's, are in :attr:`containers`."""
        return self.primary.owner if self.primary else None

    @property
    def basis(self) -> str:
        """The primary's basis, or NO_TARGET."""
        return self.primary.basis if self.primary else NO_TARGET

    @property
    def more_assets(self) -> tuple[str, ...]:
        """The other containers' assets, each once, never the primary's (Breadth, Sweep)."""
        if not self.containers:
            return ()
        rest = (c.asset for c in self.containers[1:] if c.asset != self.asset)
        return tuple(dict.fromkeys(rest))

    @property
    def floor_eligible(self) -> bool:
        """True when the primary may fire a floor."""
        return self.primary is not None and self.primary.floor_eligible

    def message_fields(self) -> dict[str, object]:
        """The ``behaviour.Message`` fields this sets: ``Message(..., **fields)``."""
        return {
            "asset": self.asset,
            "sensitivity": self.sensitivity,
            "exposure": self.exposure,
            "owner": self.owner,
            "more_assets": self.more_assets,
        }


# ── the lookup ──────────────────────────────────────────────────────────────────────────


class TouchedAssetLookup:
    """Resolves a call's touched asset against one route's register (AI-1, AI-2, AI-13).

    ``targets`` is the scan's ``tool_targets`` (None: no tool has target inputs, so every
    call has no touched asset). ``pseudonyms`` is required: give the gateway's keyed
    pseudonymizer, the same one live and offline, so the handles agree. An unkeyed one
    (``Pseudonymizer(None)``) is a deliberate choice, since a repository name can be
    recovered from its plain hash; :attr:`keyed` says which one a lookup holds.

    The lookup is an exact canonical-id dict first, O(1) per value, then a linear
    ``name_coverage`` pass over the register's containers for a value no id equals. The
    spec's token index and memo are deferred, so the name pass has no time bound: in
    synthetic development timings it costs about 20 us per container, which reaches DEP-7's
    5 ms budget at a few hundred containers.
    """

    def __init__(
        self,
        register: AssetRegister,
        targets: Mapping[str, object] | None,
        pseudonyms: Pseudonyms,
    ) -> None:
        self.register = register
        self._targets = parse_tool_targets(targets)
        self._pseudonyms = pseudonyms
        self._containers = tuple(sorted(register.containers or ()))
        exact: dict[str, list[str]] = {}
        for asset in self._containers:
            exact.setdefault(canonical_id(asset), []).append(asset)
        self._exact = {key: tuple(ids) for key, ids in exact.items()}

    @property
    def keyed(self) -> bool:
        """True when the container and owner handles are keyed HMACs."""
        return self._pseudonyms.keyed

    def target_spec(self, tool: str) -> TargetSpec | None:
        """The tool's target inputs, or None when the scan declares none."""
        return self._targets.get(tool) if self._targets else None

    def touched(self, tool: str, args: object) -> Touched:
        """Every container the call's target inputs name, resolved."""
        spec = self.target_spec(tool)
        if spec is None or not isinstance(args, Mapping):
            return Touched()
        return Touched.from_containers(
            self.container(*named) for named in named_containers(spec, args)
        )

    def container(self, value: str, owner: str | None = None, name: str | None = None) -> Container:
        """One canonical container value (``owner/repo``) with its owner value and its own
        name (see :meth:`match`), resolved."""
        kind, ids = self.match(value, owner, name)
        handle = None if owner is None else self._handle(OWNER_PREFIX, owner)
        if kind is not None:
            asset = ids[0]
            exposure = self.register.exposure.get(asset) or self.register.repositories.get(value)
            return Container(asset, NAMED, self.register.sensitivity[asset], exposure, handle, kind)
        return Container(
            self._handle(CONTAINER_PREFIX, value),
            AMBIGUOUS if len(ids) > 1 else UNREGISTERED,
            exposure=self.register.repositories.get(value),
            owner=handle,
            candidates=ids,
        )

    def match(
        self, value: str, owner: str | None = None, name: str | None = None
    ) -> tuple[str | None, tuple[str, ...]]:
        """The register ids a canonical container value names, and how.

        ``owner`` is the value's owner part and ``name`` the rest, the container's own name;
        by default the value without a leading ``owner/``.

        1. A value under an owner the deployment does not register names nothing, and so
           does a value that is only an owner: an owner says where a container lives, not
           which one it is.
        2. Exact: the value, then its tails with leading qualifiers dropped
           (``helios/helios-public-site`` -> ``helios-public-site``), against the canonical
           ids; the first spelling that hits wins. A leading-segment spelling is never tried,
           since it may be an owner, so a path reaches a registered folder only by step 3
           (hierarchy containers are out of scope for the exact pass).
        3. Name: every container whose id the value covers to :data:`NAME_MATCH_FLOOR`,
           except one that the owner covers and the name does not.

        Returns (EXACT or UNIQUE, (id,)) for a match the register vouches for, (None, ids)
        for several ids or for a name match against inferred containers, and (None, ())
        for none.
        """
        own_name = _own_name(value, owner) if name is None else name
        if not own_name or self._foreign(value, owner):
            return None, ()
        for spelling in identifier_candidates(value):
            if spelling != value and not value.endswith(PATH_SEPARATOR + spelling):
                continue  # a leading-segment spelling: possibly an owner, never tried
            ids = self._exact.get(spelling)
            if ids:
                return (EXACT if len(ids) == 1 else None), ids
        ids = tuple(
            asset
            for asset in self._containers
            if _covers(value, asset)
            and (owner is None or _covers(own_name, asset) or not _covers(owner, asset))
        )
        vouched = len(ids) == 1 and not self.register.containers_inferred
        return (UNIQUE if vouched else None), ids

    def _foreign(self, value: str, owner: str | None) -> bool:
        """True for a container under an owner the deployment does not register."""
        owners = self.register.owners
        return (
            owner is not None
            and bool(owners)
            and owner not in owners
            and value not in self.register.repositories
        )

    def _handle(self, prefix: str, value: str) -> str:
        return prefix + self._pseudonyms.of(value)[:HANDLE_CHARS]


def _covers(text: str, asset: str) -> bool:
    """Whether ``text`` names register id ``asset`` by its words (:func:`name_coverage`)."""
    return name_coverage(text, asset) >= NAME_MATCH_FLOOR


def _own_name(value: str, owner: str | None) -> str:
    """The value without a leading ``owner/`` qualifier; empty when it is only the owner."""
    if owner is None:
        return value
    if value == owner:
        return ""
    prefix = owner + PATH_SEPARATOR
    return value[len(prefix) :] if value.startswith(prefix) else value


class ContainerValue(NamedTuple):
    """One container value a call names, canonical: ``value`` joins its target values with
    ``/`` (``helios/website``), ``owner`` is its owner input's value or None, and ``name``
    is the value without the owner, the container's own name (``website``)."""

    value: str
    owner: str | None
    name: str


def named_containers(spec: TargetSpec, args: Mapping[str, object]) -> list[ContainerValue]:
    """The canonical container values a call names, in the order it names them.

    A container needs a value for every one of its inputs; a list value names one container
    per item (AI-12). Each value is canonicalised (``identifiers.canonical_id``) and the
    values are joined with ``/``. Duplicates count once, and at most
    :data:`MAX_CONTAINERS_PER_CALL` are returned.
    """
    found: dict[str, ContainerValue] = {}
    for container in spec.containers:
        columns = [_values_of(args.get(name)) for name in container.inputs]
        if not all(columns):
            continue
        owner_at = None if container.owner is None else container.inputs.index(container.owner)
        for combination in itertools.product(*columns):
            if len(found) >= MAX_CONTAINERS_PER_CALL:
                return list(found.values())
            value = PATH_SEPARATOR.join(combination)
            if value in found:
                continue
            if owner_at is None:
                found[value] = ContainerValue(value, None, value)
            else:
                rest = combination[:owner_at] + combination[owner_at + 1 :]
                found[value] = ContainerValue(
                    value, combination[owner_at], PATH_SEPARATOR.join(rest)
                )
    return list(found.values())


def _values_of(value: object) -> list[str]:
    """A target input's canonical values, each once: one for a scalar, one per item for a
    list. Only a list's first :data:`MAX_CONTAINERS_PER_CALL` items are read, a bound on a
    call's cost (DEP-7), so an item past them names nothing."""
    items = value[:MAX_CONTAINERS_PER_CALL] if isinstance(value, (list, tuple)) else (value,)
    out: dict[str, None] = {}
    for item in items:
        if isinstance(item, int) and not isinstance(item, bool):
            item = str(item)
        if isinstance(item, str) and (canonical := canonical_id(item)):
            out[canonical] = None
    return list(out)


# ── the operation key (AI-7) ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OperationSpec:
    """A tool's operations (the scan's ``tool_operations`` entry): its selector input, a
    read or write label per selector value, and an optional label for the tool itself."""

    selector: str | None = None
    ops: Mapping[str, str] = field(default_factory=dict)
    label: str | None = None

    def __post_init__(self) -> None:
        labels = [*self.ops.values(), *([] if self.label is None else [self.label])]
        if any(label not in OPERATION_LABELS for label in labels):
            raise ValueError(f"operation labels must be {OPERATION_LABELS}: {labels}")
        if self.ops and self.selector is None:
            raise ValueError("operations need a selector input")
        object.__setattr__(self, "ops", MappingProxyType(dict(self.ops)))


@dataclass(frozen=True)
class OperationKey:
    """The engine's tool key (``tool`` or ``tool:operation``) and its read/write label."""

    key: str
    label: str | None


def parse_tool_operations(raw: Mapping[str, object] | None) -> dict[str, OperationSpec]:
    """The scan's ``tool_operations``: ``{tool: {"selector": input, "ops": {value: read |
    write}, "label": read | write}}``, every key optional. None gives no operations."""
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError(f"tool_operations must be a mapping, not {type(raw)}")
    out = {}
    for tool, entry in raw.items():
        if isinstance(entry, OperationSpec):
            out[tool] = entry
            continue
        if not isinstance(entry, Mapping):
            raise ValueError(f"tool_operations[{tool!r}] must be a mapping, not {entry!r}")
        ops = entry.get(OPS_KEY) or {}
        if not isinstance(ops, Mapping):
            raise ValueError(f"tool_operations[{tool!r}].{OPS_KEY} must be a mapping")
        out[tool] = OperationSpec(entry.get(SELECTOR_KEY), ops, entry.get(LABEL_KEY))
    return out


def operation_key(
    tool: str,
    args: object,
    operations: Mapping[str, OperationSpec],
    impact: int | None = None,
) -> OperationKey:
    """The tool key and label of one call (AI-7).

    The key is ``tool`` when the scan marks no selector, ``tool:v`` when the selector's
    value ``v`` is a declared operation, and ``tool:?`` otherwise, so an undeclared value
    never enters the history. The label is the declared operation's, else the tool's own,
    else today's rule from the tool's impact (write at 4 or above), else None.
    """
    spec = operations.get(tool)
    if spec is None or spec.selector is None:
        key, declared = tool, None
    else:
        value = args.get(spec.selector) if isinstance(args, Mapping) else None
        declared = value if isinstance(value, str) and value in spec.ops else None
        key = tool + KEY_SEPARATOR + (declared if declared is not None else UNKNOWN_OPERATION)
    if declared is not None:
        label = spec.ops[declared]
    elif spec is not None and spec.label is not None:
        label = spec.label
    elif impact is not None:
        label = WRITE if impact >= WRITE_IMPACT else READ
    else:
        label = None
    return OperationKey(key, label)


__all__ = [
    "AMBIGUOUS",
    "EXACT",
    "EXPOSURES",
    "INTERNAL",
    "NAMED",
    "NO_TARGET",
    "PRIVATE",
    "PUBLIC",
    "UNIQUE",
    "UNREGISTERED",
    "AssetRegister",
    "Container",
    "ContainerSpec",
    "ContainerValue",
    "OperationKey",
    "OperationSpec",
    "Pseudonyms",
    "TargetSpec",
    "Touched",
    "TouchedAssetLookup",
    "named_containers",
    "operation_key",
    "parse_tool_operations",
]
