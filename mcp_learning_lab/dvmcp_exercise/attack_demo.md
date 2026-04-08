# Attack Demo: Command Injection via `run_command` Tool

One-page writeup of a single agent→server attack against DVMCP. This
page is the template for a figure in the thesis evaluation chapter.

## Summary

- **Attack name:** Unauthenticated Arbitrary Command Execution
- **DVMCP vulnerability ID / section:** MCP-05 (Input Validation - Command Injection via Arguments)
- **Thesis taxonomy tier:** **Abuse** (agent has legitimate access to the tool but invokes it with malicious payload)
- **Tool(s) involved:** `run_command` (tool provides shell execution with `execSync(..., { shell: true })`)
- **One-line description:** Agent sends unvalidated shell metacharacters in `command` argument, causing arbitrary OS commands to execute with server privileges.

## Preconditions

- Agent has learned the server exists and accepts MCP JSON-RPC requests (via `initialize`)
- Agent has called `tools/list` and discovered the `run_command` tool
- No encryption, no authentication tokens, no rate limiting protecting the server
- Server is running on `localhost:3001` (or any accessible network endpoint)

## Attack Steps

1. **Initialize connection** (optional but standard): Send `initialize` request to retrieve capabilities and confirm server is reachable
2. **List tools**: Call `tools/list` to discover that `run_command` exists
3. **Craft malicious request**: Build a `tools/call` request with:
   - `name`: `"run_command"`
   - `arguments.command`: Any shell command (in this case: `"set"` to read all environment variables)
4. **Execute**: Send POST request with JSON-RPC payload
5. **Observe server behavior**: Server executes the command via Node.js `execSync()` and returns stdout in the JSON-RPC response

## The Malicious JSON-RPC Request

**Request (POST to `http://localhost:3001/`):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_command",
    "arguments": {
      "command": "set"
    }
  }
}
```

**HTTP Headers:**
```
POST / HTTP/1.1
Host: localhost:3001
Content-Type: application/json
Content-Length: 119
```

## Server Response

**Status:** HTTP 200 OK

**Body (JSON-RPC Response):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "ALLUSERSPROFILE=C:\\ProgramData\r\nAPPDATA=C:\\Users\\user\\AppData\\Roaming\r\n... [24 more env vars] ...\r\nVSCODE_INJECTION=1\r\nwindir=C:\\windows\r\n"
      }
    ]
  }
}
```

**Truncated example of leaked data:**
- `ALLUSERSPROFILE=C:\ProgramData`
- `APPDATA=C:\Users\user\AppData\Roaming`
- `COMPUTERNAME=LAPTOP-180706`
- `PATH=...` (256+ chars of system paths, tools, and hidden VS Code paths)
- `USERNAME=user`
- `USERPROFILE=C:\Users\user`

## What Actually Happened on the Server

1. **No authentication check** — server accepted the request without verifying caller identity
2. **No input validation** — `command` parameter passed directly to `execSync()`
3. **Shell enabled** — `execSync(command, { shell: true })` interprets the command as shell syntax
4. **Executed with server privileges** — the `set` command ran as the Node.js process owner
5. **Returned stdout** — all environment variables (including system config, user paths, potential secrets) flowed back in the JSON-RPC response

**Impact:** An agent now has full OS command execution capability and leaked sensitive environment data (system paths, user name, system architecture, debugger endpoints, etc.)

## Observable Signals (for Dynamic Scoring)

| Signal | Where it appears | Useful for scoring? |
|--------|------------------|---------------------|
| Tool name is "run_command" | JSON-RPC `params.name` | **✓ High** — unusual name, suggests execution |
| `arguments.command` contains shell metacharacters (pipes, redirects, subshells) | JSON-RPC `params.arguments` | **✓ Very High** — classic injection pattern |
| `arguments.command` is not quoted but contains spaces or special chars | Request payload | **✓ High** — sign of escaping bypass attempt |
| Response contains `\r\n` delimiters (multi-line output) | JSON-RPC `result.content[0].text` | **✓ Medium** — suggests command output, not normal tool response |
| Response contains environment variable names | Response text pattern matching | **✓ High** — clear exfiltration intent |
| Response size much larger than expected for "weather" or similar tools | HTTP Content-Length | **✓ Medium** — anomalous data volume |
| No rate limiting applied before execution | Server logs | **✓ High** — attacker can make unlimited calls |
| Tool description mentions "Execute a system command" | Tool definition from `tools/list` | **✓ Medium** — red flag during static analysis |

## Taxonomy Mapping

This attack instantiates **OWASP MCP Top 10 – C01: Input Injection**.

More specifically in thesis taxonomy:
- **Trust boundary:** Client (agent) → Server (vulnerable tool)
- **Attack vector:** Malicious argument in tool invocation
- **Bypass mechanism:** No input validation, shell metacharacter interpretation
- **Blast radius:** Full OS command execution = maximum impact

**Gap revealed:** The thesis taxonomy should distinguish between:
1. **Tool-level injection** (e.g., bad argument handling) — *what happened here*
2. **Argument-level injection** (e.g., SQL in a query tool, shell in a command tool) — *more specific* 

The current framework correctly flags this, but downstream defense would need argument-level inspection (e.g., AST parsing, command allowlisting) not just tool-level checks.

## Effort Cost

- **Time from clone to working exploit:** ~45 minutes
  - 15 min: Search GitHub, verify repo is real
  - 15 min: Clone, install, start server
  - 10 min: Write and test Python client
  - 5 min: Document findings
  
- **Hardest part:** Understanding how Node.js HTTP routing works (had to inspect `server.js` to verify the `/` path catches JSON-RPC)

- **Implication for thesis scope:** 
  - ✓ **5–7 demos is feasible** — DVMCP is well-structured, each vulnerability is 5–15 lines of working code
  - ✓ **Attack documentation is concrete** — raw JSON-RPC + response makes it thesis-publication ready
  - ✓ **Observable signals are clear** — dynamic scorer can extract 5–6 strong input validation signals from the request alone
  - ✓ **Supports "ground truth" evaluation** — each DVMCP vulnerability maps cleanly to a known OWASP/CWE category

## Open Questions

- Should the scoring model treat `execute_system_command` differently than `run_sql_query`? Or is the injection signal universal?
- How to weight the confidence of "this looks like shell metacharacters" vs "this is definitely shell metacharacters" in a scoring model?
- Does the thesis benefit from including the rug-pull (`MCP-02: Tool Definition Tampering`) as a second demo to show that static analysis alone is insufficient?
