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

Source: `docs/project/dynamic-layer-formula.md`, `docs/project/dynamic-layer-design.md`,
`src/mcp_security/dynamic/`

Static answers "how bad if this happens". Dynamic answers "how usual is this
action for this deployment, and is this call unusually large here".

```
rho(c) = min(125, max(cell(t, r) x lik(c) x esc(c), floor(t, r)))
```

| factor | range | source |
|---|---|---|
| `cell(t, r)` = sensitivity x blast x impact | 1 … 125 | the scan, design time |
| `lik(c)` — share of this deployment's traffic, as surprisal | **0.10 … 1.00** | observed history |
| `esc(c)` — Tukey bin over this deployment's argument history | **0.9 / 1.0 / 1.3** | observed history |
| `floor(t, r)` — lower bound of the **pre-change** band | 0 / 17 / 50 / 100 | the scan's bands |

**Likelihood**, keyed **(deployment, tool)** — not the resource (already in the
cell), not the individual agent (no agent in the corpora spans more than a
single day, median **32 calls**, so per-agent history never accumulates):

```
p   = (k_t + alpha * prior[t]) / (n + alpha)          alpha = 30
lik = 0.10 + 0.90 * clamp(log2(1/p) / log2(n + V), 0, 1)
```

The catalog prior removes cold start; a few dozen observed calls are enough for
evidence to dominate. Three cases return **lik = 1.0**: tool never seen,
deployment too new to judge, resource unresolved.

**Escalation** — Tukey's fences `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` over values this
deployment has passed for that argument; **1.5** leaves ~**0.7 %** of
well-behaved values outside. Quantities only (array lengths, numerics with a
design-time `critical_trigger`), never identifiers. Below **20** observations
the factor returns 1.0.

**Floor** — absolute score, taken from the band the cell was in *before*
anything moved it, so escalation raising a call cannot raise the floor beneath
it. The runtime reorders inside a band and may promote; it never demotes out of
a band.

**Paper worked example** (`main.tex` §4.3, from `dynamic-layer-formula.md`):
n = 183, k_t = 17, V = 16, prior 0.01613, cell 27 (medium) → p = 0.0821,
lik = 0.525 ≈ **0.53**, 27 x 0.53 = **14.2**, floor 17 binds → reported **17,
medium**.

Dropped from the earlier design, and no longer claimed in the paper: the
embedding likelihood, the behavioral-baseline and session-sequence band
signals, the optional LLM judge, and runtime egress / blast movement (no
predicate survived; unconditional movement manufactured false alarms). Session
context `x` is observable and is **not** consumed by this composition.

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

**Superseded composition.** §4 and §5 measure the four-signal layer described in
the old §2 (embedding likelihood + band signals), not the `lik x esc` layer the
paper now specifies. Do not quote these numbers for the current dynamic layer;
current measurements live in `reports/experiments/dynamic_layer/RESULTS.md`.

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
- **The rules→LLM hand-off** never fired on the §3 corpus. Unit tests only
  there. It *does* fire on the §9 corpus (50 of 262 tools) — the two statements
  are about different arms and must not be merged.
- **External benchmark comparison** for the dynamic task — none exists.
- **Cross-organization generalization.** One policy document, all deployments.
- **§9 has no oracle.** Nothing in §9 measures correctness: no held-out
  severity table, no baseline, no ablation, no detection result over the live
  traffic. §9 numbers describe an output only.

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

## 9. Descriptive corpus — v5r `nacombo` arm (Section 5)

Source of record:
`reports/experiments/v5/five_level_v2_policy_v5r_nacombo/` — `CORPUS_RESULTS.md`,
`README.md`, `live_run.md`, `live_scale_run.md`, and the per-server
`<server>.json` / `<server>_matrix.csv` pairs. Counts below were recomputed
directly from the matrices and the `tool_impact_source` maps; band counts,
tool/resource/cell counts and the per-server maxima agree with
`CORPUS_RESULTS.md` for the ten servers it tabulates.

