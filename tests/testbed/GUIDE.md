# Testbed Walkthrough Guide

A plain-English explanation of how the MCP attack testbed works, why each server
was chosen, and how to run your first attack from scratch.

## What is this testbed?

The testbed is a reproducible lab for testing MCP servers with malicious inputs.
It answers two questions:

1. **Does the attack actually work?** — send a bad payload, see if the server
   returns something dangerous (e.g., the contents of `/etc/passwd`).
2. **Does the scorer catch it?** — feed the same request through the MCP Security
   scorer and see if it assigns a high risk score.

Think of it as a controlled experiment: known bad input goes in, we measure what
comes out, and we record whether the scorer would have stopped it.

---

## The big picture (before any code)

```
You (or run_all.py)
     |
     v
attack_runner.py          <-- the brain: loops over servers and templates
     |
     +-- server_manager.py   <-- starts the MCP server process (e.g., npx ...)
     |
     +-- tool_matcher.py     <-- asks the server "what tools do you have?"
     |                           then matches them to attack templates
     |
     +-- [attack loop]       <-- for each (tool, template) pair:
     |       send malicious payload
     |       send benign payload
     |       check if response looks like damage
     |       optionally score it
     |
     +-- scorer_bridge.py    <-- calls MCP Security scorer (stub for now)
     |
     +-- metrics.py          <-- computes ASR, TPR, FPR, latency
     |
     v
results/<server>_<timestamp>.json
```

Everything is JSON-driven. The Python code never hard-codes server names or
payloads — it reads them from `servers/` and `attack_templates/` at runtime.

---

## What the code is actually doing (plain English)

Forget the Python for a second. Here is the concept in one paragraph:

> The testbed is an **automated tester that acts like a hacker**. It starts a
> server, asks it "what tools do you have?", sends bad inputs to those tools,
> checks if the server returned something dangerous, and writes down what happened.
> The Python code is just a loop that does this automatically for 24 servers × 25
> attack types so you don't have to do it by hand.

The important files are the **JSON files** — server profiles and attack templates.
They are plain text and readable without any coding knowledge. The Python harness
just reads them and executes what they describe.

### What each Python file is responsible for

| File | One-line job |
|------|-------------|
| `attack_runner.py` | The main loop — ties everything together |
| `server_manager.py` | Starts and stops the MCP server process |
| `tool_matcher.py` | Asks the server what tools it has, matches them to templates |
| `scenario_runner.py` | Runs multi-step attack sequences |
| `scorer_bridge.py` | Calls the risk scorer (currently does nothing — Phase 3) |
| `metrics.py` | Calculates ASR, TPR, FPR, latency after a run |
| `run_all.py` | Runs every server one after another (the campaign runner) |

You do not need to read or change any of these files to run the testbed.

---

## Package versions used

These are declared in `pyproject.toml` at the project root:

| Package | Minimum version | Installed | Latest (PyPI) | What it does |
|---------|----------------|-----------|---------------|-------------|
| `mcp` | `>=1.26.0` | `1.26.0` | `1.27.0` ⚠️ | Anthropic's official Python SDK for talking to MCP servers over stdio |
| `requests` | `>=2.32.0` | — | — | Standard Python HTTP library (used for HTTP-transport servers like dvmcp) |
| `pytest` | `>=8.0.0` | — | — | Runs the unit tests |
| `ruff` | `>=0.11.0` | — | — | Linter and formatter |

The `>=` prefix means "this version or newer." When you run `uv sync` it installs
the latest version that satisfies the constraint — so you always get an up-to-date
install, not a pinned-old one.

To see exactly what is installed on your machine right now:
```bash
uv pip list
```

---

## How we picked the MCP servers

### Selection criteria

We needed servers that:

1. **Are real and widely used** — results must be credible, not toy servers.
2. **Cover every attack category** — C1 (code execution) through C6 (injection),
   so every template gets exercised.
3. **Have known vulnerabilities** — assigned CVEs give the thesis grounding in
   published research.
4. **Are installable locally** — no cloud accounts needed for the core set.
5. **Include negative controls** — benign servers that should produce no damage,
   to measure false positives.

### How we actually found them

