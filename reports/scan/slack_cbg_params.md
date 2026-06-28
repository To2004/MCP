# Parameter rubric — slack:cbg

LLM-derived per `docs/standards/parameter-scoring.md`. Each row is a magnitude-bearing input parameter and how its value bands.

## `slack_get_channel_history`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `limit` | medium | number | ≥10→low · ≥50→medium · ≥100→high |

