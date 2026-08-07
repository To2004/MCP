# Scan — sqlite:cbg

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=hybrid · bands={'low': 4, 'medium': 16, 'high': 15, 'critical': 0, 'na': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Tables within a relational database system
- **blast_radius_meaning**: The extent of data affected by an operation; from modifying a single row to affecting multiple rows across one or more tables.
- **dangerous_classes**: Holds sensitive information like PII, Is executable, Involves financial transactions
- **irreversible_actions**: Deleting rows from critical tables, Inserting incorrect data into key tables
- **worked_example**: The 'write_query' tool paired with the 'api_keys' asset can severely impact security if used to delete or modify API keys, escalating severity due to potential unauthorized access.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 2 |
| `write_query` | 4 |
| `insert_row` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `employees` | 4 |
| `projects` | 4 |
| `datasets` | 4 |
| `experiments` | 3 |
| `publications` | 3 |
| `grants` | 4 |
| `api_keys` | 5 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=hybrid, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 40 (4×2×2) 🟡 | 69.28 (4×3×4) 🟠 | 34.64 (4×1×3) 🟡 |
| `projects` | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 40 (4×2×2) 🟡 | 69.28 (4×3×4) 🟠 | 34.64 (4×1×3) 🟡 |
| `datasets` | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 40 (4×2×2) 🟡 | 80 (4×4×4) 🟠 | 34.64 (4×1×3) 🟡 |
| `experiments` | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 30 (3×2×2) 🟢 | 60 (3×4×4) 🟡 | 25.98 (3×1×3) 🟢 |
| `publications` | 15 (3×1×1) 🟢 | 15 (3×1×1) 🟢 | 30 (3×2×2) 🟢 | 60 (3×4×4) 🟡 | 25.98 (3×1×3) 🟢 |
| `grants` | 20 (4×1×1) 🟢 | 20 (4×1×1) 🟢 | 40 (4×2×2) 🟡 | 80 (4×4×4) 🟠 | 34.64 (4×1×3) 🟡 |
| `api_keys` | 25 (5×1×1) 🟢 | 25 (5×1×1) 🟢 | 50 (5×2×2) 🟡 | 111.8 (5×5×4) 🔴 | 43.3 (5×1×3) 🟡 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 1 | 1 | 2 | 3 | 1 |
| `projects` | 1 | 1 | 2 | 3 | 1 |
| `datasets` | 1 | 1 | 2 | 4 | 1 |
| `experiments` | 1 | 1 | 2 | 4 | 1 |
| `publications` | 1 | 1 | 2 | 4 | 1 |
| `grants` | 1 | 1 | 2 | 4 | 1 |
| `api_keys` | 1 | 1 | 2 | 5 | 1 |

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
