# Real MCP Warm-Up — What Was Run and What It Showed

Every corpus this project had was generated from its own scan artifacts, so the
argument sizes in it were chosen by whoever wrote the generator. Any "unusually broad"
call found in such a corpus is unusual with respect to an invented distribution. This
run replaces that with traffic whose breadth comes from real account state: **1000
read-only calls against each of the three real MCP servers**, driven through the real
protocol with live credentials.

Date: 2026-08-13. Scripts: `scripts/dynamic_design/`.

## What ran

| server | package | calls | ok | failed | rate | real state driving breadth |
|---|---|---:|---:|---:|---:|---|
| github | `@modelcontextprotocol/server-github` | 1000 | 889 | 111 | 2.1/s | 12 repositories, real trees |
| calendar | `@cocal/google-calendar-mcp` | 1000 | 703 | 297 | 2.7/s | 17 calendars |
| slack | `slack-mcp-server` | 1000 | 866 | 134 | 1.6/s | 24 channels |

All three advertise exactly the catalogs the scanner captured: 26 / 13 / 15 tools.

Calendar's failures are Google's per-minute query quota (I paced at 0.1 s = 10 calls/s,
which is over it). GitHub's are mostly `search_code` queries with no results. **Neither
affects the breadth data**: the corpus records the arguments *sent*, and a call that was
rate-limited still carries a real, really-chosen argument.

**Read-only by construction.** Every tool used reads; the servers point at live
accounts, so a write would be a real external change. Slack's message-posting tool is
left disabled via `SLACK_MCP_ADD_MESSAGE_TOOL`.

Breadth comes from real cardinality rather than from a distribution anyone picked: the
number of calendars in a `list-events` call is bounded by how many exist on the account,
Slack's `limit` spans the formats that server actually accepts (`1d`/`30d`/`50`), GitHub's
`perPage` spans the API's own legal range. What remains authored is *which* call to make
— unavoidable for any generator, and worth stating rather than glossing.

## Does the breadth spec cover the calls?

Two different questions, separated because they fail differently. **Name coverage**: is
the argument in the spec at all? **Extraction coverage**: of the arguments called a
quantity, how many actually yield a number? The second matters more — a parameter
classified as a quantity but never parsed looks covered and contributes nothing.

| server | source | arg instances | distinct | name gap | classified | extracted | extract % |
|---|---|---:|---:|---:|---:|---:|---:|
| github | schema | 2791 | 13 | 1 | 383 | 383 | 100% |
| github | llm | 2791 | 13 | 1 | 383 | 383 | 100% |
| slack | schema | 1954 | 9 | 0 | 1047 | 1047 | 100% |
| slack | llm | 1954 | 9 | 0 | 1047 | 1047 | 100% |
| calendar | schema | 2560 | 10 | 0 | 2364 | 788 | 33% |
| calendar | llm | 2560 | 10 | 0 | 1991 | 415 | 21% |

**Name coverage is effectively total** — one gap in 32 distinct `(tool, argument)` pairs:
`list_issues.perPage`, which the live server accepts and the scanned schema does not
declare. That is the schema-versus-wire drift predicted earlier, now observed on real
traffic rather than argued about.

**The LLM answer: yes, it covers the calls** — every argument real traffic sent is in
both specs, save that one. The LLM's advantage is elsewhere and was measured on servers
never inspected while writing the rules: on `sqlite` it classified `read_query.sql` as a
quantity, reading *"the query can return up to 100 rows"* out of the description, where
a schema-only pass sees a bare `string` and reports nothing. Breadth living inside a
query language is invisible to JSON Schema, and the model found it.

## Two defects the real traffic exposed

**1. The label ambiguity had a real cost.** Before the fix, `github/llm` extracted
**0 of 340** quantities. The classifiers disagree about whether a paged `perPage` is a
`count` or a `magnitude`; the parser was label-driven, and a count parser demands a list
while `perPage` is an integer. So a purely taxonomic disagreement silently discarded
every quantity on that server.

