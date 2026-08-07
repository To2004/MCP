# Agent judge panel — ranking the blast-radius experiments

Four Claude judge agents with distinct personas independently reviewed the
experiment artifacts (`blast_experiments_comparison.md`, the floor/rowfix
outputs and change logs, the ctx prompts) and ranked the four candidates:
`ctx`, `floor-plain`, `floor-gated`, `rowfix`. Each judge verified claims
against the files; none saw another judge's verdict.

## Scoreboard

| candidate | Raven (red-team) | Moss (SOC) | Marchetti (methodology) | Halvorsen (audit) | mean |
|---|---|---|---|---|---|
| **floor-gated** | 7 | 8 | 6 | 9 | **7.50** |
| floor-plain | 9 | 4 | 4 | 8 | 6.25 |
| rowfix | 5 | 6.5 | 7 | 5 | 5.88 |
| ctx | 3 | 3 | 3 | 2 | 2.75 |

First-place votes: floor-gated 2 (Moss, Halvorsen), floor-plain 1 (Raven),
rowfix 1 (Marchetti). ctx ranked last on all four cards.

## Where the panel agrees

- **ctx last, unanimously**: missed the flagship delete-event cell after a full
  re-scan, non-deterministic (cells drifted, dropped, or went N/A on unchanged
  inputs), worst workload-per-fix. Its value is the *finding*, not the fix: the
  model's own profile proves comprehension was never the problem — the coverage
  rubric is.
- **floor-gated is the only candidate never ranked below 2nd**: full offender
  coverage, deterministic, one-sentence rule, no recon inflation.
- **rowfix has the best audit trail and the best experimental design**, and is
  the only candidate that also de-escalates over-scored cells — but 19/51
  coverage and unmeasured rerun stability keep it from winning outright.

## Where the panel splits (and why)

- **plain vs gated** hinges on one question: should reads/listings on crown-jewel
  assets be floored too? Raven says yes (reading/enumerating a private key IS
  the attack; gated leaves it cheap). Moss and Halvorsen say no (plain mints
  criticals out of `get-event` and `list-calendars` — recon inflation that
  trains people to rubber-stamp).
- **rules vs judgment**: Marchetti ranks rowfix first because it is the only
  *measurement* (frozen baseline, single variable, falsifiable principles,
  honest coverage) and calls the floors' 51/51 metric circular — the rule is
  graded by its own definition. Halvorsen ranks the floors first for exactly
  the same property Marchetti discounts: the guarantee is provable by
  inspection.

## Action items surfaced by the judges

1. **Raven**: sens-keyed floors are blind to destruction on low-sensitivity
   assets (`write_file` on `db_schema.sql`, sens 3 impact 5, stays 15). Add a
   raw-impact floor so an impact-5 verb cannot hide behind low sensitivity.
2. **Moss**: keep rowfix's de-escalations (it removed junk criticals like
   `conversations_history` on team-leads) even if the floor supplies the raises.
3. **Marchetti**: (a) run rowfix k times and report repair-set agreement before
   trusting it; (b) evaluate the floors against an external oracle sample, not
   the circular offender metric; (c) test transfer on a fourth, unseen server;
   (d) the durable fix is a reversibility/consequence term in the blast rubric
   itself, per ctx's negative result.
4. **Halvorsen**: record why floors 4/3 were chosen; tighten rowfix prompts so
   justifications cite cell-specific evidence, not templated principle text.

## Panel verdicts (verbatim)

---

## Raven (red-team operator)
**One-line philosophy:** A scorer earns its keep only if every delete/write/exfil path onto a juicy asset lands high enough to trip the gate — coverage beats cleverness, and I'll take paranoid over breached every time.

**Scores (0-10):** ctx: 3 | floor-plain: 9 | floor-gated: 7 | rowfix: 5

**Ranking:** 1st floor-plain, 2nd floor-gated, 3rd rowfix, 4th ctx

