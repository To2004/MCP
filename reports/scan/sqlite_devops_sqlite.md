# Scan — sqlite:devops_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · bands={'low': 8, 'medium': 5, 'high': 9, 'critical': 3}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables that store various types of data such as user information, API tokens, deployment records, audit logs, and public metrics.
- **blast_radius_meaning**: The extent to which a tool can affect the integrity or confidentiality of assets. A narrow touch might involve reading from a single table, while severe actions could include modifying critical tables that hold sensitive information.
- **worked_example**: The 'write_query' tool paired with the 'users' asset class could severely impact security if used to update or delete sensitive user information.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 1 |
| `write_query` | 3 |
| `insert_row` | 3 |

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
| `users` | 10 🟡 | 5 🟢 | 15 🟠 | 60 🔴 | 30 🟠 |
| `api_tokens` | 4 🟢 | 4 🟢 | 8 🟠 | 48 🔴 | 36 🟠 |
| `deployments` | 9 🟡 | 3 🟢 | 9 🟡 | 36 🟠 | 18 🟠 |
| `audit_log` | 12 🟠 | 4 🟢 | 8 🟠 | 36 🔴 | 24 🟠 |
| `public_metrics` | 3 🟢 | 2 🟢 | 1 🟢 | 9 🟡 | 6 🟡 |
