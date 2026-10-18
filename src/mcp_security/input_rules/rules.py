"""Run-time lookup of tool-input rules: argument values to a level from 1 to 5.

The rules are written once per tool at design time (v13,
``docs/standards/tool-input-levels.md``; v12 stage 2 before it) for the inputs
that can change how risky a call is. At call time nothing here asks a model:
every rule is a table lookup, a threshold comparison, a lowercase substring test
or a domain comparison.

Level 1 is the safest realistic value and 5 the riskiest; an ordinary call gets
1 to 3. A call's input level is the maximum over its inputs, the same
never-under-score principle as ``binding.resolver.worst_severity``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

LEVELS = frozenset({1, 2, 3, 4, 5})
KINDS = frozenset({"ranges", "register", "keywords", "values", "domain", "email"})
MEASURES = frozenset({"value", "length", "hour_of_day", "weekday", "span_hours",
                      "hours_from_now"})
#: Measures that grow without bound: the top range must be open, or values past
#: it would fall back to a default that can sit below the top range's level.
GROWING_MEASURES = frozenset({"value", "length", "span_hours"})
#: The ``email`` kind's fixed ladder, from the policy: its own people are the
#: normal audience, any outside address is unusual. Own, partner and flagged
#: domains are lists only the policy can give; a personal mailbox can be read
#: from the address itself.
EMAIL_LEVELS = {"own": 1, "partner": 2, "unreadable": 3, "other": 4, "personal": 5,
                "flagged": 5}
#: The level a value naming or carrying a credential gets.
CREDENTIAL_LEVEL = 5
#: Fragments that name or carry a credential, matched like ``keywords`` fragments.
CREDENTIAL_WORDS = (
    "password", "passwd", "secret", "token", "credential", "api_key", "apikey", "api key",
    "access_key", "private key", "private_key", "id_rsa", "id_ed25519", "id_ecdsa", ".ssh",
    ".env", ".pem",
)
#: A value that looks like a file path: a separator, or a file extension at the end.
_PATH_LIKE = re.compile(r"[/\\]|\.[A-Za-z0-9]{1,5}$")
#: Personal mailbox providers: an address here leaves the organization's control.
PERSONAL_MAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "icloud.com", "me.com", "aol.com", "proton.me", "protonmail.com", "gmx.com",
    "mail.com", "yandex.com", "zoho.com"})


@dataclass(frozen=True)
class OrgDomains:
    """The organization's address lists, from its policy or deployment."""

    own: tuple[str, ...] = ()
    partner: tuple[str, ...] = ()
    flagged: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputLevel:
    """One input's level for one call, and why."""

    path: str
    level: int | None  # None: absent, and absence adds nothing
    matched: str  # what decided it, e.g. "range 500..5000", "asset x", "default"
    unresolved: bool = False  # the value could not be read the way the rule expects


@dataclass(frozen=True)
class CallLevel:
    """A call's input level: the highest input level, and which inputs set it."""

    level: int | None
    set_by: tuple[str, ...]
    inputs: tuple[InputLevel, ...]


# --------------------------------------------------------------------------- validation


def _is_level(x: object) -> bool:
    return isinstance(x, int) and not isinstance(x, bool) and x in LEVELS


def _is_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _bound(x: object, open_end: float) -> float:
    return float(x) if _is_number(x) else open_end


def reachable_ranges(ranges: list) -> list[dict]:
    """The ranges some value can match. Ranges are tried in order and the first
    match wins, so a range wholly inside the earlier ones is never reached."""
    reached, covered = [], []  # covered: (lo, hi) intervals of the earlier ranges
    for r in ranges:
        if not isinstance(r, dict):
            continue
        lo, hi = _bound(r.get("min"), float("-inf")), _bound(r.get("max"), float("inf"))
        if lo >= hi:
            continue
        point = lo  # walk the range left to right over the earlier intervals
        for a, b in sorted(covered):
            if a <= point < b:
                point = b
        if point < hi:
            reached.append(r)
        covered.append((lo, hi))
    return reached


