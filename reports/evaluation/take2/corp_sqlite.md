# Evaluation ground truth — corp_sqlite

> Design-time reviewed risk table. **Used only to grade the scanner's output; the scanner never reads this file.**

## Server

| Field | Value |
| --- | --- |
| name | corp_sqlite |
| server | corp-sqlite-server |
| mcp_kind | SQL database |
| version | static-take2-2026-06-23 |
| model_reviewed | True |
| formula | `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact` |
| band_distribution | {'low': 15, 'medium': 7, 'high': 7, 'critical': 1} |
| judge_ran | True |
| judge_overrides | 8 |

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Database tables containing various types of data such as employee information, customer details, orders, API keys, and insights.
- **blast_radius_meaning**: The extent to which a tool can affect the data within an asset. A narrow touch might be reading from one table, while the most severe action could involve modifying or deleting records across multiple tables.
- **worked_example**: The 'write_query' tool paired with the 'api_keys' asset is highly severe because it can modify or delete sensitive API keys, which are critical for securing access to services.
- **dangerous_classes**: holds secrets, holds PII at scale, is executable
- **irreversible_actions**: deletes, executes code, transfers funds, sends external messages

### Tool impact (1 read · 2 recoverable · 3 destructive)

| tool | impact |
| --- | --- |
| `list_tables` | 1 |
| `describe_table` | 1 |
| `read_query` | 1 |
| `write_query` | 3 |
| `insert_row` | 3 |

### Asset sensitivity (1 low – 5 crown-jewel)

| asset | sensitivity |
| --- | --- |
| `employees` | 4 |
| `customers` | 4 |
| `orders` | 3 |
| `api_keys` | 5 |
| `insights` | 3 |
| `sqlite_sequence` | 2 |

## Risk matrix (score · band)

Band legend: 🟢 low · 🟡 medium · 🟠 high · 🔴 critical

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `employees` | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 36 🟠 |
| `customers` | 4 🟢 | 4 🟢 | 4 🟢 | 48 🟠 | 36 🟠 |
| `orders` | 3 🟢 | 3 🟢 | 3 🟢 | 36 🟠 | 18 🟡 |
| `api_keys` | 5 🟡 | 5 🟡 | 5 🟡 | 60 🔴 | 30 🟠 |
| `insights` | 3 🟢 | 3 🟢 | 3 🟢 | 27 🟠 | 18 🟡 |
| `sqlite_sequence` | 2 🟢 | 2 🟢 | 2 🟢 | 18 🟡 | 12 🟡 |
