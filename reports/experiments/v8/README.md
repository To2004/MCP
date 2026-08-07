# v8 — can a gate tell *which asset* a call touches, at runtime, without a model?

Every arm before this one scored a **tool**. `update-event` is a write, so it
scores high — but a tool is not one action. It is one action per container it can
address, and the argument chooses. Scoring the tool alone leaves a gate two bad
options: block every write, or allow a write to `aurora-crew-roster` because
writes to `aurora-team` are fine. v8 asks whether the argument can close that gap.

**There is no key table.** A gate is not handed a mapping from
`071832f5…@group.calendar.google.com` to `aurora-crew-roster`, and maintaining one
by hand across every deployment is not a plausible ask. So the gate does not have
to *name* the asset — it has to **not under-score** it. The severity of a call is
therefore the **worst severity among every asset it could be touching**, and the
question v8 answers is how much that costs.

That framing carries a guarantee: as long as the true asset is somewhere in the
resolved set, the maximum over the set can never fall below the truth. **Recall
1.0 means under-scoring is impossible.** The only cost of not knowing is
over-scoring, and over-scoring is measurable.

Two further constraints, both non-negotiable:

**No model may run.** The decision happens in front of the server, on the call
path, per call. Every mechanism is deterministic Python — dictionary lookup,
regex, IDF-weighted token overlap. The scanner's LLM stages run at design time and
reach this experiment only as artifacts already on disk (the policy register, the
operation ladder). A resolution costs no tokens, reproduces exactly, and cannot be
steered by text an attacker places in an argument.

**Nothing may be configured per server.** No code names `calendarId`, `repo` or
`channel_id`; none names a listing verb or an organization's domain. Three
hand-written configs would have scored better and proved nothing about a fourth
server. Everything is discovered from observed traffic and validated against the
register — see [`src/mcp_security/binding/`](../../../src/mcp_security/binding/)
for the method.

## Data

The 3,000 real calls of the v5r `nacombo` live corpus — 1,000 per server against
three live MCP deployments, each labelled with the asset a human said it touched.
The resolver never reads that column.

| server | calls | tools | register rows | containers addressed |
|---|---:|---:|---:|---:|
| `calendar_aurora` | 1000 | 12 | 17 | 6 calendars |
| `github_helios` | 1000 | 24 | 19 | 5 repositories |
| `slack_vireo` | 1000 | 12 | 15 | 7 channels |

## Result 1 — discovery finds the container key, unaided

One key per server, and the right one, with no configuration:

| server | discovered key | enumerating verb found | rejected candidates |
|---|---|---|---|
| `calendar_aurora` | `calendarId` | none (listing output truncated in corpus) | `summary`, `start`, `end`, `eventId`, `timeZone`, `sendUpdates` |
| `github_helios` | `repo` | `search_issues`, `list_pull_requests` | `owner`, `path`, `branch`, `state`, `head`, `q`, `title`, `body`, `pull_number`, `issue_number` |
| `slack_vireo` | `channel_id` | `conversations_search_messages` | `limit`, `filter_in_channel`, `action`, `ts`, `channel_types` |

Each rejection carries its reason, and the reasons are structural rather than
tuned: `head` gets *"a new value on 100% of calls — minted per call, not reused"*;
`q` gets *"multi-word — natural language, not a handle"*; `limit` gets *"28 values
share 3 assets (11%) — a filter, not distinct containers"*.

`calendar_aurora` is the interesting case: the corpus truncates every tool output
at 280 characters, so `list-calendars` never shows a complete calendar. The
enumeration route is unavailable and the content-classification fallback carries
the whole server on its own — which is exactly the condition a filesystem or any
non-enumerable namespace imposes permanently.

## Result 2 — 16 of 18 containers bound correctly

| server | bound correctly | route |
|---|---|---|
| `calendar_aurora` | 5 / 6 | content only |
| `github_helios` | 5 / 5 | enumeration |
| `slack_vireo` | 6 / 7 | 5 enumeration, 2 content |
| **total** | **16 / 18 (0.889)** | |

Both misses are worth stating precisely:

- **`slack_vireo` is not a real error.** The channel binds to `vireo-announcements`,
  the register's id; the corpus labels those calls `announcements`. Every other
  prefixed pair scores 0.8 on the alias check and passes; this one scores 0.667 and
  does not. Counting it as correct gives **17/18 (0.944)**.