def register_table(rule: dict, assets: dict[str, int] | None = None) -> dict[str, int]:
    """The asset table a ``register`` rule looks names up in: ``assets`` (the
    tool's, passed at run time) plus the rule's own ``assets`` (v13 writes the
    policy's whole register into the rule), entries that are not levels left out."""
    own = rule.get("assets")
    table = dict(assets or {})
    if isinstance(own, dict):
        table.update({str(a): lv for a, lv in own.items() if _is_level(lv)})
    return table


def levels_covered(rule: dict, assets: dict[str, int] | None = None) -> set[int]:
    """The levels a rule reaches with entries of its own; ``default`` does not count.

    Only entries some value can reach count: a range wholly inside earlier
    ranges, or a repeated value, never decides a level. A ``register`` rule also
    reaches the scanned level of every asset in its table (``register_table``)."""
    kind = rule.get("kind")
    entries: list = []
    if kind == "ranges":
        entries = [r.get("level") for r in reachable_ranges(rule.get("ranges") or [])]
    elif kind in ("keywords", "register"):
        entries = [g.get("level") for g in rule.get("groups") or [] if isinstance(g, dict)]
        if kind == "register":
            entries += list(register_table(rule, assets).values())
            entries += [o.get("level") for o in rule.get("overrides") or [] if isinstance(o, dict)]
    elif kind == "values":
        seen: set[str] = set()
        for e in rule.get("values") or []:
            if isinstance(e, dict) and str(e.get("value")).casefold() not in seen:
                seen.add(str(e.get("value")).casefold())
                entries.append(e.get("level"))
    elif kind == "domain":
        entries = [rule.get("internal"), rule.get("external")]
    elif kind == "email":
        entries = list(EMAIL_LEVELS.values())
    return {x for x in entries if _is_level(x)}


def rule_problems(row: dict, tool_paths: set[str] | frozenset[str], *,
                  all_levels: bool = False, assets: dict[str, int] | None = None) -> list[str]:
    """Design-time check of one input's rule; an empty list means usable.

    A rule that fails here is rejected when it is written, never discovered
    broken during a live call. With ``all_levels`` (v13), each level 1 to 5 must
    also be reached by an entry of the rule's own; ``assets`` are the tool's
    reachable assets with their scanned level, which a ``register`` rule reaches."""
    problems: list[str] = []
    rule = row.get("rule")
    if not isinstance(rule, dict) or rule.get("kind") not in KINDS:
        return ["rule is missing or of an unknown kind"]
    absent = row.get("when_absent")
    if absent is not None and not _is_level(absent):
        problems.append("when_absent is not null or a level 1-5")
    kind = rule["kind"]
    if kind not in ("domain", "email") and not _is_level(rule.get("default")):
        problems.append("default is not a level 1-5")
    if kind == "ranges":
        problems += _range_problems(rule, tool_paths)
    elif kind == "register":
        own = rule.get("assets")
        if own is not None and not (isinstance(own, dict) and all(
                isinstance(a, str) and _is_level(lv) for a, lv in own.items())):
            problems.append("a register rule's assets must map asset names to levels 1-5")
        for o in rule.get("overrides") or []:
            if not (isinstance(o, dict) and isinstance(o.get("asset"), str)
                    and _is_level(o.get("level"))):
                problems.append("a register override needs an asset name and a level 1-5")
        problems += _group_problems(rule.get("groups") or [], "register")
    elif kind == "keywords":
        groups = rule.get("groups")
        if not isinstance(groups, list) or not groups:
            problems.append("keywords rule has no groups")
        problems += _group_problems(groups or [], "keywords")
    elif kind == "values":
        entries = rule.get("values")
        if not isinstance(entries, list) or not entries:
            problems.append("values rule lists no values")
        for e in entries or []:
            if not isinstance(e, dict) or "value" not in e or not _is_level(e.get("level")):
                problems.append("a values entry has no value or no level 1-5")
    elif kind == "domain":
        if not (_is_level(rule.get("internal")) and _is_level(rule.get("external"))):
            problems.append("domain rule needs internal and external levels 1-5")
    if all_levels and not problems:
        if kind not in ("domain", "email") and rule["default"] > ORDINARY_TOP:
            problems.append(f"default is {rule['default']}: a value that matches nothing is "
                            f"ordinary, so the default is 1 to {ORDINARY_TOP}")
        missing = sorted(LEVELS - levels_covered(rule, assets))
        if missing:
            problems.append(f"levels {missing} have no entry of their own; every level 1 to 5 "
                            "needs at least one")
        if kind == "register":
            problems += _name_word_clashes(rule.get("groups") or [], register_table(rule, assets))
    return problems