- **Anthropic's official list** — Anthropic publishes reference servers on GitHub
  under `modelcontextprotocol/servers`. These are the most widely deployed and
  have the most CVE coverage: `filesystem`, `fetch`, `git`, `sqlite`, `everything`,
  `memory`, `time`.
- **CVE databases** — searched NVD and GitHub advisories for `mcp-server` in 2025.
  This surfaced `aws-mcp` (CVSS 9.6), `markdownify`, `serverless`, and others.
- **Community hubs** — `mcp.so`, `smithery.ai`, and the Awesome-MCP GitHub list
  provided community-popular servers like `desktop-commander`, `playwright-mcp`,
  `brave-search`, `notion-mcp`, and `context7-mcp`.
- **Research benchmarks** — MCPTox (NeurIPS 2025) used `sequential-thinking`
  as a test target, so we included it to align with published benchmarks.
- **DVMCP** — "Damn Vulnerable MCP" is a deliberately insecure server built
  specifically for security research, similar to DVWA in web security.

### Why three tiers?

| Tier | Count | Purpose |
|------|-------|---------|
| `vulnerable` | 22 | Real attack surface — expect damage |
| `benign` | 3 | Negative controls — expect no damage |
| `optional` | 6 | Require API keys — excluded from default runs |

Benign servers (`everything`, `memory`, `time`) are essential: if the scorer
flags them, those are **false positives**. We need both true positives and
false positives to compute TPR and FPR.

---

## Server inventory

### Core vulnerable servers (no API key needed)

| Server | Install package | Installed | Latest | Status | Key CVEs | Attack surface |
|--------|----------------|-----------|--------|--------|----------|----------------|
| `filesystem` | `@modelcontextprotocol/server-filesystem` | `2026.1.14` | `2026.1.14` | ✅ | CVE-2025-53109, CVE-2025-53110 | Path traversal — reads `/etc/passwd` via `../../` |
| `fetch` | `mcp-server-fetch` (PyPI) | `2025.4.7` | `2025.4.7` | ✅ | CVE-2025-65513 | SSRF — fetches internal URLs the agent shouldn't reach |
| `git` | `mcp-server-git` (PyPI) | `2026.1.14` | `2026.1.14` | ✅ | CVE-2025-68143/44/45 | Argument injection — malicious flags injected into git commands |
| `sqlite` | `mcp-server-sqlite` (PyPI) | `2025.4.25` | `2025.4.25` | ✅ | _(none assigned)_ | SQL injection — no parameterized queries |
| `desktop-commander` | `@wonderwhy-er/desktop-commander` | `0.2.38` | `0.2.38` | ✅ | _(none assigned)_ | Shell execution — runs arbitrary system commands |
| `playwright-mcp` | `@playwright/mcp` | `0.0.70` | `0.0.70` | ✅ | _(none assigned)_ | Browser SSRF — navigates to attacker-controlled URLs |
| `puppeteer-mcp` | `@modelcontextprotocol/server-puppeteer` | `2025.5.12` | `2025.5.12` | ✅ | _(none assigned)_ | File access via headless browser |
| `godot` | `godot-mcp` | `0.1.0` | `0.1.0` | ✅ | CVE-2026-25546 | `projectPath` argument injection |
| `mcp-obsidian` | `mcp-obsidian` | `1.0.0` | `1.0.0` | ✅ | _(none assigned)_ | Reads/writes markdown vault files |
| `sequential-thinking` | `@modelcontextprotocol/server-sequential-thinking` | `2025.12.18` | `2025.12.18` | ✅ | _(none assigned)_ | MCPTox benchmark target |

### Optional servers (require API keys)

