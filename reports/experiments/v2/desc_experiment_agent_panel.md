# Agent judge panel — round 2: `five_level_v2_desc`

The same four judge personas that ranked the blast experiments
(`blast_experiments_agent_panel.md`) evaluated the org-description /
no-sensitivity experiment. Each judge re-read their own round-1 verdict for
calibration, then verified claims against the desc artifacts (matrices,
`server-profiles.md`, `band_label_no_sens`, the driver) and the
`five_level_v2_fs` baseline.

## Combined scoreboard (both rounds)

| candidate | Raven | Moss | Marchetti | Halvorsen | mean |
|---|---|---|---|---|---|
| **floor-gated** | 7 | 8 | 6 | 9 | **7.50** |
| floor-plain | 9 | 4 | 4 | 8 | 6.25 |
| rowfix | 5 | 6.5 | 7 | 5 | 5.88 |
| **desc (new)** | 6 | 5.5 | 5 | 4 | **5.13** |
| ctx | 3 | 3 | 3 | 2 | 2.75 |

desc placed 3rd or 4th on every card — a consistent middle: better than ctx
everywhere, never beating floor-gated.

## Panel consensus on desc

**Unanimous praise — the band floor.** `band_label_no_sens`'s deterministic
irreversibility floor (`impact == 5 → at least high`, `impact 5 ∧ blast ≥ 4 →
critical`) closes the delete-event class BY RULE, on every server, with no LLM
discretion and no bolt-on script. All four judges independently identified it
as the best single mechanism in the experiment — and Marchetti notes it is
exactly the "fix the rubric, not the overrides" direction demanded in round 1.
Driver hygiene (fresh out-dir, no-clobber, fail-loud profile parsing) was also
praised across the board.

**Unanimous criticism — removing the sensitivity primitive.** Four
formulations of the same defect:

- **Raven**: value compensation is lexical, not semantic — named secrets
  (key/password/token) get blast 5, but per-patient PHI reads price at 3 LOW,
  same as README (`medical_history.txt`, `kyc_passport.png`). "I read charts
  one patient at a time, by name, and no gate blinks." Plus alias arbitrage:
  `read_file` vs `read_text_file` on the same file, 3 low vs 12–15 high.
- **Moss**: the floor is ungated — `conversations_join` #random = HIGH, joining
  incident-response = 25/25 CRITICAL while a fake message in that channel
  mid-incident = 4/25 medium. Only 20 possible (blast, impact) pairs: "the
  queue ranks verbs, not what they're pointed at." (Though desc is the first
  candidate with NEGATIVE workload delta: −91 high+critical cells, −44%.)
- **Marchetti**: sensitivity was not removed, it was *laundered* — the profiles
  contain literal 1–5 sensitivity tables, and value re-enters blast
  stochastically (`read_file` blast 1 on README vs 5 on payslips, identical
  reach). Blast is no longer a reach measurement. Four simultaneous changes in
  one arm = no attributable inference; the 2×2 ablation
  ({desc on/off} × {sens scored/not}) is the missing experiment.
- **Halvorsen**: the challengeable number is gone — "payslips outranks README"
  used to be a logged 4-vs-1 an auditor could dispute; now it is un-logged LLM
  interpretation of prose. `server-profiles.md` is a production scoring input
  with no owner, no version, no sign-off, uncommitted in git, and deliberately
  uneven profile lengths (53–493 words, allocated by experimental design, not
  risk). "I certify the rule and decline to certify the system."

## Action items the panel converged on

1. **Keep `band_label_no_sens`'s irreversibility floor** — port it back into
   the sensitivity-scored pipeline (every judge wants this rule regardless of
   the sensitivity question).
2. **Restore a logged asset-value primitive** beside the description (or gate
   the floor on a value tier) — the ungated floor over-pages on wallpaper
   (README write = high, holidays delete = high) and under-prices contextual
   PII reads.
3. **Run the 2×2 ablation** (desc on/off × sensitivity on/off) — without it,
   nothing about the description's contribution is attributable.
4. **Put `server-profiles.md` under change control**: commit it, name an owner,
   hash its version into every scan artifact it influenced.
5. **Fix alias incoherence** (`read_file` vs `read_text_file` pricing) — noted
   by Raven, Marchetti, and Halvorsen independently; either pin per-verb
   impact/blast or reconcile aliases before scoring.
6. **Analyze the tier experiment the profiles were designed for** (XS–XL
   lengths) — the ablation was built into the input but never read out.

