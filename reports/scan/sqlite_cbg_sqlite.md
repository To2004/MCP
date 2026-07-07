# Scan — sqlite:cbg_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · bands={'low': 0, 'medium': 15, 'high': 20, 'critical': 0}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables containing various types of records such as employee information, projects, datasets, experiments, publications, grants, and API keys.
- **blast_radius_meaning**: The extent to which a tool can affect the data within an asset. A narrow touch might involve reading or modifying specific rows, while reaching far could mean altering entire tables or executing queries that impact multiple records across different tables.
- **worked_example**: The 'write_query' tool paired with the 'api_keys' asset is highly severe because it can modify or delete sensitive API keys, which are critical for securing access to various services.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 1 |
| `write_query` | 2 |
| `insert_row` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `employees` | 4 |
| `projects` | 4 |
| `datasets` | 4 |
| `experiments` | 3 |
| `publications` | 2 |
| `grants` | 4 |
| `api_keys` | 5 |

## Risk matrix (score · band)

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟡 |
| `projects` | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟡 |
| `datasets` | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟡 |
| `experiments` | 12 🟡 | 12 🟡 | 12 🟡 | 18 🟡 | 12 🟡 |
| `publications` | 8 🟡 | 8 🟡 | 8 🟡 | 12 🟡 | 8 🟡 |
| `grants` | 16 🟠 | 16 🟠 | 16 🟠 | 24 🟠 | 16 🟡 |
| `api_keys` | 20 🟠 | 10 🟡 | 20 🟠 | 40 🟠 | 20 🟠 |

## Tool atomic operations

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
