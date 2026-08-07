"""Discover a deployment's binding structure from its own traffic.

Nothing in this module names an argument key, a tool, or a domain. Everything it
knows it derives from two inputs a gate already has: the calls it has observed,
and the policy register the organization published. The same code therefore runs
unchanged against a server kind nobody anticipated.

Three things are discovered, by one idea each:

**Which argument names a container.**
    A container identifier is the one kind of argument value that *also appears
    in another tool's output* — because a server that lets an agent address a
    container also, somewhere, lets it enumerate them. Free-text arguments
    (``query``, ``body``) never reappear that way; enum arguments (``state``)
    reappear but fail the next test.

**Which tool enumerates them.**
    The same test names it: whichever tool's outputs contain those values.

**Whether the key is real.**
    A candidate is accepted only if its values link to at least two *distinct*
    register rows. This is what separates a container key from an enum, with no
    threshold on length, entropy or cardinality — ``state=open`` reappears in
    outputs but binds to no asset, so it is rejected by the same rule that
    accepts ``calendarId``.

Discovery is deterministic and model-free. It runs once per deployment, off the
call path.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from mcp_security.static_scoring.server_policies import PolicyAssetRow

from .identifiers import (
    canonical_id,
    describes_call_target,
    email_domains,
    fragments_with_offsets,
    identifier_candidates,
    inverse_document_frequency,
    name_coverage,
    normalize_key,
    tokens,
    weighted_overlap,
    windows_around,
)

#: A candidate key must carry values on at least this many calls to be judged.
#: Set low: the point is to exclude arguments seen once, not to demand traffic.
MIN_OBSERVATIONS = 5

#: A container key addresses a bounded set. Above this many distinct values the
#: argument is free text, whatever else it looks like.
MAX_DISTINCT_VALUES = 64

#: Containers are *reused*: a deployment has a handful of them and addresses each
#: one over and over. An identifier minted per call — an event id, a pull-request
#: number, a timestamp — has a distinct value almost every time it appears. The
#: ratio of distinct values to observations separates the two without any
#: knowledge of what either names.
MAX_REUSE_RATIO = 0.25

#: A listing tool prints the same name beside the same identifier every time. A
#: value that merely co-occurs with whatever happened to be nearby links
#: inconsistently, so a link is believed only when this share of its windows
#: agree.
MIN_LINK_CONSISTENCY = 0.6

#: A candidate key is accepted only if its values bind to at least this many
#: distinct register rows. Two is the minimum that shows the key *discriminates*
#: rather than naming one thing.
MIN_DISTINCT_ASSETS = 2

#: Containers are what the whole surface operates on, so more than one verb takes
#: them. A search string or a page size is consumed by the one verb that needs
#: it. Counting the verbs that accept a key separates the two.
MIN_CONSUMING_TOOLS = 2

#: Distinct containers hold distinct things, so a container key's values map
#: nearly one-to-one onto register rows. A filter argument — a date range, a
#: page size — has several values that all describe the same asset, and falls
#: below this ratio of distinct assets to bound values.
MIN_INJECTIVITY = 0.6

#: When no verb enumerates the containers, classification of returned content is
#: the only route left, and it is a weaker signal: it must clear a higher bar
#: before it is allowed to *establish* a key rather than merely extend one.
CONTENT_ONLY_INJECTIVITY = 0.8
CONTENT_ONLY_MIN_ASSETS = 3

#: How much of a register id the name beside an identifier must account for. At
#: 0.8 a two-word id needs both words (or an abbreviation of one); a single
#: shared word out of two is not enough, so a window merely mentioning "busy"
#: does not bind an identifier to ``free-busy-availability``.
NAME_LINK_FLOOR = 0.8

#: Minimum weighted-overlap for a content-derived link to be believed.
CONTENT_LINK_FLOOR = 0.12

#: An identifier is a handle, not a sentence. A key whose values are mostly
#: multi-word phrases is carrying natural language — a search string, a title, a
#: commit message — however few distinct values the traffic happened to reuse.
MAX_PHRASE_SHARE = 0.5

#: A token appearing in this share of a deployment's containers is boilerplate —
#: JSON scaffolding, a shared vocabulary — and identifies none of them. Content
#: linking scores on what distinguishes a container from its siblings.
MAX_BACKGROUND_SHARE = 0.5

#: A domain is the organization's own if it accounts for at least this share of
#: the email addresses the deployment's own data contains.
ORG_DOMAIN_SHARE = 0.10


@dataclass(frozen=True)
class Binding:
    """One container identifier linked to one register asset, with its evidence."""

    container_id: str
    asset_id: str
    route: str
    basis: str
    score: float


@dataclass(frozen=True)
class Discovery:
    """Everything derived from a deployment's traffic, plus why."""

    container_keys: tuple[str, ...]
    listing_tools: tuple[str, ...]
    org_domains: tuple[str, ...]
    bindings: dict[str, Binding]
    rejected: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def asset_ids(self) -> frozenset[str]:
        return frozenset(binding.asset_id for binding in self.bindings.values())

    def lookup(self, raw: str) -> Binding | None:
        """The binding for an identifier, trying each spelling it could carry."""
        for candidate in identifier_candidates(raw):
            binding = self.bindings.get(candidate)
            if binding is not None:
                return binding
        return None


