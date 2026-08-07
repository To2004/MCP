# Ground Truth — every number and mechanism the paper may claim

**Authoring rule: if it is not in this file or in `refs.bib`, it may not be
written.** No number may be rounded, restated, or extrapolated. When a fact is
absent here, the correct action is to omit the claim, not to estimate it.

Source of record for each block is given so a reviewer (or a verifier agent)
can re-check it.

## 1. The scoring model

Source: `reports/experiments/v5/PROMPT_ROLES.md`,
`src/mcp_security/static_scoring/pipeline.py`

Three primitives, each on 1–5, multiplied:

```
score = asset_sensitivity x blast_radius x tool_impact      range 1..125
```

then a deterministic assembly (bulk twins, alias twins, gated blast floor) and
`band_label()` → one of {low, medium, high, critical}. The `v5r` mode removes
the blast roof; a roof can only ever under-score.

Bands are not raw thresholds. `band_label()` encodes explicit security floors —
e.g. any irreversible operation is at least medium. Floors were derived by
measuring where an LLM reviewer systematically disagreed with raw thresholds.

### Pipeline stages (v5r: four prompts)

| Stage | What | LLM? |
|---|---|---|
| 0 | Domain inference — once per server, from the whole catalog | yes |
| 1 | Tool impact (1–5), per tool | **rules first**, LLM only on abstention |
| 2 | Asset sensitivity (1–5), per asset | yes — classify→map against the policy |
| 3 | Blast radius (1–5), per (tool, asset) | yes |
| — | Assembly + banding | deterministic |

Inputs are exactly two documents: the captured tool catalog (`tools/list`) and
the organization's policy section. The per-asset sensitivity table in
`server-profiles.md` is **held out** and used only as ground truth.

### The deterministic impact ladder

Source: `reports/experiments/v5/STATIC_RULES.md`,
`static_impact.classify_by_operation()`

One question decides the tier: is this operation a read, a write, or a removal?

| Tier | Operation |
|---|---|
| 1 | none — server talks about itself (ping, health, version, whoami) |
| 2 | metadata — names, ids, counts, sizes, timestamps, permissions, schema, listings; consumption state |
| 3 | content read **or** limited write (append a line, add a comment, set one named field) |
| 4 | ordinary write — caller supplies what the item says |
| 5 | removal or execution — delete, wipe, drop, purge, truncate; execute code; move money |

Vocabulary: **281 patterns** (none 16, metadata 52, read 46, write 122, remove
45), plus 119 ambiguous single words (name-scoped), 10 generic read verbs, 9
parameter detectors.

**The 3/4 boundary is externally grounded**, and this is citable:

| | tier 3 | tier 4 |
|---|---|---|
| HTTP | `PATCH` — partial modification, unmentioned fields untouched (RFC 5789) | `PUT` — client sends the complete representation (RFC 9110) |
| CVSS v4.0 integrity | `VI:L` — "the amount of modification is limited" | `VI:H` — "a total loss of integrity" |

Breadth is deliberately **not** on this ladder — blast radius scores coverage.
The rules read no breadth vocabulary (`all`, `every`, `bulk`, `batch`), no
glob, no recursion switch.

### Rules-to-model hand-off

`classify()` reports a confidence: **0.35** when no tier verb matched, **0.8**
when a verb fired, **0.95** when a verb fired and an MCP annotation corroborated
it. The model is consulted when confidence < `STATIC_IMPACT_MIN_CONFIDENCE`
(0.5) — the case where the rules do not know, not where they disagree.
`tool_impact_source` records the deciding scorer per tool.

## 2. The dynamic layer

Source: `docs/project/dynamic-scoring-design.md`, `src/mcp_security/dynamic/`

Static answers "how bad if this happens". Dynamic answers "how abnormal is this
call, from this agent, in this session, given its actual input".

Four signals, cheap → expensive:

| # | Signal | File | LLM? |
|---|---|---|---|
| 0 | Embedding likelihood — hashing vectorizer over tool + arg tokens + structural flags, TruncatedSVD, novelty = mean distance to 5 nearest historical calls, calibrated against the history's own quantiles (q99 → z=2) | `dynamic/embedding.py` | no |
| 1 | Behavioral baseline — deviation from the persona's own history: unseen tool, first touch of a high-sensitivity asset, burst above normal rate | `dynamic/baseline.py` | no |
| 2 | Session sequence risk — cumulative sensitivity in a session; flags sensitive-read → external-write within a window | `dynamic/sequence.py` | no |
| 3 | LLM judge — decodes/normalizes arguments (base64, hex, shell expansion), classifies intent | `dynamic/judge.py` | yes, optional |

