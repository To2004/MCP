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

``breadth`` (v2, a bare 1-5 number) removed only the comparison mechanism that broke
``rank`` — not position leaking into a reply generated in one autoregressive pass over
the whole input list. Measured over the same 24 tools
(``scripts/check_breadth_stability.py``, ``reports/experiments/breadth_spec/breadth_stability.json``):
``kind`` was stable under reversal (94.7%) but ``breadth`` was not (62.5% mean, 59.8%
median, only 3/24 tools identical). Disagreement was not random across the 1-5 range —
it concentrated at the fuzzy adjacent boundaries the scale gave no bright-line test for
(3-vs-4, 1-vs-2; ``tier 5`` — a parameter that plainly names the asset — held at 88%),
and it did not track tool size (Spearman ≈ 0.06 against input count).

The fix was two things, tested separately before being combined
(``reports/experiments/dynamic_layer/v6/breadth_prompt_categories.md`` and
``v7/breadth_prompt_window.md``; full trail in ``reports/experiments/breadth_spec/``):

* the bare 1-5 number became ``resource_role``, a **named** 5-step decision procedure
  (``no_data_effect`` < ``shapes_output`` < ``sizes_amount`` < ``alters_reach`` <
  ``names_resource``) with a bright-line test at each fuzzy boundary the old scale
  lacked — a creation-call rule (nothing existing to narrow into on an ``insert``), a
  list tie-breaker (each entry another stored unit, or one field of one unit), and a
  window/range rule (a time or number window narrows, it does not alter reach). This
  alone (``check_breadth_categories_stability.py``) raised agreement to 87.6%.
* a forced yes/no version of the same five checks, with the label derived in code
  (lowest "yes" wins) rather than picked by the model, was tried and made things
  *worse* (68.9%, two tools dropped entirely) — five independently-noisy binary
  judgments instead of one categorical pick multiplied the places order could enter,
  it did not remove them. The model choosing directly from explained levels is what
  works, not a forced checklist.

Final measured result, same forward/reversed test as ``rank``'s and v2's own:
``kind`` 95.8%, ``resource_role`` **91.7% mean / 95.9% median, 12/24 tools identical**
(``check_breadth_v7_stability.py window``,
``reports/experiments/breadth_spec/breadth_v7_window_stability.json`` —
re-run once with byte-identical output to confirm this is order-sensitivity, not
sampling noise; every call here is greedy, seed 0). A companion experiment that split
``kind`` and ``resource_role`` into two separate model calls, on the theory that fewer
questions per call would reduce cross-talk, instead scored *worse* (85.8%,
``breadth_split_stability.json``) — the two questions asked together, in one reply with
one shared chain of reasoning, is the better design, not the split.

``external_effect`` is new alongside ``resource_role``: a yes/no for whether a value
sends data outward (an email, a webhook, a notification) — independent of
``resource_role``, since a notification flag changes nothing stored (``no_data_effect``)
but still matters for risk. Folding it into ``resource_role`` was what made v3's
notification-adjacent flags (``sendUpdates``, ``guestsCanInviteOthers``) some of its
least stable inputs; a separate field keeps ``resource_role`` about stored data only.

An input nobody could classify is recorded as ``kind: "none"`` — not a quantity — since
that is what the runtime must do with it regardless, and most inputs genuinely are not
quantities. The gap is not hidden: ``source`` is ``unclassified`` rather than ``schema``
or ``llm``, so counting those tells you whether the scan needs re-running.

