# v4 — shorter, standards-grounded prompts (DESIGN ONLY — not run)

Nothing in this folder has been executed. It is the proposal to read and approve
before spending a GPU run.

## What v4 changes

1. **Rewrite both scoring prompts against published standards** instead of
   hand-grown prose — CVSS v4.0's vulnerable-vs-subsequent system split for
   blast, the MCP tool-annotation vocabulary for impact. Impact drops 84 % in
   size, blast 70 %. See [`scoring-prompts.md`](scoring-prompts.md) for the full
   proposed text and the source list.
2. **Tool impact stops receiving the description.** Inputs become the tool JSON
   alone — no org profile, no inferred domain profile. Justified by the v3
   `imponly` arm: withholding the asset table left 12 of 13 impacts identical.
3. **Blast radius receives everything**, plus the sibling tool and asset lists so
   reach is judged comparatively rather than one blind cell at a time.
4. **A tier-5 blast now requires a flag in the org table** (`hub`, `population`,
   `self-sufficient`). Prose adjectives can no longer open an escape route —
   the deterministic fix for `recruiting|list-events = 5`.

## Why (evidence from earlier generations)

| Finding | Where | Consequence for v4 |
|---|---|---|
| Impact ignores the asset table | v3 `five_level_v2_pure_imponly` — 12/13 impacts unchanged | remove the description from the impact stage |
| Prose drives blast over-reads | v3 `terse` arm fixed `recruiting` 5→4 by removing prose only | tier-5 must be flag-sanctioned |
| Same tool, same sensitivity, blast 1 vs 5 | v3 audit (20 tools on fs, 12 on github, 7 on slack) | give blast the sibling lists + a consistency rule |
| Prompts are long | impact 6 484 chars, blast 8 099 chars | rewrite against standards; cut examples |

## Files

| File | What |
|---|---|
| `scoring-prompts.md` | **the proposal** — both new prompts verbatim, the source list, and a line-by-line diff of what was cut |
| `inputs/calendar_real.tools.json` | the tool catalog this run would consume |
| `inputs/calendar_real.profile.md` | the org profile this run would consume |
| `reference/v3-scoring-prompts-CURRENT.md` | the prompts that produced the v3 results, preserved for comparison |

## Open questions to settle before running

1. **Bulk severity.** With the description gone from the impact stage, does
   `create-events` still reach 5? The v3 `imponly` arm says it falls to 4 and the
   deterministic bulk rule catches it — acceptable, but confirm you want the
   floor doing that work rather than the prompt.
2. **Blast ceiling of 4 without a flag** is stricter than v3. `contacts` and
   `event-attendee-lists` carry `population`, so they can still reach 5; every
   other calendar asset is capped at 4. Check that matches your intent.
3. **Sibling lists cost tokens** — 13 tool names + 16 asset ids per blast call on
   calendar, more on github (26 tools). Cheap here, worth watching on bigger
   servers.
4. The v3 audit's other open items are unchanged and independent of this
   proposal: the dead assets (`contacts`, `outbound-invite-email`,
   `message-reactions` are never touched by any tool) and the uncovered
   `get-current-time`.

## If approved, the run would be

```
sbatch --job-name=mcp-v4 --export=ALL,MODE=five_level_v2_v4,ONLY=calendar_real,\
OUT_DIR=<repo>/reports/experiments/v4/five_level_v2_v4 scripts/scan_pure.sbatch
```

…after the new prompts are wired as a new impact mode. Comparison target:
`v3/five_level_v2_pure_v3/calendar_real.json` (same inputs, same deterministic
rules, so every difference is attributable to the prompts).
