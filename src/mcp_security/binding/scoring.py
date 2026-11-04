"""Score one call against the scanned tool x asset severity matrix.

The matrix already prices every ``(tool, asset)`` pair at design time, so
scoring a call is not a modelling problem — it is a lookup, plus the question of
*which row*. Four steps, in order:

1. **Look the tool up.** Its candidates are the assets with a scored cell. The
   register's ``Tools`` column already excluded the rest, which is why no
   separate read-versus-write filter is needed here: a read verb simply has no
   cell against "what a write creates".
2. **One candidate — done.** The severity is that cell. Nothing about the
   arguments can change it, so the arguments are not read.
3. **Several candidates — read the arguments.** A key table if the deployment
   has one, then a direct string match of each argument value against the
   candidate asset ids.
4. **Take the worst.** Of whatever matched, or of every candidate when nothing
   did.

The guarantee is in step 4: as long as the asset actually touched is among the
candidates, the maximum over the chosen set cannot fall below its true cell. Not
knowing costs precision, never safety.

**Target inputs (AI-3).** When the scan carries ``tool_targets`` (the inputs that
name the container a call works on, such as a repository's owner and name), step 3
reads only those inputs' values. A decoy path or a body that mentions another
asset can then neither lower nor raise the priced asset; a tool with no declared
target input reads nothing and is priced at the worst case. A scan without
``tool_targets`` reads every argument string, exactly as before (v1-v4).

Nothing here retains state. No table is built, no traffic observed, no call
remembered.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .discovery import Discovery
from .identifiers import name_coverage

#: How much of an asset id an argument value must account for before the value
#: is taken to name that asset. High on purpose: this runs over every argument,
#: including free-text payload, so one shared word must never be enough.
NAME_MATCH_FLOOR = 0.8
#: The keys of the explicit form of one container in ``tool_targets``.
INPUTS_KEY, OWNER_KEY = "inputs", "owner"


@dataclass(frozen=True)
class ContainerSpec:
    """One container a call names: the target inputs whose values, joined in this order
    with ``/``, spell it (``owner``, ``repo`` -> ``helios/website``).

    ``owner`` is the input that names the container's owner (EXP-1), or None when none
    does. It must be one of ``inputs``.
    """

    inputs: tuple[str, ...]
    owner: str | None = None

    def __post_init__(self) -> None:
        if not self.inputs or not all(isinstance(n, str) and n for n in self.inputs):
            raise ValueError(f"a container needs one or more input names, not {self.inputs!r}")
        if self.owner is not None and self.owner not in self.inputs:
            raise ValueError(f"owner input {self.owner!r} is not one of {self.inputs!r}")


@dataclass(frozen=True)
class TargetSpec:
    """A tool's target inputs (the scan's ``tool_targets`` entry): one container, or
    several when the tool names a source and a destination (AI-12)."""

    containers: tuple[ContainerSpec, ...]

    def __post_init__(self) -> None:
        if not self.containers:
            raise ValueError("a target spec needs at least one container")

    @property
    def inputs(self) -> tuple[str, ...]:
        """Every target input of the tool, each once, in declared order."""
        return tuple(dict.fromkeys(n for c in self.containers for n in c.inputs))


def parse_tool_targets(raw: Mapping[str, object] | None) -> dict[str, TargetSpec] | None:
    """The scan's ``tool_targets`` field as :class:`TargetSpec` per tool; None stays None.

    Each tool's entry takes one of three shapes:

    - ``["owner", "repo"]``: one container. With two or more inputs the first is the
      owner, the qualifier prefix of ``owner/repo``; one input has no owner.
    - ``[["owner", "repo"], ["organization"]]``: several containers, each as above.
    - ``[{"inputs": ["owner", "repo"], "owner": "owner"}, ...]``: the explicit form, where
      ``owner`` may be null. The forms mix: a bare string is a one-input container.

    Raises :class:`ValueError` on any other shape, so a malformed scan fails at load.
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError(f"tool_targets must be a mapping of tool to inputs, not {type(raw)}")
    return {tool: _target_spec(tool, entry) for tool, entry in raw.items()}