``breadth`` (the 1-5 int the runtime's ``BREADTH_WEIGHT``/``_relative_weight`` still
consume) is now DERIVED from ``resource_role`` (``ROLE_TO_BREADTH``), not asked for
directly — the model has never been asked for a bare number since v2. ``resource_role``
and ``external_effect`` are also kept on the entry verbatim, so a consumer that wants the
named level or the outward-effect signal directly does not have to reverse the mapping.
"""

from __future__ import annotations

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import ToolSpec

#: How a larger value is expressed, if it can be read as a quantity at all. There is no
#: "unresolved" kind: an input nobody could classify reads ``none``, because that is what
#: the runtime must do with it anyway. The gap moves to ``source``, where ``unclassified``
#: means nothing answered. Wire/storage vocabulary — unchanged since v2, so every
#: consumer (``dynamic_v2.py``'s ``MEASURABLE``/``parse_quantity`` included) keeps
#: working. The prompt asks the model for ``not_size`` instead of ``none`` (clearer next
#: to ``no_data_effect``); ``_resolve_with_model`` translates it back before storing.
KINDS = ("none", "count", "magnitude", "range")
_MODEL_KINDS = set(KINDS)
#: What the model is actually asked for; translated to ``KINDS`` on the way in.
_PROMPT_KIND_VALUES = {"count", "magnitude", "range", "not_size"}
_PROMPT_KIND_TO_STORED = {"not_size": "none"}
#: The five named steps ``resource_role`` walks, in order from least to most central to
#: the asset the call acts on. Replaces v2's bare 1-5 ``breadth`` number — see the module
#: docstring for why (each step has a bright-line test a number alone did not).
RESOURCE_ROLES = ("no_data_effect", "shapes_output", "sizes_amount", "alters_reach",
                  "names_resource")
#: ``resource_role`` -> the 1-5 int the runtime (``BREADTH_WEIGHT`` / ``_relative_weight``
#: in ``dynamic_v2.py``) still consumes. The model is never asked for this number
#: directly; it is derived from the name it picked.
ROLE_TO_BREADTH = {name: level for level, name in enumerate(RESOURCE_ROLES, start=1)}
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

# No REAL parameter name appears in this prompt, by design: concrete examples are the
# main channel through which a prompt memorises the set it is measured on. The four
# worked-example tools (query_records, create_ticket, list_containers, save_items) are
# synthetic and do not match any scanned catalog.
#
# Filled with .replace(), not .format() -- the examples and reply schema below use
# single, unescaped braces, which .format() cannot pass through.
_BREADTH_PROMPT = """You label the input parameters of one MCP tool.

Judge what the value MEANS in a real call. The declared type is a hint only. It is
often wider or narrower than the value it actually carries.

<label name="kind">
If a caller passed a BIGGER value here, what makes it bigger?

count      The value holds several things and what matters is how many.
           This includes several things packed into one string with a separator.
           e.g. ["a.txt","b.txt"] ; "id1,id2,id3"

magnitude  The value is one number, and a bigger number means more work done or more
           data returned. This includes a number written as text, with or without a
           unit suffix.
           e.g. limit=500 ; page_size ; "30d" meaning thirty days

range      The value is one end of an interval, and what matters is how wide the
           interval is between it and its partner parameter.
           e.g. start_date, whose partner is end_date ; from_line, whose partner is to_line

not_size   None of the above. The value picks one particular thing, switches a mode on
           or off, or is free text being written.
           e.g. file_id ; sort="asc" ; the body of a message

Rule: a value that identifies something is not_size even when it is a number.
One id is not bigger than another id.
</label>

<label name="resource_role">
How much does this parameter decide WHICH STORED DATA the call touches?

First work out which parameter of this tool NAMES the stored unit the call acts on —
the record, file, table, folder, mailbox, channel, calendar, repository the call is
about. Call that the naming parameter. Some tools have one; some have none.

If the call CREATES a new stored unit rather than acting on an existing one, the naming
parameter is the one saying WHERE the new unit lands (which folder, which workspace,
which project) — not the fields filling in the new unit's own contents. Those content
fields are level 4 below, even on a creation call, because nothing existing is there yet
for them to narrow.

Read all five levels before you answer, then pick the ONE that fits best.

5  names_resource
   This value itself names or matches the stored unit the call acts on, or several such
   units at once. Change it and the call points somewhere else entirely.

4  alters_reach
   The value stays inside the unit the naming parameter chose (or, on a creation call,
   inside the new unit being created), but changes WHAT content is read or written
   there.