| Server | Env var needed | Install package | Installed | Latest | Status | Key CVEs | Attack surface |
|--------|---------------|----------------|-----------|--------|--------|----------|----------------|
| `github-mcp` | `GITHUB_TOKEN` | `@modelcontextprotocol/server-github` | `2025.4.8` | `2025.4.8` | ✅ | _(none assigned)_ | Data exfiltration via GitHub API |
| `aws-mcp` | AWS credentials | `@modelcontextprotocol/server-aws-kb-retrieval` | `0.6.2` | `0.6.2` | ✅ | CVE-2025-5277 (CVSS 9.6) | Command injection in AWS API calls |
| `google-maps-mcp` | `GOOGLE_MAPS_API_KEY` | `@modelcontextprotocol/server-google-maps` | `0.6.2` | `0.6.2` | ✅ | _(none assigned)_ | Location data exfiltration |
| `context7-mcp` | Upstash API key | `@upstash/context7-mcp` | `2.1.7` | `2.1.7` | ✅ | _(none assigned)_ | RADE (retrieval-augmented data exfil) vector |
| `adx-mcp` | Azure credentials | `@azure/mcp` | `2.0.0-beta.39` | `2.0.0-beta.40` | ⚠️ outdated | CVE-2026-33980 (CVSS 8.3) | KQL injection into Azure Data Explorer |
| `brave-search` | `BRAVE_API_KEY` | `@modelcontextprotocol/server-brave-search` | `0.6.2` | `0.6.2` | ✅ | _(none assigned)_ | _(search only)_ |
| `exa-mcp` | `EXA_API_KEY` | `exa-mcp` | `0.0.7` | `0.0.7` | ✅ | _(none assigned)_ | _(search only)_ |
| `firecrawl-mcp` | `FIRECRAWL_API_KEY` | `firecrawl-mcp` | `3.11.0` | `3.11.0` | ✅ | _(none assigned)_ | _(search only)_ |
| `tavily-search` | `TAVILY_API_KEY` | `tavily-mcp` | `0.2.18` | `0.2.18` | ✅ | _(none assigned)_ | _(search only)_ |
| `slack-mcp` | `SLACK_BOT_TOKEN` | `@modelcontextprotocol/server-slack` | `2025.4.25` | `2025.4.25` | ✅ | _(none assigned)_ | _(search only)_ |
| `notion-mcp` | `NOTION_API_KEY` | `@notionhq/notion-mcp-server` | _(not installed)_ | `2.2.1` | — | _(none assigned)_ | _(search only)_ |

### Benign (negative controls)

| Server | Install package | Why benign |
|--------|----------------|-----------|
| `everything` | `@modelcontextprotocol/server-everything` | Safe reference tools only |
| `memory` | `@modelcontextprotocol/server-memory` | In-memory store, no I/O |
| `time` | `mcp-server-time` | Returns current time, zero side effects |

---

## stdio vs HTTP — the two server types

Not all MCP servers work the same way. There are two transport types and it
matters practically because one requires manual setup.

### Type A: stdio (most servers — download and run locally)

The harness **launches the server as a background process** on your machine and
talks to it through stdin/stdout (text piped between programs).

```
Your Python harness
        |
        | stdin / stdout (text pipe)
        |
  npx @modelcontextprotocol/server-filesystem sandbox/
  (process the harness started for you)
```

You do not start anything manually. The harness installs and starts the server,
runs the attacks, and kills the process when done.

**All active servers in the testbed use stdio.** Examples: `filesystem`, `fetch`,
`git`, `sqlite`, `playwright-mcp`, `desktop-commander`.

### Type B: HTTP (a few servers — must be running first)

The server runs separately as a web service, and the harness connects to it over
HTTP like calling an API endpoint.

```
Your Python harness
        |
        | HTTP POST to http://localhost:3001
        |
  node dvmcp-test/server.js
  (you started this manually in another terminal)
```

You must start the server yourself first, then run the harness. This is harder
to automate, which is why HTTP servers ended up in `servers/disabled/`.

**Only disabled servers use HTTP** (`dvmcp`, `bridge`). You do not need them for
the core thesis runs.

### How the harness knows which type to use

Each server profile JSON has a `"transport"` field:

```json
{ "transport": "stdio" }   // harness starts it for you
{ "transport": "http",
  "base_url": "http://localhost:3001" }  // harness connects to it
```

---

## Do I need to connect my GitHub account?

**No — not for the core testbed.**

But this is slightly more subtle than "it skips it." Here is exactly what happens.

### What run_all.py actually does

The campaign runner **always tries** to attack every server, including `github-mcp`.
It calls `_attack_one("github-mcp", ...)`. The server process fails to start because
no GitHub token is set in the environment, so it returns 0 results.