- **`calendar_aurora` is a real error.** `43c607dd…` binds to `aurora-crew-roster`
  when the label says `aurora-maintenance`. Both are operational-commitment
  calendars whose register descriptions share the vocabulary of schedules,
  windows and deadlines — content classification cannot separate them, and this
  is the failure mode that route has.

## Result 3 — the number a gate acts on: over-scoring

`L0` is the no-knowledge floor: every asset the tool can reach, worst severity.
`L3` reads the arguments. Severity is the register's 1-5 scale.

| server | over-score, no knowledge | over-score, reading the input | cut | exactly right |
|---|---:|---:|---:|---|
| `calendar_aurora` | +1.46 | **+0.85** | 42% | 24% → 32% |
| `github_helios` | +0.51 | **+0.20** | 62% | 37% → 62% |
| `slack_vireo` | +0.68 | **+0.27** | 61% | 46% → 73% |
| **mean** | **+0.88** | **+0.44** | **51%** | |

**Reading the arguments halves the over-scoring**, and roughly doubles how often
the gate assigns exactly the right severity. On two servers, under-scoring is
**0.000** — the guarantee holds empirically, not just on paper.

### Where the guarantee breaks, and why

`github_helios` under-scores on **18%** of calls. That is not a resolver failure
and no narrowing can fix it: the register's `Tools` column does not home
`create_pull_request_review` to the repositories it is labelled against, so the
true asset is not in the candidate set at all and the maximum over that set is
below the truth.

**Under-scoring occurs exactly where register coverage is incomplete** — recall
0.630 on that server, 18% under-scored. That makes register completeness a
*safety* property rather than a tidiness one, and it is the single most valuable
thing to fix before any of this is deployed.

## Result 3b — the ablation: what each mechanism buys

Averaged over the three servers, 3,000 calls:

| level | mean set size | top-1 accuracy |
|---|---:|---:|
| L0 tool-only | 5.65 | 0.124 |
| L3 full | 2.83 | 0.551 |

**Set size halves and top-1 goes up 4.4×, with recall unchanged.** Per server:

| server | L0 recall | L3 recall | L0 top1 | L3 top1 | L0 set | L3 set |
|---|---:|---:|---:|---:|---:|---:|
| `calendar_aurora` | 0.930 | 0.930 | 0.078 | **0.677** | 6.33 | 3.28 |
| `github_helios` | 0.630 | 0.622 | 0.084 | **0.541** | 4.08 | 2.36 |
| `slack_vireo` | 0.553 | 0.553 | 0.211 | **0.434** | 6.52 | 2.85 |

The whole gain comes from `L1 +catalog`; `L2 +operation` and `L3 +egress` move
top-1 by ~0.02 and mainly trim set size. **Binding the argument to a container is
the mechanism that matters** — the structural refinements are second-order.

## Result 4 — the register is the binding constraint, not the resolver

`L0 recall` is the ceiling: the fraction of calls whose labelled asset the
register's `Tools` column homes to that tool at all. No resolver can exceed it,
and on two servers it is the number that hurts.

- **`github_helios`: 0.630.** `create_pull_request_review` is labelled against
  `helios-scada-gateway` 36 times, but that row's `Tools` cell does not list the
  verb. Same for `create_issue` and `list_issues` on `helios-grid-infra-config`.
  The register's homing is incomplete, and this is the same gap v7 shows from the
  other side, where the scored matrix came out *wider* than the register.
- **`slack_vireo`: 0.553.** Six labels (`eng-platform`, `trial-ops`,
  `announcements`, `safety-pv`, `regulatory-fda`, `lab-informatics`) are not
  register ids at all — the register spells them `vireo-*`. Under the
  alias-tolerant measure recall is **0.922**, so this is a corpus labelling
  defect, not a method result. It needs fixing before v8 numbers are quoted
  anywhere.

## Result 5 — resolution does not degrade under attack

Recall by call category, at L3:

| server | BENIGN | MISUSE | MALICIOUS |
|---|---:|---:|---:|
| `calendar_aurora` | 0.958 | 0.804 | **1.000** |
| `github_helios` | 0.428 | 0.912 | 0.720 |
| `slack_vireo` (alias) | 0.844 | **1.000** | **1.000** |

This is the security-relevant direction: adversarial calls resolve at least as
well as benign ones, and on two servers perfectly. An attacker gains nothing by
naming the crown-jewel container, because naming it is what binds it. The one
place resolution weakens is the *unbound* path — and that path returns the closure
over every container rather than a guess, so it fails loud rather than low.