Two compositions coexist:

- band signals (baseline / sequence / judge) fuse via `escalate()` and can only
  **raise** risk above the static floor;
- embedding likelihood fills the likelihood slot: `final_risk = static_score x
  likelihood`, likelihood in **[0.1, 1.0]**. The 0.1 floor bounds the discount —
  a scanned-critical cell keeps a tenth of its risk even when the call looks
  demonstrably normal. A call with no benign history keeps full static risk
  (likelihood 1.0).

Performance: fit **< 0.5 s per server**, scoring **~0.05 ms per call**.

## 3. Static evaluation — v5

Source: `reports/experiments/v5/five_level_v2_policy_v5/EVALUATION.md`

Three real vendor servers. **56 assets, 55 tools.** Ground truth = the held-out
per-asset table in `server-profiles.md`.

| Server | Assets | Tools | MAE | Exact | Within 1 |
|---|--:|--:|--:|--:|--:|
| calendar_real | 16 | 13 | 0.125 | 88% | **100%** |
| github_real | 20 | 26 | 0.10 | 90% | **100%** |
| slack_real | 20 | 16 | 0.10 | 90% | **100%** |

**50 of 56 assets match exactly; no asset is off by more than one tier**, from
a document that states no number anywhere.

The six misses, all adjacent-tier, all defensible:

| Asset | Derived | Org | Reading |
|---|--:|--:|---|
| `account-directory` (calendar) | 5 | 4 | sits beside the Restricted-class account configuration in the register |
| `calendar-records` (calendar) | 2 | 3 | read as a bare attribute listing |
| `infra-config` (github) | 4 | 5 | scored as serious-lasting-harm, not control-plane |
| `repository-catalog` (github) | 3 | 2 | full catalog enumeration maps the estate |
| `incident-response` (slack) | 5 | 4 | `self-sufficient` flag + credentials pasted mid-incident |
| `research-team` (slack) | 4 | 3 | pre-publication research read as competitively damaging |

### Tool impact — the ladder needed no model

| Server | Tools | Static ladder | LLM fallback | Agrees with v4's LLM |
|---|--:|--:|--:|--:|
| calendar_real | 13 | 13 | 0 | 13/13 |
| github_real | 26 | 26 | 0 | 24/26 |
| slack_real | 16 | 16 | 0 | 14/16 |

**55/55 decided by rules, 0 LLM calls, 51/55 (93%) agreement with v4's LLM**;
every disagreement is one tier (`get_pull_request_files` 3 vs 2, `search_users`
3 vs 2, `conversations_leave` 4 vs 5, `usergroups_me` 5 vs 4).

**Important honesty constraint.** The fallback never fired because all three
vendor catalogs declare no MCP annotations, so every tool's confidence was
either 0.8 or 0.35 — nothing landed in between. The hybrid hand-off is
**covered by unit tests only** on this corpus. Do not claim it was exercised.

### Blast radius — the noisy stage

| Server | Cells | Differing | Raised | Lowered | Became N/A | Left N/A |
|---|--:|--:|--:|--:|--:|--:|
| calendar_real | 208 | 40 | 11 | 3 | 15 | 11 |
| github_real | 520 | 100 | 26 | 21 | 32 | 21 |
| slack_real | 320 | 72 | 30 | 18 | 16 | 8 |

19–22% of cells moved between arms with the same rubric and same asset ids. v4
measured **23–35 cells per server** of run-to-run variance with the prompt held
fixed, so this is at or somewhat above that stage's own noise. Roughly half the
movement is the relevance gate flipping.

Totals move in **both** directions — policy context is not a uniform discount:
Σ score calendar 2280 → 2697, slack 3779 → 4096, github 6340 → 5328.

## 4. Dynamic evaluation — discrimination

Source: `reports/dynamic_eval/SUMMARY.md`

Self-generated discrimination test; labels come from the synthetic testbed by
construction. Each session scored static-only and static⊗dynamic, so the delta
is exactly what the dynamic signal adds. A session's score is its riskiest call's
band.

**Flag threshold = high**

| Scorer | Recall (adversarial) | Flagged (misuse) | Fall-out (benign) |
|---|--:|--:|--:|
| static | 91% | 63% | 49% |
| combined | **100%** | 71% | 49% |