#: v13: the highest level an ordinary value gets. A value no entry matches is
#: ordinary, so a rule's ``default`` may not exceed it.
ORDINARY_TOP = 3
#: How far a ``register`` name word may sit from a listed asset whose name contains it.
NAME_WORD_TOLERANCE = 1


def _clashes(word: str, level: int, assets: dict[str, int]) -> bool:
    return bool(word.strip()) and any(
        word.casefold() in asset.casefold() and abs(level - asset_level) > NAME_WORD_TOLERANCE
        for asset, asset_level in assets.items())


def drop_clashing_name_words(rule: dict, assets: dict[str, int]) -> dict:
    """``rule`` without the ``register`` name words that contradict a listed asset.

    Such a word adds nothing for the asset itself, which the scan rates first,
    and rates other names with that word the opposite way; dropping it is a
    safe repair. Only ``register`` rules are checked: in a path or a query the
    same word means something else (``config`` in a file path is not the
    ``grid-infra-config`` repository). Blank fragments are dropped from
    ``register`` and ``keywords`` groups, and a group left empty is dropped too.
    Other kinds are returned as is."""
    kind = rule.get("kind")
    if kind not in ("register", "keywords") or not isinstance(rule.get("groups"), list):
        return rule
    groups = []
    for g in rule["groups"]:
        if not (isinstance(g, dict) and isinstance(g.get("contains"), list)
                and _is_level(g.get("level"))):
            groups.append(g)
            continue
        kept = [w for w in g["contains"] if not isinstance(w, str) or (
            w.strip() and not (kind == "register" and _clashes(w, g["level"], assets)))]
        if kept:
            groups.append({**g, "contains": kept})
    return {**rule, "groups": groups}


def dropped_name_words(before: dict, after: dict) -> list[tuple[str, int]]:
    """The (word, level) pairs ``drop_clashing_name_words`` removed, blank ones aside."""
    def words(rule: dict) -> set[tuple[str, int]]:
        return {(w, g["level"]) for g in rule.get("groups") or []
                if isinstance(g, dict) and _is_level(g.get("level"))
                and isinstance(g.get("contains"), list)
                for w in g["contains"] if isinstance(w, str) and w.strip()}
    return sorted(words(before) - words(after))


def _name_word_clashes(groups: list[dict], assets: dict[str, int]) -> list[str]:
    """Name words that contradict the listed assets they are part of.

    A name word rates names nobody listed; when it is part of a listed asset's
    name (``scada`` in ``helios-scada-gateway``), it must agree with that
    asset's scanned level, or other names with the same word get the opposite
    rating."""
    clashes = sorted({(w, g["level"], asset, level) for g in groups for w in g["contains"]
                      for asset, level in assets.items()
                      if w.strip() and w.casefold() in asset.casefold()
                      and abs(g["level"] - level) > NAME_WORD_TOLERANCE})
    return [f"name word {w} is at level {lv} but is part of the listed asset {asset}, which "
            f"is level {level}; keep it within one level of the asset, or drop it"
            for w, lv, asset, level in clashes]


def _group_problems(groups: list, kind: str) -> list[str]:
    problems = []
    for g in groups:
        words = g.get("contains") if isinstance(g, dict) else None
        if not isinstance(words, list) or not words or not all(
                isinstance(w, str) and w.strip() for w in words):
            problems.append(f"a {kind} group has no plain-text fragments")
        if not isinstance(g, dict) or not _is_level(g.get("level")):
            problems.append(f"a {kind} group has no level 1-5")
    return problems