3  sizes_amount
   A naming parameter exists, and this value only caps, bounds, or narrows what comes
   out of the unit it named. Delete this parameter and the call still does basically the
   same thing to basically the same data.

2  shapes_output
   The same information arrives either way — this value only changes its order, format,
   or which instalment of it arrives.

1  no_data_effect
   The stored data is identical whatever this value is. It concerns running the call,
   logging it, timing it, or sending a notification to someone — nothing stored changes.

Tie-breakers. These beat any feeling you get from the parameter's name.

- A list is level 5 only when EACH ENTRY is another stored unit the call reads or writes
  on its own. A list whose entries only fill one field inside a SINGLE unit is level 4,
  not 5.
  Level 5 example: a parameter listing several item ids, each one written or read
  separately.
  Level 4 example: a parameter listing several names into ONE field of a single record
  (e.g. who should be told about it) — one record, one field, however many names.

- A parameter offering a fixed menu of categories that narrows a listing is level 3 even
  when it accepts several values at once. It selects nothing new; it filters.

- Free text written into a place another parameter already chose is level 4, however
  confidential that text is.

- A flag deciding whether the write really lands, or how much of it lands, is level 4.
  A flag changing only speed, logging, retries, or notifications is level 1.

- If a tool has no naming parameter at all and one value alone decides which stored
  things come back, that value is level 5, not level 3.

- If two levels seem to fit, re-read the naming-parameter test above before choosing —
  do not drop to the lower level without checking it against the test.
- A parameter that is one end of a time or numeric WINDOW (kind: range) bounding
  which records fall inside an already-chosen container is level 3, not level 4 —
  it narrows which of the container's contents are returned, the same as a limit
  or a filter. This holds whether the window is on a listing call or bounds one
  field inside a single record: the test is still whether it narrows an existing
  selection (level 3) or changes WHAT is read or written there (level 4), and a
  date or number range being the shape of the value does not by itself move it.
</label>

<label name="external_effect">
Does this value cause data to leave the system or reach a third party — an email, an
invite, a notification, a webhook, a share link, an outbound request?
Answer yes or no. This is independent of resource_role. A value can be level 1 and
still be yes.
</label>

