# Parameter Breadth Classifier — v2 (proposed)

Two labels per parameter, judged independently. The model does not order anything and does
no arithmetic.

Changes from v1:

- **`breadth` measures reach, not quantity type.** It asks how much stored data a
  parameter can open, judged independently of whether a number can be read from it — so
  an identifier or a glob is scored on what it reaches, not dismissed for having no size.
- **`targets` is gone**, subsumed by that scale.
- **Ordering is gone.** The model scores each parameter against fixed anchors rather than
  against its neighbours, which removes the presentation-order sensitivity that made v1's
  ordering unusable (Kendall τ 0.538 forward vs reversed, negative on the largest tools).

---

## The prompt

```text
You are analysing the input parameters of one API tool.

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


(2) "breadth" — 1 to 5. HOW MUCH OF THE STORED DATA can this one parameter reach?

    Answer this INDEPENDENTLY of question (1). An identifier has no larger or smaller
    value, so its "kind" is none — but it still decides which stored thing is opened, and
    that is what this question is about. Judge the reach, not whether a number can be read
    from it.

    Assume every other parameter is at its narrowest legal value, and ask what the widest
    legal value of THIS one would open up.

    1  an unknown or unbounded set of stored things
       The reachable set cannot be listed in advance.
       e.g. a path or query accepting a wildcard; a scope switch set to "all"; a value
       whose empty form means "match everything"

    2  many separate containers
       Each step up pulls in another whole store of things.
       e.g. a list of calendar ids; a page size on a tool that LISTS calendars, channels,
       repositories or tables, since a bigger page returns more of them

    3  one whole container, and everything inside it
       e.g. the name or id of a table, folder, repository, channel or calendar

    4  part of one container — more records, or more detail about records
       e.g. a page size on a tool listing the messages in ONE channel; a time window
       inside one calendar; a field list; a maximum response size

    5  nothing about which data is reached, or how much of it comes back
       e.g. a sort order; a response format; a cursor; a dry-run flag; content being
       written

    Three rules override the examples:
      - a wider UNIT beats a bigger number. A limit of 1000 records inside one container
        is 4; a limit of 5 containers is 2
      - a parameter that narrows or filters an already-chosen set is 5, however powerful
        the filter
      - importance is not breadth. A parameter naming the single most sensitive record in
        the system is still 4, because it opens one record


Tool: {tool}
Description: {desc}

Parameters:
{params}

Reply with ONLY a JSON object. Include every parameter exactly once, using its name
exactly as written, in the order given:
{"inputs": [{"name": <parameter name>, "kind": "none|count|magnitude|range",
"breadth": 1, "why": "<one short clause>"}]}
```

## The two questions are orthogonal, and that is the point

`kind` and `breadth` ask different things, and an earlier draft quietly tied them
together — treating "no number can be read from this" as "this does not touch the data".

| | asks | used for |
|---|---|---|
| `kind` | can a quantity be **read** from this value, and in what unit? | extraction — turning an argument into a number the runtime can compare against history |
| `breadth` | how much stored data can this parameter **reach**? | risk — how much a deviation on this parameter should count |

A record id is `kind: none` because one identifier is not larger than another, and
`breadth: 4` because it opens a record. A glob path is `kind: none` and `breadth: 1`,
because it can match anything. Neither fact tells you the other.

Getting this wrong shaped the previous scale badly. Measured over the three servers,
**200 of 303 inputs (66%) are `kind: none`** — and the old scale reserved its bottom two
levels for exactly those, so two thirds of the parameters were pushed into the bucket
that weighs nothing. Under the scale above, an identifier or a path is judged on what it
opens, so a `none` input can sit at level 1.

**Bounded-versus-unbounded is not asked.** It splits 91 to 12 among the quantities, and
the schema states it outright: `maximum`, `maxItems` and small `enum`s are already
extracted at scan time. Code applies that, not the model.

## Why 1–5 rather than an ordering

v1 asked the model to order a tool's inputs. Measured over 24 tools, asking twice with the
inputs presented in opposite order gave **Kendall τ 0.538**, only 3 of 24 identical, and
**negative τ on the two largest tools** — the signature of the model echoing the order it
was given.

A fixed scale removes that: each parameter is judged against written anchors, not against
whichever parameters happen to sit near it in the prompt. The cost is that a 1–5 score is
*pointwise*, which the LLM-ranking literature calls the least reliable form. What makes it
defensible here is that the levels are **anchored with definitions and examples** rather
than left as bare numbers, and that the score is used as a weight, not as a threshold.

**This needs its own stability measurement before adoption** — the τ 0.538 figure describes
v1's listwise ordering and says nothing about a rubric score. The equivalent check is the
label flip rate over repeated runs at temperature 0.

## Why `targets` is gone

It asked whether a parameter decides *which* stored thing is touched — a boolean over the
same axis `breadth` now measures with five levels. `targets: true` is `breadth ≤ 4`, and
`targets: false` is `breadth 5`, so the boolean carried strictly less and could contradict
the scale it duplicated.

## Why omission is not asked

The scanner sees a schema, not traffic. Whether omitting a parameter widens a call is a
runtime question and the runtime already answers it from things it actually knows:

- the schema declares a `default` → that value applied, so substitute it;
- no default, and this deployment's traffic shows the argument in use → impute Q3;
- no default, and nobody ever passes it → ignore it.

Asking the model to predict the same thing would be inference layered on top of fact.

---

## How `breadth` enters the score

`breadth` weights the ramp — but a ramp only exists where `kind` gave the runtime a number
to compare. So the two labels do different work here too: `kind` decides *whether* an
argument is measurable, `breadth` decides *how much its deviation counts*.

```python
WEIGHT  = {1: 1.00, 2: 0.85, 3: 0.60, 4: 0.40, 5: 0.0}
BOUNDED = 0.85          # applied when the schema states a maximum / maxItems

D = 0.80 + 0.50 × ( 1 − Π (1 − WEIGHT[breadth] × bound_factor × ramp) )
```

An argument that pulls in whole containers keeps full influence; one that returns a few
more rows from a container already chosen counts for well under half. A `kind: none`
parameter contributes nothing regardless of its breadth — not because it is safe, but
because there is no number to compare. Its reach is the cell's business, not `D`'s.

The ramp itself is unchanged: quartiles are still learned per `(server, tool, argument)`
from observed values.

**Why this fixes what v1's ordering broke.** v1 ranked *every* input, so on a channel
listing tool the filter took first place and the page size — the argument that actually
multiplies channels reached — landed fourth and got the smallest weight. A request for the
largest page the API allows fell from 1.30 to 0.88. Under the scale above that page size
is breadth 1, weight 1.00, because the rubric asks what the value reaches rather than
which parameter looks most important.
