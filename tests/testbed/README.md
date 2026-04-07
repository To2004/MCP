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
├── attack_templates/      # Attack definitions (one JSON per attack class)
│   ├── command_injection.json
│   ├── path_traversal.json
│   ├── sql_injection.json
│   ├── ssrf.json
│   ├── auth_bypass.json
│   ├── resource_exhaustion.json
│   └── tool_poisoning.json
├── harness/               # Python execution engine
│   ├── attack_runner.py   # Orchestrates sessions and collects results
│   ├── server_manager.py  # Starts/stops stdio & HTTP servers
│   ├── tool_matcher.py    # Matches templates to live tools by keyword
│   ├── scorer_bridge.py   # Calls the MCP Security scorer (stub in Phase 1)
│   ├── metrics.py         # Computes ASR, TPR/FPR, latency p95
│   ├── test_attack_runner.py
│   ├── test_tool_matcher.py
│   └── test_metrics.py
├── servers/               # Server profiles (one JSON per server)
│   ├── filesystem.json
│   ├── fetch.json
│   ├── git.json
│   ├── data_vis.json
│   ├── dvmcp.json
│   ├── everything.json
│   ├── memory.json
│   └── time.json
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

# Run all servers
uv run python -m tests.testbed.harness.attack_runner --all --mode attack

# Run the testbed unit tests only
uv run pytest tests/testbed/harness/ -v
```

## Server Profiles

| Name        | Tier       | CVE(s)                                        | Expected Categories |
|-------------|------------|-----------------------------------------------|---------------------|
| filesystem  | vulnerable | CVE-2025-53109, CVE-2025-53110                | C2                  |
| fetch       | vulnerable | CVE-2025-65513                                | C2                  |
| git         | vulnerable | CVE-2025-68143, CVE-2025-68144, CVE-2025-68145 | C1                 |
| data_vis    | vulnerable | CVE-2026-5322                                 | C1                  |
| dvmcp       | vulnerable | (intentionally insecure, no CVE)              | C1, C3, C4          |
| everything  | benign     | —                                             | none                |
| memory      | benign     | —                                             | none                |
| time        | benign     | —                                             | none                |

Tier `benign` servers act as negative controls; they should produce no damage
and low scorer output.

## Attack Templates

| ID                 | Category | CWE      | Tools Matched (keywords)                          |
|--------------------|----------|----------|---------------------------------------------------|
| path_traversal     | C2       | CWE-22   | read, file, open, load, path, content             |
| ssrf               | C2       | CWE-918  | fetch, url, http, request, get, browse, web       |
| command_injection  | C1       | CWE-78   | run, exec, command, shell, system, eval           |
| sql_injection      | C1       | CWE-89   | query, sql, db, database, table, select, data     |
| auth_bypass        | C3       | CWE-306  | admin, root, privileged, manage, config, panel    |
| resource_exhaustion| C4       | CWE-400  | run, exec, compute, generate, analyze, search     |
| tool_poisoning     | C6       | CWE-116  | * (all tools)                                     |

Categories follow the MCP Server Attack Taxonomy: C1 = code/command execution,
C2 = data exfiltration, C3 = privilege escalation, C4 = DoS, C6 = injection.

## Running the Harness

```bash
# Attack mode: just execute payloads, record damage, no scoring
python -m tests.testbed.harness.attack_runner --server <name> --mode attack

# Eval mode: execute payloads AND run the scorer, record scores
python -m tests.testbed.harness.attack_runner --server <name> --mode eval

# Repeat each payload N times (for latency averages)
python -m tests.testbed.harness.attack_runner --server filesystem --trials 3

# Save results to a custom path
python -m tests.testbed.harness.attack_runner --server filesystem \
    --output /tmp/my_run.json

# Run all servers, all templates
python -m tests.testbed.harness.attack_runner --all --mode attack
```

Results are saved to `tests/testbed/results/<server>_<timestamp>.json`.

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

## Metrics

| Metric        | Definition                                                                 |
|---------------|----------------------------------------------------------------------------|
| ASR           | Attack Success Rate — fraction of malicious payloads that caused damage    |
| TPR           | True Positive Rate — fraction of malicious requests the scorer flagged     |
| FPR           | False Positive Rate — fraction of benign requests incorrectly flagged      |
| Score MAE     | Mean Absolute Error of scorer output vs expected range midpoints           |
| Latency p95   | 95th-percentile round-trip time per tool call (ms)                         |

`damage_detected` is determined by a regex pattern (`damage_indicator`) stored
in each attack template and matched against the tool's response. A scorer
threshold of 5.0 (out of 10) is the default for TPR/FPR calculations.

## Phase Status

| Phase | Status   | Description                                              |
|-------|----------|----------------------------------------------------------|
| 1     | Done     | Harness, server profiles, attack templates, metrics      |
| 2     | Planned  | Wire live MCP Security scorer into scorer_bridge.py      |
| 3     | Planned  | Expand to 15+ servers; calibrate thresholds per category |