Arm options: `asset_flags=none`, `blast_prompt=scope`, `floors=none`,
`relevance=combo`. Sensitivity source `llm_policy_class`, derived from
`docs/mcp-tools/server-policies.md` alone. Band thresholds: medium 17, high 50,
critical 100, on the 1–125 range.

### Corpus size

**16 server deployments** over **9 distinct tool catalogs** (the GitHub, Slack
and calendar catalogs are each deployed under two organizations; the filesystem
catalog under five tenants). **262 tools**, **221 register resources**,
**3,615** (tool, resource) cells. **1,182 scored (33%)**, **2,433 N/A (67%)**.
Bands over the scored cells: **444 low, 458 medium, 242 high, 38 critical**.
High+critical = 280 = 24% of scored cells, 7.7% of all cells. **8** cells reach
the maximum of 125.

| Kind | Deployment | Tools | Res. | Cells | Scored | N/A | low | med | high | crit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Filesystem | `fs_fintech_fs` | 14 | 18 | 252 | 103 | 149 | 39 | 36 | 24 | 4 |
| Filesystem | `fs_medical_clinic_fs` | 14 | 16 | 224 | 86 | 138 | 27 | 37 | 22 | 0 |
| Filesystem | `fs_corp_filesystem` | 14 | 16 | 224 | 87 | 137 | 36 | 26 | 21 | 4 |
| Filesystem | `fs_law_firm_fs` | 14 | 15 | 210 | 89 | 121 | 33 | 43 | 13 | 0 |
| Filesystem | `fs_media_studio_fs` | 14 | 16 | 224 | 111 | 113 | 63 | 36 | 12 | 0 |
| Source repo | `github_real` | 26 | 20 | 520 | 139 | 381 | 39 | 48 | 52 | 0 |
| Source repo | `github_helios` | 26 | 19 | 494 | 126 | 368 | 29 | 46 | 47 | 4 |
| Chat | `slack_real` | 16 | 20 | 320 | 101 | 219 | 37 | 48 | 6 | 10 |
| Chat | `slack_vireo` | 16 | 15 | 240 | 62 | 178 | 18 | 38 | 5 | 1 |
| Calendar | `calendar_real` | 13 | 16 | 208 | 68 | 140 | 22 | 27 | 14 | 5 |
| Calendar | `calendar_aurora` | 13 | 17 | 221 | 71 | 150 | 14 | 33 | 18 | 6 |
| SQL | `sqlite_cbg_sqlite` | 5 | 11 | 55 | 37 | 18 | 13 | 13 | 7 | 4 |
| Public data | `finance_tools` | 17 | 6 | 102 | 27 | 75 | 18 | 9 | 0 | 0 |
| Public data | `openbb` | 30 | 5 | 150 | 36 | 114 | 23 | 12 | 1 | 0 |
| Public data | `sec_edgar` | 21 | 6 | 126 | 27 | 99 | 24 | 3 | 0 | 0 |
| Public data | `yahoo_finance` | 9 | 5 | 45 | 12 | 33 | 9 | 3 | 0 | 0 |
| **Total** | **16** | **262** | **221** | **3,615** | **1,182** | **2,433** | **444** | **458** | **242** | **38** |

### Impact provenance

Per **distinct catalog** (151 distinct tools): ladder **127 (84%)**, model
**24 (16%)**. Per **deployment** (262 tools, repeated catalogs counted once per
organization): ladder **212**, model **50**.

| Catalog | Tools | Ladder | Model |
|---|---:|---:|---:|
| `filesystem` | 14 | 12 | 2 |
| `github` | 26 | 15 | 11 |
| `slack` | 16 | 13 | 3 |
| `calendar` | 13 | 9 | 4 |
| `sqlite` | 5 | 4 | 1 |
| `finance-tools` | 17 | 17 | 0 |
| `openbb` | 30 | 27 | 3 |
| `sec-edgar` | 21 | 21 | 0 |
| `yahoo-finance` | 9 | 9 | 0 |
| **Total** | **151** | **127** | **24** |