## Panel verdicts (verbatim)

*The four full verdicts below are reproduced unedited.*

---

## Raven (red-team operator) — on five_level_v2_desc

**Score (0-10):** 6

**Where it lands in my previous ranking (ctx 3, floor-plain 9, floor-gated 7, rowfix 5):** Third. Above rowfix (5) and ctx (3) because the impact-5 band floor finally fixes the whole destruction class deterministically and universally instead of the 19/51 rowfix left half-done. Below floor-gated (7) and well below floor-plain (9) — because ripping out sensitivity reopened the exact hole that made me crown plain: the crown-jewel *read* on regulated PII/PHI. desc actually regresses below the old sensitivity baseline on that axis, and that is a coverage judge's cardinal sin.

**GOOD:**
- The flagship is dead. `delete-event` on personal/team/executive/recruiting AND holidays all land blast1×impact5 = score 5, band **high** — the impact-5 floor prices destruction as high even at blast 1, on every calendar, with no LLM re-scan to demote it (unlike ctx, which shipped it at 20 medium and rolled dice on other cells). More complete than rowfix, cleaner than gated.
- `audit_log.txt` `write_file` = blast2×impact5 = **10 high** and `edit_file` = 16 high. Tampering with the security log finally trips the gate — under ctx this was 20 medium. Same win on the fintech `access_log.txt` (write 25 critical, edit 20 high).
- Named credential crown jewels are covered on *every* verb: `private_key.pem` read 15 high / move 20 high / write 25 critical / edit 20 high; fintech `stripe_api_key.txt`, `db_root_password.txt`, `pan_tokens.csv` all read 15 high, move 20 high, write 25 critical. That is floor-plain's exfil-read strength reproduced without a sensitivity primitive — the description carried the blast number here.

**BAD:**
- Removing sensitivity **flattened regulated data files onto the scratch-file scale**, and the description compensated only in prose, not in the numbers. The model bumped blast for things that *look* like secrets (key/password/token/vault) and for directory scopes, but left contextually-sensitive data files at blast 1. The server-profiles doc screams "PHI, sens 5, C-first, batch-read is the exfil signature" — and the scorer read a single patient chart at blast 1 = **low**. Prose ≠ price.
- The compensation is lexical, not semantic. It's asymmetric and gameable, and it means a doc that *understates* an asset (or names it blandly) leaves that asset priced as a scratch file — the whole risk of this design.
- Score-scale collapse: the "high" band now spans 5/25 to 20/25. A delete-event high (5) and a payslip-overwrite critical (25) are 5x apart, yet everything rides on `band_label_no_sens`; the number itself is decorative.

**Cells I'd exploit under desc (with numbers):**
- **The kill shot — medical tenant.** `patients/alice_johnson/medical_history.txt` `read_file` = blast1×impact3 = **3 low**; same for `prescription.txt`, `intake_form.txt`, and every `bob_martinez/*` chart. Named-patient PHI exfil is priced identically to `README.md` read (3 low). The old sensitivity baseline would have carried sens5×3 into this cell; desc drops it to low. I read charts one patient at a time, by name, and no band-gate blinks. The scanner only caught the *directory-wide* `patients/` read (15 high) — I never touch the directory.
- **Fintech PII.** `customers/cust_0001/kyc_passport.png` `read_file` = **3 low**, `profile.json` `read_file` = **3 low** — identity-theft-grade documents the profile explicitly rates sens 5, priced as scratch.
- **Alias arbitrage.** Same asset, same operation, two prices: fintech `payments/settlements/2026-05_settlement.csv` `read_file` = 3 low but `read_text_file` = 12 high; medical `hipaa_notice.txt` `read_file` = 3 low vs `read_text_file` = 15 high. I just call the `read_file` (DEPRECATED) alias and pay low for the identical read.
- **Exfil-by-move on payroll.** `payslips_q1.csv` `move_file` = blast1×impact4 = **4 medium** — relocating the payroll file out of the tree is medium, while `private_key.pem` `move_file` got blast5 = 20 high. Inconsistent, and medium clears the gate.
- **Lure on the PII calendar.** `create-event` on `recruiting` = blast1×impact4 = **4 medium**, unchanged from baseline — planting a poisoned invite on the candidate-PII calendar still doesn't floor.