def _target_spec(tool: object, entry: object) -> TargetSpec:
    """One tool's ``tool_targets`` entry, parsed."""
    if not isinstance(tool, str) or not tool:
        raise ValueError(f"tool_targets has a tool name that is not a string: {tool!r}")
    if isinstance(entry, TargetSpec):
        return entry
    if isinstance(entry, (str, bytes)) or not isinstance(entry, Sequence) or not entry:
        raise ValueError(f"tool_targets[{tool!r}] must be a non-empty list, not {entry!r}")
    if all(isinstance(item, str) for item in entry):
        return TargetSpec((_qualified(tuple(entry)),))
    return TargetSpec(tuple(_container_spec(tool, item) for item in entry))


def _container_spec(tool: str, item: object) -> ContainerSpec:
    """One container of a several-container entry."""
    if isinstance(item, str):
        return ContainerSpec((item,))
    if isinstance(item, Mapping):
        inputs = item.get(INPUTS_KEY)
        if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
            raise ValueError(f"tool_targets[{tool!r}]: {INPUTS_KEY!r} must be a list of names")
        return ContainerSpec(tuple(inputs), item.get(OWNER_KEY))
    if isinstance(item, Sequence) and not isinstance(item, bytes):
        if not all(isinstance(name, str) for name in item):
            raise ValueError(f"tool_targets[{tool!r}]: input names must be strings: {item!r}")
        return _qualified(tuple(item))
    raise ValueError(f"tool_targets[{tool!r}] has an entry of an unknown shape: {item!r}")


def _qualified(inputs: tuple[str, ...]) -> ContainerSpec:
    """The short form: with several inputs, the first one is the owner (qualifier prefix)."""
    return ContainerSpec(inputs, inputs[0] if len(inputs) > 1 else None)


@dataclass(frozen=True)
class CallScore:
    """What a gate acts on: one severity, and why it came out that way."""

    tool: str
    severity: float
    #: The assets that could not be ruled out. One entry when the call resolved.
    assets: tuple[str, ...]
    #: The asset whose cell set the severity.
    driver: str | None
    #: How the set was reached: ``no-cells``, ``sole-candidate``, ``named``,
    #: or ``unresolved`` (nothing in the arguments narrowed it).
    basis: str
    #: True when the severity is the worst case rather than the actual asset.
    worst_case: bool