What the `"requires_api_key": true` flag controls is **what happens after that failure**:

```
results = run_attack("github-mcp")   # tries it

if results == []:
    if requires_api_key:
        → log as "API key skip" — keep the profile for next time
    else:
        → log as "unreachable" — move profile to servers/disabled/
```

So the flag means: "this failure is expected, don't permanently disable this server."
Without the flag, an empty result would cause the profile to be moved to `disabled/`.

### The difference between "api key skip" and "unreachable"

| Situation | What run_all.py does | Profile location after run |
|-----------|---------------------|---------------------------|
| Server fails, `requires_api_key: true` | Logs "API key skip" | Stays in `servers/` |
| Server fails, no flag | Logs "unreachable" | Moved to `servers/disabled/` |

### Optional servers and their keys

| Server | Key needed | What happens without it |
|--------|-----------|------------------------|
| `github-mcp` | `GITHUB_TOKEN` | Server fails to start, logged as skip |
| `brave-search` | `BRAVE_API_KEY` | Server fails to start, logged as skip |
| `exa-mcp` | `EXA_API_KEY` | Server fails to start, logged as skip |
| `firecrawl-mcp` | `FIRECRAWL_API_KEY` | Server fails to start, logged as skip |
| `tavily-search` | `TAVILY_API_KEY` | Server fails to start, logged as skip |
| `slack-mcp` | `SLACK_BOT_TOKEN` | Server fails to start, logged as skip |
| `notion-mcp` | `NOTION_API_KEY` | Server fails to start, logged as skip |

The 15 core servers (`filesystem`, `fetch`, `git`, `sqlite`, `playwright-mcp`, etc.)
need **no account, no API key, and no login**. They install from npm/uv and run
entirely on your local machine.

### If you ever do want to test github-mcp

```bash
# Windows — set the token in your current shell session
set GITHUB_TOKEN=ghp_yourtoken...

# Then run normally
uv run python -m tests.testbed.harness.attack_runner --server github-mcp --mode attack
```

This connects to GitHub's API using your token, so the server can make real
GitHub API calls. The attack tests whether a malicious agent could abuse those
calls to exfiltrate repository data. It is entirely optional for the thesis.

---

## How a single attack run works — step by step

This walks through exactly what happens when you run:

```bash
uv run python -m tests.testbed.harness.attack_runner --server filesystem --mode attack
```

### Step 1 — Load the server profile

`attack_runner.py` calls `server_manager.load_profile("filesystem")`.

It reads `tests/testbed/servers/filesystem.json`:
```json
{
  "name": "filesystem",
  "transport": "stdio",
  "install": "npm install -g @modelcontextprotocol/server-filesystem",
  "start_cmd": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "tests/testbed/sandbox"]
}
```

### Step 2 — Install the server (if not already installed)

`install_server(profile)` runs the `install` command. If the package is already
installed, npm/uv is fast and skips re-downloading.

### Step 3 — Start the server process

`server_manager.stdio_session(profile)` launches the process:
```
npx -y @modelcontextprotocol/server-filesystem tests/testbed/sandbox
```
This starts the server with `tests/testbed/sandbox/` as the allowed root directory.
The harness connects to it over stdin/stdout using the MCP protocol.

### Step 4 — Discover tools

Inside the open session, the harness calls `session.list_tools()`.
The server responds with its tool list, for example:
```
read_file, write_file, list_directory, create_directory, move_file, ...
```

### Step 5 — Match templates to tools

`tool_matcher.match(tools, templates)` iterates over all 25 attack templates.
Each template declares keywords like `["read", "file", "open", "load", "path"]`.
The matcher checks if any tool name contains those words:

- `path_traversal` keywords: `read, file, path` → matches `read_file` ✓
- `command_injection` keywords: `run, exec, shell` → no match for filesystem ✗
- `tool_poisoning` keywords: `*` (wildcard) → matches every tool ✓

### Step 6 — Send malicious payloads

For each matched (tool, template) pair, the harness iterates through payloads.
For `path_traversal` against `read_file`:

```
payload: "../../etc/passwd"
args sent to server: {"path": "../../etc/passwd"}
```

The server runs the tool with that argument. The harness records the response.

### Step 7 — Check for damage