def _range_problems(rule: dict, tool_paths) -> list[str]:
    problems = []
    if rule.get("measure") not in MEASURES:
        problems.append(f"unknown measure {rule.get('measure')!r}")
    if rule.get("measure") == "span_hours" and _match_path(rule.get("with"), tool_paths) is None:
        problems.append("span_hours names no sibling input in 'with'")
    ranges = rule.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        return problems + ["ranges rule has no ranges"]
    for r in ranges:
        if not isinstance(r, dict) or not _is_level(r.get("level")):
            problems.append("a range has no level 1-5")
            continue
        lo, hi = r.get("min"), r.get("max")
        if (lo is not None and not _is_number(lo)) or (hi is not None and not _is_number(hi)):
            problems.append("a range bound is not a number or null")
        elif lo is not None and hi is not None and lo >= hi:
            problems.append(f"a range has min {lo} not below max {hi}")
    if rule.get("measure") in GROWING_MEASURES and not any(
            isinstance(r, dict) and r.get("max") is None for r in ranges):
        problems.append("no range is open at the top: values above the highest max "
                        "would fall back to the default")
    return problems


def _match_path(path: object, paths) -> str | None:
    """The member of ``paths`` that ``path`` names, ignoring ``[]`` list markers."""
    if not isinstance(path, str):
        return None
    if path in paths:
        return path
    bare = path.replace("[]", "")
    return next((p for p in paths if p.replace("[]", "") == bare), None)


# --------------------------------------------------------------------------- evaluation


def values_at(args: dict, path: str) -> list:
    """Every value at a dotted path; ``name[]`` walks into a list.

    ``attendees[].email`` returns one email per attendee. A ``[]`` step over a
    scalar takes the scalar, because some inputs accept a value or a list."""
    nodes: list = [args]
    for step in path.split("."):
        name, walk = step.removesuffix("[]"), step.endswith("[]")
        found: list = []
        for node in nodes:
            if not isinstance(node, dict) or name not in node or node[name] is None:
                continue
            value = node[name]
            if walk and isinstance(value, list):
                found.extend(v for v in value if v is not None)
            else:
                found.append(value)
        nodes = found
    return nodes


def _datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _aligned(a: datetime, b: datetime) -> tuple[datetime, datetime]:
    """Make two date-times comparable when only one carries a time zone."""
    if (a.tzinfo is None) != (b.tzinfo is None):
        return a.replace(tzinfo=None), b.replace(tzinfo=None)
    return a, b


def _measure(rule: dict, value: object, args: dict, now: datetime) -> float | None:
    measure = rule.get("measure")
    if measure == "value":
        if _is_number(value):
            return float(value)
        try:
            return float(str(value))
        except ValueError:
            return None
    if measure == "length":
        return float(len(value)) if isinstance(value, (list, str, dict)) else None
    when = _datetime(value)
    if when is None:
        return None
    if measure == "hour_of_day":
        return when.hour + when.minute / 60
    if measure == "weekday":
        return float(when.weekday())
    if measure == "hours_from_now":
        a, b = _aligned(when, now)
        return (a - b).total_seconds() / 3600
    if measure == "span_hours":
        # one end alone reads from it up to now (``after`` with no ``before``)
        others = [d for d in map(_datetime, values_at(args, rule.get("with", ""))) if d]
        a, b = _aligned(when, others[0] if others else now)
        return abs((a - b).total_seconds()) / 3600
    return None


def _match_asset(value: object, assets: dict[str, int],
                 aliases: dict[str, str] | None = None) -> tuple[str, int] | None:
    """The most sensitive listed asset the value names, if any.

    ``aliases`` maps a raw identifier to an asset id: a deployment knows its own
    channel and calendar ids (``C0BL...`` is ``vireo-unblinding``). Without an
    alias, matches an asset id equal to the value or contained in it. Opaque
    identifiers with no alias need the traffic-discovered bindings of
    ``mcp_security.binding``."""
    alias = (aliases or {}).get(str(value).strip())
    if alias is not None and alias in assets:
        return alias, assets[alias]
    text = str(value).casefold().replace("_", "-").replace(" ", "-")
    hits = [(level, asset) for asset, level in assets.items()
            if asset.casefold() == text or asset.casefold() in text]
    if not hits:
        return None
    level, asset = max(hits)
    return asset, level