**Per experiment:**
- ctx — GOOD: highest raw lift of the three LLM-free-of-floors approaches on paper (27/51), and it nailed the single juiciest cell I'd actually run — `move_file` on `private_key.pem` b1→b5, 20→125 — plus `move_file payslips_q1.csv` 16→50. When it fires on exfil it fires hard. BAD: it whiffed the flagship. `delete-event` on personal/team/executive stays b1 → **20 medium** (impact-5 destruction waved through), and `write_file` on `audit_log.txt` stays **20 medium** — that's tampering with the security log, priced so a gateway lets it pass. Worse, it's a non-deterministic re-scan that *lowered* live cells (`conversations_leave research-team` b1→12, `usergroups_update usergroup-directory` 32→24) and dropped others to `na`. A scorer that randomly under-prices on re-run is a liability, not a fix.
- floor-plain — GOOD: raised all 51 offenders to high/critical, deterministic, no LLM in the loop to hallucinate a demotion. And because it keys off sensitivity for *every* cell, it also floors the non-mutating exfil reads — `list_directory`/`search_files`/`read` on a sens-5 asset get pushed to blast≥4, so listing/reading a private key finally prices high. That's an exfil path the gated variant leaves open. Blunt, and I love blunt. BAD: zero reach discrimination — a sens-5 read and a sens-5 delete both get blast≥4, which dulls the gateway's ability to rank within the danger tier. And it's blind to impact on lower-sensitivity assets (see below). Minor sins to me.
- floor-gated — GOOD: covers all 51 mutating offenders deterministically, same guaranteed floor on every create/delete/write/move onto a sens≥4 asset, with far less over-block noise than plain. BAD: gating on impact≥4 means the non-mutating exfil reads on juicy assets stay cheap — `list_directory`/`search_files` on `private_key.pem` keep baseline blast, staying low. Reading/enumerating a private key IS the attack; leaving it low is a real hole plain doesn't have.
- rowfix — GOOD: fixed the destruction class the whole exercise was about — every `delete-event` raised (recruiting all the way to b5→125), and it caught the read-side private-key enumeration (`list_directory`/`search_files` on `private_key.pem` b1→b5→50). Deterministic-ish, auditable, every change carries a justification. BAD: only 19/51 raised — it leaves 32 mutate/write paths sitting at medium. Damningly, `move_file private_key.pem` stays b1 → **20 medium**: it flagged *listing* the key but not *relocating* it, so the stronger exfil sails through. `create-event` on sens-5 `recruiting` stays **20 medium**, `write_file core.c` (impact 5 overwrite) stays **20 medium**. Too many doors left unlocked for a coverage judge.

**Cells I'd exploit that still slip through the winner (floor-plain):** The floor keys on *sensitivity only*, so impact-5 destruction on a merely medium-sensitivity asset is invisible to it. `write_file` on `projects/db_schema.sql` (sens 3, impact 5) — rowfix repaired this to 60 high, floor-plain leaves it at baseline **15 low/medium** because sens-3 gets no floor. Same story: `write_file file-records` (sens 3, impact 5) and `delete-event holidays` (sens 1, impact 5) stay low. I overwrite your schema or nuke a shared calendar of "low-sensitivity" events and the gate never blinks. Any destructive verb parked on a sens≤3 asset is my lane against floor-plain.

**Verdict:** The two floors win because they're the only candidates that don't leave a single mutating offender under-priced, and I don't lose sleep over their over-blocking — I lose sleep over the delete that got waved through. Plain edges gated because it also prices the exfil *reads* on the crown-jewel assets, which gated leaves cheap. ctx is dead last and it earned it: the one experiment specifically pointed at the delete-event bug is the one that still ships delete-event at 20 medium, then randomly demotes other live cells on top of it — that's not a fix, that's a coin flip. Bolt a raw-impact floor onto floor-plain so an impact-5 verb can't hide behind low sensitivity, and I'd actually deploy it.

---

## Moss (SOC / gateway operator)

**One-line philosophy:** Every cell you push into high/critical is a ticket on my desk — up-rank the deletes, but the day a `list-calendars` call pages me is the day my analysts start rubber-stamping approvals.

**Scores (0-10):** ctx: 3 | floor-plain: 4 | floor-gated: 8 | rowfix: 6.5

**Ranking:** 1st floor-gated, 2nd rowfix, 3rd floor-plain, 4th ctx

**Workload math (extra high+critical cells vs baseline, per experiment):**
Baseline high+critical: calendar 53 (48h+5c), slack 52 (37+15), fs 103 (81+22) = **208 total**.
- ctx: calendar 63 (+10), slack 61 (+9), fs 132 (+29) → **+48 total** (256), for only 27/51 offenders fixed = **1.78 extra cells per offender**
- floor-plain: calendar 66 (+13), slack 79 (+27), fs 133 (+30) → **+70 total** (278), 51/51 = **1.37 per offender**
- floor-gated: calendar 62 (+9), slack 66 (+14), fs 114 (+11) → **+34 total** (242), 51/51 = **0.67 per offender** — best ratio on the board
- rowfix: calendar 57 (+4), slack 63 (+11), fs 106 (+3) → **+18 total** (226), 19/51 = 0.95 per offender — cheapest absolute load, and it's the only one that also *removes* noise

