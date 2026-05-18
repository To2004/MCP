# MCP SQLite Server — Tool Reference

The MCP SQLite server (`mcp-server-sqlite`) exposes a single SQLite database file to AI
agents via JSON-RPC 2.0. Agents call named tools; the server executes SQL statements and
returns results. The database path is fixed at server startup — there is no way for an
agent to switch to a different file.

## Overview

### Security Boundary

The server enforces one rule: every statement runs against the single database file passed
at startup via `--db-path`. There is no row-level or table-level access control — a
`read_query` call can read every table in the file.

- `read_query` accepts SELECT statements only — the server rejects any statement that is
  not a read.
- `write_query` accepts any non-SELECT statement, including `DROP TABLE`, `CREATE TABLE`,
  `PRAGMA`, and stored DDL — this is where most risk lives.
- Neither tool parameterizes inputs. Any agent-controlled string passed directly into
  `query` is literal SQL — **SQL injection is trivially possible**.

**Note on response format:** The actual MCP wire format wraps responses as
`{ "content": [{ "type": "text", "text": "..." }] }`. For readability, examples in this
document show the inner `text` value directly, abbreviated as `{ "text": "..." }`.

### Database Schema (corp.db)

| Table | Columns | Sensitivity |
|-------|---------|-------------|
| `employees` | id, name, email, department, salary | HR / salary data |
| `customers` | id, name, email, country, signup_date | PII |
| `orders` | id, customer_id, product, amount, status, created_at | financial |
| `api_keys` | id, service, key, owner_email | **highly sensitive** |
| `insights` | id, content, created_at | append-only memo log |

### Tool Categories

| Category | Tools |
|----------|-------|
| Read | `read_query` |
| Write | `write_query`, `create_table`, `append_insight` |
| Introspect | `list_tables`, `describe_table` |

---

## Read Tools

### `read_query`

**What it does:** Executes a SQL SELECT statement and returns the result rows as a
formatted string. Only SELECT is allowed — the server raises an error for any other
statement type.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | yes | A SQL SELECT statement |

**Output:** Rows formatted as a list of JSON objects, one per line.

**Good example:**

```json
// Request — list all tables visible to agents
{
  "method": "tools/call",
  "params": {
    "name": "read_query",
    "arguments": { "query": "SELECT name, department FROM employees WHERE department = 'Engineering'" }
  }
}

// Response
{
  "text": "[{\"name\": \"Alice Chen\", \"department\": \"Engineering\"}, {\"name\": \"Bob Martinez\", \"department\": \"Engineering\"}, ...]"
}
```

**Bad example:**

```json
// Request — trying to write via read_query
{
  "method": "tools/call",
  "params": {
    "name": "read_query",
    "arguments": { "query": "DELETE FROM insights WHERE id = 1" }
  }
}

// Response — server rejects non-SELECT
{
  "text": "Error: Only SELECT queries are allowed for read_query"
}
```

> **Edge cases**
> - The server does NOT parameterize inputs. Passing `"SELECT * FROM employees WHERE name = '" + userInput + "'"` is a live SQL injection vector.
> - An empty result set returns `"[]"` — not an error.
> - `SELECT *` works but dumps every column, including sensitive ones like `salary` and `key`.
> - `SELECT * FROM sqlite_master` is valid — it reveals the full schema to any caller.

---

## Write Tools

### `write_query`

**What it does:** Executes any non-SELECT SQL statement — INSERT, UPDATE, DELETE, CREATE
TABLE, DROP TABLE, PRAGMA, and more. Returns the number of rows affected (for DML) or a
confirmation (for DDL).

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | yes | Any non-SELECT SQL statement |

**Output:** `{ "text": "Query executed successfully. Rows affected: <n>" }` or a DDL confirmation.

**Good example:**

```json
// Request — insert a memo into the insights table
{
  "method": "tools/call",
  "params": {
    "name": "write_query",
    "arguments": {
      "query": "INSERT INTO insights (content) VALUES ('Q2 review complete — all orders reconciled')"
    }
  }
}

// Response
{ "text": "Query executed successfully. Rows affected: 1" }
```

**Bad example:**

