# Study Guide: Understanding This Exercise

A ground-up walkthrough of what happens in this folder, written for
someone new to MCP, JSON-RPC, and async protocols.

## 1. The Big Picture

You are writing a thesis about **defending MCP servers from risky
agents**. Before you can score whether an agent request is risky, you
need to *see a real attack* end-to-end. This folder is that exercise.

The attacker and victim roles are:

```
[ Agent / client ]  --- JSON-RPC request --->  [ MCP server ]
    (threat source)                                (protected asset)
```

Your thesis treats the **server as the victim** and the **agent as the
threat source**. DVMCP gives you a deliberately broken server so you
can play the agent and prove an attack works.

## 2. Core Concepts (Cheat Sheet)

| Term | Plain-English meaning |
|------|------------------------|
| **MCP** (Model Context Protocol) | A standard way for AI agents to call tools on a server. Think "REST API, but designed for LLM tool-use." |
| **JSON-RPC 2.0** | The wire format MCP uses. Every request is a JSON object with `jsonrpc`, `id`, `method`, and `params`. |
| **Tool** | A named function the server exposes (e.g. `run_command`, `read_file`). The agent can list them and call them. |
| **DVMCP** | "Damn Vulnerable MCP" — an intentionally insecure MCP server built for security training. |
| **`tools/list`** | JSON-RPC method: "server, what tools do you have?" |
| **`tools/call`** | JSON-RPC method: "server, run tool X with arguments Y." |
| **`execSync`** | Node.js function that runs a shell command synchronously. Dangerous when fed unvalidated user input. |

## 3. Anatomy of a JSON-RPC Request

Every request you send looks like this:

```json
{
  "jsonrpc": "2.0",       // protocol version, always "2.0"
  "id": 1,                 // correlates request with response
  "method": "tools/call",  // what you want the server to do
  "params": {              // arguments for the method
    "name": "run_command",
    "arguments": { "command": "set" }
  }
}
```

Server responds with the same `id` plus a `result` or `error`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "content": [ { "type": "text", "text": "..." } ] }
}
```

That is the whole protocol. No magic.

## 4. File-by-File Walkthrough

### `README.md` — Why the exercise exists

Lists four thesis decisions that depend on seeing a real attack. Defines
scope (one demo, not a framework) and the single deliverable
(`attack_demo.md`). Read this first to remember why you did this.

### `setup_notes.md` — Reproducibility log

Append-only running log: DVMCP commit, Node version, install steps,
the 10 tools the server exposes. If you (or a thesis reviewer) need to
rebuild this environment in six months, this file is the recipe.

Key fact it records: **DVMCP installed cleanly, no fixes needed.** That
matters because it shows the *effort cost* of one demo is low — useful
evidence for scoping the thesis.

### `client.py` — Your attacker

A 135-line Python script that speaks JSON-RPC over raw sockets. It does
**not** use any MCP SDK — it hand-builds the HTTP + JSON payload. This
is deliberate: the thesis wants you fluent in the wire protocol, not
dependent on a library that hides it.

What it does in order:
1. `initialize` — handshake to confirm server is alive
2. `tools/list` — ask the server what tools exist
3. `tools/call` with `echo "..."` — harmless sanity check
4. `tools/call` with `set` — **the actual exploit**, reads all env vars

### `attack_demo.md` — The thesis deliverable

One page, thesis-publication ready. Structure:

- **Summary** — attack name, taxonomy tier, tools involved
- **Preconditions** — what the attacker knows beforehand
- **Attack steps** — numbered reproduction
- **The malicious JSON-RPC request** — exact bytes on the wire
- **Server response** — what leaked
- **What actually happened on the server** — root cause analysis
- **Observable signals** — the table of detection signals for your
  dynamic scoring model (this is the thesis connection)
- **Taxonomy mapping** — OWASP MCP Top 10, trust boundary, blast radius
- **Effort cost** — time spent, what was hardest
- **Open questions** — design questions for the scoring model

## 5. The Attack, Step by Step

### 5.1 What the vulnerability is

In `dvmcp-test/server.js`, the `run_command` tool takes an `arguments.command`
string and passes it to Node's `execSync(command, { shell: true })`. Because
`shell: true` is set, the string is interpreted by the OS shell — so shell
metacharacters (`;`, `|`, `&&`, `$()`) give the attacker full OS control.

### 5.2 Why it works

Three failures stack up:
1. **No authentication** — anyone who reaches port 3001 can call tools.
2. **No input validation** — the `command` field is not checked.
3. **Shell enabled** — `{shell: true}` interprets metacharacters.

Any one of these, alone, would usually not be catastrophic. All three
together = arbitrary code execution.

### 5.3 What you sent

A single JSON-RPC POST containing `"command": "set"` (Windows: print
all environment variables).

### 5.4 What you got back

24+ environment variables, including `USERNAME`, `USERPROFILE`, `PATH`,
`COMPUTERNAME`, VS Code debug endpoints — all in a single response.

### 5.5 Why this matters for your thesis

Your **dynamic scoring model** would sit in front of the server and see
this exact request. The `attack_demo.md` signals table tells you which
features to extract:

- tool name (`run_command` → high-risk prior)
- argument content (shell metacharacters → very high-risk signal)
- response size (anomalously large for a "tool call")
- response content (env-var patterns → exfiltration fingerprint)

These are the **observable features** your model will score on.

## 6. Taxonomy Placement

The attack is **Abuse tier** in your thesis taxonomy:

- The agent has *legitimate* access (it's allowed to call tools).
- It abuses that access with a *malicious payload*.
- This is different from **Bypass tier** (where an attacker circumvents
  a control that was supposed to stop them) — here, *there was no
  control to bypass.*

Trust boundary crossed: **Client (agent) → Server**. Blast radius:
**Full OS command execution** on the server host.

## 7. How to Reproduce This Yourself

From scratch:

```bash
# 1. Clone DVMCP
cd C:/Users/user/Documents/GitHub/MCP
git clone https://github.com/cybersecai-uk/dvmcp.git dvmcp-test
cd dvmcp-test