**Verdict (2-3 sentences, in persona):** The band floor is the real thing — it kills the delete-event/audit-log destruction class outright, deterministically, on every asset, which is more than rowfix or ctx ever managed and as clean as gated. But tearing out the sensitivity primitive and trusting a prose profile to backfill the numbers is exactly the trade a red-teamer refuses: it prices a named private key perfectly and a named patient's medical history as low as a README, so the single juiciest attack I'd run against the clinic tenant — read the chart by name — walks straight through a gate the old baseline would have caught. Bolt the destruction floor onto a scorer that still keeps sensitivity in the *read* price and I'm back to a 9; ship it as-is and I own your PHI at blast 1.

---

## Moss (SOC / gateway operator) — on five_level_v2_desc

**Score (0-10):** 5.5

**Where it lands in my previous ranking (ctx 3, floor-plain 4, floor-gated 8, rowfix 6.5):** Between floor-plain and rowfix: floor-gated 8 > rowfix 6.5 > **desc 5.5** > floor-plain 4 > ctx 3. It's the first candidate that *reduces* my total load and it fixes the delete-event class deterministically — but it does it by ripping out the sensitivity gate that made floor-gated an 8, and the hole it leaves gets filled by whatever blast/impact number the LLM feels like today. It mints criticals for `conversations_join`, and a critical for a join is worse for analyst calibration than ten mediums for deletes.

**Workload math (high+critical vs baseline on calendar/slack/fs):** Baseline: calendar 53 (48h+5c), slack 52 (37+15), fs 103 (81+22) = 208. Desc (`band_distribution` in the JSONs): calendar 18 (17h+1c, **-35**), slack 40 (28h+12c, **-12**), fs 59 (48h+11c, **-44**) = **117 total, -91 cells (-44%)**. First experiment on this bench whose delta is negative. But the composition matters: of slack's 40, **10 are the `conversations_join` verb** (high on general/announcements/random/engineering/research-team/agent-channel-membership; **25/25 critical** on incident-response/exec-private/team-leads, 20 on on-call), and of fs's 59, 4-5 are `write_file` highs on assets the profile itself calls near-public (`README.md`, `onboarding/`, `onboarding/org_chart.png`, `projects/known_defects.csv` — all blast 1, impact 5, score 5/25 → high). Call it ~15 junk pages inside the 117.

