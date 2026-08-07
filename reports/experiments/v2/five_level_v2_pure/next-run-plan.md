# Pure run — audit findings and the plan for the next run (NOT yet run)

## Finding 1 — asset sensitivity IS used; it just has different values now

Verified from the artifact: the matrix's `sensitivity` column is populated and
every score is `sens × blast × impact` (e.g. `personal,delete-event` = 3×1×5 =
15). What changed is the SOURCE: the old `five_level_v2_fs` run had the LLM
guess sensitivities; pure takes them from the org table. The LLM systematically
guessed HIGHER on 12 of 16 assets (personal 4→3, recruiting 5→4, contacts 5→4,
free-busy 5→3, rsvp-state 4→2, color-catalog 3→1, …) and LOWER on one
(connected-account-config 4→5). This single change explains most of the score
drop vs the fs experiment — the org's own numbers are simply less inflated. If
any org value looks wrong, the fix is editing the table row, not the scanner.

## Finding 2 — why pure differs from five_level_v2_fs calendar (all six deltas)

| # | delta | fs baseline | pure |
|---|---|---|---|
| 1 | sensitivity source | LLM stage (inflated) | org table (logged) |
| 2 | asset registry | demo scopes + LLM-generated homing assets | the profile table rows (Contents+Why as descriptions) |
| 3 | prompt preamble | inferred domain profile only | org description + inferred profile in every stage |
| 4 | blast prompt | plain coverage+N/A | + "sensitivity supplied separately, blast = pure reach" note |
| 5 | deterministic assembly | none | alias-twin pass + gated blast floor (raw preserved) |
| 6 | band function | band_label (calibrated for impact 1-3 — miscalibrated for the 5-ladder) | band_label_v5 (sens-aware irreversibility floors) |

Inputs to pure (verified, recorded as `registry_source`):
`reports/tool_lists/calendar_real.json` + the `calendar_real` profile section —
nothing else. Prompts that actually ran are dumped verbatim in
`scoring-prompts.md` (4 LLM stages: domain inference, impact ×13, blast ×208,
baseline ×1; sensitivity/floors/alias/bands are code, not prompts).

## Finding 3 — the gaps spotted are real

1. **No plural/bulk dominance rule.** `create-events` (bulk, "skips conflict
   and duplicate detection") got impact 5 in the fs run but 4 in this run —
   equal to singular `create-event`. On personal/team the model gave the bulk
   verb higher blast (3 vs 1), but on executive/recruiting the sens-4 floor
   raised the singular to 3 too, ERASING the bulk distinction. Same class of
   bug in fs: `read_multiple_files` blast 2 < `read_file` blast 5 on payslips —
   the batch verb priced BELOW the single read.
2. **No impact-keyed blast minimum.** The floors are keyed on sensitivity only
   ({sens5→b≥4, sens4→b≥3}, gate impact≥4). Nothing says "impact 5 implies
   blast ≥ N" — destruction can sit at blast 1.
3. **The rules are invisible in the outputs.** The floor/alias/band rules live
   in the JSON (`blast_floor`, `alias_fixups`) and code docstrings, but the
   human-readable .md and scoring-prompts.md do not state them.

## Plan for the next run (v3 — awaiting go-ahead)

1. **Bulk-twin dominance pass** (deterministic, next to the alias pass):
   detect bulk variants of a singular tool — name pluralization
   (`create-event`/`create-events`), `multiple|bulk|batch` in name, or an
   array-typed primary parameter — and enforce per asset:
   `impact(bulk) ≥ impact(singular)` and `blast(bulk) ≥ blast(singular)`;
   when the floors make them equal, bump the bulk blast +1 (cap 5) so one call
   that writes many items always prices above one that writes one. This also
   fixes the `read_multiple_files` inversion. Logged like alias_fixups.
2. **Impact-keyed floor row**: extend the floor table with an impact axis —
   proposal: impact 5 → blast ≥ 2 regardless of sensitivity (destruction is
   never a pinpoint *consequence*), keeping the existing sens-keyed mins.
3. **Band seam decision** (needs the user's call — the two judges pull in
   opposite directions):
   - Option A (Raven): `sens ≥ 4 ∧ impact ≥ 4 → at least high` (closes
     payslips-move 48-medium, audit-log-edit 48-medium, recruiting-create
     48-medium).
   - Option B (Moss): additionally demote `impact 5 ∧ sens ≤ 3 ∧ blast = 1`
     from high to medium (silences known_defects/db_schema 15-highs).
   - A and B are compatible; adopting both shifts the seam exactly once.
4. **Rules visibility**: emit a "Deterministic rules applied" section into
   every scan .md and the prompts dump (floor table, gate, alias/bulk twins,
   band clause list).
5. **Input manifest**: record the tool-catalog sha256 next to profile_sha256
   so BOTH inputs are hashed in the artifact.
6. Re-run pure calendar with 1-2-4-5 (+3 as decided), diff against this run —
   determinism means every changed cell is attributable to the new rules.