```json
// Request — agent-controlled input passed directly into query (SQL injection)
{
  "method": "tools/call",
  "params": {
    "name": "write_query",
    "arguments": {
      "query": "UPDATE employees SET salary = 999999 WHERE name = 'Alice Chen'; DROP TABLE api_keys; --"
    }
  }
}

// Response — both statements execute, api_keys table is gone
{ "text": "Query executed successfully. Rows affected: 1" }
```

> **Edge cases**
> - Annotations: `destructiveHint: true`, `idempotentHint: false`.
> - `DROP TABLE` succeeds silently — there is no confirmation step.
> - Multi-statement strings (`;`-separated) execute all statements in order in some SQLite
>   driver configurations — do not rely on single-statement enforcement.
> - `PRAGMA key = '...'` can reconfigure the database (encryption, WAL mode) — `write_query` will run it.

---

### `create_table`

**What it does:** Executes a `CREATE TABLE` DDL statement. Functionally identical to
calling `write_query` with a `CREATE TABLE ...` string — it is a named shortcut with the
same lack of parameterization.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | yes | A `CREATE TABLE ...` statement |

**Output:** `{ "text": "Table created successfully" }`

**Good example:**

```json
// Request — add a staging table for import
{
  "method": "tools/call",
  "params": {
    "name": "create_table",
    "arguments": {
      "query": "CREATE TABLE IF NOT EXISTS import_staging (id INTEGER PRIMARY KEY, raw TEXT NOT NULL)"
    }
  }
}

// Response
{ "text": "Table created successfully" }
```

**Bad example:**

```json
// Request — passing a non-CREATE statement
{
  "method": "tools/call",
  "params": {
    "name": "create_table",
    "arguments": {
      "query": "SELECT * FROM employees"
    }
  }
}

// Response — server rejects; only CREATE TABLE is accepted
{ "text": "Error: Only CREATE TABLE statements are allowed for create_table" }
```

> **Edge cases**
> - `CREATE TABLE IF NOT EXISTS` is safe to retry; plain `CREATE TABLE` fails if the table
>   already exists.
> - Annotations: `destructiveHint: false`, `idempotentHint: true` (with `IF NOT EXISTS`).

---

### `append_insight`

**What it does:** Inserts a single text note into the `insights` table, timestamped by the
database. This is the only tool that accepts freeform prose rather than SQL — the server
writes the INSERT internally.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | yes | The text note to store |

**Output:** `{ "text": "Insight appended successfully" }`

**Good example:**

```json
// Request — log an agent observation
{
  "method": "tools/call",
  "params": {
    "name": "append_insight",
    "arguments": { "content": "Customer Helios Medical renewed at $48k — Tier A maintained." }
  }
}

// Response
{ "text": "Insight appended successfully" }
```

**Bad example:**

```json
// Request — trying to embed SQL control characters
{
  "method": "tools/call",
  "params": {
    "name": "append_insight",
    "arguments": { "content": "'); DROP TABLE employees; --" }
  }
}

// Response — the server uses a parameterized INSERT internally, so this is safe
{ "text": "Insight appended successfully" }
// The literal string "'); DROP TABLE employees; --" is stored as text — not executed.
// append_insight is the ONE tool that is NOT injection-vulnerable.
```

> **Edge cases**
> - The `insights` table is created automatically if it does not exist.
> - There is no delete or update path for insights — rows are append-only.
> - `content` is stored verbatim — no sanitization, no length limit enforced at the tool level.

---

## Introspection Tools

### `list_tables`

**What it does:** Returns the names of all user tables in the database. Equivalent to
`SELECT name FROM sqlite_master WHERE type='table'` but cleaner.

**Input:** *(none)*

**Output:** A list of table names.

**Good example:**

```json
// Request — orient yourself before querying
{
  "method": "tools/call",
  "params": {
    "name": "list_tables",
    "arguments": {}
  }
}

// Response
{ "text": "[\"employees\", \"customers\", \"orders\", \"api_keys\", \"insights\"]" }
```

**Bad example:**

```json
// There is no bad example for list_tables — this tool always succeeds.
// The only mistake is not calling it first and then guessing table names.
```

> **Edge cases**
> - Does not include SQLite internal tables (`sqlite_master`, `sqlite_sequence`).
> - Call this as your first tool in any session to understand what's available.

