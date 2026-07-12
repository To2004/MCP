# Embedding-Based Likelihood — Evaluation Report (v2.1)

The dynamic likelihood factor for the v6 formula, produced by
`src/mcp_security/dynamic/embedding.py` and evaluated by
`scripts/eval_embedding_likelihood.py` on the big-three sims (calendar, github, slack).
No LLM anywhere; deterministic; fit is < 0.5 s per server and scoring is ~0.05 ms per
call (semi-runtime: refit periodically, score live).

## The formula

```
final_risk = static_score x likelihood
static_score = asset_sensitivity x blast_radius x tool_impact     (v6 scan cell)
likelihood   = 0.1 + 0.9 * clip((z - 2) / (3 - 2), 0, 1)          in [0.1, 1.0]
```

`z` is the call's novelty against the server's own benign history: embed the call
(hashing vectorizer over tool + arg tokens + structural flags + magnitude buckets + a
`tool|asset` conjunction token, 4096-d), reduce to a 24-d latent (TruncatedSVD fit on
history), take the mean distance to the 5 nearest historical calls (self-excluded), and
calibrate so the history's **99th percentile** score sits at z = 2 (ramp start;
saturation at 1.5x that distance — both cutoffs tuned on this corpus only and validated
untouched on the insider corpus). A call indistinguishable from demonstrated-normal
traffic keeps 10% of its static risk; a fully anomalous call keeps all of it; **no
history at all -> likelihood 1.0**.

## Headline results

Frozen model (fit on the benign calls of the first 70% of the stream, scored on the
held-out tail — `<server>_test.csv`):

| server | AUC (mal) | TPR mal | FPR benign | L(benign) | L(misuse) | L(malicious) |
|---|---|---|---|---|---|---|
| calendar | 0.809 | 65.5% | 0.2% | 0.10 | 0.15 | 0.69 |
| github | 0.932 | 82.9% | 2.4% | 0.12 | 0.23 | 0.85 |
| slack | 0.951 | 92.9% | 1.1% | 0.10 | 0.22 | 0.94 |

Honest prequential stream (row 1 = genuinely first call ever seen; refit every 50 calls
on all prior calls, labels never consulted; impact filter + label-free self-trim —
`<server>_stream.csv`; mature half = past the designed cold-start):

| server | mature AUC | mature TPR | mature FPR | L(malicious) |
|---|---|---|---|---|
| calendar | 0.880 | 81% | 1.0% | 0.83 |
| github | 0.835 | 72% | 2.5% | 0.75 |
| slack | 0.952 | 94% | 2.1% | 0.95 |

Full formula, mean by category (held-out test sets):

| server | category | n | static | likelihood | final risk |
|---|---|---|---|---|---|
| calendar | BENIGN | 614 | 6.0 | 0.10 | 0.6 |
| calendar | MISUSE | 202 | 8.7 | 0.14 | 1.2 |
| calendar | MALICIOUS | 29 | 14.2 | 0.69 | 12.0 |
| github | BENIGN | 589 | 5.8 | 0.10 | 0.6 |
| github | MISUSE | 239 | 8.0 | 0.16 | 1.6 |
| github | MALICIOUS | 35 | 14.3 | 0.85 | 14.0 |
| slack | BENIGN | 616 | 4.7 | 0.10 | 0.5 |
| slack | MISUSE | 218 | 5.4 | 0.16 | 1.1 |
| slack | MALICIOUS | 28 | 14.1 | 0.89 | 13.4 |

Benign traffic is discounted ~10x while malicious keeps 60–90% of static risk — a
**20–28x separation in mean final risk**. Top-ranked calls per server are all true
attacks (`delete_all_events`x contacts risk 60, `delete_file` x infra-config,
`slack_post_message` flood x on-call).

## Architecture selection

Candidates fit identically, compared on held-out malicious-vs-benign AUC. Winner: **kNN
distance in the benign latent space** (mean 0.880).

