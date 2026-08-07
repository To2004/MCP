"""Resolve ``(tool, arguments)`` to the register assets a call actually touches.

The register's ``Tools`` column already answers a weaker question — which assets
a tool *can* reach. That candidate set is the starting point, and the arguments
only ever narrow it. Resolution therefore never searches the asset space; it
filters a list the policy already wrote down.

Every mechanism is deterministic: a dictionary lookup into the discovered
bindings, a regex over register prose, a set membership test on email domains.
No model runs on the call path, so a decision costs nothing, reproduces exactly,
and cannot be steered by text an attacker places in an argument.

Four levels, each adding one mechanism, so an evaluation can attribute every
point of precision to the thing that bought it:

``TOOL_ONLY``
    The register candidate set, unfiltered. The upper bound on recall and the
    baseline any argument-aware method has to beat on set size.
``CATALOG``
    Container identifiers resolved through the discovered bindings, so the five
    calendars a verb could reach collapse to the one it named.
``OPERATION``
    Assets whose description names the opposite operation are dropped — a read
    does not touch "what a write creates".
``EGRESS``
    Assets describing data leaving the organization are admitted only when the
    call carries an identifier outside the deployment's own domains, or mints a
    container the register never covered.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import IntEnum

from mcp_security.static_scoring.server_policies import PolicyAssetRow

from .catalog import ToolSpec
from .discovery import Discovery
from .identifiers import (
    canonical_id,
    describes_call_target,
    describes_egress,
    email_domains,
    inverse_document_frequency,
    name_coverage,
    name_tokens,
    normalize_key,
    tokens,
    weighted_overlap,
)

#: Parameter-name words meaning the parameter carries a person, so its absence is
#: informative: a verb that *can* name recipients and does not name any outside
#: one is not sending mail outside.
_RECIPIENT_WORDS = frozenset(
    {"attendee", "attendees", "recipient", "recipients", "email", "invitee", "invitees",
     "participant", "participants", "to", "cc", "bcc"}
)


class Level(IntEnum):
    """Ablation levels, each a superset of the mechanisms below it."""

    TOOL_ONLY = 0
    CATALOG = 1
    OPERATION = 2
    EGRESS = 3


#: Atomic operations that read state, as recorded by the scanner's operation ladder.
READ_OPS = frozenset({"READ", "LIST", "SEARCH", "GET", "QUERY"})
#: Atomic operations that change it.
WRITE_OPS = frozenset({"CREATE", "WRITE", "UPDATE", "DELETE", "MERGE", "MOVE", "JOIN", "LEAVE"})

#: Verbs inside a call-target row's description, naming the operation family that
#: reaches it. ``event-records`` says "What a create/update/delete targets"; a
#: ``list-events`` call does not touch it.
_READ_VERB_RE = re.compile(
    r"\b(reads?|search\w*|history|returns?|listings?|reaches|lists?|shows?|views?|displays?|"
    r"gets?|queries|querys?)\b",
    re.I,
)
_WRITE_VERB_RE = re.compile(
    r"\b(creates?|writes?|updates?|deletes?|edits?|merges?|targets?|moves?|adds?|removes?|"
    r"authenticat\w*|authori[sz]\w*|registers?|links?|connects?|revokes?|switch\w*|"
    r"issues?|grants?|withdraws?|provisions?|rotates?|resets?)\b",
    re.I,
)

#: An identifier shorter than this is not searched for inside other values: a
#: two- or three-character token matches by accident far more often than it
#: matches on purpose.
_MIN_EMBEDDED_LENGTH = 4

#: How much of a register asset id an argument value must account for before the
#: value is taken to name that asset directly. High on purpose: this route runs
#: over *every* argument, including free-text payload, so a single shared word
#: must never be enough.
DIRECT_NAME_FLOOR = 0.8

#: Register flag marking a row as the *view* of something rather than the thing
#: itself — names and attributes with no content behind them. A read-flavoured
#: mode reaches the view; a write-flavoured mode reaches what the view describes.
_VIEW_FLAG = "metadata-only"


def _keep_nonempty(before: list[AssetHit], after: list[AssetHit]) -> list[AssetHit]:
    """A narrowing step may never remove the last asset.

    Every filter here answers "is this asset *also* in play?", never "does this
    call touch anything?". Returning nothing where the register says the tool
    reaches something is strictly worse than returning the register's answer, so
    an emptying filter is discarded.
    """
    return after if after else before


@dataclass(frozen=True)
class AssetHit:
    """One asset a call touches, with how it was determined."""

    asset_id: str
    mechanism: str
    basis: str


@dataclass(frozen=True)
class Resolution:
    """Every asset a call touches, plus what could not be determined."""

    tool: str
    hits: tuple[AssetHit, ...]
    #: Container identifiers in the arguments that the discovery could not bind.
    unbound_containers: tuple[str, ...] = ()
    #: True when the call names no container and therefore reaches every one.
    fanout: bool = False
    #: True when the call DID name a container the catalog cannot bind. The
    #: result is the same closure as a fan-out, but the cause is different and a
    #: gate should treat it differently: a fan-out is the verb behaving normally,
    #: an unbound handle is a container the deployment has never seen.
    unresolved_container: bool = False
    #: True when the call creates a container no catalog can already know.
    mints_container: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def asset_ids(self) -> frozenset[str]:
        return frozenset(hit.asset_id for hit in self.hits)

    @property
    def primary(self) -> str | None:
        """The single best answer, for comparison against a single-label corpus.

        A bound container wins: it is the only asset the arguments named
        outright. Failing that, an asset a structural mechanism selected, then a
        lone remaining candidate. ``None`` when the call genuinely spreads.
        """
        for mechanism in ("catalog", "mode", "egress", "operation"):
            matches = [hit for hit in self.hits if hit.mechanism == mechanism]
            if matches:
                return matches[0].asset_id
        return self.hits[0].asset_id if len(self.hits) == 1 else None


def worst_severity(
    resolution: Resolution, sensitivity: dict[str, int]
) -> tuple[int, str | None]:
    """The severity a gate must assume for a call, and the asset that sets it.

    A gate is not obliged to name the asset — it is obliged not to under-score.
    So the severity of a call is the worst among everything it could be touching,
    which is exactly the maximum over the resolved set.

    This is what makes a key table optional rather than required. With one, the
    set collapses to a single container and the severity is that container's.
    Without one, the set is every candidate and the severity is the worst of
    them: blunter, never wrong in the dangerous direction. **As long as the true
    asset is somewhere in the set, the maximum over the set can never come out
    below the truth**, so the only cost of not knowing is over-scoring, and that
    cost is measurable.
    """
    scored = [
        (sensitivity[asset], asset) for asset in resolution.asset_ids if asset in sensitivity
    ]
    if not scored:
        return 0, None
    severity, asset = max(scored)
    return severity, asset


class AssetResolver:
    """Resolve calls against one deployment's register and discovered bindings."""

    def __init__(
        self,
        rows: list[PolicyAssetRow],
        discovery: Discovery | None = None,
        tool_operations: dict[str, str | list[str]] | None = None,
        tools: dict[str, ToolSpec] | None = None,
    ) -> None:
        """``tool_operations`` maps a tool to its atomic operations.

        A single string is accepted for convenience, but the full list is what
        the scanner records and what this class needs: ``create_repository`` has
        ``primary_op="WRITE"`` and ``atomic_ops=["CREATE", "WRITE"]``, so reading
        only the primary operation would miss every container-creating verb.
        """
        self._rows = {row.asset_id: row for row in rows}
        #: Omitting ``discovery`` is the **stateless** mode, and the default.
        #: Nothing is observed, accumulated or stored: a decision is a pure
        #: function of this call, the policy register and the tool schemas.
        #: Retaining a learned identifier-to-asset table would be a record of
        #: what a deployment contains and what was accessed — worth avoiding even
        #: though it costs precision on servers whose identifiers are opaque.
        self._discovery = discovery or Discovery((), (), (), {})
        self._tools = tools or {}
        self._operations = {
            tool: frozenset(op.upper() for op in ([ops] if isinstance(ops, str) else ops))
            for tool, ops in (tool_operations or {}).items()
        }
        self._reach: dict[str, list[str]] = {}
        for row in rows:
            for tool in row.tools:
                self._reach.setdefault(tool, []).append(row.asset_id)

    def candidates(self, tool: str) -> list[str]:
        """Assets the register says this tool can reach."""
        return list(self._reach.get(tool, ()))

    def resolve(self, tool: str, args: dict, level: Level = Level.EGRESS) -> Resolution:
        """The assets a call touches, narrowed to ``level``."""
        candidates = self.candidates(tool)
        if not candidates:
            return Resolution(tool=tool, hits=(), notes=("tool reaches no register asset",))

        if level == Level.TOOL_ONLY:
            return Resolution(
                tool=tool,
                hits=tuple(
                    AssetHit(asset, "register", "register Tools column") for asset in candidates
                ),
            )

        bound, unbound = self._bind_containers(args)
        # Stateless route: does any argument value spell out one of the assets
        # this verb can reach? Needs no table and no history.
        named, siblings = self._bind_by_name(args, candidates)
        if named:
            bound = {**named, **bound}
        catalog_assets = self._discovery.asset_ids | frozenset(named) | siblings
        containers = [asset for asset in candidates if asset in catalog_assets]

        hits: list[AssetHit] = []
        fanout = False
        unresolved = False
        if bound:
            hits.extend(
                AssetHit(asset_id, "catalog", basis)
                for asset_id, basis in bound.items()
                if asset_id in containers
            )
        elif containers:
            # Either the call named no container, or it named one nothing can
            # bind. Both reach the same closure — every container the verb can
            # touch — because narrowing further would be a guess. Only the
            # reason differs, and the flags carry it.
            unresolved = bool(unbound)
            fanout = not unresolved
            reason = (
                f"named {unbound[0]!r}, which no container binds — closure over every one"
                if unresolved
                else "no container named — reaches every one"
            )
            hits.extend(AssetHit(asset, "register", reason) for asset in containers)
        hits.extend(
            AssetHit(asset, "register", "register Tools column")
            for asset in candidates
            if asset not in catalog_assets
        )

        if level >= Level.OPERATION:
            hits = _keep_nonempty(hits, self._filter_by_operation(tool, hits))
            hits = self._rank_by_mode(tool, args, hits)
        notes: tuple[str, ...] = ()
        mints = self._mints_container(tool)
        if level >= Level.EGRESS:
            filtered, notes = self._filter_egress(tool, args, hits, mints)
            hits = _keep_nonempty(hits, filtered)

        return Resolution(
            tool=tool,
            hits=tuple(hits),
            unbound_containers=tuple(unbound),
            fanout=fanout,
            unresolved_container=unresolved,
            mints_container=mints,
            notes=notes,
        )

    # -- internals ---------------------------------------------------------- #

    def _bind_containers(self, args: dict) -> tuple[dict[str, str], list[str]]:
        """Container identifiers in the arguments, split into bound and unbound."""
        bound: dict[str, str] = {}
        unbound: list[str] = []
        for key, value in args.items():
            if normalize_key(key) not in self._discovery.container_keys:
                continue
            for raw in value if isinstance(value, list) else [value]:
                if not isinstance(raw, (str, int)) or not str(raw).strip():
                    continue
                binding = self._discovery.lookup(str(raw))
                if binding is None:
                    unbound.append(canonical_id(str(raw)))
                    continue
                bound[binding.asset_id] = f"{key}={binding.container_id!r}: {binding.basis}"
        if not bound:
            bound = self._bind_embedded(args)
        return bound, unbound

    def _bind_by_name(
        self, args: dict, candidates: list[str]
    ) -> tuple[dict[str, str], frozenset[str]]:
        """Match argument values against the register's own asset ids, as strings.

        Many deployments name the thing after the concept: a repository called
        ``helios-scada-gateway``, a channel called ``#vireo-safety-pv``, a table
        called ``api_keys``, a calendar whose display name is "Aurora Airways —
        Executive". Where that holds, the argument *is* the asset id in another
        spelling, and no key table is needed at all.

        Only the tool's own candidates are considered, so a value can never bind
        to something the register says this verb cannot reach. Scoring is
        :func:`name_coverage`, which already folds case, punctuation and
        abbreviation — the three ways the live servers were observed to differ.

        Where it does not hold — an opaque Google calendar id, a filesystem path
        against a concept id like ``payroll-records`` — nothing matches and the
        caller falls back to the closure, and the call is scored at the worst
        severity it could possibly carry.

        Returns the assets a value names, and the assets that are *siblings* of
        them. A sibling is a candidate the same value partially matched — sharing
        the organizational prefix that register ids carry, as
        ``helios-grid-infra-config`` shares "helios" with a value naming
        ``helios-scada-gateway``. A single-valued argument carries one container,
        so a sibling it did not name is one this call did not touch. Candidates
        the value did not resemble at all are left alone: those are facets, not
        alternatives.

        Where ids share no prefix — ``api_keys`` beside ``employees`` — nothing
        is recognized as a sibling and every candidate stays in. That is the
        intended degradation: imprecise, never unsafe.
        """
        found: dict[str, str] = {}
        related: set[str] = set()
        for key, value in args.items():
            for raw in value if isinstance(value, list) else [value]:
                if not isinstance(raw, str) or not raw.strip():
                    continue
                scored = [(name_coverage(raw, asset), asset) for asset in candidates]
                hits = [asset for score, asset in scored if score >= DIRECT_NAME_FLOOR]
                if not hits:
                    continue
                for asset in hits:
                    found[asset] = f"{key}={raw[:40]!r} names {asset!r}"
                related.update(
                    asset for score, asset in scored if 0.0 < score < DIRECT_NAME_FLOOR
                )
        return found, frozenset(related) | frozenset(found)

    def _bind_embedded(self, args: dict) -> dict[str, str]:
        """Container identifiers written *inside* another argument's value.

        Servers routinely let a caller scope a broad verb without giving it a
        container parameter: ``search_code(q="repo:acme/api password")``,
        ``read_query(sql="SELECT * FROM api_keys")``,
        ``conversations_search_messages(filter_in_channel="C0BL…")``. The
        identifier is there; only the key is missing. Scanning every value for a
        known identifier recovers it, and is applied only when the container key
        produced nothing, so a real key always wins.

        Matching is on word boundaries: a table named ``grants`` must not bind
        because some prose contained "grants funding".
        """
        found: dict[str, str] = {}
        for key, value in args.items():
            for raw in value if isinstance(value, list) else [value]:
                if not isinstance(raw, str) or not raw.strip():
                    continue
                haystack = raw.lower()
                for container_id, binding in self._discovery.bindings.items():
                    if len(container_id) < _MIN_EMBEDDED_LENGTH:
                        continue
                    pattern = rf"(?<![a-z0-9_./-]){re.escape(container_id)}(?![a-z0-9_.-])"
                    if re.search(pattern, haystack):
                        found[binding.asset_id] = (
                            f"{key} contains {container_id!r}: {binding.basis}"
                        )
        return found

    def _filter_by_operation(self, tool: str, hits: list[AssetHit]) -> list[AssetHit]:
        """Drop call-target assets whose description names the other operation family."""
        operations = self._operations.get(tool)
        if not operations:
            return hits
        is_read = bool(operations & READ_OPS)
        is_write = bool(operations & WRITE_OPS)
        if is_read == is_write:  # neither, or genuinely both — no basis to filter
            return hits
        operation = sorted(operations & (READ_OPS | WRITE_OPS))[0]
        kept: list[AssetHit] = []
        for hit in hits:
            row = self._rows.get(hit.asset_id)
            if row is None or not describes_call_target(row.description):
                kept.append(hit)
                continue
            wants_read = bool(_READ_VERB_RE.search(row.description))
            wants_write = bool(_WRITE_VERB_RE.search(row.description))
            if not (wants_read or wants_write):
                kept.append(hit)
            elif (is_read and wants_read) or (is_write and wants_write):
                kept.append(
                    AssetHit(hit.asset_id, "operation", f"{operation} matches its description")
                )
        return kept

    def _declares_recipient(self, tool: str) -> bool:
        """Whether this tool has a parameter that names who receives something.

        The distinction matters: a verb that *can* carry recipients and carries
        none is telling you nothing left the organization. A verb with no such
        parameter is telling you nothing at all — the recipients live in stored
        state — so its egress asset must stay in, conservatively.
        """
        spec = self._tools.get(tool)
        if spec is None:
            return False
        return any(set(name_tokens(name)) & _RECIPIENT_WORDS for name in spec.properties)

    def _filter_egress(
        self, tool: str, args: dict, hits: list[AssetHit], mints: bool
    ) -> tuple[list[AssetHit], tuple[str, ...]]:
        """Admit boundary-crossing assets only when the call actually crosses it."""
        egress = [
            hit
            for hit in hits
            if (row := self._rows.get(hit.asset_id)) and describes_egress(row.description)
        ]
        if not egress:
            return hits, ()
        if not self._declares_recipient(tool):
            return hits, (f"{tool} names no recipient parameter — egress assumed",)
        domains = set(email_domains(json.dumps(args)))
        outside = domains - set(self._discovery.org_domains)
        fires = bool(outside) or mints
        if fires:
            reason = (
                f"recipient outside {sorted(self._discovery.org_domains)}"
                if outside
                else "creates a container outside the register"
            )
            kept = [
                AssetHit(hit.asset_id, "egress", reason) if hit in egress else hit for hit in hits
            ]
            return kept, ()
        dropped = {hit.asset_id for hit in egress}
        return (
            [hit for hit in hits if hit.asset_id not in dropped],
            (f"no boundary crossing: {sorted(dropped)} dropped",),
        )

    def _rank_by_mode(self, tool: str, args: dict, hits: list[AssetHit]) -> list[AssetHit]:
        """Use a tool's documented modes to name the primary asset it shares.

        This *ranks*, it never removes. A mode says which asset the call is
        chiefly about, not which ones it leaves alone: listing accounts returns
        the directory and, in the same response, the scopes that directory
        describes; adding one rewrites the scopes and puts a new row in the
        directory. Both assets are in play either way, so dropping one would
        trade a true answer for a tidier set.

        Some tools carry several register assets and separate them by a mode
        argument rather than by a container: ``manage-accounts`` documents
        ``'list' (show accounts)`` against ``'add' (authenticate new account)``,
        which is the difference between reading the account directory and
        rewriting what every other tool can reach. The tool states both the mode
        values and what each one does, so the mode's own words are scored against
        the candidate descriptions.
        """
        spec = self._tools.get(tool)
        if spec is None:
            return hits
        parameter = spec.mode_parameter()
        if parameter is None:
            return hits
        chosen = next(
            (v for k, v in args.items() if normalize_key(k) == normalize_key(parameter)), None
        )
        meaning = spec.modes().get(str(chosen))
        if meaning is None:
            return hits
        # The mode's own value is a verb too ('list', 'issue', 'revoke'), and is
        # often the clearest one, so it is scored alongside the documented gloss.
        meaning = f"{chosen} {meaning}"
        # Only assets this tool alone distinguishes are in play; a bound container
        # was named outright and is never overruled by prose.
        candidates = [h for h in hits if h.mechanism != "catalog"]
        if len(candidates) < 2:
            return hits
        documents = {
            hit.asset_id: tokens(f"{hit.asset_id} {self._rows[hit.asset_id].description}")
            for hit in candidates
            if hit.asset_id in self._rows
        }
        if len(documents) < 2:
            return hits
        best_asset = self._mode_target(meaning, list(documents))
        if best_asset is None:
            return hits
        return [
            AssetHit(hit.asset_id, "mode", f"{parameter}={chosen!r}: {meaning!r}")
            if hit.asset_id == best_asset
            else hit
            for hit in hits
        ]

    def _mode_target(self, meaning: str, candidates: list[str]) -> str | None:
        """Which candidate a documented mode selects.

        First on *kind*: the register flags a row ``metadata-only`` when it is the
        view of something — a list of names with no content behind it. A mode
        that shows or lists reaches that view; a mode that adds, removes or
        authenticates reaches the thing the view describes. Descriptions of two
        assets on the same tool often share every content word ("accounts"), so
        this structural split decides where prose cannot.

        Falling back to prose only when the flags do not separate them.
        """
        reads = bool(_READ_VERB_RE.search(meaning))
        writes = bool(_WRITE_VERB_RE.search(meaning))
        if reads != writes:
            views = [a for a in candidates if _VIEW_FLAG in self._rows[a].flags]
            things = [a for a in candidates if _VIEW_FLAG not in self._rows[a].flags]
            wanted = views if reads else things
            if len(wanted) == 1:
                return wanted[0]
        documents = {
            asset: tokens(f"{asset} {self._rows[asset].description}") for asset in candidates
        }
        weights = inverse_document_frequency(list(documents.values()))
        observed = set(tokens(meaning))
        scored = [
            (weighted_overlap(observed, document, weights)[0], asset)
            for asset, document in documents.items()
        ]
        best_score, best_asset = max(scored)
        return best_asset if best_score > 0 else None

    def _mints_container(self, tool: str) -> bool:
        """Whether this verb creates a container no catalog can already know."""
        if "CREATE" not in self._operations.get(tool, frozenset()):
            return False
        return any(
            describes_call_target(row.description) and "creates" in row.description.lower()
            for asset in self.candidates(tool)
            if (row := self._rows.get(asset))
        )


__all__ = [
    "AssetHit",
    "DIRECT_NAME_FLOOR",
    "AssetResolver",
    "Level",
    "READ_OPS",
    "Resolution",
    "WRITE_OPS",
    "worst_severity",
]
