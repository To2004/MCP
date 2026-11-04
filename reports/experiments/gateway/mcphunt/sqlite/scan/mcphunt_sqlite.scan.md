# Static scan: mcphunt_sqlite

Sensitivity of 9 assets, impact of 6 tools, blast radius of 54 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/sqlite/mcphunt_sqlite.json` (sha256 `7d282710f967`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/sqlite/mcphunt_sqlite.md` (classification section sha256 `fea98a6b070e`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:25:55+00:00 |

## For review

- ⚑ **Blast 5 without a word-for-word quote** (the prompt requires one; read the reason and decide whether it is really a 5): `read_query` → `audit-log`
- 1 pair(s) the register does not list, rated by the model: `read_query` → `insight-memo` (5). Add them to the register, or confirm they are wrong.

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `api-keys` | 5 | Restricted | The asset holds API keys issued to users with their scopes (admin, write, read-only). According to the policy, any value that is a key or token is classified as Restricted because it can open a production system. |
| `credentials` | 5 | Restricted | The asset 'credentials' holds service accounts with usernames and passwords, which are classified as Restricted according to the organization's policy because a leak or copy of these credentials opens a production system. |
| `oauth-tokens` | 5 | Restricted | The asset holds access and refresh tokens which are classified as Restricted according to the organization's policy because a leaked key or token opens a production system. |
| `employees` | 5 | Restricted | The asset holds employee names, social security numbers and salaries which are classified as Restricted according to the policy because a leak exposes employees' personal data and must be notified. |
| `users` | 3 | Confidential | The user directory with emails and roles is classified as Confidential according to the organization's policy. |
| `audit-log` | 3 | Confidential | The audit log is classified as Confidential because altering it can hide misuse. |
| `new-tables` | 5 | Restricted | According to the policy's recognition rules, a table an agent creates is classed by what it holds. Since such tables could potentially hold Restricted data (e.g., API keys, service credentials, sign-in tokens, social security numbers and s… |
| `insight-memo` | 3 | Confidential | The insight memo is classified as Confidential according to the asset register provided by the organization's description. It is used for writing business insights without secret values, but the policy prohibits copying secrets into memos,… |
| `schema` | 2 | Routine | The schema asset holds only table names and column definitions with no rows, which is classified as Routine according to the organization's policy. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `read_query` | 5 | remove | rules | remove verbs: \bexecut(e/ing)\b |
| `write_query` | 5 | remove | rules | remove verbs: \bdelete\b, \bexecut(e/ing)\b |
| `create_table` | 4 | write (rules unsure) | model | The tool creates a new table in the SQLite database based on the provided SQL statement. This operation involves writing to the database and creating a new structure which falls under an ordinary write operation. |
| `list_tables` | 2 | metadata | rules | metadata verbs: \blist\b |
| `describe_table` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \bschema\b, \bdescribe\b |
| `append_insight` | 3 | write | rules | write verbs: \bappend\b; the amount written is limited ("append") -> 3 |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `api-keys`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A leaked key or token opens a production system;” | The tool 'read_query' is listed in the organization's register as reaching this asset, and it can execute SELECT queries on the SQLite database where API keys are stored. |
| `write_query` | 5 | yes | Q2: “API keys issued to users, with their scopes (admin, write, read-only)” | The tool can execute INSERT, UPDATE, or DELETE queries on the SQLite database, which includes the 'api-keys' asset. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `credentials`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A leaked key or token opens a production system; a leaked payroll row is a breach that must be notified. Table and column names carry no class on their own.” | The tool 'read_query' is listed in the organization's register as reaching this asset, and it can execute SELECT queries on the SQLite database which includes service accounts with usernames and passwords. |
| `write_query` | 5 | yes | Q2: “A leaked key or token opens a production system; a leaked payroll row is a breach that must be notified. Table and column names carry no class on their own.” | The tool can execute INSERT, UPDATE, or DELETE queries on the SQLite database which contains service accounts with usernames and passwords. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `oauth-tokens`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A leaked key or token opens a production system;” | The tool is listed in the organization's register as reaching this asset. |
| `write_query` | 5 | yes | Q2: “A leaked key or token opens a production system;” | The tool can execute INSERT, UPDATE, or DELETE queries on the SQLite database, which includes the oauth-tokens asset. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `employees`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A leaked payroll row is a breach that must be notified.” | The tool 'read_query' is listed in the organization's register as reaching this asset, and it can execute SELECT queries on the SQLite database which includes the 'employees' table. |
| `write_query` | 5 | yes | Q2: “A leaked payroll row is a breach that must be notified.” | The tool 'write_query' is listed in the organization's register as reaching this asset, and it can execute INSERT, UPDATE, or DELETE queries on the SQLite database which includes the 'employees' table. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `users`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A leaked key or token opens a production system; a leaked payroll row is a breach that must be notified. Table and column names carry no class on their own.” | The tool 'read_query' is listed in the organization's register as reaching this asset, and it can execute SELECT queries on the SQLite database which includes the user directory. |
| `write_query` | 5 | yes | Q2: “A leaked key or token opens a production system; a leaked payroll row is a breach that must be notified. Table and column names carry no class on their own.” | The tool 'write_query' is listed in the organization's register as reaching this asset, and it can execute INSERT, UPDATE, or DELETE queries on the user directory. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `audit-log`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2 | The tool 'read_query' is listed in the organization's register as reaching this asset, and it can execute SELECT queries on the audit log. |
| `write_query` | 5 | yes | Q2: “altering it hides misuse” | The tool 'write_query' is listed in the organization's register as reaching this asset, and it can execute INSERT, UPDATE, or DELETE queries on the audit log. |

Not reached: `create_table`, `list_tables`, `describe_table`, `append_insight`

### `new-tables`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | yes | Q2: “A table an agent creates is classed by what it holds. Table and column names are Routine. Aggregation: a query that returns every row of a table ranks a step above a query for one row, and a join that puts names next to keys or social… | The organization's register lists read_query as a tool that reaches new-tables. |
| `write_query` | 5 | yes | Q2: “A table an agent creates is classed by what it holds. Table and column names are Routine. Aggregation: a query that returns every row of a table ranks a step above a query for one row, and a join that puts names next to keys or social… | The tool 'write_query' is listed in the organization's register as reaching this asset, and it can execute INSERT, UPDATE, or DELETE queries on tables an agent creates. |
| `create_table` | 1 | yes | none | The tool 'create_table' is listed in the organization's register as reaching this asset, and it directly creates new tables which are part of the 'new-tables' asset. |

Not reached: `list_tables`, `describe_table`, `append_insight`

### `insight-memo`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_query` | 5 | no | Q2: “API keys issued to users, with their scopes (admin, write, read-only)” | The tool 'read_query' can execute SELECT queries on the SQLite database, which includes reading from the 'api-keys' asset. |
| `append_insight` | 1 | yes | none | The tool `append_insight` is explicitly listed in the organization's register as reaching this asset, and its description matches the purpose of adding insights to the memo. |

Not reached: `write_query`, `create_table`, `list_tables`, `describe_table`

### `schema`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `list_tables` | 1 | yes | none | The tool 'list_tables' is listed in the organization's register as reaching this asset, and it operates on table names which are part of the schema. |
| `describe_table` | 2 | yes | none | The tool 'describe_table' is listed in the organization's register as reaching this asset, and it retrieves schema information for a specific table. |

Not reached: `read_query`, `write_query`, `create_table`, `append_insight`