`_check_damage(response_text, damage_indicator)` runs a regex against the response.
For `path_traversal`, the indicator is `root:|daemon:|/etc/passwd|uid=`.

If the response contains `root:x:0:0:root:/root:/bin/bash`, damage is `True`.

### Step 8 — Send the benign payload

Every template also has a safe version. For `path_traversal` it might be:
`"sandbox/hello.txt"` — a path inside the allowed directory.
This runs the same tool with a safe argument. `damage_detected` is always `False`
for benign payloads (they are the negative control for each template).

### Step 9 — (Optional) Score it

In `--mode eval`, after each call the harness calls `scorer_bridge.score(...)`.
This is currently a stub returning `{}`. In Phase 3 it will call the live scorer.

### Step 10 — Save results

All results accumulate in a list and are written to:
```
tests/testbed/results/filesystem_20260409T120000.json
```

Each entry looks like:
```json
{
  "server": "filesystem",
  "template_id": "path_traversal",
  "category": "C2",
  "tool": "read_file",
  "payload_label": "unix_traversal",
  "payload_type": "malicious",
  "args": {"path": "../../etc/passwd"},
  "response_snippet": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:...",
  "damage_detected": true,
  "error": null,
  "score": {},
  "latency_ms": 14.2
}
```

### Step 11 — Clean sandbox

After the run, the sandbox directory is wiped. Any files written during the attack
(e.g., by `write_file` payloads) are deleted before the next run.

---

## Running a full campaign

```bash
uv run python tests/testbed/run_all.py --mode attack
```

`run_all.py` is the campaign orchestrator. It:

1. Scans `tests/testbed/servers/*.json` to get all active server names.
2. Skips servers whose `requires_api_key` env var is missing.
3. Calls `run_server()` for each server.
4. If a server fails to connect, moves its profile to `servers/disabled/`.
5. After all servers, combines results and saves:
   - `results/campaign_<timestamp>.json`
   - `results/report_<timestamp>.md`
6. Prints a summary: total servers reached, overall ASR, etc.

---

## Understanding the output

### Console output (per tool call)

```
[C2/path_traversal] read_file('unix_traversal') -> DAMAGE [+]  score: N/A
[C2/path_traversal] read_file('benign') -> [benign] safe [ok]  score: N/A
[C6/tool_poisoning] read_file('prompt_override') -> no damage  score: N/A
```

- `[C2/path_traversal]` — attack category and template ID
- `read_file('unix_traversal')` — tool called and payload label
- `DAMAGE [+]` — the damage_indicator regex matched the response
- `no damage` — regex did not match (attack failed or tool rejected it)
- `score: N/A` — scorer not wired yet (Phase 3)

### Key metrics

| Metric | What it means |
|--------|--------------|
| **ASR** (Attack Success Rate) | What fraction of malicious payloads caused actual damage |
| **TPR** (True Positive Rate) | What fraction of harmful calls the scorer would have flagged |
| **FPR** (False Positive Rate) | What fraction of safe calls the scorer would have incorrectly flagged |
| **Latency p95** | 95th-percentile response time per call, in milliseconds |

---

## Multi-step scenarios

Some attacks require multiple steps in sequence. The `attack_scenarios/` folder
holds five of these:

| Scenario | What it models |
|----------|---------------|
| `session_abuse` | 5 innocent-looking reads, then a destructive write/delete |
| `replay_attack` | Same operation twice — checks for missing idempotency guards |
| `privilege_escalation_chain` | Read config → discover admin tool → call it |
| `indirect_prompt_injection_scenario` | Fetch URL with injected prompt → injected cmd executes |
| `idempotency_abuse_scenario` | 10 rapid creates → floods storage |

Run them alongside templates:
```bash
uv run python -m tests.testbed.harness.attack_runner --server filesystem --scenarios --mode attack
```

---

## Common commands

```bash
# First time: install project dependencies
uv sync

# Attack one server with all 25 templates
uv run python -m tests.testbed.harness.attack_runner --server filesystem --mode attack

# Run one specific template
uv run python -m tests.testbed.harness.attack_runner --server git --template git_argument_injection --mode attack

# Include multi-step scenarios
uv run python -m tests.testbed.harness.attack_runner --server filesystem --scenarios --mode attack

# Run all active servers (full campaign)
uv run python tests/testbed/run_all.py --mode attack

# Run the harness unit tests
uv run pytest tests/testbed/harness/ -v
```

