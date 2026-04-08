# MCP Attack Testbed

A reproducible harness for attacking real MCP servers with structured payloads
and evaluating the MCP Security scorer's detection accuracy.

## Overview

The testbed serves two purposes:

1. **Empirical attack data** — run known-bad payloads against real MCP servers,
   record which ones cause observable damage, and build a ground-truth dataset.
2. **Scorer evaluation** — feed the same requests through the MCP Security
   scorer and measure TPR, FPR, and latency against that ground truth.

Attack payloads are kept separate from server implementations. Adding a new
server requires only dropping a JSON profile; no Python changes are needed.

## Directory Structure

```
tests/testbed/
├── attack_templates/      # Attack definitions — 25 templates (one JSON per attack class)
│   ├── command_injection.json
│   ├── path_traversal.json
│   ├── sql_injection.json
│   ├── ssrf.json
│   ├── auth_bypass.json
│   ├── resource_exhaustion.json
│   ├── tool_poisoning.json
│   ├── env_variable_exfil.json
│   ├── git_argument_injection.json
│   ├── output_injection.json
│   ├── behavioral_fingerprinting.json
│   ├── wildcard_fallback.json
│   ├── log_tampering.json
│   ├── db_credential_exposure.json
│   ├── throttle_bypass.json
│   ├── scraping.json
│   ├── tool_misuse.json
│   ├── false_error_escalation.json
│   ├── state_corruption.json
│   ├── protocol_exhaustion.json
│   ├── denial_of_wallet.json
│   ├── toxic_content_proxy.json
│   ├── idempotency_abuse.json
│   ├── rade_exfiltration.json
│   └── indirect_prompt_injection.json
├── attack_scenarios/      # Multi-step scenario definitions (one JSON per scenario)
├── harness/               # Python execution engine
│   ├── attack_runner.py   # Orchestrates sessions and collects results
│   ├── scenario_runner.py # Executes ordered multi-step attack scenarios
│   ├── server_manager.py  # Starts/stops stdio & HTTP servers
│   ├── tool_matcher.py    # Matches templates to live tools by keyword
│   ├── scorer_bridge.py   # Calls the MCP Security scorer (stub in Phase 1)
│   ├── metrics.py         # Computes ASR, TPR/FPR, latency p95
│   ├── test_attack_runner.py
│   ├── test_tool_matcher.py
│   └── test_metrics.py
├── servers/               # Server profiles — 32 profiles (one JSON per server)
└── results/               # JSON result files written at runtime (git-ignored)
```

## Quick Start

```bash
# Install dependencies
uv sync

# Run all attack templates against the filesystem server (attack-only mode)
uv run python -m tests.testbed.harness.attack_runner --server filesystem --mode attack

# Run a single template against a server and score the results
uv run python -m tests.testbed.harness.attack_runner \
    --server filesystem --template path_traversal --mode eval

# Run attack templates AND multi-step scenarios against a server
uv run python -m tests.testbed.harness.attack_runner --server filesystem --scenarios --mode eval

# Run only scenarios (via scenario_runner directly)
uv run python -m tests.testbed.harness.scenario_runner filesystem eval

# Run all servers
uv run python -m tests.testbed.harness.attack_runner --all --mode attack

# Run the testbed unit tests only
uv run pytest tests/testbed/harness/ -v
```

## Server Profiles

The testbed includes **32 server profiles** across three tiers:

- **Vulnerable (22)**: filesystem, fetch, git, data_vis, dvmcp, bridge, markdownify, godot,
  serverless, sqlite, desktop-commander, playwright-mcp, aws-mcp, fastmcp-server,
  puppeteer-mcp, github-mcp, google-maps-mcp, context7-mcp, adx-mcp, sequential-thinking,
  mcp-obsidian, pandoc-mcp, mcp-run-python
- **Benign (3)**: everything, memory, time (negative controls — should produce no damage)
- **Optional (6)**: brave-search, exa-mcp, firecrawl-mcp, tavily-search, slack-mcp,
  notion-mcp (require API key; run tool_poisoning and behavioral_fingerprinting only
  when key absent)

Tier `benign` servers act as negative controls; they should produce no damage and low
scorer output. Tier `optional` servers are excluded from default `--all` runs unless
the relevant API key is present in the environment.

## Adding a New Server

1. Create `tests/testbed/servers/<name>.json` with this schema:

```json
{
  "name": "my_server",
  "description": "What this server does",
  "cve": ["CVE-YYYY-XXXXX"],
  "tier": "vulnerable",
  "transport": "stdio",
  "install": "pip install my-mcp-server",
  "start_cmd": ["uvx", "my-mcp-server"],
  "expected_attack_categories": ["C1", "C2"]
}
```

For HTTP servers add `"transport": "http"` and `"base_url": "http://localhost:PORT"`.

2. The harness auto-discovers new profiles — no Python changes required.

## Attack Templates

25 templates organized by category. Categories follow the MCP Server Attack Taxonomy:
C1 = code/command execution, C2 = data exfiltration, C3 = privilege escalation,
C4 = DoS/resource abuse, C5 = indirect harm, C6 = injection.