**GOOD:**
- **The impact-5 floor fixes delete-event with zero bolt-ons.** All 7 calendar assets' `delete-event` cells land at high (blast 1, impact 5, score 5) straight from `band_label_no_sens` in `pipeline.py` — no LLM rule, no rowfix pass, one auditable line: `impact == 5 → high`. That's the flagship bug closed the way floor-gated closed it.
- **Net -91 pages** on the three overlapping servers, and most of what got demoted deserved it — baseline's sensitivity-inflated recon highs are gone (`executive,list-calendars` 4 medium, `get-event` 3 low).
- **Sensitivity is being smuggled back in through blast, and sometimes well:** payslips `read_file` is blast 5 → 15 high while `README.md read_file` is blast 1 → 3 low; `private_key.pem move_file` 20 high; `sensitive/security/` scope reads all 15 high. So no — README and payslip cells do NOT band the same in practice, because the profile-fed LLM gives them different blast. The profile text is doing real work.
- Fs high/critical list is mostly defensible: root `/` and `sensitive/` scope writes at 20-25 critical, `core.c write_file` 25 critical (matches the profile's supply-chain call), `audit_log.txt edit_file` 16 high.

**BAD:**
- **The floor is ungated now, and it amplifies LLM impact mistakes.** The scanner decided `conversations_join` = impact 5 on every channel, so joining **#random** is a HIGH and joining incident-response is a **25/25 critical — the maximum score in the entire system — while planting a fake message in incident-response mid-incident is a 4/25 medium** (`conversations_add_message` blast 1). One miscalibrated verb times a hard floor = a whole junk verb-class on my queue, and there's no sensitivity column left to gate it out. Floor-gated's `sens >= 4` condition existed precisely to stop this.
- **New blind spots where blast fails to smuggle:** `executive,search-events` is blast 3 → 9 **medium** while `personal,search-events` is blast 4 → 12 **high** — the exec calendar now ranks *below* a personal one on reads, an inversion baseline's sensitivity column prevented. `holidays,delete-event` pages identically to `executive,delete-event` (both 5 high) because the band is a pure function of (blast,impact).
- **Tuning question answered: there are only 20 (blast,impact) pairs.** The band column can distinguish at most 20 cell types across all 13 servers; every asset with the same pair bands identically, so 100% of asset ranking rides on the LLM's blast call — a nondeterministic number with no second column to cross-check, and an empty `sensitivity` field in the CSV, so "why did this page" now requires reading model prose instead of a matrix.
- **The profiles are not gateable.** `server-profiles.md` contains genuinely useful facts ("nothing in the sanctioned workflow requires reading `sensitive/security/`", peak sens per asset, CIA priority) — but none of it lands as a column I can put a rule on. It only changes prose into slightly different LLM numbers. I can't write a gating config against a paragraph.

**Verdict (2-3 sentences, in persona):** Desc is the first candidate that hands pages *back* — minus 91 cells and delete-event finally fixed by one deterministic line — so credit where due, but it paid for it by firing the only deterministic co-signer I had: with sensitivity gone, every band is the LLM's blast call wearing a trench coat, and the day my analysts see `join #random → HIGH` and `join incident-response → 25/25 CRITICAL` next to `fake message in incident-response → medium`, the rubber stamps come out. Keep the impact-5 floor and the max-25 scale, but put a gate back on that floor — asset column or profile-derived tier, I don't care, something I can grep — because right now the queue ranks verbs, not what they're pointed at. Floor-gated still wears the crown.

---

## Dr. Sela Marchetti (methodologist) — on five_level_v2_desc

**Score (0-10):** 5

**Where it lands in my previous ranking (ctx 3, floor-plain 4, floor-gated 6, rowfix 7):** Between floor-plain and floor-gated: ctx 3, floor-plain 4, **desc 5**, floor-gated 6, rowfix 7. It finally does the thing I demanded — a deterministic, rubric-level irreversibility floor (`impact == 5 → high` in `band_label_no_sens`, pipeline.py:155-163) instead of per-scan overrides — and that alone lifts it above floor-plain. But it buys that fix inside a two-variable (really four-variable) confounded arm whose numbers cannot be attributed, compared, or externally validated, so it cannot touch the two candidates whose one virtue was clean inference (rowfix) or provable scope (floor-gated).

**GOOD:**
- **The delete-event class is fixed by the right mechanism.** `calendar_real_matrix.csv` shows every `delete-event` cell at blast 1 × impact 5 → band **high**, deterministically, from the band function itself — not from an LLM's mood or a bolt-on script. This is exactly the "fix the rubric, not the overrides" direction from my last card, executed as a written, re-derivable rule that transfers unchanged to all 13 servers. Credit where due.
- **Driver hygiene is exemplary**: `scan_desc_no_sens.py` writes to a fresh directory, refuses to clobber without `--overwrite`, keys artifacts 1:1 to profile sections, and the profile parser fails loudly when a section is missing rather than silently scanning without context.
- **The prompts show real construct discipline in design**: DESC preamble splits authority cleanly (org authoritative for importance, registry for capability, "the description does not license an action no tool can perform"), and `_NO_SENS_NOTE` explicitly anticipates and forbids the value-into-blast failure mode.
- **The profile document has an ablation designed into it** (XS–XL length tiers spread within server kind, with named within-kind comparisons) — someone was thinking about dose-response, which is more experimental intent than any prior arm showed.
- 13 servers including 4 new themed filesystem tenants over an *identical* 14-tool surface is a genuinely good transfer instrument — it answers my "test on unseen servers" demand in structure, if not yet in analysis.

**BAD:**
- **Sensitivity was not removed; it was laundered.** The profiles contain literal per-asset 1–5 sensitivity tables ("Sens. 5" columns in fs_fintech_fs, sqlite_devops), so the "deleted" primitive re-enters as prose the model reads before every stage — it just no longer appears as an auditable number in the output. And the matrices prove it re-emerges inside blast: `read_file` on `README.md` gets blast 1 while `read_file` on `payslips_q1.csv` and `private_key.pem` gets blast 5 — three single-file reads with *identical* reach. `write_file` (full overwrite, identical coverage everywhere) is blast 1 on README and blast 5 on payslips. Blast is no longer a reach measurement; it is an unquantified value×reach composite, which is double-counting in reverse and destroys the attribution the multiplicative model existed to provide. Note the prompt *did this to itself*: `_NO_SENS_NOTE` forbids smuggling value into blast in one sentence and, two sentences later, opens tier-5 escape routes for description-named "dangerous-class populations" — a sanctioned backdoor.
- **At equal (blast, impact), differentiation is now impossible by construction** — `band_label_no_sens` is a pure function of two ints. Where the description failed to move blast, value distinctions vanish: `delete-event` on the public `holidays` calendar bands **high**, identical to `delete-event` on `executive`; `write_file` on a sensitivity-1 README bands **high**. The old model over-waved deletes through; this one cannot rank them.
- **The description input is unversioned and self-authored**: `server-profiles.md` is untracked in git (`??`), written by the same team that scores with it, with no external org or oracle behind it. The intervention variable itself has no provenance.
- **No analysis artifact exists** in `five_level_v2_desc/` — 39 output files, zero comparison, zero tier-experiment readout. The experiment ran; the experiment was not analyzed.

**Design flaws that cap the score (numbered):**
1. **Unresolvable confound**: description added AND sensitivity removed AND formula/scale changed AND bands recalibrated AND a fresh LLM re-scan with known rescan variance and shifted N/A sets — a single arm carrying at least four simultaneous changes, with no desc-with-sens arm and no no-desc-no-sens arm. The design licenses exactly one inference: "the combined bundle produces these numbers." No delta can be attributed to the description, which was the stated research question.
2. **Construct substitution presented as construct removal**: asset value now lives (a) in prose the model reads, (b) in blast via escape routes, (c) nowhere in the delete rows — three inconsistent homes, none of them a number an auditor can point to. `blast × impact` is not the claimed value×reach×action model; it is reach×action with value stochastically leaking into reach.
3. **Cross-experiment incomparability**: 25-point scale, new band function dominated by categorical floors (the 13%/40% "same fractions" threshold derivation is cosmetic — the floors, not the thresholds, decide most bands), and a new N/A landscape mean no score, band count, or offender metric here can be compared to any prior arm. The delete-event "fix" is also definitionally true (the rule is `impact 5 → high`; deletes are impact 5) — same circularity I flagged on the floors' 51/51.
4. **Circular, unversioned ground truth**: the experimenters wrote the org's "own" description, did not commit it, and validate nothing against any external party. Profile quality is deliberately uneven (53–493 words) but the tier variable is confounded with organization except in the within-kind pairs, which were not analyzed.
5. **Intra-matrix incoherence left unexamined**: `read_file` vs `read_text_file` on `audit_log.txt` score blast 1 vs 2; `read_multiple_files` on payslips gets blast 2 while single `read_file` gets 5. Single-draw LLM noise, no k-run stability, no error bars — my standing complaint, still unaddressed.

**What would fix the design (concrete ablations/validations):**
1. Run the missing 2×2: {desc on/off} × {sensitivity scored/not}, same servers, same seed policy — only then is "what did the description do" answerable. The desc-with-sens cell also directly tests whether description and scored sensitivity double-count.
2. Freeze and commit `server-profiles.md` (hash it into each scan JSON) so the intervention variable has provenance; have a second, independent author write profiles for 3 servers and measure score sensitivity to authorship.
3. Quantify the value-leak: regress desc-mode blast on baseline sensitivity at fixed (tool, coverage); if sensitivity predicts blast, report it as the redefinition it is, and either sanction it formally (rename the primitive) or close the escape-route backdoor in `_NO_SENS_NOTE`.
4. k=3 re-scans of at least the two identical-surface filesystem pairs (fintech XL vs media XS); report per-cell agreement before reading anything into tier effects — then actually run the tier analysis the profile doc promises.
5. External oracle panel on a stratified cell sample including the new structural over-escalations (`write_file`/`delete` on sensitivity-1 assets now banding high) to price the false-positive cost of the irreversibility floor, which the current design cannot see.

**Verdict (2-3 sentences, in persona):** This arm finally puts the irreversibility judgment where I said it belonged — in a deterministic rubric — and then wraps that one clean rule in the least attributable design of the five I have now judged: four simultaneous changes, an unversioned self-authored treatment, and a "removed" primitive that demonstrably re-enters through blast on payslips while vanishing on deletes. The matrices don't show sensitivity deleted; they show it driven underground, where no one can audit, reproduce, or price it. Ship the band floor, commit the profiles, run the 2×2 — until then this is a bundle of confounded numbers wrapped around one good sentence of rubric.

---

## Ingrid Halvorsen (compliance & risk auditor) — on five_level_v2_desc

**Score (0-10):** 4

**Where it lands in my previous ranking (ctx 2, floor-plain 8, floor-gated 9, rowfix 5):** Fourth of five — above ctx, below rowfix. Final order: floor-gated 9, floor-plain 8, rowfix 5, **desc 4**, ctx 2. The band rule inside desc is floor-gated's equal — deterministic, one paragraph, ratifiable — but it is bolted onto a full non-deterministic re-scan (ctx's sin) and it deletes the one logged number (sensitivity) that made asset value challengeable, while adding an ungoverned free-text file as a scoring input. The rule earns marks; the system it is embedded in loses them.

