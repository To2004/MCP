# Scan — sqlite:cbg

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_na · bands={'low': 3, 'medium': 13, 'high': 24, 'critical': 1, 'na': 14}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Tables within the CBG database containing various types of records and metadata.
- **blast_radius_meaning**: The extent to which a tool can affect rows or columns across one or more tables, from modifying a single row to affecting all rows in multiple related tables.
- **dangerous_classes**: Holds PII at scale, Is executable, Involves financial transactions
- **irreversible_actions**: Deletes rows from a table, Inserts rows into tables that cannot be rolled back
- **worked_example**: write_query on employees: A DELETE query can remove employee records, which is severe if not recoverable.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 2 |
| `describe_table` | 2 |
| `read_query` | 3 |
| `write_query` | 5 |
| `insert_row` | 4 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `employees` | 4 |
| `projects` | 3 |
| `datasets` | 5 |
| `experiments` | 3 |
| `publications` | 3 |
| `grants` | 4 |
| `api_keys` | 5 |
| `table-catalog` | 2 |
| `table-metadata` | 3 |
| `database-records` | 3 |
| `table-records` | 4 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_na, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 24 (4×2×3) 🟢 | 80 (4×4×5) 🟠 | 16 (4×1×4) 🟢 |
| `projects` | N/A | 24 (3×4×2) 🟢 | 18 (3×2×3) 🟢 | 60 (3×4×5) 🟡 | 12 (3×1×4) 🟢 |
| `datasets` | 10 (5×1×2) 🟢 | 20 (5×2×2) 🟢 | 30 (5×2×3) 🟢 | 100 (5×4×5) 🔴 | 20 (5×1×4) 🟢 |
| `experiments` | 6 (3×1×2) 🟢 | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 60 (3×4×5) 🟡 | 12 (3×1×4) 🟢 |
| `publications` | N/A | 24 (3×4×2) 🟢 | 27 (3×3×3) 🟢 | 60 (3×4×5) 🟡 | 12 (3×1×4) 🟢 |
| `grants` | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 24 (4×2×3) 🟢 | 80 (4×4×5) 🟠 | 16 (4×1×4) 🟢 |
| `api_keys` | 10 (5×1×2) 🟢 | 10 (5×1×2) 🟢 | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 20 (5×1×4) 🟢 |
| `table-catalog` | 8 (2×2×2) 🟢 | N/A | 24 (2×4×3) 🟢 | N/A | N/A |
| `table-metadata` | N/A | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A |
| `database-records` | N/A | N/A | 18 (3×2×3) 🟢 | N/A | N/A |
| `table-records` | N/A | N/A | 24 (4×2×3) 🟢 | 80 (4×4×5) 🟠 | 16 (4×1×4) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 1 | 1 | 2 | 4 | 1 |
| `projects` | N/A | 4 | 2 | 4 | 1 |
| `datasets` | 1 | 2 | 2 | 4 | 1 |
| `experiments` | 1 | 1 | 2 | 4 | 1 |
| `publications` | N/A | 4 | 3 | 4 | 1 |
| `grants` | 1 | 1 | 2 | 4 | 1 |
| `api_keys` | 1 | 1 | 5 | 5 | 1 |
| `table-catalog` | 2 | N/A | 4 | N/A | N/A |
| `table-metadata` | N/A | 1 | 2 | N/A | N/A |
| `database-records` | N/A | N/A | 2 | N/A | N/A |
| `table-records` | N/A | N/A | 2 | 4 | 1 |

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
