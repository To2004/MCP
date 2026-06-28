# Parameter rubric — calendar:cbg

LLM-derived per `docs/standards/parameter-scoring.md`. Each row is a magnitude-bearing input parameter and how its value bands.

## `create_event`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `attendees` | medium | list_length | ≥3→low · ≥6→medium · ≥10→high · ≥20→critical |

## `update_event`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `attendees` | medium | list_length | ≥3→low · ≥7→medium · ≥11→high |
| `duration_min` | low | number | ≥30→low · ≥60→medium · ≥120→high |

## `send_email_invite`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `recipients` | medium | list_length | ≥1→low · ≥5→medium · ≥20→high · ≥50→critical |