**Flag threshold = critical**

| Scorer | Recall (adversarial) | Flagged (misuse) | Fall-out (benign) |
|---|--:|--:|--:|
| static | 56% | 24% | 9% |
| combined | **81%** | 24% | **9%** |

Adversarial sessions caught **only** by the dynamic signal: 8 of 88 at high,
**22 of 88 at critical**.

Session mean band-rank (low=1 … critical=4), static → combined: adversarial
3.47 → 3.81, misuse 2.84 → 2.92, benign 2.41 → 2.41.

Ten servers, per-server table in the source; n benign ranges 86–498, n
adversarial 4–20.

**The headline is the critical row: +25 points of recall at unchanged 9%
benign fall-out.** The three-way benign / misuse / adversarial split is by
construction — misuse is accidental-insider behaviour, expected to sit between
the other two, and it does (2.84 vs 2.41 and 3.47).

## 5. Real-traffic validation

Source: `reports/dynamic_eval/REAL_DATA_VALIDATION.md`

Everything in §4 is synthetic. This validates calibration and the featurizer on
genuinely real MCP traffic.

- Live `uvx mcp-server-git` over stdio against this repository (**223 real
  commits**), driven by `scripts/capture_real_git_mcp.py`.
- **400 real tool calls**, 399/400 executed OK, **12 git tools** exercised,
  **106 distinct call signatures**. Arguments drawn from real history — real
  40-char SHAs, real paths, real branch names.
- Fit on the first 70% chronologically, scored the held-out 30%.
- **Benign false-positive rate 0.8%** (target 1–2%); mean held-out likelihood
  0.107 — essentially everything sits on the 0.1 floor as intended.
- The q99 quantile-anchored ramp, tuned on the synthetic calendar/github/slack
  corpus, **transferred to real git traffic with no adjustment**.
- Three injected clearly-anomalous calls (200-char commit message, bare
  `git_reset`, fake `exfiltrate_all` with a payload) all score high.

Why no external benchmark: graded per-action severity ground truth for this
task barely exists (`reports/severity_eval/SUMMARY.md`).

## 6. The evaluation setting — what is real, what is synthesized

**Real:** the tool catalogs, captured from live vendor MCP servers via
`tools/list` — calendar 13 tools, github 26, slack 16. The git corpus in §5 is
real execution against a real repository.

**Synthesized:** the organizational policies (`docs/mcp-tools/server-policies.md`,
written against `docs/standards/mcp-policy-spec.md`), the asset registers, and
the invocation scenarios (`scripts/make_dynamic_testbed.py`,
`scripts/make_insider_testbed.py`).

Say this precisely. It is an **evaluation setting**, not a benchmark.

## 7. What is NOT measured — do not claim these

- **Scalability versus manual assessment.** No measurement exists. Do not claim
  the framework is faster or cheaper than human review.
- **The LLM judge** (`dynamic/judge.py`) is wired but was **not run** in the
  testbed report — it needs a GPU job.
- **The rules→LLM hand-off** never fired on this corpus (§3). Unit tests only.
- **External benchmark comparison** for the dynamic task — none exists.
- **Live third-party servers.** GitHub / Slack / Calendar tokens are expired;
  the vendor catalogs are real captures but the servers were not driven live.
- **Cross-organization generalization.** One policy document, three servers.

## 8. Citation policy for this paper

`refs.bib` holds 37 entries in nine strands (A–I). `refs-full.bib` holds the
77-entry corpus; pull an entry across if a section needs it, and never invent a
key. Every factual sentence must rest on one of:

1. a number from this file, or
2. a `\cite` to a key that exists in `refs.bib`, or
3. an explicit statement that the point is this paper's own design choice.

Externally grounded design decisions that should be cited where used:

| Design decision | Keys (all present in `refs.bib`) |
|---|---|
| The 3/4 impact boundary — limited vs ordinary write | `dusseault2010patch` (RFC 5789), `fielding2022http` (RFC 9110), `first2023cvss4` (CVSS v4.0) |
| Classify-then-map sensitivity from policy | `nist2004fips199`, `nist2008sp80060` |
| Risk value conditioning an authorization decision | `cheng2007fuzzymls`, `kandala2011radac`, `atlam2020riskbased` |
| Identity cannot separate good calls from bad | `huang2026caller`, `mellafe2026capability` |
| Graded beats binary for operator action | `cao2024mad` |

`refs.bib` now holds **40** entries.
