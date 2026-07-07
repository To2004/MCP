# Scan — sqlite:devops_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · bands={'low': 4, 'medium': 7, 'high': 12, 'critical': 2}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables containing various types of data such as user information, API tokens, deployment records, audit logs, and public metrics.
- **blast_radius_meaning**: The extent to which a tool can affect the integrity or confidentiality of assets. A narrow touch might involve reading from a single table, while severe actions could include modifying critical tables that hold sensitive information.
- **worked_example**: The 'write_query' tool paired with the 'users' asset could lead to severe consequences if used to delete or modify user records, as it impacts sensitive PII data.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 1 |
| `write_query` | 3 |
| `insert_row` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `users` | 5 |
| `api_tokens` | 4 |
| `deployments` | 3 |
| `audit_log` | 4 |
| `public_metrics` | 1 |

## Risk matrix (score · band)

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `users` | 20 🟠 | 20 🟠 | 20 🟠 | 60 🔴 | 20 🟠 |
| `api_tokens` | 16 🟠 | 16 🟠 | 16 🟠 | 48 🔴 | 16 🟡 |
| `deployments` | 12 🟡 | 12 🟡 | 12 🟡 | 27 🟠 | 12 🟡 |
| `audit_log` | 16 🟠 | 16 🟠 | 16 🟠 | 36 🟠 | 16 🟡 |
| `public_metrics` | 4 🟢 | 4 🟢 | 4 🟢 | 9 🟡 | 4 🟢 |

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