def _domain_of(value: object) -> str | None:
    text = str(value).strip().casefold()
    if "@" in text:
        return text.rsplit("@", 1)[1] or None
    if "://" in text:
        return urlparse(text).hostname
    return None


def fragment_in(fragment: str, text: str) -> bool:
    """True when ``fragment`` occurs in ``text`` at the start of a word.

    ``site`` matches ``site-a`` and ``sites`` but not ``website``; a fragment
    that starts with a separator (``.env``, ``/keys``) matches anywhere."""
    frag = fragment.casefold()
    if not frag:
        return False
    if not frag[0].isalnum():
        return frag in text
    return re.search(r"(?<![0-9a-z])" + re.escape(frag), text) is not None


def credential_path(value: object) -> str | None:
    """The credential fragment in a path-like value (``deploy/.env``), if any.

    Applied to every input whatever its rule, so a key file is rated 5 even when
    a path is looked up as an asset name; a bare name (a repository called
    ``token-service``) is not a path and is left to its rule."""
    if not isinstance(value, str) or not _PATH_LIKE.search(value.strip()):
        return None
    text = value.casefold()
    return next((w for w in CREDENTIAL_WORDS if fragment_in(w, text)), None)


def _keyword_hit(groups: list[dict], value: object) -> tuple[int, str] | None:
    """The highest-level group with a fragment the lowercased value contains at a word start."""
    text = str(value).casefold()
    hits = [(g["level"], w) for g in groups for w in g["contains"] if fragment_in(w, text)]
    return max(hits) if hits else None


def _in_domains(domain: str, domains: tuple[str, ...]) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in domains)


_ADDRESS = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def _email_level(value: object, org: OrgDomains) -> tuple[int, str, bool]:
    """The ``email`` kind's fixed ladder: own domain 1, partner 2, no readable
    domain 3, another organization 4, a personal mailbox or a flagged domain 5.
    Without the organization's own domains every other address is treated as
    outside (4), never assumed internal, and flagged unresolved. A list or an
    object (attendee records) is searched for addresses; the highest level counts."""
    if isinstance(value, (list, dict)):
        found = [_email_level(m, org) for m in _ADDRESS.findall(json.dumps(value))]
        if not found:
            return EMAIL_LEVELS["unreadable"], "no readable address", True
        return max(found, key=lambda g: g[0])
    domain = _domain_of(value)
    if domain is None:
        return EMAIL_LEVELS["unreadable"], "no readable domain", True
    for name in ("own", "flagged", "partner"):
        if _in_domains(domain, getattr(org, name)):
            return EMAIL_LEVELS[name], f"{name} domain {domain}", False
    if domain in PERSONAL_MAIL_DOMAINS:
        return EMAIL_LEVELS["personal"], f"personal mailbox {domain}", False
    return EMAIL_LEVELS["other"], f"other domain {domain}", not org.own


