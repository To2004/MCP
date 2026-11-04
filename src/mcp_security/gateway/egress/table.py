"""B10: the per-platform egress table, so a hosting platform's callers count as one network.

Hosted agent platforms send every tenant's MCP calls from a few published ranges, so all their
callers share one /16, and after three of them the org discount waves the next one through. A
route's ``shared_egress`` names a table of those ranges (``platform_egress.json`` here is the
shipped one). Every address inside a platform's ranges has the network value
``platform:<label>``: it stays in the caller's own Footprint (a platform he never used is new),
it is never pseudonymised (PS10), and the engine never applies the org discount to it.

Each entry is marked ``verified`` (someone opened ``source`` on ``checked`` and copied
``cidrs`` from it) or ``UNVERIFIED`` (a placeholder, or a range nobody has checked). Only
verified ranges are used unless the table sets ``use_unverified``. Ranges are never invented.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from datetime import date
from ipaddress import ip_network
from pathlib import Path

#: The version of an egress-table file this gateway reads, and its entries' marks.
EGRESS_TABLE_VERSION = 1
EGRESS_VERIFIED, EGRESS_UNVERIFIED = "verified", "UNVERIFIED"
EGRESS_STATUSES = (EGRESS_VERIFIED, EGRESS_UNVERIFIED)
#: The keys an egress-table file may hold at its top level; any other is a typo, refused.
TABLE_KEYS = frozenset({"version", "use_unverified", "platforms"})
#: The network value of an address inside a platform's range (Part A: "platform:" + label).
PLATFORM_PREFIX = "platform:"
PLATFORM_LABEL = re.compile(r"[a-z0-9][a-z0-9_.-]{0,62}")
SOURCE_SCHEMES = ("https://", "http://")
#: The shipped table: the ranges checked so far, and placeholders for the rest.
DEFAULT_EGRESS_TABLE = Path(__file__).with_name("platform_egress.json")


def platform_network(label: str) -> str:
    """The network value of an address in platform ``label``'s egress ranges."""
    return f"{PLATFORM_PREFIX}{label}"


def is_platform_network(value: str | None) -> bool:
    """Whether a network value is a platform's (no org discount; never pseudonymised)."""
    return bool(value) and value.startswith(PLATFORM_PREFIX)


@dataclass(frozen=True)
class EgressPlatform:
    """One hosting platform's egress ranges. Every address inside them counts as one network,
    :func:`platform_network` of the label. A ``verified`` entry names the page its ranges were
    copied from and the day it was opened; an ``UNVERIFIED`` one is a placeholder (no ranges)
    or a range nobody has checked."""

    label: str
    status: str
    cidrs: tuple[str, ...] = ()
    source: str | None = None
    checked: str | None = None  # ISO date the source was opened
    note: str | None = None

    def __post_init__(self) -> None:
        where = f"egress platform {self.label!r}"
        if not (isinstance(self.label, str) and PLATFORM_LABEL.fullmatch(self.label)):
            raise ValueError(f"{where}: a label is lowercase letters, digits, '_', '.', '-'")
        if self.status not in EGRESS_STATUSES:
            raise ValueError(f"{where}: status must be one of {EGRESS_STATUSES}")
        for cidr in self.cidrs:
            try:
                if not isinstance(cidr, str):
                    raise TypeError(cidr)
                ip_network(cidr)  # strict: a range with host bits set is a typo
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{where}: bad CIDR {cidr!r}") from exc
        if self.status == EGRESS_VERIFIED:
            _check_verified(self, where)

    @property
    def network(self) -> str:
        """The network value of an address in this platform's ranges."""
        return platform_network(self.label)


def _check_verified(platform: EgressPlatform, where: str) -> None:
    """A verified entry has ranges, an http(s) source and an ISO ``checked`` date."""
    if not platform.cidrs:
        raise ValueError(f"{where}: a verified platform lists its ranges")
    if not (isinstance(platform.source, str) and platform.source.startswith(SOURCE_SCHEMES)):
        raise ValueError(f"{where}: a verified platform names the page it was copied from")
    try:
        date.fromisoformat(str(platform.checked))
    except ValueError as exc:
        raise ValueError(f"{where}: 'checked' must be the ISO date the source was opened") from exc


@dataclass(frozen=True)
class EgressTable:
    """The egress table a route's ``shared_egress`` names. Only verified platforms are used,
    unless ``use_unverified`` is set; the ranges in use may not overlap across platforms, so
    an address names at most one platform. ``digest`` is the SHA-256 of the file the table
    was read from (None when built in code), so the route can pin the ranges it used."""

    platforms: tuple[EgressPlatform, ...] = ()
    use_unverified: bool = False
    digest: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        labels = [p.label for p in self.platforms]
        if len(set(labels)) != len(labels):
            raise ValueError("egress table: each platform label appears once")
        if not isinstance(self.use_unverified, bool):
            raise ValueError("egress table: use_unverified must be true or false")
        ranges = [(p.label, ip_network(c)) for p in self.in_use for c in p.cidrs]
        for i, (label, net) in enumerate(ranges):
            for other, other_net in ranges[i + 1 :]:
                # overlaps() is False across IPv4 and IPv6, so mixed tables need no guard
                if other != label and net.overlaps(other_net):
                    raise ValueError(f"egress table: {label!r} and {other!r} overlap")

    @property
    def in_use(self) -> tuple[EgressPlatform, ...]:
        """The platforms whose ranges count: verified ones, and UNVERIFIED ones if opted in."""
        return tuple(
            p for p in self.platforms if p.status == EGRESS_VERIFIED or self.use_unverified
        )

    @property
    def unverified(self) -> tuple[str, ...]:
        """Labels of the UNVERIFIED entries, for the gateway to name on its start line."""
        return tuple(p.label for p in self.platforms if p.status == EGRESS_UNVERIFIED)

    def shared_networks(self) -> tuple[tuple[str, str], ...]:
        """The (label, CIDR) pairs in use, in file order: ``BehaviourConfig.shared_networks``."""
        return tuple((p.label, cidr) for p in self.in_use for cidr in p.cidrs)


def load_egress_table(path: str | Path = DEFAULT_EGRESS_TABLE) -> EgressTable:
    """An egress-table file, ``{"version": 1, "use_unverified": false, "platforms":
    [{"label", "status", "cidrs", "source", "checked", "note"}, ...]}``. Fails loudly on
    another version, an unknown key, a bad range or an unchecked "verified" entry."""
    data = Path(path).read_bytes()
    raw = json.loads(data)
    if not isinstance(raw, dict) or raw.get("version") != EGRESS_TABLE_VERSION:
        raise ValueError(f"egress table {path}: expected version {EGRESS_TABLE_VERSION}")
    if unknown := set(raw) - TABLE_KEYS:
        raise ValueError(f"egress table {path}: unknown keys {sorted(unknown)}")
    entries = raw.get("platforms")
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise ValueError(f"egress table {path}: 'platforms' must be a list of objects")
    known = {f.name for f in fields(EgressPlatform)}
    platforms = []
    for entry in entries:
        if unknown := set(entry) - known:
            raise ValueError(f"egress table {path}: unknown keys {sorted(unknown)}")
        if not isinstance(entry.get("cidrs", []), list):
            raise ValueError(f"egress table {path}: 'cidrs' must be a list")
        platforms.append(EgressPlatform(**{**entry, "cidrs": tuple(entry.get("cidrs", ()))}))
    return EgressTable(
        tuple(platforms),
        use_unverified=raw.get("use_unverified", False),
        digest=hashlib.sha256(data).hexdigest(),
    )