# 2. Install and start (one terminal)
npm install
node server.js          # server now on localhost:3001

# 3. Run the attack (second terminal)
cd ../mcp_learning_lab/dvmcp_exercise
python client.py
```

You should see the JSON-RPC request printed, the HTTP response, and the
list of environment variables the server leaked.

## 8. Common Beginner Questions

**Q: What is "async" about MCP, and does this exercise use it?**
MCP is typically transported over async channels (stdio streams or
HTTP/SSE for streaming). In this exercise you use **plain synchronous
HTTP POST** because DVMCP exposes a simple request/response endpoint.
You did not need `asyncio` here. When you move to the thesis scoring
model, you'll likely wrap an async server — but not today.

**Q: Why raw sockets instead of `requests` or an MCP SDK?**
Two reasons: (1) no external dependencies to install, (2) forces you to
see the exact HTTP bytes. Using `requests` would hide the protocol
underneath `requests.post(...)`.

**Q: Is this a "real" attack or a toy?**
The *vulnerability pattern* (`execSync` with `shell: true` and
unvalidated input) is real and has caused actual CVEs in production
Node apps. DVMCP packages it in a teaching-friendly server.

**Q: What is the next step after this exercise?**
Per `attack_demo.md` open questions: decide whether to add a second
demo (probably MCP-02 rug-pull), and start converting the "Observable
Signals" table into feature extractors for the dynamic scoring model.

## 9. Where This Connects in the Repo

- **Thesis taxonomy** — see `Literature_review/mcp_server_attacks.md`
  and the taxonomy discussion in `Literature_review/README.md`. This
  demo is one concrete row in that taxonomy.
- **Scoring model** — not yet built (lives in `src/mcp_security/`).
  The signals table in `attack_demo.md` is the spec for its first
  feature extractor.
- **`dvmcp-test/`** (sibling folder) — the actual vulnerable server
  you cloned. Do not modify; treat it as a black-box target.

## 10. TL;DR

> You cloned a deliberately broken MCP server, sent it one JSON-RPC
> request containing a shell command, and it ran the command and
> leaked your Windows environment. You wrote that up as one page of
> thesis evidence showing (a) one attack demo takes ~45 minutes, and
> (b) the observable signals you need for your scoring model are
> visible on the wire.
