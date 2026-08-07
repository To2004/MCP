# Agent judge panel — final round: `pure ult`

The same four judge personas from rounds 1 (blast experiments) and 2 (desc)
evaluated the final configuration: `five_level_v2_ult` scoring machinery
(org-table sensitivity, gated blast floor, alias-twin pass, `band_label_v5`)
with the **pure** registry construction (tool catalog + spec-v1 org profile as
the only scanner inputs). Every judge independently verified the evidence —
including re-running the determinism diff themselves.

## Final scores and all-time scoreboard

| candidate | Raven | Moss | Marchetti | Halvorsen | mean |
|---|---|---|---|---|---|
| **pure ult (final)** | 8 | 8.5 | 8 | 9 | **8.38** |
| floor-gated | 7 | 8 | 6 | 9 | 7.50 |
| floor-plain | 9 | 4 | 4 | 8 | 6.25 |
| rowfix | 5 | 6.5 | 7 | 5 | 5.88 |
| desc | 6 | 5.5 | 5 | 4 | 5.13 |
| ctx | 3 | 3 | 3 | 2 | 2.75 |

**Unanimous #1** — the first candidate every judge ranked first, including
Raven demoting her own floor-plain (9) below it: pure ult's residual holes
bottom out at medium where plain's bottomed out at low.

## What the panel verified (not just accepted)

- **Determinism**: Ingrid, Moss, and Marchetti each independently diffed the
  two pure runs — 208/208 cells bit-identical (empty diff / cmp / matching
  md5). The "numbers move on re-scan" era is over for this configuration.
- **Attribution upgrade** (Marchetti): determinism retroactively makes every
  ablation delta a *pure lever effect* — no variance term under greedy
  decoding. The _tools (87%, hub-cell demotion) and _struct (83%, upward
  drift) rejections are clean results.
- **Workload** (Moss): 94 high+critical cells vs the baseline's 208 (−55%)
  with the sensitivity gate restored; slack criticals 15 → 0; every surviving
  critical earns its page; four arguable cells in total across four servers.
- **Attack coverage** (Raven): alias arbitrage closed, move-the-key 100 high,
  audit-log write 100 critical, impact-5-on-sens-3 no longer hides at low,
  hub cell 125 critical even store-blind.
- **Governance** (Ingrid): value primitive logged and challengeable;
  profile_sha256 + raw-blast + fixup audit trail in every artifact; spec v1
  with Owner/Provenance/Content unit; band rule ratified.

## Corrections the panel forced (honest numbers)

- **Marchetti's attribution catch**: the headline "95.5% pure-vs-full
  agreement" spans a PROFILE EDIT (the two runs record different profile
  hashes) and excludes 14 scored↔N/A migrations; counted over all 208 cells
  the honest number is **191/208 = 91.8%**, and the clean comparison requires
  re-running the full-input base on the current profile hash.

## Converged conditions before "ship"

1. **Commit the scoring inputs** (Ingrid + Marchetti): `server-profiles.md`,
   `mcp-profile-spec.md`, the pure driver and artifacts are untracked — "a
   hash whose preimage exists only in a working tree is provenance on a
   post-it." CODEOWNERS/sign-off on profile edits.
2. **Re-run the full-input base on the current profile** for a single-lever
   pure-vs-full comparison (cheap: deterministic).
3. **Take pure to servers it wasn't raised on** (slack/github/fs profiles
   already exist; finance untouched in seven rounds) + repeat the two-run
   stability diff there.
4. **The medium-seam tension** (the one open scoring question): Raven wants
   sens-4 mutations and impact-5 deletes unable to settle at medium
   (payslips move 48, audit-log edit 48, batch-read inversion 24 < 60);
   Moss wants the sens-3 destruction floor NOT to page high
   (known_defects.csv write 15 high). Any band_label_v5 refinement must
   resolve both directions at once — a deliberate calibration decision, not
   a bug fix.
5. Run metadata (timestamp/run id/endpoint) in artifacts; reconcile the
   spec's stale implementation-status table; build or descope the unbuilt
   validators; input-perturbation robustness (how much does a one-word
   profile edit move?); external oracle validation.