## What the resolver refuses to do

- An identifier nothing binds returns the **closure** over every container the
  verb can reach, flagged `unresolved_container`. Guessing low is how a gate gets
  walked past.
- A call naming no container at all is a genuine **fan-out** (`slack_vireo` 17.6%,
  `github_helios` 8.1%, `calendar_aurora` 0%), reported separately.
- A creation verb that mints a container the catalog cannot yet know is flagged
  `mints_container` — the case where binding is impossible in principle, because
  the asset does not exist until after the call.

## Result 6 — transfer to server kinds the rules never saw

The rules were written against calendar, GitHub and Slack. Two other kinds
already in the repo — `sqlite` and `filesystem` — were then run with **no code
changes**, over the full `tool × asset` matrix (keys supplied, as in Result 3b):

| server | L0 tool-only | with the arguments | recall | cells reached |
|---|---:|---:|---:|---|
| `sqlite_cbg_sqlite` | 7.79 | **1.97** | 1.000 | 33 / 33 |
| `fs_corp_filesystem` | 6.10 | **2.29** | 1.000 | 51 / 51 |

**The first run of `fs_corp_filesystem` narrowed nothing at all — 6.10 → 6.10.**
`canonical_id` was stripping everything before the last `/`, which is correct for
GitHub's `owner/repo` and destroys a filesystem, where `sensitive/keys/id.pem` and
`public/keys/id.pem` are different assets with the same basename. Three
development servers all used a prefix qualifier, so none of them could ever have
shown it. Identifier matching now tries the full value, then shorter tails
(prefix qualifiers), then shorter heads (hierarchies).

`sqlite` forced a second mechanism: `read_query(sql="SELECT * FROM api_keys")`
carries the identifier *inside* a free-text argument with no container parameter
at all. Building that also improved the original servers — Slack fan-out on the
live corpus fell from 17.6% to 11.9% (`filter_in_channel`), and it covers GitHub's
`search_code(q="repo:owner/name …")`. Three independent servers demanding the same
mechanism is the best evidence available that it is general rather than fitted.

## Result 7 — what is still fitted, honestly

| still hand-written | server-specific? |
|---|---|
| read / write verb words | no — general English |
| time, recipient, query parameter words | no — general naming conventions |
| egress words (*leaving, outside, external*) | no — general |
| the `"What a …"` register phrasing | **yes — one author wrote every register here** |
| the `metadata-only` flag name | **yes — this repo's policy spec** |
| ~11 numeric thresholds | no sensitivity analysis has been run |

Lexicons are provably incomplete: mid-development the mode mechanism silently
picked the wrong asset because `authorise` was missing from the write verbs. The
defensible claim is **the structure transfers across five server kinds; the
register-phrasing conventions do not.**

## Limitations

- Five server kinds, one deployment each. Better than three, still small.
- The held-out key tables for `sqlite` and `filesystem` were supplied by hand.
  That matches the harness premise (keys given) but means those two servers test
  *resolution*, never *discovery*.
- The thresholds are global — one set of five constants across all three servers,
  never per server — but they are still constants, and no sensitivity analysis
  has been run on them.
- The corpus labels one asset per call while the truth is a set, so `recall` and
  `mean set size` must be read together; neither alone is meaningful.
- The filesystem server, the only genuinely non-enumerable namespace, is not in
  this corpus. It is where the content route would face its real test.

## Reproducing

```bash
uv run python scripts/evaluate_binding.py                       # live corpus, keys discovered
uv run python scripts/evaluate_binding_synthetic.py             # full matrix, keys given
uv run python scripts/evaluate_binding_synthetic.py --held-out  # sqlite + filesystem
uv run pytest tests/test_binding.py                             # 27 tests, invented server kind
```

| file | what it holds |
|---|---|
| [`METHOD.md`](METHOD.md) | **how the method works**, with diagrams and a real call traced end to end |
| `synthetic_results.json` | full `tool × asset` matrix, three development servers |
| `synthetic_heldout.json` | same, on `sqlite` and `filesystem` — kinds the rules never saw |
| `given_keys.json` | the key tables supplied to the synthetic harness |
| `binding_results.json` | full per-server result: discovery, bindings with evidence, every level, per-category |
| [`src/mcp_security/binding/`](../../../src/mcp_security/binding/) | the method, with its own README |