**Per experiment:**
- ctx — GOOD: Some genuinely smart calls — `move_file` on `private_key.pem` b1→b5 (125) is a real threat that deserves the page; `hr-internal add_message` b1→b4 shows it can reason about context. BAD: It misses the flagship bug — calendar `delete-event` on personal/team/executive is *still* b1→20 medium after a full re-scan; that's the cell that motivated this whole exercise. Worst efficiency of the four (+48 workload for 27 fixes). Incoherent within rows: `create-event recruiting` gets b5→100 (blast 5 for creating *one* event?) while `conversations_leave` offenders all stay b1. And it's a full nondeterministic re-scan — na counts churned on every server (fs 121→100, calendar 132→123), so my diffs are garbage and next re-scan the numbers move again. Can't gate on a coin flip.
- floor-plain — GOOD: Deterministic, auditable, catches all 51 offenders, zero LLM variance. BAD: It floors *everything*, and 90 of its 144 floored cells are non-mutating. Concrete pages I refuse to take: `list-calendars` on personal/team goes 8 medium → 24 **high** (b1→b3) — that's enumeration, not damage; `get-event` on recruiting goes 15 → 60 **critical** — reading one event; `get-freebusy`/`list-events`/`search-events` on free-busy-availability all jump 45 high → 60 **critical**. All 4 new calendar criticals it mints are read tools. This is the exact recon-inflation failure mode that trains people to click approve.
- floor-gated — GOOD: Same 51/51 offender coverage as plain at half the cost (+34 vs +70), and *every* extra high cell is a mutation (impact ≥4) on a sensitive asset (sens ≥4) — `delete-event` personal/team/exec land at 60 high, recruiting at 100, exactly the fix that was ordered. The calendar CSV confirms it leaves `list-calendars`, `get-event`, `search-events` byte-identical to baseline: zero recon inflation, zero new criticals on calendar (5→5). Deterministic, one-line rule I can explain to an auditor. BAD: It's a blunt instrument — sens-4 x impact-4 always ≥48 high regardless of actual reach, so a few marginal cells (e.g., `usergroups_create` x metadata → 48) ride along; and it can only raise, never fix the over-scored recon cells already in my queue.
- rowfix — GOOD: Cheapest workload (+18), every one of its 60 repairs has a logged justification I can read in `slack_real_changes.csv`, it nails the motivating case (`delete-event` all four calendar cells raised, recruiting → b5/125), and it is the *only* candidate that de-escalates junk: `team-leads conversations_history` 60 critical → 36 high, `channel-messages conversations_unreads` 48 critical → 36 high, `exec-private conversations_mark` 32 high → 16 medium. Somebody finally took pages *off* my desk. BAD: Coverage is thin — 19/51. It leaves the entire calendar `create-event` row and slack `conversations_add_message incident-response` at b1/16 medium, so a third of the original bug survives. A couple of repairs are shaky (blast 1→4 for `conversations_join` on a sens-1 engineering channel — harmless band-wise, but the justification is hand-wavy).

**Verdict:** Ship floor-gated: full coverage of the actual bug at 0.67 extra pages per fix, deterministic, and it never touches a read tool — that's the only one of the four I'd let write to my gating config unattended. Run rowfix behind it as the auditor, because it's the only experiment that understands scores can go *down*, and steal its de-escalations. Floor-plain turns `list-calendars` into a high and `get-event` into a critical, ctx spends more pages than anyone while missing `delete-event` entirely and re-rolling the dice every scan — both go in the bin.

---

## Dr. Sela Marchetti (methodologist)

**One-line philosophy:** An intervention is worth exactly the inference it licenses — if you cannot attribute the change, reproduce it, or transfer it, you have a number, not a result.

**Scores (0-10):** ctx: 3 | floor-plain: 4 | floor-gated: 6 | rowfix: 7

**Ranking:** 1st rowfix, 2nd floor-gated, 3rd floor-plain, 4th ctx