## Verbatim verdicts

*(reproduced unedited)*

---

## Raven (red-team) — final round: pure ult
**Score (0-10):** 8

**All-time ranking:** 1st **pure ult (8)** — new top — > floor-plain (9→demoted to 2nd) > floor-gated (7) > desc (6) > rowfix (5) > ctx (3). I am moving it above floor-plain despite the lower raw number: floor-plain earned its 9 by bluntly flooring every sensitive cell, but its one exploitable lane was impact-5 destruction hiding behind low sensitivity (db_schema write_file sat at 15 **low**). Pure ult closes that exact lane, adds determinism and production-shape, and kills the alias arbitrage plain never touched. Its residual holes bottom out at **medium**, whereas plain's bottomed out at **low** — a coverage judge allergic to under-scoring ranks the one that under-scores *less badly* first.

**My prior findings it fixed:**
- **Alias arbitrage — CLOSED.** read_file vs read_text_file are now byte-identical on every fs asset: private_key.pem 75 high / 75 high, payslips 60 / 60, audit_log 48 / 48, core.c 60 / 60. The `alias_fixups` twin pass did its job — no cheap `read_file` door.
- **Move-the-key inconsistency — FIXED.** private_key.pem move_file = `5,5,4,100,high`; was 20 medium under desc. Relocating the key now floors high.
- **sens-keyed floors blind to impact-5 on sens≤3 — FIXED via the sens-aware band floor.** db_schema.sql write_file `3,1,5,15,high`, known_defects.csv write_file `3,1,5,15,high`, file-records write_file `3,1,5,15,high`. Impact-5 destruction on a sens-3 asset can no longer hide at low — floor-plain left db_schema at 15 low, this lifts it to high.
- **Audit-log tampering — FIXED on the primary verb.** audit_log.txt write_file = `4,5,5,100,critical`; was 20 medium under ctx.
- **PHI-read-low class — FIXED in principle.** Sensitivity is back in the *read* price via the per-asset table: payslips read_file 60 high, private_key read 75 high, read_multiple on private_key 75 high. That is floor-plain's exfil-read strength reproduced deterministically.
- Determinism/shape: hub cell connected-account-config|manage-accounts = `5,5,5,125,critical`, the max, in pure form with no store access; 95.5% band agreement with the full scan; 208/208 bit-identical on rerun. This is the belt-and-suspenders I asked for.

**What still slips through (cells + numbers):**
- **holidays,delete-event = `1,1,5,5,MEDIUM`**. The sens-aware band floor demoted impact-5 destruction of a shared calendar back to medium — delete-event is "high everywhere" EXCEPT here. Nuke the shared calendar and the gate blinks yellow, not red.
- **payslips_q1.csv,move_file = `4,3,4,48,MEDIUM`** — payroll exfil-by-move clears a high-gate. The *gated* blast floor (sens4→b≥3) permits blast 3 = score 48 = medium, exactly where floor-plain's ungated floor would have driven it high. Same door on **audit_log move_file 48 medium** and **core.c move_file 48 medium**.
- **audit_log.txt,edit_file = `4,3,4,48,MEDIUM`** — edit-the-security-log arbitrage: write_file is 100 critical but the *edit* verb on the same log prices medium.
- **payslips_q1.csv,read_multiple_files = `4,2,3,24,MEDIUM`** — batch read priced BELOW the single read_file (60 high). The batch-exfil verb is the cheaper path; the inversion is my lane.
- **recruiting,create-event = `4,3,4,48,MEDIUM`** — my desc finding, only half-fixed: blast rose 1→3 so the score moved 4→48, but the band is still medium. A poisoned invite planted on the candidate-PII calendar still does not floor.

