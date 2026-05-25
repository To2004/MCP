"""Classify a tool's atomic ops from its README/description text.

Each rule is a small function that takes (tool_name, description, readme_excerpt)
and returns either a RuleHit or None. The public classify_from_readme()
function runs every rule and collects all hits.

Rule IDs follow the pattern: readme.<atomic_op_lower>.<short_name>
"""

from __future__ import annotations

import re

from .rules_base import Confidence, RuleHit


def _matches_any(text: str, patterns: list[str]) -> str | None:
    """Return the first pattern that matches text (case-insensitive), or None."""
    lower = text.lower()
    for pat in patterns:
        if re.search(rf"\b{pat}\b", lower):
            return pat
    return None


def _rule_execute_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"execute[sd]?\s+(?:shell|command|script|arbitrary|code)",
        r"run[s]?\s+(?:an?\s+)?(?:shell|command|script|arbitrary|code)",
        r"shell\s+command",
        r"eval(?:uate[sd]?)?",
        r"spawn[s]?\s+(?:an?\s+)?(?:new\s+)?process",
        r"subprocess",
        r"invoke[s]?\s+an?\s+command",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.execute.shell_keyword",
            atomic_op="EXECUTE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_delete_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"deletes?\s+(?:a|the|an|all|every|files?|rows?|records?|messages?|resources?|tables?)",
        r"permanently\s+delete[sd]?",
        r"removes?\s+(?:a|the|an|all|files?|rows?|records?|messages?|resources?|the\s+resource)",
        r"drops?\s+(?:a\s+)?(?:table|database|index)",
        r"destroys?\s+(?:a|the|an|all|files?|rows?|records?|messages?|resources?)",
        r"erases?\s+(?:a|the|an|all|files?|rows?|records?|messages?)",
        r"purges?\s+(?:a|the|an|all|files?|rows?|records?|messages?)",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.delete.keyword",
            atomic_op="DELETE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_overwrite_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"overwrites?",
        r"completely\s+overwrites?",
        r"replaces?\s+(?:the\s+)?content",
        r"replaces?\s+(?:an?\s+)?existing",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.overwrite.keyword",
            atomic_op="OVERWRITE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_schema_modify_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"alters?\s+(?:the\s+)?schema",
        r"modif(?:y|ies)\s+(?:the\s+)?(?:database\s+)?schema",
        r"creates?\s+(?:a\s+)?(?:new\s+)?table",
        r"adds?\s+(?:a\s+)?column",
        r"ddl\s+statement",
        r"create\s+table",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.schema_modify.keyword",
            atomic_op="SCHEMA_MODIFY",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_broadcast_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"posts?\s+(?:an?\s+)?(?:new\s+)?(?:message|update|notification)",
        r"sends?\s+(?:an?\s+)?(?:message|email|notification)",
        r"publish(?:e[sd])?",
        r"broadcasts?",
        r"reply\s+to",
        r"announce[sd]?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.broadcast.keyword",
            atomic_op="BROADCAST",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_write_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"inserts?\s+(?:a\s+)?(?:new\s+)?(?:row|record|entry|note|text\s+note)",
        r"writes?\s+(?:a\s+)?(?:new\s+)?file",
        r"appends?\s+(?:a\s+)?(?:note|entry|line|row|insight)",
        r"adds?\s+(?:a\s+)?(?:new\s+)?(?:row|record|entry|note|comment)",
        r"creates?\s+(?:a\s+)?(?:new\s+)?(?:issue|pr|pull\s+request|comment|gist)",
        r"posts?\s+(?:a\s+)?(?:new\s+)?(?:issue|pr|comment)",
        r"append_insight",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.write.keyword",
            atomic_op="WRITE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_modify_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"edits?\s+(?:a\s+)?(?:file|entry|note)",
        r"updates?\s+(?:an?\s+)?(?:existing\s+)?(?:issue|pr|file|record|entry|message)",
        r"renames?",
        r"modif(?:y|ies)\s+(?:an?\s+)?(?:existing|entry|record|file|note)",
        r"find-and-replace",
        r"patch(?:e[sd])?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.modify.keyword",
            atomic_op="MODIFY",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_move_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"moves?\s+(?:a\s+)?(?:file|directory|resource)",
        r"renames?\s+(?:a\s+)?(?:file|directory|branch|resource)",
        r"moves?\s+or\s+renames?",
        r"relocate[sd]?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.move.keyword",
            atomic_op="MOVE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_create_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"creates?\s+(?:a\s+)?(?:new\s+)?(?:directory|folder|branch|repository|repo|gist)",
        r"creates?\s+(?:a\s+)?(?:directory|folder)\s+and",
        r"makes?\s+(?:a\s+)?(?:new\s+)?(?:directory|folder)",
        r"forks?\s+(?:a\s+)?(?:repository|repo)",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.create.keyword",
            atomic_op="CREATE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_read_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    name_lower = name.lower()
    patterns = [
        r"returns?\s+(?:the\s+)?(?:full\s+)?(?:text\s+)?contents?",
        r"returns?\s+(?:the\s+)?(?:most\s+recent\s+)?(?:n\s+)?messages",
        r"reads?\s+(?:a\s+)?file",
        r"gets?\s+(?:the\s+)?(?:contents?|file|messages?)",
        r"fetches?\s+(?:the\s+)?(?:contents?|file|messages?)",
        r"views?\s+(?:the\s+)?(?:contents?|file)",
        r"executes?\s+(?:a\s+)?sql\s+select",
        r"select\s+statement",
    ]
    matched = _matches_any(haystack, patterns)
    name_match = name_lower.startswith(("read_", "get_", "fetch_", "view_")) and not any(
        kw in name_lower for kw in ("info", "metadata", "schema", "size", "stat", "profile")
    )
    if matched or name_match:
        return RuleHit(
            rule_id="readme.read.keyword",
            atomic_op="READ",
            confidence=Confidence.HIGH,
            matched_on=matched or f"name_prefix:{name_lower.split('_')[0]}_",
        )
    return None