### Highest-scoring cell per deployment

| Deployment | Tool × resource | sens·blast·impact | Score |
|---|---|---|---:|
| `fs_fintech_fs` | `write_file` × `card-vault` | 5·5·4 | 100 |
| `fs_corp_filesystem` | `write_file` × `security-keys` | 5·5·4 | 100 |
| `fs_medical_clinic_fs` | `write_file` × `patient-charts` | 5·4·4 | 80 |
| `fs_law_firm_fs` | `write_file` × `matter-files` | 5·4·4 | 80 |
| `fs_media_studio_fs` | `write_file` × `unreleased-imagery` | 4·4·4 | 64 |
| `github_helios` | `push_files` × `helios-scada-gateway` | 5·5·4 | 100 |
| `github_real` | `fork_repository` × `infra-config` | 4·5·4 | 80 |
| `slack_real` | `conversations_leave` × `incident-response` | 5·5·5 | 125 |
| `slack_vireo` | `usergroups_users_update` × `usergroup-membership` | 4·5·5 | 100 |
| `calendar_real` | `manage-accounts` × `connected-account-config` | 5·5·5 | 125 |
| `calendar_aurora` | `delete-event` × `aurora-exec` | 5·5·5 | 125 |
| `sqlite_cbg_sqlite` | `write_query` × `api_keys` | 5·5·5 | 125 |
| `finance_tools` | `calculate` × `expression-evaluator` | 4·3·3 | 36 |
| `openbb` | `install_skill` × `server-capability-install` | 4·4·4 | 64 |
| `sec_edgar` | `get_recommended_tools` × `concept-catalogs` | 3·3·3 | 27 |
| `yahoo_finance` | `get_historical_stock_prices` × `research-query-pattern` | 3·3·3 | 27 |

Public-data control: `finance_tools`, `sec_edgar` and `yahoo_finance` produce
**0 high and 0 critical** cells across their **273** cells. The only high cell
in the public-data group is `openbb`'s `install_skill` × `server-capability-install`
at 64; the ladder abstained on that verb and the model assigned impact 4.

`conversations_leave` × `incident-response` = 125 comes from `llm_fallback`
impact 5, sensitivity 5 (`self-sufficient` flag), blast 5. The operation
removes the agent's own channel access. Reported as produced, not patched.

### Live traffic

Pilot (`live_run.md`): **98 live calls**, **93 OK / 5 ERROR**, 52 benign /
21 misuse / 25 malicious.

Scaled (`live_scale_run.md`): **3,000 live calls**, **2,998 OK / 2 ERROR**,
exact 50/25/25 per org. The two errors are transient Google Calendar
`operation was aborted` responses.

| Deployment | Calls | B/M/A | Tools live | OK |
|---|---:|---|---:|---:|
| `github_helios` | 1,000 | 500/250/250 | 24 of 26 | 1,000 |
| `slack_vireo` | 1,000 | 500/250/250 | 12 of 16 | 1,000 |
| `calendar_aurora` | 1,000 | 500/250/250 | 12 of 13 | 998 |
| **Total** | **3,000** | 1,500/750/750 | 48 | **2,998** |

Attack caps per run: ≤8 merges, ≤8 repo creates, ≤5 unblinding posts. Cleanup
created-then-removed: **92** files on perimeter `main`, **80** branches,
**39** issues, **5** PRs, **8** repositories; post-run residue audit **0** on
every category. **5** verbs cannot execute live on these deployments
(`fork_repository`; `usergroups_create` / `usergroups_update` /
`usergroups_users_update`; `respond-to-event`) and are recorded as ERROR.

Category labels are assigned by the generator against each server's policy
section — **not** an independent annotation. No detection result is reported
over this traffic in this arm.

### The one failure

`maverick` (119 tools) aborted the model server on its first call — CUDA
flash-attention kernel abort (`launch_fattn` → `ggml_abort`) at that prompt
length with a quantised KV cache. Excluded from every number above.
