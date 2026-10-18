"""Mechanical, non-LLM structural fact extraction for one tool's declared inputs.

Layer A of ``docs/standards/tool-input-features.md``: cardinality, domain
(open/closed), declared bounds, required, default -- every fact the JSON
Schema states outright. Computed here, in plain Python, so the model is
handed these as given context rather than asked to re-derive (or
contradict) them. No LLM, no network, deterministic.
"""

from __future__ import annotations


def _flatten_combinators(spec: dict) -> list[dict]:
    """``spec`` plus every ``anyOf``/``oneOf``/``allOf`` branch, one level deep."""
    branches = [spec]
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in spec.get(key, []) or []:
            if isinstance(sub, dict):
                branches.append(sub)
    return branches


def _types_of(spec: dict) -> set[str]:
    """Every JSON-Schema type this parameter may take, across combinator branches."""
    found: set[str] = set()
    for branch in _flatten_combinators(spec):
        t = branch.get("type")
        if isinstance(t, str):
            found.add(t)
        elif isinstance(t, list):
            found.update(x for x in t if isinstance(x, str))
    return found


def _first(spec: dict, *keys: str):
    """First non-None value for any of ``keys``, checked across combinator branches."""
    for branch in _flatten_combinators(spec):
        for key in keys:
            value = branch.get(key)
            if value is not None:
                return value
    return None


def _leaf_facts(spec: dict, inherited_description: str | None) -> dict:
    """Facts for one non-object, non-array-of-objects schema node.

    Carries the argument's own ``description`` (or, absent that, the
    nearest containing object's) alongside the structural facts, so the
    prompt can send this ledger *instead of* the raw ``input_schema`` for
    schema-heavy tools rather than both -- duplicating both was what made
    ``create-event``'s prompt+reply too large for a modest context window.
    """
    types = _types_of(spec)
    enum = _first(spec, "enum", "const")
    is_array = "array" in types
    facts: dict = {
        "type": sorted(types) or None,
        "description": _first(spec, "description") or inherited_description,
        "cardinality": "array" if is_array else "scalar",
        "domain": "closed" if (enum is not None or types == {"boolean"}) else "open",
        "format": _first(spec, "format"),
        "pattern": _first(spec, "pattern"),
        "enum": enum,
        "default": _first(spec, "default"),
    }
    if is_array:
        facts["min_items"] = _first(spec, "minItems")
        facts["max_items"] = _first(spec, "maxItems")
        facts["unique_items"] = _first(spec, "uniqueItems")
    if types & {"integer", "number"}:
        facts["minimum"] = _first(spec, "minimum", "exclusiveMinimum")
        facts["maximum"] = _first(spec, "maximum", "exclusiveMaximum")
    if "string" in types:
        facts["min_length"] = _first(spec, "minLength")
        facts["max_length"] = _first(spec, "maxLength")
    return facts


def facts_for(input_schema: dict) -> dict[str, dict]:
    """``{dotted_path: facts}`` for every argument a tool declares, nested included.

    Follows the same dotted-path / ``[]`` convention as
    ``docs/standards/input-typing.md`` (``files[].path``): an array gets one
    entry for itself (its own cardinality/bounds) and, if its items are
    structured, one entry per nested field under ``{path}[]``.
    """
    out: dict[str, dict] = {}

    def walk(spec: dict, path: str, required: bool, inherited_description: str | None) -> None:
        if not isinstance(spec, dict):
            return
        types = _types_of(spec)
        own_description = spec.get("description") or inherited_description
        if "object" in types or (not types and "properties" in spec):
            props = spec.get("properties") or {}
            req = set(spec.get("required") or [])
            for name, sub in props.items():
                child = f"{path}.{name}" if path else name
                walk(sub, child, name in req, own_description)
            return
        facts = _leaf_facts(spec, inherited_description)
        facts["required"] = required
        if path:
            out[path] = facts
        if "array" in types:
            items = spec.get("items")
            if isinstance(items, dict):
                walk(items, f"{path}[]", False, own_description)

    walk(input_schema or {}, "", False, None)
    return out
