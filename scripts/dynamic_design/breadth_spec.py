"""Classify every tool input by BREADTH TYPE, not by a guessed critical threshold.

The scan's existing ``critical_trigger`` asks the model one hard question: "at what
value does this argument become critical?" That answer depends on the organization —
20 attendees is everyone at a ten-person company and a small meeting at a large one —
so the model correctly declines most of the time and only 10-14% of inputs carry a
threshold. Everything without one is invisible to the runtime layer.

This module asks the easy question instead: **is this argument a quantity that makes
the call broader, and in what unit?** That is a property of the schema, identical at
every organization, and mostly answerable with no model at all:

    none       identifier, flag, enum, free text  -> the runtime ignores it
    count      an array; its LENGTH is the quantity
    magnitude  a number whose VALUE is the quantity (limit, perPage, depth)
    range      one end of a span; the SPAN is the quantity (timeMin/timeMax)

Where the JSON Schema states its own bounds (``maxItems``, ``maximum``) those are
recorded as a design-time ceiling — a free, exact cold-start threshold that needs
neither a model nor traffic. Where it states none, ``bounded`` is False, which is the
honest form of the scan's ``"unbounded (no LIMIT)"`` string.

Deterministic, no network, no LLM. Run::

    python3 scripts/dynamic_design/breadth_spec.py
"""

from __future__ import annotations

import json
from pathlib import Path

TOOL_LISTS = Path("reports/tool_lists")
EXPORTS = Path("reports/exports")
OUT = Path("reports/experiments/breadth_spec")
SERVERS = {"github": "github_real", "slack": "slack_real", "calendar": "calendar_real"}

def _types_of(spec: dict) -> set[str]:
    """Every JSON-Schema type this parameter may take, flattening anyOf/oneOf/allOf."""
    found: set[str] = set()
    t = spec.get("type")
    if isinstance(t, str):
        found.add(t)
    elif isinstance(t, list):
        found.update(x for x in t if isinstance(x, str))
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in spec.get(key, []) or []:
            if isinstance(sub, dict):
                found |= _types_of(sub)
    return found


def _bound_of(spec: dict, keys: tuple[str, ...]) -> int | float | None:
    """The tightest declared bound under ``keys``, searching anyOf/oneOf branches too."""
    found: list[int | float] = []
    for key in keys:
        value = spec.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            found.append(value)
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in spec.get(key, []) or []:
            if isinstance(sub, dict):
                nested = _bound_of(sub, keys)
                if nested is not None:
                    found.append(nested)
    return max(found) if found else None


def classify(name: str, spec: dict) -> dict:
    """What the JSON Schema alone can settle about one parameter. **No name heuristics.**

    Reading parameter names is guessing at semantics, and guessing drifts into fitting:
    every misclassification tempts one more token into a list, tuned on whatever servers
    happen to be under the microscope. Substring rules had already made `timeMax` a
    magnitude (it contains "max"), `calendarId` a range ("calendar" contains "end") and
    `account` a count ("account" contains "count").

    So this pass claims only what the schema states as structure:

    * an ``enum`` is a fixed choice, never a quantity;
    * an ``array``'s length is its breadth;
    * ``maxItems``/``maximum`` are declared ceilings, ``default`` the value applied when
      the caller omits the argument.

    Everything else is left ``unresolved`` for the model pass, which is asked exactly one
    question it can answer without knowing the organization: is this a quantity, and in
    what unit. What neither settles is imputed at Q3 at runtime rather than fixed here
    with another rule.
    """
    types = _types_of(spec)
    enum = spec.get("enum") or any(
        isinstance(s, dict) and s.get("enum") for s in spec.get("anyOf", []) or []
    )
    out = {"name": name, "types": sorted(types), "kind": "unresolved", "ceiling": None,
           "bounded": False, "parse": None, "why": "",
           # The value the server applies when the caller omits the argument. Declared
           # by the server, so it is fact rather than inference.
           "default": spec.get("default")}

    if enum:
        out.update(kind="none", why="enum: a fixed choice, not a quantity")
        return out

    if "array" in types:
        ceiling = _bound_of(spec, ("maxItems",))
        out.update(kind="count", ceiling=ceiling, bounded=ceiling is not None,
                   why="array: its length is the breadth of the call")
        return out

    if types & {"integer", "number"}:
        out["ceiling"] = _bound_of(spec, ("maximum", "exclusiveMaximum"))
        out["bounded"] = out["ceiling"] is not None
        out["why"] = "numeric, but only the model can say whether it counts or names"
        return out

    out["why"] = "the schema states no structure the runtime can use"
    return out


def parameters(tool: dict) -> dict[str, dict]:
    """``{name: subschema}`` for one tool's declared inputs."""
    schema = tool.get("input_schema") or tool.get("inputSchema") or {}
    props = schema.get("properties")
    return props if isinstance(props, dict) else {}


def spec_for(kind: str) -> dict:
    """Breadth spec for one server, plus the coverage comparison against the scan."""
    tools = json.loads((TOOL_LISTS / f"{SERVERS[kind]}.json").read_text())
    tools = tools["tools"] if isinstance(tools, dict) else tools
    old = json.loads((EXPORTS / f"{SERVERS[kind]}.json").read_text())["tool_input_ranking"]

    per_tool: dict[str, list[dict]] = {}
    for tool in tools:
        per_tool[tool["name"]] = [classify(n, s) for n, s in parameters(tool).items()]

    old_names, old_trig = set(), set()
    for tool_name, block in old.items():
        for entry in block.get("inputs", []):
            old_names.add((tool_name, entry["name"]))
            if entry.get("critical_trigger"):
                old_trig.add((tool_name, entry["name"]))
    new_names = {(t, e["name"]) for t, es in per_tool.items() for e in es}

    return {
        "server": kind,
        "tools": per_tool,
        "coverage": {
            "n_tools": len(per_tool),
            "n_inputs_schema": len(new_names),
            "n_inputs_scan": len(old_names),
            "scan_only": sorted(f"{t}.{n}" for t, n in old_names - new_names),
            "schema_only": sorted(f"{t}.{n}" for t, n in new_names - old_names),
            "old_with_trigger": len(old_trig),
            "new_with_kind": sum(1 for es in per_tool.values() for e in es if e["kind"] not in ("none", "unresolved")),
            "new_with_ceiling": sum(1 for es in per_tool.values() for e in es if e["ceiling"] is not None),
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{'server':<10}{'tools':>6}{'inputs':>8}{'old trigger':>13}{'new kind':>10}"
          f"{'schema ceiling':>16}{'name mismatch':>15}")
    for kind in SERVERS:
        spec = spec_for(kind)
        c = spec["coverage"]
        mismatch = len(c["scan_only"]) + len(c["schema_only"])
        print(f"{kind:<10}{c['n_tools']:>6}{c['n_inputs_schema']:>8}"
              f"{c['old_with_trigger']:>13}{c['new_with_kind']:>10}"
              f"{c['new_with_ceiling']:>16}{mismatch:>15}")
        (OUT / f"{kind}.json").write_text(json.dumps(spec, indent=1))
    print(f"\nwritten to {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
