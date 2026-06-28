# Parameter rubric — fs:law_firm_fs

LLM-derived per `docs/standards/parameter-scoring.md`. Each row is a magnitude-bearing input parameter and how its value bands.

## `read_file`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `tail` | medium | number | ≥10→low · ≥50→medium · ≥100→high |
| `head` | medium | number | ≥10→low · ≥50→medium · ≥100→high |

## `read_text_file`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `head` | medium | number | ≥10→low · ≥50→medium · ≥100→high |
| `tail` | medium | number | ≥10→low · ≥50→medium · ≥100→high |

## `read_multiple_files`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `paths` | medium | list_length | ≥1→low · ≥5→medium · ≥10→high · ≥20→critical |

## `write_file`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `content` | medium | length of the content string | ≥100→low · ≥1000→medium · ≥5000→high |

## `edit_file`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `edits` | medium | list_length | ≥1→low · ≥5→medium · ≥10→high · ≥20→critical |

## `list_directory_with_sizes`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `path` | low | null | — |

## `directory_tree`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `path` | low | null | — |
| `excludePatterns` | medium | length of the excludePatterns list | ≥0→low · ≥1→medium · ≥3→high |

## `search_files`

| parameter | base | extract | cutoffs |
| --- | --- | --- | --- |
| `pattern` | medium | parsed_limit | ≥100→low · ≥500→medium · ≥1000→high |
| `excludePatterns` | low | list_length | ≥1→low · ≥5→medium |

