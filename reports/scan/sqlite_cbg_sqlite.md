# Scan — sqlite:cbg_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · bands={'low': 6, 'medium': 13, 'high': 11, 'critical': 5}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables containing various types of records such as employee information, projects, datasets, experiments, publications, grants, and API keys.
- **blast_radius_meaning**: The extent to which a tool can affect the data within an asset. A narrow touch might involve reading or modifying a single row, while reaching far could mean altering multiple rows or even deleting entire tables.
- **worked_example**: The 'write_query' tool paired with the 'api_keys' asset is highly severe because it can modify or delete sensitive API keys, which are critical for securing access to various services.

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
| `employees` | 4 |
| `projects` | 4 |
| `datasets` | 5 |
| `experiments` | 3 |
| `publications` | 2 |
| `grants` | 5 |
| `api_keys` | 5 |

## Risk matrix (score · band)

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 8 🟡 | 8 🟡 | 8 🟠 | 36 🔴 | 16 🟡 |
| `projects` | 12 🟠 | 4 🟢 | 8 🟡 | 36 🔴 | 16 🟠 |
| `datasets` | 15 🟠 | 5 🟡 | 10 🟠 | 45 🔴 | 20 🟡 |
| `experiments` | 9 🟡 | 9 🟡 | 9 🟡 | 27 🟠 | 12 🟢 |
| `publications` | 2 🟢 | 2 🟢 | 4 🟡 | 18 🟠 | 8 🟡 |
| `grants` | 15 🟠 | 5 🟢 | 10 🟠 | 45 🔴 | 20 🟡 |
| `api_keys` | 5 🟢 | 10 🟡 | 10 🟠 | 60 🔴 | 30 🟠 |