class MatrixScorer:
    """Score calls against one server's scanned matrix.

    ``cells`` is the scanner's ``asset -> tool -> score`` table and ``bands`` its
    ``asset -> tool -> band`` twin; a pair banded ``na`` is one the register never
    homed, and is not a candidate. ``targets`` is the scan's ``tool_targets`` field
    (AI-3; see :func:`parse_tool_targets`), or None when the scan has none.
    """

    #: Band marking a cell the register never homed.
    UNSCORED_BAND = "na"

    def __init__(
        self,
        cells: dict[str, dict[str, float]],
        bands: dict[str, dict[str, str]],
        discovery: Discovery | None = None,
        targets: Mapping[str, object] | None = None,
    ) -> None:
        self._by_tool: dict[str, dict[str, float]] = {}
        for asset, row in cells.items():
            for tool, score in row.items():
                if bands.get(asset, {}).get(tool) == self.UNSCORED_BAND or score is None:
                    continue
                self._by_tool.setdefault(tool, {})[asset] = float(score)
        #: Optional and off by default. A deployment that keeps an
        #: identifier-to-asset table can supply one; nothing here builds or
        #: retains it.
        self._discovery = discovery
        #: AI-3: each tool's target inputs, or None to read every argument (v1-v4).
        self._targets = parse_tool_targets(targets)

    @property
    def reads_targets_only(self) -> bool:
        """True when the scan declared target inputs, so free text is never read."""
        return self._targets is not None

    def candidates(self, tool: str) -> dict[str, float]:
        """The assets this tool has a scored cell against, and their scores."""
        return dict(self._by_tool.get(tool, {}))

    def match_values(self, tool: str, args: object) -> list[str]:
        """The argument strings step 3 reads for this call, in order.

        Without target inputs, every scalar string in the arguments. With them, only the
        values of the tool's target inputs (list values flattened); none for a tool that
        declares no target input, so that tool is priced at the worst case.
        """
        if self._targets is None:
            return _strings_in(args)
        spec = self._targets.get(tool)
        if spec is None or not isinstance(args, Mapping):
            return []
        return _strings_in([args[name] for name in spec.inputs if name in args])

    def match_key(self, tool: str, args: object) -> str:
        """Everything :meth:`score` reads from the arguments, as a cache key.

        Without target inputs it is today's key, the whole argument JSON. With them it is
        only the target values (AI-3), so a cache keyed on it hits more often and never
        holds an issue body or a file's contents.
        """
        if self._targets is None:
            return json.dumps(args, sort_keys=True, default=str)
        return json.dumps(self.match_values(tool, args))

    def score(self, tool: str, args: dict) -> CallScore:
        """The severity to act on for one call."""
        candidates = self.candidates(tool)
        if not candidates:
            return CallScore(tool, 0.0, (), None, "no-cells", worst_case=False)

        # Step 2 — a tool with one scored asset needs no argument analysis.
        if len(candidates) == 1:
            asset, score = next(iter(candidates.items()))
            return CallScore(tool, score, (asset,), asset, "sole-candidate", worst_case=False)

        # Step 3 — narrow using the arguments. Naming a container excludes the
        # *other containers* (its siblings, which share the naming), but never a
        # facet — an asset nothing resembled, reached on every call regardless of
        # which container. Dropping a facet is how the earlier version
        # under-scored: `search_code(q="repo:…/public-site")` names the low
        # repo yet still returns `code-records` from every repo.
        matched, siblings = self._match(self.match_values(tool, args), candidates)
        if matched:
            chosen = {a for a in candidates if a not in siblings or a in matched}
            basis = "named"
        else:
            chosen = set(candidates)
            basis = "unresolved"

        # Step 4 — the worst of whatever survived. Among equal cells the v1-v4 path takes
        # whichever the set yields first, which varies with PYTHONHASHSEED. The target-input
        # path takes an asset the call named before a kept facet, then the first by id, so a
        # driver-keyed history records the container and a live and an offline process agree.
        if self._targets is not None:
            pool = sorted(chosen, key=lambda asset: (asset not in matched, asset))
        else:
            pool = chosen
        driver = max(pool, key=lambda asset: candidates[asset])
        return CallScore(
            tool=tool,
            severity=candidates[driver],
            assets=tuple(sorted(chosen)),
            driver=driver,
            basis=basis,
            worst_case=not matched or len(chosen) > 1,
        )

    def _match(self, values: list[str], candidates: dict[str, float]) -> tuple[set[str], set[str]]:
        """Assets the argument values name, and the siblings a name excludes.

        A *sibling* is a candidate some value partially matched — it shares the
        naming of a matched asset (the organizational prefix register ids carry),
        so a single-valued argument that named one did not also name it. A
        candidate no value resembled at all is a facet, never a sibling, and is
        never excluded.
        """
        found: set[str] = set()
        siblings: set[str] = set()
        for value in values:
            if self._discovery is not None:
                binding = self._discovery.lookup(value)
                if binding is not None and binding.asset_id in candidates:
                    found.add(binding.asset_id)
                    continue
            for asset in candidates:
                score = name_coverage(value, asset)
                if score >= NAME_MATCH_FLOOR:
                    found.add(asset)
                elif score > 0.0:
                    siblings.add(asset)
        return found, siblings | found


def _strings_in(args: object) -> list[str]:
    """Every scalar string an argument object contributes, flattened."""
    found: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str) and value.strip():
            found.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(args)
    return found


__all__ = [
    "CallScore",
    "ContainerSpec",
    "MatrixScorer",
    "NAME_MATCH_FLOOR",
    "TargetSpec",
    "parse_tool_targets",
]