**Verdict (2-3 sentences, in persona):** This is the first candidate I'd actually put in front of a gateway: it kills the alias arbitrage, floors the key-move to 100 high, and finally prices impact-5 destruction on sens-3 assets as high instead of letting it hide behind a low sensitivity key — deterministically, in the store-blind shape a real deployment ships. But the sens-aware band floor and the sens4→b≥3 gate cut a new seam of medium-band doors — payslips move 48, audit-log edit 48, batch-read 24, holidays delete 5 — every one a destruction-or-exfil path on a crown asset that clears a high gate at medium, which is precisely the under-score I refuse to sleep on. Tighten the gate so a sens-4 mutation or an impact-5 delete cannot settle at medium, and this is a 9; ship it as-is and I exfil your payroll by renaming a file.

---

## Moss (SOC) — final round: pure ult

**Score (0-10):** 8.5

**All-time ranking:** **pure ult 8.5** > floor-gated 8 > rowfix 6.5 > desc 5.5 > floor-plain 4 > ctx 3. First candidate to unseat floor-gated. It keeps floor-gated's two virtues (gated mutation floor, zero recon inflation) and adds the three things floor-gated couldn't do: it *removes* load (floor-gated could only add), it de-escalates junk (rowfix's one trick, now built into the bands — `exec-private,conversations_mark` is 16 **low**, below even rowfix's 16 medium), and it diffs deterministically (208/208 cells identical across two independent pure runs — verified, empty diff).

**Workload math:** Baseline high+critical: calendar 53 (48h+5c), slack 52 (37+15), fs 103 (81+22) = **208**. Ult (`band_distribution` in the JSONs): calendar **8** (6h+2c, −45), slack **28** (28h+**0c**, −24), fs **58** (49h+9c, −45) = **94 total, −114 cells (−55%)** — and −23 below desc's 117, while putting the sensitivity gate *back*. Slack criticals go 15 → 12 (desc) → **0**. The two calendar criticals are both `manage-accounts` on account-config assets (125, 100) — those are real. Fs's 9 criticals are all `write_file` on `/`, `sensitive/*`, `core.c` (100–125) — every one earns its page. Composition check on my old junk: the ten `conversations_join` pages that desc minted (incl. three 25/25 criticals) are gone — join on `#random`/`general`/`announcements` is now **4 low**, and sens-4 channels cap at 64–80 high. Recon inflation dead: `personal,list-calendars` 6 low, `personal,get-event` 9 low, `executive,get-event` 12 medium. Residual junk I'd still flag, quoted: `projects/known_defects.csv,write_file,3,1,5,15,high`, `projects/db_schema.sql,write_file,3,1,5,15,high`, `file-records,write_file,3,1,5,15,high` (fs), `internal-docs,create_or_update_file,3,1,5,15,high` (github) — blast-1 score-15 cells riding the destruction floor onto sens-3 assets, ~4-6 cells total across four servers. And one ordering wrinkle survives: `incident-response,conversations_join,4,5,4,80,high` still outranks `incident-response,conversations_add_message,4,3,4,48,medium` — join above message-forgery in the same channel is the last echo of the desc-era verb miscalibration, though at high-vs-medium instead of critical-vs-medium it no longer breaks analyst calibration.

**My prior asks it delivered / missed:** Delivered: (1) grep-able sensitivity column — column 3 of every matrix CSV, I can write gating rules against it again; (2) floor gated on asset value — `delete-event` lands 15 high on sens-3 calendars via the irreversibility band and 60 high on executive/recruiting via the gated blast floor, while `README.md,write_file,1,1,5,5,medium` proves the wallpaper rule works (desc banded that same cell high); (3) join-verb criticals gone — confirmed, slack has zero criticals; (4) trustworthy diffs — bit-identical rerun, verified myself. Partially delivered: rowfix-style de-escalations — no explicit repair pass, but the bands do the job (`team-leads,conversations_history` 60 critical → 48 high; `channel-messages,conversations_unreads` 48 critical → 48 high; `conversations_mark` junk all low). Missed/remaining: the destruction floor still has no lower gate for sens-3 blast-1 cells (the four 15-highs above), and stability was only measured on calendar — I want the same two-run diff on slack/fs/github before I trust those matrices equally.