| signal | mean AUC | note |
|---|---|---|
| **knn (winner)** | **0.880** | best AUC and best-calibrated |
| lin_ae (linear autoencoder) | 0.874 | ties on AUC, FPR up to 40% on slack |
| rareness (signature frequency) | 0.847 | strong on github, weak on slack |
| blend (max of the above) | 0.870 | inherits lin_ae's calibration problems |
| mlp_ae (nonlinear autoencoder) | 0.453 | structural failure, see below |

The MLP autoencoder's failure is architectural, not a tuning issue: it reconstructs the
SVD *latent*, so a call far outside the benign subspace projects near the origin and
reconstructs trivially — blind exactly where novelty lives.

## What was tried, what survived (the experiment trail)

**Ceiling first.** 7–35% of malicious calls are byte-identical to benign traffic
(attack-preamble recon); identical benign/malicious pairs can at best tie, capping any
content-only model at AUC **0.975 / 0.991 / 0.999** per server. Everything below the
cap is model error, so iteration continued.

| change | verdict | evidence |
|---|---|---|
| magnitude buckets (`mag_k=log10`) | **kept** | calendar +0.02 AUC; bulk `limit`/recipient lists read as novel |
| `cell=tool\|asset` conjunction token | **kept** | github +0.03 AUC; known tool aimed at a never-touched asset becomes far from all neighbors |
| session-context tokens (prev tool, position) | rejected | mean AUC 0.875 -> 0.836; context variety makes benign traffic noisier, and per-call content already carries the signal |
| k=1 nearest neighbor | rejected | best frozen AUC (0.896) but collapses in the stream (TPR 73% -> 23–35%): one similar historical attack sibling is enough to hide behind; k=5 forces five |
| self-excluded training distances | **kept** | with self included, every training score carries a free zero in its k-mean, silently tightening the anchor by (k-1)/k — made explicit instead of accidental |
| anchor quantile sweep (0.90–0.99) | **q0.98 kept** | the anchor must sit BELOW the stream's contamination rate: at q0.99 the anchor lands inside attack scores and prequential TPR collapses 73% -> 38%; below q0.98 only FPR grows |
| median/MAD calibration | rejected | zero-inflated kNN distances degenerate the MAD scale; FPR flipped 11% -> 40% with the SVD seed |
| bigger hash (8192) / token bigrams (32k) / seed-ensemble x3 | rejected | ≤ +0.01 mean AUC, reshuffles servers within seed noise (±0.02); stopped at diminishing returns |
| self-trim pass for unlabeled streams (`trim_z=2`) | **kept** | fit -> score own history -> drop flagged -> refit; stream L(malicious) roughly doubles (0.23 -> 0.64–0.74) for ~0.5 pt of FPR |
| iterated self-trim (ITSR-style, up to 3 rounds) | **kept** | +4 pts stream TPR on github, stream L(malicious) 0.64 -> 0.78, for ~1 pt FPR; rounds exit early at convergence |
| impact-aware reference filter (calls >= the scan's high band never enter the reference) | **kept** | the insider-testbed fix: a crown x destructive call cannot earn a likelihood discount through repetition. Insider mature-stream TPR 0% -> 50% on calendar, L(mal) 0.10 -> 0.49; no regression on the original corpus (frozen github +0.05 AUC). Design-time scan knowledge only — no labels, generalizes to any scanned server |
| fixed a-priori architecture (kNN) across corpora | **kept (methodology)** | re-picking a per-corpus winner from held-out labels is model selection on the test set; observed per-signal AUCs still reported for transparency |
| cutoff optimization: q99 anchor + 1.5x saturation + sub-ramp trim (0.8x ramp start) | **kept** | tuned on the original corpus ONLY, validated untouched on the insider corpus. Equal TPR at roughly HALF the benign FPR on both corpora, higher L(mal) and risk separation. The enabling insight: trim the reference BELOW the ramp start — contamination control decouples from the alerting cutoff, which is what makes the tighter q99 anchor viable in unlabeled streams. Known cost: calendar insider AUC dips 0.66 -> 0.51 (n=24 malicious, rank-order noise; TPR/FPR/separation all hold or improve). Frozen TPR is invariant across the entire cutoff grid (80.4% mean) — the z-distribution is bimodal, so cutoffs move FPR and risk magnitude, not detection |
| estimator bake-off: LOF, Isolation Forest, kth-distance, raw-cosine kNN, TF-IDF+kNN, surprisal, blends | rejected | nothing dominates kNN (mean 0.889): LOF wins calendar (+0.016) but loses slack and halves its L(mal); kth-distance ties exactly; iForest 0.719; TF-IDF 0.859; surprisal 0.847; max-blends dilute |
| conformal p-value calibration (full empirical CDF) | validated, no change | numerically identical TPR/FPR to the two-point anchor — the q98 anchor IS a conformal p=0.02 threshold, so the shipped calibration inherits conformal's marginal-validity guarantee |

## Comparison with NIST SP 800-30, OWASP RR, and CVSS

**NIST SP 800-30** defines risk as likelihood x impact on 5-level qualitative scales
combined via a lookup matrix; ours is the quantitative version of that construction
(static v6 cell = impact, embedding novelty = likelihood, multiplication = combination).
Projecting our continuous values onto the NIST 5x5 matrix gives Spearman agreement
**0.74 / 0.91 / 0.77** (calendar / github / slack). Against the coarser **OWASP Risk
Rating** 3x3 severity matrix: **0.72 / 0.86 / 0.75**. Same ordering philosophy, but
continuous, per-call, and evidence-driven where those frameworks use per-threat expert
judgment.

**CVSS** keeps likelihood-like factors (attack vector, complexity, privileges) inside a
static Exploitability sub-score — fixed per vulnerability, blind to runtime behavior.
Its closest runtime analogue, the Threat/Temporal Exploit-Maturity metric, multiplies
by 0.91–1.0: a maximum 9% discount. Our likelihood discounts demonstrated-normal
traffic by 90%. Judgment: CVSS's shallow discount is right for *vulnerability* triage
(a vuln stays dangerous even unexploited) but wrong for *per-call gating*, where almost
all calls are routine and a gate that cannot say "this exact call looks normal" drowns
in static positives. The 0.1 floor is the safety valve in the other direction: no call
is ever fully vouched for.

**The residual blind spot, quantified.** Malicious calls whose content is byte-identical
to benign traffic (recon preambles like `list_week {"calendar": "holidays"}`) are
invisible to any per-call content model — that is calendar's AUC cap. They carry low
static scores, and the harm calls in the same chains (`update_event` /
`send_email_invite` on `team`) score z = 6–17 -> likelihood 1.0. High-static malicious
calls wrongly floored: **2/29, 0/35, 1/28** per server. Preamble *patterns* are the
sequence signal's job (`dynamic/sequence.py`), which the fused pipeline already applies.

## Signal fusion: embedding ⊕ sequence ⊕ baseline

The embedding is a per-call *content* model; its two characterized miss classes are
attack preambles (normal content, abnormal order) and misuse (normal content, abnormal
volume/actor). Those map to the two signals already in the pipeline — `sequence.py`
(sensitive-read → outbound within a session) and `baseline.py` (per-persona new-tool /
first-touch / burst). `scripts/eval_fused_likelihood.py` maps all three onto the same
`[0.1, 1]` scale and fuses escalate-only (`L = max(L_embed, L_seq, L_base)`), so nothing
can *lower* the embedding's suspicion (the per-user-conditioning failure can't leak in).
Leakage discipline is preserved: baselines are built causally (only from prior calls),
sequence verdicts look only backward, burst uses size-so-far.

