"""Classify each tool input by BREADTH: does its value decide how *much* the call covers?

The runtime layer scores a call by how broad it is for this deployment. To do that it
must first know which arguments carry breadth at all — an array whose length is a
fan-out, a number that bounds a page, a pair of endpoints whose span is a window. That
question is answered once, at scan time, and shipped in the scan artifact as
``tool_breadth``.

**What this module deliberately does not do is pick a threshold.** "How big is too big"
is a property of the organization — twenty attendees is everyone at a ten-person company
and a small meeting at a large one — so the cut-points are built at runtime from the
values a deployment actually passes. Asked for a threshold, a model correctly declines:
the scan's older ``critical_trigger`` field is populated on only 10-14% of inputs.

Two passes, asked different questions:

* **structure** — what the JSON Schema states outright. An ``enum`` is a fixed choice, an
  ``array``'s length is its breadth, ``maxItems``/``maximum`` are declared ceilings, and
  ``default`` is the value that applies when the caller omits the argument. No parameter
  *name* is ever read here. Reading names is guessing at semantics, and guessing drifts
  into fitting: substring rules had already made ``timeMax`` a magnitude (it contains
  "max"), ``calendarId`` a range ("calendar" contains "end") and ``account`` a count.
* **semantics** — everything structure leaves ``unresolved``, handed to the local model.
  Whether a string is a date endpoint or an identifier, and whether a number counts rows
  or names a pull request, is meaning rather than structure.

v1 of this prompt also asked for two things the older ``tool_input_ranking`` was reaching
for. Neither survived, and this module emits neither field now
(``tests/scanner/test_breadth.py::test_no_ordering_and_no_pointwise_risk_score_are_emitted``
asserts ``"rank" not in entry`` and ``"targets" not in entry`` for every input):

* ``rank`` — a listwise ordering of a tool's inputs by how much of the system the call can
  be made to touch, most first. It failed its own stability test: reversing the order
  inputs are presented in and asking again should not change an answer that is about the
  inputs and not about the prompt, but measured over 24 tools it agreed with itself at
  Kendall's tau **0.538 mean**, and went **negative** on the two largest tools —
  `create-event` (23 inputs, τ = −0.37) and `update-event` (20 inputs, τ = −0.47), worse
  than a coin flip on exactly the tools where getting the order right matters most
  (``reports/experiments/breadth_spec/rank_stability.json``). Positional bias in listwise
  LLM ranking is architectural — causal attention couples a candidate's score to where it
  sat in the prompt — so this is not a prompt-wording problem.
* ``targets`` — whether a value decides *which* stored thing the call acts on. Not
  unstable, but redundant with a job this module already isn't responsible for: which
  asset a call can reach is priced into the static cell, and folding it into a runtime
  volume factor would double-count it there.

``breadth`` replaced ``rank``: each input is scored **independently against the fixed 1-5
rubric below**, so nothing about grading one input depends on where another one sat in the
prompt. That is what actually fixed the instability, not a smaller prompt or a stricter
retry.

An input nobody could classify is recorded as ``kind: "none"`` — not a quantity — since
that is what the runtime must do with it regardless, and most inputs genuinely are not
quantities. The gap is not hidden: ``source`` is ``unclassified`` rather than ``schema``
or ``llm``, so counting those tells you whether the scan needs re-running.
"""

from __future__ import annotations

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import ToolSpec

#: How a larger value is expressed, if it can be read as a quantity at all. There is no
#: "unresolved" kind: an input nobody could classify reads ``none``, because that is what
#: the runtime must do with it anyway. The gap moves to ``source``, where ``unclassified``
#: means nothing answered.
KINDS = ("none", "count", "magnitude", "range")
_MODEL_KINDS = set(KINDS)
#: How central a parameter is to the asset the call acts on: 5 it names the asset (or
#: several), 4 an important part of it, 3 an unimportant part, 2 indirect, 1 not at all.
#: Judged independently of ``kind`` — an identifier has no size but may be the very thing
#: that names the asset.
BREADTH_LEVELS = (1, 2, 3, 4, 5)
#: What an unclassified parameter gets: the middle of the scale, so a gap in the scan
#: neither silences an argument nor treats it as the most central thing on its tool.
DEFAULT_BREADTH = 3
#: One retry when a reply is rejected. Measured over 270 tools, 38 replies were rejected
#: whole and every unresolved input traced to one of them — none to a model that had
#: looked and hesitated. Rejection is a formatting failure, and formatting failures retry
#: well; a hallucinated threshold would not, which is why only shape is retried here.
_RETRIES = 1