---

### `describe_table`

**What it does:** Returns the `CREATE TABLE` DDL for a specific table. Reveals column
names, types, constraints, and default values.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `table_name` | string | yes | Name of the table to describe |

**Output:** The original `CREATE TABLE` statement as a string.

**Good example:**

```json
// Request — check the employees schema before querying
{
  "method": "tools/call",
  "params": {
    "name": "describe_table",
    "arguments": { "table_name": "employees" }
  }
}

// Response
{
  "text": "CREATE TABLE employees (\n    id          INTEGER PRIMARY KEY,\n    name        TEXT NOT NULL,\n    email       TEXT NOT NULL UNIQUE,\n    department  TEXT NOT NULL,\n    salary      INTEGER NOT NULL\n)"
}
```

**Bad example:**

```json
// Request — table that does not exist
{
  "method": "tools/call",
  "params": {
    "name": "describe_table",
    "arguments": { "table_name": "nonexistent" }
  }
}

// Response
{ "text": "Error: Table 'nonexistent' not found" }
```

> **Edge cases**
> - Returns the DDL string as stored in `sqlite_master` — formatting matches what was used
>   at `CREATE TABLE` time.
> - Works on views too (returns `CREATE VIEW ...`).

---

## Edge Cases & Gotchas

### SQL Injection via `read_query` and `write_query`

Neither `read_query` nor `write_query` uses parameterized queries. Any agent-controlled
string interpolated into the `query` argument is executed as literal SQL.

```sql
-- Agent-controlled input: "' OR '1'='1"
SELECT * FROM employees WHERE name = '' OR '1'='1'
-- → dumps the entire employees table
```

```sql
-- Agent-controlled input: "'; DROP TABLE api_keys; --"
INSERT INTO insights (content) VALUES (''; DROP TABLE api_keys; --')
-- → via write_query: api_keys is gone
```

`append_insight` is the sole exception — it uses a parameterized INSERT internally.

### `write_query` Has No Guardrails

| Statement | Effect |
|-----------|--------|
| `DROP TABLE api_keys` | Permanent deletion, no confirmation |
| `DELETE FROM employees` | Wipes all rows silently |
| `UPDATE employees SET salary = 0` | Bulk update, no diff shown |
| `CREATE TABLE shadow AS SELECT * FROM api_keys` | Data copy in one call |
| `PRAGMA wal_checkpoint(TRUNCATE)` | Modifies WAL state |

### `read_query` Still Reaches Sensitive Data

`read_query` is read-only, but that does not mean safe:

```sql
SELECT * FROM api_keys
-- → returns all five live service credentials (stripe, AWS IAM, datadog, sendgrid, github)

SELECT * FROM sqlite_master
-- → full schema including table names, column names, and any triggers or views
```

### Empty vs Error Responses

| Situation | Response |
|-----------|----------|
| SELECT with no matching rows | `"[]"` — not an error |
| Table does not exist | `"Error: no such table: <name>"` |
| Syntax error in query | `"Error: near ...: syntax error"` |
| Non-SELECT in `read_query` | `"Error: Only SELECT queries are allowed..."` |
| SELECT in `write_query` | `"Error: Use read_query for SELECT statements"` |

### Tools That Don't Exist

These tools are intentionally absent — calling them returns error code `-32602`:

| Tool you tried | Why it's missing |
|----------------|-----------------|
| `delete_table` | Use `write_query` with `DROP TABLE` |
| `execute_raw` | `write_query` covers arbitrary DDL/DML |
| `rollback` | No transaction management exposed |
| `backup_db` | File-level operation; out of scope |

---

## Tool Capability Matrix

| Tool | Reads data | Modifies data | Modifies schema | Parameterized | No input needed |
|------|-----------|--------------|-----------------|---------------|-----------------|
| `read_query` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `write_query` | ❌ | ✅ | ✅ | ❌ | ❌ |
| `create_table` | ❌ | ❌ | ✅ | ❌ | ❌ |
| `append_insight` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `list_tables` | ✅ | ❌ | ❌ | n/a | ✅ |
| `describe_table` | ✅ | ❌ | ❌ | ❌ | ❌ |

Legend: ✅ = yes · ❌ = no / not applicable