<examples>
Tool: query_records
Parameters: dataset_id, filter_text, limit, sort_by, trace_id
{"inputs":[
{"name":"dataset_id","effect":"a different dataset is read","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"filter_text","effect":"same dataset, narrows which rows come back","kind":"not_size","resource_role":"sizes_amount","external_effect":"no"},
{"name":"limit","effect":"same rows, fewer or more of them","kind":"magnitude","resource_role":"sizes_amount","external_effect":"no"},
{"name":"sort_by","effect":"same rows, different order","kind":"not_size","resource_role":"shapes_output","external_effect":"no"},
{"name":"trace_id","effect":"stored data untouched","kind":"not_size","resource_role":"no_data_effect","external_effect":"no"}]}

Tool: create_ticket
Parameters: project_id, title, watchers, window_start, window_end, notify_watchers, layout_version
Naming parameter: project_id — it says where the new ticket lands.
{"inputs":[
{"name":"project_id","effect":"the ticket is created in a different project","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"title","effect":"same project, different content in the new ticket","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"watchers","effect":"one ticket, more names in one field of it","kind":"count","resource_role":"alters_reach","external_effect":"yes"},
{"name":"window_start","effect":"one ticket, widens or narrows its window with window_end","kind":"range","resource_role":"alters_reach","external_effect":"no"},
{"name":"window_end","effect":"one ticket, widens or narrows its window with window_start","kind":"range","resource_role":"alters_reach","external_effect":"no"},
{"name":"notify_watchers","effect":"ticket stored identically, decides who gets emailed about it","kind":"not_size","resource_role":"no_data_effect","external_effect":"yes"},
{"name":"layout_version","effect":"decides which display template is attached to the new ticket","kind":"not_size","resource_role":"alters_reach","external_effect":"no"}]}

Tool: list_containers
Parameters: space_id, kinds, exclude_hidden, page_size, cursor
{"inputs":[
{"name":"space_id","effect":"a different workspace is listed","kind":"not_size","resource_role":"names_resource","external_effect":"no"},
{"name":"kinds","effect":"same workspace, narrows which container kinds are listed","kind":"count","resource_role":"sizes_amount","external_effect":"no"},
{"name":"exclude_hidden","effect":"same workspace, narrows the listing","kind":"not_size","resource_role":"sizes_amount","external_effect":"no"},
{"name":"page_size","effect":"same containers, fewer or more of them","kind":"magnitude","resource_role":"sizes_amount","external_effect":"no"},
{"name":"cursor","effect":"same containers, a later instalment","kind":"not_size","resource_role":"shapes_output","external_effect":"no"}]}

Tool: save_items
Parameters: keys, content, overwrite, dry_run
{"inputs":[
{"name":"keys","effect":"each entry is another item written","kind":"count","resource_role":"names_resource","external_effect":"no"},
{"name":"content","effect":"same items, different bytes written into them","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"overwrite","effect":"same items, decides whether existing bytes are destroyed","kind":"not_size","resource_role":"alters_reach","external_effect":"no"},
{"name":"dry_run","effect":"same items, decides whether the write lands at all","kind":"not_size","resource_role":"alters_reach","external_effect":"no"}]}
</examples>

<tool>
Name: {tool}
Description: {desc}
Parameters:
{params}
</tool>

For each parameter, first state in one short clause what changes about the stored data
when only that value changes, then give kind, then resource_role, then external_effect.

Reply with ONLY this JSON. Every parameter exactly once, names copied exactly as
written, in the order given.

{"inputs":[{"name":"<name>","effect":"<one short clause>","kind":"count|magnitude|range|not_size","resource_role":"no_data_effect|shapes_output|sizes_amount|alters_reach|names_resource","external_effect":"yes|no"}]}"""


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
    """Ask the local model for the kind and resource role of each unresolved parameter.

    Returns ``{}`` unless the reply classifies exactly the parameters it was given: a
    partial answer is never merged, because it would silently mix model output with the
    structural default and make the provenance of a classification unreadable.

    Translates the prompt's own vocabulary back to the stored one: ``not_size`` ->
    ``none`` (``KINDS``), and ``resource_role`` -> the 1-5 ``breadth`` int
    (``ROLE_TO_BREADTH``) the runtime still consumes, alongside ``resource_role`` and
    ``external_effect`` kept verbatim.
    """
    props = _properties(tool)
    lines = "\n".join(
        f"- {name} (declared type: {props[name].get('type') or 'unspecified'}): "
        f"{str(props[name].get('description') or '')[:200]}"
        for name in unresolved
    )
    # .replace(), not .format() -- the prompt's own JSON examples and reply schema use
    # single, unescaped braces.
    prompt = (_BREADTH_PROMPT.replace("{tool}", tool.name)
                              .replace("{desc}", (tool.description or "")[:300])
                              .replace("{params}", lines))
    reply = query_ollama(prompt, model=model) if model else query_ollama(prompt)
    if not isinstance(reply, dict) or not isinstance(reply.get("inputs"), list):
        return {}
    out: dict[str, dict] = {}
    for item in reply["inputs"]:
        if not isinstance(item, dict):
            return {}
        name = item.get("name")
        kind = item.get("kind")
        role = item.get("resource_role")
        external_effect = item.get("external_effect")
        if (name not in unresolved or name in out or kind not in _PROMPT_KIND_VALUES
                or role not in ROLE_TO_BREADTH or external_effect not in ("yes", "no")):
            return {}
        out[name] = {
            "kind": _PROMPT_KIND_TO_STORED.get(kind, kind),
            "breadth": ROLE_TO_BREADTH[role],
            "resource_role": role,
            "external_effect": external_effect == "yes",
            "why": str(item.get("effect", ""))[:140],
        }
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
                    # No structural equivalent for either -- always the model's answer,
                    # settled_by_schema or not.
                    resource_role=answer["resource_role"],
                    external_effect=answer["external_effect"],
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