# No parameter name from any scanned server appears in this prompt, by design: concrete
# examples are the main channel through which a prompt memorises the set it is measured on.
_BREADTH_PROMPT = """You are analysing the input parameters of one API tool.

Answer two questions about each parameter. Judge what the parameter MEANS, not how it is
declared — a declared type is often wider or narrower than what the value carries.


(1) "kind" — if a caller supplied a LARGER value, how is "larger" expressed?

    count      the value is a collection, and what matters is how many items it holds
               (including a collection encoded inside one string with a separator)
               e.g. a list of file paths; "a,b,c" where the commas separate targets

    magnitude  the value is a single number, and a bigger number means more work done or
               more data returned (including a number written as text, with or without a
               unit suffix)
               e.g. a page size; a row limit; "30d" meaning thirty days

    range      the value is one endpoint of an interval, and the SIZE of the interval
               between it and its partner parameter is what matters
               e.g. a window start, whose partner is the window end

    none       the value names or selects one particular thing, switches a mode on or
               off, or is free-form content being written
               e.g. a record id; a sort order; the body of a message

    A value that identifies something is "none" even when it is numeric: one identifier
    is not larger than another.


(2) "breadth" — 1 to 5. HOW CENTRAL IS THIS PARAMETER TO THE ASSET the call acts on?

    Answer this INDEPENDENTLY of question (1). An identifier has no larger or smaller
    value, so its "kind" is none — but it may be the very thing that names the asset, and
    that is what this question is about. Judge what the parameter decides, not whether a
    number can be read from it.

    Do not reason from the wording of this tool's domain. Apply one test to every
    parameter: hold every other parameter fixed, change only this value, and ask what
    changes about the STORED DATA the call acts on.

    5  a different stored thing is acted on
       The value selects, names or matches the unit of stored data itself. Changing it
       points the call somewhere else entirely. This includes any value that selects
       SEVERAL such units at once — a list, or a pattern that matches an open-ended set.

    4  the same stored thing, but materially different contents are read or written
       The value decides which parts of that unit are affected, or turns the operation
       from a limited one into a far-reaching one within it.

    3  the same contents, in a different amount or slice
       The value only sizes or bounds what is already selected. Removing it leaves a
       call that does essentially the same thing to essentially the same data.

    2  the same data, presented differently
       The value shapes the request or the reply rather than what is reached — the same
       information arrives in another order, form, or instalment.

    1  nothing about the stored data changes
       The value concerns execution, bookkeeping or presentation only.

    Four rules override any intuition from the parameter's name:
      - a list, array or pattern that selects stored things is 5, however few entries it
        happens to carry: what matters is that each entry is another one
      - a value that narrows or filters within something already selected is 3, however
        powerful the filter
      - centrality is not sensitivity. A parameter naming a mundane unit of stored data
        is still 5; a parameter carrying highly confidential content that is merely
        written into an already-chosen destination is not raised for it
      - if two levels seem to fit, choose the lower one


Tool: {tool}
Description: {desc}

Parameters:
{params}

Reply with ONLY a JSON object. Include every parameter exactly once, using its name
exactly as written, in the order given:
{{"inputs": [{{"name": <parameter name>, "kind": "none|count|magnitude|range",
"breadth": 1, "why": "<one short clause>"}}]}}"""


def _types_of(schema: dict) -> set[str]:
    """Every JSON-Schema type a parameter may take, flattening ``anyOf``/``oneOf``/``allOf``."""
    found: set[str] = set()
    declared = schema.get("type")
    if isinstance(declared, str):
        found.add(declared)
    elif isinstance(declared, list):
        found.update(x for x in declared if isinstance(x, str))
    for key in ("anyOf", "oneOf", "allOf"):
        for branch in schema.get(key, []) or []:
            if isinstance(branch, dict):
                found |= _types_of(branch)
    return found


def _bound_of(schema: dict, keys: tuple[str, ...]) -> int | float | None:
    """The loosest declared bound under ``keys``, searching ``anyOf``/``oneOf`` branches too."""
    found: list[int | float] = []
    for key in keys:
        value = schema.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            found.append(value)
    for key in ("anyOf", "oneOf", "allOf"):
        for branch in schema.get(key, []) or []:
            if isinstance(branch, dict):
                nested = _bound_of(branch, keys)
                if nested is not None:
                    found.append(nested)
    return max(found) if found else None


