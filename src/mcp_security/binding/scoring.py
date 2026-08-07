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

Nothing here retains state. No table is built, no traffic observed, no call
remembered.
"""

from __future__ import annotations

from dataclasses import dataclass

from .discovery import Discovery
from .identifiers import name_coverage

#: How much of an asset id an argument value must account for before the value
#: is taken to name that asset. High on purpose: this runs over every argument,
#: including free-text payload, so one shared word must never be enough.
NAME_MATCH_FLOOR = 0.8


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
    homed, and is not a candidate.
    """

    #: Band marking a cell the register never homed.
    UNSCORED_BAND = "na"

    def __init__(
        self,
        cells: dict[str, dict[str, float]],
        bands: dict[str, dict[str, str]],
        discovery: Discovery | None = None,
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

    def candidates(self, tool: str) -> dict[str, float]:
        """The assets this tool has a scored cell against, and their scores."""
        return dict(self._by_tool.get(tool, {}))

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
        matched, siblings = self._match(args, candidates)
        if matched:
            chosen = {a for a in candidates if a not in siblings or a in matched}
            basis = "named"
        else:
            chosen = set(candidates)
            basis = "unresolved"

        # Step 4 — the worst of whatever survived.
        driver = max(chosen, key=lambda asset: candidates[asset])
        return CallScore(
            tool=tool,
            severity=candidates[driver],
            assets=tuple(sorted(chosen)),
            driver=driver,
            basis=basis,
            worst_case=not matched or len(chosen) > 1,
        )

    def _match(self, args: dict, candidates: dict[str, float]) -> tuple[set[str], set[str]]:
        """Assets the arguments name, and the siblings a name excludes.

        A *sibling* is a candidate some value partially matched — it shares the
        naming of a matched asset (the organizational prefix register ids carry),
        so a single-valued argument that named one did not also name it. A
        candidate no value resembled at all is a facet, never a sibling, and is
        never excluded.
        """
        found: set[str] = set()
        siblings: set[str] = set()
        for value in _strings_in(args):
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


def _strings_in(args: dict) -> list[str]:
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


__all__ = ["CallScore", "MatrixScorer", "NAME_MATCH_FLOOR"]
