# Evaluation ground truth — cbg_sqlite

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | cbg_sqlite |
| server | cbg-sqlite-server |
| mcp_kind | SQL database |
| version | static-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 18, 'medium': 10, 'high': 6, 'critical': 1} |
| judge_ran | True |
| judge_overrides | 6 |

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables containing various types of records such as employee information, projects, datasets, experiments, publications, grants, and API keys.
- **blast_radius_meaning**: The extent to which a tool can affect the data within an asset. A narrow touch might be reading from one table, while the most severe action could involve deleting or modifying critical data across multiple tables.
- **worked_example**: The 'write_query' tool paired with the 'api_keys' asset is highly severe because it can modify or delete sensitive API keys, which are critical for securing access to various services.
- **dangerous_classes**: holds secrets, holds PII at scale, is executable
- **irreversible_actions**: deletes, executes code, transfers funds, sends external messages

### Tool impact (1 read · 2 recoverable · 3 destructive)

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 1 |
| `write_query` | 3 |
| `insert_row` | 2 |

### Asset sensitivity (1 low – 5 crown-jewel)

| asset | sensitivity |
| --- | --- |
| `employees` | 4 |
| `projects` | 4 |
| `datasets` | 3 |
| `experiments` | 3 |
| `publications` | 2 |
| `grants` | 4 |
| `api_keys` | 5 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 16 🟡 |
| `projects` | 4 🟢 | 4 🟢 | 4 🟢 | 36 🟠 | 16 🟡 |
| `datasets` | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 12 🟡 |
| `experiments` | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 12 🟡 |
| `publications` | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 8 🟡 |
| `grants` | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 16 🟡 |
| `api_keys` | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 30 🟠 |