def classify_structural(name: str, schema: dict) -> dict:
    """What the JSON Schema alone settles about one parameter. Reads no parameter name."""
    types = _types_of(schema)
    enum = schema.get("enum") or any(
        isinstance(branch, dict) and branch.get("enum")
        for branch in schema.get("anyOf", []) or []
    )
    entry = {
        "name": name,
        "kind": "none",
        # How much stored data this parameter can reach, 1 (widest) to 5 (nothing). Only
        # meaning can answer that, so structure leaves it unset.
        "breadth": None,
        "ceiling": None,
        "default": schema.get("default"),
        "source": "schema",
        "why": "the schema states no structure the runtime can use",
    }
    # Nothing has classified this yet; `none` is the safe reading, `source` records that
    # it was defaulted rather than decided.
    entry["source"] = "unclassified"
    if enum:
        entry.update(kind="none", source="schema", why="enum: a fixed choice, not a quantity")
        return entry
    if "array" in types:
        entry.update(kind="count", source="schema", ceiling=_bound_of(schema, ("maxItems",)),
                     why="array: its length is the breadth of the call")
        return entry
    if types & {"integer", "number"}:
        entry.update(ceiling=_bound_of(schema, ("maximum", "exclusiveMaximum")),
                     why="numeric, but only meaning says whether it counts or names")
    return entry


def _properties(tool: ToolSpec) -> dict[str, dict]:
    """``{name: subschema}`` for one tool's declared inputs."""
    props = (tool.input_schema or {}).get("properties")
    return props if isinstance(props, dict) else {}


def _resolve_with_model(tool: ToolSpec, unresolved: list[str], model: str | None) -> dict[str, dict]:
    """Ask the local model for the kind of each unresolved parameter.

    Returns ``{}`` unless the reply classifies exactly the parameters it was given: a
    partial answer is never merged, because it would silently mix model output with the
    structural default and make the provenance of a classification unreadable.
    """
    props = _properties(tool)
    lines = "\n".join(
        f"- {name} (declared type: {props[name].get('type') or 'unspecified'}): "
        f"{str(props[name].get('description') or '')[:200]}"
        for name in unresolved
    )
    prompt = _BREADTH_PROMPT.format(
        tool=tool.name, desc=(tool.description or "")[:300], params=lines
    )
    reply = query_ollama(prompt, model=model) if model else query_ollama(prompt)
    if not isinstance(reply, dict) or not isinstance(reply.get("inputs"), list):
        return {}
    out: dict[str, dict] = {}
    for item in reply["inputs"]:
        if not isinstance(item, dict):
            return {}
        name, kind = item.get("name"), item.get("kind")
        if name not in unresolved or name in out or kind not in _MODEL_KINDS:
            return {}
        breadth = item.get("breadth")
        if breadth not in BREADTH_LEVELS:
            return {}
        out[name] = {"kind": kind, "breadth": breadth,
                     "why": str(item.get("why", ""))[:140]}
    return out if set(out) == set(unresolved) else {}


def classify_tool_breadth(tool: ToolSpec, *, use_llm: bool = False,
                          model: str | None = None) -> dict:
    """Breadth entries for one tool's inputs, from both passes.

    **Every** parameter goes to the model, including ones whose ``kind`` the schema
    already settled. The two passes answer different questions: the schema knows an array
    is an array, but only meaning knows whether its items are containers, records or
    formatting flags — and that is what ``breadth`` grades. Asking only about the
    schema-ambiguous ones left arrays, the inputs whose length *is* the fan-out, with no
    reach grade at all.

    Where they overlap, structure wins on ``kind``: an array's length is a count whatever
    the model calls it.
    """
    entries = {name: classify_structural(name, schema)
               for name, schema in _properties(tool).items()}
    if use_llm and entries:
        for _ in range(1 + _RETRIES):
            answers = _resolve_with_model(tool, list(entries), model)
            if not answers:
                continue
            for name, answer in answers.items():
                entry = entries[name]
                settled_by_schema = entry["source"] == "schema"
                entry.update(
                    kind=entry["kind"] if settled_by_schema else answer["kind"],
                    breadth=answer["breadth"],
                    source="schema+llm" if settled_by_schema else "llm",
                    why=entry["why"] if settled_by_schema else answer["why"],
                )
            break
    return {"inputs": list(entries.values())}


def classify_breadth(tools: list[ToolSpec], *, use_llm: bool = False,
                     model: str | None = None) -> dict[str, dict]:
    """``{tool: {"inputs": [...]}}`` for every tool, for the scan artifact."""
    return {tool.name: classify_tool_breadth(tool, use_llm=use_llm, model=model)
            for tool in tools}