The fix inverts the dependency: **`kind` decides only whether to look, the value's own
shape decides how to read it.** Lists and dicts give their length, numbers give their
value, numeric strings parse with unit suffixes, and a scalar where a collection was
expected is a collection of one. That took github from 0% to 100% and slack from 86% to
100%, and it makes the runtime immune to the count/magnitude confusion rather than
dependent on resolving it.

**2. `range` was classified and never extracted.** 1,380+ instances of `timeMin`/`timeMax`
were labelled correctly and dropped, because a single endpoint is not a quantity — the
span is. `span_of()` now emits one `<span:days>` quantity per call from the widest pair
of endpoints. This was the single largest class of quantity arguments in the corpus, and
a per-argument parser cannot see it by construction.

Calendar's remaining 33% is largely an artifact of how the table counts: each endpoint is
counted as "classified but not extracted" while the span it contributes to is not a wire
argument and is not counted at all.

## The dynamic layer, warmed on real traffic

```
warm-up: 2982 real calls -> 10 tracked quantities, 10 with enough history to judge

D          calls    share            (cold, for comparison)
0.8         1104   36.8%              21.8%
1.0         1896   63.2%              78.0%
1.3            0    0.0%               0.1%

speed: 3000 calls in 64.8 ms = 46,329 calls/sec (21.6 us/call)
```

### Warm-up transfer is partial, and that is the sharpest finding

The warm-up and the corpus under test do not exercise the same arguments. Of the 15
quantities the test corpus carries, the 3000 real calls warmed **8**:

| server | quantities warmed | quantities in test | overlap |
|---|---:|---:|---:|
| slack | 5 | 6 | 5 |
| calendar | 3 | 7 | 3 |
| **github** | 2 | 2 | **0** |

GitHub's real traffic exercised `list_commits.perPage` and `search_repositories.perPage`;
the test corpus uses `push_files.files` and `update_issue.labels`. **No shared argument at
all**, which is exactly why github still scores every call 1.0 after a thousand real calls
of warm-up. The warm-up is not too small — it is aimed somewhere else.

This generalises past this run: a per-argument reference means warm-up only transfers
where the same argument recurs. Coverage has to be planned per *argument*, not per server
and not by call volume.

Two things worth reading carefully.

**The warm-up works**: calls judged "ordinary" rose from 21.8% to 36.8%, because real
history supplies fences for arguments the cold run had to abstain on.

**And 1.3 went to zero.** Real-world normal is *wider* than the synthetic corpus's range,
so once the fences are set by observed practice, nothing in `live_scale` exceeds them.
That confirms the four abnormals the cold run produced were cold-start artifacts —
tight early fences, not broad calls. **The corpus under test contains no breadth
anomalies at all**, and warming on real traffic is what made that visible.

Speed is not a constraint: 23 microseconds per call, no model, no network, no state
beyond a capped per-argument history.

## What happens when an ID is wrong

Traced end to end against the live server, warmed on the real corpus:

| call | D | reason |
|---|---:|---|
| `list-events(calendarId="primary", 7-day span)` | 0.8 | `calendarId=1 normal` |
| `list-events(calendarId="X8912-does-not-exist", 7-day span)` | **0.8** | `calendarId=1 normal` — identical |
| `get-event(eventId="X8912")` | 1.0 | no quantity argument |
| `list-events(calendarId=[50 calendars], 365-day span)` | **1.3** | `calendarId=50 abnormal` |

**A wrong ID scores exactly like a right one**, which is the design working as
specified: an unknown identifier must not raise risk, or every first-time access becomes
an alert. Breadth still fires where it should — fifty calendars reaches 1.3.