**GOOD:**
- `band_label_no_sens` (pipeline.py, lines 135-166) is exactly what I ask a control to be: a written, deterministic function of two logged integers. I reproduced every band in `calendar_real_matrix.csv` from (blast, impact) alone. The irreversibility floor closes the delete-event class **by rule**: all seven scored `delete-event` cells sit at blast 1, impact 5 → high, with no LLM discretion able to demote them once impact is 5. `manage-accounts` on connected-account-config (blast 4, impact 5) lands critical by the same clause. When the regulator asks "why is this cell high," the answer is a sentence in a docstring, not a model's mood.
- It closes the gap Raven logged against my previous winner: impact-5 destruction on low-sensitivity assets can no longer hide behind a sensitivity key — the floor is unconditional.
- `scan_desc_no_sens.py`'s docstring commits to writing a NEW directory and refusing to clobber existing artifacts without `--overwrite`. Prior evidence is preserved by default. Approved, and I would like this made standard across every scan script.
- The profile parser fails loudly when a server has no section rather than silently scanning without context. Correct posture.

**BAD:**
- **The challengeable number is gone.** The `sensitivity` column in both CSVs is blank. In the baseline, "payslips outranks README" was a logged 4-vs-1 an auditor could dispute in writing. Now `payslips_q1.csv/read_file` is high because the model wrote blast **5** for reading *one named file* — that is not coverage, that is asset value smuggled into the blast primitive after the model read prose, with no record of which sentence did it. The rationale moved from a column to un-logged LLM interpretation. That is an audit-trail regression, full stop.
- **Determinism of the primitives did not improve — the record proves it.** `source_code/core.c`: `read_file` blast 5 (15, high) but `read_text_file` blast 1 (3, low) — the same file, the same operation class, twelve points apart. `payslips_q1.csv`: `read_file` blast 5 but `read_multiple_files` blast 2. I cannot defend either pair to anyone. The deterministic band function is fed by dice.
- **The guarantee is conditional.** The impact-5 floor closes delete-event only for as long as the LLM keeps pricing delete verbs at impact 5. Nothing pins impact; a re-scan that returns impact 4 dissolves the "guarantee" silently. Floor-gated operated once, over a frozen, inspected baseline; desc re-rolls every primitive every scan.
- **Asset value can no longer demote.** `holidays/delete-event` (a public calendar, sens 1 in the profile) is high, identical to executive; `README.md/write_file` is high. A floor with no sensitivity term prices wallpaper as crown jewels, and my Moss colleague's analysts will rubber-stamp accordingly.

