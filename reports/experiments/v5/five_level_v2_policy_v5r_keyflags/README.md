# v5r · `keyflags` arm

Impact mode `five_level_v2_v5r_keyflags`. Everything about the method — the scoring formula, the static impact ladder, what each prompt is for, and the standards the rubrics are grounded in — is shared with every other arm and documented once, one level up:

- [`../README.md`](../README.md)
- [`../STATIC_RULES.md`](../STATIC_RULES.md)
- [`../PROMPT_ROLES.md`](../PROMPT_ROLES.md)
- [`../GROUNDING.md`](../GROUNDING.md)

The prompts **as this arm actually ran them** are in [`scoring-prompts-AS-RUN.md`](scoring-prompts-AS-RUN.md) in this folder.

## What this arm changes

| option | value | what it means |
|---|---|---|
| `asset_flags` | `key` | only the flags judged important are shown; the rest are withheld |

## Contents

| file | what it holds |
|---|---|
| `<server>.json` | the full artifact: every primitive, its reasoning, and its provenance |
| `<server>.md` | the same scan as a readable report |
| `<server>_matrix.csv` | the tool × asset score matrix |
| `scoring-prompts-AS-RUN.md` | every prompt this arm sent, rendered |

