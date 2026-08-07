# Scan — sqlite:cbg_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 8, 'medium': 16, 'high': 6, 'critical': 6, 'na': 19}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Tables within the CBG research-arm database containing information about employees, projects, datasets, experiments, publications, grants, and API keys.
- **blast_radius_meaning**: The extent to which a tool can affect records across different tables. A narrow touch affects only specific rows or columns in one table, while the most severe action could impact multiple tables and their contents.
- **dangerous_classes**: contains secrets, holds PII at scale, is pre-publication IP
- **irreversible_actions**: write_query, insert_row
- **worked_example**: The 'write_query' tool on the 'api_keys' asset could severely impact confidentiality by modifying or deleting API keys, which are critical for secure access.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 2 |
| `describe_table` | 2 |
| `read_query` | 3 |
| `write_query` | 5 |
| `insert_row` | 4 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 11 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `employees` | — |
| `projects` | — |
| `datasets` | — |
| `experiments` | — |
| `publications` | — |
| `grants` | — |
| `api_keys` | — |
| `table-catalog` | — |
| `table-metadata` | — |
| `database-records` | — |
| `table-records` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | N/A | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 20 (4×5) 🔴 | 8 (2×4) 🟡 |
| `projects` | N/A | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 15 (3×5) 🟠 | 4 (1×4) 🟢 |
| `datasets` | N/A | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 15 (3×5) 🟠 | 4 (1×4) 🟢 |
| `experiments` | N/A | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 20 (4×5) 🔴 | 4 (1×4) 🟢 |
| `publications` | N/A | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 15 (3×5) 🟠 | 4 (1×4) 🟢 |
| `grants` | N/A | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 20 (4×5) 🔴 | 4 (1×4) 🟢 |
| `api_keys` | N/A | 2 (1×2) 🟢 | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 8 (2×4) 🟡 |
| `table-catalog` | 2 (1×2) 🟢 | N/A | N/A | N/A | N/A |
| `table-metadata` | 4 (2×2) 🟢 | 4 (2×2) 🟢 | N/A | N/A | N/A |
| `database-records` | N/A | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | N/A |
| `table-records` | N/A | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 4 (1×4) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | N/A | 1 | 3 | 4 | 2 |
| `projects` | N/A | 1 | 3 | 3 | 1 |
| `datasets` | N/A | 1 | 3 | 3 | 1 |
| `experiments` | N/A | 1 | 3 | 4 | 1 |
| `publications` | N/A | 1 | 2 | 3 | 1 |
| `grants` | N/A | 1 | 2 | 4 | 1 |
| `api_keys` | N/A | 1 | 5 | 5 | 2 |
| `table-catalog` | 1 | N/A | N/A | N/A | N/A |
| `table-metadata` | 2 | 2 | N/A | N/A | N/A |
| `database-records` | N/A | N/A | 5 | 5 | N/A |
| `table-records` | N/A | N/A | 5 | 5 | 1 |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `list_tables` | **LIST** | 1 (Low) | LIST | rules |
| `describe_table` | **METADATA** | 1 (Low) | METADATA | rules |
| `read_query` | **READ** | 2 (Low) | READ | rules |
| `write_query` | **EXECUTE** | 5 (Critical) | DELETE, EXECUTE, OVERWRITE, SCHEMA_MODIFY, WRITE | rules |
| `insert_row` | **WRITE** | 3 (Medium) | WRITE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `describe_table` | `table` | 2 | — | merely names the target |
| `read_query` | `sql` | 5 | null | fully controllable free-form query |
| `write_query` | `sql` | 5 | — | fully controllable query with potential for bulk operations |
| `insert_row` | `values` | 5 | — | fully controlled payload by caller |
| `insert_row` | `table` | 2 | — | merely names the target |