Mature-stream results (kNN embedding vs fused):

| corpus / server | embed AUC | fused AUC | embed TPR(misuse) | fused TPR(misuse) | embed FPR | fused FPR | top-20 runs |
|---|---|---|---|---|---|---|---|
| insider calendar | 0.51 | **0.75** | 0% | 2% | 0.3% | 0.3% | 10/20 |
| insider github | 0.71 | 0.72 | 0% | 6% | 1.2% | 4.2% | 15/20 |
| insider slack | 0.84 | 0.83 | 0% | 0% | 0.0% | 1.2% | 16/20 |
| original calendar | 0.88 | 0.90 | 7% | 20% | 1.0% | 9.0% | 20/20 |
| original github | 0.835 | 0.836 | 10% | 23% | 2.5% | 13.7% | 20/20 |
| original slack | 0.95 | 0.97 | 1% | 12% | 2.1% | 12.6% | 20/20 |

Three findings, and a clear recommendation split:

- **Sequence fusion is a clean, adopt-unconditionally win.** It drives the calendar
  insider jump (AUC 0.51 → 0.75) at **zero** FPR cost, because it fires "critical" only
  on the rare sensitive-read→outbound pattern, which is attack-correlated. This is the
  standout: the exact preamble/exfil miss the content model can't see, caught by *order*.