**Verdict (2-3 sentences, in persona):** For the first time in this bake-off I read every high and critical on four servers and found four cells I'd argue with — four, out of 94, versus a baseline that made me eat 208 with recon highs and join criticals mixed in. The sensitivity column is back where I can grep it, the floor only fires on things that actually break, deletes finally page, wallpaper never does, and two runs produce the same bytes so my diff pipeline means something again. Ship it: 8.5, new all-time first — the missing half-point is the sens-3 floor riders and the un-rerun slack/fs/github stability numbers, and I'll hand it back the day `known_defects.csv` pages someone at 3am.

---

## Dr. Sela Marchetti (methodology) — final round: pure ult

**Score (0-10):** 8

**All-time ranking:** 1st **pure ult (8)**, 2nd rowfix (7), 3rd floor-gated (6), 4th desc (5), 5th floor-plain (4), 6th ctx (3).

**Demands satisfied:**
- **Fix the rubric, not the overrides — SATISFIED.** `band_label_v5` is a pure function of three logged primitives with sens-aware irreversibility floors; the gate-grid null result (all four floor variants → byte-identical band distributions on all four servers) is the proof that the rubric, not the override machinery, now decides bands. The blast floor has been demoted to a within-band numeric nudge — exactly where an override belongs.
- **Restore an auditable value primitive — SATISFIED.** `asset_sensitivity` is back as an explicit per-asset integer sourced from the org's own table (`sensitivity_source: org_profile`), identical in both arms I checked (16/16 assets), and `ProfileCoverageError` aborts on gaps rather than guessing. This is the auditable number desc buried in prose.
- **Rerun stability — SATISFIED, and it retroactively upgrades the ablations.** I ran `cmp` myself: the two pure runs are bit-identical across the full JSON, all 208 cells. More important than the k question: determinism means identical inputs give identical outputs, so **every delta between ablation arms is now 100% attributable to the lever** — the comparison doc's caveat that "part of each arm's drift is rescan variance" is actually too modest; under greedy decoding there is no variance term. The 87%/92%/83% numbers are clean lever effects. k=2 is sufficient to demonstrate determinism *in this environment*; it does not need to be k=10.
- **Single-lever ablations — SATISFIED for _tools and _leanimp.** I verified base, _tools, and _leanimp share the same profile hash — genuinely one lever each. Rejecting _tools on the hub-critical demotion and _struct on systematic drift, and keeping base over _leanimp on simplicity at 92%, is honest adjudication with pre-stateable criteria.
- **Hash the profile input — HALF.** `profile_sha256` is in every artifact and I verified the current calendar profile hashes to the recorded value. But `git status` says `server-profiles.md`, `mcp-profile-spec.md`, `scan_pure_desc.py`, and both pure artifact directories are all **untracked (`??`)**. A hash whose preimage exists only in a working tree is provenance on a post-it. Commit them; this is one command.

**Still open:**
1. **The 95.5% is not single-lever attributable.** Pure records a different profile hash than the ult base it is compared against — the profile was edited between the two runs, so the comparison confounds the registry-construction lever with a profile revision. Determinism makes the fix nearly free: re-run ult base on the current profile and re-measure. Also, 64/67 excludes the 14 cells that changed scored↔N/A status; counting N/A agreement over all 208 cells gives 191/208 = **91.8%**, which is the honest headline. Still good — but report that one.
2. **Transfer.** Pure ran on calendar only — one server, the same one every hypothesis was developed on. The claim "the profile spec is sufficient input" is n=1; slack/github/fs profiles exist and the scan is deterministic and cheap. Finance remains untouched across all seven rounds.
3. **Input-perturbation robustness.** Determinism answers "same input, same output"; the operationally relevant question is now "how much does a one-word profile edit move?" — the hash-mismatch between arms shows edits happen. Unmeasured.
4. **Value-leak quantification** — never run as asked (regress blast on sensitivity at fixed coverage). Restoring sensitivity as an explicit primitive and the gate-grid's band-nullity lower the stakes considerably, but "blast is now a pure reach measure" remains asserted, not shown.
5. **External oracle** — still no independent panel pricing any of these bands; every criterion in seven rounds has been internal. The desc-with-sens vs desc-no-sens contrast is approximated by ult-vs-desc grid rows but with sens-source uncontrolled, so the 2x2 is populated, not designed.

