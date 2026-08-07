# Runtime asset binding

Which policy-register asset does a given call actually touch?

The static arms score a **tool**: `update-event` is a write, so it scores high.
But a tool is not one action — it is one action per container it can address, and
the argument chooses. Scoring the tool alone means either blocking every write or
allowing a write to the crew roster because writes to the team calendar are fine.
This package closes that gap: it turns `(tool, arguments)` into the set of
register assets the call reaches.

## Two properties that constrain the design

**No model runs on the call path.** A gate decides in front of the server, per
call, so every mechanism here is deterministic Python — dictionary lookup, regex,
IDF-weighted token overlap. The scanner's LLM stages run at design time and reach
this package only as artifacts already on disk. A resolution costs no tokens,
reproduces exactly, and cannot be steered by text an attacker writes into an
argument.

**Nothing is configured per server.** No file here names `calendarId`, `repo` or
`channel_id`; none names a listing verb or an organization's domain. All of it is
discovered from observed traffic and validated against the register, so the same
code resolves a server kind it has never seen. Three hand-written configs would
have scored better and proved nothing.

## Modules

| module | what it does |
|---|---|
| `identifiers.py` | text primitives: key folding, identifier canonicalization, tokens, proximity windows |
| `discovery.py` | derives the container key, the enumerating verb, the org domains, and the id → asset bindings |
| `resolver.py` | `(tool, args) → set[asset]`, in four ablation levels |

## How discovery works

The register's `Tools` column already says which assets a tool *can* reach. The
arguments only narrow that list, so resolution never searches the asset space.
What it needs is the link from a runtime identifier to a register row, and that is
derived in three steps.

**1 — which argument names a container.** Five gates, none of them domain
knowledge:

| gate | rejects |
|---|---|
| bounded value set | `summary`, `path`, `branch` — free text |
| reused, not minted per call | `eventId`, `head`, `pull_number` — a new value nearly every call |
| values are handles, not phrases | `q`, `title`, `body` — multi-word natural language |
| taken by more than one verb | `filter_in_channel` — a filter one verb needs |
| values map near one-to-one onto register rows | `limit`, `state` — many values, one asset |

**2 — which verb enumerates them.** Whichever tool's *output* contains those
identifiers. A server that lets an agent address a container also, somewhere,
lets it enumerate them. The human name is read from the text nearest the
identifier — nearest, not merely present, because a compact listing puts every
name inside one window. A link is believed only when most occurrences agree, which
is what separates a listing from coincidence, with no per-format parser.

**3 — when nothing enumerates.** Fall back to classifying what calls against the
identifier returned, scored against register descriptions. Only tokens that
*distinguish* one container from its siblings count; shared scaffolding collapses
every container onto whichever row uses the same common words. This route is
weaker, so it must clear a higher bar before it may establish a key rather than
merely extend one.

Steps 2 and 3 mirror how production systems answer the same question — XACML's
Policy Information Point resolves resource attributes from the authoritative
source at decision time; Microsoft Purview and AWS Macie classify content once and
look the label up later.

## The four levels

| level | mechanism |
|---|---|
| `TOOL_ONLY` | the register candidate set, unfiltered — the recall ceiling and the baseline |
| `CATALOG` | container identifiers resolved through the discovered bindings |
| `OPERATION` | drop rows describing the opposite operation — a read does not touch "what a write creates" |
| `EGRESS` | admit boundary-crossing rows only when the call carries an address outside the org, or mints a container |

## What it refuses to do

- **Never guesses a container.** An identifier nothing binds returns the closure
  over every container the verb reaches, flagged `unresolved_container`. Guessing
  low is how a gate gets walked past.
- **Never catalogs a call-target row.** `event-records` ("What a create/update/
  delete targets") has no standing identity for an argument to name.
- **Returns a set, not one asset.** `update-event` genuinely touches the calendar,
  the event record, and the attendee list at once.

## Usage

```python
from mcp_security.binding import AssetResolver, Level, discover

found = discover(observed_calls, register_rows)          # once per deployment
resolver = AssetResolver(register_rows, found, tool_ops)  # once
resolution = resolver.resolve("update-event", args)       # per call
resolution.asset_ids       # frozenset of register asset ids
resolution.primary         # single best answer, or None when it genuinely spreads
resolution.mints_container # this call creates a container no catalog can know
```

Measured by [`scripts/evaluate_binding.py`](../../../scripts/evaluate_binding.py);
results in [`reports/experiments/v8/`](../../../reports/experiments/v8/).