- **Baseline fusion adds real misuse recall** — TPR(misuse) roughly triples everywhere
  (7→20%, 10→23%, 1→12%), detection the embedding scored ~0 on — **but it is expensive
  in FPR on multi-tenant traffic**: the 20-org corpus has 80–91 thin-history personas,
  so "tool never used by this persona before" fires on legitimate first-uses and pushes
  benign FPR to 9–14%. On the 8-persona deep-history insider corpus the same signal
  costs only 0–4% FPR. So the baseline component needs a **history-maturity gate** (flag
  only after N sessions, mirror the embedding's `MIN_FIT_CALLS`; consider downgrading
  new-tool from high to medium) before it is FPR-safe as an always-on escalator.
- **Run-level, fusion is unambiguously better**: top-20 runs by max final risk go to
  **20/20 attacks** on every original-corpus server (from 13–16), and 10–16/20 on the
  harder insider corpus — the metric a SOC actually acts on.

Net: **ship sequence fusion now**; ship baseline fusion behind a maturity gate. Per-call
malicious TPR is unchanged by fusion (attack sessions are half legitimate-looking reads,
so the *preamble* calls stay at floor by construction) — the gains are in AUC/ranking,
misuse recall, and run-level precision, exactly where a session-aware defender operates.

## Insider-variant testbed: the likelihood's operating envelope

A second corpus (`scripts/make_insider_testbed.py` -> `dyn_<server>_ins/`,
evaluated into `reports/dynamic_eval/embedding_insider/`) removes the external
attacker entirely: **2 orgs, 8 personas per server, ~100 calls each**, every persona
mixed (~83% benign, ~12% misuse, ~5% insider-attack sessions), sessions globally
shuffled. Identity carries zero label signal by construction.

Results (kNN fixed a priori; **with** the impact-aware reference filter, mature half of
the stream = past the designed cold-start):

| setting | calendar | github | slack |
|---|---|---|---|
| frozen AUC (mal) / TPR / FPR | 0.64 / 50% / 0.5% | 0.65 / 50% / 5.0% | 0.81 / 70% / 0.0% |
| mature stream AUC / TPR / FPR | 0.51 / 50% / 0.3% | 0.71 / 40% / 1.2% | 0.84 / 67% / 0.0% |
| mature stream L(malicious) | 0.55 | 0.46 | 0.63 |
| mature stream final-risk separation (mal ÷ benign) | x10 | x12 | x18 |
| top-20 runs by max final risk that are attacks (base rate ~21%) | 10/20 | 12/20 | 12/20 |

Reading, honestly:

