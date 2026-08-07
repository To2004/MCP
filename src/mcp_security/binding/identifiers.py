"""Shared text utilities for binding: keys, identifiers, tokens, and evidence.

Nothing here knows what a calendar or a repository is. Every function works on
the shapes an MCP call actually has — argument keys, opaque identifier strings,
and free-form tool output — so the same code serves a server kind it has never
seen.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_KEY_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})", re.IGNORECASE)
#: A run of identifier-ish characters — what a name looks like in any output format.
_FRAGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._#/-]*")

#: Tokens too common across a policy register to carry linking signal.
STOPWORDS = frozenset(
    """the a an and or of to in on for with by is are what any every no not it its
    this that these those from at as be been has have had which who whom whose
    each per one two both all some most more than then so such only own same
    other others into out up down over under again further once here there when
    where why how can could may might must shall should will would name id ids
    true false null none data type value values item items list""".split()
)


_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def name_tokens(name: str) -> list[str]:
    """Split a parameter name into its words: ``calendarId`` -> ``["calendar", "id"]``.

    Matching parameter names by substring is a trap: ``calendarId`` contains
    "end", ``timeMin`` contains "min", and a naive regex classifies a container
    key as a date filter. Splitting on camelCase and separators first makes the
    comparison exact.
    """
    spaced = _CAMEL_SPLIT_RE.sub(" ", name)
    return [token for token in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if token]


def normalize_key(name: str) -> str:
    """Reduce an argument key to its comparable form (``calendarId`` -> ``calendarid``)."""
    return _KEY_NORMALIZE_RE.sub("", name.lower())


def canonical_id(raw: str) -> str:
    """A container identifier reduced to its comparable core.

    Only decoration that carries no identity is removed: surrounding quotes, a
    leading sigil (``#channel``), and a trailing service domain
    (``…@group.calendar.google.com``).

    Path structure is deliberately **kept**. An earlier version also dropped
    everything before the last ``/``, which is right for ``owner/repo`` and
    destroys a filesystem, where ``sensitive/keys/id.pem`` and
    ``public/keys/id.pem`` are different assets with the same basename. Matching
    a qualified name against a bare one is a lookup concern, handled by
    :func:`identifier_candidates`, not something to throw away here.
    """
    value = raw.strip().strip("\"'").lstrip("#@")
    if "@" in value:
        value = value.split("@", 1)[0]
    return value.strip("/").lower()


def identifier_candidates(raw: str) -> list[str]:
    """Spellings of an identifier to try against a key table, best first.

    Two shapes of qualification exist and they pull in opposite directions:

    * a **qualifier prefix** — ``owner/repo``, ``workspace/project`` — where the
      tail is the container and the head only says where it lives, so leading
      segments are dropped;
    * a **hierarchy** — ``sensitive/hr/payroll.csv`` — where the head is the
      container and the tail is something inside it, so trailing segments are
      dropped and the nearest known ancestor wins.

    Trying the exact value first, then shorter tails, then shorter heads, serves
    both without knowing which kind a given server uses.
    """
    value = canonical_id(raw)
    if not value:
        return []
    parts = [part for part in value.split("/") if part]
    candidates = [value]
    candidates += ["/".join(parts[index:]) for index in range(1, len(parts))]
    candidates += ["/".join(parts[:index]) for index in range(len(parts) - 1, 0, -1)]
    seen: set[str] = set()
    return [c for c in candidates if c and not (c in seen or seen.add(c))]


#: A register description opening this way names what a *call* reached rather
#: than a container that exists on its own ("What a create/update/delete
#: targets", "What a history read or search returns"). Such a row can never be a
#: catalog entry: it has no standing identity for an argument to name. The
#: phrasing is a register-authoring convention, shared by every framework arm.
_CALL_TARGET_RE = re.compile(r"^\s*what\s+an?\s+", re.IGNORECASE)

#: Words marking a register row as describing something *leaving* the
#: organization. Deliberately verbs and directions, never boundary nouns: a row
#: reading "systems inside the CIP electronic security perimeter" describes an
#: asset within the boundary, not one crossing it.
_EGRESS_RE = re.compile(
    r"\b(leav\w*|outside|external|unrecallable|exits?|escapes?)\b", re.IGNORECASE
)


def describes_call_target(description: str) -> bool:
    """Whether a register description names a call's target, not a standing container."""
    return bool(_CALL_TARGET_RE.match(description))


def describes_egress(description: str) -> bool:
    """Whether a register description names data or identity leaving the organization."""
    return bool(_EGRESS_RE.search(description))


def _singular(token: str) -> str:
    """A crude plural strip, so ``Holidays`` in an output matches ``holiday`` in a register."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(text: str) -> list[str]:
    """Lowercased content tokens, stopwords and very short fragments dropped."""
    return [
        _singular(t) for t in _TOKEN_RE.findall(text.lower())
        if t not in STOPWORDS and len(t) > 2
    ]


def token_similarity(left: str, right: str) -> float:
    """Symmetric token-overlap score in ``[0, 1]`` between two short names."""
    left_tokens = set(_TOKEN_RE.findall(canonical_id(left)))
    right_tokens = set(_TOKEN_RE.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return 2 * len(left_tokens & right_tokens) / (len(left_tokens) + len(right_tokens))


#: Shortest token that may be matched by prefix. Below it, abbreviation matching
#: fires on noise ("id" would match "identity", "on" would match "onboarding").
_MIN_PREFIX_TOKEN = 3


def _token_matches(candidate: str, target: str) -> bool:
    """Whether one name token satisfies another, allowing abbreviation.

    Register ids abbreviate what the deployment spells out: a calendar named
    "Aurora Airways — Executive" is the register's ``aurora-exec``. Treating the
    shorter token as satisfied when it prefixes the longer one recovers that,
    and is directional enough not to fire on unrelated words.
    """
    if candidate == target:
        return True
    short, long = sorted((candidate, target), key=len)
    return len(short) >= _MIN_PREFIX_TOKEN and long.startswith(short)


def name_coverage(name: str, asset_id: str) -> float:
    """How much of a register id the deployment's own name accounts for.

    Deliberately asymmetric. A calendar called "Aurora Airways — Ops Team"
    contains everything ``aurora-team`` names, plus words of its own; a symmetric
    overlap score punishes it for the extra words and can leave a correct link
    below threshold. What matters is whether the *register id* is covered, not
    whether the name is economical.
    """
    wanted = set(_TOKEN_RE.findall(asset_id.lower()))
    if not wanted:
        return 0.0
    available = set(_TOKEN_RE.findall(canonical_id(name)))
    matched = sum(
        1 for token in wanted if any(_token_matches(token, other) for other in available)
    )
    return matched / len(wanted)


def email_domains(text: str) -> list[str]:
    """Every email domain appearing in a blob of text, lowercased."""
    return [domain.lower() for domain in _EMAIL_RE.findall(text)]


def inverse_document_frequency(documents: list[list[str]]) -> dict[str, float]:
    """IDF weights over a small corpus, so register-wide words carry no signal."""
    frequency: Counter[str] = Counter()
    for document in documents:
        frequency.update(set(document))
    total = max(len(documents), 1)
    return {token: math.log(total / count) + 1.0 for token, count in frequency.items()}


def weighted_overlap(
    observed: set[str], target: list[str], weights: dict[str, float]
) -> tuple[float, str | None]:
    """Cosine-like score between observed tokens and a target document.

    Returns the score and the single highest-weighted shared token, which is the
    evidence a human reads when auditing why an identifier was bound.
    """
    target_set = set(target)
    shared = observed & target_set
    if not shared:
        return 0.0, None
    numerator = sum(weights.get(token, 1.0) for token in shared)
    norm = math.sqrt(sum(weights.get(token, 1.0) for token in target_set)) or 1.0
    evidence = max(shared, key=lambda token: weights.get(token, 1.0))
    return numerator / norm, evidence


def windows_around(text: str, needle: str, radius: int = 160) -> list[tuple[str, int]]:
    """Slices of ``text`` around each occurrence of ``needle``, with its offset.

    Used to read the human-readable name a listing output places next to an
    identifier, without parsing the output's format. JSON objects, CSV rows and
    prose all put the two within a few dozen characters of each other, so a
    character window generalizes where a per-format parser would not.

    The offset is returned because a compact listing puts *every* container's
    name inside one window; only proximity distinguishes the one this identifier
    belongs to.
    """
    if not needle:
        return []
    found: list[tuple[str, int]] = []
    start = 0
    lowered, target = text.lower(), needle.lower()
    while True:
        index = lowered.find(target, start)
        if index < 0:
            return found
        left = max(0, index - radius)
        found.append((text[left : index + len(needle) + radius], index - left))
        start = index + len(needle)


def fragments_with_offsets(window: str) -> list[tuple[str, int]]:
    """Word-like fragments of a window, each with its character offset."""
    return [(match.group(0), match.start()) for match in _FRAGMENT_RE.finditer(window)]


__all__ = [
    "STOPWORDS",
    "canonical_id",
    "describes_call_target",
    "describes_egress",
    "email_domains",
    "identifier_candidates",
    "fragments_with_offsets",
    "inverse_document_frequency",
    "name_coverage",
    "name_tokens",
    "normalize_key",
    "token_similarity",
    "tokens",
    "weighted_overlap",
    "windows_around",
]