**Governance findings on server-profiles.md as a scoring input:** The document is now part of the scoring system — "whoever edits that file changes future risk scores" — and it carries **no named owner, no version identifier, no approval or review date, no change log, and no access control** beyond ordinary repo write access. Worse, it self-describes as an experimental instrument: profile lengths are "deliberately uneven" so tiers can be A/B'd — `fs_media_studio_fs` gets 53 words of asset-value statement while `fs_fintech_fs` gets 493, allocated by experimental design, not by risk. I cannot accept as the authoritative statement of asset value a document in which the amount of statement each asset receives was randomized. Credit where due: the L/XL profiles state per-asset severity crisply (the fintech table — sens plus C/I/A per asset with a one-line why — is genuinely scoreable), and the fail-loud parse keys are correct. But to replace a scored primitive this file would need, at minimum: a named accountable owner, a version stamp whose hash is logged into every scan artifact it influenced, a committee review date, and mandatory sign-off on edits (CODEOWNERS or equivalent). None of that is present. As it stands, an unreviewed markdown edit is a production scoring change with no paper trail.

**Verdict (2-3 sentences, in persona):** The band function I would ratify this quarter — a deterministic irreversibility floor that closes the delete-event class by written rule is precisely the guarantee I awarded floor-gated a 9 for — but a rule is only as defensible as its inputs, and desc feeds it re-rolled LLM primitives contaminated by an unversioned, owner-less prose file while erasing the one logged number an auditor could challenge. When the regulator asks why payslips outranks the README, "the model read the description and felt blast was 5" is an opinion, not a control. Keep the band function, restore a logged asset-value primitive beside it, and put server-profiles.md under change control with an owner and a version hash in every artifact — until then I certify the rule and decline to certify the system.