**Errors are ignored, deliberately.** The reference answers *what breadth does this
organization ask for*, not *what succeeded*. Checked against the real failures, that is
the right call: every one was incidental — GitHub's were empty `search_code` results and
rate limits, Slack's 134 were all the placeholder `thread_ts` in this generator,
Calendar's 297 were Google's per-minute quota. **Not one was the organization declining
to work that way**, and the arguments in all 543 were perfectly ordinary. Filtering them
out discarded 543 valid observations and left the fences worse informed — tracked
quantities fell 10 to 9 and the "ordinary" share dropped 36.8% to 35.0%. Telling a
semantic refusal from a transient one would need per-server error parsing, which does not
generalise. Status is not read.

**A wrong ID also enumerates the right ones.** The live error carries
`Available calendars: ...`, so probing is a real misuse shape here — and one this design
cannot see, since every probe carries a single identifier and `count = 1`. It would only
show up as a failure rate, which is both cross-call (out of scope) and error-derived
(ignored by design). **This is an accepted boundary, not a gap to close**: the runtime
does not know which identifiers are valid, and nothing about a single unknown identifier
distinguishes a typo from an attack.

## What is still wrong

- **Only 10 tracked quantities across 2982 real calls, and 0 of github's transfer.** The
  generator exercises a handful of arguments per server. Coverage has to be planned per
  argument, not per server — see the transfer table above.
- **No abnormal traffic exists anywhere.** Both corpora are ordinary use. Nothing has yet
  demonstrated that D separates broad calls from narrow ones, because no broad calls have
  been observed — only that it declines to invent them.
- **`list_issues.perPage`** — one live argument absent from the scanned schema. Small, but
  it is the failure mode that matters: a missing name is silently skipped, and the call
  scores as though it had no quantities.
- **Calendar quota** capped the run at 703 successful calls; pacing needs to respect
  per-minute quotas, not just per-day.
- **The LLM's kind labels remain inconsistent** (`read_file.tail` = count,
  `read_text_file.tail` = magnitude). Now harmless, because extraction ignores the label.

## How I would improve it

1. **Collapse `count` and `magnitude` into one `quantity` label.** The evidence is now
   from real traffic rather than the dev set: the distinction never changed an
   extraction outcome and once destroyed 100% of one server's coverage. The model is
   reliable on *whether* something is a quantity (90–96%) and unreliable on *which kind*.
   Asking only the reliable question removes the failure mode by construction.
2. **Reconcile schema names against wire names at load**, and report the gap rather than
   skipping unknown arguments in silence.
3. **Plan the call set per argument, not per server.** The transfer table shows volume is
   not the constraint: 1000 real github calls warmed nothing the test corpus uses. Drive
   every `(tool, argument)` the breadth spec marks as a quantity — roughly 40 of them —
   rather than whichever ones a hand-written plan happened to reach.
4. **Get genuinely broad calls into a corpus** without inventing the distribution. The
   honest source is real usage that happens to be wide — a real bulk export, a real
   backfill — not a script that picks large numbers, since detecting deviation from a
   distribution we authored proves nothing.

## Reproduce

```bash
export GITHUB_TOKEN=$(gh auth token)
export SLACK_MCP_XOXP_TOKEN=...          # from Keys.zip, line SLACK_MCP_XOXP_TOKEN=
export GOOGLE_OAUTH_CREDENTIALS=/path/to/googlecalendarkey.json

python3 scripts/dynamic_design/make_real_warmup.py --server github   --n 1000
python3 scripts/dynamic_design/make_real_warmup.py --server calendar --n 1000 --pace 0.5
python3 scripts/dynamic_design/make_real_warmup.py --server slack    --n 1000 --pace 0.4

python3 scripts/dynamic_design/check_breadth_coverage.py --corpus real
python3 scripts/dynamic_design/dynamic_v2.py --warmup reports/experiments/real_warmup/*.csv
```

The breadth spec itself: `breadth_spec.py` (schema, deterministic) and `breadth_llm.py`
(qwen2.5:32b via `breadth_llm.sbatch` — 74 tools, 0 unusable replies, ~8.5 min on one
RTX 4090).