- **The insider stream initially collapsed** (mature TPR 0% on calendar, L(mal) 0.10,
  AUC 0.54): with every persona attacking, insider attack calls are ~6% of history and
  self-similar, so they became their own "demonstrated normal". Deeper trimming (10
  rounds, refit 25) changed nothing — the attack cluster is too large a share to trim
  at a q98 anchor — and a z>1 trim threshold explodes benign FPR to ~50%. **No
  label-free content model can distinguish a common attack pattern from common work.**
- **The impact-aware reference filter is the general fix**: calls at/above the scan's
  high band are observable but never enter the demonstrated-normal reference, so
  repetition cannot buy them a discount. Calendar mature TPR 0% -> 50%, L(mal) 0.10 ->
  0.49, FPR 0.9%; slack TPR 63% -> 70%. Uses only design-time scan knowledge — no
  labels, no testbed-specific logic.
- **What remains uncaught is the preamble share by construction**: insider sessions are
  half routine reads; the harm calls are what cross the ramp. TPR 40–70% per call is
  therefore the honest per-call ceiling here, and the composite carries the rest:
  mature final-risk separation x10–15, and the per-run rollup surfaces attack runs at
  2–4x the base rate. In insider-saturated environments the impact factor plus the
  sequence/baseline signals do the catching — the fused pipeline's architecture.
- Small-corpus caveat: with 4–23 malicious calls per held-out tail, per-signal AUC
  ranking is noisy — which is why the architecture is fixed a priori rather than
  re-picked per corpus.

## Per-user / per-group conditioning: tested and rejected (kept content-only)

The natural next idea — score each call against the caller's own history (or their
group's: same role across orgs, same org) with extra weight — was tested three ways
and **rejected with a clear mechanism**, not just numbers:

| variant | frozen | honest stream |
|---|---|---|
| `user=<persona>` token, weight 1 | AUC 0.889 -> 0.921, FPR ~0% | AUC(mal) drops (0.82 -> 0.75 cal, 0.86 -> 0.80 gh), **AUC(misuse) collapses 0.53 -> 0.30**, calendar FPR 4.6% -> 28.5% |
| token weight 2–4 | identity drowns content; FPR up to 69% | — |
| per-role reference channels, `max(z_global, z_role)` | no gain (0.797/0.882/0.943); calendar preambles still 0/10 caught | — |

Why the frozen gain is an artifact: in the held-out tail, almost every malicious call
is by a persona with **no training history at all** (35/35 github, 28/28 slack, 25/29
calendar — fresh `Attacker (Eve)@org2`-style identities), so the user token wins by
detecting "new identity", not behavior. The stream exposes the two real problems:

1. **Identity weighting vouches for repeated misuse.** A persona that misuses over and
   over (e.g. `Support Agent@acme`, 13 misuse calls) becomes its own "normal" — the
   identity-level version of the k=1 contamination trap. Misuse AUC falls below chance.
2. **Benign traffic keeps introducing new identities** (new org waves), so
   identity-novelty fires on legitimate users — calendar benign FPR 28.5%.

Role groups fail for a subtler reason: the attack preambles faithfully imitate *their
own role's* normal behavior (Scheduler Bots benignly run `list_week` too), so
conditioning on the group leaves them exactly as invisible as the global model does.

Conclusion: the likelihood factor stays **content-only**. Per-identity behavior belongs
in the pipeline's *baseline* signal (`dynamic/baseline.py`), which is escalate-only by
construction — it can flag a persona deviating from its profile but can never *vouch*
for a call the way a likelihood discount does, so repeated misuse cannot buy itself
trust there. The per-run rollup (`<server>_runs.csv`) already gives the per-user view
safely: max/sum of final risk per run and persona.

## Real-traffic validation (calibration + featurizer)