**Verdict (2-3 sentences, in persona):** For the first time in this bake-off I can re-derive the result instead of taking its word: the primitive is a logged number from a hashed document, the bands come from a written function, the ablation deltas are — by verified determinism — pure lever effects, and I confirmed the bit-identity claim with my own `cmp`. The remaining sins are of omission, not construction: the hashed inputs sit uncommitted in the working tree, the flagship 95.5% quietly spans a profile edit and an N/A migration that shave it to 91.8%, and calendar remains the only server pure has ever seen. Commit the profiles, re-run the base on the current hash, and take pure to a server it wasn't raised on — this is the first candidate whose flaws are a to-do list rather than a design.

---

## Ingrid Halvorsen (audit) — final round: pure ult

**Score (0-10):** 9

**All-time ranking:** 1st **pure ult (9)**, 2nd floor-gated (9), 3rd floor-plain (8), 4th rowfix (5), 5th desc (4), 6th ctx (2). Pure ult edges floor-gated for first despite the equal number: floor-gated was a deterministic patch over a frozen baseline; pure ult is a deterministic *system* — same guarantee, generalized, with the inputs finally under evidence. I verified the determinism claim myself rather than taking the submission's word: `five_level_v2_pure` vs `five_level_v2_pure_rerun`, calendar_real.json and the 208-row matrix CSV, byte-for-byte identical.

**Now certifiable:** (1) The asset-value primitive — restored as a logged, per-row column sourced from the org's own table, never model-scored, with `ProfileCoverageError` aborting and naming missing ids rather than guessing; this closes the desc regression in full. (2) The artifact hash chain — `profile_sha256` of the exact text the model saw, plus the assembly audit trail (`blast_radius_raw`, `alias_fixups`, `blast_floor`); any changed cell now traces to a named input or a written rule. (3) The band rule — `band_label_v5`, deterministic and sensitivity-aware, the floor-gated guarantee generalized; I ratify it. (4) Rerun stability of this configuration on calendar_real — 208/208 cells bit-identical, verified by my own diff, not the submitter's. (5) Profile governance *structure* — spec v1 with Owner, Provenance, Content unit, absolute sensitivity anchors, and the calendar_real section conforms.

**Remaining conditions:** (1) **The scoring input is an untracked file.** `git status` returns `??` for server-profiles.md — no commit history, no CODEOWNERS, no enforced sign-off. An Owner line in prose is a declaration; version control is a control. This was my named condition last round and it is still open — I certify the configuration, not the change-control process, until that file is committed with mandatory review on edits. (2) Artifacts should carry run metadata (timestamp, run id, model endpoint): identical outputs are consistent with either deterministic execution or a cached replay, and I want the independence of the two runs attestable from the artifacts alone. (3) Stability is evidenced on one server; run the two-scan comparison on the remaining ult servers before fleet-wide certification. (4) Reconcile the documentation contradiction I found: the spec's implementation-status table says the skeleton emitter is "not built" and Contents/flags are "specified only," while server-profiles.md states the Contents facts were generated by `emit_profile_skeleton.py` and the pure run consumed the L3 grammar — one of these is stale, and a stale status table in a governance spec is itself a finding. (5) Build or formally descope the unimplemented validators (public-conflict is listed as an error-severity check; only coverage is enforced today).

**Verdict (2-3 sentences, in persona):** For three rounds I have asked for the same four things — a logged asset-value number I can challenge, outputs that do not drift on unchanged inputs, a hash of what the model actually read, and a band rule a committee can ratify — and pure ult is the first candidate to deliver all four at once; I diffed the two runs myself and found not one differing byte across 208 cells. What remains is not engineering but housekeeping with teeth: the document that now sets production risk scores is sitting untracked in the working directory, which means the finest hash chain in this bake-off terminates in a file with no history. Commit it, put an owner's signature between it and every future edit, and I will sign the ten.