| ID                          | Category | CWE      | Key Match Keywords                                    |
|-----------------------------|----------|----------|-------------------------------------------------------|
| path_traversal              | C2       | CWE-22   | read, file, open, load, path, content                 |
| ssrf                        | C2       | CWE-918  | fetch, url, http, request, get, browse, web           |
| command_injection           | C1       | CWE-78   | run, exec, command, shell, system, eval               |
| sql_injection               | C1       | CWE-89   | query, sql, db, database, table, select, data         |
| auth_bypass                 | C3       | CWE-306  | admin, root, privileged, manage, config, panel        |
| resource_exhaustion         | C4       | CWE-400  | run, exec, compute, generate, analyze, search         |
| tool_poisoning              | C6       | CWE-116  | * (all tools)                                         |
| env_variable_exfil          | C2       | CWE-200  | env, environment, variable, config, secret, key       |
| git_argument_injection      | C1       | CWE-88   | git, clone, fetch, pull, push, commit, branch         |
| output_injection            | C6       | CWE-1236 | render, display, output, format, export, write        |
| behavioral_fingerprinting   | C2       | CWE-209  | * (all tools)                                         |
| wildcard_fallback           | C1       | CWE-20   | * (all tools)                                         |
| log_tampering               | C1       | CWE-221  | log, audit, record, trace, history, event             |
| db_credential_exposure      | C2       | CWE-522  | connect, credential, password, auth, token, dsn       |
| throttle_bypass             | C4       | CWE-770  | search, list, fetch, get, query, paginate             |
| scraping                    | C2       | CWE-200  | fetch, get, browse, scrape, crawl, url, web           |
| tool_misuse                 | C5       | CWE-441  | send, post, publish, notify, message, email           |
| false_error_escalation      | C3       | CWE-755  | retry, fallback, escalate, error, recover, admin      |
| state_corruption            | C3       | CWE-666  | write, update, set, save, store, create               |
| protocol_exhaustion         | C4       | CWE-400  | connect, open, session, stream, socket, channel       |
| denial_of_wallet            | C4       | CWE-400  | generate, analyze, summarize, embed, classify, infer  |
| toxic_content_proxy         | C5       | CWE-693  | send, post, publish, render, display, generate        |
| idempotency_abuse           | C4       | CWE-770  | create, add, insert, upload, register, put            |
| rade_exfiltration           | C6       | CWE-20   | read, fetch, load, get, retrieve, content             |
| indirect_prompt_injection   | C6       | CWE-20   | fetch, read, load, browse, get, summarize             |

## Multi-Step Scenarios

The `attack_scenarios/` directory contains JSON files defining ordered sequences
of tool calls within a single session. These model attacks that require multiple
steps to exploit:

| ID                               | Category | Steps | Attack Modelled                                        |
|----------------------------------|----------|-------|--------------------------------------------------------|
| replay_attack                    | C3       | 2     | Replay same operation — no idempotency guard           |
| session_abuse                    | C3       | 7     | Benign reads followed by privileged write              |
| privilege_escalation_chain       | C1       | 3     | Read config → call admin tool                          |
| indirect_prompt_injection_scenario | C6     | 2     | Fetch injected content → execute injected cmd          |
| idempotency_abuse_scenario       | C4       | 10    | Repeated creates → storage flood                       |

See `attack_scenarios/README.md` for the full schema.

## Running the Harness

```bash
# Attack mode: just execute payloads, record damage, no scoring
uv run python -m tests.testbed.harness.attack_runner --server <name> --mode attack

# Eval mode: execute payloads AND run the scorer, record scores
uv run python -m tests.testbed.harness.attack_runner --server <name> --mode eval

# Include multi-step scenarios in a run
uv run python -m tests.testbed.harness.attack_runner --server <name> --scenarios --mode eval

# Repeat each payload N times (for latency averages)
uv run python -m tests.testbed.harness.attack_runner --server filesystem --trials 3

# Save results to a custom path
uv run python -m tests.testbed.harness.attack_runner --server filesystem \
    --output /tmp/my_run.json

# Run all servers, all templates
uv run python -m tests.testbed.harness.attack_runner --all --mode attack
```

Results are saved to `tests/testbed/results/<server>_<timestamp>.json`.

## Metrics

| Metric      | Definition                                                                 |
|-------------|----------------------------------------------------------------------------|
| ASR         | Attack Success Rate — fraction of malicious payloads that caused damage    |
| TPR         | True Positive Rate — fraction of malicious requests the scorer flagged     |
| FPR         | False Positive Rate — fraction of benign requests incorrectly flagged      |
| Score MAE   | Mean Absolute Error of scorer output vs expected range midpoints           |
| Latency p95 | 95th-percentile round-trip time per tool call (ms)                         |

`damage_detected` is determined by a regex pattern (`damage_indicator`) stored
in each attack template and matched against the tool's response. A scorer
threshold of 5.0 (out of 10) is the default for TPR/FPR calculations.

## Phase Status

| Phase | Status  | Description                                                          |
|-------|---------|----------------------------------------------------------------------|
| 1     | Done    | Harness, server profiles (32), attack templates (25), metrics        |
| 2     | Done    | Multi-step scenario runner (5 scenarios)                             |
| 3     | Planned | Wire live MCP Security scorer into scorer_bridge.py                  |
| 4     | Planned | Calibrate thresholds per category; CI integration                    |