def _value_level(rule: dict, value: object, args: dict, *, assets: dict[str, int],
                 aliases: dict[str, str], org: OrgDomains,
                 now: datetime) -> tuple[int, str, bool]:
    kind = rule["kind"]
    if kind == "ranges":
        x = _measure(rule, value, args, now)
        if x is None:
            return rule["default"], "default (value not readable for this measure)", True
        for r in rule["ranges"]:
            lo, hi = r.get("min"), r.get("max")
            if (lo is None or x >= lo) and (hi is None or x < hi):
                return r["level"], f"{rule['measure']} {x:g} in {lo}..{hi}", False
        return rule["default"], f"{rule['measure']} {x:g}: no range, default", False
    if kind == "register":
        hit = _match_asset(value, register_table(rule, assets), aliases)
        if hit is None:
            words = _keyword_hit(rule.get("groups") or [], value)
            if words is not None:
                return words[0], f"name contains {words[1]}", False
            return rule["default"], "names no listed asset, default", True
        override = next((o["level"] for o in rule.get("overrides") or []
                         if o.get("asset") == hit[0]), None)
        if override is not None:
            return override, f"asset {hit[0]} (policy override)", False
        return hit[1], f"asset {hit[0]}", False
    if kind == "keywords":
        hit = _keyword_hit(rule["groups"], value)
        if hit is None:
            return rule["default"], "no keyword, default", False
        return hit[0], f"contains {hit[1]}", False
    if kind == "email":
        return _email_level(value, org)
    if kind == "values":
        # an opaque id the deployment knows (a calendar id) is compared by its asset name
        seen = {str(value).casefold(), aliases.get(str(value).strip(), "").casefold()} - {""}
        for entry in rule["values"]:
            if str(entry["value"]).casefold() in seen:
                return entry["level"], f"value {entry['value']}", False
        return rule["default"], "unlisted value, default", False
    # domain: without known org domains, or without a readable domain, assume external
    domain = _domain_of(value)
    if domain is None or not org.own:
        return rule["external"], "domain unknown, treated as external", True
    internal = _in_domains(domain, org.own)
    return (rule["internal"], f"internal domain {domain}", False) if internal else (
        rule["external"], f"external domain {domain}", False)


def evaluate_input(row: dict, args: dict, *, assets: dict[str, int] | None = None,
                   aliases: dict[str, str] | None = None, org_domains: tuple[str, ...] = (),
                   now: datetime | None = None, partner_domains: tuple[str, ...] = (),
                   flagged_domains: tuple[str, ...] = ()) -> InputLevel:
    """The level one input's rule gives for this call's arguments.

    A list input takes the highest level among its items. ``org_domains``,
    ``partner_domains`` and ``flagged_domains`` are the organization's address
    lists, read by the ``domain`` and ``email`` kinds."""
    path, rule = row["path"], row["rule"]
    values = values_at(args, path)
    absent = not values
    if absent:
        if row.get("when_absent") is not None:
            return InputLevel(path, row["when_absent"], "absent")
        if row.get("schema_default") is None:
            return InputLevel(path, None, "absent, adds nothing")
        values = [row["schema_default"]]  # left out: the server uses its default
    now = now or datetime.now(timezone.utc)
    org = OrgDomains(tuple(org_domains), tuple(partner_domains), tuple(flagged_domains))
    graded = [_value_level(rule, v, args, assets=assets or {}, aliases=aliases or {},
                           org=org, now=now) for v in values]
    graded += [(CREDENTIAL_LEVEL, f"credential-shaped path ({w})", False)
               for w in map(credential_path, values) if w]
    level, matched, unresolved = max(graded, key=lambda g: g[0])
    if absent:
        # the server's own default is an ordinary call; leaving an input out is
        # rated above that only through ``when_absent``, which the policy must back
        level = min(level, ORDINARY_TOP)
    return InputLevel(path, level, ("absent, default: " if absent else "") + matched, unresolved)


def evaluate_call(rows: list[dict], args: dict, *, assets: dict[str, int] | None = None,
                  aliases: dict[str, str] | None = None, org_domains: tuple[str, ...] = (),
                  now: datetime | None = None, partner_domains: tuple[str, ...] = (),
                  flagged_domains: tuple[str, ...] = ()) -> CallLevel:
    """A call's input level: the maximum over its rule-bearing inputs.

    ``rows`` are one tool's stage 2 rows; rows without a rule (inputs stage 1
    dropped) are skipped, so an unimportant input can never raise the level."""
    levels = tuple(evaluate_input(r, args, assets=assets, aliases=aliases,
                                  org_domains=org_domains, now=now,
                                  partner_domains=partner_domains,
                                  flagged_domains=flagged_domains)
                   for r in rows if isinstance(r.get("rule"), dict))
    scored = [lv for lv in levels if lv.level is not None]
    if not scored:
        return CallLevel(None, (), levels)
    top = max(lv.level for lv in scored)
    return CallLevel(top, tuple(lv.path for lv in scored if lv.level == top), levels)
