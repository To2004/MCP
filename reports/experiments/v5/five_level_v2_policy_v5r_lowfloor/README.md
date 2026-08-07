# v5r · `lowfloor` arm

Impact mode `five_level_v2_v5r_lowfloor`. Everything about the method — the scoring formula, the static impact ladder, what each prompt is for, and the standards the rubrics are grounded in — is shared with every other arm and documented once, one level up:

- [`../README.md`](../README.md)
- [`../STATIC_RULES.md`](../STATIC_RULES.md)
- [`../PROMPT_ROLES.md`](../PROMPT_ROLES.md)
- [`../GROUNDING.md`](../GROUNDING.md)

The prompts **as this arm actually ran them** are in [`scoring-prompts-AS-RUN.md`](scoring-prompts-AS-RUN.md) in this folder.

## What this arm changes

| option | value | what it means |
|---|---|---|
| `asset_flags` | `none` | the register's `Flags` column is withheld — the model reads the tool's own parameters and the policy prose instead |
| `blast_prompt` | `selfassess` | the blast prompt asks the flag *concepts* as questions (hub? population? self-sufficient?) without ever naming a flag |
| `floors` | `low` | the sensitivity/impact floors are each lowered by one, and anything that would land below 3 is dropped |

## Contents

| file | what it holds |
|---|---|
| `<server>.json` | the full artifact: every primitive, its reasoning, and its provenance |
| `<server>.md` | the same scan as a readable report |
| `<server>_matrix.csv` | the tool × asset score matrix |
| `scoring-prompts-AS-RUN.md` | every prompt this arm sent, rendered |