---

## Adding a new server (no Python required)

1. Create `tests/testbed/servers/<name>.json`:

```json
{
  "name": "my_server",
  "description": "What this server does",
  "cve": ["CVE-YYYY-XXXXX"],
  "tier": "vulnerable",
  "transport": "stdio",
  "install": "npm install -g my-mcp-server",
  "start_cmd": ["npx", "-y", "my-mcp-server"],
  "expected_attack_categories": ["C1", "C2"]
}
```

2. Run the harness — it auto-discovers the new file.

For HTTP servers, replace `start_cmd` with `"base_url": "http://localhost:PORT"`.

---

## File map at a glance

```
tests/testbed/
├── GUIDE.md                  ← you are here
├── README.md                 ← concise technical reference
├── run_all.py                ← full campaign orchestrator
├── servers/
│   ├── filesystem.json       ← one profile per server
│   ├── fetch.json
│   ├── git.json
│   └── ...                   (24 active, 8 in disabled/)
├── attack_templates/
│   ├── path_traversal.json   ← one template per attack class
│   ├── command_injection.json
│   └── ...                   (25 total)
├── attack_scenarios/
│   ├── session_abuse.json    ← multi-step attack scripts
│   └── ...                   (5 total)
├── harness/
│   ├── attack_runner.py      ← main execution loop
│   ├── server_manager.py     ← start/stop server processes
│   ├── tool_matcher.py       ← match templates to live tools
│   ├── scenario_runner.py    ← run multi-step scenarios
│   ├── scorer_bridge.py      ← scorer integration (stub now)
│   └── metrics.py            ← ASR, TPR/FPR, latency
├── sandbox/                  ← isolated filesystem for file tests
└── results/                  ← JSON + markdown output (git-ignored)
```

---

## Filesystem Attack Chains — `attack_fs_chains.py`

A standalone white-hat attack campaign against the two Anthropic filesystem
MCP servers running under WSL (`/tmp/fs_328` v2025.3.28, `/tmp/fs_729`
v2025.7.29), using only `read_file` and `list_directory`. Not part of the
generic `attack_runner.py` harness — runs directly and writes its own
multi-sheet Excel report.

**What it does:**
- **Phase 0** — Hardcoded source-analysis of both `index.js` files
  (`validatePath`, `isPathWithinAllowedDirectories`, allow-list setup).
- **Phase 1** — 10 recon probes that fingerprint error shapes and leak info.
- **Phase 2** — 15 primitive probes, one question each.
- **Phase 3** — 15 attack chains (`C1`-`C15`) including prefix confusion,
  symlink plants, symlink chain/loop/dangling, dir-symlink, parent-dir
  symlink, **hardlink escape** (the main bet that paid off), TOCTOU race,
  procfs pivots, Unicode NFC/NFD, null-byte truncation, CVE-53110 mutations,
  type confusion, and resource exhaustion.
- **Phase 4/5** — Differential diff + PoC extraction embedded in the Excel
  writer.

**Safety:** all fixtures live under `/tmp/mcp_attack_{328,729}` and
`/tmp/victim_{328,729}`. Escape detection uses a canary string
`ATTACKER_CANARY_12345` — no real host secrets are required for the win
condition. Final `finally:` block wipes everything.

**Run:**

```
uv run python tests/testbed/attack_fs_chains.py
```

Runtime: ~90 seconds. Outputs:

- `excel_reports/fs_attack_chains.xlsx` — 8-sheet comparative report
  (Summary, Source_Analysis, Recon, Primitives, Chain_Steps, Diff, PoCs, Raw)
- `excel_reports/fs_attack_chains.source_notes.md` — Phase 0 gap analysis
- `excel_reports/fs_attack_chains.raw.jsonl` — audit log (git-ignored)

**Spec:** `docs/superpowers/specs/2026-04-10-fs-attack-chains-design.md`
**Plan:** `docs/superpowers/plans/2026-04-10-fs-attack-chains.md`