def _args_of(call: dict) -> dict:
    try:
        parsed = json.loads(call.get("args") or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _scalar_values(value: object) -> list[str]:
    """Every scalar string a JSON argument value contributes, flattened."""
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [str(value)]
    if isinstance(value, list):
        return [v for item in value for v in _scalar_values(item)]
    return []


def _candidate_keys(calls: list[dict]) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Argument keys whose values look like reused containers, and why others do not.

    Two gates, both free of any domain knowledge: the value set must be bounded,
    and it must be *reused* rather than minted per call. Together they admit
    ``calendarId`` (6 values over 800 calls) and reject ``eventId``, ``timeMin``
    and ``query`` (a fresh value nearly every time).
    """
    values: dict[str, set[str]] = defaultdict(set)
    observations: Counter[str] = Counter()
    for call in calls:
        for key, value in _args_of(call).items():
            found = _scalar_values(value)
            if not found:
                continue
            normalized = normalize_key(key)
            observations[normalized] += 1
            values[normalized].update(canonical_id(v) for v in found)

    accepted: dict[str, set[str]] = {}
    rejected: dict[str, str] = {}
    for key, found in values.items():
        seen = observations[key]
        if seen < MIN_OBSERVATIONS:
            continue
        if len(found) < 2:
            rejected[key] = f"one distinct value over {seen} calls — names nothing to choose"
            continue
        if len(found) > MAX_DISTINCT_VALUES:
            rejected[key] = f"{len(found)} distinct values — free text, not a container set"
            continue
        reuse = len(found) / seen
        if reuse > MAX_REUSE_RATIO:
            rejected[key] = f"a new value on {reuse:.0%} of calls — minted per call, not reused"
            continue
        phrases = sum(1 for value in found if " " in value.strip())
        if phrases / len(found) > MAX_PHRASE_SHARE:
            rejected[key] = (
                f"{phrases}/{len(found)} values are multi-word — natural language, not a handle"
            )
            continue
        accepted[key] = found
    return accepted, rejected


def _outputs_by_tool(calls: list[dict]) -> dict[str, list[str]]:
    outputs: dict[str, list[str]] = defaultdict(list)
    for call in calls:
        text = call.get("output") or ""
        if text:
            outputs[call.get("tool", "")].append(text)
    return outputs


def _consistent_link(
    windows: list[tuple[str, int]], rows: list[PolicyAssetRow]
) -> tuple[str, float, str] | None:
    """The register row this identifier sits beside, when the windows agree.

    "Beside" means nearest, not merely present: a compact listing puts every
    container's name inside one window, so the candidate names are ranked by
    similarity first and by distance from the identifier second. A value that
    only co-occurs with nearby text links to a different name each time, so the
    modal link's share is what separates a real listing from coincidence — with
    no knowledge of the output's format.
    """
    votes: Counter[str] = Counter()
    evidence: dict[str, tuple[float, str]] = {}
    for window, needle_at in windows:
        best: tuple[float, int, str, str] | None = None
        for fragment, offset in fragments_with_offsets(window):
            distance = abs(offset - needle_at)
            for row in rows:
                score = name_coverage(fragment, row.asset_id)
                if score < NAME_LINK_FLOOR:
                    continue
                rank = (score, -distance)
                if best is None or rank > (best[0], -best[1]):
                    best = (score, distance, row.asset_id, fragment)
        if best is not None:
            votes[best[2]] += 1
            evidence.setdefault(best[2], (best[0], best[3]))
    if not votes:
        return None
    asset_id, count = votes.most_common(1)[0]
    if count / sum(votes.values()) < MIN_LINK_CONSISTENCY:
        return None
    score, fragment = evidence[asset_id]
    return asset_id, score, f"listed beside {fragment!r}"


def _enumerating_tool(
    values: set[str], outputs: dict[str, list[str]], exclude: set[str], rows: list[PolicyAssetRow]
) -> tuple[str, dict[str, tuple[str, float, str]]] | None:
    """The tool whose output best *distinguishes* these identifiers.

    Coverage alone is not enough: a free/busy response mentions every calendar id
    yet describes them all with the same word. The tool that enumerates
    containers is the one whose windows link them to the most *distinct* register
    rows, which is exactly what makes a listing useful.

    ``exclude`` holds the tools that consume the key as an argument — a tool
    echoing back the id it was handed proves nothing about enumeration.
    """
    best: tuple[int, int, str, dict[str, tuple[str, float, str]]] | None = None
    for tool, texts in outputs.items():
        if tool in exclude:
            continue
        joined = "\n".join(texts)
        links: dict[str, tuple[str, float, str]] = {}
        for value in values:
            windows = windows_around(joined, value)
            if not windows:
                continue
            link = _consistent_link(windows, rows)
            if link is not None:
                links[value] = link
        if not links:
            continue
        distinct = len({asset for asset, _, _ in links.values()})
        rank = (distinct, len(links))
        if best is None or rank > (best[0], best[1]):
            best = (distinct, len(links), tool, links)
    return (best[2], best[3]) if best else None


def _link_by_name(
    values: set[str], rows: list[PolicyAssetRow]
) -> dict[str, tuple[str, float, str]]:
    """Link identifiers to register rows by the value spelling the asset id out.

    The cheapest route of the three, and the only one needing neither an
    enumerating verb nor returned content: many deployments name the thing after
    the concept, so ``repo="helios-scada-gateway"`` already *is*
    ``helios-scada-gateway``, and ``#vireo-safety-pv`` is ``vireo-safety-pv``.

    Run over observed values rather than per call, so the result is the set of
    assets that argument can name — a key table derived from nothing but the
    traffic and the register.
    """
    linked: dict[str, tuple[str, float, str]] = {}
    for value in values:
        scored = [(name_coverage(value, row.asset_id), row.asset_id) for row in rows]
        score, asset_id = max(scored) if scored else (0.0, "")
        if score >= NAME_LINK_FLOOR:
            linked[value] = (asset_id, score, f"the value spells out {asset_id!r}")
    return linked


def _link_by_content(
    observed: dict[str, Counter], rows: list[PolicyAssetRow]
) -> dict[str, tuple[str, float, str]]:
    """Link identifiers to register rows by what calls against them returned.

    Only the tokens that *distinguish* one container from its siblings are
    scored. Pooled tool output is mostly shared scaffolding — field names, the
    platform's own vocabulary, the organization's house style — and matching on
    it collapses every container onto whichever register row happens to use the
    same common words.
    """
    documents = {row.asset_id: tokens(f"{row.asset_id} {row.description}") for row in rows}
    weights = inverse_document_frequency(list(documents.values()))

    background: Counter[str] = Counter()
    for counts in observed.values():
        background.update(set(counts))
    limit = max(1, int(len(observed) * MAX_BACKGROUND_SHARE))
    shared = {token for token, count in background.items() if count > limit}

    linked: dict[str, tuple[str, float, str]] = {}
    for container_id, counts in observed.items():
        distinctive = set(counts) - shared
        if not distinctive:
            continue
        scored = []
        for asset_id, document in documents.items():
            score, evidence = weighted_overlap(distinctive, document, weights)
            if evidence is not None:
                scored.append((score, asset_id, evidence))
        if not scored:
            continue
        score, asset_id, evidence = max(scored)
        if score >= CONTENT_LINK_FLOOR:
            linked[container_id] = (asset_id, score, f"returned content matched {evidence!r}")
    return linked


def _observed_content(calls: list[dict], key: str) -> dict[str, Counter]:
    """Pooled output tokens per container identifier named by ``key``."""
    pooled: dict[str, Counter] = defaultdict(Counter)
    for call in calls:
        text = call.get("output") or ""
        if not text:
            continue
        for arg_key, value in _args_of(call).items():
            if normalize_key(arg_key) != key:
                continue
            for raw in _scalar_values(value):
                pooled[canonical_id(raw)].update(tokens(text))
    return pooled


def _drop_redundant_keys(
    keys: list[str], calls: list[dict], bindings: dict[str, Binding]
) -> tuple[list[str], list[tuple[str, str]]]:
    """Keep only the keys that bind calls no better key already binds.

    A sub-object handle — a pull-request number, an issue number — rides along
    with the container key on every call that carries it, and links to whatever
    container it lives in. It is a true statement that adds nothing, so it is
    dropped in favour of the key that covers strictly more.
    """
    coverage: dict[str, set[int]] = {key: set() for key in keys}
    for index, call in enumerate(calls):
        args = _args_of(call)
        for key in keys:
            for arg_key, value in args.items():
                if normalize_key(arg_key) != key:
                    continue
                if any(canonical_id(str(v)) in bindings for v in _scalar_values(value)):
                    coverage[key].add(index)
    ranked = sorted(keys, key=lambda key: (-len(coverage[key]), key))
    kept: list[str] = []
    dropped: list[tuple[str, str]] = []
    covered: set[int] = set()
    for key in ranked:
        added = coverage[key] - covered
        if kept and not added:
            dropped.append((key, "binds no call a stronger key does not already bind"))
            continue
        kept.append(key)
        covered |= coverage[key]
    return kept, dropped


def discover_org_domains(calls: list[dict]) -> tuple[str, ...]:
    """Email domains the deployment's own data uses often enough to be its own.

    An organization's people appear constantly in its own calendars, channels and
    directories; a counterparty appears rarely. Frequency alone separates them,
    so no domain has to be configured.
    """
    counts: Counter[str] = Counter()
    for call in calls:
        counts.update(email_domains(call.get("output") or ""))
    total = sum(counts.values())
    if not total:
        return ()
    return tuple(
        domain for domain, count in counts.most_common() if count / total >= ORG_DOMAIN_SHARE
    )


def discover(calls: list[dict], rows: list[PolicyAssetRow]) -> Discovery:
    """Derive container keys, listing tools and bindings from observed traffic."""
    # A row describing what a call reached has no standing identity, so no
    # argument can name it and it is never a catalog target.
    linkable = [row for row in rows if not describes_call_target(row.description)]
    outputs = _outputs_by_tool(calls)
    candidates, shape_rejects = _candidate_keys(calls)

    accepted_keys: list[str] = []
    listing_tools: list[str] = []
    bindings: dict[str, Binding] = {}
    rejected: list[tuple[str, str]] = list(shape_rejects.items())

    for key, values in sorted(candidates.items()):
        consumers = {
            call.get("tool", "")
            for call in calls
            if any(normalize_key(k) == key for k in _args_of(call))
        }
        if len(consumers) < MIN_CONSUMING_TOOLS:
            rejected.append((key, f"taken by {len(consumers)} verb — a filter, not a container"))
            continue
        found = _enumerating_tool(values, outputs, consumers, linkable)
        proposed: dict[str, Binding] = {}
        if found is not None:
            tool, links = found
            for value, (asset_id, score, basis) in links.items():
                proposed[value] = Binding(value, asset_id, "listing", f"{tool}: {basis}", score)
        for container_id, (asset_id, score, basis) in _link_by_name(values, linkable).items():
            proposed.setdefault(container_id, Binding(container_id, asset_id, "name", basis, score))
        for container_id, (asset_id, score, basis) in _link_by_content(
            _observed_content(calls, key), linkable
        ).items():
            proposed.setdefault(container_id, Binding(container_id, asset_id, "content", basis,
                                                      score))

        if not proposed:
            rejected.append((key, "no value linked to any register asset"))
            continue
        distinct = {binding.asset_id for binding in proposed.values()}
        injectivity = len(distinct) / len(proposed)
        # A value that spells out its own asset id is as strong as an enumerating
        # verb saying so — both are statements, not inferences.
        listed = {b.asset_id for b in proposed.values() if b.route in {"listing", "name"}}

        # An enumerating verb is the strong evidence: it stated the link. Content
        # classification only extends such a key, and has to clear a higher bar
        # before it may establish one on its own.
        if listed:
            floor_assets, floor_injectivity, why = MIN_DISTINCT_ASSETS, MIN_INJECTIVITY, "listed"
        else:
            floor_assets = CONTENT_ONLY_MIN_ASSETS
            floor_injectivity = CONTENT_ONLY_INJECTIVITY
            why = "content-only"
        if len(distinct) < floor_assets:
            rejected.append(
                (key, f"{why}: bound {len(distinct)} distinct asset(s), needs {floor_assets}")
            )
            continue
        if injectivity < floor_injectivity:
            rejected.append(
                (key, f"{why}: {len(proposed)} values share {len(distinct)} assets "
                      f"({injectivity:.0%}) — a filter, not distinct containers")
            )
            continue
        accepted_keys.append(key)
        if found is not None:
            listing_tools.append(found[0])
        for container_id, binding in proposed.items():
            existing = bindings.get(container_id)
            if existing is None or binding.score > existing.score:
                bindings[container_id] = binding

    accepted_keys, redundant = _drop_redundant_keys(accepted_keys, calls, bindings)
    rejected.extend(redundant)

    # An enumerating output names containers the traffic never addressed — a
    # repository nobody opened, a pull-request number picked up in passing. They
    # are never looked up, so carrying them only inflates the catalog.
    addressed = {value for key in accepted_keys for value in candidates.get(key, ())}
    bindings = {cid: binding for cid, binding in bindings.items() if cid in addressed}

    return Discovery(
        container_keys=tuple(accepted_keys),
        listing_tools=tuple(dict.fromkeys(listing_tools)),
        org_domains=discover_org_domains(calls),
        bindings=bindings,
        rejected=tuple(rejected),
    )


__all__ = [
    "Binding",
    "CONTENT_LINK_FLOOR",
    "Discovery",
    "MAX_BACKGROUND_SHARE",
    "MAX_DISTINCT_VALUES",
    "MAX_PHRASE_SHARE",
    "MAX_REUSE_RATIO",
    "MIN_LINK_CONSISTENCY",
    "MIN_CONSUMING_TOOLS",
    "MIN_DISTINCT_ASSETS",
    "CONTENT_ONLY_INJECTIVITY",
    "CONTENT_ONLY_MIN_ASSETS",
    "MIN_INJECTIVITY",
    "MIN_OBSERVATIONS",
    "NAME_LINK_FLOOR",
    "discover",
    "discover_org_domains",
]
