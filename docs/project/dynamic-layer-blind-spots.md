# What the Dynamic Layer Sees, and What It Cannot

An audit of the runtime layer against what a server-side observer could in principle
measure. Three questions: which dimensions are covered, which are excluded on purpose,
and which were simply forgotten. The third list is the useful one — two entries, both
measured, both cheap.

Companion to [Dynamic Layer v2 — The Calculation](dynamic-layer-formula-v2.md).

## The classifier generalises — swept across every catalog on disk

Before auditing the dimensions, the coverage question: does the breadth spec work outside
the three servers it was written against? Ten catalogs, none of the seven new ones
inspected while writing the rules:

| catalog | tools | inputs | quantity args | required | w/ default | optional, no default |
|---|---:|---:|---:|---:|---:|---:|
| maverick | 119 | 306 | 165 | 21 | 144 | 0 |
| openbb | 30 | 111 | 48 | 8 | 12 | 28 |
| github | 26 | 130 | 25 | 1 | 0 | 24 |
| sec_edgar | 21 | 50 | 18 | 4 | 14 | 0 |
| slack | 16 | 63 | 19 | 2 | 9 | 8 |
| filesystem | 14 | 25 | 8 | 2 | 2 | 4 |
| calendar | 13 | 110 | 54 | 15 | 0 | 39 |
| finance_tools | 17 | 19 | 5 | 2 | 3 | 0 |
| yahoo_finance | 9 | 17 | 4 | 3 | 1 | 0 |
| sqlite | 5 | 5 | 0 | 0 | 0 | 0 |
| **total** | **270** | **836** | **346** | **58** | **185** | **103** |

**41% of all inputs carry a quantity**, on servers the rules never saw. `sqlite`'s zero is
the known structural limit: its breadth lives inside SQL, which no schema declares.

## Covered

| dimension | how | where it comes from |
|---|---|---|
| how bad the action could be | `cell(tool, asset)` | the scan, design time |
| how much this call covers | `D` — quantity arguments against observed quartiles | runtime, per call |

## Excluded on purpose, and why

| dimension | why not |
|---|---|
| **identity / roles** | not obtainable without OAuth; and the design does not gate on who |
| **ownership** (does this caller own object X) | this is BOLA, [OWASP API #1](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/). Detecting it needs ownership context and multiple identities ([AuthProbe](https://arxiv.org/abs/2607.20574) is explicit about this). Unavailable, so out of scope by construction |
| **intent** | lives on the agent side; the server never sees the task. This is what [Intent-Governed Access Control](https://arxiv.org/html/2606.22916v2) does, from the other vantage point |
| **provenance / taint** | needs agent-side visibility into what the agent read |
| **rate, burst, sequence** | cross-call state; dropped so the scorer stays a pure function |

Each of these is a *stated boundary*, not a gap. Together they are why this is a
prioritisation signal rather than an access-control mechanism.

## Forgotten — and both are in scope

### 1 · The absent bound scores lower than a large one

Measured, warmed on real traffic:

```
conversations_history  limit=10           ->  D 0.81
conversations_history  limit=999          ->  D 1.30
conversations_history  OMITS limit        ->  D 1.00      <-- broader than 999, scored lower

list-events            7-day window       ->  D 0.80
list-events            OMITS timeMin/Max  ->  D 0.80      <-- all of time, same score

list_commits           perPage=100        ->  D 1.25
list_commits           OMITS perPage      ->  D 1.00
```

Omitting a limiting argument is the *widest possible* request — the caller has expressed
no bound at all — and the runtime reads it as "no information" and abstains. This is
precisely the case the original scan called `unbounded (no LIMIT)`, which the parser
dropped because it carried no number.

It is also the canonical form of [OWASP API4:2023 Unrestricted Resource
Consumption](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/):
the most common manifestation of unbounded fetching is a query with no `LIMIT`, `TOP`, or
equivalent constraint.

**The fix is in the schema already.** Of the 346 quantity arguments swept above:

- **185 declare a default.** Substituting the declared default when the argument is
  omitted is exact, deterministic, and free — Slack's `conversations_history.limit`
  defaults to `"1d"`, so an omitted limit should score as a one-day window, not as
  silence.
- **103 are optional with no default.** For these, absence genuinely means unbounded, and
  the honest score is the top of the ramp, not the middle.
- 58 are required and cannot be omitted.

### 2 · The response is never looked at

The layer scores the *request*. It never reads what came back — and the response is the
only place the true breadth of a call is visible. A request with `limit` omitted looks
like nothing; its response is a megabyte.

On 17 real tool calls captured from one server, response bodies ranged **112 to 19,519
bytes — a factor of 174**. For comparison, `D` spans a factor of 1.625 end to end. The
response carries roughly two orders of magnitude more dynamic range than every request
argument combined.

This is a recognised signal: unusual response payload size is a primary data-exfiltration
indicator, and the case it catches is exactly the one rate limiting misses — a client
making a modest number of calls that each return very large bodies.

**And this layer is unusually free to use it.** A blocking gateway must decide before the
call executes, so the response is unavailable to it. This layer never blocks; it ranks a
queue a human reviews afterwards. The constraint that looked like a weakness is what
makes the strongest available signal admissible.

The data is already captured — `logs/proxy/.../parsed/calls.csv` carries `response_text`,
and the mitmproxy capture carries `resp_body`. What is missing is that
`make_real_warmup.py` records only `status`, so the corpora built for this work discarded
response sizes. That is a one-field change to the generator.

## Worth considering, not yet argued either way

- **Time of day.** A per-call timestamp needs only a per-organization histogram, not
  sequence state, so it does not violate the stateless constraint. It is a standard
  exfiltration signal. Whether an agent framework has a meaningful "unusual hour" is an
  open question.
- **Multi-signal composition.** The API-security literature is consistent that combined
  signals beat any single one — a broad request *plus* a large response is stronger
  evidence than either. The current formula takes the widest single quantity; combining
  request breadth with response volume is the obvious first composition.

## What this changes

Nothing about the formula's shape. Both forgotten dimensions are quantity arguments in
the same sense the existing ones are: an omitted bound is a quantity whose value is
"unbounded", and a response size is a quantity measured after the fact rather than parsed
from the request. Both feed the same quartile reference and the same ramp.

The ID question, by contrast, stays closed. Identifiers are opaque, ownership is
unavailable, and a single unknown identifier does not distinguish a typo from an attack.
Counting *distinct* identifiers is breadth and is already covered per call; counting them
across calls is the session dimension that was deliberately dropped.