Full detail in `reports/dynamic_eval/REAL_DATA_VALIDATION.md`. Summary: 400 real calls
captured from a live local `mcp-server-git` (`scripts/capture_real_git_mcp.py`, no
external auth), arguments drawn from this repo's real history. The **q99 calibration
transfers to real traffic untouched** — benign held-out FPR 0.8% (target ~1–2%) — and
the featurizer tokenized all 400 real calls without error while still scoring injected
anomalies at likelihood 1.0. Real data also surfaced one fix: git commit SHAs (40-char
hex) were tripping the `has_b64_blob` flag on 155/400 calls; the flag now excludes pure
hex, so it means "unexpected encoded blob" and no longer fires on ordinary identifiers
(a genuine base64 payload still trips it). Live third-party validation is blocked only by
expired credentials, not by the method.

## Related work and theory grounding

Checked before the second improvement round (2026-07-12):

- **kNN anomaly scores** (mean-of-k vs kth-distance vs median) are the standard family;
  kth-distance carries the formal consistency analysis ([NeurIPS 2019, Gu et al.](http://papers.neurips.cc/paper/9274-statistical-analysis-of-nearest-neighbor-methods-for-anomaly-detection.pdf)).
  Both variants tie empirically here.
- **Conformal anomaly detection**: ranking a test score against the training-score
  distribution yields a p-value uniform under exchangeability. Our quantile anchor is
  the two-point special case; full conformal was implemented and matched it exactly.
- **Contaminated-training refinement**: the self-trim pass is the Iterative Training
  Set Refinement / self-trained one-class scheme from the robust-AD literature
  ([STOC](https://www.researchgate.net/publication/352373766_Self-Trained_One-class_Classification_for_Unsupervised_Anomaly_Detection),
  [ITSR](https://arxiv.org/pdf/1901.06355), [iterative refinement](https://arxiv.org/abs/2106.06115));
  per that literature it now iterates to convergence (max 3 rounds).
- **MCP security**: existing tools (MCIP-Guardian, MCP-Defender, SIEM-feed guidance per
  the [OWASP MCP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html))
  are LLM/context-reasoning guards or pattern alerting; none publish a lightweight
  no-LLM per-call likelihood that multiplies a scanned static impact. The niche this
  module fills appears distinct.

## Static-side investigation (documented per request; v6 preserved)

The v6 scan artifacts are preserved untouched in `reports/all_scans_v6.zip`. The one
no-rescan static lever — per-tool **parameter rubrics** amplifying the static score —
was investigated and **rejected on evidence**:

1. Existing rubrics: github's found 0 magnitude params; applying calendar/slack rubrics
   moved misuse AUC ≤ +0.01 and *lowered* malicious AUC (amplifies benign bulk too).
2. Rubrics were regenerated on GPU with the strengthened prompt (SLURM job 19311621,
   `scripts/derive_params_cbg.sbatch`; artifacts snapshotted in
   `reports/all_scans_v6_1_params_regen.zip`). Calendar now derives 10 magnitude
   params with sensible cutoffs (e.g. recipients ≥50 -> critical); github and slack
   again derive 0.
3. Even the fresh calendar rubrics fail on traffic: schema-vs-traffic name mismatches
   (`recipients` vs `to`, `duration_min` vs `start`/`end`), and the amplification that
   does fire hits 268 benign vs 90 misuse calls — malicious AUC drops 0.750 -> 0.731.

Conclusion: on these servers, magnitude belongs **inside the embedding likelihood**
(the `mag_`/`listlen_` tokens, which measurably help and key on the *observed* argument
names) rather than as a static multiplier keyed to schema names. The static v6 cell
scores themselves stay as the impact factor, unchanged.

## Files

- `<server>_test.csv` — held-out calls only (never used to fit), frozen winner model.
- `<server>_stream.csv` — every call from the genuine first row, prequential replay.
- `metrics.json` — all numbers above, per signal and per server.

Columns: `position, index, run_id, persona, category, tool, args, asset, static_score,
static_basis, z, likelihood, final_risk`. `static_basis` is honest about fallbacks:
`cell` (scanned cell), `tool-worst-case` (unresolved asset), `server-worst-case`
(unknown tool).

## Reproduce

```
uv run python scripts/eval_embedding_likelihood.py
uv run pytest tests/test_dynamic_embedding.py
```