**Per experiment:**
- ctx — GOOD: The only experiment that produced a genuine *finding*: with a full per-tool understanding profile injected, delete-event still gets blast 1 because the model's own profile correctly says one call deletes one event. That is a clean falsification of the "model lacks comprehension" hypothesis — the coverage rubric, not context, is the binding constraint. That negative result is worth more than its positive numbers. BAD: As an intervention it is inferentially bankrupt. It re-scans everything with an LLM known to have re-scan variance, so every observed delta = prompt effect + noise + drift in *other* primitives, unseparated. The comparison table betrays it: scores change at fixed blast (b3→36, b1→12, b2→50 — impacts/sensitivities moved), cells flip to N/A (usergroups_me, edit_file|file-contents; fs na 121→100), one offender got *lowered* (conversations_leave|exec-private b2→b1), and fs low band went 14→27 — a large uncontrolled shift in non-target cells. 27/51 offenders raised, with no way to say how many by the prompt versus the dice.
- floor-plain — GOOD: Perfectly deterministic and attributable — `scripts/apply_blast_floor.py` does exactly what it says, zero variance, trivially transferable to any server, never lowers, preserves N/A. Internal validity of the *mechanism* is flawless. BAD: The construct is broken twice. First, 51/51 is circular — the rule is literally "raise blast when sens≥4 and blast is low," and the offender metric is "sens≥4 cells whose blast is low"; success is true by construction and constitutes no evidence. Second, plain floors *read and metadata* tools on sensitive assets, directly contradicting the framework's own definition that blast prices reach, not value — sensitivity now enters the product twice (once as s, once through the floor on b). It manufactures high-band reconnaissance cells the rubric explicitly wants low.
- floor-gated — GOOD: Same determinism and reproducibility as plain, but the impact≥4 gate confines the override to the mutation cells that actually motivated the work; band distributions confirm restraint (calendar critical stays 5 vs plain's 9; slack/fs untouched outside the target region). As an engineering backstop it is the only candidate you could ship tomorrow and re-derive bit-identically. BAD: Still circular on the headline metric (51/51 is definitional, not evidential) and still hard-codes a sensitivity→blast coupling that double-counts sensitivity in s×b×i. It cannot distinguish a genuinely pinpoint, easily-reverted touch (which P4 in rowfix correctly protects) from a broad one — it is a policy, not a measurement, and it will impose that policy on servers where it is wrong.
- rowfix — GOOD: The best experimental design of the four: frozen baseline (no re-scan confound), a single manipulated variable (blast only, enforced by code-level guardrails in `scripts/row_consistency_repair.py` — clamping, N/A pass-through, no-op dropping), every change logged with a principle-citing justification, and principles P1-P4 that are actually falsifiable orderings rather than vibes. P4 explicitly resists the double-counting that sinks floor. Its calendar delete-event repairs (b1→b3/b4/b5) hit exactly the motivating bug via the *intended* mechanism. Its 19/51 is honest, not circular. BAD: LLM-stochastic with rerun variance *unmeasured* — one seed, one draw; the repair set's stability across k reruns is the single most important missing number. Coverage is inconsistent (fixed slack add_message rows but left calendar create-event and most fs offenders untouched), and it also moved non-offender cells (slack low 15→8) without a false-positive audit. Silent dropping of invalid repairs, while safe, hides model failure modes.

**Methodological caveats the team should not sweep under the rug:** (1) The offender metric is circular for both floor variants — report it for ctx/rowfix only, and evaluate floor against an *external* criterion: an expert/oracle panel labeling a held-out cell sample (offenders AND the medium→high migrants, to price false positives), plus transfer to a fourth, unseen server. (2) The baseline itself is one draw from a variant LLM — the 51-cell offender set is a sample, not a population; re-scan the baseline k times and report offender-set stability before treating "51" as ground truth. (3) rowfix needs k reruns with repair-set Jaccard/agreement reported; until then "19 raised" has no error bar. (4) ctx's N/A churn changes the denominator between arms — band distributions are not comparable across different na counts. (5) All three servers are human-workspace domains (calendar/chat/files); nothing here tests transfer to e.g. the finance or github catalogs already in the repo. (6) ctx's negative result should redirect effort: the fix belongs in the blast *rubric* (a consequence-severity or reversibility term), not in more context or more overrides.

**Verdict:** rowfix wins on the only currency I trade in — attributable, guardrailed, logged, single-variable inference — but it is provisional until someone runs it three times and shows me the repair sets agree; floor-gated is the reproducible backstop you deploy while admitting it is a policy whose "51/51" proves nothing because it was scored by its own definition. ctx is a confounded intervention that happens to contain the study's most valuable sentence: the model already understands delete-event perfectly and the rubric still prices it at 1. Fix the rubric, validate rowfix's stability, keep gated as a belt-and-suspenders floor, and never again let an experiment grade itself.

---

## Ingrid Halvorsen (compliance & risk auditor)

**One-line philosophy:** A score I cannot reproduce, explain cell-by-cell, and defend in a post-incident review is not a control — it is an opinion.

**Scores (0-10):** ctx: 2 | floor-plain: 8 | floor-gated: 9 | rowfix: 5

**Ranking:** 1st floor-gated, 2nd floor-plain, 3rd rowfix, 4th ctx

**Per experiment:**
- ctx — GOOD: It occasionally reasons well about specific cells (move_file on private_key.pem raised b1→b5, which is materially correct). BAD: Everything else. It is a full non-deterministic re-scan: it caught only 27 of 51 offenders, it *lowered* previously correct scores (conversations_leave exec-private fell from high 32 to medium 16), and cells that were scored in the baseline drifted to N/A entirely (usergroups_me, edit_file/file-contents) with nobody having changed anything. There is no per-change record, no guarantee, and no reason to believe a re-run reproduces any of it. When the regulator asks why delete-event on a personal calendar is still 20/125 "medium" under this candidate, the answer is "the model felt differently that day." Unacceptable.
- floor-plain — GOOD: A written, deterministic rule closed 51 of 51 offender cells with mathematical certainty; the guarantee is provable by inspection (max(blast, floor) — no scored sens-4/5 cell can multiply down to pinpoint), floors never lower a score, N/A is untouched, and baseline values are preserved alongside floored ones for audit. Same inputs, same outputs, forever. BAD: It is over-broad: it raised 144 cells across the three servers versus 54 for gated, sweeping read-only and reconnaissance tools into the floor. When the customer asks why a metadata listing on a sensitive asset was priced as if it were a mutation, the honest answer is "the rule doesn't distinguish" — a defensible answer, but a weaker one.
- floor-gated — GOOD: Everything floor-plain guarantees, with the scope discipline plain lacks: the floor applies only where the documented failure mode lives (impact ≥ 4 mutations), still closes all 51 offenders, and leaves reads at the model's coverage blast. The rule fits in one sentence a risk committee can ratify, and the script docstring states motivation, rule, variants, and invariants — that docstring is committee-ready as written. Deterministic post-processing over a frozen baseline; the audit answer to any changed cell is the rule itself. BAD: The floor values (5→4, 4→3) are asserted, not derived; I would want the committee minute recording why 3 and 4 were chosen. And it inherits any baseline error it does not target — a mispriced read stays mispriced. These are governance chores, not defects.
- rowfix — GOOD: This is the only candidate that understood what an audit trail is: every change logged with old/new blast, old/new score, band transition, and a cited principle (P1-P4); guardrails restrict changes to blast, clamped, N/A untouched; unrepaired rows pass through byte-identical. If I must accept an LLM in the loop, this is the governance harness I would demand. BAD: The harness is better than the results. It repaired only 19 of 51 offenders — create-event on the recruiting calendar (sens 5) sits untouched at 20 "medium", the exact class of failure that motivated this exercise — and the auditor itself is an LLM, so a re-run gives me no guarantee the same 19 cells are repaired for the same reasons. A beautiful log of an incomplete, unstable repair is still incomplete and unstable. It also raised holidays (sensitivity 1), scope creep the offender definition never asked for.

**Audit-trail assessment (quote one logged rowfix justification and grade it):** From calendar_real_changes.csv: *"P2: search-events should have blast >= get-event as it likely reaches more items."* Grade: B-minus. It does the two things a defensible entry must do — cites a written principle (P2) and names the specific comparator cell that makes the row inconsistent — and that is genuinely better than anything ctx produces. But "likely" is a hedge no auditor should sign, and the P1 entries are near-verbatim boilerplate repeated across six rows ("Impact 5 should not have a lower score than impact 2-3/2-4/3-4...") — templated recitation of the principle rather than cell-specific evidence. Specific in form, generic in substance.

**Verdict:** I can put floor-gated in front of a risk committee this quarter: one sentence of rule, a provable guarantee that no sensitive mutation prices as pinpoint, identical output on every re-run, and the baseline preserved beside the correction — floor-plain is the same instrument with a wider blade if the committee prefers conservatism over precision. Rowfix has the finest paperwork in the field and I commend whoever built its logging, but paperwork documenting a 19-of-51 repair rate from a non-deterministic auditor is a well-annotated gap, not a control. Ctx I decline to certify at all: scores that drift, drop, and vanish between runs of unchanged inputs are precisely what this office exists to prevent.