def _rule_search_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"searches?\s+(?:for|the|across|files?|code|index|messages|matching\s+paths)",
        r"finds?\s+(?:files?|matches|messages|issues|results|paths)\s+matching",
        r"glob\s+pattern",
        r"runs?\s+(?:github\s+)?(?:code\s+)?search",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or name.lower().startswith("search_"):
        return RuleHit(
            rule_id="readme.search.keyword",
            atomic_op="SEARCH",
            confidence=Confidence.HIGH,
            matched_on=matched or "name_prefix:search_",
        )
    return None


_METADATA_NAME_KEYWORDS = ("info", "stat", "schema", "profile", "metadata", "size")


def _rule_metadata_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"returns?\s+metadata",
        r"returns?\s+(?:the\s+)?(?:size|timestamps?|type|permissions|profile|attributes)",
        r"returns?\s+(?:the\s+)?(?:create\s+table\s+)?ddl",
        r"describes?\s+(?:a\s+)?(?:table|schema|profile)",
        r"file\s+info",
        r"get\s+info",
        r"metadata\s+about\s+(?:a\s+)?(?:file|directory|table)",
        r"detailed\s+(?:slack\s+)?profile",
    ]
    matched = _matches_any(haystack, patterns)
    name_lower = name.lower()
    name_match = (
        name_lower.startswith(("get_", "describe_"))
        and any(kw in name_lower for kw in _METADATA_NAME_KEYWORDS)
    )
    if matched or name_match:
        return RuleHit(
            rule_id="readme.metadata.keyword",
            atomic_op="METADATA",
            confidence=Confidence.HIGH,
            matched_on=matched or "name_pattern:get/describe_info",
        )
    return None


def _rule_list_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        (
            r"lists?\s+(?:the\s+)?(?:immediate\s+)?(?:contents?|channels?|tables?|files?|"
            r"branches?|users?|members?|directories|directory|notifications?|issues?|releases?)"
        ),
        r"enumerate[sd]?",
        r"returns?\s+(?:the\s+)?names\s+of\s+all",
        r"returns?\s+(?:a\s+)?(?:paginated\s+)?list",
        r"directory\s+listing",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or name.lower().startswith("list_"):
        return RuleHit(
            rule_id="readme.list.keyword",
            atomic_op="LIST",
            confidence=Confidence.HIGH,
            matched_on=matched or "name_prefix:list_",
        )
    return None


_RULES = [
    _rule_execute_keywords,
    _rule_delete_keywords,
    _rule_overwrite_keywords,
    _rule_schema_modify_keywords,
    _rule_broadcast_keywords,
    _rule_write_keywords,
    _rule_modify_keywords,
    _rule_move_keywords,
    _rule_create_keywords,
    _rule_read_keywords,
    _rule_search_keywords,
    _rule_metadata_keywords,
    _rule_list_keywords,
]


def classify_from_readme(
    tool_name: str, description: str, readme_excerpt: str
) -> list[RuleHit]:
    """Run every README-rule against the inputs and collect hits.

    A single tool can yield multiple hits for different atomic ops. Hits are
    de-duplicated by (rule_id, atomic_op) so a rule fires at most once per
    tool, but multiple rules can tag the same op.
    """
    seen: set[tuple[str, str]] = set()
    hits: list[RuleHit] = []
    for rule in _RULES:
        hit = rule(tool_name, description, readme_excerpt)
        if hit is None:
            continue
        key = (hit.rule_id, hit.atomic_op)
        if key in seen:
            continue
        seen.add(key)
        hits.append(hit)
    return hits
