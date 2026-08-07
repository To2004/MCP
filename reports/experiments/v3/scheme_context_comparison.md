# Description context & scheme experiments — calendar (roof-free)

How much of the org profile does the scanner actually need? Four arms over the
same tool catalog + calendar profile, **roof disabled** so the effect is the
description alone. All are the `five_level_v2_ult` v3 machinery (bulk rules +
floors); only what the model SEES of the profile changes.

| arm | what the model sees | na | low | medium | high | critical |
|---|---|---|---|---|---|---|
| **full** (baseline) | whole profile: prose + table + flags | 134 | 19 | 43 | 10 | 2 |
| noflags | profile with the 6 judgement flags stripped | 134 | 19 | 44 | 9 | 2 |
| terse | fact line + Asset/Sens/shape+flags table, NO prose | 112 | 19 | 65 | 11 | 1 |
| rich | full profile + the whole tool registry in every prompt | 132 | 19 | 45 | 10 | 2 |

## Findings

**1. The recruiting over-read is caused by PROSE, not flags.**
`recruiting|list-events` blast: full 5 · noflags 5 · **terse 4** · rich 4. Removing
the flags left it at 5; removing the *prose* ("candidate identities and pending
moves") dropped it to 4. The model was inferring a population-disclosure escape
from a sentence. Confirms the earlier catch — a read of the recruiting calendar
is total-but-contained (4), not systemic (5), since recruiting carries no
population flag.

**2. Less context HELPS blast but HURTS tool impact and relevance.**
- Blast: terse removed the prose that caused the population over-read.
- Tool impact: `create-events` fell 5 → 4 under terse — the model needed the
  profile context to rate the bulk tool high (whether 5 or 4 is correct for a
  *recoverable* bulk-create is itself arguable).
- Relevance (N/A): terse scored 22 MORE cells (na 134 → 112, medium 43 → 65) —
  with sparse asset descriptions the model could not tell which tools do NOT
  touch an asset, so it over-covered.

**3. Flags barely moved calendar** (noflags ≈ full) — even the hub-critical
`manage-accounts|connected-account-config` (125) survived without the `hub`
flag, because the calendar prose already says "access hub for every calendar."
On a server whose prose is thinner, the flags would carry more.

**4. Rich (more context) ≈ full**, but it did fix recruiting to 4 and shaved two
N/A — a mild point for more context, not less.

## Verdict

"Less is better" does not hold uniformly. The description's PROSE is double-edged:
it supplies the context tool-impact and relevance need, but it also lets the
model over-infer blast escapes the flags don't sanction. The clean split is:
**keep the full profile for impact/relevance, and correct the prose-driven blast
over-reads with the deterministic roof** (which caps a non-escaping read at
blast 4 by rule) rather than by starving the description. Terse is the wrong
lever — it fixes one cell and breaks the N/A precision on twenty.
