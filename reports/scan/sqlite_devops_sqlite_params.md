# Parameter rubric — sqlite:devops_sqlite

LLM-derived per `docs/standards/parameter-scoring.md`. Each row is a magnitude-bearing input parameter and how its value bands.

## `read_query`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `sql` | medium | parsed_limit | ≥100→low · ≥500→medium · ≥1000→high |

## `write_query`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `sql` | high | parsed_limit | ≥100→low · ≥1000→medium · ≥5000→high |

## `insert_row`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `values` | low | parsed_limit | ≥1→low |

